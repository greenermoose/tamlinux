# SPDX-License-Identifier: GPL-3.0-or-later
"""Challenge offline Hyprland facts and replies; never touch a compositor."""

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shell" / "host"))
import helper_contract as contract
import hyprland_helper_backend as hypr


def monitor():
    return {"name": "DP-2", "disabled": False, "dpmsStatus": False, "focused": True,
            "x": -1080, "y": 100, "width": 3840, "height": 2160,
            "scale": 2, "transform": 1, "refreshRate": 59.94,
            "activeWorkspace": {"id": 160, "name": "160:dev"}, "mirrorOf": "none",
            "availableModes": ["3840x2160@59.94Hz"]}


def facts(row):
    return hypr.monitor_facts(json.dumps([row]))[0]


class FactTests(unittest.TestCase):
    def test_rotated_scaled_pixels_and_layout_have_distinct_units(self):
        fact = facts(monitor())
        self.assertEqual(fact.pixel_mode, contract.Mode(3840, 2160, 59940))
        self.assertEqual(fact.logical_rect, contract.Rect(-1080, 100, 1080, 1920))
        self.assertEqual(fact.transform, "90")
        self.assertTrue(fact.enabled)
        self.assertFalse(fact.powered)
        self.assertTrue(fact.focused)
        self.assertEqual(fact.workspace_number, 160)

    def test_all_transform_axes_and_names(self):
        for value, name in enumerate(hypr.TRANSFORMS):
            with self.subTest(transform=value):
                fact = facts({**monitor(), "transform": value})
                self.assertEqual(fact.transform, name)
                expected = (1080, 1920) if value % 2 else (1920, 1080)
                self.assertEqual((fact.logical_rect.width, fact.logical_rect.height), expected)

    def test_cpp_half_rounding_and_refresh_precision(self):
        fact = facts({**monitor(), "width": 2565, "height": 1445, "scale": 2,
                      "transform": 0, "refreshRate": 59.9405})
        self.assertEqual((fact.logical_rect.width, fact.logical_rect.height), (1283, 723))
        self.assertEqual(fact.pixel_mode.refresh_millihz, 59941)

    def test_named_and_out_of_dispatch_range_workspace_are_observations(self):
        row = monitor()
        row["activeWorkspace"] = {"id": -1337, "name": "chat"}
        self.assertIsNone(facts(row).workspace_number)
        self.assertEqual(facts(row).workspace_name, "chat")
        row["activeWorkspace"] = {"id": 200, "name": "200"}
        self.assertEqual(facts(row).workspace_number, 200)
        with self.assertRaises(ValueError):
            hypr.request_plan("focus-workspace", 200)

    def test_disabled_output_does_not_reuse_stale_live_facts(self):
        row = {**monitor(), "disabled": True, "dpmsStatus": True}
        self.assertEqual(hypr.monitor_facts(json.dumps([row])), ())
        fact = hypr.monitor_facts(json.dumps([row]), include_disabled=True)[0]
        self.assertFalse(fact.enabled)
        self.assertFalse(fact.powered)
        self.assertFalse(fact.focused)
        self.assertIsNone(fact.pixel_mode)
        self.assertIsNone(fact.workspace_number)
        self.assertIsNone(fact.scale)
        self.assertEqual(fact.logical_rect, contract.Rect(-1080, 100, 0, 0))

    def test_missing_empty_and_reported_modes_are_distinct(self):
        row = monitor()
        self.assertEqual(facts(row).modes, (contract.Mode(3840, 2160, 59940),))
        row["availableModes"] = []
        self.assertEqual(facts(row).modes, ())
        del row["availableModes"]
        self.assertIsNone(facts(row).modes)
        row["refreshRate"] = 0
        self.assertIsNone(facts(row).pixel_mode.refresh_hz)

    def test_unrepresentable_mirror_is_explicitly_unsupported(self):
        with self.assertRaises(hypr.UnsupportedOperation):
            facts({**monitor(), "mirrorOf": "0"})

    def test_missing_and_untrusted_fact_fields_fail(self):
        for key in ["disabled", "dpmsStatus", "focused", "x", "y", "width", "height",
                    "scale", "transform", "refreshRate", "activeWorkspace"]:
            row = monitor()
            del row[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                facts(row)
        for key, value in [("disabled", 1), ("dpmsStatus", "false"), ("focused", 0),
                           ("width", True), ("height", 0), ("scale", True), ("scale", 0),
                           ("scale", float("nan")), ("refreshRate", float("inf")),
                           ("scale", 10 ** 400), ("transform", 8), ("transform", "1"),
                           ("name", "DP-2; exit"), ("x", -1000001)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                facts({**monitor(), key: value})

    def test_duplicate_focus_output_and_workspace_fail(self):
        first = monitor()
        second = copy.deepcopy(first)
        second["name"] = "DP-1"
        second["activeWorkspace"] = {"id": 2, "name": "2"}
        for rows in [[first, first], [first, second],
                     [first, {**second, "focused": False, "activeWorkspace": first["activeWorkspace"]}]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                hypr.monitor_facts(json.dumps(rows))

    def test_malformed_advertised_modes_fail(self):
        for value in ["3840x2160@59.94Hz", [None], ["1920x1080@nanHz"],
                      ["32769x1080@60Hz"], ["1920x1080@1001Hz"], ["1920x1080@60Hz"] * 257]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                facts({**monitor(), "availableModes": value})

    def test_json_bounds_duplicate_keys_and_flags_fail(self):
        for payload in ['[{"name":"DP-2","name":"DP-1"}]', "[NaN]", "[]" * 131073]:
            with self.subTest(length=len(payload)), self.assertRaises(ValueError):
                hypr.monitor_facts(payload)
        with self.assertRaises(ValueError):
            hypr.monitor_facts(json.dumps([monitor()] * 65))
        with self.assertRaises(ValueError):
            hypr.monitor_facts("[]", include_disabled=1)

    def test_active_workspace_retains_named_unknown_number(self):
        focus = hypr.active_workspace('{"id":-1337,"name":"chat","monitor":"DP-2"}')
        self.assertEqual((focus.name, focus.number, focus.output), ("chat", None, "DP-2"))
        for value in [{}, {"id": True, "name": "chat", "monitor": "DP-2"},
                      {"id": 0, "name": "", "monitor": "DP-2"}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                hypr.active_workspace(json.dumps(value))


class ReplyTests(unittest.TestCase):
    def test_single_reply_requires_exact_ok(self):
        plan = hypr.request_plan("focus-workspace", 160)
        self.assertTrue(plan.outcome("ok\n").ok)
        for reply in ["recorded\n", "not ok", "ok but error", "ok\nerror"]:
            with self.subTest(reply=reply):
                self.assertFalse(plan.outcome(reply).ok)

    def test_batch_uses_wire_delimiter_and_retains_each_failure(self):
        plan = hypr.request_plan("batch", [("focus-workspace", 160),
                    ("focus-output", "DP-2"), ("move-workspace", "DP-1")])
        outcome = plan.outcome("ok\n\n\nmissing monitor\nmore detail\n\n\nok\n")
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.succeeded_indexes, (0, 2))
        self.assertEqual(outcome.failed_indexes, (1,))
        self.assertEqual(outcome.unreported_indexes, ())
        self.assertTrue(plan.outcome("ok\n\n\nok\n\n\nok").ok)
        for reply in ["ok", "ok\nok\nok", "ok\n\n\nok\n\n\n"]:
            with self.subTest(reply=reply), self.assertRaises(ValueError):
                plan.outcome(reply)

    def test_reply_size_encoding_type_and_read_outcome_fail(self):
        plan = hypr.request_plan("reload")
        for value in [None, "x" * 262145, "\ud800", "ok\0"]:
            with self.subTest(value_type=type(value)), self.assertRaises(ValueError):
                plan.outcome(value)
        with self.assertRaises(ValueError):
            hypr.request_plan("monitors").outcome("ok")


if __name__ == "__main__":
    unittest.main()
