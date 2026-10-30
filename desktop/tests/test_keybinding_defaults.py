"""Exercise the actual Lua defaults with the same scan used by the explorer."""
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / 'commands/tam-menu-keybindings/tam-menu-keybindings'
REMINDER = ROOT / 'commands/tam-reminder/tam-reminder'
CATALOG = ROOT / 'desktop/shell/services/keybindings/BindingCatalog.js'


class DefaultsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        base = Path(cls.temp.name)
        cfg = base / 'tamlinux/session'
        cfg.mkdir(parents=True)
        bindir = base / 'bin'
        bindir.mkdir()
        helper = bindir / 'tam-cmd-present'
        helper.write_text('#!/bin/sh\ncommand -v "$1" >/dev/null\n')
        helper.chmod(0o755)
        source = ROOT / 'desktop/session'
        modules = ['media', 'clipboard', 'tiling', 'utilities', 'voxtype', 'applications']
        (cfg / 'hyprland.lua').write_text(
            'package.path = ' + json.dumps(str(source / '?.lua') + ';' + str(source / '?/init.lua') + ';') + ' .. package.path\n'
            + 'TAMLINUX_HYPR_ROOT = ' + json.dumps(str(source)) + '\n'
            + 'tamlinux_preinstalled_bindings = true\nrequire("hypr.tamlinux.helpers")\n'
            + ''.join('require("hypr.tamlinux.bindings.' + m + '")\n' for m in modules))
        env = dict(os.environ, XDG_CONFIG_HOME=str(base), PATH=str(bindir) + os.pathsep + os.environ['PATH'], DEBUG='1')
        run = subprocess.run([str(SCAN), '--scan'], env=env, text=True, capture_output=True, check=True)
        if run.stderr:
            raise AssertionError(run.stderr)
        cls.rows = list(csv.reader(io.StringIO(run.stdout), delimiter='\t'))
        if len(cls.rows) < 100:
            raise AssertionError('Incomplete Lua scan')
        raw = subprocess.check_output(['node', '-e', 'process.stdout.write(JSON.stringify(require(process.argv[1]).entries))', str(CATALOG)], text=True)
        cls.catalog = json.loads(raw)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_no_default_keyboard_chord_exceeds_three_physical_keys(self):
        shifted = {'less', 'greater', 'colon', 'quotedbl', 'question', 'exclam', 'at', 'numbersign', 'dollar', 'percent', 'asciicircum', 'ampersand', 'asterisk', 'parenleft', 'parenright'}
        too_long = []
        for mask, description, key, *_ in self.rows:
            modifiers = int(mask).bit_count()
            extra_shift = int(key.lower() in shifted and not (int(mask) & 1))
            if modifiers + extra_shift > 2 and not key.startswith(('mouse:', 'switch:')):
                too_long.append((description, mask, key))
        self.assertEqual(too_long, [])

    def test_no_unintended_duplicate_default_chords(self):
        chords = {}
        allowed = {(8, 'tab'), (9, 'tab'), (0, 'f9')}
        for mask, description, key, *_ in self.rows:
            chord = (int(mask), key.lower())
            chords.setdefault(chord, []).append(description)
        self.assertEqual({k: v for k, v in chords.items() if len(v) > 1 and k not in allowed}, {})

    def test_start_and_resize_mouse_bindings_are_portable_defaults(self):
        right_click = [row for row in self.rows if row[2] == 'mouse:273']
        self.assertEqual(right_click, [
            ['64', 'Start menu', 'mouse:273', 'exec', 'tam-menu toggle start'],
            ['72', 'Resize window', 'mouse:273', 'lua', 'hl.dsp.window.resize()'],
        ])

    def test_catalog_covers_every_resolved_default_binding(self):
        entries = {(str(e['mask']), e['key'], e['dispatcher'], e['arg']) for e in self.catalog}
        missing = [(r[1], r[2]) for r in self.rows if len(r) >= 5 and r[3] and r[4] and (r[0], r[2], r[3], r[4]) not in entries]
        self.assertEqual(missing, [])
        self.assertTrue(all(e['action'] and e['why'] and e['mnemonic'] for e in self.catalog))

    def test_clear_reminders_requires_explicit_confirmation(self):
        base = Path(self.temp.name)
        bindir = base / 'bin'
        selector = bindir / 'tam-menu-select'
        marker = base / 'cleared'
        shell = base / 'shell/services/reminders'
        shell.mkdir(parents=True, exist_ok=True)
        helper = shell / 'reminder.sh'
        helper.write_text('#!/bin/sh\nprintf "%s" "$1" > "$TEST_MARKER"\n')
        helper.chmod(0o755)
        env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ['PATH'], TAMLINUX_SHELL_DIR=str(base / 'shell'), TEST_MARKER=str(marker))
        for selection, expected in [('Cancel', False), ('Clear reminders', True)]:
            selector.write_text('#!/bin/sh\nprintf "%s\\n" ' + json.dumps(selection) + '\n')
            selector.chmod(0o755)
            if marker.exists():
                marker.unlink()
            subprocess.run([str(REMINDER), '--confirm-clear'], env=env, check=True)
            self.assertEqual(marker.exists(), expected)
            if expected:
                self.assertEqual(marker.read_text(), 'clear')
