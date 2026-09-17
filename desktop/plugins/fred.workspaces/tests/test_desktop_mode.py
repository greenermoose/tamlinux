import importlib.util
from importlib.machinery import SourceFileLoader
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import call, patch


HELPER = Path(__file__).resolve().parents[1] / "omarchy-desktop-mode"
LOADER = SourceFileLoader("omarchy_desktop_mode", str(HELPER))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
desktop_mode = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(desktop_mode)


def completed(returncode=0, stdout="ok\n", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class MappingTests(unittest.TestCase):
    def test_workspace_sets_for_one_two_three_and_four_monitors(self):
        expected = {
            (1, 1): [1],
            (2, 1): [2],
            (5, 1): [5],
            (1, 2): [1, 2],
            (2, 2): [3, 4],
            (5, 2): [9, 10],
            (1, 3): [1, 2, 3],
            (2, 3): [4, 5, 6],
            (5, 3): [13, 14, 15],
            (2, 4): [5, 6, 7, 8],
            (10, 3): [28, 29, 30],
        }
        for coordinates, workspaces in expected.items():
            with self.subTest(coordinates=coordinates):
                self.assertEqual(desktop_mode.workspace_ids(*coordinates), workspaces)

    def test_inverse_desktop_mapping(self):
        for set_size in (1, 2, 3, 4):
            for desktop in (1, 2, 5, 10):
                for workspace in desktop_mode.workspace_ids(desktop, set_size):
                    self.assertEqual(
                        desktop_mode.desktop_for_workspace(workspace, set_size),
                        desktop,
                    )

    def test_invalid_mapping_coordinates_are_rejected(self):
        for args in ((0, 0, 1), (1, -1, 1), (1, 1, 1), (1, 0, 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                desktop_mode.workspace_for_monitor(*args)


class MonitorDiscoveryTests(unittest.TestCase):
    def test_geometry_order_filtering_and_tie_breaks(self):
        data = [
            {"name": "RIGHT", "x": 300, "y": 0},
            {"name": "TIE-B", "x": 100, "y": 50},
            {"name": "LEFT", "x": -200, "y": 20},
            {"name": "TIE-A", "x": 100, "y": 50},
            {"name": "MIRROR", "x": 400, "y": 0, "mirrorOf": "RIGHT"},
            {"name": "DISABLED", "x": 500, "y": 0, "disabled": True},
            {"name": "bad name", "x": 0, "y": 0},
            {"name": "NO-X", "y": 0},
            {"name": "LEFT", "x": 900, "y": 0},
        ]
        self.assertEqual(
            desktop_mode.ordered_monitors(data),
            ["LEFT", "TIE-A", "TIE-B", "RIGHT"],
        )

    def test_invalid_json_shape_and_monitor_cap(self):
        self.assertEqual(desktop_mode.ordered_monitors({"name": "DP-1"}), [])
        data = [{"name": f"DP-{index}", "x": index, "y": 0} for index in range(20)]
        self.assertEqual(len(desktop_mode.ordered_monitors(data)), 16)

    def test_discovery_rejects_failed_oversized_and_malformed_output(self):
        results = (
            completed(returncode=1),
            completed(stdout="[" + (" " * desktop_mode.MAX_HYPRCTL_OUTPUT) + "]"),
            completed(stdout="not-json"),
        )
        for result in results:
            with self.subTest(result=result), patch.object(desktop_mode, "run_hyprctl", return_value=result):
                self.assertEqual(desktop_mode.discover_monitors(), [])

    def test_resolve_writes_versioned_monitor_set_and_outer_endpoints(self):
        monitors = ["DP-2", "DP-1", "HDMI-A-1"]
        with (
            patch.object(desktop_mode, "load_full_config", return_value=("", "", 0, "")),
            patch.object(desktop_mode, "discover_monitors", return_value=monitors),
            patch.object(desktop_mode, "read_state_file", return_value=""),
            patch.object(desktop_mode, "atomic_write_state") as write_state,
            patch.dict(desktop_mode.os.environ, {}, clear=True),
        ):
            self.assertEqual(
                desktop_mode.resolve_monitors(),
                (monitors, "DP-2", "HDMI-A-1"),
            )
        payload = json.loads(write_state.call_args.args[1])
        self.assertEqual(payload["version"], 2)
        self.assertEqual(payload["monitors"], monitors)
        self.assertEqual(payload["count"], 3)
        self.assertEqual(payload["left"], "DP-2")
        self.assertEqual(payload["right"], "HDMI-A-1")

    def test_failed_discovery_does_not_reuse_configured_endpoints(self):
        with (
            patch.object(desktop_mode, "load_full_config", return_value=("DP-2", "HDMI-A-1", 0, "")),
            patch.object(desktop_mode, "discover_monitors", return_value=[]),
            patch.object(desktop_mode, "atomic_write_state") as write_state,
            patch.dict(desktop_mode.os.environ, {}, clear=True),
        ):
            self.assertEqual(desktop_mode.resolve_monitors(), ([], "", ""))
            write_state.assert_not_called()


class DispatchTests(unittest.TestCase):
    MONITORS = ["DP-2", "DP-1", "HDMI-A-1"]

    def test_batch_uses_one_bounded_hyprctl_request(self):
        expressions = [
            'hl.dsp.focus({ monitor = "DP-2" })',
            'hl.dsp.focus({ workspace = "4" })',
        ]
        with patch.object(desktop_mode, "run_hyprctl", return_value=completed()) as run:
            self.assertTrue(desktop_mode.dispatch_batch(expressions))
        run.assert_called_once_with(
            [
                "--batch",
                'dispatch hl.dsp.focus({ monitor = "DP-2" }); '
                'dispatch hl.dsp.focus({ workspace = "4" })',
            ],
            timeout=5.0,
        )

    def test_three_monitor_switch_places_contiguous_set_and_restores_focus(self):
        with (
            patch.object(desktop_mode, "focused_monitor", return_value="DP-1"),
            patch.object(desktop_mode, "dispatch_batch", return_value=True) as batch,
            patch.object(
                desktop_mode,
                "monitor_snapshot",
                return_value=({"DP-2": 4, "DP-1": 5, "HDMI-A-1": 6}, "DP-1"),
            ),
            patch.object(desktop_mode, "atomic_write_state") as write_state,
        ):
            self.assertTrue(desktop_mode.switch_windows(2, self.MONITORS))
        expressions = batch.call_args.args[0]
        self.assertIn('hl.dsp.focus({ workspace = "4" })', expressions)
        self.assertIn('hl.dsp.workspace.move({ monitor = "DP-1" })', expressions)
        self.assertIn('hl.dsp.focus({ workspace = "6" })', expressions)
        self.assertEqual(expressions[-1], 'hl.dsp.focus({ monitor = "DP-1" })')
        write_state.assert_called_once_with("desktop-current", "2\n")

    def test_two_monitor_switch_preserves_pair_mapping(self):
        with (
            patch.object(desktop_mode, "focused_monitor", return_value="LEFT"),
            patch.object(desktop_mode, "dispatch_batch", return_value=True) as batch,
            patch.object(desktop_mode, "monitor_snapshot", return_value=({"LEFT": 9, "RIGHT": 10}, "LEFT")),
            patch.object(desktop_mode, "atomic_write_state"),
        ):
            self.assertTrue(desktop_mode.switch_windows(5, ["LEFT", "RIGHT"]))
        expressions = batch.call_args.args[0]
        self.assertIn('hl.dsp.focus({ workspace = "9" })', expressions)
        self.assertIn('hl.dsp.focus({ workspace = "10" })', expressions)

    def test_failed_batch_does_not_advance_current_state(self):
        with (
            patch.object(desktop_mode, "focused_monitor", return_value="DP-2"),
            patch.object(desktop_mode, "dispatch_batch", return_value=False),
            patch.object(
                desktop_mode,
                "monitor_snapshot",
                return_value=({"DP-2": 4, "DP-1": 5, "HDMI-A-1": 6}, "DP-2"),
            ),
            patch.object(desktop_mode, "atomic_write_state") as write_state,
        ):
            self.assertFalse(desktop_mode.switch_windows(2, self.MONITORS))
        write_state.assert_not_called()

    def test_verification_failure_does_not_advance_current_state(self):
        with (
            patch.object(desktop_mode, "focused_monitor", return_value="DP-2"),
            patch.object(desktop_mode, "dispatch_batch", return_value=True),
            patch.object(
                desktop_mode,
                "monitor_snapshot",
                return_value=({"DP-2": 1, "DP-1": 5, "HDMI-A-1": 6}, "DP-2"),
            ),
            patch.object(desktop_mode, "atomic_write_state") as write_state,
        ):
            self.assertFalse(desktop_mode.switch_windows(2, self.MONITORS))
        write_state.assert_not_called()

    def test_discovery_failure_switches_one_workspace_only(self):
        with (
            patch.object(desktop_mode, "focused_monitor", return_value=""),
            patch.object(desktop_mode, "dispatch_focus_workspace", return_value=True) as focus,
            patch.object(desktop_mode, "place_workspace") as place,
            patch.object(desktop_mode, "atomic_write_state"),
        ):
            self.assertTrue(desktop_mode.switch_windows(3, []))
        focus.assert_called_once_with(3)
        place.assert_not_called()

    def test_move_uses_focused_monitor_position_then_activates_set(self):
        with (
            patch.object(desktop_mode, "current_mode", return_value="windows"),
            patch.object(desktop_mode, "focused_monitor", return_value="DP-1"),
            patch.object(desktop_mode, "dispatch_move_window", return_value=True) as move,
            patch.object(desktop_mode, "switch_windows", return_value=True) as switch,
            patch.object(desktop_mode, "dispatch_focus_monitor", return_value=True) as focus,
        ):
            desktop_mode.move_window(2, False, self.MONITORS, "DP-2", "HDMI-A-1")
        move.assert_called_once_with(5, False)
        switch.assert_called_once_with(2, self.MONITORS)
        focus.assert_called_once_with("DP-1")

    def test_silent_move_uses_right_workspace_without_switching_set(self):
        with (
            patch.object(desktop_mode, "current_mode", return_value="windows"),
            patch.object(desktop_mode, "focused_monitor", return_value="HDMI-A-1"),
            patch.object(desktop_mode, "dispatch_move_window", return_value=True) as move,
            patch.object(desktop_mode, "switch_windows") as switch,
            patch.object(desktop_mode, "dispatch_focus_monitor") as focus,
        ):
            desktop_mode.move_window(2, True, self.MONITORS, "DP-2", "HDMI-A-1")
        move.assert_called_once_with(6, False)
        switch.assert_not_called()
        focus.assert_not_called()

    def test_dispatch_uses_fallback_when_lua_dispatch_fails(self):
        with patch.object(
            desktop_mode,
            "run_hyprctl",
            side_effect=[completed(returncode=1, stderr="error"), completed()],
        ) as run:
            self.assertTrue(desktop_mode.dispatch_focus_workspace(4))
        self.assertEqual(
            run.call_args_list,
            [
                call(["dispatch", 'hl.dsp.focus({ workspace = "4" })']),
                call(["dispatch", "workspace", "4"]),
            ],
        )


class ResilienceTests(unittest.TestCase):
    CANONICAL_TOPO = [
        {"output": "DP-2", "mode": "1920x1080@60", "position": "0x720", "scale": 1.5, "x": 0, "y": 720},
        {"output": "DP-1", "mode": "2560x1440@60", "position": "1280x0", "scale": 1.0, "x": 1280, "y": 0},
        {"output": "HDMI-A-1", "mode": "1920x1080@60", "position": "3840x360", "scale": 1.0, "x": 3840, "y": 360},
    ]

    def test_topology_anchored_workspace_mapping_normal(self):
        with (
            patch.object(desktop_mode, "load_canonical_topology", return_value=self.CANONICAL_TOPO),
            patch.object(desktop_mode, "discover_monitors", return_value=["DP-2", "DP-1", "HDMI-A-1"]),
            patch.object(desktop_mode, "atomic_write_state"),
        ):
            monitors, left, right, slots, topo_size, _ = desktop_mode.resolve_topology()
            self.assertEqual(topo_size, 3)
            self.assertEqual(slots, {"DP-2": 0, "DP-1": 1, "HDMI-A-1": 2})

            self.assertEqual(desktop_mode.workspace_for_slot(1, slots["DP-2"], topo_size), 1)
            self.assertEqual(desktop_mode.workspace_for_slot(1, slots["DP-1"], topo_size), 2)
            self.assertEqual(desktop_mode.workspace_for_slot(1, slots["HDMI-A-1"], topo_size), 3)

            self.assertEqual(desktop_mode.workspace_for_slot(2, slots["DP-2"], topo_size), 4)
            self.assertEqual(desktop_mode.workspace_for_slot(2, slots["DP-1"], topo_size), 5)
            self.assertEqual(desktop_mode.workspace_for_slot(2, slots["HDMI-A-1"], topo_size), 6)

            self.assertEqual(desktop_mode.workspace_for_slot(5, slots["DP-2"], topo_size), 13)
            self.assertEqual(desktop_mode.workspace_for_slot(5, slots["DP-1"], topo_size), 14)
            self.assertEqual(desktop_mode.workspace_for_slot(5, slots["HDMI-A-1"], topo_size), 15)

    def test_configured_topology_size_widens_the_grid(self):
        # A configured topology_size larger than the canonical monitor list
        # must reach resolve_topology (it used to be dropped on the way).
        with (
            patch.object(desktop_mode, "load_full_config", return_value=("", "", 4, "")),
            patch.object(desktop_mode, "load_canonical_topology", return_value=self.CANONICAL_TOPO),
            patch.object(desktop_mode, "discover_monitors", return_value=["DP-2", "DP-1", "HDMI-A-1"]),
            patch.object(desktop_mode, "read_state_file", return_value=""),
            patch.object(desktop_mode, "atomic_write_state") as write_state,
            patch.dict(desktop_mode.os.environ, {}, clear=True),
        ):
            _, _, _, slots, topo_size, _ = desktop_mode.resolve_topology()
            self.assertEqual(topo_size, 4)
            self.assertEqual(slots, {"DP-2": 0, "DP-1": 1, "HDMI-A-1": 2})
            self.assertEqual(desktop_mode.workspace_for_slot(2, slots["DP-1"], topo_size), 6)
        payload = json.loads(write_state.call_args.args[1])
        self.assertEqual(payload["topology_size"], 4)

    def test_slot_stability_when_center_monitor_drops(self):
        with (
            patch.object(desktop_mode, "load_canonical_topology", return_value=self.CANONICAL_TOPO),
            patch.object(desktop_mode, "discover_monitors", return_value=["DP-2", "HDMI-A-1"]),
            patch.object(desktop_mode, "atomic_write_state") as write_state,
        ):
            monitors, left, right, slots, topo_size, _ = desktop_mode.resolve_topology()
            self.assertEqual(topo_size, 3)
            self.assertEqual(slots, {"DP-2": 0, "HDMI-A-1": 2})

            self.assertEqual(desktop_mode.workspace_for_slot(1, slots["DP-2"], topo_size), 1)
            self.assertEqual(desktop_mode.workspace_for_slot(1, slots["HDMI-A-1"], topo_size), 3)

            self.assertEqual(desktop_mode.workspace_for_slot(2, slots["DP-2"], topo_size), 4)
            self.assertEqual(desktop_mode.workspace_for_slot(2, slots["HDMI-A-1"], topo_size), 6)

            self.assertEqual(desktop_mode.workspace_for_slot(5, slots["DP-2"], topo_size), 13)
            self.assertEqual(desktop_mode.workspace_for_slot(5, slots["HDMI-A-1"], topo_size), 15)
            self.assertEqual(desktop_mode.desktop_for_workspace(14, topo_size), 5)

            payload = json.loads(write_state.call_args.args[1])
            self.assertTrue(payload["degraded"])
            self.assertEqual(payload["count"], 2)
            self.assertEqual(payload["topology_size"], 3)

    def test_geometric_gap_compression_when_center_drops(self):
        live_monitors = [
            {"name": "DP-2", "x": 0, "y": 720, "width": 1920, "height": 1080, "scale": 1.5, "refreshRate": 60.0},
            {"name": "HDMI-A-1", "x": 3840, "y": 360, "width": 1920, "height": 1080, "scale": 1.0, "refreshRate": 60.0},
        ]
        with (
            patch.object(desktop_mode, "run_hyprctl", side_effect=[
                completed(stdout=json.dumps(live_monitors)),
                completed(stdout="ok"),
            ]) as run_ctl,
        ):
            desktop_mode.ensure_contiguous_layout(["DP-2", "HDMI-A-1"], self.CANONICAL_TOPO)

            self.assertEqual(run_ctl.call_count, 2)
            eval_arg = run_ctl.call_args_list[1].args[0]
            self.assertEqual(eval_arg[0], "eval")
            self.assertIn('output = "HDMI-A-1"', eval_arg[1])
            self.assertIn('position = "1280x360"', eval_arg[1])

    def test_geometric_layout_restoration_when_all_monitors_present(self):
        live_monitors = [
            {"name": "DP-2", "x": 0, "y": 720, "width": 1920, "height": 1080, "scale": 1.5, "refreshRate": 60.0},
            {"name": "DP-1", "x": 1280, "y": 0, "width": 2560, "height": 1440, "scale": 1.0, "refreshRate": 60.0},
            {"name": "HDMI-A-1", "x": 1280, "y": 360, "width": 1920, "height": 1080, "scale": 1.0, "refreshRate": 60.0},
        ]
        with (
            patch.object(desktop_mode, "run_hyprctl", side_effect=[
                completed(stdout=json.dumps(live_monitors)),
                completed(stdout="ok"),
            ]) as run_ctl,
        ):
            desktop_mode.ensure_contiguous_layout(["DP-2", "DP-1", "HDMI-A-1"], self.CANONICAL_TOPO)

            self.assertEqual(run_ctl.call_count, 2)
            eval_arg = run_ctl.call_args_list[1].args[0]
            self.assertIn('output = "HDMI-A-1"', eval_arg[1])
            self.assertIn('position = "3840x360"', eval_arg[1])

    def test_switch_windows_degraded_two_monitors_preserves_slots(self):
        with (
            patch.object(desktop_mode, "load_canonical_topology", return_value=self.CANONICAL_TOPO),
            patch.object(desktop_mode, "focused_monitor", return_value="DP-2"),
            patch.object(desktop_mode, "dispatch_batch", return_value=True) as batch,
            patch.object(
                desktop_mode,
                "monitor_snapshot",
                return_value=({"DP-2": 4, "HDMI-A-1": 6}, "DP-2"),
            ),
            patch.object(desktop_mode, "atomic_write_state") as write_state,
        ):
            self.assertTrue(desktop_mode.switch_windows(2, ["DP-2", "HDMI-A-1"]))

        expressions = batch.call_args.args[0]
        self.assertIn('hl.dsp.focus({ workspace = "4" })', expressions)
        self.assertIn('hl.dsp.focus({ workspace = "6" })', expressions)
        self.assertNotIn('hl.dsp.focus({ workspace = "5" })', expressions)
        write_state.assert_called_once_with("desktop-current", "2\n")

    def test_reconcile_syncs_current_desktop_on_returned_display(self):
        with (
            patch.object(desktop_mode, "resolve_topology", return_value=(
                ["DP-2", "DP-1", "HDMI-A-1"], "DP-2", "HDMI-A-1",
                {"DP-2": 0, "DP-1": 1, "HDMI-A-1": 2}, 3, ["DP-2", "DP-1", "HDMI-A-1"]
            )),
            patch.object(desktop_mode, "load_canonical_topology", return_value=self.CANONICAL_TOPO),
            patch.object(desktop_mode, "ensure_contiguous_layout"),
            patch.object(desktop_mode, "current_mode", return_value="windows"),
            patch.object(desktop_mode, "read_state_file", return_value="2"),
            patch.object(desktop_mode, "switch_windows", return_value=True) as switch,
            patch.object(desktop_mode, "write_desktop_monitors_state"),
        ):
            desktop_mode.reconcile()
            switch.assert_called_once_with(2, ["DP-2", "DP-1", "HDMI-A-1"], {"DP-2": 0, "DP-1": 1, "HDMI-A-1": 2}, 3)


if __name__ == "__main__":
    unittest.main()
