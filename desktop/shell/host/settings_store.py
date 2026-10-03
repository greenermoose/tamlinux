"""Settings document for the clock proof host."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path


class SettingsError(Exception):
    """Settings failed validation or the destination was refused."""

MAX_STRING = 512
SCALAR_TYPES = (str, int, float, bool)


def validate_document(document: dict, allowed_ids: set[str]) -> dict:
    if not isinstance(document, dict) or document.get("version") != 1:
        raise SettingsError("settings version must be 1")
    entries = document.get("entries")
    if not isinstance(entries, dict):
        raise SettingsError("settings entries must be an object")
    clean_entries = {}
    for plugin_id, entry in entries.items():
        if plugin_id not in allowed_ids:
            raise SettingsError(f"unknown plugin id: {plugin_id}")
        if not isinstance(entry, dict) or entry.get("id") != plugin_id:
            raise SettingsError(f"entry id does not match {plugin_id}")
        clean = {"id": plugin_id}
        for key, value in entry.items():
            if key == "id":
                continue
            if type(value) not in SCALAR_TYPES:
                raise SettingsError(f"unsupported setting type for {key}")
            if isinstance(value, str) and len(value) > MAX_STRING:
                raise SettingsError(f"setting {key} is too long")
            if isinstance(value, float) and value != value:
                raise SettingsError(f"setting {key} is not finite")
            clean[key] = value
        clean_entries[plugin_id] = clean
    return {"version": 1, "entries": clean_entries}


def write_settings(directory: Path, document: dict, allowed_ids: set[str]) -> Path:
    """Atomically write settings.json inside a private directory."""
    cleaned = validate_document(document, allowed_ids)
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise SettingsError("settings directory is not a real directory")
    info = directory.stat()
    if info.st_uid != os.getuid() or (info.st_mode & 0o077) != 0:
        raise SettingsError("settings directory must be private to the current user")
    payload = (json.dumps(cleaned, indent=2) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".settings.", suffix=".tmp", dir=directory)
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, payload)
        os.fsync(fd)
    except Exception:
        os.close(fd)
        os.unlink(temporary)
        raise
    os.close(fd)
    destination = directory / "settings.json"
    os.replace(temporary, destination)
    os.chmod(destination, 0o600)
    return destination


def read_settings(path: Path, allowed_ids: set[str]) -> dict:
    file_info = Path(path)
    if file_info.is_symlink() or not file_info.is_file():
        raise SettingsError("settings file is missing")
    parent = file_info.parent
    parent_stat = parent.stat()
    st = file_info.stat()
    private_dir = parent_stat.st_uid == os.getuid() and (parent_stat.st_mode & 0o077) == 0
    private_file = st.st_uid == os.getuid() and (st.st_mode & 0o077) == 0
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or not (private_dir or private_file):
        raise SettingsError("settings file is not a private regular file")
    if st.st_size > 64 * 1024:
        raise SettingsError("settings file is too large")
    try:
        document = json.loads(file_info.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SettingsError("settings file is malformed") from exc
    return validate_document(document, allowed_ids)
