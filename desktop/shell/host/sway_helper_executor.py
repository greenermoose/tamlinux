# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional 0.4.0 executor candidate; existing helpers do not load this module.

Callers select an IPC socket explicitly. Mutations are recorded unless live is
exactly True. A recorded plan is not a successful compositor operation. Failed
or interrupted mutations may have changed state; callers must reconcile it.
"""

from dataclasses import dataclass
import os
import selectors
import signal
import stat
import subprocess
import time

import helper_contract as contract
import sway_helper_backend as backend

IO_BYTES = contract.MAX_BYTES  # per stream, per child, bounded during collection
DIAGNOSTIC_BYTES = 4096
DEADLINES = {"monitors": 4.0, "monitors-all": 4.0, "batch": 5.0,
             "monitor-rule": 5.0, "reload": 8.0}


class TransportError(Exception):
    def __init__(self, reason, *, started=False):
        super().__init__(reason)
        self.reason = reason
        self.started = started


@dataclass(frozen=True)
class ExecutionResult:
    state: str
    plan: backend.RequestPlan | None = None
    data: object = None
    outcome: contract.CommandOutcome | None = None
    reason: str | None = None
    # This means delivery was attempted, not that a state change was verified.
    may_have_changed: bool = False
    stderr: str = ""

    @property
    def ok(self):
        return self.state == "succeeded"


def _socket_path(value):
    if not isinstance(value, str) or not os.path.isabs(value) or "\0" in value:
        raise contract.ContractError("socket path")
    try:
        length = len(value.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise contract.ContractError("socket encoding") from error
    if length > 107:
        raise contract.ContractError("socket path length")
    return value


def _check_socket(path):
    """Refuse symlinks, foreign sockets and non-private immediate parents.

    This is an endpoint selection check, not protection against processes owned
    by this same user replacing an ancestor or socket after inspection.
    """
    parent = os.lstat(os.path.dirname(path))
    node = os.lstat(path)
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid()
            or parent.st_mode & 0o077 or not stat.S_ISSOCK(node.st_mode)
            or node.st_uid != os.getuid()):
        raise TransportError("endpoint")


def _capture(argv, deadline):
    """Drain both pipes against a single monotonic deadline and byte limits."""
    if time.monotonic() >= deadline:
        raise TransportError("deadline")
    try:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env={"PATH": "/usr/bin", "LC_ALL": "C.UTF-8"},
                                   cwd="/", start_new_session=True)
    except OSError as error:
        raise TransportError("unavailable") from error
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    try:
        with selectors.DefaultSelector() as selector:
            for name in streams:
                pipe = getattr(process, name)
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            # Even one-byte writes cannot make this an unbounded event loop.
            for _ in range(2 * IO_BYTES + 64):
                if not selector.get_map():
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TransportError("deadline", started=True)
                for key, _ in selector.select(remaining):
                    buffer = streams[key.data]
                    chunk = os.read(key.fileobj.fileno(), min(65536, IO_BYTES - len(buffer) + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif len(buffer) + len(chunk) > IO_BYTES:
                        raise TransportError("capped", started=True)
                    else:
                        buffer.extend(chunk)
            else:
                raise TransportError("capped", started=True)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TransportError("deadline", started=True)
        try:
            code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            raise TransportError("deadline", started=True) from error
        try:
            stdout = streams["stdout"].decode("utf-8")
            stderr = streams["stderr"].decode("utf-8")
        except UnicodeDecodeError as error:
            raise TransportError("encoding", started=True) from error
        return subprocess.CompletedProcess(argv, code, stdout, stderr)
    except OSError as error:
        raise TransportError("transport", started=True) from error
    finally:
        # Also kill descendants holding a pipe after the direct child exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        process.stdout.close()
        process.stderr.close()


def execute(operation, payload=None, *, socket_path, live=False):
    """Execute a named plan and return typed facts or a truthful failure.

    Reads share one deadline, so a slow first read does not grant the second
    another full timeout. Inconsistent snapshots fail without guessing or
    replaying a mutation. No ambient SWAYSOCK/I3SOCK or live-action flag is read.
    """
    plan = None
    try:
        if type(live) is not bool:
            raise contract.ContractError("live flag")
        plan = backend.request_plan(operation, payload)
        path = _socket_path(socket_path)
    except backend.UnsupportedOperation:
        return ExecutionResult("unsupported", reason="unsupported")
    except (ValueError, TypeError):
        return ExecutionResult("failed", plan=plan, reason="rejected")
    if plan.commands and not live:
        return ExecutionResult("recorded", plan=plan)
    attempted_mutation = False
    diagnostic = ""
    try:
        _check_socket(path)
        deadline = time.monotonic() + DEADLINES.get(operation, 2.0)
        prefix = (backend.SWAYMSG, "-s", path)
        if plan.commands:
            result = _capture(prefix + plan.command_argv()[1:], deadline)
            attempted_mutation = True
            diagnostic = result.stderr[:DIAGNOSTIC_BYTES]
            # swaymsg can exit 2 for a valid partial-failure JSON response.
            outcome = plan.outcome(result.stdout)
            success = result.returncode == 0 and outcome.ok
            return ExecutionResult("succeeded" if success else "failed", plan=plan,
                                   outcome=outcome,
                                   reason=None if success else "command-failed",
                                   may_have_changed=True, stderr=diagnostic)
        replies = []
        for argv in plan.query_argvs():
            result = _capture(prefix + argv[1:], deadline)
            diagnostic = result.stderr[:DIAGNOSTIC_BYTES]
            if result.returncode != 0:
                return ExecutionResult("failed", plan=plan, reason="query-failed",
                                       stderr=diagnostic)
            replies.append(result.stdout)
        data = (backend.active_workspace(replies[0]) if operation == "active-workspace"
                else backend.monitor_facts(*replies, include_disabled=operation == "monitors-all"))
        return ExecutionResult("succeeded", plan=plan, data=data, stderr=diagnostic)
    except TransportError as error:
        return ExecutionResult("failed", plan=plan, reason=error.reason,
                               may_have_changed=bool(plan.commands) and error.started)
    except OSError:
        return ExecutionResult("failed", plan=plan, reason="endpoint",
                               may_have_changed=attempted_mutation)
    except ValueError:
        return ExecutionResult("failed", plan=plan, reason="invalid-reply",
                               may_have_changed=attempted_mutation, stderr=diagnostic)
