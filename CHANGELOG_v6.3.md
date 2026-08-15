ZiziPlayer v6.3.0 (versionCode 10)
Built on v6.2.1. Where 6.2 was about pixels, this release is about the three things that would have
hurt real users after the store upload: their data, the wait, and the package itself.
Nothing in the UI moved. The list geometry, the mini player, the round controls and the cover-derived
palette are exactly as you tested them.
1. Track identity: derived from the file, not from the provider row
The bug. The primary key was whatever the source handed us: "media:$mediaStoreId", or a UUID
over the SAF document URI. Six tables hang off that key - favorites, playlist_tracks, track_fx,
hidden, play_stats - which is to say, everything the user has invested in.
Neither key is a property of the file:
MediaStore.Audio.Media._ID is a row id in the media provider. It changes on re-index: moving the file, renaming its folder, clearing media storage, restoring a backup, or a system update that triggers a full rescan. It is also reused for a different file after a deletion, so the old scheme could silently attach your favourites to the wrong track.
A SAF document URI embeds the tree grant. Re-picking the same folder, or remounting an SD card, changes it.
So a re-index wiped favourites, playlists, per-track speed/pitch/reverb, hidden tracks and play
counts - quietly, with no error and no way back. This is the single most damaging bug in the app.
The fix. TrackId.forFile():
id = "f:" + sha1("<display name lowercased>|<size in bytes>")[0..23]
Name and size are exact, available from both sources without opening the file (DISPLAY_NAME/SIZE
on MediaStore, COLUMN_DISPLAY_NAME/COLUMN_SIZE on SAF), and unchanged by anything the media
provider does. 96 bits of hash, fixed width, stored in six tables and compared on every list build.
Deliberately not in the key:
Duration. MediaStore reads it from the container header, MediaMetadataRetriever computes it from the stream, and the two disagree by milliseconds on plenty of files. Straddling a rounding boundary would hand one file two identities.
Path. Excluded so that moving a file between folders keeps its history.
Degenerate input is handled: some providers report SIZE as 0, and hashing that would collapse every
such file into a single id - the library would appear to contain one track. Those fall back to a
URI-derived "u:" form.
Migration, and why it is in two parts. SQLite has no SHA-1 and no access to the file system, so
the new keys cannot be computed inside a migration. Therefore:
MIGRATION_2_3 only adds sizeBytes and legacyId and stamps legacyId = id on every existing row. No id is touched, nothing can be lost.
The rewrite happens once, in Kotlin, during the first scan after the upgrade. The scanner reports both the new id and the id a file would have had under 6.2, so old key and new key meet inside the same object, and MusicDao.remapTrackId moves the child rows across in one transaction.
Three properties of that remap worth stating:
Bounded by the user's data, not the library. Only ids that actually appear in favourites, playlists, FX, hidden or stats are remapped. Simulated on a 3384-file library with 40 favourites, 120 playlist entries and 15 FX rows: 173 updates, not 3384.
Crash-safe. The "done" flag is written only after the pass completes, every UPDATE is idempotent, and the old rows are still present until the scan finishes. A process death means the next launch retries.
UPDATE OR IGNORE. The same file reachable through both MediaStore and a SAF grant existed twice under the old scheme; a plain UPDATE would hit the primary key and abort the whole transaction. The correct row is kept and the stale one is swept by the prune queries.
PlaybackMemory follows the remap too, otherwise "resume where you left off" would break exactly
once, on the upgrade.
Verified by simulation over 3384 synthetic files, then re-indexing every MediaStore row:
favourites survived : 40/40        [v6.2 behaviour: 0/40]
playlist entries    : 120/120
per-track FX        : 15/15
identity stable across move / re-grant : yes
byte-identical duplicate in two folders: merged (intended)
zero-size files                        : distinct ids, not collapsed
Side effect, free of charge. Deduplication is now by identity instead of the old
title|artist|duration guess. That heuristic merged genuinely different tracks that happened to
share a name and a length - live takes, remasters, slowed and sped-up edits, of which this library
has a great many. They no longer disappear.
One accepted cost. ArtworkIndex caches extracted colours and the "this file has no cover" flag
by track id, and those keys are not remapped. After the upgrade each cover is quantised once more
(1-3 ms, then cached again). Remapping a SharedPreferences cache from inside the data layer would
have meant wiring the UI package into the repository, which is not worth it for a one-time cost.
2. Folder scanning: 13574 binder calls down to 50
The bug. scanTree walked the tree with DocumentFile and read tags inline, on one thread,
recursively, with no progress and no way to stop.
DocumentFile is the expensive part, and not for the obvious reason: listFiles() queries the
directory, and then every property read is another IPC round trip. isDirectory, isFile,
type, name - four binder calls per entry, before a single tag is read.
v6.2  first scan :  13574 binder calls + 3381 tag reads (serial)
v6.3  first scan :     50 binder calls + 3381 tag reads (4 in parallel)
v6.3  rescan     :     50 binder calls +    0 tag reads
What changed:
One projected query per directory. DocumentsContract.buildChildDocumentsUriUsingTree with a five-column projection; document id, name, MIME type, size and modification time all come out of that one row. 99.6% of the binder traffic is gone.
Tag reading is off the walk, capped at 4 concurrent MediaMetadataRetriever instances - enough to saturate storage without provoking an OEM media-server stall.
Unchanged files skip tag reading entirely. The database snapshot is handed to the scanner; a file whose id and byte size match an existing row cannot have different tags, so its row is carried over and only its URI and folder are refreshed. A rescan now costs the walk and nothing else.
Iterative, not recursive. A deep tree used to grow the stack with its depth, and a provider reporting a cycle would have overflowed it. There is also a hard bound of 20000 directories.
Cancellable, per directory and per file. Leaving the screen or removing the folder stops the work instead of letting it run to completion in the background.
Wider format coverage. Providers routinely return application/octet-stream for FLAC and Opus, so the extension list is the fallback and now includes opus, oga, wma, m4b, mka, aif, aiff.
release() on the retriever throws on some OEM builds when setDataSource failed. It can no longer take the whole scan down.
A crash that was hiding in plain sight
MediaStore.Audio.Media.RELATIVE_PATH only exists from API 29. v6.2 asked for it with
getColumnIndexOrThrow on every API level, so on Android 8 and 9 the scan threw
IllegalArgumentException, the caller's runCatching swallowed it, and the library came up empty
with no error shown - on a minSdk 26 app. Optional columns are now resolved with getColumnIndex
and the folder label falls back to the parent directory of the legacy DATA path.
Progress that means something
"Сканируем…" with no end in sight is indistinguishable from a hang, and on a large folder that wait
was tens of seconds. The badge now reads Чтение тегов · 1250 / 3381.
Progress is exposed as its own StateFlow and deliberately kept out of LibraryUiState. It
ticks every 25 files; folding it into the library state would push filter, search, folder counting
and a full sort of the library through Dispatchers.Default dozens of times per scan and hand
Compose a new list each time. That is precisely the mistake v3 made with the playback position.
Scans are also serialised, latest wins. The startup scan, "add folder" and a manual refresh could
overlap: two passes writing the same rows, two sets of tag readers competing for the decoder, and
whichever finished first clearing the badge while the other was still running. The new scan cancels
and joins the previous one before touching the database.
Note the trap here, because the obvious fix is wrong: plain single-flight - ignore anything asked
while a scan is in flight - breaks first launch. The startup scan begins before the storage
permission is granted, so it finds nothing, and the rescan fired when the user taps "Allow" is
precisely the one that must not be dropped. Cancel-and-join gets both properties.
And pruneOrphans() actually runs. It sat behind an early return that was taken whenever nothing
had gone stale - the common case - so orphaned favourites and playlist entries accumulated forever.
3. The package itself
A real adaptive icon. android:icon pointed at @drawable/ic_launcher_foreground: a single vector with a black rectangle baked in, used raw. No adaptive shape, no parallax, no themed icon, and the glyph sat at the edge of the launcher's crop. Now mipmap-anydpi-v26/ic_launcher.xml with separate background, foreground and monochrome layers (themed icons, Android 13+), plus roundIcon. The glyph is built inside the 62x62 safe box centred on (54,54), which is the only region guaranteed to survive every mask.
android:label is a resource. The manifest cannot be localised, and a hardcoded label is one of the first things a store review flags. values/strings.xml now holds app_name. The in-app Compose strings are still inline - moving two hundred of them is a separate job and would bury the real changes of this release.
No more white flash on cold start. The theme had no windowBackground, so the first frame was the platform default - white on most OEM skins - before Compose drew the dark UI.
Two dependencies removed. androidx.documentfile (the scanner no longer uses it) and androidx.palette (superseded by the in-app quantiser back in 6.2). Both were still shipped, both still had keep rules aimed at them.
R8 rules corrected. The dead palette rule is gone; added keeps for Room's generated _Impl classes and for the @Transaction default method on MusicDao, which R8 sees as unused because it is only reached through generated code. That class of mistake is a release-only crash.
CI that cannot lie. .github/workflows/build.yml builds assembleRelease without continue-on-error - a workflow that goes green on a failed build is worse than none, because it teaches you to trust the tick. Lint runs separately as a report and does not gate the build. gradle-wrapper.properties pins Gradle 8.11.1 and the workflow regenerates the wrapper from it, so no binary jar has to be committed while ./gradlew still works locally.
Files touched
app/build.gradle.kts                              versionCode 10, 6.3.0, two deps removed
app/proguard-rules.pro                            dead palette rule out, Room _Impl keeps in
app/src/main/AndroidManifest.xml                  adaptive + round icon, label from resources
app/src/main/res/values/strings.xml               new
app/src/main/res/values/styles.xml                windowBackground
app/src/main/res/drawable/ic_launcher_background.xml    new
app/src/main/res/drawable/ic_launcher_foreground.xml    rebuilt to adaptive geometry
app/src/main/res/drawable/ic_launcher_monochrome.xml    new
app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml      new
app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml new
app/src/main/java/app/ziziplayer/data/TrackId.kt        new
app/src/main/java/app/ziziplayer/data/Entities.kt       sizeBytes, legacyId
app/src/main/java/app/ziziplayer/data/ZiziDatabase.kt   version 3, MIGRATION_2_3
app/src/main/java/app/ziziplayer/data/MusicDao.kt       allTracks, referencedTrackIds, remapTrackId
app/src/main/java/app/ziziplayer/data/MusicScanner.kt   rewritten
app/src/main/java/app/ziziplayer/data/MusicRepository.kt scan order, one-shot remap, progress
app/src/main/java/app/ziziplayer/data/SettingsStore.kt  ids_migrated_v3 flag
app/src/main/java/app/ziziplayer/data/PlaybackMemory.kt follows the remap
app/src/main/java/app/ziziplayer/ZiziApplication.kt     registers MIGRATION_2_3
app/src/main/java/app/ziziplayer/ui/MainViewModel.kt    scanProgress, single-flight, withScan
app/src/main/java/app/ziziplayer/ui/screens/LibraryScreen.kt  badge shows progress
.github/workflows/build.yml                       new
gradle/wrapper/gradle-wrapper.properties          new
Not done, and why
Not compiled. There is no Android SDK in my sandbox. This is verified by algorithm simulation (the id scheme and the migration were modelled in Python against a 3384-file library and a full re-index), plus balance and reference checks on every file - not by gradlew assembleRelease. Build it before trusting it.
gradle-wrapper.jar is absent on purpose: it is a binary, I cannot fetch it (no network), and the workflow regenerates it. Run gradle wrapper --gradle-version 8.11.1 once if you want ./gradlew locally.
Still no tests. The migration is exactly the thing that deserves an instrumented Room MigrationTestHelper test. That needs a device or an emulator, so it belongs in the next pass.
In-app strings not externalised. Deliberate, see above.
