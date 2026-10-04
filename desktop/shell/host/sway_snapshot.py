"""Turn Sway fixtures into the compositor snapshot. This module does not run commands."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compositor_commands as commands  # noqa: E402

BINDS_LIMIT = commands.BINDS_LIMIT
DEVICES_LIMIT = commands.DEVICES_LIMIT
MONITORS_LIMIT = commands.MONITORS_LIMIT
KEYMAP_LIMIT = commands.KEYMAP_LIMIT
DESCRIPTION_LIMIT = commands.DESCRIPTION_LIMIT
WINDOW_LIMIT = commands.WINDOW_LIMIT
TITLE_LIMIT = commands.TITLE_LIMIT
CLASS_LIMIT = commands.CLASS_LIMIT
WORKSPACE_LIST_LIMIT = commands.WORKSPACE_LIST_LIMIT
POSITION_LIMIT = 100000

MODS = {
    "Shift": 1,
    "Caps": 2,
    "Ctrl": 4,
    "Control": 4,
    "Alt": 8,
    "Mod1": 8,
    "Mod2": 16,
    "Mod3": 32,
    "Mod4": 64,
    "Super": 64,
    "Mod5": 128,
}
BIND_LINE = re.compile(
    r"^bindsym\s+(?:--(?:locked|no-repeat|release|whole-window|border)\s+)*(\S+)\s+(\S.*)$"
)
WORKSPACE_COMMAND = re.compile(r"^workspace number ([1-9]|10)$")
OUTPUT_COMMAND = re.compile(r"^focus output ([A-Za-z0-9._-]{1,64})$")
FIXTURE_FILES = (
    "ext-workspace.json",
    "outputs.json",
    "workspaces.json",
    "inputs.json",
    "bindings.conf",
)


def require_directory(value: str) -> Path:
    if not isinstance(value, str) or value == "" or "\x00" in value:
        raise commands.CompositorCommandError("fixture")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise commands.CompositorCommandError("fixture")
    root = path.resolve()
    if not root.is_dir():
        raise commands.CompositorCommandError("fixture")
    return root


def _read_named(root: Path, name: str, limit: int) -> str:
    path = root / name
    if not path.is_file() or path.is_symlink():
        return ""
    resolved = path.resolve()
    if resolved.parent != root:
        raise commands.CompositorCommandError("fixture")
    text = resolved.read_text(encoding="utf-8")
    if len(text) > limit:
        return ""
    return text


def _loads(text: str, limit: int) -> object:
    if text == "" or len(text) > limit:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _workspace_number(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.isdigit():
        number = int(value)
    else:
        return 0
    try:
        return commands.require_workspace(number)
    except commands.CompositorCommandError:
        return 0


def _output_name(value: object) -> str:
    if not isinstance(value, str):
        return ""
    try:
        return commands.require_output(value)
    except commands.CompositorCommandError:
        return ""


def _position(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    if isinstance(value, float) and value != value:
        return 0
    number = int(round(float(value)))
    if number > POSITION_LIMIT:
        return POSITION_LIMIT
    if number < -POSITION_LIMIT:
        return -POSITION_LIMIT
    return number


def _window(item: object) -> dict | None:
    if not isinstance(item, dict):
        return None
    raw_class = item.get("className", item.get("app_id", item.get("class", "")))
    raw_title = item.get("title", item.get("name", ""))
    if not isinstance(raw_class, str):
        raw_class = ""
    if not isinstance(raw_title, str):
        raw_title = ""
    raw_class = raw_class.replace("\r", " ").replace("\n", " ")
    raw_title = raw_title.replace("\r", " ").replace("\n", " ")
    if raw_class == "" and raw_title == "":
        return None
    if len(raw_class) > CLASS_LIMIT:
        raw_class = raw_class[:CLASS_LIMIT]
    if len(raw_title) > TITLE_LIMIT:
        raw_title = raw_title[: TITLE_LIMIT - 3] + "..."
    return {"className": raw_class, "title": raw_title}


def _windows(item: dict) -> list[dict]:
    raw = item.get("windows", item.get("nodes"))
    if not isinstance(raw, list):
        return []
    found: list[dict] = []
    for entry in raw:
        summary = _window(entry)
        if summary is None:
            continue
        found.append(summary)
        if len(found) >= WINDOW_LIMIT:
            break
    return found


def _description(item: dict) -> str:
    text = item.get("description")
    if not isinstance(text, str) or text == "":
        make = item.get("make") if isinstance(item.get("make"), str) else ""
        model = item.get("model") if isinstance(item.get("model"), str) else ""
        text = f"{make} {model}".strip()
    return commands.bounded_description(text)


def parse_bindings(text: str) -> str:
    """JSON bind array for Bindings.parseBinds. exec, include, and other commands are dropped."""
    if not isinstance(text, str) or text == "":
        return "[]"
    if len(text) > BINDS_LIMIT:
        text = text[:BINDS_LIMIT]
    records: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if "exec" in stripped or "include" in stripped:
            continue
        matched = BIND_LINE.fullmatch(stripped)
        if not matched:
            continue
        combo, command = matched.group(1), matched.group(2).strip()
        parts = combo.split("+")
        key = parts[-1]
        if key == "" or key in MODS or len(key) > 64:
            continue
        mask = 0
        rejected = False
        for modifier in parts[:-1]:
            bit = MODS.get(modifier)
            if bit is None:
                rejected = True
                break
            mask |= bit
        if rejected:
            continue
        workspace = WORKSPACE_COMMAND.fullmatch(command)
        output = OUTPUT_COMMAND.fullmatch(command)
        if workspace:
            dispatcher, arg = "workspace", f"number {workspace.group(1)}"
        elif output:
            dispatcher, arg = "focus", f"output {output.group(1)}"
        else:
            continue
        records.append({
            "modmask": mask,
            "key": key,
            "description": "",
            "dispatcher": dispatcher,
            "arg": arg,
            "submap": "",
        })
        if len(records) >= 4096:
            break
    encoded = json.dumps(records, separators=(",", ":"))
    if len(encoded) > BINDS_LIMIT:
        return encoded[:BINDS_LIMIT]
    return encoded


def active_keymap(payload: object) -> str:
    """Layout name from `swaymsg -t get_inputs`, or empty."""
    if isinstance(payload, str):
        if len(payload) > DEVICES_LIMIT:
            return ""
        payload = _loads(payload, DEVICES_LIMIT)
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        return ""
    for item in payload:
        if not isinstance(item, dict):
            continue
        if item.get("type") not in (None, "keyboard"):
            continue
        name = item.get("xkb_active_layout_name")
        if not isinstance(name, str) or name == "" or "\n" in name or "\r" in name:
            continue
        if len(name) > KEYMAP_LIMIT:
            name = name[:KEYMAP_LIMIT]
        return name
    return ""


def _workspaces_from_ext(payload: object) -> tuple[list[dict], int] | None:
    if isinstance(payload, dict):
        sets = payload.get("windowsets")
    elif isinstance(payload, list):
        sets = payload
    else:
        return None
    if not isinstance(sets, list) or not sets:
        return None
    spaces: list[dict] = []
    focused = 0
    seen: set[int] = set()
    for item in sets:
        if not isinstance(item, dict) or len(spaces) >= WORKSPACE_LIST_LIMIT:
            continue
        number = _workspace_number(item.get("id", item.get("name")))
        if number == 0 or number in seen:
            continue
        seen.add(number)
        windows = _windows(item)
        occupied = item.get("occupied") is True or bool(windows)
        if item.get("active") is True and focused == 0:
            focused = number
        spaces.append({
            "id": number,
            "output": _output_name(item.get("output")),
            "occupied": occupied,
            "windows": windows,
        })
    if not spaces:
        return None
    spaces.sort(key=lambda space: int(space["id"]))
    return spaces, focused


def _workspaces_from_i3(payload: object) -> tuple[list[dict], int]:
    if not isinstance(payload, list):
        return [], 0
    spaces: list[dict] = []
    focused = 0
    seen: set[int] = set()
    for item in payload:
        if not isinstance(item, dict) or len(spaces) >= WORKSPACE_LIST_LIMIT:
            continue
        number = _workspace_number(item.get("num", item.get("id")))
        if number == 0 or number in seen:
            continue
        seen.add(number)
        windows = _windows(item)
        if item.get("focused") is True and focused == 0:
            focused = number
        spaces.append({
            "id": number,
            "output": _output_name(item.get("output")),
            "occupied": bool(windows),
            "windows": windows,
        })
    spaces.sort(key=lambda space: int(space["id"]))
    return spaces, focused


def _outputs(payload: object) -> tuple[list[dict], str]:
    if not isinstance(payload, list):
        return [], ""
    outputs: list[dict] = []
    focused = ""
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = _output_name(item.get("name"))
        if name == "" or name in seen:
            continue
        seen.add(name)
        rect = item.get("rect") if isinstance(item.get("rect"), dict) else {}
        if item.get("focused") is True and focused == "":
            focused = name
        power = item.get("power")
        if power is False:
            dpms_on = False
        else:
            dpms_on = True
        outputs.append({
            "name": name,
            "focused": name == focused,
            "activeWorkspaceId": _workspace_number(item.get("current_workspace")),
            "dpmsOn": dpms_on,
            "description": _description(item),
            "x": _position(rect.get("x", item.get("x"))),
            "y": _position(rect.get("y", item.get("y"))),
            "special": item.get("special") is True,
        })
    outputs.sort(key=lambda output: str(output["name"]))
    for output in outputs:
        output["focused"] = output["name"] == focused
    return outputs, focused


def snapshot_from_parts(
    ext_workspace: object,
    outputs_payload: object,
    workspaces_payload: object,
    inputs_payload: object,
    bindings_text: str,
) -> dict:
    """ext-workspace windowsets win. i3 workspaces are the fallback. Outputs stay i3."""
    chosen = _workspaces_from_ext(ext_workspace)
    if chosen is None:
        workspaces, focused_workspace = _workspaces_from_i3(workspaces_payload)
    else:
        workspaces, focused_workspace = chosen
    outputs, focused_output = _outputs(outputs_payload)
    return {
        "outputs": outputs,
        "focusedOutputName": focused_output,
        "workspaces": workspaces,
        "focusedWorkspaceId": focused_workspace,
        "bindingsText": parse_bindings(bindings_text),
        "activeKeymap": active_keymap(inputs_payload),
    }


def snapshot_from_directory(directory: Path | str) -> dict:
    root = require_directory(str(directory))
    ext_text = _read_named(root, "ext-workspace.json", MONITORS_LIMIT)
    outputs_text = _read_named(root, "outputs.json", MONITORS_LIMIT)
    workspaces_text = _read_named(root, "workspaces.json", MONITORS_LIMIT)
    inputs_text = _read_named(root, "inputs.json", DEVICES_LIMIT)
    bindings_text = _read_named(root, "bindings.conf", BINDS_LIMIT)
    return snapshot_from_parts(
        _loads(ext_text, MONITORS_LIMIT),
        _loads(outputs_text, MONITORS_LIMIT),
        _loads(workspaces_text, MONITORS_LIMIT),
        _loads(inputs_text, DEVICES_LIMIT),
        bindings_text,
    )


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        sys.stderr.write("fixture directory required\n")
        return 2
    try:
        snapshot = snapshot_from_directory(argv[0])
    except commands.CompositorCommandError:
        sys.stderr.write("fixture rejected\n")
        return 2
    sys.stdout.write(json.dumps(snapshot, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
