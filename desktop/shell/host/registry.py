"""Validate plugin manifests before the shell loads them.

As a command (plan 18 step 0.3.2 items 6 and 10):

    registry.py validate <plugin-dir>   print the load record, or fail
    registry.py entries <plugins-dir>   print {id: entry file} for every
                                        plugin there that validates

`entries` leaves a plugin that fails off the map and names it on stderr;
it never fails the shell for one bad plugin.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


class RegistryError(Exception):
    """A manifest or entry point is not safe to load."""


def _contained_file(root: Path, relative: str) -> Path:
    if not relative or relative.startswith("/") or "\\" in relative:
        raise RegistryError(f"entry point must be a relative path: {relative!r}")
    root = root.resolve()
    current = root
    parts = Path(relative).parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise RegistryError(f"entry point escapes the plugin root: {relative!r}")
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise RegistryError(f"entry point contains a symlink: {relative}")
        if not current.exists():
            raise RegistryError(f"entry point does not exist: {relative}")
    if not current.is_file():
        raise RegistryError(f"entry point is not a file: {relative}")
    resolved = current.resolve()
    if not resolved.is_relative_to(root):
        raise RegistryError(f"entry point resolves outside the plugin root: {relative}")
    return resolved


def validate_manifest(root: Path, manifest: dict, seen_ids: set[str] | None = None) -> dict:
    """Return a load record for one manifest, or raise RegistryError."""
    if not isinstance(manifest, dict):
        raise RegistryError("manifest must be an object")
    if manifest.get("schemaVersion") != 1:
        raise RegistryError("schemaVersion must be 1")
    plugin_id = manifest.get("id")
    if not isinstance(plugin_id, str) or not plugin_id or "/" in plugin_id or plugin_id in (".", ".."):
        raise RegistryError("manifest id is missing or invalid")
    seen = seen_ids if seen_ids is not None else set()
    if plugin_id in seen:
        raise RegistryError(f"duplicate plugin id: {plugin_id}")
    kinds = manifest.get("kinds")
    if not isinstance(kinds, list) or "bar-widget" not in kinds:
        raise RegistryError("manifest must include bar-widget kind")
    points = manifest.get("entryPoints")
    if not isinstance(points, dict):
        raise RegistryError("entryPoints must be an object")
    relative = points.get("barWidget")
    if not isinstance(relative, str):
        raise RegistryError("entryPoints.barWidget must be a string")
    path = _contained_file(Path(root), relative)
    seen.add(plugin_id)
    return {"id": plugin_id, "root": str(Path(root).resolve()), "entry": str(path)}


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"malformed manifest: {path.name}") from exc
    if not isinstance(data, dict):
        raise RegistryError("malformed manifest: not an object")
    return data


def validate_directory(root: Path, seen_ids: set[str] | None = None) -> dict:
    manifest_path = Path(root) / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RegistryError("manifest.json is missing")
    return validate_manifest(Path(root), load_manifest(manifest_path), seen_ids)


def validate_directories(roots: list[Path]) -> list[dict]:
    """Validate plugins in order, rejecting an id that appears twice."""
    seen: set[str] = set()
    return [validate_directory(Path(root), seen) for root in roots]


def plugin_entries(plugins_dir: Path) -> tuple[dict[str, str], list[str]]:
    """Each plugin directory under plugins_dir, by name, that validates and
    whose manifest id is its directory name; and why each other one was left
    out."""
    entries: dict[str, str] = {}
    problems: list[str] = []
    seen: set[str] = set()
    base = Path(plugins_dir)
    if not base.is_dir():
        return entries, [f"{base}: not a directory"]
    for child in sorted(base.iterdir()):
        if child.name.startswith(".") or not child.is_dir():
            continue
        try:
            record = validate_directory(child, seen)
        except RegistryError as exc:
            problems.append(f"{child.name}: {exc}")
            continue
        if record["id"] != child.name:
            seen.discard(record["id"])
            problems.append(f"{child.name}: manifest id {record['id']!r} is not the directory name")
            continue
        entries[record["id"]] = record["entry"]
    return entries, problems


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("validate", "entries"):
        print("usage: registry.py validate <plugin-dir> | entries <plugins-dir>", file=sys.stderr)
        return 2
    if argv[1] == "validate":
        try:
            record = validate_directory(Path(argv[2]))
        except RegistryError as exc:
            print(f"registry: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(record))
        return 0
    entries, problems = plugin_entries(Path(argv[2]))
    for problem in problems:
        print(f"registry: left off the bar: {problem}", file=sys.stderr)
    print(json.dumps(entries, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
