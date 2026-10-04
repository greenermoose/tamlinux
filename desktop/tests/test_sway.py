"""Sway argv and fixture snapshots. These tests do not run swaymsg."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP / "shell" / "host"))

import compositor_commands as hyprland  # noqa: E402
import sway_commands as commands  # noqa: E402
import sway_snapshot as snapshot  # noqa: E402

FIXTURE = DESKTOP / "fixtures" / "sway"


class CommandTests(unittest.TestCase):
    def test_read_and_action_commands_are_fixed(self):
        self.assertEqual(commands.inputs_argv(), ["/usr/bin/swaymsg", "-t", "get_inputs", "-r"])
        self.assertEqual(commands.outputs_argv(), ["/usr/bin/swaymsg", "-t", "get_outputs", "-r"])
        self.assertEqual(commands.workspaces_argv(), ["/usr/bin/swaymsg", "-t", "get_workspaces", "-r"])
        self.assertEqual(commands.focus_workspace_argv(4), ["/usr/bin/swaymsg", "workspace", "number", "4"])
        self.assertEqual(commands.focus_workspace_request(4), "workspace number 4")
        self.assertEqual(commands.focus_output_argv("DP-1"), ["/usr/bin/swaymsg", "focus", "output", "DP-1"])
        self.assertEqual(commands.focus_output_request("DP-1"), "focus output DP-1")
        self.assertEqual(
            commands.set_dpms_argv("HDMI-A-1", False),
            ["/usr/bin/swaymsg", "output", "HDMI-A-1", "power", "off"],
        )
        self.assertEqual(commands.set_dpms_request("HDMI-A-1", "on"), "output HDMI-A-1 power on")

    def test_rejects_bad_names_and_workspaces(self):
        for name in ("", "DP-1;rm", "../x", "DP 1", "a" * 65):
            with self.subTest(name=name):
                with self.assertRaises(hyprland.CompositorCommandError):
                    commands.focus_output_argv(name)
                with self.assertRaises(hyprland.CompositorCommandError):
                    commands.set_dpms_request(name, True)
        for workspace in (True, 0, 11, "1"):
            with self.subTest(workspace=workspace):
                with self.assertRaises(hyprland.CompositorCommandError):
                    commands.focus_workspace_argv(workspace)  # type: ignore[arg-type]
        with self.assertRaises(hyprland.CompositorCommandError):
            commands.set_dpms_argv("DP-1", "disable")

    def test_modules_do_not_launch_processes(self):
        for module in (commands, snapshot):
            text = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("subprocess", text)
            self.assertNotIn("os.system", text)
            self.assertNotIn("Popen", text)


class SnapshotTests(unittest.TestCase):
    def test_fixture_prefers_ext_workspace(self):
        data = snapshot.snapshot_from_directory(FIXTURE)
        self.assertEqual([item["name"] for item in data["outputs"]], ["DP-1", "HDMI-A-1"])
        self.assertEqual(data["focusedOutputName"], "DP-1")
        self.assertEqual(data["focusedWorkspaceId"], 1)
        self.assertEqual([space["id"] for space in data["workspaces"]], [1, 4])
        self.assertEqual(data["workspaces"][0]["windows"], [{"className": "foot", "title": "shell"}])
        self.assertFalse(data["outputs"][1]["dpmsOn"])
        self.assertEqual(data["outputs"][0]["description"], "Dell S2725DSM")
        self.assertEqual(data["outputs"][0]["activeWorkspaceId"], 1)
        self.assertEqual(data["activeKeymap"], "English (US)")
        binds = json.loads(data["bindingsText"])
        self.assertEqual(binds, [
            {"modmask": 64, "key": "1", "description": "", "dispatcher": "workspace", "arg": "number 1", "submap": ""},
            {"modmask": 64, "key": "4", "description": "", "dispatcher": "workspace", "arg": "number 4", "submap": ""},
            {"modmask": 65, "key": "1", "description": "", "dispatcher": "focus", "arg": "output DP-1", "submap": ""},
        ])
        self.assertNotIn("exec", data["bindingsText"])
        self.assertNotIn("foot", data["bindingsText"])
        self.assertNotIn("scratchpad", data["bindingsText"])

    def test_empty_ext_workspace_uses_i3(self):
        data = snapshot.snapshot_from_parts(
            {"windowsets": []},
            [{"name": "DP-1", "focused": True, "power": True, "current_workspace": "2", "rect": {"x": 0, "y": 0}}],
            [{"num": 2, "focused": True, "output": "DP-1", "windows": [{"app_id": "foot", "name": "shell"}]}],
            [{"type": "keyboard", "xkb_active_layout_name": "German"}],
            "bindsym Mod4+2 workspace number 2\n",
        )
        self.assertEqual([space["id"] for space in data["workspaces"]], [2])
        self.assertEqual(data["focusedWorkspaceId"], 2)
        self.assertEqual(data["workspaces"][0]["windows"][0]["className"], "foot")
        self.assertEqual(data["activeKeymap"], "German")
        self.assertIn('"arg":"number 2"', data["bindingsText"])

    def test_bindings_drop_other_commands_and_cap(self):
        text = "\n".join([
            "bindsym Mod4+Return exec foot",
            "include /etc/sway/config",
            "bindsym $mod+1 workspace number 1",
            "bindsym Mod4+1 workspace number 1; exec true",
            "bindsym Mod4+9 workspace number 9",
        ])
        encoded = snapshot.parse_bindings(text)
        self.assertEqual(json.loads(encoded)[0]["arg"], "number 9")
        self.assertEqual(len(json.loads(encoded)), 1)
        huge = "bindsym Mod4+1 workspace number 1\n" * 20000
        capped = snapshot.parse_bindings(huge)
        self.assertLessEqual(len(capped), snapshot.BINDS_LIMIT)

    def test_keymap_is_bounded(self):
        self.assertEqual(snapshot.active_keymap([{"type": "pointer"}]), "")
        self.assertEqual(snapshot.active_keymap("x" * (snapshot.DEVICES_LIMIT + 1)), "")
        long_name = "k" * 200
        self.assertEqual(len(snapshot.active_keymap([{"xkb_active_layout_name": long_name}])), snapshot.KEYMAP_LIMIT)

    def test_rejects_a_relative_fixture_directory(self):
        with self.assertRaises(hyprland.CompositorCommandError):
            snapshot.snapshot_from_directory("fixtures/sway")
        with self.assertRaises(hyprland.CompositorCommandError):
            snapshot.require_directory("/tmp/../etc")


class SourceBoundaryTests(unittest.TestCase):
    def test_adapter_matches_the_command_text(self):
        qml = (DESKTOP / "shell" / "host" / "SwayAdapter.qml").read_text(encoding="utf-8")
        self.assertIn("import Quickshell.WindowManager", qml)
        self.assertIn("import Quickshell.I3", qml)
        self.assertIn('"/usr/bin/swaymsg", "-t", "get_inputs", "-r"', qml)
        self.assertIn('"/usr/bin/swaymsg", "-t", "get_outputs", "-r"', qml)
        self.assertIn('"/usr/bin/swaymsg", "-t", "get_workspaces", "-r"', qml)
        self.assertIn('"/usr/bin/swaymsg", "workspace", "number"', qml)
        self.assertIn('"/usr/bin/swaymsg", "focus", "output"', qml)
        self.assertIn('"/usr/bin/swaymsg", "output", output, "power", word', qml)
        self.assertIn('return "workspace number "', qml)
        self.assertIn('return "focus output "', qml)
        self.assertIn('return "output " + output + " power "', qml)
        self.assertIn("I3.dispatch(focusWorkspaceRequest(number))", qml)
        self.assertIn("I3.dispatch(focusOutputRequest(output))", qml)
        self.assertIn("I3.dispatch(setDpmsRequest(output, word))", qml)
        self.assertIn("WindowManager.windowsets", qml)
        self.assertIn("workspacesFromI3", qml)
        self.assertLess(qml.index("workspacesFromWindowsets"), qml.index("workspacesFromI3"))
        self.assertIn('["/usr/bin/python3", "-I", root + "/sway_snapshot.py", fixture]', qml)
        self.assertIn("TAMLINUX_COMPOSITOR_LIVE_ACTIONS", qml)
        self.assertNotIn("hyprctl", qml)
        self.assertNotIn("sh -c", qml)
        self.assertNotIn("bash", qml)

    def test_only_the_sway_adapter_imports_sway_modules(self):
        adapter = DESKTOP / "shell" / "host" / "SwayAdapter.qml"
        seen = False
        for path in DESKTOP.rglob("*.qml"):
            text = path.read_text(encoding="utf-8")
            if path == adapter:
                seen = True
                continue
            self.assertNotIn("Quickshell.I3", text, path.name)
            self.assertNotIn("Quickshell.WindowManager", text, path.name)
            self.assertNotIn("swaymsg", text, path.name)
        self.assertTrue(seen)
        facade = (DESKTOP / "shell" / "host" / "Compositor.qml").read_text(encoding="utf-8")
        self.assertIn('backendName === "sway" ? "SwayAdapter.qml" : "HyprlandAdapter.qml"', facade)
        self.assertIn("Qt.createComponent", facade)

    def test_launcher_selects_one_compositor(self):
        text = (DESKTOP / "launch-clock-proof").read_text(encoding="utf-8")
        self.assertIn('env.pop("TAMLINUX_COMPOSITOR_LIVE_ACTIONS", None)', text)
        self.assertIn('env.pop("TAMLINUX_SWAY_FIXTURE", None)', text)
        self.assertIn('"TAMLINUX_COMPOSITOR": compositor', text)
        self.assertIn('if args.compositor == "sway":', text)
        self.assertIn('compositor: str = "hyprland"', text)


if __name__ == "__main__":
    unittest.main()
