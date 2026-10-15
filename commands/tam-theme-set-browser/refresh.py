#!/usr/bin/env python3
"""Refresh existing default browser profiles without starting a closed browser."""
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import sys

PROFILES = {'chromium': 'chromium', 'google-chrome-stable': 'google-chrome',
            'google-chrome': 'google-chrome', 'microsoft-edge-stable': 'microsoft-edge',
            'brave': 'BraveSoftware/Brave-Browser', 'brave-origin': 'BraveSoftware/Brave-Browser'}


def running_profile(profile):
    try:
        lock = profile / 'SingletonLock'
        hostname, pid = os.readlink(lock).rsplit('-', 1)
        if hostname != socket.gethostname() or not pid.isascii() or not pid.isdigit() or int(pid) <= 1:
            return False
        if lock.lstat().st_uid != os.getuid() or Path('/proc', pid).stat().st_uid != os.getuid():
            return False
        endpoint = (profile / 'SingletonSocket').stat()
        return stat.S_ISSOCK(endpoint.st_mode) and endpoint.st_uid == os.getuid()
    except (OSError, ValueError):
        return False


def refresh(command, profile, timeout=5):
    if not running_profile(profile):
        return 'not-running'
    # A browser may exit between the singleton check and the IPC invocation.
    # Bound that race and terminate only the new invocation's process group.
    child = subprocess.Popen([str(command), '--refresh-platform-policy', '--no-startup-window'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        status = child.wait(timeout=timeout)
        return 'refreshed' if status == 0 else 'failed'
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=1)
        except ProcessLookupError:
            child.wait(timeout=1)
        return 'timeout'


def main():
    config = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')
    failed = False
    for command in sys.argv[1:]:
        if command not in PROFILES:
            raise ValueError('Unsupported browser refresh command')
        result = refresh(command, config / PROFILES[command])
        if result in ('timeout', 'failed'):
            print(f'Browser policy stored; {command} policy refresh {result}.', file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
