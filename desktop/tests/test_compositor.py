"""Argv and source checks for the compositor facade. These tests do not run hyprctl."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP / "shell" / "host"))

import compositor_commands as commands  # noqa: E402


class CommandTests(unittest.TestCase):
    def test_read_commands_are_fixed(self):
        self.assertEqual(commands.binds_argv(), ["/usr/bin/hyprctl", "binds"])
        self.assertEqual(commands.devices_argv(), ["/usr/bin/hyprctl", "-j", "devices"])
        self.assertEqual(commands.monitors_argv(), ["/usr/bin/hyprctl", "-j", "monitors"])

    def test_focus_and_dpms_commands(self):
        self.assertEqual(
            commands.focus_workspace_argv(4),
            ["/usr/bin/hyprctl", "dispatch", 'hl.dsp.focus({ workspace = "4" })'],
        )
        self.assertEqual(
            commands.focus_output_argv("DP-1"),
            ["/usr/bin/hyprctl", "dispatch", 'hl.dsp.focus({ monitor = "DP-1" })'],
        )
        self.assertEqual(
            commands.set_dpms_argv("HDMI-A-1", False),
            [
                "/usr/bin/hyprctl",
                "eval",
                'hl.dispatch(hl.dsp.dpms({ action = "disable", monitor = "HDMI-A-1" }))',
            ],
        )
        self.assertEqual(
            commands.set_dpms_argv("eDP-1", True)[2],
            'hl.dispatch(hl.dsp.dpms({ action = "enable", monitor = "eDP-1" }))',
        )

    def test_rejects_bad_names_and_workspaces(self):
        for name in ("", "DP-1;rm", "../x", "DP 1", "a" * 65, "DP-1\n"):
            with self.subTest(name=name):
                with self.assertRaises(commands.CompositorCommandError):
                    commands.focus_output_argv(name)
                with self.assertRaises(commands.CompositorCommandError):
                    commands.set_dpms_argv(name, True)
        for workspace in (True, False, 0, 11, -1, "1", 1.5):
            with self.subTest(workspace=workspace):
                with self.assertRaises(commands.CompositorCommandError):
                    commands.focus_workspace_argv(workspace)  # type: ignore[arg-type]
        with self.assertRaises(commands.CompositorCommandError):
            commands.set_dpms_argv("DP-1", "off")  # type: ignore[arg-type]

    def test_keymap_and_monitor_snapshot(self):
        payload = {
            "keyboards": [
                {"name": "extra", "active_keymap": "German"},
                {"name": "main", "main": True, "active_keymap": "English (US)"},
            ]
        }
        self.assertEqual(commands.active_keymap(payload), "English (US)")
        self.assertEqual(commands.active_keymap('{"keyboards": []}'), "")
        self.assertEqual(commands.active_keymap("x" * (commands.DEVICES_LIMIT + 1)), "")
        snapshot = commands.snapshot_from_monitors([
            {"name": "HDMI-A-1", "focused": False, "activeWorkspace": {"id": 3}, "dpmsStatus": True},
            {"name": "DP-1", "focused": True, "activeWorkspace": {"id": 1}, "dpmsStatus": False},
            {"name": "bad name", "focused": False, "activeWorkspace": {"id": 9}},
            {"name": "DP-2", "focused": False, "activeWorkspace": {"id": True}},
        ])
        self.assertEqual(snapshot, {
            "names": ["DP-1", "DP-2", "HDMI-A-1"],
            "focused": "DP-1",
            "workspaces": [1, 3],
        })

    def test_module_does_not_launch_processes(self):
        text = Path(commands.__file__).read_text(encoding="utf-8")
        self.assertNotIn("subprocess", text)
        self.assertNotIn("os.system", text)
        self.assertNotIn("Popen", text)


class SourceBoundaryTests(unittest.TestCase):
    def test_adapter_matches_the_command_text(self):
        qml = (DESKTOP / "shell" / "host" / "HyprlandAdapter.qml").read_text(encoding="utf-8")
        self.assertIn("import Quickshell.Hyprland", qml)
        self.assertIn('"/usr/bin/hyprctl"', qml)
        self.assertIn('"binds"', qml)
        self.assertIn('"-j"', qml)
        self.assertIn('"devices"', qml)
        self.assertIn('"monitors"', qml)
        self.assertIn('hl.dsp.focus({ workspace = "', qml)
        self.assertIn('hl.dsp.focus({ monitor = "', qml)
        self.assertIn('hl.dsp.dpms({ action = "', qml)
        self.assertIn('"enable"', qml)
        self.assertIn('"disable"', qml)
        self.assertIn("TAMLINUX_COMPOSITOR_LIVE_ACTIONS", qml)
        self.assertIn(r"/^[A-Za-z0-9._-]{1,64}$/", qml)
        self.assertIn(r"/^(?:[1-9]|10)$/", qml)
        self.assertIn(str(commands.BINDS_LIMIT), qml)
        self.assertIn(str(commands.KEYMAP_LIMIT), qml)
        self.assertNotIn("sh -c", qml)
        self.assertNotIn("bash", qml)

    def test_other_qml_does_not_touch_hyprland(self):
        adapter = DESKTOP / "shell" / "host" / "HyprlandAdapter.qml"
        seen = False
        for path in DESKTOP.rglob("*.qml"):
            text = path.read_text(encoding="utf-8")
            if path == adapter:
                seen = True
                continue
            self.assertNotIn("Quickshell.Hyprland", text, path.name)
            self.assertNotIn("hyprctl", text, path.name)
            self.assertNotIn("Hyprland.", text, path.name)
        self.assertTrue(seen)

    def test_launcher_clears_live_actions(self):
        text = (DESKTOP / "launch-clock-proof").read_text(encoding="utf-8")
        self.assertIn('env.pop("TAMLINUX_COMPOSITOR_LIVE_ACTIONS", None)', text)

    def test_fixture_only_reads_the_facade(self):
        text = (DESKTOP / "fixtures" / "compositor" / "BarWidget.qml").read_text(encoding="utf-8")
        self.assertIn('moduleName: "tamlinux.compositor"', text)
        self.assertIn("outputForScreen", text)
        self.assertNotIn("IpcHandler", text)
        self.assertNotIn("import Quickshell", text)


if __name__ == "__main__":
    unittest.main()
