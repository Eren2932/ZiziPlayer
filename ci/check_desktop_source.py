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
        'page header continuous through actions': 'actions: @Composable () -> Unit' in ui and 'CollectionViewport(remote.collection.artworkTrack()' in ui and 'hero + 244.dp.toPx()' in ui and 'if (collapsed) Panel else Color.Transparent' in ui,
        'page header honors artwork preference': 'if (s.prefs.artworkColor) collectionTone(cover?.primary)' in ui,
        'header hue and contrast bounded': 'lch[0].coerceIn(.36f, .50f)' in palette and '(lch[1] * 1.18f).coerceAtMost(.22f)' in palette,
        'artwork reload includes URL': 'null, track?.id, track?.artwork, track?.artworkUrl, api, hero)' in ui,
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
    appearance = read(prefix + 'desktop/ui/DesktopAppearance.kt')
    hero = read(prefix + 'desktop/ui/HeroArtwork.kt')
    chrome = read(prefix + 'desktop/ui/WindowChrome.kt')
    checks.update({
        'shared lazy viewport for local and catalog pages': ui.count('CollectionViewport(') == 3 and 'state = state, reserveScrollbar = false' in ui,
        'hero background belongs to viewport not lazy header': 'Box(modifier.then(collectionBackground(track, s, state, artist)))' in ui,
        'scroll reads occur inside draw callback': 'val scroll = if (state.firstVisibleItemIndex == 0)' in ui and 'HeroMotion.visibility(scroll, hero)' in ui,
        'tail vanishes continuously before lazy disposal': '1f - smooth(progress(scroll, height))' in appearance and 't * t * (3f - 2f * t)' in appearance,
        'parallax and reduced motion share exact scroll input': 'HeroMotion.travel(scroll, motion)' in ui and 'if (motion) .28f else 1f' in appearance,
        'no hard one-pixel gradient boundary': 'hero + 1.dp.toPx()' not in ui and '(hero / end) to landing' in ui,
        'high-resolution tier shares original disk bytes': 'if (hero) 1600 else 480' in ui and 'diskPath(diskKey)' in ui and 'rememberDisk(diskKey, bytes)' in ui,
        'cover memory has pixel and count bounds': '64L * 1024 * 1024' in ui and 'size > 64' in ui,
        'wide photos remain unmodified': 'source.width >= 1000) return source' in hero,
        'small portraits have bounded enlargement and feathering': '1.25' in hero and 'AlphaComposite.DstIn' in hero and 'BufferedImage(24, 10' in hero,
        'black caption uses supported Compose drag area': 'import androidx.compose.foundation.window.WindowDraggableArea' in ui and 'WindowDraggableArea(' in ui,
        'decoration selected once with native fallback': 'remember { ui.appearance.nativeFrame }' in ui and 'undecorated = !nativeFrame, resizable = true' in ui,
        'native and caption close share shutdown': 'Window(onCloseRequest = close' in ui and 'WindowCaptionButton("Закрыть приложение", 3, close)' in ui,
        'caption buttons labelled and keyboard clickable': 'contentDescription = label' in chrome and 'role = Role.Button' in chrome,
        'appearance writes are serialized off UI thread': 'Channel<DesktopAppearance>(Channel.CONFLATED)' in model and 'for (value in appearanceWrites)' in model and 'appearanceWriter.join()' in model,
        'settings expose motion panorama and native frame': all(x in ui for x in ('s.appearance.copy(motion = it)', 's.appearance.copy(panoramicArtists = it)', 's.appearance.copy(nativeFrame = it)')),
        'notice overlays rather than shifting scroll viewport': 'padding(bottom = 104.dp, start = 24.dp, end = 24.dp)' in ui,
        'local artwork is not called an artist portrait': 'Исполнитель · обложка локального трека' in ui,
        'desktop package version advanced': 'version = "0.3.5"' in build and 'packageVersion = "0.3.5"' in build,
    })
    discovery = read(prefix + 'desktop/ui/DiscoveryArtwork.kt')
    checks.update({
        'discovery uses 24 real catalog queries': discovery.count('DiscoveryGenre("') == 24 and 'api.browse(query, "album").items' in model,
        'discovery bounds fanout cache and errors': 'Semaphore(2)' in discovery and 'cache.size > 48' in discovery and '60_000L else 600_000L' in discovery,
        'discovery cancellation propagates': 'catch (e: CancellationException) { throw e }' in discovery and 'currentCoroutineContext().ensureActive()' in discovery,
        'discovery refresh invalidates obsolete response': 'generation++; cache.clear()' in discovery and 'token == generation' in discovery,
        'genre artwork loaded lazily with debounce': 'produceState<List<CatalogCollection>>' in ui and 'delay(180)' in ui and 's.discovery.albums(genre.query)' in ui,
        'tilted covers open actual catalog albums': 'rotationZ = if (front) 14f else -9f' in ui and '.clickable { s.open(album) }' in ui,
        'search refresh uses visible field not stale query': 'if (searchText.isNotBlank()) search(searchText, s.searchKind)' in ui and 's.cancelSearch(); s.refreshDiscovery()' in ui,
        'refresh handler does not silently ignore busy clicks': 'IconButton(onClick = onClick, enabled = enabled' in ui and 'if (!refreshing) onClick()' not in ui,
        'home search has no verbose helper labels': 'Введи запрос в строке сверху — подсказки появятся во время ввода' not in ui and 'не персональная выдача сервера.' not in ui,
        'double click observer does not steal window drag': 'awaitPointerEvent(PointerEventPass.Initial)' in ui and 'detectTapGestures(onDoubleTap' not in ui,
    })
    upstream = json.loads(read('upstream.json'))
    for item in upstream['files']:
        checks['upstream hash: ' + item['path']] = hashlib.sha256((root/item['path']).read_bytes()).hexdigest() == item['sha256']
    for name, passed in checks.items(): print(('PASS ' if passed else 'FAIL ') + name)
    if not all(checks.values()): raise SystemExit(1)
    print(f'{len(checks)} static contracts passed. Compilation/runtime tests are separate.')

if __name__ == '__main__':
    check(Path(os.environ['DESKTOP_PROJECT']))
