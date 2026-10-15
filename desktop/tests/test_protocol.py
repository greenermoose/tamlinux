"""Run the actual QML bindings against mutable protocol fixtures, offscreen."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]


class ProtocolTests(unittest.TestCase):
    def test_reactive_protocol_fixtures(self):
        with tempfile.TemporaryDirectory(prefix="tamlinux-protocol-") as directory:
            root = Path(directory)
            config = root / "config"
            (config / "host").mkdir(parents=True)
            shutil.copyfile(DESKTOP / "fixtures/protocol/shell.qml", config / "shell.qml")
            for name in ("ProtocolState.qml", "protocol_model.js"):
                shutil.copyfile(DESKTOP / "shell/host" / name, config / "host" / name)
            env = {"PATH": "/usr/bin", "HOME": directory, "XDG_RUNTIME_DIR": directory,
                   "XDG_CONFIG_HOME": directory, "XDG_CACHE_HOME": directory,
                   "QT_QPA_PLATFORM": "offscreen", "QSG_RENDER_LOOP": "basic"}
            result = subprocess.run(
                ["/usr/bin/quickshell", "--no-color", "-p", str(config)],
                env=env, capture_output=True, text=True, timeout=15, check=False,
            )
        log = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, log)
        self.assertIn("PROTOCOL_FIXTURE_OK", log)
        self.assertNotIn("PROTOCOL_FIXTURE_FAILED", log)
        self.assertNotIn("TypeError", log)
        self.assertNotIn("ReferenceError", log)

    def test_protocol_owns_standard_imports_and_starts_no_processes(self):
        qml = (DESKTOP / "shell/host/ProtocolState.qml").read_text()
        self.assertIn("import Quickshell.WindowManager", qml)
        self.assertIn("WindowManager.windowsets", qml)
        self.assertIn("Quickshell.screens", qml)
        for banned in ("Process", "Quickshell.Hyprland", "Quickshell.I3"):
            self.assertNotIn(banned, qml)

    def test_protocol_models_are_polled_never_bound(self):
        # A QML binding over ext-workspace bindables re-captures observers
        # inside Quickshell's property update group; Qt then calls a freed
        # observer (2026-10-14 TTY1 crashes). Only plain reads are allowed.
        qml = (DESKTOP / "shell/host/ProtocolState.qml").read_text()
        for line in qml.splitlines():
            declaration = re.match(r"\s*(?:readonly\s+)?property\s+\w+\s+\w+\s*:\s*(.*)", line)
            if not declaration:
                continue
            value = declaration.group(1)
            for live in ("WindowManager", "Quickshell.screens", "Model.snapshot(windowsets", "Model.snapshot(currentSets"):
                self.assertNotIn(live, value, line)
        self.assertIn("onTriggered: state.refresh()", qml)
        self.assertIn("Component.onCompleted: refresh()", qml)


if __name__ == "__main__":
    unittest.main()
