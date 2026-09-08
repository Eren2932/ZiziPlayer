"""Static source contracts, NOT a Kotlin compiler or UI/connection integration test."""
import hashlib
import json
import os
from pathlib import Path


def check(root: Path):
    def read(path): return (root / path).read_text(encoding='utf-8')
    prefix = 'src/main/kotlin/app/ziziplayer/'
    ui = read(prefix + 'desktop/ui/DesktopMain.kt')
    network = read(prefix + 'desktop/network/ZiziClient.kt')
    bundled = read(prefix + 'desktop/network/BundledConnection.kt')
    bridge = read(prefix + 'desktop/network/StreamBridge.kt')
    build = read('build.gradle.kts')
    checks = {
        'matte UI has no gradient brush': 'Brush.verticalGradient' not in ui and 'private val Base = Color.Black' in ui,
        'mobile surface, chip and text colors': all(x in ui for x in ('0xFF101010', '0xFF1B1B1B', '0xFFF6F7F8')),
        'no server or bootstrap input in settings': 'Bootstrap-токен' not in ui and 'HTTPS-адрес сервера' not in ui and 'fun connect(' not in ui,
        'bundled client attached to player on startup': 'BundledConnection.load()' in ui and 'player.client = api' in ui,
        'manual preference not used for bootstrap origin': 'DesktopPreferences.server' not in ui,
        'audio settings do not replace network client': 's.audioSettings(executable)' in ui,
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
