"""Opt-in GTK 3 surface proof in a private software-rendered compositor."""
import os
from pathlib import Path
import re
import select
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
class Gtk3PaletteProbe(unittest.TestCase):
    def test_window_uses_token_colours(self):
        for command in ('sway', 'grim', 'cc', 'pkg-config'):
            if not shutil.which(command):
                self.skipTest(f'{command} is unavailable')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'gtk+-3.0'], text=True, capture_output=True)
        if flags.returncode:
            self.skipTest('GTK 3 development files are unavailable')
        tokens = tomllib.loads((DESKTOP / 'assets/tamarack.toml').read_text())
        theme = theme_tests.ThemeOwnership('test_all_bundled_themes_generate_without_inherited_tools')
        theme.setUp()
        self.addCleanup(theme.doCleanups)
        with tempfile.TemporaryDirectory(prefix='tamlinux-gtk3-proof-') as temporary:
            root = Path(temporary)
            runtime = root / 'run'; runtime.mkdir(mode=0o700)
            home = root / 'home'; home.mkdir()
            config = root / 'config'; (config / 'gtk-3.0').mkdir(parents=True)
            binary = root / 'probe'
            subprocess.run(['cc', str(DESKTOP / 'tests/fixtures/gtk3_palette_probe.c'), '-o', str(binary),
                            *shlex.split(flags.stdout)], check=True, timeout=30)
            sway_config = root / 'sway.conf'; sway_config.write_text('output HEADLESS-1 resolution 320x240\n')
            env = {'HOME': str(home), 'XDG_CONFIG_HOME': str(config), 'XDG_RUNTIME_DIR': str(runtime),
                   'PATH': os.environ.get('PATH', '/usr/bin'), 'WLR_BACKENDS': 'headless',
                   'WLR_LIBINPUT_NO_DEVICES': '1', 'WLR_RENDERER': 'pixman'}
            with (root / 'sway.log').open('w+') as log:
                compositor = subprocess.Popen(['sway', '-c', str(sway_config)], env=env, stdout=log, stderr=log)
                try:
                    deadline = time.monotonic() + 10
                    socket = None
                    while time.monotonic() < deadline and compositor.poll() is None:
                        sockets = [p for p in runtime.glob('wayland-[0-9]*') if not p.name.endswith('.lock')]
                        if sockets:
                            socket = sockets[0].name
                            break
                        time.sleep(.1)
                    if not socket:
                        log.seek(0)
                        self.fail('headless compositor did not start: ' + log.read()[-1000:])
                    env.update({'WAYLAND_DISPLAY': socket, 'GDK_BACKEND': 'wayland', 'GSETTINGS_BACKEND': 'memory'})
                    for variant in ('dark', 'light'):
                        with self.subTest(variant=variant):
                            colors = tokens[variant]
                            theme.call('set', 'tamarack-' + variant)
                            (config / 'gtk-3.0/gtk.css').write_bytes((theme.current / 'theme/gtk3.css').read_bytes())
                            app = subprocess.Popen([str(binary)], env=env, stdout=subprocess.PIPE,
                                                   stderr=subprocess.DEVNULL, text=True)
                            try:
                                self.assertTrue(select.select([app.stdout], [], [], 10)[0], 'GTK app did not report a label')
                                actual = list(map(float, app.stdout.readline().split()))
                                expected = [int(colors['foreground'][i:i+2], 16) / 255 for i in (1, 3, 5)] + [1.0]
                                self.assertEqual(len(actual), 4)
                                for measured, target in zip(actual, expected):
                                    self.assertAlmostEqual(measured, target, places=3)
                                image = subprocess.check_output(['grim', '-o', 'HEADLESS-1', '-t', 'ppm', '-'], env=env, timeout=10)
                                header = re.match(rb'P6\s+(\d+)\s+(\d+)\s+255\s', image)
                                self.assertIsNotNone(header, 'invalid PPM screenshot')
                                width, height = map(int, header.groups())
                                pixels = image[header.end():]
                                self.assertEqual(len(pixels), width * height * 3)
                                expected_bg = bytes.fromhex(colors['background'][1:])
                                count = sum(pixels[i:i+3] == expected_bg for i in range(0, len(pixels), 3))
                                self.assertGreater(count, width * height // 2, 'window background did not use token')
                            finally:
                                app.terminate()
                                app.wait(timeout=5)
                                app.stdout.close()
                finally:
                    compositor.terminate()
                    compositor.wait(timeout=5)
