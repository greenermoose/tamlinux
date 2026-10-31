"""Private D-Bus child for the opt-in GTK portal test; never run in a user bus."""
import os
from pathlib import Path
import select
import subprocess
import sys
import time

root = Path(sys.argv[1])
dark, light = sys.argv[2:4]
env = os.environ.copy()


def run(*args):
    return subprocess.run(args, env=env, check=True, text=True, capture_output=True, timeout=12).stdout.strip()


def verify_isolation():
    profile = (root / 'profile').resolve()
    config = (root / 'config').resolve()
    if env.get('DCONF_PROFILE') != str(profile) or env.get('XDG_CONFIG_HOME') != str(config):
        raise RuntimeError('private profile and configuration are required')
    if profile.read_text() != 'user-db:tamprobe\n':
        raise RuntimeError('expected a unique temporary dconf database')
    if not env.get('DBUS_SESSION_BUS_ADDRESS') or not (root / 'run' / env['WAYLAND_DISPLAY']).exists():
        raise RuntimeError('private bus and compositor are required')


verify_isolation()
run('gsettings', 'set', 'org.gnome.desktop.interface', 'color-scheme', 'prefer-dark')
database = root / 'config/dconf/tamprobe'
deadline = time.monotonic() + 5
while not database.is_file() and time.monotonic() < deadline:
    time.sleep(.05)
if not database.is_file() or run('dconf', 'read', '/org/gnome/desktop/interface/color-scheme') != "'prefer-dark'":
    raise RuntimeError('temporary dconf database was not initialized')
services = []
for process in Path('/proc').iterdir():
    if not process.name.isdigit():
        continue
    try:
        if b'dconf-service' not in (process / 'cmdline').read_bytes():
            continue
        environment = (process / 'environ').read_bytes().split(b'\0')
        if (('DCONF_PROFILE=' + str(root / 'profile')).encode() in environment and
                ('XDG_CONFIG_HOME=' + str(root / 'config')).encode() in environment):
            services.append(process.name)
    except (OSError, PermissionError):
        continue
if len(services) != 1:
    raise RuntimeError('cannot verify the private dconf service environment')

with (root / 'portal.log').open('w') as log:
    portal = subprocess.Popen(['/usr/lib/xdg-desktop-portal'], env=env, stdout=log, stderr=log)
    app = None
    try:
        time.sleep(2)
        app = subprocess.Popen([str(root / 'probe')], env=env, stdout=subprocess.PIPE, stderr=log, text=True)
        def wait_color(expected):
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if select.select([app.stdout], [], [], .5)[0] and app.stdout.readline().strip() == expected:
                    return
                if app.poll() is not None:
                    break
            raise RuntimeError('portal did not deliver expected palette ' + expected)
        wait_color(dark)
        run('gsettings', 'set', 'org.gnome.desktop.interface', 'color-scheme', 'prefer-light')
        wait_color(light)
        if run('dconf', 'read', '/org/gnome/desktop/interface/color-scheme') != "'prefer-light'":
            raise RuntimeError('temporary preference was not updated')
        print('temporary database and dark-to-light portal change verified')
    finally:
        if app:
            app.terminate()
            app.wait(timeout=5)
            app.stdout.close()
        portal.terminate()
        portal.wait(timeout=5)
