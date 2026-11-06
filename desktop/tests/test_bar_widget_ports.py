"""Source checks for the ported bar indicators, keyboard layout, and tray widgets."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

WIDGET_FILES: list[tuple[str, str, bool]] = [
    ("desktop/shell/bar/widgets/Indicators.qml", "plugins/bar/widgets/Indicators.qml", False),
    ("desktop/shell/bar/indicators/Dnd.qml", "plugins/bar/indicators/Dnd.qml", False),
    ("desktop/shell/bar/indicators/NightLight.qml", "plugins/bar/indicators/NightLight.qml", False),
    ("desktop/shell/bar/indicators/Reminder.qml", "plugins/bar/indicators/Reminder.qml", False),
    ("desktop/shell/bar/indicators/ScreenRecording.qml", "plugins/bar/indicators/ScreenRecording.qml", False),
    ("desktop/shell/bar/indicators/StayAwake.qml", "plugins/bar/indicators/StayAwake.qml", False),
    # KeyboardLayout.qml left this list at plan 18 step 0.3.1, when it moved
    # onto the compositor facade; test_compositor's boundary test covers it.
    ("desktop/shell/bar/widgets/KeyboardLayoutModel.js", "plugins/bar/widgets/KeyboardLayoutModel.js", True),
    ("desktop/shell/bar/widgets/Tray.qml", "plugins/bar/widgets/Tray.qml", False),
    ("desktop/shell/bar/widgets/TrayModel.js", "plugins/bar/widgets/TrayModel.js", False),
]


def expected_header(orig_path: str, unchanged: bool) -> list[str]:
    change_line = (
        "// Unchanged."
        if unchanged
        else "// Changes: owned module, id, and command names."
    )
    return [
        f"// Ported from omarchy 4.0.4 shell/{orig_path}\n",
        "// (MIT, Copyright (c) David Heinemeier Hansson; see ../../services/LICENSE-omarchy).\n",
        f"{change_line}\n",
        "\n",
    ]


class BarWidgetPortTests(unittest.TestCase):
    def test_files_exist_are_utf8_and_end_with_single_newline(self):
        for new_path, _, _ in WIDGET_FILES:
            path = ROOT / new_path
            self.assertTrue(path.is_file(), f"{new_path} does not exist")
            raw = path.read_bytes()
            self.assertTrue(raw.endswith(b"\n"), f"{new_path} does not end with newline")
            self.assertFalse(raw.endswith(b"\n\n"), f"{new_path} ends with multiple newlines")
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                self.fail(f"{new_path} is not valid UTF-8: {exc}")

    def test_files_have_exact_four_line_headers(self):
        for new_path, orig_path, unchanged in WIDGET_FILES:
            path = ROOT / new_path
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            self.assertGreaterEqual(len(lines), 4, f"{new_path} has fewer than 4 lines")
            expected = expected_header(orig_path, unchanged)
            self.assertEqual(lines[:4], expected, f"Header mismatch in {new_path}")
            self.assertEqual(lines[3], "\n", f"Line 4 is not empty in {new_path}")

    def test_bodies_contain_zero_omarchy_and_dictation(self):
        for new_path, _, _ in WIDGET_FILES:
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            for word in ("omarchy", "dictation"):
                matches = re.findall(re.escape(word), body, re.IGNORECASE)
                self.assertEqual(
                    len(matches),
                    0,
                    f"Found {len(matches)} occurrences of {word!r} in {new_path}",
                )

    def test_bodies_drop_qs_imports(self):
        for new_path, _, _ in WIDGET_FILES:
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            self.assertNotIn("qs.Commons", body, f"{new_path} contains qs.Commons")
            self.assertNotIn("qs.Ui", body, f"{new_path} contains qs.Ui")

    def test_indicators_default_list_and_indicator_files_exist(self):
        indicators_path = ROOT / "desktop/shell/bar/widgets/Indicators.qml"
        lines = indicators_path.read_text(encoding="utf-8").splitlines(keepends=True)
        body = "".join(lines[4:])
        match = re.search(r"readonly property var defaultIndicatorEntries:\s*(\[[^\]]+\])", body)
        self.assertIsNotNone(match, "defaultIndicatorEntries property not found in Indicators.qml")
        raw_list = match.group(1)
        entries = [s.strip().strip('"').strip("'") for s in raw_list.strip("[]").split(",") if s.strip()]
        expected_entries = ["ScreenRecording", "Reminder", "NightLight", "Dnd", "StayAwake"]
        self.assertEqual(entries, expected_entries)
        for name in expected_entries:
            indicator_file = ROOT / f"desktop/shell/bar/indicators/{name}.qml"
            self.assertTrue(indicator_file.is_file(), f"Missing indicator file {indicator_file}")

    def test_tray_uses_owned_by_shell(self):
        tray_model_body = (ROOT / "desktop/shell/bar/widgets/TrayModel.js").read_text(encoding="utf-8")
        self.assertIn("function ownedByShell(item, layout)", tray_model_body)
        self.assertIn("ownedByShell: ownedByShell", tray_model_body)
        tray_qml_body = (ROOT / "desktop/shell/bar/widgets/Tray.qml").read_text(encoding="utf-8")
        self.assertIn("function ownedByShell(item)", tray_qml_body)

if __name__ == "__main__":
    unittest.main()
