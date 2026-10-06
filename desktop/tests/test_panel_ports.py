"""Source checks for the ported shell panels and speed-test overlay."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OMARCHY = Path("/usr/share/omarchy/shell")

COMMANDS = [
    "audio-input-set-default",
    "audio-output-set-default",
    "audio-output-sink",
    "audio-sink-availability",
    "bluetooth-device",
    "bluetooth-power",
    "dns",
    "launch-floating-terminal-with-presentation",
    "network-band",
    "network-status",
    "network-qr",
    "network-password",
    "network-speedtest",
    "disk-speedtest",
    "battery-status",
    "powerprofiles-list",
    "powerprofiles-set",
    "system-stats",
]

CMD_PATTERN = re.compile(
    r"omarchy-("
    + "|".join(re.escape(c) for c in sorted(COMMANDS, key=len, reverse=True))
    + r")(?![a-z0-9-])"
)

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


def port_line(line: str) -> str:
    line = line.replace("import qs.Commons", "import Tam.Commons")
    line = line.replace("import qs.Ui", "import Tam.Ui")
    if "WlrLayershell.namespace:" in line or "layerNamespace:" in line:
        line = line.replace('"omarchy-', '"tamlinux-')
    line = line.replace("omarchy.", "tamlinux.")
    line = CMD_PATTERN.sub(r"tam-\1", line)
    return line


def port(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        if line.strip() == 'property string omarchyPath: Quickshell.env("OMARCHY_PATH")':
            continue
        out.append(port_line(line))
    return "".join(out)


# Changes made after the mechanical port, while wiring each panel. Each is
# (old, new) applied once to the ported body.
ADAPTATIONS = {
    # x forgets a device; Tam.Ui's key catcher makes that opt-in (0.2.4).
    "desktop/shell/panels/bluetooth/Panel.qml": [
        ("    PanelKeyCatcher {\n      id: keyCatcher\n",
         "    PanelKeyCatcher {\n      id: keyCatcher\n      deleteOnX: true\n"),
    ],
}


def adapt(new_path: str, body: str) -> str:
    for old, new in ADAPTATIONS.get(new_path, []):
        assert body.count(old) == 1, (new_path, old)
        body = body.replace(old, new)
    return body


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

    def test_bodies_match_ported_original_text(self):
        if not OMARCHY.is_dir():
            self.skipTest(f"Omarchy root {OMARCHY} not present")
        for new_path, orig_path, _ in PANEL_FILES:
            orig_text = (OMARCHY / orig_path).read_text(encoding="utf-8")
            expected_body = adapt(new_path, port(orig_text))
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            actual_body = "".join(lines[4:])
            self.assertEqual(actual_body, expected_body, f"Ported body mismatch in {new_path}")

    def test_unchanged_files_match_and_changed_files_differ(self):
        if not OMARCHY.is_dir():
            self.skipTest(f"Omarchy root {OMARCHY} not present")
        for new_path, orig_path, unchanged in PANEL_FILES:
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

    def test_only_speaker_tuning_preserves_omarchy_name(self):
        matches: list[tuple[str, str]] = []
        for new_path, _, _ in PANEL_FILES:
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            for line in body.splitlines():
                if re.search(r"omarchy", line, re.IGNORECASE):
                    matches.append((new_path, line.strip()))
        self.assertEqual(
            len(matches),
            1,
            f"Expected exactly 1 omarchy match in bodies, got: {matches}",
        )
        matched_file, matched_line = matches[0]
        self.assertEqual(matched_file, "desktop/shell/panels/audio/Panel.qml")
        self.assertIn("omarchy_speaker_tuning", matched_line)

    def test_bodies_drop_omarchy_path_and_remap_qs_imports(self):
        omarchy_present = OMARCHY.is_dir()
        for new_path, orig_path, _ in PANEL_FILES:
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            self.assertNotIn("qs.Commons", body, f"{new_path} contains qs.Commons")
            self.assertNotIn("qs.Ui", body, f"{new_path} contains qs.Ui")
            self.assertNotIn("OMARCHY_PATH", body, f"{new_path} contains OMARCHY_PATH")
            if omarchy_present:
                orig_text = (OMARCHY / orig_path).read_text(encoding="utf-8")
                if "import qs.Commons" in orig_text:
                    self.assertIn(
                        "import Tam.Commons",
                        body,
                        f"{new_path} missing import Tam.Commons",
                    )
                if "import qs.Ui" in orig_text:
                    self.assertIn(
                        "import Tam.Ui",
                        body,
                        f"{new_path} missing import Tam.Ui",
                    )

    def test_command_and_layer_counts_match_expectations(self):
        if not OMARCHY.is_dir():
            self.skipTest(f"Omarchy root {OMARCHY} not present")
        for new_path, orig_path, _ in PANEL_FILES:
            orig_text = (OMARCHY / orig_path).read_text(encoding="utf-8")
            lines = (ROOT / new_path).read_text(encoding="utf-8").splitlines(keepends=True)
            body = "".join(lines[4:])
            for cmd in COMMANDS:
                orig_matches = len(
                    re.findall(rf"omarchy-{re.escape(cmd)}(?![a-z0-9-])", orig_text)
                )
                orig_layer_matches = 0
                for line in orig_text.splitlines():
                    if (
                        "WlrLayershell.namespace:" in line or "layerNamespace:" in line
                    ) and f'"{cmd}"' in line:
                        pass
                    if (
                        "WlrLayershell.namespace:" in line or "layerNamespace:" in line
                    ) and f'"omarchy-{cmd}"' in line:
                        orig_layer_matches += 1
                tam_matches = len(re.findall(rf"tam-{re.escape(cmd)}(?![a-z0-9-])", body))
                self.assertEqual(
                    tam_matches,
                    orig_matches - orig_layer_matches,
                    f"Command count mismatch for {cmd} in {new_path}: got {tam_matches}, "
                    f"expected {orig_matches} - {orig_layer_matches}",
                )

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

    def test_mutation_guard_verifies_substitution_rules(self):
        synthetic_input = (
            '  property string omarchyPath: Quickshell.env("OMARCHY_PATH")\n'
            "import qs.Commons\n"
            "import qs.Ui\n"
            'WlrLayershell.namespace: "omarchy-network-qr"\n'
            'layerNamespace: "omarchy-speed-test"\n'
            'moduleName: "omarchy.audio"\n'
            "omarchy-network-qr-extra\n"
            "omarchy-dns\n"
        )
        expected_output = (
            "import Tam.Commons\n"
            "import Tam.Ui\n"
            'WlrLayershell.namespace: "tamlinux-network-qr"\n'
            'layerNamespace: "tamlinux-speed-test"\n'
            'moduleName: "tamlinux.audio"\n'
            "omarchy-network-qr-extra\n"
            "tam-dns\n"
        )
        self.assertEqual(port(synthetic_input), expected_output)
