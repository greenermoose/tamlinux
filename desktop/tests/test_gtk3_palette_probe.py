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
                            def luminance(value):
                                channels = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
                                return sum((c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4) * weight
                                           for c, weight in zip(channels, (.2126, .7152, .0722)))
                            low, high = sorted((luminance(colors['foreground']), luminance(colors['surface'])))
                            self.assertGreaterEqual((high + .05) / (low + .05), 4.5)
                            theme.call('set', 'tamarack-' + variant)
                            (config / 'gtk-3.0/gtk.css').write_bytes((theme.current / 'theme/gtk3.css').read_bytes())
                            app = subprocess.Popen([str(binary)], env=env, stdout=subprocess.PIPE,
                                                   stderr=subprocess.DEVNULL, text=True)
                            try:
                                self.assertTrue(select.select([app.stdout], [], [], 10)[0], 'GTK app did not report a label')
                                actual = list(map(float, app.stdout.readline().split()))
                                expected = [int(colors['foreground'][i:i+2], 16) / 255 for i in (1, 3, 5)] + [1.0]
                                self.assertEqual(len(actual), 20)
                                for measured, target in zip(actual[:4], expected):
                                    self.assertAlmostEqual(measured, target, places=3)
                                self.assertEqual(actual[8:11], [1.0, 1.0, 1.0], 'entry bounds, focus or selection unavailable')
                                for measured, target in zip(actual[11:15], expected):
                                    self.assertAlmostEqual(measured, target, places=3, msg='normal entry text did not use foreground')
                                self.assertEqual(actual[19], 1.0, 'normal entry bounds unavailable')
                                image = subprocess.check_output(['grim', '-o', 'HEADLESS-1', '-t', 'ppm', '-'], env=env, timeout=10)
                                header = re.match(rb'P6\s+(\d+)\s+(\d+)\s+255\s', image)
                                self.assertIsNotNone(header, 'invalid PPM screenshot')
                                width, height = map(int, header.groups())
                                pixels = image[header.end():]
                                self.assertEqual(len(pixels), width * height * 3)
                                expected_bg = bytes.fromhex(colors['background'][1:])
                                count = sum(pixels[i:i+3] == expected_bg for i in range(0, len(pixels), 3))
                                self.assertGreater(count, width * height // 2, 'window background did not use token')
                                x, y, w, h = map(int, actual[4:8])
                                self.assertTrue(0 <= x < x+w <= width and 0 <= y < y+h <= height)
                                entry_pixels = b''.join(pixels[(row*width+x)*3:(row*width+x+w)*3] for row in range(y, y+h))
                                accent = bytes.fromhex(colors['accent'][1:])
                                coords = [(i % w, i // w) for i in range(w*h) if entry_pixels[3*i:3*i+3] == accent]
                                self.assertGreater(len(coords), 100, 'selected entry did not use accent fill')
                                left, right = min(p[0] for p in coords), max(p[0] for p in coords)
                                top, bottom = min(p[1] for p in coords), max(p[1] for p in coords)
                                selected_text = sum(entry_pixels[(row*w+col)*3:(row*w+col)*3+3] == expected_bg
                                                    for row in range(top, bottom+1) for col in range(left, right+1))
                                self.assertGreater(selected_text, 0, 'selected entry text did not use selection foreground')
                                x, y, w, h = map(int, actual[15:19])
                                self.assertTrue(0 <= x < x+w <= width and 0 <= y < y+h <= height)
                                normal_pixels = b''.join(pixels[(row*width+x)*3:(row*width+x+w)*3] for row in range(y, y+h))
                                surface = bytes.fromhex(colors['surface'][1:])
                                foreground = bytes.fromhex(colors['foreground'][1:])
                                self.assertGreater(sum(normal_pixels[i:i+3] == surface for i in range(0, len(normal_pixels), 3)), 100,
                                                   'normal entry did not use token surface')
                                self.assertGreater(sum(normal_pixels[i:i+3] == foreground for i in range(0, len(normal_pixels), 3)), 0,
                                                   'normal entry text did not render in foreground colour')
                            finally:
                                app.terminate()
                                app.wait(timeout=5)
                                app.stdout.close()
                finally:
                    compositor.terminate()
                    compositor.wait(timeout=5)
