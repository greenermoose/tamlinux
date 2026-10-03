"""Validate plugin manifests before the clock proof loads them."""

from __future__ import annotations

import json
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
