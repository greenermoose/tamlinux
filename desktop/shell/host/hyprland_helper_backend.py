# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline Hyprland counterpart to the 0.4.0 helper contract candidate.

Build requests and decode facts only. Existing helpers do not load this module.
Transport, config persistence, rollback and live parity remain separate work.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import math
import re

import compositor_commands as commands
import helper_contract as contract

READS = frozenset({"monitors", "monitors-all", "active-workspace",
                   "config-errors", "rollinglog"})
MUTATIONS = frozenset({"focus-workspace", "focus-workspace-fallback",
    "focus-output", "focus-output-fallback", "move-window", "move-window-fallback",
    "move-workspace", "move-workspace-fallback", "dpms", "dpms-fallback",
    "batch", "monitor-rule", "reload"})
OPERATIONS = READS | MUTATIONS
TRANSFORMS = ("normal", "90", "180", "270", "flipped", "flipped-90",
              "flipped-180", "flipped-270")
MODE = re.compile(r"([1-9]\d{0,4})x([1-9]\d{0,4})@(\d{1,4}(?:\.\d{1,5})?)Hz")


class UnsupportedOperation(contract.ContractError):
    """Facts cannot be represented truthfully by this candidate."""


def _sequence(value, lengths):
    if not isinstance(value, (list, tuple)) or len(value) not in lengths:
        raise contract.ContractError("payload shape")
    return value


def _output(value):
    name = contract.output_name(value)
    if name in {"current", "left", "right", "up", "down"}:
        raise contract.ContractError("output selector is not a literal name")
    return name


def _choice(value, true_word, false_word):
    if type(value) is bool:
        return value
    if not isinstance(value, str) or value not in {true_word, false_word}:
        raise contract.ContractError("choice")
    return value == true_word


@dataclass(frozen=True)
class RequestPlan:
    operation: str
    queries: tuple[tuple[str, ...], ...] = ()
    commands: tuple[tuple[str, ...], ...] = ()

    def query_argvs(self):
        return self.queries

    def command_argv(self):
        if not self.commands:
            raise contract.ContractError("no mutation commands")
        if self.operation != "batch":
            return self.commands[0]
        return (commands.HYPRCTL, "--batch",
                "; ".join(" ".join(argv[1:]) for argv in self.commands))

    def outcome(self, payload):
        """Interpret Hyprland's triple-newline batch separator, never exit code.

        `ok` confirms an IPC acknowledgement, not verified display state.
        Unknown/short replies fail without guessing which mutation executed.
        """
        if not self.commands:
            raise contract.ContractError("read plan has no command outcome")
        if not isinstance(payload, str):
            raise contract.ContractError("reply type")
        try:
            size = len(payload.encode("utf-8"))
        except UnicodeEncodeError as error:
            raise contract.ContractError("reply encoding") from error
        if size > contract.MAX_BYTES or "\0" in payload:
            raise contract.ContractError("reply size/text")
        replies = payload.rstrip("\n").split("\n\n\n") if self.operation == "batch" else [payload.rstrip("\n")]
        if len(replies) != len(self.commands) or any(not reply for reply in replies):
            raise contract.ContractError("command reply count")
        succeeded = tuple(i for i, reply in enumerate(replies) if reply == "ok")
        failed = tuple(i for i, reply in enumerate(replies) if reply != "ok")
        return contract.CommandOutcome(not failed, succeeded, failed)


def request_plan(operation, payload=None):
    """Build the same bounded named helper operations as the Sway candidate."""
    if not isinstance(operation, str) or operation not in OPERATIONS:
        raise contract.ContractError("operation")
    if operation in READS or operation == "reload":
        if payload is not None:
            raise contract.ContractError("unexpected payload")
        if operation == "reload":
            return RequestPlan(operation, commands=(tuple(commands.reload_argv()),))
        builder = {"monitors": commands.monitors_argv,
                   "monitors-all": commands.monitors_all_argv,
                   "active-workspace": commands.active_workspace_argv,
                   "config-errors": commands.config_errors_argv,
                   "rollinglog": commands.rollinglog_argv}[operation]
        return RequestPlan(operation, queries=(tuple(builder()),))
    if operation.startswith("focus-workspace"):
        number = contract.helper_workspace(commands.parse_workspace(payload, public=False))
        builder = (commands.focus_workspace_fallback_argv if operation.endswith("-fallback")
                   else commands.dispatch_focus_workspace_argv)
        argv = builder(number)
    elif operation.startswith("focus-output"):
        builder = (commands.focus_output_fallback_argv if operation.endswith("-fallback")
                   else commands.focus_output_argv)
        argv = builder(_output(payload))
    elif operation.startswith("move-window"):
        number, follow = _sequence(payload, {2})
        number = contract.helper_workspace(commands.parse_workspace(number, public=False))
        follow = _choice(follow, "follow", "stay")
        builder = (commands.move_window_fallback_argv if operation.endswith("-fallback")
                   else commands.move_window_argv)
        argv = builder(number, follow)
    elif operation == "move-workspace":
        argv = commands.move_workspace_argv(_output(payload))
    elif operation == "move-workspace-fallback":
        number, output = _sequence(payload, {2})
        number = contract.helper_workspace(commands.parse_workspace(number, public=False))
        argv = commands.move_workspace_fallback_argv(number, _output(output))
    elif operation.startswith("dpms"):
        output, power = _sequence(payload, {2})
        power = _choice(power, "on", "off")
        builder = (commands.set_dpms_fallback_argv if operation.endswith("-fallback")
                   else commands.set_dpms_argv)
        argv = builder(_output(output), power)
    elif operation == "monitor-rule":
        fields = _sequence(payload, {2, 4, 5})
        output = _output(fields[0])
        if len(fields) == 2:
            if fields[1] != "disabled":
                raise contract.ContractError("disabled payload")
            argv = commands.monitor_rule_argv(output, disabled=True)
        else:
            try:
                argv = commands.monitor_rule_argv(output, disabled=False, mode=fields[1],
                    position=fields[2], scale=fields[3],
                    transform=fields[4] if len(fields) == 5 else None)
            except OverflowError as error:
                raise contract.ContractError("scale outside contract bounds") from error
    elif operation == "batch":
        if not isinstance(payload, list) or not 1 <= len(payload) <= contract.MAX_COMMANDS:
            raise contract.ContractError("batch")
        steps = []
        for step in payload:
            kind, value = _sequence(step, {2})
            if not isinstance(kind, str) or kind not in {"focus-workspace", "focus-output", "move-workspace"}:
                raise contract.ContractError("batch step")
            steps.extend(request_plan(kind, value).commands)
        return RequestPlan(operation, commands=tuple(steps))
    else:
        raise contract.ContractError("operation")
    return RequestPlan(operation, commands=(tuple(argv),))


def _number(value, minimum, maximum):
    if type(value) not in (int, float) or not minimum <= value <= maximum:
        raise contract.ContractError("number outside contract bounds")
    return value


def _millihz(value):
    _number(value, 0, 1000)
    return int((Decimal(str(value)) * 1000).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _mode_list(value):
    if not isinstance(value, list) or len(value) > contract.MAX_MODES:
        raise contract.ContractError("mode list")
    result = []
    for item in value:
        match = MODE.fullmatch(item) if isinstance(item, str) else None
        if not match:
            raise contract.ContractError("advertised mode")
        width, height, refresh = match.groups()
        result.append(contract.mode({"width": int(width), "height": int(height),
                                     "refresh": _millihz(float(refresh))}))
    return tuple(result)


def _workspace(value):
    if not isinstance(value, dict):
        raise contract.ContractError("workspace")
    number = contract.integer(value.get("id"), -2147483648, 2147483647)
    if number == 0:
        raise contract.ContractError("zero workspace number")
    return contract.text(value.get("name")), number if number > 0 else None


@dataclass(frozen=True)
class WorkspaceFocus:
    name: str
    number: int | None
    output: str


def active_workspace(workspace_json):
    value = contract.decode(workspace_json)
    name, number = _workspace(value)
    return WorkspaceFocus(name, number, contract.output_name(value.get("monitor")))


def monitor_facts(monitors_json, *, include_disabled=False):
    """Preserve common facts; derive logical bounds using Hyprland rounding.

    IPC reports untransformed pixels. Hyprland swaps axes for odd transforms,
    then rounds positive scaled dimensions away from zero at a half. Mirrored
    outputs are unsupported: their workspace ownership needs its own contract.
    Disabled rows can retain stale mode, workspace and DPMS values; those do
    not describe an enabled output. The candidate has no physical-size fields
    that can hold known values. Advertised refresh strings are already rounded
    by Hyprland; they are observed values, not precision for hardware retraining.
    """
    if type(include_disabled) is not bool:
        raise contract.ContractError("include disabled flag")
    result, seen, focus_count, workspace_owners = [], set(), 0, set()
    for row in contract.records(contract.decode(monitors_json), contract.MAX_OUTPUTS):
        name = contract.output_name(row.get("name"))
        if name in seen:
            raise contract.ContractError("duplicate output")
        seen.add(name)
        enabled = not contract.boolean(row.get("disabled"))
        powered = contract.boolean(row.get("dpmsStatus"))
        focused = contract.boolean(row.get("focused"))
        x = contract.integer(row.get("x"), -1000000, 1000000)
        y = contract.integer(row.get("y"), -1000000, 1000000)
        modes = _mode_list(row["availableModes"]) if "availableModes" in row else None
        if enabled:
            if row.get("mirrorOf", "none") != "none":
                raise UnsupportedOperation("mirrored output")
            width = contract.integer(row.get("width"), 1, 32768)
            height = contract.integer(row.get("height"), 1, 32768)
            scale = _number(row.get("scale"), 0.1, 16)
            transform = contract.integer(row.get("transform"), 0, 7)
            logical_w, logical_h = (height, width) if transform % 2 else (width, height)
            bounds = contract.rect({"x": x, "y": y,
                "width": math.floor(logical_w / scale + 0.5),
                "height": math.floor(logical_h / scale + 0.5)})
            pixel_mode = contract.Mode(width, height, _millihz(row.get("refreshRate")))
            workspace_name, number = _workspace(row.get("activeWorkspace"))
            workspace_id = row["activeWorkspace"]["id"]
            if workspace_id in workspace_owners:
                raise contract.ContractError("workspace on multiple outputs")
            workspace_owners.add(workspace_id)
            focus_count += focused
            if focus_count > 1:
                raise contract.ContractError("ambiguous output focus")
            transform = TRANSFORMS[transform]
        else:
            # The IPC keeps last mode/scale/workspace after output disable.
            bounds = contract.Rect(x, y, 0, 0)
            pixel_mode = scale = transform = workspace_name = number = None
            powered = focused = False
        fact = contract.OutputFacts(name, enabled, powered, focused, pixel_mode,
                                   bounds, scale, transform, workspace_name, number, modes)
        if include_disabled or enabled:
            result.append(fact)
    return tuple(result)
