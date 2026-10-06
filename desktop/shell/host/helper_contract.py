# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline 0.4.0 contract candidate; no imports or calls to a compositor.

Keep physical mode pixels separate from logical layout coordinates. Unknown
facts remain None. This is not a drop-in backend for the existing helpers.
The candidate bounds are reviewable policy, not upstream Sway limits.
"""

from dataclasses import dataclass
import json
import re

MAX_BYTES = 262144
MAX_OUTPUTS = 64
MAX_WORKSPACES = 256
MAX_MODES = 256
MAX_COMMANDS = 64
HELPER_WORKSPACE_MAX = 160
OUTPUT_NAME = re.compile(r"[A-Za-z0-9._-]{1,64}")
TRANSFORMS = frozenset({"normal", "90", "180", "270", "flipped",
                        "flipped-90", "flipped-180", "flipped-270"})


class ContractError(ValueError):
    pass


def integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ContractError("integer outside contract bounds")
    return value


def helper_workspace(value):
    return integer(value, 1, HELPER_WORKSPACE_MAX)


def output_name(value):
    if not isinstance(value, str) or not OUTPUT_NAME.fullmatch(value):
        raise ContractError("output name")
    return value


def text(value):
    if not isinstance(value, str) or len(value) > 256 or "\0" in value:
        raise ContractError("text")
    return value


def boolean(value):
    if type(value) is not bool:
        raise ContractError("boolean")
    return value


def records(value, maximum):
    if not isinstance(value, list) or len(value) > maximum:
        raise ContractError("record list")
    if any(not isinstance(item, dict) for item in value):
        raise ContractError("record object")
    return value


def decode(payload):
    """Bounded JSON; duplicate keys and non-finite numbers are not facts."""
    if not isinstance(payload, str):
        raise ContractError("JSON size/type")
    try:
        size = len(payload.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise ContractError("invalid UTF-8 text") from error
    if size > MAX_BYTES:
        raise ContractError("JSON size/type")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ContractError("duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_):
        raise ContractError("non-finite JSON number")

    try:
        return json.loads(payload, object_pairs_hook=unique, parse_constant=nonfinite)
    except (ValueError, RecursionError) as error:
        raise ContractError("invalid JSON") from error


@dataclass(frozen=True)
class Mode:
    width: int
    height: int
    refresh_millihz: int

    @property
    def refresh_hz(self):
        return self.refresh_millihz / 1000 if self.refresh_millihz else None


def mode(value):
    if not isinstance(value, dict):
        raise ContractError("mode")
    return Mode(integer(value.get("width"), 1, 32768),
                integer(value.get("height"), 1, 32768),
                integer(value.get("refresh"), 0, 1000000))


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int


def rect(value):
    if not isinstance(value, dict):
        raise ContractError("rect")
    return Rect(integer(value.get("x"), -1000000, 1000000),
                integer(value.get("y"), -1000000, 1000000),
                integer(value.get("width"), 0, 32768),
                integer(value.get("height"), 0, 32768))


@dataclass(frozen=True)
class OutputFacts:
    name: str
    enabled: bool
    powered: bool
    focused: bool
    pixel_mode: Mode | None
    logical_rect: Rect
    scale: float | None
    transform: str | None
    workspace_name: str | None
    workspace_number: int | None
    modes: tuple[Mode, ...] | None
    # IPC lacks documented physical dimensions; don't invent millimetres.
    physical_width_mm: None = None
    physical_height_mm: None = None


def output_facts(outputs, workspaces):
    """Join two IPC responses. Focus comes from default-seat workspace facts.

    These reads aren't atomic. Inconsistent joins fail for a later bounded
    retry by the eventual executor; this function never retries or runs it.
    """
    workspaces = records(workspaces, MAX_WORKSPACES)
    by_name, focused_output = {}, None
    for workspace in workspaces:
        name = text(workspace.get("name"))
        if name in by_name:
            raise ContractError("duplicate workspace")
        number = integer(workspace.get("num"), -1, 2147483647)
        if number == 0:
            raise ContractError("zero workspace number")
        owner = output_name(workspace.get("output"))
        visible = boolean(workspace.get("visible"))
        focused = boolean(workspace.get("focused"))
        if focused:
            if focused_output is not None or not visible:
                raise ContractError("ambiguous workspace focus")
            focused_output = owner
        by_name[name] = (number if number > 0 else None, owner, visible)

    result, seen = [], set()
    for output in records(outputs, MAX_OUTPUTS):
        name = output_name(output.get("name"))
        if name in seen:
            raise ContractError("duplicate output")
        seen.add(name)
        enabled = boolean(output.get("active"))
        powered = boolean(output.get("power"))
        bounds = rect(output.get("rect"))
        workspace_name = output.get("current_workspace")
        number = None
        if enabled:
            workspace_name = text(workspace_name)
            joined = by_name.get(workspace_name)
            if not joined or joined[1] != name or not joined[2]:
                raise ContractError("inconsistent output/workspace snapshots")
            number = joined[0]
            scale = output.get("scale")
            if type(scale) not in (int, float) or not 0 < scale <= 16:
                raise ContractError("scale")
            transform = output.get("transform")
            if not isinstance(transform, str) or transform not in TRANSFORMS:
                raise ContractError("transform")
            current = mode(output.get("current_mode"))
        else:
            if workspace_name is not None or powered or focused_output == name:
                raise ContractError("inconsistent disabled output")
            scale, transform, current = None, None, None
        modes = (tuple(mode(item) for item in records(output["modes"], MAX_MODES))
                 if "modes" in output else None)
        result.append(OutputFacts(name, enabled, powered, focused_output == name,
                                  current, bounds, scale, transform,
                                  workspace_name, number, modes))
    if focused_output is not None and focused_output not in seen:
        raise ContractError("focused output missing")
    return tuple(result)


@dataclass(frozen=True)
class CommandOutcome:
    ok: bool
    succeeded_indexes: tuple[int, ...]
    failed_indexes: tuple[int, ...]


def command_outcome(payload, expected_commands=1):
    """All parsed command replies must succeed; a batch is not atomic."""
    integer(expected_commands, 1, MAX_COMMANDS)
    replies = records(decode(payload), MAX_COMMANDS)
    if len(replies) != expected_commands:
        raise ContractError("command reply count")
    succeeded, failed = [], []
    for index, reply in enumerate(replies):
        success = boolean(reply.get("success"))
        if "parse_error" in reply:
            success = success and not boolean(reply["parse_error"])
        if "error" in reply:
            success = success and text(reply["error"]) == ""
        (succeeded if success else failed).append(index)
    return CommandOutcome(not failed, tuple(succeeded), tuple(failed))
