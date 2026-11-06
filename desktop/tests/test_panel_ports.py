"""Source checks for the ported shell panels and speed-test overlay."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PANEL_FILES: list[tuple[str, str, bool]] = [
    ("desktop/shell/panels/audio/Panel.qml", "plugins/panels/audio/Panel.qml", False),
    ("desktop/shell/panels/audio/Model.js", "plugins/panels/audio/Model.js", True),
    ("desktop/shell/panels/bluetooth/Panel.qml", "plugins/panels/bluetooth/Panel.qml", False),
    ("desktop/shell/panels/bluetooth/Model.js", "plugins/panels/bluetooth/Model.js", True),
    ("desktop/shell/panels/network/Panel.qml", "plugins/panels/network/Panel.qml", False),
    ("desktop/shell/panels/network/Model.js", "plugins/panels/network/Model.js", True),
    ("desktop/shell/panels/wifiqr/Panel.qml", "plugins/panels/wifiqr/Panel.qml", False),
    ("desktop/shell/panels/wifiqr/Model.js", "plugins/panels/wifiqr/Model.js", False),
    ("desktop/shell/panels/power/Panel.qml", "plugins/panels/power/Panel.qml", False),
    ("desktop/shell/panels/power/Model.js", "plugins/panels/power/Model.js", True),
    ("desktop/shell/panels/speedtest/Panel.qml", "plugins/panels/speedtest/Panel.qml", False),
    ("desktop/shell/panels/diskspeedtest/Panel.qml", "plugins/panels/disk-speedtest/Panel.qml", False),
    ("desktop/shell/modules/Tam/Ui/SpeedTestOverlay.qml", "Ui/SpeedTestOverlay.qml", False),
]

LAYER_NAMES: dict[str, str] = {
    "tamlinux-network-qr": "desktop/shell/panels/wifiqr/Panel.qml",
    "tamlinux-network-speedtest": "desktop/shell/panels/speedtest/Panel.qml",
    "tamlinux-disk-speedtest": "desktop/shell/panels/diskspeedtest/Panel.qml",
    "tamlinux-speed-test": "desktop/shell/modules/Tam/Ui/SpeedTestOverlay.qml",
}


def expected_header(new_path: str, orig_path: str, unchanged: bool) -> list[str]:
    lic = (
        "../../../services/LICENSE-omarchy"
        if new_path.startswith("desktop/shell/modules/")
        else "../../services/LICENSE-omarchy"
    )
    change_line = (
        "// Unchanged."
        if unchanged
        else "// Changes: owned module, id, layer, and command names."
    )
    return [
        f"// Ported from omarchy 4.0.4 shell/{orig_path}\n",
        f"// (MIT, Copyright (c) David Heinemeier Hansson; see {lic}).\n",
        f"{change_line}\n",
        "\n",
    ]


class PanelPortTests(unittest.TestCase):
    def test_files_exist_are_utf8_and_end_with_single_newline(self):
        for new_path, _, _ in PANEL_FILES:
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
        for new_path, orig_path, unchanged in PANEL_FILES:
            path = ROOT / new_path
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            self.assertGreaterEqual(len(lines), 4, f"{new_path} has fewer than 4 lines")
            expected = expected_header(new_path, orig_path, unchanged)
            self.assertEqual(lines[:4], expected, f"Header mismatch in {new_path}")
            self.assertEqual(lines[3], "\n", f"Line 4 is not empty in {new_path}")

    def test_panel_bodies_use_owned_names(self):
        matches: list[tuple[str, str]] = []
        for new_path, _, _ in PANEL_FILES:
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            for line in body.splitlines():
                if re.search(r"omarchy", line, re.IGNORECASE):
                    matches.append((new_path, line.strip()))
        self.assertEqual(matches, [], f"Inherited active panel names: {matches}")
        panel = (ROOT / "desktop/shell/panels/audio/Panel.qml").read_text()
        writer = (ROOT / "commands/tam-audio-tuning/tam-audio-tuning").read_text()
        self.assertIn("tamlinux_speaker_tuning", panel)
        self.assertIn("sink_name=tamlinux_speaker_tuning", writer)

    def test_bodies_drop_omarchy_path_and_qs_imports(self):
        for new_path, _, _ in PANEL_FILES:
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            self.assertNotIn("qs.Commons", body, f"{new_path} contains qs.Commons")
            self.assertNotIn("qs.Ui", body, f"{new_path} contains qs.Ui")
            self.assertNotIn("OMARCHY_PATH", body, f"{new_path} contains OMARCHY_PATH")

    def test_each_layer_name_appears_only_in_its_panel(self):
        for layer_name, expected_file in LAYER_NAMES.items():
            for new_path, _, _ in PANEL_FILES:
                lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
                body = "".join(lines[4:])
                count = body.count(layer_name)
                expected_count = 1 if new_path == expected_file else 0
                self.assertEqual(
                    count,
                    expected_count,
                    f"Expected {layer_name} in {new_path} to appear {expected_count} times, got {count}",
                )

