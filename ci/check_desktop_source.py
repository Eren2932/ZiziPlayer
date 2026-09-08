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
    store = read(prefix + 'desktop/LibraryStore.kt')
    player = read(prefix + 'desktop/DesktopPlayer.kt')
    offline = read(prefix + 'desktop/OfflineFiles.kt')
    network = read(prefix + 'desktop/network/ZiziClient.kt')
    bundled = read(prefix + 'desktop/network/BundledConnection.kt')
    bridge = read(prefix + 'desktop/network/StreamBridge.kt')
    build = read('build.gradle.kts')
    checks = {
        'matte UI has no gradient brush': 'Brush.verticalGradient' not in ui and 'private val Base = Color.Black' in ui,
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
        'mobile search geometry': 'RoundedCornerShape(3.5.dp)' in ui and '49.5.dp' in ui and 'fontSize = 17.sp' in ui,
        'mobile refresh motion': 'tween(900, easing = LinearEasing)' in ui and 'tween(340, easing = FastOutSlowInEasing)' in ui,
        'authenticated redirects remain disabled': 'instanceFollowRedirects = false' in network,
        'HTTP opt-in checked by exact origin': 'sameOrigin(uri, legacyOrigin)' in network and 'resolver.allowHttp' in bundled,
        'stream bridge uses same scoped policy': 'e.requestMethod, target.legacyOrigin)' in bridge,
        'bootstrap comes from build environment': 'environmentVariable("RESOLVER_TOKEN")' in build,
        'device key cache wired to auth exchange': 'tokenStore.save(DeviceCredential' in network,
        'auth backoff remains five minutes': 'retryAt = now + 300_000' in network,
        'device 401 recovery bounded to one retry': 'if (e.code != 401) throw e' in network and 'return request()' in network,
    }
    upstream = json.loads(read('upstream.json'))
    for item in upstream['files']:
        checks['upstream hash: ' + item['path']] = hashlib.sha256((root/item['path']).read_bytes()).hexdigest() == item['sha256']
    for name, passed in checks.items(): print(('PASS ' if passed else 'FAIL ') + name)
    if not all(checks.values()): raise SystemExit(1)
    print(f'{len(checks)} static contracts passed. Compilation/runtime tests are separate.')

if __name__ == '__main__':
    check(Path(os.environ['DESKTOP_PROJECT']))
