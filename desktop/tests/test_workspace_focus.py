"""Output repair must never pass input focus through a side monitor."""
import unittest
from unittest.mock import patch
import test_workspace_timeline as fixture


class WorkspaceFocusTests(unittest.TestCase):
    setUp = fixture.WorkspaceTimelineTests.setUp
    backend = fixture.WorkspaceTimelineTests.backend
    events = fixture.WorkspaceTimelineTests.events
    switch = fixture.WorkspaceTimelineTests.switch

    def test_active_output_is_first_without_focus_cycle(self):
        self.switch(2)
        batch = [step for op, payload in self.calls if op == "batch" for step in payload]
        self.assertEqual(batch, [("select-output-workspace", (5, "ACTIVE")),
                                 ("select-output-workspace", (4, "SIDE")),
                                 ("select-output-workspace", (6, "HP"))])
        self.assertEqual(self.focus, "ACTIVE")

    def test_returning_hp_repairs_only_hp_and_leaves_geometry_alone(self):
        self.switch(2)
        self.active["HP"] = 99
        self.calls.clear()
        self.assertEqual(self.engine.reconcile("output-change"), "reconciled")
        batches = [payload for op, payload in self.calls if op == "batch"]
        self.assertEqual(batches, [[("select-output-workspace", (6, "HP"))]])
        self.engine.ensure_contiguous_layout.assert_not_called()
        self.assertEqual(self.focus, "ACTIVE")

    def test_aligned_request_has_no_mutation(self):
        self.switch(2)
        self.calls.clear()
        self.switch(2)
        self.assertFalse(any(op == "batch" for op, _ in self.calls))

    def test_native_action_failure_never_falls_back_to_focus_cycle(self):
        self.reject = True
        self.switch(2)
        self.assertEqual(self.focus, "ACTIVE")
        self.assertFalse(any(op.startswith("focus-") for op, _ in self.calls))
        self.assertFalse(self.engine.read_desktop_intent()["complete"])

    def test_realign_targets_only_named_output(self):
        self.engine.publish_desktop_intent(2, "ACTIVE")
        self.assertTrue(self.engine.realign_monitor("HP", 1, list(self.active),
                                                   {"SIDE": 0, "ACTIVE": 1, "HP": 2}, 3))
        self.assertEqual(self.active, {"SIDE": 1, "ACTIVE": 2, "HP": 6})
        self.assertEqual(self.focus, "ACTIVE")
        self.assertFalse(any(op.startswith("focus-") for op, _ in self.calls))

    def test_user_geometry_is_not_rewritten_on_known_panel_return(self):
        self.engine.reconcile("output-change")
        self.engine.ensure_contiguous_layout.assert_not_called()

    def test_new_connector_uses_existing_topology_repair(self):
        self.active["NEW"] = 99
        self.engine.reconcile("output-change")
        self.engine.ensure_contiguous_layout.assert_called_once()

    def test_side_failure_leaves_active_desktop_applied(self):
        self.during_batch = lambda: self.active.pop("HP", None)
        self.switch(2)
        self.assertEqual(self.active["ACTIVE"], 5)
        self.assertEqual(self.focus, "ACTIVE")
        self.assertFalse(self.engine.read_desktop_intent()["complete"])

    def test_origin_loss_adopts_surviving_focus_on_next_event(self):
        def remove_origin():
            self.active.pop("ACTIVE", None)
            self.focus = "SIDE"  # compositor chooses a surviving output
        self.during_batch = remove_origin
        self.switch(2)
        self.during_batch = None
        self.calls.clear()
        self.assertEqual(self.engine.reconcile("output-change"), "incomplete: workspace placement")
        self.assertEqual(self.active, {"SIDE": 4, "HP": 6})
        self.assertEqual(self.focus, "SIDE")
        self.assertFalse(any(op == "batch" for op, _ in self.calls))
        self.assertFalse(self.engine.read_desktop_intent()["complete"])
