#!/usr/bin/env python3
"""Single-request Chromium native messaging endpoints. GPL-3.0-or-later."""
import json
import os
from pathlib import Path
import select
import struct
import subprocess
import sys
import time
from urllib.parse import urlsplit

ORIGINS = {
    'copy': 'chrome-extension://bgpiichlckmfanooecilcjemknkcpngb/',
    'download': 'chrome-extension://dedjgknigfeelejglamclffonmophnfl/',
}
MAX_MESSAGE = 65536
MAX_URL = 16384


def read_exact(stream, size, deadline):
    data = bytearray()
    while len(data) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([stream], [], [], remaining)[0]:
            raise ValueError('Native request deadline expired')
        part = os.read(stream.fileno(), size - len(data))
        if not part:
            raise ValueError('Truncated native request')
        data.extend(part)
    return bytes(data)


def request(stream):
    deadline = time.monotonic() + 5
    size = struct.unpack('<I', read_exact(stream, 4, deadline))[0]
    if not 0 < size <= MAX_MESSAGE:
        raise ValueError('Native request exceeds bounds')
    value = json.loads(read_exact(stream, size, deadline).decode('utf-8'))
    if not isinstance(value, dict) or set(value) != {'url'}:
        raise ValueError('Expected a URL request')
    url = value['url']
    if not isinstance(url, str) or not url or len(url.encode('utf-8')) > MAX_URL:
        raise ValueError('URL exceeds bounds')
    if any(ord(c) < 32 or ord(c) == 127 for c in url):
        raise ValueError('URL contains control characters')
    return url


def handle(action, url):
    if action == 'copy':
        result = subprocess.run(['wl-copy', '--type', 'text/plain'], input=url.encode(),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
        if result.returncode == 0:
            try:
                subprocess.run(['tam-notification-send', '-g', '󰅍', 'URL copied to clipboard'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
            except (OSError, subprocess.SubprocessError):
                pass
        return {'copied': result.returncode == 0}
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Download requires an HTTP(S) URL without credentials')
    worker = Path(__file__).resolve().with_name('download-worker')
    subprocess.Popen(['bash', str(worker), '--download', url], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {'accepted': True}


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    if action not in ORIGINS or len(sys.argv) < 3 or sys.argv[2] != ORIGINS[action]:
        sys.exit('Refused native messaging origin')
    try:
        reply = handle(action, request(sys.stdin.buffer))
    except (OSError, ValueError, UnicodeError, RecursionError, subprocess.SubprocessError) as error:
        print('native-host: '+str(error), file=sys.stderr)
        reply = {'copied': False} if action == 'copy' else {'accepted': False}
    payload = json.dumps(reply, separators=(',', ':')).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('<I', len(payload)) + payload)
    sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
