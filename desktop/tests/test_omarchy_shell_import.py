"""The one-time conversion of the Omarchy shell's shell.json (plan 18 step 0.3.2 item 6)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP / "adapters"))

import omarchy_shell_import as conversion  # noqa: E402

SCRIPT = DESKTOP / "adapters" / "omarchy_shell_import.py"
FIXTURE = DESKTOP / "fixtures" / "omarchy-shell" / "shell.json"
DEFAULT_LAYOUT = DESKTOP / "shell" / "bar" / "default-layout.json"


def bar(layout, **extra):
    return {"bar": {"layout": layout, **extra}}


class ConversionTests(unittest.TestCase):
    def test_todays_shell_json_gives_the_default_layout(self):
        layout, settings, notes = conversion.convert(json.loads(FIXTURE.read_text(encoding="utf-8")))
        default = json.loads(DEFAULT_LAYOUT.read_text(encoding="utf-8"))
        self.assertEqual(layout["layout"], default["layout"])
        self.assertEqual(layout["centerAnchor"], default["centerAnchor"])
        self.assertEqual((layout["position"], layout["transparent"]), ("top", False))
        self.assertEqual(notes, [])
        self.assertEqual(settings, {"version": 1, "entries": {"fred.clock": {
            "id": "fred.clock", "format": "dddd HH:mm", "formatAlt": "d MMMM yyyy",
            "verticalFormat": "HH\n—\nmm", "birthYear": 1970, "lifeExpectancy": 90}}})

    def test_every_omarchy_widget_maps_and_others_are_named(self):
        layout, _, notes = conversion.convert(bar({
            "left": [{"id": "omarchy.power"}, {"id": "omarchy.clock"}, {"id": "acme.thing"}],
            "center": [{"id": "fred.clock"}, {"id": "fred.clock"}],
            "right": "nope",
        }))
        self.assertEqual(layout["layout"], {"left": [{"id": "tamlinux.power"}],
                                            "center": [{"id": "fred.clock"}], "right": []})
        self.assertEqual(notes, [
            "left: 'omarchy.clock' has no Tamlinux widget, left out",
            "left: 'acme.thing' has no Tamlinux widget, left out",
            "center: fred.clock appears twice, second left out",
            "right: not a list, left empty",
        ])
        self.assertEqual(set(conversion.WIDGETS.values()), {
            "tamlinux.menu", "tamlinux.indicators", "tamlinux.keyboard-layout", "tamlinux.tray",
            "tamlinux.audio", "tamlinux.bluetooth", "tamlinux.network", "tamlinux.power"})

    def test_position_transparency_and_anchor(self):
        layout, _, notes = conversion.convert(bar({}, position="left", transparent=True,
                                                  centerAnchor="omarchy.indicators"))
        self.assertEqual((layout["position"], layout["transparent"], layout["centerAnchor"]),
                         ("top", True, "tamlinux.indicators"))
        self.assertEqual(notes, ["position 'left' is not top or bottom, read as top"])
        layout, _, _ = conversion.convert(bar({}, position="bottom", transparent="yes",
                                              centerAnchor="acme.thing"))
        self.assertEqual((layout["position"], layout["transparent"], layout["centerAnchor"]),
                         ("bottom", False, ""))

    def test_settings_keep_plain_values_only(self):
        _, settings, notes = conversion.convert(bar({"center": [
            {"id": "fred.clock", "format": "HH:mm", "nested": {"a": 1}, "list": [1]}]}))
        self.assertEqual(settings["entries"], {"fred.clock": {"id": "fred.clock", "format": "HH:mm"}})
        self.assertEqual(notes, ["fred.clock: setting nested is not a plain value, left out",
                                 "fred.clock: setting list is not a plain value, left out"])

    def test_a_setting_the_shell_would_refuse_fails_the_conversion(self):
        with self.assertRaises(conversion.ConversionError):
            conversion.convert(bar({"center": [{"id": "fred.clock", "format": "x" * 513}]}))

    def test_no_bar_is_an_error(self):
        for document in ([], {}, {"bar": {}}, {"bar": {"layout": []}}):
            with self.assertRaises(conversion.ConversionError):
                conversion.convert(document)


class CommandTests(unittest.TestCase):
    def run_import(self, *args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, timeout=20)

    def test_writes_both_files_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "tamlinux" / "shell"
            done = self.run_import(FIXTURE, out)
            self.assertEqual(done.returncode, 0, done.stderr)
            layout = json.loads((out / "layout.json").read_text(encoding="utf-8"))
            settings = json.loads((out / "settings.json").read_text(encoding="utf-8"))
            self.assertEqual(layout["position"], "top")
            self.assertEqual(list(settings["entries"]), ["fred.clock"])
            before = (out / "layout.json").read_text(encoding="utf-8")
            again = self.run_import(FIXTURE, out)
            self.assertEqual(again.returncode, 1)
            self.assertIn("will not overwrite", again.stderr)
            self.assertEqual((out / "layout.json").read_text(encoding="utf-8"), before)

    def test_unreadable_input_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            bad = Path(temporary) / "shell.json"
            bad.write_text("{", encoding="utf-8")
            out = Path(temporary) / "out"
            done = self.run_import(bad, out)
            self.assertEqual(done.returncode, 1)
            self.assertFalse(out.exists())
            self.assertEqual(self.run_import().returncode, 2)


if __name__ == "__main__":
    unittest.main()
