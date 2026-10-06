"""Argv and source checks for the compositor facade. These tests do not run hyprctl."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

DESKTOP = Path(__file__).resolve().parents[1]
# The plugin repositories sit beside the checkout, or above a worktree.
WORKSPACE = Path(os.environ.get("TAMLINUX_WORKSPACE") or next(
    (p for p in DESKTOP.parents if (p / "clock-fred-tamlinux").is_dir()), DESKTOP.parents[1]
))
sys.path.insert(0, str(DESKTOP / "shell" / "host"))

import compositor_commands as commands  # noqa: E402
import hyprland_backend as backend  # noqa: E402


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
                "dispatch",
                'hl.dsp.dpms({ action = "off", monitor = "HDMI-A-1" })',
            ],
        )
        self.assertEqual(
            commands.set_dpms_argv("eDP-1", "on")[2],
            'hl.dsp.dpms({ action = "on", monitor = "eDP-1" })',
        )
        self.assertEqual(
            commands.set_dpms_fallback_argv("DP-1", False),
            ["/usr/bin/hyprctl", "dispatch", "dpms", "off", "DP-1"],
        )

    def test_focus_window_by_address(self):
        for address in ("55d1c2a0", "0x55D1C2A0"):
            with self.subTest(address=address):
                self.assertEqual(
                    commands.focus_window_argv(address),
                    ["/usr/bin/hyprctl", "dispatch", 'hl.dsp.focus({ window = "address:0x55d1c2a0" })'],
                )
        for address in ("", "0x", "zz", "0x" + "f" * 17, "1;rm", 12, None):
            with self.subTest(address=address):
                with self.assertRaises(commands.CompositorCommandError):
                    commands.focus_window_argv(address)
        for name in ("Slack", "Google Chrome", "org.gnome.Nautilus", "c++-app"):
            self.assertEqual(commands.require_app_name(name), name)
        for name in ("", " lead", '"x"', "a(b)", "a" * 65, "x\n", None):
            with self.subTest(name=name):
                with self.assertRaises(commands.CompositorCommandError):
                    commands.require_app_name(name)

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
            commands.set_dpms_argv("DP-1", "disable")

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

    def test_keyboards_from_devices(self):
        payload = {
            "keyboards": [
                {"name": "power-button", "layout": "us,de", "active_keymap": "English (US)", "active_layout_index": 0},
                {"name": "kbd", "main": True, "layout": "us,de", "active_keymap": "German", "active_layout_index": 1},
                {"name": "bad name", "active_keymap": "x"},
                {"name": "nl", "active_keymap": "a\nb", "active_layout_index": True},
                "not a board",
            ]
        }
        self.assertEqual(commands.keyboards_from(payload), [
            {"name": "power-button", "layout": "us,de", "activeKeymap": "English (US)", "activeLayoutIndex": 0, "main": False},
            {"name": "kbd", "layout": "us,de", "activeKeymap": "German", "activeLayoutIndex": 1, "main": True},
            {"name": "nl", "layout": None, "activeKeymap": "", "activeLayoutIndex": 0, "main": False},
        ])
        many = {"keyboards": [{"name": f"k{i}"} for i in range(commands.KEYBOARD_LIMIT + 4)]}
        self.assertEqual(len(commands.keyboards_from(many)), commands.KEYBOARD_LIMIT)
        self.assertEqual(commands.keyboards_from("not json"), [])
        self.assertEqual(commands.keyboards_from('{"keyboards": {}}'), [])
        self.assertEqual(commands.keyboards_from("x" * (commands.DEVICES_LIMIT + 1)), [])

    def test_switch_keyboard_layout(self):
        self.assertEqual(
            commands.switch_keyboard_layout_argv("at-translated-set-2-keyboard"),
            ["/usr/bin/hyprctl", "switchxkblayout", "at-translated-set-2-keyboard", "next"],
        )
        for bad in ("", "a b", "x;rm", "a" * 65, None):
            with self.subTest(bad=bad), self.assertRaises(commands.CompositorCommandError):
                commands.switch_keyboard_layout_argv(bad)  # type: ignore[arg-type]
        self.assertEqual(commands.bounded_description("HP\n22cwa"), "HP 22cwa")
        self.assertEqual(commands.bounded_description(None), "")
        self.assertEqual(len(commands.bounded_description("d" * 200)), commands.DESCRIPTION_LIMIT)
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

    def test_helper_reads_and_dispatch_commands(self):
        self.assertEqual(commands.monitors_all_argv(), ["/usr/bin/hyprctl", "monitors", "all", "-j"])
        self.assertEqual(commands.active_workspace_argv(), ["/usr/bin/hyprctl", "activeworkspace", "-j"])
        self.assertEqual(commands.reload_argv(), ["/usr/bin/hyprctl", "reload"])
        self.assertEqual(commands.config_errors_argv(), ["/usr/bin/hyprctl", "configerrors"])
        self.assertEqual(commands.rollinglog_argv(), ["/usr/bin/hyprctl", "rollinglog"])
        self.assertEqual(
            commands.dispatch_focus_workspace_argv(28),
            ["/usr/bin/hyprctl", "dispatch", 'hl.dsp.focus({ workspace = "28" })'],
        )
        self.assertEqual(
            commands.focus_workspace_fallback_argv(4),
            ["/usr/bin/hyprctl", "dispatch", "workspace", "4"],
        )
        self.assertEqual(
            commands.move_window_argv(6, False),
            [
                "/usr/bin/hyprctl",
                "dispatch",
                'hl.dsp.window.move({ workspace = "6", follow = false })',
            ],
        )
        self.assertEqual(
            commands.move_window_fallback_argv(6, True),
            ["/usr/bin/hyprctl", "dispatch", "movetoworkspace", "6"],
        )
        self.assertEqual(
            commands.move_workspace_argv("DP-1"),
            ["/usr/bin/hyprctl", "dispatch", 'hl.dsp.workspace.move({ monitor = "DP-1" })'],
        )
        self.assertEqual(
            commands.move_workspace_fallback_argv(4, "HDMI-A-1"),
            ["/usr/bin/hyprctl", "dispatch", "moveworkspacetomonitor", "4", "HDMI-A-1"],
        )
        self.assertEqual(
            commands.focus_output_fallback_argv("DP-2"),
            ["/usr/bin/hyprctl", "dispatch", "focusmonitor", "DP-2"],
        )

    def test_batch_is_built_from_named_steps(self):
        argv = commands.batch_argv([
            ("focus-output", "DP-2"),
            ("focus-workspace", 4),
            ("move-workspace", "DP-1"),
        ])
        self.assertEqual(
            argv,
            [
                "/usr/bin/hyprctl",
                "--batch",
                'dispatch hl.dsp.focus({ monitor = "DP-2" }); '
                'dispatch hl.dsp.focus({ workspace = "4" }); '
                'dispatch hl.dsp.workspace.move({ monitor = "DP-1" })',
            ],
        )
        with self.assertRaises(commands.CompositorCommandError):
            commands.batch_argv([])
        with self.assertRaises(commands.CompositorCommandError):
            commands.batch_argv([("dispatch", "workspace")])
        with self.assertRaises(commands.CompositorCommandError):
            commands.batch_argv([("focus-workspace", 4)] * (commands.BATCH_LIMIT + 1))
        with self.assertRaises(commands.CompositorCommandError):
            commands.focus_workspace_argv(11)
        with self.assertRaises(commands.CompositorCommandError):
            commands.dispatch_focus_workspace_argv(commands.DISPATCH_WORKSPACE_MAX + 1)

    def test_monitor_rule_fields_are_bounded(self):
        self.assertEqual(
            commands.monitor_rule_text(
                "DP-1",
                disabled=False,
                mode="2560x1440@59.951",
                position="1280x0",
                scale=1,
                transform=0,
            ),
            'hl.monitor({ output = "DP-1", mode = "2560x1440@59.951", '
            'position = "1280x0", scale = 1, transform = 0, disabled = false })',
        )
        self.assertEqual(
            commands.monitor_rule_argv("HDMI-A-1", disabled=True),
            ["/usr/bin/hyprctl", "eval", 'hl.monitor({ output = "HDMI-A-1", disabled = true })'],
        )
        for mode in ("1920x1080@60", "preferred", "1920x1080@60Hz"):
            commands.require_mode(mode)
        for bad in ("preferred;rm", "1920x1080", "auto", "1920x1080@60 Hz", ""):
            with self.subTest(mode=bad), self.assertRaises(commands.CompositorCommandError):
                commands.require_mode(bad)
        with self.assertRaises(commands.CompositorCommandError):
            commands.monitor_rule_text("DP-1", disabled=False, mode="preferred", position="1 0", scale=1)


class BackendTests(unittest.TestCase):
    def test_reads_run_and_mutations_record(self):
        recorded = subprocess.CompletedProcess(["/usr/bin/hyprctl"], 0, "{}\n", "")
        env = os.environ.copy()
        env.pop("TAMLINUX_COMPOSITOR_LIVE_ACTIONS", None)
        with patch.dict(os.environ, env, clear=True), patch.object(backend.subprocess, "run", return_value=recorded) as run:
            result = backend.run("monitors", None)
            self.assertEqual(run.call_args.args[0], commands.monitors_argv())
            self.assertEqual(run.call_args.kwargs["env"]["PATH"], "/usr/bin")
            self.assertNotIn("HOME", run.call_args.kwargs["env"])
            run.reset_mock()
            recorded_action = backend.run("dpms", ["DP-1", "off"])
            run.assert_not_called()
            self.assertEqual(recorded_action.returncode, 0)
            self.assertEqual(recorded_action.stdout, "recorded\n")
            self.assertEqual(recorded_action.args, commands.set_dpms_argv("DP-1", "off"))

    def test_live_mutation_uses_the_fixed_argv(self):
        completed = subprocess.CompletedProcess(["/usr/bin/hyprctl"], 0, "ok\n", "")
        with (
            patch.dict(os.environ, {"TAMLINUX_COMPOSITOR_LIVE_ACTIONS": "1"}, clear=False),
            patch.object(backend.subprocess, "run", return_value=completed) as run,
        ):
            backend.run("reload", None)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], commands.reload_argv())

    def test_backend_rejects_unknown_operations(self):
        with self.assertRaises(commands.CompositorCommandError):
            backend.run("dispatch", ["workspace", "1"])


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
        self.assertIn('hl.dsp.focus({ window = "address:', qml)
        self.assertIn(r"/^[A-Za-z0-9][A-Za-z0-9 ._+-]{0,63}$/", qml)
        self.assertIn(commands.APP_NAME_RE.pattern.strip("^$"), qml)
        self.assertIn('"on"', qml)
        self.assertIn('"off"', qml)
        self.assertNotIn("hl.dispatch", qml)
        self.assertNotIn('action = "enable"', qml)
        self.assertNotIn('action = "disable"', qml)
        self.assertIn("TAMLINUX_COMPOSITOR_LIVE_ACTIONS", qml)
        self.assertIn(r"/^[A-Za-z0-9._-]{1,64}$/", qml)
        self.assertIn(r"/^(?:[1-9]|10)$/", qml)
        self.assertIn(str(commands.BINDS_LIMIT), qml)
        self.assertIn(str(commands.KEYMAP_LIMIT), qml)
        self.assertIn(str(commands.DESCRIPTION_LIMIT), qml)
        self.assertIn("description:", qml)
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

    def test_helpers_do_not_build_hyprland_commands(self):
        root = WORKSPACE
        helpers = (
            root / "workspaces-fred-tamlinux" / "tam-desktop-mode",
            root / "monitor-fred-tamlinux" / "fred-monitor-layout",
            root / "monitor-fred-tamlinux" / "fred-monitor-state",
            root / "monitor-fred-tamlinux" / "fred-monitor-reset",
        )
        for path in helpers:
            text = path.read_text(encoding="utf-8")
            for banned in ("hyprctl", "hl.dsp", "hl.monitor"):
                self.assertNotIn(banned, text, path.name)

    def test_plugin_qml_reads_the_facade(self):
        root = WORKSPACE
        names = (
            "clock", "agents", "sysinfo", "weather", "tides",
            "keyboard", "monitor", "workspaces",
        )
        seen = 0
        for name in names:
            plugin = root / f"{name}-fred-tamlinux"
            self.assertTrue(plugin.is_dir(), name)
            for path in plugin.rglob("*.qml"):
                text = path.read_text(encoding="utf-8")
                seen += 1
                self.assertNotIn("Quickshell.Hyprland", text, path.name)
                self.assertNotIn("/usr/bin/hyprctl", text, path.name)
        self.assertGreater(seen, 0)

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
