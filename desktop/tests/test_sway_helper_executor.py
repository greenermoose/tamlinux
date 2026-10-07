# SPDX-License-Identifier: GPL-3.0-or-later
"""Executor failure paths and real bounded child IO; no compositor is used."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HOST = Path(__file__).resolve().parents[1] / "shell" / "host"
sys.path.insert(0, str(HOST))
import sway_helper_executor as executor
from test_helper_contract import sample


def reply(stdout, code=0, stderr=""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = self.directory.name + "/ipc.sock"
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.bind(self.path)
        self.addCleanup(self.socket.close)

    def run_operation(self, operation, payload=None, **kwargs):
        return executor.execute(operation, payload, socket_path=self.path, **kwargs)

    def test_recording_never_contacts_compositor_and_is_not_success(self):
        with patch.object(executor, "_capture") as capture, patch.dict(os.environ, {
                "TAMLINUX_COMPOSITOR_LIVE_ACTIONS": "1", "SWAYSOCK": "/elsewhere"}):
            result = self.run_operation("focus-workspace", 160)
        capture.assert_not_called()
        self.assertEqual(result.state, "recorded")
        self.assertFalse(result.ok)
        self.assertFalse(result.may_have_changed)
        self.assertIsNone(result.outcome)

    def test_invalid_live_flag_and_requests_are_rejected_before_io(self):
        for operation, payload, live in [("focus-workspace", 161, True),
                                         ("focus-output", "*", True),
                                         ("reload", None, "1"),
                                         ("reload", None, 1),
                                         ("unknown", None, True)]:
            with self.subTest(operation=operation, live=live), patch.object(executor, "_capture") as capture:
                result = self.run_operation(operation, payload, live=live)
                self.assertEqual(result.reason, "rejected")
                capture.assert_not_called()

    def test_unsupported_does_not_become_recorded_or_successful(self):
        for operation, payload in [("rollinglog", None), ("config-errors", None),
                                   ("monitor-rule", ["DP-2", "preferred", "0x0", 1])]:
            with self.subTest(operation=operation), patch.object(executor, "_capture") as capture:
                result = self.run_operation(operation, payload)
                self.assertEqual(result.state, "unsupported")
                self.assertFalse(result.ok)
                capture.assert_not_called()

    def test_explicit_socket_and_one_deadline_for_both_reads(self):
        outputs, workspaces = sample()
        with patch.object(executor, "_capture", side_effect=[reply(json.dumps(outputs)),
                reply(json.dumps(workspaces))]) as capture, patch.dict(os.environ, {
                    "SWAYSOCK": "/wrong", "I3SOCK": "/also-wrong"}):
            result = self.run_operation("monitors")
        self.assertTrue(result.ok)
        self.assertEqual(result.data[0].pixel_mode.width, outputs[0]["current_mode"]["width"])
        self.assertEqual(result.data[0].logical_rect.width, outputs[0]["rect"]["width"])
        calls = capture.call_args_list
        for call in calls:
            self.assertEqual(call.args[0][:3], ("/usr/bin/swaymsg", "-s", self.path))
        self.assertEqual(calls[0].args[1], calls[1].args[1])

    def test_read_failure_stops_join_and_returns_no_stale_data(self):
        with patch.object(executor, "_capture", return_value=reply("[]", 1, "failed")) as capture:
            result = self.run_operation("monitors-all")
        self.assertEqual(result.reason, "query-failed")
        self.assertEqual(capture.call_count, 1)
        self.assertIsNone(result.data)
        self.assertFalse(result.may_have_changed)

    def test_inconsistent_or_malformed_facts_fail_without_retry(self):
        outputs, workspaces = sample()
        workspaces[0]["output"] = "other"
        for responses in [(json.dumps(outputs), json.dumps(workspaces)), ("[NaN]", "[]")]:
            with self.subTest(responses=responses), patch.object(executor, "_capture",
                    side_effect=[reply(value) for value in responses]) as capture:
                result = self.run_operation("monitors-all")
                self.assertEqual(result.reason, "invalid-reply")
                self.assertIsNone(result.data)
                self.assertEqual(capture.call_count, 2)

    def test_named_workspaces_keep_name_without_inventing_number(self):
        workspace = [{"name": "mail", "num": -1, "output": "DP-2",
                      "focused": True, "visible": True}]
        with patch.object(executor, "_capture", return_value=reply(json.dumps(workspace))):
            result = self.run_operation("active-workspace")
        self.assertTrue(result.ok)
        self.assertEqual(result.data.name, "mail")
        self.assertIsNone(result.data.number)

    def test_partial_failure_keeps_successful_indexes_even_with_exit_two(self):
        responses = '[{"success":true},{"success":false,"error":"failed"}]'
        with patch.object(executor, "_capture", return_value=reply(responses, 2)):
            result = self.run_operation("move-window", [160, "follow"], live=True)
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "command-failed")
        self.assertEqual(result.outcome.succeeded_indexes, (0,))
        self.assertEqual(result.outcome.failed_indexes, (1,))
        self.assertTrue(result.may_have_changed)

    def test_command_success_needs_valid_json_count_and_zero_process_status(self):
        for data, code, reason in [("[]", 0, "invalid-reply"),
                                   ('[{"success":"true"}]', 0, "invalid-reply"),
                                   ('[{"success":true}]', 1, "command-failed"),
                                   ('[{"success":false}]', 0, "command-failed")]:
            with self.subTest(data=data, code=code), patch.object(executor, "_capture",
                    return_value=reply(data, code)):
                result = self.run_operation("reload", live=True)
                self.assertEqual(result.reason, reason)
                self.assertTrue(result.may_have_changed)
        with patch.object(executor, "_capture", return_value=reply('[{"success":true}]')):
            self.assertTrue(self.run_operation("reload", live=True).ok)

    def test_interrupted_mutation_reports_uncertain_delivery_without_replay(self):
        for started in (False, True):
            with self.subTest(started=started), patch.object(executor, "_capture",
                    side_effect=executor.TransportError("deadline", started=started)) as capture:
                result = self.run_operation("reload", live=True)
                self.assertEqual(result.reason, "deadline")
                self.assertEqual(result.may_have_changed, started)
                self.assertEqual(capture.call_count, 1)

    def test_bad_socket_paths_never_trigger_automatic_discovery(self):
        for path in [None, "", "relative", "/tmp/x\0", "/" + "a" * 107, "/tmp/\ud800"]:
            with self.subTest(path=repr(path)), patch.object(executor, "_capture") as capture:
                result = executor.execute("monitors", socket_path=path)
                self.assertEqual(result.reason, "rejected")
                capture.assert_not_called()

    def test_socket_symlink_regular_file_missing_and_open_parent_fail(self):
        link = Path(self.directory.name) / "link"
        link.symlink_to(self.path)
        file = Path(self.directory.name) / "file"
        file.write_text("data")
        for path in [str(link), str(file), self.path + "missing"]:
            with self.subTest(path=path), patch.object(executor, "_capture") as capture:
                self.assertEqual(executor.execute("monitors", socket_path=path).reason, "endpoint")
                capture.assert_not_called()
        os.chmod(self.directory.name, 0o755)
        self.assertEqual(self.run_operation("monitors").reason, "endpoint")
        os.chmod(self.directory.name, 0o700)


class CaptureTests(unittest.TestCase):
    def capture_python(self, source, seconds=1):
        return executor._capture((sys.executable, "-I", "-c", source), time.monotonic() + seconds)

    def test_child_has_closed_environment_no_stdin_and_fixed_cwd(self):
        with patch.dict(os.environ, {"SWAYSOCK": "/bad", "LD_PRELOAD": "/bad", "PYTHONPATH": "/bad"}):
            result = self.capture_python("import os,sys,json; print(json.dumps(dict(os.environ))); "
                                         "print(os.getcwd()); print(repr(sys.stdin.read()))")
        lines = result.stdout.splitlines()
        self.assertEqual(json.loads(lines[0]), {"PATH": "/usr/bin", "LC_ALL": "C.UTF-8"})
        self.assertEqual(lines[1:], ["/", "''"])

    def test_both_pipes_are_drained_and_exit_status_preserved(self):
        result = self.capture_python("import os,sys; os.write(1,b'x'*100000); "
                                     "os.write(2,b'y'*100000); sys.exit(2)")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(len(result.stdout), 100000)
        self.assertEqual(len(result.stderr), 100000)

    def test_each_stream_is_capped_during_collection(self):
        for fd in (1, 2):
            with self.subTest(fd=fd), patch.object(executor, "IO_BYTES", 4096):
                with self.assertRaises(executor.TransportError) as error:
                    self.capture_python(f"import os; os.write({fd},b'x'*10000000)")
                self.assertEqual(error.exception.reason, "capped")
                self.assertTrue(error.exception.started)

    def test_hung_and_slow_drip_children_share_hard_deadline(self):
        for source in ["import time; time.sleep(30)",
                       "import time,os\nfor _ in range(1000):\n os.write(1,b'x'); time.sleep(.02)"]:
            with self.subTest(source=source):
                before = time.monotonic()
                with self.assertRaises(executor.TransportError) as error:
                    self.capture_python(source, .15)
                self.assertEqual(error.exception.reason, "deadline")
                self.assertTrue(error.exception.started)
                self.assertLess(time.monotonic() - before, 2)

    def test_closed_pipes_do_not_hide_a_hung_process(self):
        with self.assertRaises(executor.TransportError) as error:
            self.capture_python("import os,time; os.close(1); os.close(2); time.sleep(30)", .15)
        self.assertEqual(error.exception.reason, "deadline")

    def test_pipe_held_by_descendant_is_bounded(self):
        with self.assertRaises(executor.TransportError) as error:
            self.capture_python("import os,time\nif os.fork()==0: time.sleep(30)", .15)
        self.assertEqual(error.exception.reason, "deadline")

    def test_invalid_utf8_is_not_replaced_with_invented_json(self):
        with self.assertRaises(executor.TransportError) as error:
            self.capture_python("import os; os.write(1,b'\\xff')")
        self.assertEqual(error.exception.reason, "encoding")

    def test_missing_binary_and_expired_deadline_do_not_claim_delivery(self):
        with self.assertRaises(executor.TransportError) as error:
            executor._capture(("/nonexistent/swaymsg",), time.monotonic() + 1)
        self.assertEqual(error.exception.reason, "unavailable")
        self.assertFalse(error.exception.started)
        with self.assertRaises(executor.TransportError) as error:
            executor._capture(("/usr/bin/false",), time.monotonic() - 1)
        self.assertEqual(error.exception.reason, "deadline")
        self.assertFalse(error.exception.started)


if __name__ == "__main__":
    unittest.main()
