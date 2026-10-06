# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline request/response challenges; no swaymsg or hyprctl execution."""

import ast
import json
import sys
import unittest
from pathlib import Path

HOST = Path(__file__).resolve().parents[1] / "shell" / "host"
sys.path.insert(0, str(HOST))

import compositor_commands as hyprland
from helper_contract import ContractError
import sway_helper_backend as sway


class RequestTests(unittest.TestCase):
    def test_read_plans_are_fixed_and_separate_from_mutations(self):
        self.assertEqual(sway.request_plan("monitors").query_argvs(), (
            ("/usr/bin/swaymsg", "-t", "get_outputs", "-r"),
            ("/usr/bin/swaymsg", "-t", "get_workspaces", "-r")))
        self.assertEqual(sway.request_plan("active-workspace").queries, ("get_workspaces",))
        self.assertEqual(sway.request_plan("reload").commands, ("reload",))
        with self.assertRaises(ContractError):
            sway.request_plan("monitors").command_argv()

    def test_160_is_shared_helper_range_not_shell_ui_range(self):
        hyprland.dispatch_focus_workspace_argv(160)
        plan = sway.request_plan("focus-workspace", 160)
        self.assertEqual(plan.commands, ("workspace --no-auto-back-and-forth number 160",))
        with self.assertRaises(hyprland.CompositorCommandError):
            hyprland.focus_workspace_argv(160)
        for value in [0, 161, True, 1.5, "1; exit"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                sway.request_plan("focus-workspace", value)

    def test_wire_fallback_names_have_explicit_plans(self):
        for name, payload in [("focus-workspace", 160), ("focus-output", "DP-2"),
                              ("move-window", [160, "stay"]), ("dpms", ["DP-2", "on"])]:
            with self.subTest(name=name):
                self.assertEqual(sway.request_plan(name, payload).commands,
                                 sway.request_plan(name + "-fallback", payload).commands)
        self.assertEqual(sway.request_plan("move-workspace-fallback", [160, "DP-2"]).commands,
                         ("workspace --no-auto-back-and-forth number 160",
                          "move workspace to output DP-2"))

    def test_move_follow_explicitly_selects_destination_without_toggle(self):
        move = "move --no-auto-back-and-forth container to workspace number 160"
        self.assertEqual(sway.request_plan("move-window", [160, "stay"]).commands, (move,))
        self.assertEqual(sway.request_plan("move-window", [160, True]).commands,
                         (move, "workspace --no-auto-back-and-forth number 160"))
        for follow in [1, [], None, "toggle"]:
            with self.subTest(follow=follow), self.assertRaises(ContractError):
                sway.request_plan("move-window", [160, follow])

    def test_power_is_not_disable_and_rejects_selector_or_injection(self):
        self.assertEqual(sway.request_plan("dpms", ["DP-2", False]).commands,
                         ("output DP-2 power off",))
        for name in ["*", "current", "left", "DP-2; exit", "DP-2\n"]:
            with self.subTest(name=name), self.assertRaises(ContractError):
                sway.request_plan("dpms", [name, "off"])
        for value in [0, None, "toggle", "off; exit"]:
            with self.subTest(value=value), self.assertRaises(ContractError):
                sway.request_plan("dpms", ["DP-2", value])

    def test_monitor_commands_keep_mode_hz_position_and_scale_bounded(self):
        self.assertEqual(sway.request_plan("monitor-rule",
                         ["DP-2", "1920x1080@59.94", "-1920x100", "1.125"]).commands,
                         ("output DP-2 enable", "output DP-2 mode 1920x1080@59.94Hz",
                          "output DP-2 pos -1920 100", "output DP-2 scale 1.125"))
        self.assertEqual(sway.request_plan("monitor-rule", ["DP-2", "disabled"]).commands,
                         ("output DP-2 disable",))
        for fields in [["DP-2", "bad"], ["DP-2", "1920x1080@60; exit", "0x0", 1],
                       ["DP-2", "1920x1080@60", "0x0; exit", 1],
                       ["DP-2", "1920x1080@60", "0x0", True],
                       ["DP-2", "1920x1080@60", "0x0", 10 ** 400]]:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                sway.request_plan("monitor-rule", fields)

    def test_unverified_transform_and_preferred_mode_are_not_guessed(self):
        self.assertEqual(sway.request_plan("monitor-rule",
                         ["DP-2", "1920x1080@60Hz", "0x0", 1, 0]).commands[-1],
                         "output DP-2 transform normal")
        for mode, transform in [("preferred", 0), ("1920x1080@60", 1),
                                ("1920x1080@60", 7)]:
            with self.subTest(mode=mode, transform=transform):
                with self.assertRaises(sway.UnsupportedOperation):
                    sway.request_plan("monitor-rule", ["DP-2", mode, "0x0", 1, transform])

    def test_windows_batch_order_and_single_argv_argument(self):
        plan = sway.request_plan("batch", [("focus-output", "DP-2"),
                                          ("focus-workspace", 160),
                                          ("move-workspace", "DP-1")])
        self.assertEqual(plan.command_argv(), ("/usr/bin/swaymsg", "-r", "--",
                         "focus output DP-2; workspace --no-auto-back-and-forth number 160; "
                         "move workspace to output DP-1"))
        for steps in [[], [("reload", None)], [("batch", [])], [("dpms", ["DP-2", "on"])],
                      [("focus-workspace", 1)] * 65]:
            with self.subTest(steps=steps), self.assertRaises(ContractError):
                sway.request_plan("batch", steps)

    def test_partial_batch_outcome_requires_recovery(self):
        plan = sway.request_plan("batch", [("focus-workspace", 160), ("focus-output", "DP-2")])
        outcome = plan.outcome('[{"success":true},{"success":false,"error":"missing output"}]')
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.succeeded_indexes, (0,))
        self.assertEqual(outcome.failed_indexes, (1,))
        with self.assertRaises(ContractError):
            plan.outcome('[{"success":true}]')

    def test_unknown_operations_and_unexpected_payloads_fail(self):
        self.assertEqual(len(sway.OPERATIONS), 18)
        for operation in ["config-errors", "rollinglog"]:
            with self.subTest(operation=operation), self.assertRaises(sway.UnsupportedOperation):
                sway.request_plan(operation)
        for operation, payload in [("exec", "exit"), ("monitors", []), ("reload", "file"),
                                   ([], None), ("move-window", [1])]:
            with self.subTest(operation=operation), self.assertRaises(ContractError):
                sway.request_plan(operation, payload)


class ReadTests(unittest.TestCase):
    def test_active_workspace_preserves_named_unknown_and_observed_160(self):
        row = {"name": "160:dev", "num": 160, "output": "DP-2", "visible": True, "focused": True}
        focus = sway.active_workspace(json.dumps([row]))
        self.assertEqual((focus.name, focus.number, focus.output), ("160:dev", 160, "DP-2"))
        focus = sway.active_workspace(json.dumps([{**row, "name": "chat", "num": -1}]))
        self.assertIsNone(focus.number)
        for rows in [[], [row, row], [{**row, "focused": "true"}], [{**row, "visible": False}]]:
            with self.subTest(rows=rows), self.assertRaises(ContractError):
                sway.active_workspace(json.dumps(rows))

    def test_monitors_all_preserves_disabled_unknowns(self):
        disabled = {"name": "DP-2", "active": False, "power": False,
                    "current_workspace": None, "rect": {"x": 0, "y": 0, "width": 0, "height": 0}}
        self.assertEqual(sway.monitor_facts(json.dumps([disabled]), "[]"), ())
        facts = sway.monitor_facts(json.dumps([disabled]), "[]", include_disabled=True)
        self.assertEqual(len(facts), 1)
        self.assertIsNone(facts[0].scale)
        self.assertIsNone(facts[0].pixel_mode)

    def test_candidate_cannot_start_a_process_or_write_config(self):
        forbidden = {"subprocess", "os", "socket", "shutil", "importlib"}
        for filename in ["helper_contract.py", "sway_helper_backend.py"]:
            tree = ast.parse((HOST / filename).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(forbidden & {name.name.split('.')[0] for name in node.names})
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or "").split('.')[0], forbidden)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"open", "exec", "eval", "__import__"})


if __name__ == "__main__":
    unittest.main()
