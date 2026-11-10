"""Workspace event sequences with no live compositor, process or state access."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


HELPER = Path(__file__).resolve().parents[1] / "plugins/fred.workspaces/tam-desktop-mode"
PREFIX = "tam-desktop-mode event "


class WorkspaceTimelineTests(unittest.TestCase):
    def setUp(self):
        loader = SourceFileLoader("workspace_timeline_test", str(HELPER))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        self.engine = importlib.util.module_from_spec(spec)
        loader.exec_module(self.engine)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.dict(os.environ, {
            "HOME": str(directory), "XDG_STATE_HOME": str(directory / "state"),
            "XDG_CONFIG_HOME": str(directory / "config"),
            "XDG_RUNTIME_DIR": str(directory / "runtime"),
        }, clear=True))
        # Every backend call is intercepted, and an accidental direct process
        # launch fails the test. Never rely on inherited live-action variables.
        self.stack.enter_context(patch.object(self.engine, "run_named", side_effect=self.backend))
        self.stack.enter_context(patch.object(subprocess, "run", side_effect=AssertionError("real process")))
        self.stack.enter_context(patch.object(subprocess, "Popen", side_effect=AssertionError("real process")))
        self.stack.enter_context(patch.object(self.engine, "load_canonical_topology", return_value=[
            {"output": "SIDE", "position": "0x0"},
            {"output": "ACTIVE", "position": "1920x0"},
            {"output": "HP", "position": "3840x0"},
        ]))
        self.stack.enter_context(patch.object(self.engine, "load_full_config", return_value=("", "", 0, "")))
        self.stack.enter_context(patch.object(self.engine, "ensure_contiguous_layout"))
        self.engine.atomic_write_state("desktop-mode", "windows\n")
        self.engine.atomic_write_state("desktop-current", "1\n")
        self.active = {"SIDE": 1, "ACTIVE": 2, "HP": 3}
        self.focus = "ACTIVE"
        self.off = False
        self.calls = []
        self.during_batch = None
        self.reject = False
        self.log = self.stack.enter_context(redirect_stderr(io.StringIO()))

    def backend(self, operation, payload=None):
        self.calls.append((operation, payload))
        value = "ok\n"
        if operation == "monitors":
            value = json.dumps([{"name": name, "x": index * 1920, "y": 0,
                                 "activeWorkspace": {"id": ws}, "focused": name == self.focus,
                                 "dpmsStatus": not self.off}
                                for index, (name, ws) in enumerate(self.active.items())])
        elif operation == "workspaces":
            value = json.dumps([{"id": ws, "monitor": name} for name, ws in self.active.items()])
        elif operation == "batch":
            if self.during_batch:
                self.during_batch()
            if self.reject:
                return subprocess.CompletedProcess([], 1, "", "disconnected")
            for step, argument in payload:
                if step == "focus-output":
                    if argument not in self.active:
                        return subprocess.CompletedProcess([], 1, "", "disconnected")
                    self.focus = argument
                elif step == "focus-workspace":
                    self.active[self.focus] = argument
        elif operation == "focus-output":
            self.focus = payload
        elif operation not in ("dpms", "dpms-fallback"):
            raise AssertionError((operation, payload))
        return subprocess.CompletedProcess([], 0, value, "")

    def events(self):
        return [json.loads(line[len(PREFIX):]) for line in self.log.getvalue().splitlines()
                if line.startswith(PREFIX)]

    def switch(self, number):
        self.engine.switch_desktop(str(number), list(self.active), "SIDE", "HP",
                                   {"SIDE": 0, "ACTIVE": 1, "HP": 2}, 3)

    def test_switch_records_origin_assignment_and_observed_completion(self):
        self.switch(2)
        events = self.events()
        self.assertEqual([e["event"] for e in events],
                         ["start", "intent-accepted", "placement-start", "placement-observed", "end"])
        self.assertEqual(len({e["sequence"] for e in events}), 1)
        self.assertEqual(events[-1]["origin"], "ACTIVE")
        self.assertEqual(events[-1]["result"], "complete")
        self.assertEqual(events[3]["outputs"]["HP"],
                         {"expected": 6, "observed": 6, "result": "aligned"})
        self.assertEqual(self.focus, "ACTIVE")

    def test_hp_disappearing_during_batch_is_incomplete_and_repair_failure_is_visible(self):
        self.during_batch = lambda: self.active.pop("HP", None)
        self.switch(2)
        self.assertEqual(self.events()[-1]["result"], "partial")
        self.assertEqual(self.events()[3]["result"], "batch-failed")
        self.during_batch = None
        self.active["HP"] = 99
        self.reject = True
        self.assertEqual(self.engine.reconcile("output-change"), "incomplete: workspace placement")
        self.assertEqual(self.events()[-1]["result"], "partial")
        self.assertEqual(self.events()[-1]["reason"], "output-change")

    def test_hp_return_already_aligned_causes_no_workspace_batch(self):
        self.active.pop("HP")
        self.switch(2)
        self.active["HP"] = 6
        self.calls.clear()
        self.assertEqual(self.engine.reconcile("output-change"), "reconciled: aligned")
        self.assertFalse(any(op == "batch" for op, _ in self.calls))
        self.assertEqual(self.active["ACTIVE"], 5)
        self.assertEqual(self.events()[-1]["result"], "aligned")

    def test_dark_reconcile_defers_without_batch_or_power_request(self):
        self.off = True
        self.assertEqual(self.engine.reconcile(), "deferred: dpms off")
        self.assertFalse(any(op in ("batch", "dpms", "dpms-fallback") for op, _ in self.calls))
        self.assertEqual(self.events()[-1]["result"], "deferred")

    def test_failure_after_start_has_paired_failure_record(self):
        with patch.object(self.engine, "switch_windows", side_effect=RuntimeError("private detail")):
            with self.assertRaises(RuntimeError):
                self.switch(2)
        self.assertEqual([e["event"] for e in self.events()], ["start", "intent-accepted", "end"])
        self.assertEqual(self.events()[-1]["result"], "failure")
        self.assertNotIn("private detail", self.log.getvalue())
        self.assertIsNone(self.engine._TIMELINE)

    def test_clock_correlation_survives_wall_clock_reversal_and_has_subseconds(self):
        with patch.object(self.engine.time, "time_ns", side_effect=[2_000_000_123, 1_000_000_456]), \
             patch.object(self.engine.time, "clock_gettime_ns", side_effect=[10_123_456, 10_234_567]):
            with self.engine.timeline_action("test") as result:
                result["result"] = "complete"
        start, end = self.events()
        self.assertGreater(start["wall_ns"], end["wall_ns"])
        self.assertLess(start["monotonic_ns"], end["monotonic_ns"])
        self.assertEqual(end["monotonic_ns"], 10_234_567)

    def test_unavailable_log_sink_does_not_prevent_switch(self):
        with patch.object(self.engine.sys.stderr, "write", side_effect=BrokenPipeError):
            self.switch(2)
        self.assertEqual(self.active, {"SIDE": 4, "ACTIVE": 5, "HP": 6})
        self.assertIsNone(self.engine._TIMELINE)

    def test_passive_status_is_quiet_and_does_not_query_compositor(self):
        with patch.object(self.engine.sys, "argv", ["tam-desktop-mode", "status"]), \
             redirect_stdout(io.StringIO()) as output:
            self.engine.main()
        self.assertEqual(output.getvalue(), "windows\n")
        self.assertEqual(self.calls, [])
        self.assertEqual(self.log.getvalue(), "")

    def test_busy_request_retains_pending_intent_without_dispatch(self):
        with patch.object(self.engine, "acquire_command_lock", return_value=None), \
             patch.object(self.engine.sys, "argv", ["tam-desktop-mode", "switch", "2"]):
            with self.assertRaises(SystemExit) as error:
                self.engine.main()
        self.assertEqual(error.exception.code, 75)
        self.assertEqual(self.events()[-1]["result"], "pending")
        self.assertEqual(self.engine.read_desktop_intent()["desktop"], 2)
        self.assertEqual(self.calls, [("monitors", None)])

    def test_records_fit_one_line_even_with_maximum_topology(self):
        self.active = {f"OUTPUT-{i:02}-" + "x" * 54: i + 1 for i in range(16)}
        self.focus = next(iter(self.active))
        slots = {name: i for i, name in enumerate(self.active)}
        self.engine.switch_desktop("2", list(self.active), self.focus, self.focus, slots, 16)
        for line in self.log.getvalue().splitlines():
            self.assertLessEqual(len(line.encode()) + 1, 4096)
            self.assertTrue(line.startswith(PREFIX))
            json.loads(line[len(PREFIX):])

    def test_cli_reconcile_failure_returns_nonzero_and_keeps_stdout_small(self):
        self.reject = True
        self.active["HP"] = 99
        with patch.object(self.engine, "acquire_command_lock", return_value=123), \
             patch.object(self.engine.sys, "argv", ["tam-desktop-mode", "reconcile", "output-change"]), \
             redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as error:
                self.engine.main()
        self.assertEqual(error.exception.code, 1)
        self.assertEqual(output.getvalue(), "incomplete: workspace placement\n")

    def test_invalid_power_output_is_rejected_without_logging_untrusted_text(self):
        with patch.object(self.engine.sys, "argv", ["tam-desktop-mode", "dpms-on", "bad\noutput"]):
            with self.assertRaises(SystemExit) as error:
                self.engine.main()
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.events(), [])
        self.assertFalse(any(op == "dpms" for op, _ in self.calls))

    def test_power_failure_records_output_and_action_not_raw_backend_error(self):
        with patch.object(self.engine, "dpms_on", return_value=False), \
             patch.object(self.engine.sys, "argv", ["tam-desktop-mode", "dpms-on", "HP"]):
            with self.assertRaises(SystemExit) as error:
                self.engine.main()
        self.assertEqual(error.exception.code, 1)
        event = self.events()[-1]
        self.assertEqual((event["output"], event["requested"], event["result"]), ("HP", "on", "failure"))


if __name__ == "__main__":
    unittest.main()
