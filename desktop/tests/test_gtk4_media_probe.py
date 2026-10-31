"""Opt-in proof of a GTK 4.20+ media query in a private compositor.

The probe changes GtkSettings directly. It does not prove portal propagation,
personal CSS integration, application coverage or safe installed theme changes.
"""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time
import tomllib
import unittest

import test_theme_ownership as theme_tests

DESKTOP = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('TAMLINUX_GTK_PROOF') == '1', 'opt-in headless GTK proof')
class Gtk4MediaProbe(unittest.TestCase):
    def test_generated_palette_changes_in_running_libadwaita_window(self):
        for command in ('sway', 'cc', 'pkg-config'):
            if not shutil.which(command):
                self.skipTest(f'{command} is unavailable')
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
        for variant in ('dark', 'light'):
            theme.call('set', 'tamarack-' + variant)
            styles[variant] = (theme.current / 'theme/gtk4.css').read_text()
        with tempfile.TemporaryDirectory(prefix='tamlinux-gtk-media-') as temporary:
            root = Path(temporary)
            runtime = root / 'run'; runtime.mkdir(mode=0o700)
            home = root / 'home'; home.mkdir()
            config = root / 'config'; (config / 'gtk-4.0').mkdir(parents=True)
            css = ''.join(f'@media (prefers-color-scheme: {mode}) {{\n{styles[mode]}\n}}\n'
                          for mode in ('dark', 'light'))
            (config / 'gtk-4.0/gtk.css').write_text(css)
            binary = root / 'probe'
            subprocess.run(['cc', '-Wno-deprecated-declarations', str(DESKTOP / 'tests/fixtures/gtk4_media_probe.c'),
                            '-o', str(binary), *shlex.split(flags.stdout)], check=True, timeout=30)
            sway_config = root / 'sway.conf'; sway_config.write_text('output HEADLESS-1 resolution 320x240\n')
            env = {'HOME': str(home), 'XDG_CONFIG_HOME': str(config), 'XDG_RUNTIME_DIR': str(runtime),
                   'PATH': os.environ.get('PATH', '/usr/bin'), 'WLR_BACKENDS': 'headless',
                   'WLR_LIBINPUT_NO_DEVICES': '1', 'WLR_RENDERER': 'pixman', 'GDK_BACKEND': 'wayland',
                   'GSETTINGS_BACKEND': 'memory', 'GSK_RENDERER': 'cairo'}
            with (root / 'sway.log').open('w+') as log:
                compositor = subprocess.Popen(['sway', '-c', str(sway_config)], env=env, stdout=log, stderr=log)
                try:
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline and compositor.poll() is None:
                        sockets = [p for p in runtime.glob('wayland-[0-9]*') if not p.name.endswith('.lock')]
                        if sockets:
                            break
                        time.sleep(.1)
                    else:
                        log.seek(0)
                        self.fail('headless compositor did not start: ' + log.read()[-1000:])
                    env['WAYLAND_DISPLAY'] = sockets[0].name
                    result = subprocess.run([str(binary)], env=env, capture_output=True, text=True, check=True, timeout=10)
                    rows = result.stdout.splitlines()
                    self.assertEqual(len(rows), 2, result.stderr)
                    for variant, row in zip(('dark', 'light'), rows):
                        actual = list(map(float, row.split()))
                        color = tokens[variant]['foreground']
                        expected = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)] + [1.0]
                        self.assertEqual(len(actual), 4)
                        for measured, target in zip(actual, expected):
                            self.assertAlmostEqual(measured, target, places=3, msg=variant)
                finally:
                    compositor.terminate()
                    compositor.wait(timeout=5)
