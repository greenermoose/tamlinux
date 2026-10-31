"""Opt-in GTK portal proof, with an isolated bus, display and dconf profile."""
import os
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest

import test_theme_ownership as theme_tests

DESKTOP = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('TAMLINUX_GTK_PROOF') == '1', 'opt-in headless GTK proof')
class Gtk4PortalProbe(unittest.TestCase):
    def test_generated_palette_follows_portal_without_restarting_window(self):
        for command in ('sway', 'grim', 'cc', 'pkg-config', 'dbus-run-session', 'dconf', 'gsettings'):
            if not shutil.which(command):
                self.skipTest(f'{command} is unavailable')
        if not Path('/usr/lib/xdg-desktop-portal').is_file():
            self.skipTest('desktop portal is unavailable')
        if subprocess.run(['pkg-config', '--atleast-version=4.20', 'gtk4']).returncode:
            self.skipTest('GTK 4.20 or newer is unavailable')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'libadwaita-1'], text=True, capture_output=True)
        if flags.returncode:
            self.skipTest('libadwaita development files are unavailable')
        tokens = tomllib.loads((DESKTOP / 'assets/tamarack.toml').read_text())
        theme = theme_tests.ThemeOwnership('test_all_bundled_themes_generate_without_inherited_tools')
        theme.setUp()
        self.addCleanup(theme.doCleanups)
        styles = {}
        for mode in ('dark', 'light'):
            theme.call('set', 'tamarack-' + mode)
            styles[mode] = (theme.current / 'theme/gtk4.css').read_text()
        with tempfile.TemporaryDirectory(prefix='tamlinux-portal-proof-') as temporary:
            root = Path(temporary)
            for directory in ('run', 'home', 'config/gtk-4.0', 'data', 'cache'):
                (root / directory).mkdir(parents=True, mode=0o700)
            (root / 'profile').write_text('user-db:tamprobe\n')
            css = ''.join(f'@media (prefers-color-scheme: {mode}) {{\n{styles[mode]}\n}}\n'
                          for mode in ('dark', 'light'))
            (root / 'config/gtk-4.0/gtk.css').write_text(css)
            subprocess.run(['cc', '-Wno-deprecated-declarations', str(DESKTOP / 'tests/fixtures/gtk4_portal_probe.c'),
                            '-o', str(root / 'probe'), *shlex.split(flags.stdout)], check=True, timeout=30)
            (root / 'sway.conf').write_text('output HEADLESS-1 resolution 320x240\n')
            env = {'HOME': str(root / 'home'), 'XDG_CONFIG_HOME': str(root / 'config'),
                   'XDG_RUNTIME_DIR': str(root / 'run'), 'XDG_DATA_HOME': str(root / 'data'),
                   'XDG_CACHE_HOME': str(root / 'cache'), 'DCONF_PROFILE': str(root / 'profile'),
                   'XDG_CURRENT_DESKTOP': 'sway', 'PATH': '/usr/local/bin:/usr/bin:/bin',
                   'WLR_BACKENDS': 'headless', 'WLR_LIBINPUT_NO_DEVICES': '1', 'WLR_RENDERER': 'pixman',
                   'GDK_BACKEND': 'wayland', 'GSK_RENDERER': 'cairo'}
            with (root / 'sway.log').open('w+') as log:
                compositor = subprocess.Popen(['sway', '-c', str(root / 'sway.conf')], env=env, stdout=log, stderr=log)
                try:
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline and compositor.poll() is None:
                        sockets = [p for p in (root / 'run').glob('wayland-[0-9]*') if not p.name.endswith('.lock')]
                        if sockets:
                            break
                        time.sleep(.1)
                    else:
                        log.seek(0)
                        self.fail('headless compositor did not start: ' + log.read()[-1000:])
                    env['WAYLAND_DISPLAY'] = sockets[0].name
                    def color(mode):
                        value = tokens[mode]['foreground']
                        return ' '.join(f'{int(value[i:i+2], 16)/255:.3f}' for i in (1, 3, 5)) + ' 1.000'
                    result = subprocess.run(['dbus-run-session', '--', sys.executable,
                                             str(DESKTOP / 'tests/fixtures/gtk4_portal_runner.py'), str(root),
                                             color('dark'), color('light'), json.dumps(tokens)], env=env, text=True,
                                            capture_output=True, timeout=45)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn('temporary database and dark-to-light portal change verified', result.stdout)
                finally:
                    compositor.terminate()
                    compositor.wait(timeout=5)
