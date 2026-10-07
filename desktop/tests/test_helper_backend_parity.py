# SPDX-License-Identifier: GPL-3.0-or-later
"""Fixture parity and public request boundaries, not live/hardware parity."""

import ast
import dataclasses
import json
from pathlib import Path
import sys
import unittest

HOST = Path(__file__).resolve().parents[1] / "shell" / "host"
sys.path.insert(0, str(HOST))
import hyprland_helper_backend as hypr
import sway_helper_backend as sway


class RequestParityTests(unittest.TestCase):
    def test_candidate_has_no_process_or_config_write_api(self):
        tree = ast.parse((HOST / "hyprland_helper_backend.py").read_text())
        forbidden = {"subprocess", "os", "socket", "shutil", "importlib"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse(forbidden & {name.name.split('.')[0] for name in node.names})
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split('.')[0], forbidden)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"open", "exec", "eval", "__import__"})

    def test_named_helper_surface_matches(self):
        self.assertEqual(hypr.OPERATIONS, sway.OPERATIONS)
        for operation in ["monitors", "monitors-all", "active-workspace"]:
            for adapter in [hypr, sway]:
                with self.subTest(operation=operation, adapter=adapter.__name__):
                    plan = adapter.request_plan(operation)
                    self.assertTrue(plan.query_argvs())
                    self.assertFalse(plan.commands)
                    with self.assertRaises(ValueError):
                        plan.command_argv()

    def test_shared_mutations_have_bounded_wire_requests(self):
        requests = [("focus-workspace", "160"), ("focus-output", "DP-2"),
                    ("move-window", [160, "follow"]), ("move-workspace", "DP-2"),
                    ("move-workspace-fallback", [160, "DP-2"]),
                    ("dpms", ["DP-2", False]), ("reload", None),
                    ("monitor-rule", ["DP-2", "1920x1080@59.94", "-1920x100", "1.125", 0]),
                    ("monitor-rule", ["DP-2", "disabled"])]
        for operation, payload in requests:
            for adapter, binary in [(hypr, "/usr/bin/hyprctl"), (sway, "/usr/bin/swaymsg")]:
                with self.subTest(operation=operation, adapter=adapter.__name__):
                    plan = adapter.request_plan(operation, payload)
                    self.assertTrue(plan.commands)
                    self.assertFalse(plan.queries)
                    self.assertEqual(plan.command_argv()[0], binary)

    def test_follow_and_power_have_equal_boolean_and_text_semantics(self):
        for operation, target, true_word, false_word in [
                ("move-window", 160, "follow", "stay"), ("dpms", "DP-2", "on", "off")]:
            for adapter in [hypr, sway]:
                with self.subTest(operation=operation, adapter=adapter.__name__):
                    self.assertEqual(adapter.request_plan(operation, [target, True]),
                                     adapter.request_plan(operation, [target, true_word]))
                    self.assertEqual(adapter.request_plan(operation, [target, False]),
                                     adapter.request_plan(operation, [target, false_word]))
                    self.assertNotEqual(adapter.request_plan(operation, [target, True]).commands,
                                        adapter.request_plan(operation, [target, False]).commands)

    def test_hyprland_uses_existing_lua_and_explicit_fallback_dispatches(self):
        self.assertEqual(hypr.request_plan("focus-workspace", 160).command_argv(),
            ("/usr/bin/hyprctl", "dispatch", 'hl.dsp.focus({ workspace = "160" })'))
        self.assertEqual(hypr.request_plan("focus-workspace-fallback", 160).command_argv(),
            ("/usr/bin/hyprctl", "dispatch", "workspace", "160"))
        self.assertEqual(hypr.request_plan("move-window-fallback", [160, "stay"]).command_argv(),
            ("/usr/bin/hyprctl", "dispatch", "movetoworkspacesilent", "160"))
        self.assertEqual(hypr.request_plan("dpms-fallback", ["DP-2", "off"]).command_argv(),
            ("/usr/bin/hyprctl", "dispatch", "dpms", "off", "DP-2"))

    def test_windows_batch_retains_order_without_generic_dispatch(self):
        plan = hypr.request_plan("batch", [["focus-output", "DP-2"],
                       ["focus-workspace", 160], ["move-workspace", "DP-1"]])
        self.assertEqual(plan.command_argv(), ("/usr/bin/hyprctl", "--batch",
            'dispatch hl.dsp.focus({ monitor = "DP-2" }); '
            'dispatch hl.dsp.focus({ workspace = "160" }); '
            'dispatch hl.dsp.workspace.move({ monitor = "DP-1" })'))
        for adapter in [hypr, sway]:
            for payload in [[], [["exec", "exit"]], [["dpms", ["DP-2", "on"]]],
                            [["focus-workspace", 1]] * 65]:
                with self.subTest(adapter=adapter.__name__, payload=payload), self.assertRaises(ValueError):
                    adapter.request_plan("batch", payload)

    def test_both_adapters_reject_injection_selectors_and_wrong_types(self):
        requests = [("focus-workspace", 0), ("focus-workspace", 161),
                    ("focus-workspace", True), ("focus-workspace", "1; exit"),
                    ("focus-output", None), ("focus-output", "left"),
                    ("focus-output", "DP-2\n"), ("focus-output", "DP-2; exit"),
                    ("move-window", [1, 1]), ("move-window", [1, []]),
                    ("dpms", ["DP-2", 0]), ("dpms", ["DP-2", None]),
                    ("monitor-rule", ["DP-2", "bad"]),
                    ("monitor-rule", ["DP-2", "1920x1080@60", "0x0", True]),
                    ("monitor-rule", ["DP-2", "1920x1080@60", "0x0", 10 ** 400]),
                    ("monitors", []), ("reload", "full-reset"), ([], None)]
        for operation, payload in requests:
            for adapter in [hypr, sway]:
                with self.subTest(operation=operation, adapter=adapter.__name__), self.assertRaises(ValueError):
                    adapter.request_plan(operation, payload)

    def test_capability_differences_are_visible(self):
        for operation in ["config-errors", "rollinglog"]:
            self.assertTrue(hypr.request_plan(operation).queries)
            with self.assertRaises(sway.UnsupportedOperation):
                sway.request_plan(operation)
        for mode, transform in [("preferred", 0), ("1920x1080@60", 7)]:
            payload = ["DP-2", mode, "0x0", 1, transform]
            self.assertTrue(hypr.request_plan("monitor-rule", payload).commands)
            with self.assertRaises(sway.UnsupportedOperation):
                sway.request_plan("monitor-rule", payload)

    def test_recorded_text_never_means_compositor_success(self):
        for adapter in [hypr, sway]:
            plan = adapter.request_plan("focus-workspace", 160)
            try:
                result = plan.outcome("recorded\n")
            except ValueError:
                continue
            self.assertFalse(result.ok)


class FactParityTests(unittest.TestCase):
    def test_equivalent_scaled_rotated_powered_off_monitor_facts(self):
        h = [{"name": "DP-2", "width": 3840, "height": 2160, "refreshRate": 59.94,
              "x": -1080, "y": 100, "scale": 2, "transform": 1, "focused": True,
              "disabled": False, "dpmsStatus": False,
              "activeWorkspace": {"id": 160, "name": "160:dev"},
              "availableModes": ["3840x2160@59.94Hz"]}]
        s = [{"name": "DP-2", "active": True, "power": False, "scale": 2,
              "transform": "90", "current_workspace": "160:dev",
              "rect": {"x": -1080, "y": 100, "width": 1080, "height": 1920},
              "current_mode": {"width": 3840, "height": 2160, "refresh": 59940},
              "modes": [{"width": 3840, "height": 2160, "refresh": 59940}]}]
        w = [{"name": "160:dev", "num": 160, "output": "DP-2", "visible": True, "focused": True}]
        self.assertEqual(hypr.monitor_facts(json.dumps(h)),
                         sway.monitor_facts(json.dumps(s), json.dumps(w)))

    def test_disabled_output_unknowns_match_despite_stale_hyprland_values(self):
        h = [{"name": "DP-2", "disabled": True, "focused": False,
              "dpmsStatus": True, "x": 0, "y": 0, "width": 1920, "height": 1080,
              "scale": 1, "transform": 0, "activeWorkspace": {"id": 1, "name": "1"}}]
        s = [{"name": "DP-2", "active": False, "power": False, "current_workspace": None,
              "rect": {"x": 0, "y": 0, "width": 0, "height": 0}}]
        self.assertEqual(hypr.monitor_facts(json.dumps(h), include_disabled=True),
                         sway.monitor_facts(json.dumps(s), "[]", include_disabled=True))

    def test_named_workspace_focus_maps_to_equal_common_fields(self):
        h = {"id": -1337, "name": "chat", "monitor": "DP-2"}
        s = [{"num": -1, "name": "chat", "output": "DP-2", "focused": True, "visible": True}]
        self.assertEqual(dataclasses.asdict(hypr.active_workspace(json.dumps(h))),
                         dataclasses.asdict(sway.active_workspace(json.dumps(s))))


if __name__ == "__main__":
    unittest.main()
