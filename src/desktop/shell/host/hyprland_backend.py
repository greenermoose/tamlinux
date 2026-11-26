"""Run one named compositor operation (Hyprland via hyprctl, or tam-pane via IPC).

Reads always run. Mutations record and return success unless
TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1. There is no generic argument list.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys

import compositor_commands as commands

READS = frozenset({
    "binds",
    "devices",
    "monitors",
    "monitors-all",
    "workspaces",
    "active-workspace",
    "config-errors",
    "rollinglog",
})
MUTATIONS = frozenset({
    "select-output-workspace",
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
    if operation == "workspaces":
        return commands.workspaces_argv()
    if operation == "active-workspace":
        return commands.active_workspace_argv()
    if operation == "config-errors":
        return commands.config_errors_argv()
    if operation == "rollinglog":
        return commands.rollinglog_argv()
    if operation == "reload":
        return commands.reload_argv()
    if operation == "select-output-workspace":
        workspace, output = _pair(payload)
        return commands.select_output_workspace_argv(workspace, output)
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


def tam_pane_socket() -> str:
    """Return $TAM_PANE_SOCKET when running under tam-pane (no Hyprland session)."""
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return ""
    return os.environ.get("TAM_PANE_SOCKET", "")


def _unescape_tsv(raw: str) -> str:
    out: list[str] = []
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == "\\" and i + 1 < n:
            nxt = raw[i + 1]
            if nxt == "\\":
                out.append("\\")
                i += 2
                continue
            if nxt == "t":
                out.append("\t")
                i += 2
                continue
            if nxt == "n":
                out.append("\n")
                i += 2
                continue
            if nxt == "r":
                out.append("\r")
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _parse_tsv_line(line: str) -> tuple[str, dict[str, str]] | None:
    parts = line.split("\t")
    if not parts or not parts[0]:
        return None
    fields: dict[str, str] = {}
    for item in parts[1:]:
        if "=" not in item:
            continue
        key, _, val = item.partition("=")
        if key:
            fields[key] = _unescape_tsv(val)
    return parts[0], fields


def _mask_to_tags(mask: int) -> list[int]:
    if mask <= 0:
        return []
    return [t for t in range(1, 10) if mask & (1 << (t - 1))]


def _modmask_from_names(mods_text: str) -> int:
    if not mods_text or mods_text == "none":
        return 0
    mask = 0
    for part in mods_text.split("+"):
        m = part.strip().lower()
        if m == "shift":
            mask |= 1
        elif m in ("ctrl", "control"):
            mask |= 4
        elif m in ("alt", "mod1"):
            mask |= 8
        elif m in ("meta", "super", "mod4"):
            mask |= 64
    return mask


def _tam_pane_rpc(sock_path: str, command: str, timeout: float) -> tuple[int, list[str], str]:
    """Send one command line to tam-pane IPC socket and collect response lines."""
    data = bytearray()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(timeout)
        conn.connect(sock_path)
        conn.sendall((command + "\n").encode("utf-8"))
        while len(data) <= commands.MONITORS_LIMIT:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data.extend(chunk)
            text = data.decode("utf-8", errors="replace")
            lines = text.splitlines()
            if lines and (lines[-1] == "END" or lines[0].startswith("ERR")):
                if lines[0].startswith("ERR"):
                    return 1, [], lines[0] + "\n"
                body = [ln for ln in lines[1:] if ln != "END"]
                return 0, body, ""
    if len(data) > commands.MONITORS_LIMIT:
        return 1, [], "capped\n"
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if lines and lines[0] == "OK":
        return 0, [ln for ln in lines[1:] if ln != "END"], ""
    return 1, [], (text.strip() or "tam-pane ipc failed") + "\n"


def _tam_pane_monitors_json(lines: list[str]) -> str:
    monitors: list[dict[str, object]] = []
    for idx, line in enumerate(lines):
        parsed = _parse_tsv_line(line)
        if not parsed or parsed[0] != "monitor":
            continue
        f = parsed[1]
        name = f.get("name", "")
        if not commands.NAME_RE.fullmatch(name):
            continue
        mask = int(f.get("tags", "0") or 0)
        tag_ids = _mask_to_tags(mask)
        active_id = tag_ids[0] if tag_ids else 1
        try:
            scale = float(f.get("scale", "1.0") or 1.0)
        except ValueError:
            scale = 1.0
        try:
            refresh_raw = float(f.get("refresh", "60") or 60.0)
        except ValueError:
            refresh_raw = 60.0
        if refresh_raw <= 0.0:
            refresh = 60.0
        elif refresh_raw > 1000.0:
            refresh = round(refresh_raw / 1000.0, 3)
        else:
            refresh = refresh_raw
        width = int(f.get("phys_w") or f.get("w") or 1920)
        height = int(f.get("phys_h") or f.get("h") or 1080)
        monitors.append({
            "id": idx,
            "name": name,
            "description": commands.bounded_description(f.get("description", "")),
            "width": width,
            "height": height,
            "refreshRate": refresh,
            "x": int(f.get("x", "0") or 0),
            "y": int(f.get("y", "0") or 0),
            "scale": scale,
            "transform": int(f.get("transform", "0") or 0),
            "focused": f.get("focused") == "1",
            "dpmsStatus": f.get("dpms") != "0",
            "disabled": False,
            "activeWorkspace": {"id": active_id, "name": str(active_id)},
        })
    return json.dumps(monitors)


def _tam_pane_workspaces_json(lines: list[str], active_only: bool) -> str:
    workspaces: list[dict[str, object]] = []
    active: dict[str, object] = {"id": 1, "name": "1", "monitor": ""}
    for line in lines:
        parsed = _parse_tsv_line(line)
        if not parsed or parsed[0] != "tag":
            continue
        f = parsed[1]
        mon = f.get("monitor", "")
        view_mask = int(f.get("view", "0") or 0)
        occ_mask = int(f.get("occupied", "0") or 0)
        view_tags = _mask_to_tags(view_mask)
        if f.get("focused") == "1" and view_tags:
            active = {"id": view_tags[0], "name": str(view_tags[0]), "monitor": mon}
        combined = sorted(set(view_tags) | set(_mask_to_tags(occ_mask)))
        for tid in combined:
            workspaces.append({
                "id": tid,
                "name": str(tid),
                "monitor": mon,
                "windows": 1 if (occ_mask & (1 << (tid - 1))) else 0,
            })
    return json.dumps(active if active_only else workspaces)


def _tam_pane_devices_json(lines: list[str]) -> str:
    boards: list[dict[str, object]] = []
    for line in lines:
        parsed = _parse_tsv_line(line)
        if not parsed or parsed[0] != "keyboard":
            continue
        f = parsed[1]
        name = f.get("name", "")
        if not commands.NAME_RE.fullmatch(name):
            continue
        boards.append({
            "name": name,
            "layout": f.get("layout", ""),
            "active_keymap": f.get("active_keymap", ""),
            "active_layout_index": int(f.get("active_layout_index", "0") or 0),
            "main": f.get("main") == "1",
        })
    return json.dumps({"keyboards": boards})


def _tam_pane_binds_json(lines: list[str]) -> str:
    out: list[dict[str, object]] = []
    for line in lines:
        parsed = _parse_tsv_line(line)
        if not parsed or parsed[0] != "bind":
            continue
        f = parsed[1]
        key = f.get("key", "").strip()
        if not key:
            continue
        action = f.get("action", "").strip()
        dispatcher, _, arg = action.partition(" ")
        out.append({
            "modmask": _modmask_from_names(f.get("mods", "")),
            "key": key,
            "description": action,
            "dispatcher": dispatcher,
            "arg": arg.strip(),
        })
    return json.dumps(out)


def _tam_pane_commands(operation: str, payload: object) -> list[str]:
    if operation == "reload":
        return ["reload"]
    if operation == "select-output-workspace":
        workspace, output = _pair(payload)
        return [f"dispatch tag view {commands.parse_workspace(workspace, public=False)} {commands.require_output(str(output))}"]
    if operation in ("focus-workspace", "focus-workspace-fallback"):
        return [f"dispatch tag view {commands.parse_workspace(payload, public=False)}"]
    if operation in ("focus-output", "focus-output-fallback"):
        return [f"dispatch monitor focus {commands.require_output(str(payload))}"]
    if operation in ("move-window", "move-window-fallback"):
        workspace, follow = _pair(payload)
        ws = commands.parse_workspace(workspace, public=False)
        cmds = [f"dispatch window move_tag {ws}"]
        if _follow(follow):
            cmds.append(f"dispatch tag view {ws}")
        return cmds
    if operation == "move-workspace":
        return [f"dispatch monitor focus {commands.require_output(str(payload))}"]
    if operation == "move-workspace-fallback":
        workspace, output = _pair(payload)
        return [f"dispatch tag view {commands.parse_workspace(workspace, public=False)} {commands.require_output(str(output))}"]
    if operation in ("dpms", "dpms-fallback"):
        output, on = _pair(payload)
        action = "on" if (on is True or on == "on") else "off"
        return [f"dispatch dpms {action} {commands.require_output(str(output))}"]
    if operation == "monitor-rule":
        # Live monitor updates on tam-pane are persisted to tam-pane/monitors.lua and applied via reload.
        return []
    if operation == "batch":
        cmds: list[str] = []
        assert isinstance(payload, list)
        for kind, value in payload:
            if kind == "select-output-workspace":
                cmds.append(f"dispatch tag view {commands.parse_workspace(value[0], public=False)} {commands.require_output(str(value[1]))}")
            elif kind == "focus-workspace":
                cmds.append(f"dispatch tag view {commands.parse_workspace(value, public=False)}")
            elif kind == "focus-output":
                cmds.append(f"dispatch monitor focus {commands.require_output(str(value))}")
            elif kind == "move-workspace":
                cmds.append(f"dispatch monitor focus {commands.require_output(str(value))}")
            elif kind == "move-workspace-to":
                cmds.append(f"dispatch tag view {commands.parse_workspace(value[0], public=False)} {commands.require_output(str(value[1]))}")
        return cmds
    raise commands.CompositorCommandError("operation")


def _run_tam_pane(sock_path: str, operation: str, payload: object, deadline: float) -> subprocess.CompletedProcess[str]:
    argv = ["tam-pane", "msg", operation]
    try:
        if operation in ("monitors", "monitors-all"):
            rc, lines, err = _tam_pane_rpc(sock_path, "monitors", deadline)
            return subprocess.CompletedProcess(argv, rc, _tam_pane_monitors_json(lines) + "\n" if rc == 0 else "", err)
        if operation == "workspaces":
            rc, lines, err = _tam_pane_rpc(sock_path, "tags", deadline)
            return subprocess.CompletedProcess(argv, rc, _tam_pane_workspaces_json(lines, active_only=False) + "\n" if rc == 0 else "", err)
        if operation == "active-workspace":
            rc, lines, err = _tam_pane_rpc(sock_path, "tags", deadline)
            return subprocess.CompletedProcess(argv, rc, _tam_pane_workspaces_json(lines, active_only=True) + "\n" if rc == 0 else "", err)
        if operation == "devices":
            rc, lines, err = _tam_pane_rpc(sock_path, "keyboards", deadline)
            return subprocess.CompletedProcess(argv, rc, _tam_pane_devices_json(lines) + "\n" if rc == 0 else "", err)
        if operation == "binds":
            rc, lines, err = _tam_pane_rpc(sock_path, "binds", deadline)
            return subprocess.CompletedProcess(argv, rc, _tam_pane_binds_json(lines) + "\n" if rc == 0 else "", err)
        if operation in ("config-errors", "rollinglog"):
            return subprocess.CompletedProcess(argv, 0, "", "")
        for cmd in _tam_pane_commands(operation, payload):
            rc, _, err = _tam_pane_rpc(sock_path, cmd, deadline)
            if rc != 0:
                return subprocess.CompletedProcess(argv, rc, "", err)
        return subprocess.CompletedProcess(argv, 0, "ok\n", "")
    except TimeoutError as exc:
        raise subprocess.TimeoutExpired(argv, deadline) from exc
    except OSError as exc:
        return subprocess.CompletedProcess(argv, 1, "", f"{exc}\n")


def run(operation: str, payload: object = None, *, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    if operation not in READS and operation not in MUTATIONS:
        raise commands.CompositorCommandError("operation")
    argv = argv_for(operation, payload)
    if operation in MUTATIONS and not live_actions():
        return subprocess.CompletedProcess(argv, 0, "recorded\n", "")
    deadline = min(DEADLINES.get(operation, 2.0), timeout) if timeout is not None else DEADLINES.get(operation, 2.0)
    sock = tam_pane_socket()
    if sock:
        return _run_tam_pane(sock, operation, payload, deadline)
    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        env=closed_env(),
        timeout=deadline,
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
        if operation in ("focus-workspace", "focus-workspace-fallback", "focus-output", "focus-output-fallback", "move-workspace", "reload", "binds", "devices", "monitors", "monitors-all", "workspaces", "active-workspace", "config-errors", "rollinglog"):
            payload: object = argv[2] if len(argv) > 2 else None
            if operation in READS or operation == "reload":
                payload = None
        elif operation in ("select-output-workspace", "dpms", "dpms-fallback", "move-window", "move-window-fallback", "move-workspace-fallback", "monitor-rule"):
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
