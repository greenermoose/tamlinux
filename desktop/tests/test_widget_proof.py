"""desktop/widget-proof: offscreen render of one bar widget."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

DESKTOP = Path(__file__).resolve().parents[1]
SCRIPT = DESKTOP / "widget-proof"
_loader = importlib.machinery.SourceFileLoader("widget_proof", str(SCRIPT))
_spec = importlib.util.spec_from_loader("widget_proof", _loader)
proof = importlib.util.module_from_spec(_spec)
_loader.exec_module(proof)


class Pieces(unittest.TestCase):
    def test_plugin_ids_resolve_under_desktop_plugins(self):
        self.assertEqual(proof.plugin_dir("fred.tamversion"), DESKTOP / "plugins/fred.tamversion")
        self.assertEqual(proof.bar_entry(DESKTOP / "plugins/fred.tamversion"), "BarWidget")
        with self.assertRaises(SystemExit):
            proof.plugin_dir("fred.absent")

    def test_plugin_without_bar_widget_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "manifest.json").write_text(json.dumps({"id": "fred.x", "entryPoints": {}}))
            with self.assertRaises(SystemExit):
                proof.bar_entry(Path(temp))

    def test_environment_is_isolated_from_the_desktop(self):
        desktop = {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-1", "DBUS_SESSION_BUS_ADDRESS": "unix:x",
                   "QT_QPA_PLATFORMTHEME": "gtk3", "GDK_BACKEND": "wayland", "HOME": "/home/u"}
        with mock.patch.dict(os.environ, desktop, clear=True):
            env = proof.environment(Path("/run/proof"), ["TAMLINUX_VERSION=0.4.4-b"])
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "QT_QPA_PLATFORMTHEME", "GDK_BACKEND"):
            self.assertNotIn(key, env)
        self.assertEqual((env["QT_QPA_PLATFORM"], env["XDG_RUNTIME_DIR"], env["TAMLINUX_VERSION"], env["HOME"]),
                         ("offscreen", "/run/proof", "0.4.4-b", "/home/u"))
        self.assertEqual(env["QML_IMPORT_PATH"], str(DESKTOP / "shell/modules"))
        with self.assertRaises(SystemExit):
            proof.environment(Path("/run/proof"), ["NOVALUE"])

    def test_generated_shell_reads_the_named_property(self):
        qml = proof.shell_qml("BarWidget", "displayText")
        self.assertIn('import "plugin" as Plugin', qml)
        self.assertIn("Plugin.BarWidget {", qml)
        self.assertIn('widget["displayText"]', qml)

    def test_result_line_and_problems_are_parsed(self):
        output = ("  INFO: Launching\n DEBUG qml: TAMLINUX_WIDGET_PROOF "
                  '{"text":"Tamlinux 0.4.4b","width":125,"height":26}\n'
                  "\x1b[31m ERROR\x1b[0m: caused by x: Type Y unavailable\n"
                  " ERROR quickshell.ipc: Failed to start IPC server\n")
        self.assertEqual(proof.parse(output), {"text": "Tamlinux 0.4.4b", "width": 125, "height": 26})
        self.assertIsNone(proof.parse("nothing"))
        self.assertEqual(proof.problems(output), ["ERROR: caused by x: Type Y unavailable"])


QUICKSHELL = proof.find_quickshell(None)


@unittest.skipUnless(QUICKSHELL and Path(QUICKSHELL).exists(), "no Quickshell available")
class Render(unittest.TestCase):
    def run_proof(self, *args):
        return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, timeout=60)

    def test_version_label_renders_with_size_and_text(self):
        result = self.run_proof("fred.tamversion", "--env", "TAMLINUX_VERSION=0.4.4-b", "--expect", "Tamlinux 0.4.4b")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertGreater(report["width"], 0)

    def test_wrong_text_fails(self):
        result = self.run_proof("fred.tamversion", "--env", "TAMLINUX_VERSION=0.4.4-b", "--expect", "Tamlinux 9")
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected 'Tamlinux 9'", json.loads(result.stdout)["failures"][0])


if __name__ == "__main__":
    unittest.main()
