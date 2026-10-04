"""Argv and i3 request strings for the Sway adapter. This module does not run commands."""

from __future__ import annotations

from compositor_commands import CompositorCommandError, require_app_name, require_output, require_workspace

SWAYMSG = "/usr/bin/swaymsg"


def inputs_argv() -> list[str]:
    return [SWAYMSG, "-t", "get_inputs", "-r"]


def outputs_argv() -> list[str]:
    return [SWAYMSG, "-t", "get_outputs", "-r"]


def workspaces_argv() -> list[str]:
    return [SWAYMSG, "-t", "get_workspaces", "-r"]


def focus_workspace_request(workspace_id: int) -> str:
    return f"workspace number {require_workspace(workspace_id)}"


def focus_workspace_argv(workspace_id: int) -> list[str]:
    number = require_workspace(workspace_id)
    return [SWAYMSG, "workspace", "number", str(number)]


def focus_output_request(name: str) -> str:
    return f"focus output {require_output(name)}"


def focus_output_argv(name: str) -> list[str]:
    output = require_output(name)
    return [SWAYMSG, "focus", "output", output]


def focus_app_request(name: object) -> str:
    app = require_app_name(name)
    pattern = "".join(f"[{c}]" if c in ".+" else c for c in app)
    return f'[app_id="(?i){pattern}"] focus'


def _power_word(on: object) -> str:
    if on is True or on == "on":
        return "on"
    if on is False or on == "off":
        return "off"
    raise CompositorCommandError("dpms")


def set_dpms_request(name: str, on: object) -> str:
    output = require_output(name)
    return f"output {output} power {_power_word(on)}"


def set_dpms_argv(name: str, on: object) -> list[str]:
    output = require_output(name)
    return [SWAYMSG, "output", output, "power", _power_word(on)]
