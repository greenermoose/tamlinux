"""Argv for the Hyprland adapter. This module does not run commands."""

from __future__ import annotations

import json
import re

HYPRCTL = "/usr/bin/hyprctl"
NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
APP_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._+-]{0,63}$")
ADDRESS_RE = re.compile(r"^(?:0x)?([0-9a-fA-F]{1,16})$")
WORKSPACE_MIN = 1
WORKSPACE_MAX = 10
DISPATCH_WORKSPACE_MAX = 160
BATCH_LIMIT = 64
MODE_RE = re.compile(
    r"^(?:preferred|[1-9]\d{0,4}x[1-9]\d{0,4}@[1-9]\d{0,3}(?:\.\d{1,3})?(?:Hz)?)$"
)
POSITION_RE = re.compile(r"^-?\d{1,6}x-?\d{1,6}$")
BINDS_LIMIT = 262144
DEVICES_LIMIT = 262144
MONITORS_LIMIT = 262144
KEYMAP_LIMIT = 128
DESCRIPTION_LIMIT = 128
WINDOW_LIMIT = 8
TITLE_LIMIT = 80
CLASS_LIMIT = 64
WORKSPACE_LIST_LIMIT = 64


class CompositorCommandError(ValueError):
    """A compositor action was not a fixed, bounded command."""


def require_output(name: str) -> str:
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise CompositorCommandError("output")
    return name


def require_workspace(workspace_id: int) -> int:
    if isinstance(workspace_id, bool) or not isinstance(workspace_id, int):
        raise CompositorCommandError("workspace")
    if workspace_id < WORKSPACE_MIN or workspace_id > WORKSPACE_MAX:
        raise CompositorCommandError("workspace")
    return workspace_id


def require_dispatch_workspace(workspace_id: int) -> int:
    """Windows-mode set ids: (desktop - 1) * topology + slot + 1, at most 160."""
    if isinstance(workspace_id, bool) or not isinstance(workspace_id, int):
        raise CompositorCommandError("workspace")
    if workspace_id < WORKSPACE_MIN or workspace_id > DISPATCH_WORKSPACE_MAX:
        raise CompositorCommandError("workspace")
    return workspace_id


def parse_workspace(value: object, *, public: bool) -> int:
    if isinstance(value, bool):
        raise CompositorCommandError("workspace")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.isdigit():
        number = int(value)
    else:
        raise CompositorCommandError("workspace")
    if public:
        return require_workspace(number)
    return require_dispatch_workspace(number)


def binds_argv() -> list[str]:
    return [HYPRCTL, "binds"]


def devices_argv() -> list[str]:
    return [HYPRCTL, "-j", "devices"]


def monitors_argv() -> list[str]:
    return [HYPRCTL, "-j", "monitors"]


def monitors_all_argv() -> list[str]:
    return [HYPRCTL, "monitors", "all", "-j"]


def active_workspace_argv() -> list[str]:
    return [HYPRCTL, "activeworkspace", "-j"]


def config_errors_argv() -> list[str]:
    return [HYPRCTL, "configerrors"]


def rollinglog_argv() -> list[str]:
    return [HYPRCTL, "rollinglog"]


def reload_argv() -> list[str]:
    return [HYPRCTL, "reload"]


def _focus_workspace_dispatch(number: int) -> list[str]:
    return [HYPRCTL, "dispatch", f'hl.dsp.focus({{ workspace = "{number}" }})']


def focus_workspace_argv(workspace_id: int) -> list[str]:
    return _focus_workspace_dispatch(require_workspace(workspace_id))


def dispatch_focus_workspace_argv(workspace_id: object) -> list[str]:
    return _focus_workspace_dispatch(parse_workspace(workspace_id, public=False))


def focus_workspace_fallback_argv(workspace_id: object) -> list[str]:
    number = parse_workspace(workspace_id, public=False)
    return [HYPRCTL, "dispatch", "workspace", str(number)]


def focus_output_argv(name: str) -> list[str]:
    output = require_output(name)
    return [HYPRCTL, "dispatch", f'hl.dsp.focus({{ monitor = "{output}" }})']


def require_app_name(name: object) -> str:
    if not isinstance(name, str) or not APP_NAME_RE.fullmatch(name):
        raise CompositorCommandError("app")
    return name


def require_address(address: object) -> str:
    match = ADDRESS_RE.fullmatch(address) if isinstance(address, str) else None
    if not match:
        raise CompositorCommandError("address")
    return "0x" + match.group(1).lower()


def focus_window_argv(address: object) -> list[str]:
    return [HYPRCTL, "dispatch", f'hl.dsp.focus({{ window = "address:{require_address(address)}" }})']


def focus_output_fallback_argv(name: str) -> list[str]:
    return [HYPRCTL, "dispatch", "focusmonitor", require_output(name)]


def move_window_argv(workspace_id: object, follow: bool) -> list[str]:
    number = parse_workspace(workspace_id, public=False)
    if not isinstance(follow, bool):
        raise CompositorCommandError("follow")
    word = "true" if follow else "false"
    return [
        HYPRCTL,
        "dispatch",
        f'hl.dsp.window.move({{ workspace = "{number}", follow = {word} }})',
    ]


def move_window_fallback_argv(workspace_id: object, follow: bool) -> list[str]:
    number = parse_workspace(workspace_id, public=False)
    if not isinstance(follow, bool):
        raise CompositorCommandError("follow")
    subcommand = "movetoworkspace" if follow else "movetoworkspacesilent"
    return [HYPRCTL, "dispatch", subcommand, str(number)]


def move_workspace_argv(name: str) -> list[str]:
    output = require_output(name)
    return [HYPRCTL, "dispatch", f'hl.dsp.workspace.move({{ monitor = "{output}" }})']


def move_workspace_fallback_argv(workspace_id: object, name: str) -> list[str]:
    number = parse_workspace(workspace_id, public=False)
    output = require_output(name)
    return [HYPRCTL, "dispatch", "moveworkspacetomonitor", str(number), output]


def _dpms_word(on: object) -> str:
    if on is True or on == "on":
        return "on"
    if on is False or on == "off":
        return "off"
    raise CompositorCommandError("dpms")


def set_dpms_argv(name: str, on: object) -> list[str]:
    output = require_output(name)
    action = _dpms_word(on)
    return [
        HYPRCTL,
        "dispatch",
        f'hl.dsp.dpms({{ action = "{action}", monitor = "{output}" }})',
    ]


def set_dpms_fallback_argv(name: str, on: object) -> list[str]:
    output = require_output(name)
    action = _dpms_word(on)
    return [HYPRCTL, "dispatch", "dpms", action, output]


def format_scale(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise CompositorCommandError("scale")
    if isinstance(value, str):
        if not re.fullmatch(r"\d+(?:\.\d+)?", value):
            raise CompositorCommandError("scale")
        number = float(value)
    else:
        number = float(value)
    if number != number or number < 0.1 or number > 10:
        raise CompositorCommandError("scale")
    text = f"{number:.3f}".rstrip("0").rstrip(".")
    if text in ("", "-0"):
        raise CompositorCommandError("scale")
    return text


def require_mode(mode: object) -> str:
    if not isinstance(mode, str) or not MODE_RE.fullmatch(mode):
        raise CompositorCommandError("mode")
    return mode


def require_position(position: object) -> str:
    if not isinstance(position, str) or not POSITION_RE.fullmatch(position):
        raise CompositorCommandError("position")
    return position


def require_transform(value: object) -> int:
    if isinstance(value, bool):
        raise CompositorCommandError("transform")
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if not isinstance(value, int) or value < 0 or value > 7:
        raise CompositorCommandError("transform")
    return value


def monitor_rule_text(
    output: str,
    *,
    disabled: bool,
    mode: object = None,
    position: object = None,
    scale: object = None,
    transform: object = None,
) -> str:
    name = require_output(output)
    if not isinstance(disabled, bool):
        raise CompositorCommandError("monitor-rule")
    if disabled:
        return f'hl.monitor({{ output = "{name}", disabled = true }})'
    shown_mode = require_mode(mode)
    shown_position = require_position(position)
    shown_scale = format_scale(scale)
    if transform is None:
        return (
            f'hl.monitor({{ output = "{name}", mode = "{shown_mode}", '
            f'position = "{shown_position}", scale = {shown_scale} }})'
        )
    shown_transform = require_transform(transform)
    return (
        f'hl.monitor({{ output = "{name}", mode = "{shown_mode}", '
        f'position = "{shown_position}", scale = {shown_scale}, '
        f"transform = {shown_transform}, disabled = false }})"
    )


def monitor_rule_argv(
    output: str,
    *,
    disabled: bool,
    mode: object = None,
    position: object = None,
    scale: object = None,
    transform: object = None,
) -> list[str]:
    return [
        HYPRCTL,
        "eval",
        monitor_rule_text(
            output,
            disabled=disabled,
            mode=mode,
            position=position,
            scale=scale,
            transform=transform,
        ),
    ]


def _dispatch_expression(argv: list[str]) -> str:
    if len(argv) != 3 or argv[0] != HYPRCTL or argv[1] != "dispatch":
        raise CompositorCommandError("batch")
    return argv[2]


def batch_argv(steps: object) -> list[str]:
    if not isinstance(steps, list) or not steps or len(steps) > BATCH_LIMIT:
        raise CompositorCommandError("batch")
    parts: list[str] = []
    for step in steps:
        if not isinstance(step, tuple) or len(step) != 2:
            raise CompositorCommandError("batch")
        kind, value = step
        if kind == "focus-workspace":
            expression = _dispatch_expression(dispatch_focus_workspace_argv(value))
        elif kind == "focus-output":
            expression = _dispatch_expression(focus_output_argv(value))
        elif kind == "move-workspace":
            expression = _dispatch_expression(move_workspace_argv(value))
        else:
            raise CompositorCommandError("batch")
        parts.append("dispatch " + expression)
    return [HYPRCTL, "--batch", "; ".join(parts)]


def active_keymap(payload: object) -> str:
    """Main keyboard layout name from `hyprctl -j devices`, or empty."""
    if isinstance(payload, str):
        if len(payload) > DEVICES_LIMIT:
            return ""
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return ""
    if not isinstance(payload, dict):
        return ""
    boards = payload.get("keyboards")
    if not isinstance(boards, list):
        return ""
    fallback = ""
    for board in boards:
        if not isinstance(board, dict):
            continue
        name = board.get("active_keymap")
        if not isinstance(name, str) or name == "" or "\n" in name or "\r" in name:
            continue
        if len(name) > KEYMAP_LIMIT:
            name = name[:KEYMAP_LIMIT]
        if board.get("main") is True:
            return name
        if fallback == "":
            fallback = name
    return fallback


KEYBOARD_LIMIT = 16


def keyboards_from(payload: object) -> list[dict]:
    """Keyboards from `hyprctl -j devices`, bounded, with the fields the
    layout widget reads. HyprlandAdapter.keyboardsFrom mirrors it."""
    if isinstance(payload, str):
        if len(payload) > DEVICES_LIMIT:
            return []
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return []
    if not isinstance(payload, dict) or not isinstance(payload.get("keyboards"), list):
        return []
    found = []
    for board in payload["keyboards"]:
        if len(found) >= KEYBOARD_LIMIT:
            break
        if not isinstance(board, dict):
            continue
        name = board.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            continue
        keymap = board.get("active_keymap")
        keymap = keymap if isinstance(keymap, str) and "\n" not in keymap and "\r" not in keymap else ""
        layout = board.get("layout")
        index = board.get("active_layout_index")
        found.append({
            "name": name,
            "layout": None if layout is None else str(layout)[:KEYMAP_LIMIT],
            "activeKeymap": keymap[:KEYMAP_LIMIT],
            "activeLayoutIndex": index if isinstance(index, int) and not isinstance(index, bool) and index >= 0 else 0,
            "main": board.get("main") is True,
        })
    return found


def switch_keyboard_layout_argv(name: str) -> list[str]:
    """Advance one keyboard to its next layout. A hyprctl command, not a
    dispatcher."""
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise CompositorCommandError("keyboard")
    return [HYPRCTL, "switchxkblayout", name, "next"]


def bounded_description(text: object) -> str:
    """Monitor description with newlines flattened and a fixed cap."""
    if not isinstance(text, str):
        return ""
    flat = text.replace("\r", " ").replace("\n", " ")
    if len(flat) > DESCRIPTION_LIMIT:
        return flat[:DESCRIPTION_LIMIT]
    return flat


def snapshot_from_monitors(data: object) -> dict:
    """Names, focused output, and active workspace ids from `hyprctl -j monitors`."""
    if not isinstance(data, list):
        raise CompositorCommandError("monitors")
    names: list[str] = []
    focused = ""
    workspaces: list[int] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            continue
        if name not in names:
            names.append(name)
        if item.get("focused") is True:
            focused = name
        workspace = item.get("activeWorkspace")
        if not isinstance(workspace, dict):
            continue
        workspace_id = workspace.get("id")
        if isinstance(workspace_id, bool) or not isinstance(workspace_id, int):
            continue
        if workspace_id > 0 and workspace_id not in workspaces:
            workspaces.append(workspace_id)
    names.sort()
    workspaces.sort()
    return {"names": names, "focused": focused, "workspaces": workspaces}
