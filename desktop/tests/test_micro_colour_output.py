"""Check actual Micro 256-colour conversion of generated Tamarack pairs.

Micro is an optional external test dependency. Pair conversion and actual
keyboard-selection output are tested separately in isolated pseudo-terminals.
"""
import fcntl
import os
import pty
import re
import select
import shutil
import struct
import subprocess
import termios
import time
import unittest

import test_theme_ownership as theme_tests


def xterm_rgb(index):
    # The first 16 colours are terminal-configurable and cannot establish a
    # portable contrast result without inspecting that terminal's palette.
    if 16 <= index <= 231:
        value = index - 16
        levels = (0, 95, 135, 175, 215, 255)
        return tuple(levels[i] for i in (value // 36, value // 6 % 6, value % 6))
    if 232 <= index <= 255:
        return (8 + 10 * (index - 232),) * 3
    raise ValueError(f'Cannot assume RGB for terminal palette index {index}')


def luminance(rgb):
    values = [channel / 255 for channel in rgb]
    return sum((v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4) * w
               for v, w in zip(values, (.2126, .7152, .0722)))


@unittest.skipUnless(shutil.which('micro'), 'Micro is needed for terminal colour conversion')
class MicroColourOutput(unittest.TestCase):
    def test_selection_uses_generated_pair_in_both_colour_modes(self):
        fixture = theme_tests.ThemeOwnership('test_all_bundled_themes_generate_without_inherited_tools')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config = fixture.base / 'micro-selection'
        (config / 'colorschemes').mkdir(parents=True)
        sample = fixture.base / 'selection.txt'
        sample.write_text('TEXTMARKER\n')
        for variant in ('dark', 'light'):
            fixture.call('set', 'tamarack-' + variant)
            scheme = (fixture.current / 'theme/micro.micro').read_text()
            selection = re.search(r'^color-link selection "(#[0-9a-fA-F]{6}),(#[0-9a-fA-F]{6})"$', scheme, re.MULTILINE)
            self.assertIsNotNone(selection)
            (config / 'colorschemes/tamlinux.micro').write_text(scheme)
            for mode in ('on', 'off'):
                with self.subTest(variant=variant, truecolour=mode):
                    master, slave = pty.openpty()
                    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 12, 60, 0, 0))

                    def session():
                        os.setsid()
                        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

                    env = os.environ | {'TERM': 'xterm-256color', 'HOME': str(fixture.base)}
                    process = subprocess.Popen([shutil.which('micro'), '-config-dir', str(config),
                        '-colorscheme', 'tamlinux', '-truecolor', mode, '-cursorline', 'false', str(sample)],
                        stdin=slave, stdout=slave, stderr=slave, env=env, preexec_fn=session)
                    os.close(slave)
                    output = b''
                    stage = 0
                    deadline = time.monotonic() + 5
                    try:
                        while time.monotonic() < deadline and process.poll() is None:
                            if select.select([master], [], [], .1)[0]:
                                try:
                                    output += os.read(master, 65536)
                                except OSError:
                                    break
                            if stage == 0 and b'TEXTMARKER' in output:
                                output = b''
                                os.write(master, b'\x1b[1;2C')  # Shift-right selects the first character.
                                stage = 1
                            elif stage == 1 and b'T' in output:
                                os.write(master, b'\x11')
                                stage = 2
                        if process.poll() is None:
                            process.terminate()
                        process.wait(timeout=2)
                    finally:
                        if process.poll() is None:
                            process.kill()
                            process.wait()
                        os.close(master)
                    self.assertEqual(stage, 2, output[-500:])
                    self.assertEqual(process.returncode, 0, output[-500:])
                    if mode == 'on':
                        match = re.search(rb'\x1b\[38;2;(\d+);(\d+);(\d+);48;2;(\d+);(\d+);(\d+)mT', output)
                        self.assertIsNotNone(match, output[-500:])
                        values = tuple(map(int, match.groups()))
                        expected = tuple(int(value[i:i+2], 16) for value in selection.groups() for i in (1, 3, 5))
                        self.assertEqual(values, expected)
                        foreground, background = values[:3], values[3:]
                    else:
                        match = re.search(rb'\x1b\[38;5;(\d+);48;5;(\d+)mT', output)
                        self.assertIsNotNone(match, output[-500:])
                        foreground, background = (xterm_rgb(int(index)) for index in match.groups())
                    low, high = sorted((luminance(foreground), luminance(background)))
                    self.assertGreaterEqual((high + .05) / (low + .05), 4.5)

    def test_generated_pairs_survive_xterm_256_colour_conversion(self):
        fixture = theme_tests.ThemeOwnership('test_all_bundled_themes_generate_without_inherited_tools')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config = fixture.base / 'micro-probe'
        (config / 'colorschemes').mkdir(parents=True)
        sample = fixture.base / 'sample.txt'
        sample.write_text('TEXTMARKER\n')
        for variant in ('dark', 'light'):
            fixture.call('set', 'tamarack-' + variant)
            scheme = (fixture.current / 'theme/micro.micro').read_text()
            roles = re.findall(r'^color-link (\S+) "(?:bold )?(#[0-9a-fA-F]{6}),(#[0-9a-fA-F]{6})"$', scheme, re.MULTILINE)
            self.assertEqual(len(roles), 22, scheme)
            # Identical pairs use the same conversion, so only launch once per pair.
            for foreground, background in sorted({(fg, bg) for _, fg, bg in roles}):
                with self.subTest(variant=variant, foreground=foreground, background=background):
                    (config / 'colorschemes/check.micro').write_text(f'color-link default "{foreground},{background}"\n')
                    master, slave = pty.openpty()
                    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 12, 60, 0, 0))

                    def session():
                        os.setsid()
                        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

                    env = os.environ | {'TERM': 'xterm-256color', 'HOME': str(fixture.base)}
                    process = subprocess.Popen([shutil.which('micro'), '-config-dir', str(config),
                        '-colorscheme', 'check', '-truecolor', 'off', '-cursorline', 'false', str(sample)],
                        stdin=slave, stdout=slave, stderr=slave, env=env, preexec_fn=session)
                    os.close(slave)
                    output = b''
                    sent = False
                    deadline = time.monotonic() + 5
                    try:
                        while time.monotonic() < deadline and process.poll() is None:
                            if select.select([master], [], [], .1)[0]:
                                try:
                                    output += os.read(master, 65536)
                                except OSError:
                                    break
                            if not sent and b'TEXTMARKER' in output:
                                os.write(master, b'\x11')
                                sent = True
                        if process.poll() is None:
                            process.terminate()
                        process.wait(timeout=2)
                    finally:
                        if process.poll() is None:
                            process.kill()
                            process.wait()
                        os.close(master)
                    self.assertEqual(process.returncode, 0, output[-500:])
                    match = re.search(rb'\x1b\[38;5;(\d+);48;5;(\d+)m[^\x1b]*TEXTMARKER', output)
                    self.assertIsNotNone(match, output[-500:])
                    low, high = sorted(luminance(xterm_rgb(int(index))) for index in match.groups())
                    self.assertGreaterEqual((high + .05) / (low + .05), 4.5)
