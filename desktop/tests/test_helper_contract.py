# SPDX-License-Identifier: GPL-3.0-or-later
"""Semantic challenges for a candidate contract; synthetic IPC, no desktop."""

import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shell" / "host"))

from helper_contract import (
    ContractError, command_outcome, decode, helper_workspace, output_facts,
)


def sample():
    # Deliberately different physical-mode and logical-layout dimensions.
    outputs = [{"name": "DP-2", "active": True, "power": False,
                "rect": {"x": -1080, "y": 100, "width": 1080, "height": 1920},
                "current_mode": {"width": 3840, "height": 2160, "refresh": 59940},
                "scale": 2.0, "transform": "90", "current_workspace": "160:dev",
                "modes": [{"width": 3840, "height": 2160, "refresh": 59940}]}]
    workspaces = [{"name": "160:dev", "num": 160, "output": "DP-2",
                   "visible": True, "focused": True}]
    return outputs, workspaces


class FactsTests(unittest.TestCase):
    def test_scaled_rotated_pixels_do_not_become_logical_size(self):
        fact = output_facts(*sample())[0]
        self.assertEqual((fact.pixel_mode.width, fact.pixel_mode.height), (3840, 2160))
        self.assertEqual((fact.logical_rect.x, fact.logical_rect.y,
                          fact.logical_rect.width, fact.logical_rect.height),
                         (-1080, 100, 1080, 1920))
        self.assertEqual(fact.pixel_mode.refresh_hz, 59.94)
        self.assertEqual(fact.workspace_number, 160)
        self.assertTrue(fact.enabled)
        self.assertTrue(fact.focused)
        self.assertFalse(fact.powered)
        self.assertIsNone(fact.physical_width_mm)
        self.assertIsNone(fact.physical_height_mm)

    def test_named_workspace_remains_unknown_number(self):
        outputs, workspaces = sample()
        outputs[0]["current_workspace"] = workspaces[0]["name"] = "chat"
        workspaces[0]["num"] = -1
        fact = output_facts(outputs, workspaces)[0]
        self.assertEqual(fact.workspace_name, "chat")
        self.assertIsNone(fact.workspace_number)

    def test_observed_number_is_not_dispatch_limit(self):
        outputs, workspaces = sample()
        workspaces[0]["num"] = 200
        self.assertEqual(output_facts(outputs, workspaces)[0].workspace_number, 200)
        with self.assertRaises(ContractError):
            helper_workspace(200)

    def test_zero_refresh_is_unknown_not_sixty(self):
        outputs, workspaces = sample()
        outputs[0]["current_mode"]["refresh"] = 0
        self.assertIsNone(output_facts(outputs, workspaces)[0].pixel_mode.refresh_hz)

    def test_disabled_output_does_not_gain_geometry_or_scale(self):
        output = {"name": "HDMI-A-1", "active": False, "power": False,
                  "current_workspace": None,
                  "rect": {"x": 0, "y": 0, "width": 0, "height": 0}}
        fact = output_facts([output], [])[0]
        self.assertFalse(fact.enabled)
        self.assertIsNone(fact.pixel_mode)
        self.assertIsNone(fact.scale)
        self.assertIsNone(fact.transform)
        self.assertIsNone(fact.modes)

    def test_missing_modes_is_distinct_from_known_empty_modes(self):
        outputs, workspaces = sample()
        outputs[0]["modes"] = []
        self.assertEqual(output_facts(outputs, workspaces)[0].modes, ())
        del outputs[0]["modes"]
        self.assertIsNone(output_facts(outputs, workspaces)[0].modes)

    def test_untrusted_types_nonfinite_and_unknown_transform_fail(self):
        for key, value in [("active", 1), ("power", "false"), ("scale", True),
                           ("scale", float("nan")), ("scale", float("inf")),
                           ("scale", 10 ** 400),
                           ("transform", "sideways"), ("transform", [])]:
            with self.subTest(key=key, value=value):
                outputs, workspaces = sample()
                outputs[0][key] = value
                with self.assertRaises(ContractError):
                    output_facts(outputs, workspaces)

    def test_missing_power_is_not_inferred_from_enabled(self):
        outputs, workspaces = sample()
        del outputs[0]["power"]
        with self.assertRaises(ContractError):
            output_facts(outputs, workspaces)

    def test_join_changes_require_retry_not_wrong_dispatch(self):
        for field, value in [("output", "DP-1"), ("name", "other"), ("visible", False)]:
            with self.subTest(field=field):
                outputs, workspaces = sample()
                workspaces[0][field] = value
                with self.assertRaises(ContractError):
                    output_facts(outputs, workspaces)

    def test_duplicate_records_and_ambiguous_focus_fail(self):
        outputs, workspaces = sample()
        cases = [(outputs * 2, workspaces), (outputs, workspaces * 2),
                 (outputs, workspaces + [{**workspaces[0], "name": "other"}])]
        for args in cases:
            with self.subTest(args=args):
                with self.assertRaises(ContractError):
                    output_facts(*args)

    def test_missing_focused_output_and_contradictory_disabled_output_fail(self):
        outputs, workspaces = sample()
        with self.assertRaises(ContractError):
            output_facts([], workspaces)
        outputs[0]["active"] = False
        with self.assertRaises(ContractError):
            output_facts(outputs, workspaces)

    def test_bounds_and_injection_names_fail(self):
        for name in ["*", "DP-2; exit", "DP-2\n", "x" * 65]:
            outputs, workspaces = sample()
            outputs[0]["name"] = name
            with self.subTest(name=name), self.assertRaises(ContractError):
                output_facts(outputs, workspaces)
        with self.assertRaises(ContractError):
            output_facts([{}] * 65, [])


class ReplyTests(unittest.TestCase):
    def test_aborted_prefix_preserves_reported_and_unreported_commands(self):
        result = command_outcome('[{"success":true},{"success":false,"parse_error":true}]',
                                 expected_commands=3)
        self.assertFalse(result.ok)
        self.assertEqual(result.succeeded_indexes, (0,))
        self.assertEqual(result.failed_indexes, (1,))
        self.assertEqual(result.unreported_indexes, (2,))
        with self.assertRaises(ContractError):
            command_outcome('[{"success":true}]', expected_commands=2)

    def test_partial_success_does_not_make_batch_atomic(self):
        result = command_outcome(json.dumps([
            {"success": True}, {"success": False, "error": "unsupported"},
            {"success": True}]), expected_commands=3)
        self.assertFalse(result.ok)
        self.assertEqual(result.succeeded_indexes, (0, 2))
        self.assertEqual(result.failed_indexes, (1,))

    def test_success_requires_every_reply_and_correct_count(self):
        self.assertTrue(command_outcome('[{"success":true}]').ok)
        self.assertFalse(command_outcome('[{"success":true,"parse_error":true}]').ok)
        self.assertFalse(command_outcome('[{"success":true,"error":"failed"}]').ok)
        for payload in ["[]", '[{"success":true},{"success":true}]',
                        '[{"success":"true"}]', '[{}]', '{}']:
            with self.subTest(payload=payload), self.assertRaises(ContractError):
                command_outcome(payload)

    def test_duplicate_keys_nonfinite_and_oversized_json_fail(self):
        for payload in ['{"success":false,"success":true}', '[NaN]',
                        '[Infinity]', '"' + 'a' * 262145 + '"', '"\ud800"']:
            with self.subTest(length=len(payload)), self.assertRaises(ContractError):
                decode(payload)

    def test_helper_id_range_is_distinct_from_shell_ui(self):
        for value in [1, 10, 11, 160]:
            self.assertEqual(helper_workspace(value), value)
        for value in [0, 161, -1, True, "160", 160.0]:
            with self.subTest(value=value), self.assertRaises(ContractError):
                helper_workspace(value)


if __name__ == "__main__":
    unittest.main()
