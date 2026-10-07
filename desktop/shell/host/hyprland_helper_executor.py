# SPDX-License-Identifier: GPL-3.0-or-later
"""Execute optional named Hyprland helper plans against an explicit IPC socket.

Existing helpers do not load this candidate. No ambient session is discovered.
Mutations record unless live is exactly True; recording is not execution.
Delivery or acknowledgement does not establish the resulting display state.
"""

from dataclasses import dataclass
import os
import socket
import struct
import time

import helper_contract as contract
import hyprland_helper_backend as backend
import sway_helper_executor as transport

MAX_REQUEST_BYTES = 16384
IO_BYTES = contract.MAX_BYTES
DEADLINES = {"monitors": 4.0, "monitors-all": 4.0, "batch": 5.0,
             "monitor-rule": 5.0, "config-errors": 5.0,
             "rollinglog": 4.0, "reload": 8.0}
TransportError = transport.TransportError


@dataclass(frozen=True)
class ExecutionResult:
    state: str
    plan: backend.RequestPlan | None = None
    data: object = None
    outcome: contract.CommandOutcome | None = None
    reason: str | None = None
    # True means sending was attempted, including potentially partial delivery.
    may_have_changed: bool = False

    @property
    def ok(self):
        return self.state == "succeeded"


def _wire_request(plan):
    """Translate our closed argv builders using hyprctl's flags/batch format."""
    argv = plan.command_argv() if plan.commands else plan.query_argvs()[0]
    if argv[0] != backend.commands.HYPRCTL:
        raise contract.ContractError("request executable")
    if argv[1] == "--batch":
        text = "[[BATCH]]" + argv[2]
    else:
        args = [arg for arg in argv[1:] if arg != "-j"]
        text = ("j/" if "-j" in argv else "/") + " ".join(args)
    if "\0" in text or "\n" in text or "\r" in text:
        raise contract.ContractError("request text")
    data = text.encode("utf-8")
    if not 1 <= len(data) <= MAX_REQUEST_BYTES:
        raise contract.ContractError("request size")
    return data


def _remaining(deadline, started):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TransportError("deadline", started=started)
    return remaining


def _request(path, data, deadline):
    """Bound connect, send and complete reply by one deadline and byte cap."""
    started = False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(_remaining(deadline, started))
            connection.connect(path)
            peer = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                                         struct.calcsize("3i"))
            _, uid, _ = struct.unpack("3i", peer)
            if uid != os.getuid():
                raise TransportError("endpoint")
            connection.settimeout(_remaining(deadline, started))
            started = True
            connection.sendall(data)
            # Also terminates requests exactly divisible by the server's
            # 1023-byte read size; reading replies continues on this socket.
            connection.shutdown(socket.SHUT_WR)
            reply = bytearray()
            while True:
                connection.settimeout(_remaining(deadline, started))
                chunk = connection.recv(min(65536, IO_BYTES - len(reply) + 1))
                if not chunk:
                    break
                if len(reply) + len(chunk) > IO_BYTES:
                    raise TransportError("capped", started=started)
                reply.extend(chunk)
            try:
                text = reply.decode("utf-8")
            except UnicodeDecodeError as error:
                raise TransportError("encoding", started=started) from error
            if "\0" in text:
                raise TransportError("encoding", started=started)
            return text
    except TimeoutError as error:
        raise TransportError("deadline", started=started) from error
    except OSError as error:
        raise TransportError("transport" if started else "endpoint",
                             started=started) from error


def execute(operation, payload=None, *, socket_path, live=False):
    """Return normalized facts or a truthful result; never retry mutations."""
    plan = None
    try:
        if type(live) is not bool:
            raise contract.ContractError("live flag")
        plan = backend.request_plan(operation, payload)
        path = transport._socket_path(socket_path)
        wire = _wire_request(plan)
    except backend.UnsupportedOperation:
        return ExecutionResult("unsupported", plan=plan, reason="unsupported")
    except (ValueError, TypeError):
        return ExecutionResult("failed", plan=plan, reason="rejected")
    if plan.commands and not live:
        return ExecutionResult("recorded", plan=plan)
    delivered = False
    try:
        transport._check_socket(path)
        text = _request(path, wire, time.monotonic() + DEADLINES.get(operation, 2.0))
        delivered = bool(plan.commands)
        if plan.commands:
            outcome = plan.outcome(text)
            return ExecutionResult("succeeded" if outcome.ok else "failed", plan=plan,
                                   outcome=outcome, may_have_changed=True,
                                   reason=None if outcome.ok else "command-failed")
        if text.startswith("error:"):
            return ExecutionResult("failed", plan=plan, reason="query-failed")
        if operation in ("monitors", "monitors-all"):
            data = backend.monitor_facts(text, include_disabled=operation == "monitors-all")
        elif operation == "active-workspace":
            data = backend.active_workspace(text)
        else:
            data = text  # Bounded config diagnostics and non-following log.
        return ExecutionResult("succeeded", plan=plan, data=data)
    except backend.UnsupportedOperation:
        return ExecutionResult("unsupported", plan=plan, reason="unsupported",
                               may_have_changed=delivered)
    except TransportError as error:
        return ExecutionResult("failed", plan=plan, reason=error.reason,
                               may_have_changed=bool(plan.commands) and error.started)
    except OSError:
        return ExecutionResult("failed", plan=plan, reason="endpoint")
    except ValueError:
        return ExecutionResult("failed", plan=plan, reason="invalid-reply",
                               may_have_changed=delivered)
