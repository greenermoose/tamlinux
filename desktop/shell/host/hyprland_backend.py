"""Run one named Hyprland operation. This is the only Python that starts hyprctl.

Reads always run. Mutations record and return success unless
TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1. There is no generic argument list.
"""

from __future__ import annotations

import os
import subprocess
import sys

import compositor_commands as commands

READS = frozenset({
    "binds",
    "devices",
    "monitors",
    "monitors-all",
    "active-workspace",
    "config-errors",
    "rollinglog",
})
MUTATIONS = frozenset({
    "focus-workspace",
    "focus-workspace-fallback",
    "focus-output",
    "focus-output-fallback",
    "move-window",
    "move-window-fallback",
    "move-workspace",
    "move-workspace-fallback",
    "dpms",
    "dpms-fallback",
    "batch",
    "monitor-rule",
    "reload",
})
DEADLINES = {
    "monitors-all": 4.0,
    "batch": 5.0,
    "monitor-rule": 5.0,
    "config-errors": 5.0,
    "rollinglog": 4.0,
    "reload": 8.0,
}


def live_actions() -> bool:
    return os.environ.get("TAMLINUX_COMPOSITOR_LIVE_ACTIONS") == "1"


def closed_env() -> dict[str, str]:
    env = {"PATH": "/usr/bin"}
    for key in ("XDG_RUNTIME_DIR", "HYPRLAND_INSTANCE_SIGNATURE"):
        value = os.environ.get(key, "")
        if value:
            env[key] = value
    return env


def _pair(payload: object) -> tuple[object, object]:
    if not isinstance(payload, (list, tuple)) or len(payload) != 2:
        raise commands.CompositorCommandError("arguments")
    return payload[0], payload[1]


def _follow(value: object) -> bool:
    if value is True or value == "follow":
        return True
    if value is False or value == "stay":
        return False
    raise commands.CompositorCommandError("follow")


def argv_for(operation: str, payload: object) -> list[str]:
    if operation == "binds":
        return commands.binds_argv()
    if operation == "devices":
        return commands.devices_argv()
    if operation == "monitors":
        return commands.monitors_argv()
    if operation == "monitors-all":
        return commands.monitors_all_argv()
    if operation == "active-workspace":
        return commands.active_workspace_argv()
    if operation == "config-errors":
        return commands.config_errors_argv()
    if operation == "rollinglog":
        return commands.rollinglog_argv()
    if operation == "reload":
        return commands.reload_argv()
    if operation == "focus-workspace":
        return commands.dispatch_focus_workspace_argv(payload)
    if operation == "focus-workspace-fallback":
        return commands.focus_workspace_fallback_argv(payload)
    if operation == "focus-output":
        return commands.focus_output_argv(str(payload))
    if operation == "focus-output-fallback":
        return commands.focus_output_fallback_argv(str(payload))
    if operation == "move-window":
        workspace, follow = _pair(payload)
        return commands.move_window_argv(workspace, _follow(follow))
    if operation == "move-window-fallback":
        workspace, follow = _pair(payload)
        return commands.move_window_fallback_argv(workspace, _follow(follow))
    if operation == "move-workspace":
        return commands.move_workspace_argv(str(payload))
    if operation == "move-workspace-fallback":
        workspace, output = _pair(payload)
        return commands.move_workspace_fallback_argv(workspace, str(output))
    if operation == "dpms":
        output, on = _pair(payload)
        return commands.set_dpms_argv(str(output), on)
    if operation == "dpms-fallback":
        output, on = _pair(payload)
        return commands.set_dpms_fallback_argv(str(output), on)
    if operation == "batch":
        return commands.batch_argv(payload)
    if operation == "monitor-rule":
        return _monitor_rule_argv(payload)
    raise commands.CompositorCommandError("operation")


def _monitor_rule_argv(payload: object) -> list[str]:
    if not isinstance(payload, (list, tuple)) or not payload:
        raise commands.CompositorCommandError("monitor-rule")
    if len(payload) == 2 and payload[1] == "disabled":
        return commands.monitor_rule_argv(str(payload[0]), disabled=True)
    if len(payload) == 4:
        return commands.monitor_rule_argv(
            str(payload[0]),
            disabled=False,
            mode=payload[1],
            position=payload[2],
            scale=payload[3],
        )
    if len(payload) == 5:
        return commands.monitor_rule_argv(
            str(payload[0]),
            disabled=False,
            mode=payload[1],
            position=payload[2],
            scale=payload[3],
            transform=payload[4],
        )
    raise commands.CompositorCommandError("monitor-rule")


def run(operation: str, payload: object = None) -> subprocess.CompletedProcess[str]:
    if operation not in READS and operation not in MUTATIONS:
        raise commands.CompositorCommandError("operation")
    argv = argv_for(operation, payload)
    if operation in MUTATIONS and not live_actions():
        return subprocess.CompletedProcess(argv, 0, "recorded\n", "")
    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        env=closed_env(),
        timeout=DEADLINES.get(operation, 2.0),
        check=False,
    )
    if len(result.stdout) > commands.MONITORS_LIMIT or len(result.stderr) > commands.MONITORS_LIMIT:
        return subprocess.CompletedProcess(argv, 1, "", "capped\n")
    return result


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write("compositor operation required\n")
        return 2
    operation = argv[1]
    try:
        if operation in ("focus-workspace", "focus-workspace-fallback", "focus-output", "focus-output-fallback", "move-workspace", "reload", "binds", "devices", "monitors", "monitors-all", "active-workspace", "config-errors", "rollinglog"):
            payload: object = argv[2] if len(argv) > 2 else None
            if operation in READS or operation == "reload":
                payload = None
        elif operation in ("dpms", "dpms-fallback", "move-window", "move-window-fallback", "move-workspace-fallback", "monitor-rule"):
            payload = argv[2:]
        else:
            raise commands.CompositorCommandError("operation")
        result = run(operation, payload)
    except commands.CompositorCommandError:
        sys.stderr.write("rejected\n")
        return 2
    except subprocess.TimeoutExpired:
        sys.stderr.write("deadline\n")
        return 1
    sys.stdout.write(result.stdout or "")
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
