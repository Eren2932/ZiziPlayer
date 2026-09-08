"""Static source contracts, NOT a Kotlin compiler or UI/connection integration test."""
import hashlib
import json
import os
from pathlib import Path


def check(root: Path):
    def read(path): return (root / path).read_text(encoding='utf-8')
    prefix = 'src/main/kotlin/app/ziziplayer/'
    ui = read(prefix + 'desktop/ui/DesktopMain.kt')
    model = read(prefix + 'desktop/ui/DesktopUi.kt')
    preview = read(prefix + 'desktop/ui/SearchPreview.kt')
    palette = read(prefix + 'desktop/ui/ArtworkPalette.kt')
    slider = read(prefix + 'desktop/ui/ThinSlider.kt')
    dock = read(prefix + 'desktop/ui/DesktopDock.kt')
    outputs = read(prefix + 'desktop/AudioOutputs.kt')
    store = read(prefix + 'desktop/LibraryStore.kt')
    player = read(prefix + 'desktop/DesktopPlayer.kt')
    offline = read(prefix + 'desktop/OfflineFiles.kt')
    network = read(prefix + 'desktop/network/ZiziClient.kt')
    bundled = read(prefix + 'desktop/network/BundledConnection.kt')
    bridge = read(prefix + 'desktop/network/StreamBridge.kt')
    build = read('build.gradle.kts')
    checks = {
        'collection-only spatial gradient with black shell': 'Brush.verticalGradient' in ui and 'private val Base = Color.Black' in ui and 'collectionTone(cover?.primary)' in ui,
        'mobile surface, chip and text colors': all(x in ui for x in ('0xFF101010', '0xFF1B1B1B', '0xFFF6F7F8')),
        'no server or bootstrap input in settings': 'Bootstrap-токен' not in ui and 'HTTPS-адрес сервера' not in ui and 'fun connect(' not in ui,
        'bundled client attached to player on startup': 'BundledConnection.load()' in model and 'player.client = api' in model,
        'manual preference not used for bootstrap origin': 'DesktopPreferences.server' not in ui,
        'audio settings do not replace network client': 's.audioSettings(executable)' in ui,
        'settings hub replaces connection form': 'fun SettingsContent' in ui and 'fun SettingsDialog' not in ui,
        'single serialized library writer': 'Channel<Write>' in model and 'for (first in writes)' in model,
        'atomic replacement plus sync and backup': all(x in store for x in ('ATOMIC_MOVE', 'fd.sync()', 'library-v1.backup.json')),
        'unknown schema remains read only': 'UnsupportedLibraryVersion' in store and 'writable = false' in store,
        'repeat executes after decoder completion': 'if (repeatMode == RepeatMode.ONE) play(track) else adjacent(1)' in player,
        'queue reorder observable and identity based': 'queueState: StateFlow' in player and 'fun move(id: String' in player,
        'offline uses scoped transport and partial file': 'target.legacyOrigin' in offline and '.part' in offline and 'INCOMPLETE_DOWNLOAD' in offline,
        'mobile DSP persistence codec': 'DspCodec.encode' in model and 'DspCodec.decode' in model,
        'desktop centered pill and exactly aligned popup': 'width(searchWidth)' in ui and 'width = searchWidth' in ui and '24.dp else 6.dp' in ui and 'PopupProperties(focusable = false)' in ui,
        'preview independent from submitted search': 'SearchPreview(scope' in model and 'fun preview(raw: String) = previews.request(raw)' in model,
        'preview debounce and obsolete-response guard': 'debounceMs: Long = 320' in preview and 'delay(debounceMs)' in preview and 'ensureActive()' in preview and 'token == generation' in preview,
        'preview cancelled at shutdown': 'periodic?.cancel(); cancelPreview()' in model,
        'preview does not persist history': 'recentSearches' not in preview and 'DesktopPreferences' not in preview,
        'preview bounded and deduplicated': 'distinctBy { it.id }.take(6)' in preview,
        'transport brand orange independent of cover': 'primary = Brand' in ui and '0xFFF97316' in slider and 'ThinSlider(value = drag' in ui,
        'one exclusive right dock': 'mutableStateOf(DesktopDock.NONE)' in ui and 'when (dock)' in ui and 'NONE, QUEUE, EFFECTS, DEVICES' in dock and 'AnimatedVisibility' not in ui,
        'library collapse and full hide': 'sidebarMode = lastVisibleSidebar' in ui and 'sidebarMode = if (sidebarMode == 2) 1 else 2' in ui,
        'page header continuous through actions': 'actions: @Composable () -> Unit' in ui and 'collectionBackground(remote.collection.artworkTrack()' in ui and 'hero + 244.dp.toPx()' in ui and 'if (collapsed) Panel else Color.Transparent' in ui,
        'page header honors artwork preference': 'if (s.prefs.artworkColor) collectionTone(cover?.primary)' in ui,
        'header hue and contrast bounded': 'lch[0].coerceIn(.36f, .50f)' in palette and '(lch[1] * 1.18f).coerceAtMost(.22f)' in palette,
        'artwork reload includes URL': 'null, track?.id, track?.artwork, track?.artworkUrl, api)' in ui,
        'bounded locks coalesce cover misses': 'loadLocks = Array(32)' in ui and 'synchronized(loadLocks[' in ui,
        'transport seek validates identity and generation': 'progress.trackId == state.track?.id && progress.generation == state.generation' in ui,
        'sticky collection header and dense rows': 'stickyHeader { TrackTableHeader' in ui and 'Artwork(track, s.client, 40.dp)' in ui,
        'mobile refresh motion': 'tween(900, easing = LinearEasing)' in ui and 'tween(340, easing = FastOutSlowInEasing)' in ui,
        'authenticated redirects remain disabled': 'instanceFollowRedirects = false' in network,
        'HTTP opt-in checked by exact origin': 'sameOrigin(uri, legacyOrigin)' in network and 'resolver.allowHttp' in bundled,
        'stream bridge uses same scoped policy': 'e.requestMethod, target.legacyOrigin)' in bridge,
        'bootstrap comes from build environment': 'environmentVariable("RESOLVER_TOKEN")' in build,
        'device key cache wired to auth exchange': 'tokenStore.save(DeviceCredential' in network,
        'auth backoff remains five minutes': 'retryAt = now + 300_000' in network,
        'device 401 recovery bounded to one retry': 'if (e.code != 401) throw e' in network and 'return request()' in network,
    }
    checks.update({
        'no constraint-width animations': 'animateDpAsState' not in ui and 'expandHorizontally' not in ui,
        'dock state survives close': 'panelStates.SaveableStateProvider(dock.name)' in ui,
        'slider thin paint and usable hit area': 'height(24.dp)' in slider and '4.dp.toPx(), StrokeCap.Round' in slider,
        'slider cancellation and obsolete identity': 'if (!committed) cancel()' in slider and 'liveGestureKey == gestureKey' in slider,
        'slider keyboard and accessibility': 'progressBarRangeInfo' in slider and 'setProgress' in slider and 'Key.MoveHome' in slider,
        'seek callback checks live generation': 'live.generation == state.generation' in ui,
        'audio devices are real mixers': 'AudioSystem.getMixerInfo()' in outputs and 'isLineSupported' in outputs,
        'active output set only after sink opens': outputs.index('val sink = JavaSoundSink') < outputs.index('mutableActive.value = route'),
        'closed old sink cannot clear new route': 'compareAndSet(route, null)' in outputs,
        'output refresh scoped to panel': 'LaunchedEffect(refresh)' in ui and 'delay(5000)' in ui,
        'search overview uses existing endpoints': 'api.browse(q, type)' in model and 'supervisorScope' in model,
        'submitted search guards generations': 'token == searchGeneration' in model and 'ensureActive()' in model,
        'discovery is grounded in library': 'distinctBy { it.artist.lowercase() }' in ui and 'SearchHub(s' in ui,
        'catalog durations parsed in seconds': 'row.optLong("dur", 0)' in network and '?.times(1000)' in network,
    })
    upstream = json.loads(read('upstream.json'))
    for item in upstream['files']:
        checks['upstream hash: ' + item['path']] = hashlib.sha256((root/item['path']).read_bytes()).hexdigest() == item['sha256']
    for name, passed in checks.items(): print(('PASS ' if passed else 'FAIL ') + name)
    if not all(checks.values()): raise SystemExit(1)
    print(f'{len(checks)} static contracts passed. Compilation/runtime tests are separate.')

if __name__ == '__main__':
    check(Path(os.environ['DESKTOP_PROJECT']))
