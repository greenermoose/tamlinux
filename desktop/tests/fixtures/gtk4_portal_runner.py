"""Private D-Bus child for the opt-in GTK portal test; never run in a user bus."""
import os
import json
from pathlib import Path
import re
import select
import subprocess
import sys
import time

root = Path(sys.argv[1])
dark, light = sys.argv[2:4]
palettes = json.loads(sys.argv[4])
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
        def wait_color(mode, expected):
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if select.select([app.stdout], [], [], .5)[0]:
                    values = app.stdout.readline().split()
                    if len(values) == 25 and ' '.join(values[:4]) == expected and values[4] == '1':
                        value = palettes[mode]['background']
                        text_color = ' '.join(f'{int(value[i:i+2], 16)/255:.3f}' for i in (1, 3, 5)) + ' 1.000'
                        if ' '.join(values[17:21]) == text_color and ' '.join(values[21:25]) == text_color:
                            return [int(value) for value in values[5:17]]
                if app.poll() is not None:
                    break
            raise RuntimeError('portal did not deliver expected palette ' + expected)
        def verify_pixels(mode, bounds):
            time.sleep(.2)
            image = subprocess.run(['grim', '-o', 'HEADLESS-1', '-t', 'ppm', '-'], env=env,
                                   capture_output=True, check=True, timeout=10).stdout
            header = re.match(rb'P6\s+(\d+)\s+(\d+)\s+255\s', image)
            if not header:
                raise RuntimeError('invalid screenshot')
            width, height = map(int, header.groups())
            pixels = image[header.end():]
            if len(pixels) != width * height * 3:
                raise RuntimeError('invalid screenshot size')
            palette = palettes[mode]
            for index, role in enumerate(('surface', 'accent', 'danger')):
                x, y, w, h = bounds[index * 4:index * 4 + 4]
                if not (0 <= x < x+w <= width and 0 <= y < y+h <= height):
                    raise RuntimeError('invalid widget bounds')
                sample = b''.join(pixels[(row*width+x)*3:(row*width+x+w)*3] for row in range(y, y+h))
                expected = bytes.fromhex(palette[role][1:])
                if sum(sample[i:i+3] == expected for i in range(0, len(sample), 3)) < 100:
                    raise RuntimeError(mode + ' ' + role + ' widget fill did not render the token')
        verify_pixels('dark', wait_color('dark', dark))
        run('gsettings', 'set', 'org.gnome.desktop.interface', 'color-scheme', 'prefer-light')
        verify_pixels('light', wait_color('light', light))
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
