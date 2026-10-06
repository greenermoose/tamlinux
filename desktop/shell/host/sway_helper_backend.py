# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure request/read candidate for workspace and monitor helpers on Sway.

No executor, subprocess, config writer, or .run() compatibility shim. Existing
helpers do not select this module. Their wiring, rollback, closed environment,
deadlines, live-action gate and live parity remain separate implementation work.
"""

from dataclasses import dataclass

import compositor_commands as validators
import helper_contract as contract

SWAYMSG = "/usr/bin/swaymsg"
READS = frozenset({"monitors", "monitors-all", "active-workspace"})
UNSUPPORTED = frozenset({"config-errors", "rollinglog"})
ALIASES = {f"{name}-fallback": name for name in (
    "focus-workspace", "focus-output", "move-window", "dpms")}
OPERATIONS = READS | UNSUPPORTED | frozenset(ALIASES) | frozenset({
    "focus-workspace", "focus-output", "move-window", "move-workspace",
    "move-workspace-fallback", "dpms", "batch", "monitor-rule", "reload"})


class UnsupportedOperation(contract.ContractError):
    """No evidenced translation is supplied by this candidate."""


def literal_output(value):
    name = contract.output_name(value)
    # These helper APIs target literal outputs, not Sway directional selectors.
    if name in {"current", "left", "right", "up", "down"}:
        raise contract.ContractError("output selector is not a literal name")
    return name


def workspace(value):
    return contract.helper_workspace(validators.parse_workspace(value, public=False))


def sequence(value, lengths):
    if not isinstance(value, (list, tuple)) or len(value) not in lengths:
        raise contract.ContractError("payload shape")
    return value


def focus_workspace(value):
    return f"workspace --no-auto-back-and-forth number {workspace(value)}"


def monitor_commands(payload):
    fields = sequence(payload, {2, 4, 5})
    output = literal_output(fields[0])
    if len(fields) == 2:
        if fields[1] != "disabled":
            raise contract.ContractError("disabled payload")
        return (f"output {output} disable",)
    mode = validators.require_mode(fields[1])
    if mode == "preferred":
        raise UnsupportedOperation("preferred-mode selection needs a defined Sway policy")
    if not mode.endswith("Hz"):
        mode += "Hz"
    x, y = validators.require_position(fields[2]).split("x")
    try:
        scale = validators.format_scale(fields[3])
    except OverflowError as error:
        raise contract.ContractError("scale outside contract bounds") from error
    commands = (f"output {output} enable", f"output {output} mode {mode}",
                f"output {output} pos {int(x)} {int(y)}", f"output {output} scale {scale}")
    if len(fields) == 5:
        transform = validators.require_transform(fields[4])
        if transform != 0:
            raise UnsupportedOperation("numeric transform mapping requires parity evidence")
        commands += (f"output {output} transform normal",)
    return commands


@dataclass(frozen=True)
class RequestPlan:
    operation: str
    queries: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()

    def query_argvs(self):
        return tuple((SWAYMSG, "-t", query, "-r") for query in self.queries)

    def command_argv(self):
        if not self.commands:
            raise contract.ContractError("no mutation commands")
        return (SWAYMSG, "-r", "--", "; ".join(self.commands))

    def outcome(self, payload):
        if not self.commands:
            raise contract.ContractError("read plan has no command outcome")
        return contract.command_outcome(payload, expected_commands=len(self.commands))


def request_plan(operation, payload=None):
    """Build bounded named requests only; this function never runs them."""
    if not isinstance(operation, str) or operation not in OPERATIONS:
        raise contract.ContractError("operation")
    if operation in UNSUPPORTED:
        raise UnsupportedOperation(operation)
    if operation in READS or operation == "reload":
        if payload is not None:
            raise contract.ContractError("unexpected payload")
        if operation == "reload":
            return RequestPlan(operation, commands=("reload",))
        queries = ("get_workspaces",) if operation == "active-workspace" else (
            "get_outputs", "get_workspaces")
        return RequestPlan(operation, queries=queries)
    base = ALIASES.get(operation, operation)
    if base == "focus-workspace":
        commands = (focus_workspace(payload),)
    elif base == "focus-output":
        commands = (f"focus output {literal_output(payload)}",)
    elif base == "move-workspace":
        commands = (f"move workspace to output {literal_output(payload)}",)
    elif base == "move-workspace-fallback":
        number, output = sequence(payload, {2})
        commands = (focus_workspace(number), f"move workspace to output {literal_output(output)}")
    elif base == "move-window":
        number, follow = sequence(payload, {2})
        if type(follow) is bool:
            follow = "follow" if follow else "stay"
        if not isinstance(follow, str) or follow not in {"follow", "stay"}:
            raise contract.ContractError("follow")
        number = workspace(number)
        commands = (f"move --no-auto-back-and-forth container to workspace number {number}",)
        if follow == "follow":
            commands += (focus_workspace(number),)
    elif base == "dpms":
        output, power = sequence(payload, {2})
        output = literal_output(output)
        if type(power) is bool:
            power = "on" if power else "off"
        if not isinstance(power, str) or power not in {"on", "off"}:
            raise contract.ContractError("power")
        commands = (f"output {output} power {power}",)
    elif base == "monitor-rule":
        commands = monitor_commands(payload)
    elif base == "batch":
        if not isinstance(payload, list) or not 1 <= len(payload) <= contract.MAX_COMMANDS:
            raise contract.ContractError("batch")
        commands = []
        for step in payload:
            kind, value = sequence(step, {2})
            if not isinstance(kind, str) or kind not in {
                    "focus-workspace", "focus-output", "move-workspace"}:
                raise contract.ContractError("batch step")
            commands.extend(request_plan(kind, value).commands)
        commands = tuple(commands)
    else:
        raise contract.ContractError("operation")
    if not 1 <= len(commands) <= contract.MAX_COMMANDS:
        raise contract.ContractError("command count")
    return RequestPlan(operation, commands=commands)


def monitor_facts(outputs_json, workspaces_json, *, include_disabled=False):
    """Return typed candidate facts, not a guessed legacy helper dictionary."""
    facts = contract.output_facts(contract.decode(outputs_json), contract.decode(workspaces_json))
    return facts if include_disabled else tuple(item for item in facts if item.enabled)


@dataclass(frozen=True)
class WorkspaceFocus:
    name: str
    number: int | None
    output: str


def active_workspace(workspaces_json):
    focused = []
    for row in contract.records(contract.decode(workspaces_json), contract.MAX_WORKSPACES):
        if contract.boolean(row.get("focused")):
            if not contract.boolean(row.get("visible")):
                raise contract.ContractError("focused workspace not visible")
            number = contract.integer(row.get("num"), -1, 2147483647)
            if number == 0:
                raise contract.ContractError("zero workspace number")
            focused.append(WorkspaceFocus(contract.text(row.get("name")),
                                          number if number > 0 else None,
                                          contract.output_name(row.get("output"))))
    if len(focused) != 1:
        raise contract.ContractError("ambiguous workspace focus")
    return focused[0]
