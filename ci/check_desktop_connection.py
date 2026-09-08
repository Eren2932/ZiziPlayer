"""Release preflight. Never print values, URLs, tokens or parser exceptions."""
import os
import sys
from urllib.parse import urlsplit

def check(values):
    raw = values.get('RESOLVER_URL', '').strip().rstrip('/')
    token = values.get('RESOLVER_TOKEN', '').strip()
    if not raw or not token:
        return 'Set RESOLVER_URL (variable) and RESOLVER_TOKEN (secret) for the build.'
    if len(token) > 4096 or any(not 32 <= ord(c) <= 126 for c in token):
        return 'Invalid bootstrap format; no credential value was logged.'
    if any(ord(c) <= 32 for c in raw):
        return 'Invalid resolver URL; no value was logged.'
    try:
        u = urlsplit(raw if '://' in raw else 'http://' + raw)
        if u.scheme not in ('http', 'https') or not u.hostname or u.username is not None or u.password is not None or '?' in raw or '#' in raw or u.port == 0:
            return 'Use a resolver URL without login, query or fragment.'
        if u.scheme == 'http' and u.hostname not in ('localhost', '127.0.0.1', '::1') and values.get('DESKTOP_ALLOW_HTTP') != 'true':
            return 'Legacy HTTP requires the allow_http build checkbox or DESKTOP_ALLOW_HTTP=true repository variable. HTTPS is recommended.'
    except ValueError:
        return 'Invalid resolver URL; no value was logged.'
    return None

if __name__ == '__main__':
    error = check(os.environ)
    print(error or 'Connection inputs validated (values not logged).')
    sys.exit(1 if error else 0)
