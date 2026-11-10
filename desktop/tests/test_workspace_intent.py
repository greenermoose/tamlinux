"""Latest intent survives IPC failure, contention and reordered helper events."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import unittest
from unittest.mock import patch

import test_workspace_timeline as fixture


class WorkspaceIntentTests(unittest.TestCase):
    setUp = fixture.WorkspaceTimelineTests.setUp
    backend = fixture.WorkspaceTimelineTests.backend
    events = fixture.WorkspaceTimelineTests.events
    switch = fixture.WorkspaceTimelineTests.switch

    def cli(self, *arguments):
        with patch.object(self.engine, "acquire_command_lock", return_value=123), \
             patch.object(self.engine.sys, "argv", ["tam-desktop-mode", *arguments]):
            self.engine.main()

    def test_failed_switch_keeps_desired_separate_from_observed_then_reconnect_repairs_it(self):
        self.reject = True
        self.switch(2)
        self.assertEqual(self.engine.read_state_file("desktop-current"), "1")
        intent = self.engine.read_desktop_intent()
        self.assertEqual((intent["desktop"], intent["complete"]), (2, False))
        self.reject = False
        self.assertEqual(self.engine.reconcile("output-change"), "reconciled")
        self.assertEqual(self.active, {"SIDE": 4, "ACTIVE": 5, "HP": 6})
        self.assertTrue(self.engine.read_desktop_intent()["complete"])
        self.assertEqual(self.engine.read_state_file("desktop-current"), "2")

    def test_newer_request_during_batch_wins_and_old_success_cannot_write_observed_state(self):
        during = []
        def publish_newer():
            self.during_batch = None
            during.append(self.engine.publish_desktop_intent(3, "ACTIVE"))
            self.assertEqual(self.engine.read_state_file("desktop-current"), "1")
        self.during_batch = publish_newer
        self.switch(2)
        self.assertEqual(self.active, {"SIDE": 7, "ACTIVE": 8, "HP": 9})
        self.assertEqual(self.engine.read_desktop_intent()["generation"], during[0]["generation"])
        self.assertEqual(self.engine.read_state_file("desktop-current"), "3")
        self.assertTrue(any(e["event"] == "superseded" for e in self.events()))

    def test_repeated_new_requests_are_bounded_and_latest_remains_pending(self):
        number = [2]
        def another():
            number[0] += 1
            self.engine.publish_desktop_intent(number[0], "ACTIVE")
        self.during_batch = another
        self.switch(2)
        self.assertEqual(sum(op == "batch" for op, _ in self.calls), self.engine.INTENT_ATTEMPTS)
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], number[0])
        self.assertFalse(self.engine.read_desktop_intent()["complete"])
        self.assertEqual(self.events()[-1]["result"], "partial")

    def test_old_repair_is_not_retried_after_new_intent_arrives(self):
        self.engine.publish_desktop_intent(2, "ACTIVE")
        def replace_and_fail():
            self.during_batch = None
            self.engine.publish_desktop_intent(3, "ACTIVE")
            self.reject = True
        self.during_batch = replace_and_fail
        self.engine.reconcile("output-change")
        self.assertEqual(sum(op == "batch" for op, _ in self.calls), 1)
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 3)
        self.assertFalse(self.engine.read_desktop_intent()["complete"])
        self.assertEqual(self.engine.read_state_file("desktop-current"), "1")

    def test_reordered_follow_event_cannot_replace_completed_explicit_request(self):
        self.switch(2)
        self.calls.clear()
        self.cli("switch", "1", "follow-timer")
        self.assertFalse(any(op == "batch" for op, _ in self.calls))
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 2)
        self.assertEqual(self.events()[-1]["result"], "stale-observation")

    def test_follow_waiting_for_lock_cannot_replace_a_newer_explicit_request(self):
        self.switch(2)
        self.calls.clear()
        def intervening():
            self.engine.publish_desktop_intent(3, "ACTIVE")
            return 123
        with patch.object(self.engine, "acquire_command_lock", side_effect=intervening), \
             patch.object(self.engine.sys, "argv", ["tam-desktop-mode", "switch", "2", "follow-timer"]):
            self.engine.main()
        self.assertFalse(any(op == "batch" for op, _ in self.calls))
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 3)

    def test_pending_intent_beats_transient_focus_in_follow_timer(self):
        self.engine.publish_desktop_intent(3, "ACTIVE")
        self.cli("switch", "1", "follow-timer")
        self.assertEqual(self.active["ACTIVE"], 8)
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 3)

    def test_deliberate_window_focus_can_follow_after_request_completes(self):
        self.switch(2)
        self.active["ACTIVE"] = 8
        self.cli("switch", "3", "follow-timer")
        self.assertEqual(self.active, {"SIDE": 7, "ACTIVE": 8, "HP": 9})
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 3)

    def test_follow_publish_compare_and_set_preserves_intervening_explicit_request(self):
        first = self.engine.publish_desktop_intent(2, "ACTIVE")
        latest = self.engine.publish_desktop_intent(3, "ACTIVE")
        result = self.engine.publish_desktop_intent(1, "ACTIVE", first["generation"])
        self.assertEqual(result, latest)
        self.assertEqual(self.engine.read_desktop_intent(), latest)

    def test_stale_completion_cannot_mark_latest_complete(self):
        first = self.engine.publish_desktop_intent(2, "ACTIVE")
        latest = self.engine.publish_desktop_intent(3, "ACTIVE")
        self.assertFalse(self.engine.finish_desktop_intent(first, True))
        self.assertEqual(self.engine.read_desktop_intent(), latest)
        self.assertEqual(self.engine.read_state_file("desktop-current"), "1")

    def test_concurrent_publishers_use_distinct_increasing_generations(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            intents = list(pool.map(lambda n: self.engine.publish_desktop_intent(n, "ACTIVE"), range(1, 9)))
        self.assertEqual(sorted(i["generation"] for i in intents), list(range(1, 9)))
        self.assertEqual(self.engine.read_desktop_intent(), max(intents, key=lambda i: i["generation"]))

    def test_duplicate_completion_is_a_state_noop(self):
        self.switch(2)
        intent = self.engine.read_desktop_intent()
        with patch.object(self.engine, "atomic_write_state") as write:
            self.assertTrue(self.engine.finish_desktop_intent(intent, True))
        write.assert_not_called()

    def test_stale_realign_number_cannot_restore_old_desktop(self):
        self.switch(2)
        self.active["HP"] = 3
        self.assertTrue(self.engine.realign_monitor("HP", 1, list(self.active),
                                                  {"SIDE": 0, "ACTIVE": 1, "HP": 2}, 3))
        self.assertEqual(self.active["HP"], 6)

    def test_busy_cli_retains_intent_under_a_real_command_lock(self):
        lock = self.engine.acquire_command_lock(timeout=0.01)
        self.addCleanup(os.close, lock)
        acquire = self.engine.acquire_command_lock
        with patch.object(self.engine, "acquire_command_lock", side_effect=lambda: acquire(timeout=0.01)), \
             patch.object(self.engine.sys, "argv", ["tam-desktop-mode", "switch", "3"]):
            with self.assertRaises(SystemExit) as error:
                self.engine.main()
        self.assertEqual(error.exception.code, self.engine.BUSY_EXIT)
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 3)
        self.assertFalse(any(op == "batch" for op, _ in self.calls))

    def test_invalid_cli_number_cannot_overwrite_pending_request(self):
        latest = self.engine.publish_desktop_intent(2, "ACTIVE")
        with self.assertRaises(SystemExit) as error:
            self.cli("switch", "11")
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.engine.read_desktop_intent(), latest)

    def test_nonwindows_switch_does_not_publish_set_intent(self):
        self.engine.atomic_write_state("desktop-mode", "mac\n")
        with patch.object(self.engine, "switch_mac", return_value=True):
            self.cli("switch", "2")
        self.assertIsNone(self.engine.read_desktop_intent())

    def test_mode_change_invalidates_old_pending_request(self):
        self.engine.publish_desktop_intent(2, "ACTIVE")
        with patch.object(self.engine, "notify_mode"):
            self.engine.set_mode("mac", list(self.active))
        self.assertIsNone(self.engine.read_desktop_intent())

    def test_invalid_or_symlinked_intent_is_not_accepted_as_trusted_state(self):
        for value in ({}, {"version": 1, "generation": True}, [], "x"):
            self.engine.atomic_write_state("desktop-intent", json.dumps(value))
            self.assertIsNone(self.engine.read_desktop_intent())
        intent = self.engine.publish_desktop_intent(2, "ACTIVE")
        state = Path(os.environ["XDG_STATE_HOME"]) / "tamlinux"
        target = state / "other-file"
        target.write_text(json.dumps(intent))
        (state / "desktop-intent").unlink()
        (state / "desktop-intent").symlink_to(target)
        self.assertIsNone(self.engine.read_desktop_intent())
        self.engine.publish_desktop_intent(3, "ACTIVE")
        self.assertEqual(json.loads(target.read_text()), intent)

    def test_failed_cli_switch_reports_nonzero_with_retained_intent(self):
        self.reject = True
        with self.assertRaises(SystemExit) as error:
            self.cli("switch", "2")
        self.assertEqual(error.exception.code, 1)
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 2)
        self.assertFalse(self.engine.read_desktop_intent()["complete"])


if __name__ == "__main__":
    unittest.main()
