"""Source checks for the ported bar indicators, keyboard layout, and tray widgets."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OMARCHY = Path("/usr/share/omarchy/shell")

COMMANDS = [
    "capture-screenrecording",
    "menu",
    "reminder",
]

CMD_PATTERN = re.compile(
    r"omarchy-("
    + "|".join(re.escape(c) for c in sorted(COMMANDS, key=len, reverse=True))
    + r")(?![a-z0-9-])"
)

WIDGET_FILES: list[tuple[str, str, bool]] = [
    ("desktop/shell/bar/widgets/Indicators.qml", "plugins/bar/widgets/Indicators.qml", False),
    ("desktop/shell/bar/indicators/Dnd.qml", "plugins/bar/indicators/Dnd.qml", False),
    ("desktop/shell/bar/indicators/NightLight.qml", "plugins/bar/indicators/NightLight.qml", False),
    ("desktop/shell/bar/indicators/Reminder.qml", "plugins/bar/indicators/Reminder.qml", False),
    ("desktop/shell/bar/indicators/ScreenRecording.qml", "plugins/bar/indicators/ScreenRecording.qml", False),
    ("desktop/shell/bar/indicators/StayAwake.qml", "plugins/bar/indicators/StayAwake.qml", False),
    ("desktop/shell/bar/widgets/KeyboardLayout.qml", "plugins/bar/widgets/KeyboardLayout.qml", False),
    ("desktop/shell/bar/widgets/KeyboardLayoutModel.js", "plugins/bar/widgets/KeyboardLayoutModel.js", True),
    ("desktop/shell/bar/widgets/Tray.qml", "plugins/bar/widgets/Tray.qml", False),
    ("desktop/shell/bar/widgets/TrayModel.js", "plugins/bar/widgets/TrayModel.js", False),
]


def port_line(line: str) -> str:
    line = line.replace("import qs.Commons", "import Tam.Commons")
    line = line.replace("import qs.Ui", "import Tam.Ui")
    line = line.replace('[ "Dictation", "ScreenRecording",', '[ "ScreenRecording",')
    line = line.replace("ownedByOmarchy", "ownedByShell")
    line = line.replace("omarchy's shell.qml", "the shell's shell.qml")
    line = line.replace("omarchy.", "tamlinux.")
    line = CMD_PATTERN.sub(r"tam-\1", line)
    return line


def port(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = [port_line(line) for line in lines]
    return "".join(out)


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

    def test_bodies_match_ported_original_text(self):
        if not OMARCHY.is_dir():
            self.skipTest(f"Omarchy root {OMARCHY} not present")
        for new_path, orig_path, _ in WIDGET_FILES:
            orig_text = (OMARCHY / orig_path).read_text(encoding="utf-8")
            expected_body = port(orig_text)
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            actual_body = "".join(lines[4:])
            self.assertEqual(actual_body, expected_body, f"Ported body mismatch in {new_path}")

    def test_unchanged_file_matches_and_changed_files_differ(self):
        if not OMARCHY.is_dir():
            self.skipTest(f"Omarchy root {OMARCHY} not present")
        for new_path, orig_path, unchanged in WIDGET_FILES:
            orig_text = (OMARCHY / orig_path).read_text(encoding="utf-8")
            ported_text = port(orig_text)
            if unchanged:
                self.assertEqual(
                    ported_text,
                    orig_text,
                    f"Expected {new_path} to be byte-identical to original",
                )
            else:
                self.assertNotEqual(
                    ported_text,
                    orig_text,
                    f"Expected {new_path} to differ from original",
                )

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

    def test_bodies_drop_qs_imports_and_use_tam_imports(self):
        omarchy_present = OMARCHY.is_dir()
        for new_path, orig_path, _ in WIDGET_FILES:
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            self.assertNotIn("qs.Commons", body, f"{new_path} contains qs.Commons")
            self.assertNotIn("qs.Ui", body, f"{new_path} contains qs.Ui")
            if omarchy_present:
                orig_text = (OMARCHY / orig_path).read_text(encoding="utf-8")
                if "import qs.Commons" in orig_text:
                    self.assertIn("import Tam.Commons", body, f"{new_path} missing import Tam.Commons")
                if "import qs.Ui" in orig_text:
                    self.assertIn("import Tam.Ui", body, f"{new_path} missing import Tam.Ui")

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

    def test_owned_by_shell_occurrences_match_originals(self):
        if not OMARCHY.is_dir():
            self.skipTest(f"Omarchy root {OMARCHY} not present")
        for new_path, orig_path in [
            ("desktop/shell/bar/widgets/TrayModel.js", "plugins/bar/widgets/TrayModel.js"),
            ("desktop/shell/bar/widgets/Tray.qml", "plugins/bar/widgets/Tray.qml"),
        ]:
            orig_text = (OMARCHY / orig_path).read_text(encoding="utf-8")
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            orig_count = orig_text.count("ownedByOmarchy")
            body_count = body.count("ownedByShell")
            self.assertGreater(orig_count, 0)
            self.assertEqual(
                body_count,
                orig_count,
                f"Occurrence mismatch in {new_path}: got {body_count} ownedByShell, expected {orig_count}",
            )
        tray_model_body = (ROOT / "desktop/shell/bar/widgets/TrayModel.js").read_text(encoding="utf-8")
        self.assertIn("function ownedByShell(item, layout)", tray_model_body)
        self.assertIn("ownedByShell: ownedByShell", tray_model_body)
        tray_qml_body = (ROOT / "desktop/shell/bar/widgets/Tray.qml").read_text(encoding="utf-8")
        self.assertIn("function ownedByShell(item)", tray_qml_body)

    def test_mutation_guard_verifies_substitution_rules(self):
        synthetic_input = (
            "import qs.Commons\n"
            "import qs.Ui\n"
            'readonly property var defaultIndicatorEntries: [ "Dictation", "ScreenRecording", "Reminder" ]\n'
            "function ownedByOmarchy(item) {\n"
            "// omarchy's shell.qml does not\n"
            'moduleName: "omarchy.tray"\n'
            'exec(["omarchy-capture-screenrecording", "stop"])\n'
            "omarchy-menu toggle\n"
            "omarchy-menu-select\n"
            "omarchy-reminder check\n"
        )
        expected_output = (
            "import Tam.Commons\n"
            "import Tam.Ui\n"
            'readonly property var defaultIndicatorEntries: [ "ScreenRecording", "Reminder" ]\n'
            "function ownedByShell(item) {\n"
            "// the shell's shell.qml does not\n"
            'moduleName: "tamlinux.tray"\n'
            'exec(["tam-capture-screenrecording", "stop"])\n'
            "tam-menu toggle\n"
            "omarchy-menu-select\n"
            "tam-reminder check\n"
        )
        self.assertEqual(port(synthetic_input), expected_output)


if __name__ == "__main__":
    unittest.main()
