"""Budgets survive independent helpers and cannot let one output block another."""
import unittest
from unittest.mock import patch
import test_workspace_timeline as fixture


class WorkspaceRetryTests(unittest.TestCase):
    setUp = fixture.WorkspaceTimelineTests.setUp
    backend = fixture.WorkspaceTimelineTests.backend
    events = fixture.WorkspaceTimelineTests.events
    switch = fixture.WorkspaceTimelineTests.switch

    def test_absent_hp_does_not_count_as_complete_and_late_return_repairs_only_hp(self):
        self.active.pop("HP")
        self.switch(2)
        first = self.engine.read_desktop_intent()
        self.assertFalse(first["complete"])
        self.assertEqual(first["outputs"]["HP"]["result"], "missing")
        self.assertEqual(first["outputs"]["HP"]["attempts"], 0)
        self.assertEqual(self.engine.read_state_file("desktop-current"), "1")
        self.active["HP"] = 3
        self.calls.clear()
        self.assertEqual(self.engine.reconcile("output-change"), "reconciled")
        self.assertEqual([p for op, p in self.calls if op == "batch"],
                         [[("select-output-workspace", (6, "HP"))]])
        self.assertTrue(self.engine.read_desktop_intent()["complete"])

    def test_rejection_has_three_attempts_across_helpers_and_duplicate_events_do_not_reset_it(self):
        self.reject = True
        self.switch(2)
        for _ in range(8):
            self.engine.reconcile("output-change")
        intent = self.engine.read_desktop_intent()
        self.assertFalse(intent["complete"])
        self.assertTrue(all(item["attempts"] == 3 and item["result"] == "expired"
                            for item in intent["outputs"].values()))
        self.assertEqual(sum(op == "batch" for op, _ in self.calls), 9)
        self.reject = False
        self.calls.clear()
        self.assertEqual(self.engine.reconcile(), "incomplete: workspace placement")
        self.assertFalse(any(op == "batch" for op, _ in self.calls))
        # An explicit retry opens a new generation and budget.
        self.engine.publish_desktop_intent(2, "ACTIVE")
        self.assertEqual(self.engine.reconcile(), "reconciled")
        self.assertTrue(self.engine.read_desktop_intent()["complete"])

    def test_elapsed_deadline_prevents_another_dispatch_even_with_attempts_left(self):
        self.reject = True
        with patch.object(self.engine.time, "monotonic_ns", return_value=100):
            self.switch(2)
        self.calls.clear()
        with patch.object(self.engine.time, "monotonic_ns", return_value=4_000_000_100):
            self.engine.reconcile()
        self.assertFalse(any(op == "batch" for op, _ in self.calls))
        self.assertTrue(all(item["result"] == "expired" for item in
                            self.engine.read_desktop_intent()["outputs"].values()))

    def test_one_rejected_side_does_not_prevent_other_side_or_active_progress(self):
        backend = self.backend
        def fail_hp(op, payload=None):
            if op == "batch" and payload[0][1][1] == "HP":
                self.reject = True
                result = backend(op, payload)
                self.reject = False
                return result
            return backend(op, payload)
        with patch.object(self.engine, "run_named", side_effect=fail_hp):
            self.switch(2)
        self.assertEqual(self.active, {"SIDE": 4, "ACTIVE": 5, "HP": 3})
        intent = self.engine.read_desktop_intent()
        self.assertEqual(intent["outputs"]["ACTIVE"]["result"], "aligned")
        self.assertEqual(intent["outputs"]["HP"]["attempts"], 1)
        self.assertFalse(intent["complete"])

    def test_publication_does_not_wait_for_the_worker_lock(self):
        with patch.object(self.engine, "acquire_command_lock", side_effect=AssertionError("worker lock")), \
             patch.object(self.engine.sys, "argv", ["helper", "accept-switch", "3", "ACTIVE"]):
            self.engine.main()
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 3)
        self.assertEqual(self.calls, [])

    def test_late_apply_consumes_newest_request_without_republishing(self):
        first = self.engine.publish_desktop_intent(2, "ACTIVE")
        latest = self.engine.publish_desktop_intent(3, "ACTIVE")
        with patch.object(self.engine, "acquire_command_lock", return_value=123), \
             patch.object(self.engine.sys, "argv", ["helper", "apply-intent"]):
            self.engine.main()
        result = self.engine.read_desktop_intent()
        self.assertEqual(result["generation"], latest["generation"])
        self.assertEqual(self.active["ACTIVE"], 8)
        self.assertFalse(self.engine.finish_desktop_intent(first, True))

    def test_realign_uses_existing_budget_and_cannot_dispatch_after_expiry(self):
        self.reject = True
        self.switch(2)
        for _ in range(5):
            self.engine.realign_monitor("HP", 2, list(self.active),
                                        {"SIDE": 0, "ACTIVE": 1, "HP": 2}, 3)
        intent = self.engine.read_desktop_intent()
        self.assertEqual(intent["outputs"]["HP"]["attempts"], 3)
        self.assertEqual(sum(op == "batch" and payload[0][1][1] == "HP"
                             for op, payload in self.calls), 3)

    def test_no_outputs_never_falls_back_to_focus_dispatch(self):
        self.active.clear()
        self.switch(2)
        self.assertFalse(self.engine.read_desktop_intent()["complete"])
        self.assertFalse(any(op.startswith("focus-") for op, _ in self.calls))

    def test_total_ipc_budget_caps_backend_calls_and_refuses_dispatch_after_expiry(self):
        from unittest.mock import Mock
        backend = Mock()
        with patch.object(self.engine, "load_backend", return_value=backend), \
             patch.object(self.engine.time, "monotonic", side_effect=[10.0, 11.0, 13.1]):
            with self.engine.compositor_budget():
                self.real_run_named("batch", [])
                expired = self.real_run_named("batch", [])
        backend.run.assert_called_once_with("batch", [], timeout=2.0)
        self.assertEqual(expired.returncode, 124)
        self.assertIsNone(self.engine._IPC_DEADLINE)
