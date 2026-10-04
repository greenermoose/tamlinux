"""Argv for the Hyprland adapter. This module does not run commands."""

from __future__ import annotations

import json
import re

HYPRCTL = "/usr/bin/hyprctl"
NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
WORKSPACE_MIN = 1
WORKSPACE_MAX = 10
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


def binds_argv() -> list[str]:
    return [HYPRCTL, "binds"]


def devices_argv() -> list[str]:
    return [HYPRCTL, "-j", "devices"]


def monitors_argv() -> list[str]:
    return [HYPRCTL, "-j", "monitors"]


def focus_workspace_argv(workspace_id: int) -> list[str]:
    number = require_workspace(workspace_id)
    return [HYPRCTL, "dispatch", f'hl.dsp.focus({{ workspace = "{number}" }})']


def focus_output_argv(name: str) -> list[str]:
    output = require_output(name)
    return [HYPRCTL, "dispatch", f'hl.dsp.focus({{ monitor = "{output}" }})']


def set_dpms_argv(name: str, on: bool) -> list[str]:
    output = require_output(name)
    if not isinstance(on, bool):
        raise CompositorCommandError("dpms")
    action = "enable" if on else "disable"
    return [
        HYPRCTL,
        "eval",
        f'hl.dispatch(hl.dsp.dpms({{ action = "{action}", monitor = "{output}" }}))',
    ]


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
