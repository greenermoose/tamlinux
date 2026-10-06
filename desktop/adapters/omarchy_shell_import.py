#!/usr/bin/env python3
"""Convert the Omarchy shell's shell.json into the Tamlinux shell's two files.

    omarchy_shell_import.py <shell.json> <output-dir>

writes <output-dir>/layout.json (the bar layout, position, and transparency)
and <output-dir>/settings.json (each widget's settings), and prints what it
left out. It runs once, when the Tamlinux bar takes over (plan 18 step 0.3.2
item 6); after that the Tamlinux shell owns both files. Existing files are
not overwritten.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HOST = Path(__file__).resolve().parents[1] / "shell" / "host"
sys.path.insert(0, str(HOST))

from settings_store import SettingsError, validate_document  # noqa: E402

# The Omarchy shell's own widgets and the Tamlinux widget that replaces each.
WIDGETS = {
    "omarchy.menu": "tamlinux.menu",
    "omarchy.indicators": "tamlinux.indicators",
    "omarchy.keyboard-layout": "tamlinux.keyboard-layout",
    "omarchy.tray": "tamlinux.tray",
    "omarchy.audio": "tamlinux.audio",
    "omarchy.bluetooth": "tamlinux.bluetooth",
    "omarchy.network": "tamlinux.network",
    "omarchy.power": "tamlinux.power",
}
SECTIONS = ("left", "center", "right")


class ConversionError(Exception):
    """The input is not an Omarchy shell.json this converter understands."""


def widget_id(omarchy_id: object) -> str | None:
    """The Tamlinux id for one layout entry, or None when there is none."""
    if not isinstance(omarchy_id, str):
        return None
    if omarchy_id in WIDGETS:
        return WIDGETS[omarchy_id]
    if omarchy_id.startswith("fred.") and len(omarchy_id) > 5:
        return omarchy_id
    return None


def convert(document: object) -> tuple[dict, dict, list[str]]:
    """(layout document, settings document, notes) for one shell.json."""
    if not isinstance(document, dict) or not isinstance(document.get("bar"), dict):
        raise ConversionError("shell.json has no bar section")
    bar = document["bar"]
    layout_in = bar.get("layout")
    if not isinstance(layout_in, dict):
        raise ConversionError("shell.json has no bar layout")
    notes: list[str] = []
    layout: dict[str, list] = {}
    entries: dict[str, dict] = {}
    placed: set[str] = set()
    for section in SECTIONS:
        items = layout_in.get(section, [])
        layout[section] = []
        if not isinstance(items, list):
            notes.append(f"{section}: not a list, left empty")
            continue
        for item in items:
            source = item.get("id") if isinstance(item, dict) else None
            target = widget_id(source)
            if target is None:
                notes.append(f"{section}: {source!r} has no Tamlinux widget, left out")
                continue
            if target in placed:
                notes.append(f"{section}: {target} appears twice, second left out")
                continue
            placed.add(target)
            layout[section].append({"id": target})
            settings = {"id": target}
            for key, value in item.items():
                if key == "id":
                    continue
                if type(value) in (str, int, float, bool):
                    settings[key] = value
                else:
                    notes.append(f"{target}: setting {key} is not a plain value, left out")
            if len(settings) > 1:
                entries[target] = settings
    anchor = widget_id(bar.get("centerAnchor")) or ""
    position = bar.get("position", "top")
    if position not in ("top", "bottom"):
        notes.append(f"position {position!r} is not top or bottom, read as top")
        position = "top"
    layout_doc = {
        "centerAnchor": anchor,
        "layout": layout,
        "position": position,
        "transparent": bar.get("transparent") is True,
    }
    try:
        settings_doc = validate_document({"version": 1, "entries": entries}, placed)
    except SettingsError as exc:
        raise ConversionError(f"settings would be refused: {exc}") from exc
    return layout_doc, settings_doc, notes


def write_new(path: Path, document: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(document, indent=2) + "\n")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: omarchy_shell_import.py <shell.json> <output-dir>", file=sys.stderr)
        return 2
    source, output = Path(argv[1]), Path(argv[2])
    try:
        layout_doc, settings_doc, notes = convert(json.loads(source.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ConversionError) as exc:
        print(f"omarchy_shell_import: {exc}", file=sys.stderr)
        return 1
    targets = (output / "layout.json", output / "settings.json")
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        print(f"omarchy_shell_import: will not overwrite {', '.join(existing)}", file=sys.stderr)
        return 1
    output.mkdir(parents=True, exist_ok=True)
    write_new(targets[0], layout_doc)
    write_new(targets[1], settings_doc)
    for note in notes:
        print(f"omarchy_shell_import: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
