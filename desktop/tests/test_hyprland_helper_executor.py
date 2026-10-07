# SPDX-License-Identifier: GPL-3.0-or-later
"""Named Hyprland execution against private IPC only; no desktop is contacted."""

import json
import os
from pathlib import Path
import socket
import struct
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

HOST = Path(__file__).resolve().parents[1] / "shell" / "host"
sys.path.insert(0, str(HOST))
import hyprland_helper_executor as executor
import hyprland_helper_backend as backend
from test_hyprland_helper_backend import monitor


class PlanExecutionTests(unittest.TestCase):
    def execute(self, operation, payload=None, **kwargs):
        with patch.object(executor.transport, "_check_socket"):
            return executor.execute(operation, payload, socket_path="/private/ipc.sock", **kwargs)

    def test_recorded_plan_is_not_executed_or_successful(self):
        with patch.object(executor, "_request") as request, patch.dict(os.environ, {
                "TAMLINUX_COMPOSITOR_LIVE_ACTIONS": "1",
                "HYPRLAND_INSTANCE_SIGNATURE": "wrong", "XDG_RUNTIME_DIR": "/wrong"}):
            result = self.execute("focus-workspace", 160)
        request.assert_not_called()
        self.assertEqual(result.state, "recorded")
        self.assertFalse(result.ok)
        self.assertFalse(result.may_have_changed)

    def test_invalid_requests_flags_and_paths_fail_before_io(self):
        cases = [("unknown", None, False), ("reload", None, "1"),
                 ("reload", None, 1), ("focus-workspace", 161, True),
                 ("focus-output", "DP-2;reload", True),
                 ("monitor-rule", ["DP-2", "disabled", "extra"], True)]
        for operation, payload, live in cases:
            with self.subTest(operation=operation, live=live), patch.object(executor, "_request") as request:
                self.assertEqual(self.execute(operation, payload, live=live).reason, "rejected")
                request.assert_not_called()
        for path in [None, "", "relative", "/x\0", "/" + "a" * 107, "/\ud800"]:
            with self.subTest(path=repr(path)), patch.object(executor, "_request") as request:
                self.assertEqual(executor.execute("monitors", socket_path=path).reason, "rejected")
                request.assert_not_called()

    def test_exact_wire_queries_and_mutations(self):
        cases = [("monitors", None, b"j/monitors"),
                 ("monitors-all", None, b"j/monitors all"),
                 ("active-workspace", None, b"j/activeworkspace"),
                 ("config-errors", None, b"/configerrors"),
                 ("rollinglog", None, b"/rollinglog"),
                 ("reload", None, b"/reload"),
                 ("focus-workspace-fallback", 160, b"/dispatch workspace 160"),
                 ("dpms-fallback", ["DP-2", "off"], b"/dispatch dpms off DP-2"),
                 ("batch", [["focus-workspace", 1], ["focus-output", "DP-2"]],
                  b'[[BATCH]]dispatch hl.dsp.focus({ workspace = "1" }); dispatch hl.dsp.focus({ monitor = "DP-2" })')]
        for operation, payload, wire in cases:
            with self.subTest(operation=operation):
                self.assertEqual(executor._wire_request(backend.request_plan(operation, payload)), wire)

    def test_wire_request_cap_is_enforced_before_delivery(self):
        with patch.object(executor, "MAX_REQUEST_BYTES", 6), patch.object(executor, "_request") as request:
            self.assertEqual(self.execute("reload", live=True).reason, "rejected")
            request.assert_not_called()

    def test_partial_batch_failures_keep_indexes_without_replay(self):
        payload = [["focus-workspace", 1], ["focus-output", "DP-2"]]
        with patch.object(executor, "_request", return_value="ok\n\n\nerror: output missing") as request:
            result = self.execute("batch", payload, live=True)
        self.assertEqual(result.reason, "command-failed")
        self.assertEqual(result.outcome.succeeded_indexes, (0,))
        self.assertEqual(result.outcome.failed_indexes, (1,))
        self.assertTrue(result.may_have_changed)
        self.assertEqual(request.call_count, 1)

    def test_acknowledgement_must_be_exact_and_complete(self):
        for reply, reason in [("ok", None), ("ok\n", None),
                              ("recorded\n", "command-failed"),
                              ("error: rejected", "command-failed"),
                              ("", "invalid-reply"), ("ok\n\n\nok", "command-failed")]:
            with self.subTest(reply=reply), patch.object(executor, "_request", return_value=reply):
                result = self.execute("reload", live=True)
                self.assertEqual(result.reason, reason)
                self.assertTrue(result.may_have_changed)
                self.assertEqual(result.ok, reason is None)
        with patch.object(executor, "_request", return_value="ok"):
            result = self.execute("batch", [["focus-workspace", 1], ["focus-output", "DP-2"]], live=True)
        self.assertEqual(result.reason, "invalid-reply")
        self.assertTrue(result.may_have_changed)

    def test_interrupted_delivery_is_uncertain_and_never_replayed(self):
        for started in (False, True):
            with self.subTest(started=started), patch.object(executor, "_request",
                    side_effect=executor.TransportError("deadline", started=started)) as request:
                result = self.execute("reload", live=True)
                self.assertEqual(result.reason, "deadline")
                self.assertEqual(result.may_have_changed, started)
                self.assertEqual(request.call_count, 1)

    def test_named_workspace_diagnostics_and_query_errors(self):
        workspace = json.dumps({"id": -1, "name": "mail", "monitor": "DP-2"})
        with patch.object(executor, "_request", return_value=workspace):
            result = self.execute("active-workspace")
        self.assertTrue(result.ok)
        self.assertEqual((result.data.name, result.data.number, result.data.output), ("mail", None, "DP-2"))
        for operation in ("config-errors", "rollinglog"):
            for text in ("", "diagnostic\n", "error: unavailable"):
                with self.subTest(operation=operation, text=text), patch.object(executor, "_request", return_value=text):
                    result = self.execute(operation)
                    self.assertEqual(result.reason, "query-failed" if text.startswith("error:") else None)
                    self.assertEqual(result.data, None if result.reason else text)
                    self.assertFalse(result.may_have_changed)

    def test_malformed_facts_and_unsupported_mirror_have_no_stale_data(self):
        row = monitor()
        row["mirrorOf"] = "OTHER"
        for text, state, reason in [("[NaN]", "failed", "invalid-reply"),
                                     ("{}", "failed", "invalid-reply"),
                                     (json.dumps([row]), "unsupported", "unsupported")]:
            with self.subTest(text=text), patch.object(executor, "_request", return_value=text):
                result = self.execute("monitors")
                self.assertEqual((result.state, result.reason), (state, reason))
                self.assertIsNone(result.data)


class PrivateIPCTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="tam-hypr-ipc-")
        self.addCleanup(self.directory.cleanup)
        self.path = self.directory.name + "/ipc.sock"
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(self.server.close)
        self.server.bind(self.path)
        self.server.listen(1)
        self.server.settimeout(2)
        self.wires = []
        self.errors = []

    def respond(self, response, *, delay=0, drip=False):
        def serve():
            try:
                with self.server.accept()[0] as connection:
                    connection.settimeout(2)
                    request = bytearray()
                    while chunk := connection.recv(65536):
                        request.extend(chunk)
                    self.wires.append(bytes(request))
                    time.sleep(delay)
                    if drip:
                        for value in response:
                            connection.sendall(bytes([value]))
                            time.sleep(.03)
                    else:
                        connection.sendall(response)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Expected when client enforces its deadline or byte cap.
            except Exception as error:
                self.errors.append(error)
        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        def finish():
            thread.join(3)
            self.assertFalse(thread.is_alive(), "private IPC server did not stop")
            self.assertEqual(self.errors, [])
        self.addCleanup(finish)

    def test_real_private_socket_returns_typed_monitor_facts(self):
        self.respond(json.dumps([monitor()]).encode())
        with patch.dict(os.environ, {"HYPRLAND_INSTANCE_SIGNATURE": "wrong",
                                     "XDG_RUNTIME_DIR": "/wrong"}):
            result = executor.execute("monitors", socket_path=self.path)
        self.assertTrue(result.ok)
        self.assertEqual(result.data[0].logical_rect.width, 1080)
        self.assertEqual(result.data[0].pixel_mode.width, 3840)
        self.assertEqual(self.wires, [b"j/monitors"])

    def test_real_private_socket_acknowledges_one_mutation(self):
        self.respond(b"ok")
        result = executor.execute("reload", socket_path=self.path, live=True)
        self.assertTrue(result.ok)
        self.assertTrue(result.may_have_changed)
        self.assertEqual(self.wires, [b"/reload"])

    def test_large_requests_terminate_at_write_half_close(self):
        wire = b"/" + b"a" * 2045  # Exactly two server-sized 1023-byte chunks.
        self.respond(b"ok")
        result = executor._request(self.path, wire, time.monotonic() + 1)
        self.assertEqual(result, "ok")
        self.assertEqual(self.wires, [wire])

    def test_stream_cap_is_enforced_before_decoding(self):
        self.respond(b"x" * 65)
        with patch.object(executor, "IO_BYTES", 64):
            result = executor.execute("reload", socket_path=self.path, live=True)
        self.assertEqual(result.reason, "capped")
        self.assertTrue(result.may_have_changed)

    def test_invalid_utf8_is_not_replaced_with_invented_facts(self):
        self.respond(b"\xff")
        result = executor.execute("monitors", socket_path=self.path)
        self.assertEqual(result.reason, "encoding")
        self.assertFalse(result.may_have_changed)

    def test_nul_response_is_rejected(self):
        self.respond(b"ok\0")
        result = executor.execute("reload", socket_path=self.path, live=True)
        self.assertEqual(result.reason, "encoding")
        self.assertTrue(result.may_have_changed)

    def test_slow_drip_does_not_reset_total_deadline(self):
        self.respond(b"ok" * 30, drip=True)
        before = time.monotonic()
        with patch.dict(executor.DEADLINES, {"reload": .12}):
            result = executor.execute("reload", socket_path=self.path, live=True)
        self.assertEqual(result.reason, "deadline")
        self.assertTrue(result.may_have_changed)
        self.assertLess(time.monotonic() - before, 1)

    def test_hung_read_has_no_mutation_delivery_flag(self):
        self.respond(b"[]", delay=.2)
        with patch.dict(executor.DEADLINES, {"monitors": .08}):
            result = executor.execute("monitors", socket_path=self.path)
        self.assertEqual(result.reason, "deadline")
        self.assertFalse(result.may_have_changed)

    def test_endpoint_validation_precedes_any_connection(self):
        link = Path(self.directory.name) / "link"
        link.symlink_to(self.path)
        file = Path(self.directory.name) / "file"
        file.write_text("data")
        for path in (str(link), str(file), self.path + "missing"):
            with self.subTest(path=path), patch.object(executor, "_request") as request:
                self.assertEqual(executor.execute("monitors", socket_path=path).reason, "endpoint")
                request.assert_not_called()
        os.chmod(self.directory.name, 0o755)
        self.assertEqual(executor.execute("monitors", socket_path=self.path).reason, "endpoint")
        os.chmod(self.directory.name, 0o700)

    def test_foreign_peer_credentials_prevent_sending(self):
        with patch.object(executor.socket, "socket") as constructor:
            connection = constructor.return_value.__enter__.return_value
            connection.getsockopt.return_value = struct.pack("3i", 123, os.getuid() + 1, 0)
            with self.assertRaises(executor.TransportError) as error:
                executor._request(self.path, b"/reload", time.monotonic() + 1)
        self.assertEqual(error.exception.reason, "endpoint")
        self.assertFalse(error.exception.started)
        connection.sendall.assert_not_called()

    def test_expired_deadline_never_claims_delivery(self):
        with self.assertRaises(executor.TransportError) as error:
            executor._request(self.path, b"/reload", time.monotonic() - 1)
        self.assertEqual(error.exception.reason, "deadline")
        self.assertFalse(error.exception.started)

    def test_failed_send_may_have_delivered_a_prefix(self):
        with patch.object(executor.socket, "socket") as constructor:
            connection = constructor.return_value.__enter__.return_value
            connection.getsockopt.return_value = struct.pack("3i", 123, os.getuid(), 0)
            connection.sendall.side_effect = BrokenPipeError("partial send")
            with self.assertRaises(executor.TransportError) as error:
                executor._request(self.path, b"/reload", time.monotonic() + 1)
        self.assertEqual(error.exception.reason, "transport")
        self.assertTrue(error.exception.started)
        connection.recv.assert_not_called()

    def test_exact_byte_limit_is_accepted(self):
        self.respond(b"x" * 64)
        with patch.object(executor, "IO_BYTES", 64):
            reply = executor._request(self.path, b"/rollinglog", time.monotonic() + 1)
        self.assertEqual(reply, "x" * 64)


if __name__ == "__main__":
    unittest.main()
