#!/usr/bin/env python3
"""Apply or reverse the reviewed 0.4.4g SDDM PAM hook cleanup.

The tool is deliberately narrow: it knows the two SDDM files and exact
pre-cleanup hashes from the reviewed 0.4.4g baseline. It never edits either
file until both inputs have passed validation and the checkpoint is durable.
Use only from the retained recovery console with SDDM stopped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile


BASELINE = {
    "etc/pam.d/sddm": {
        "sha256": "b9539d9c6e9449595f4473c2541b60a83e3a836263128061bceecb738a7f4859",
        "hooks": 1,
    },
    "etc/pam.d/sddm-autologin": {
        "sha256": "53a935ef3d4dcc107728ff8d7109fac35b41c743cea19200d3dd498ca1748a0c",
        "hooks": 2,
    },
}
HOOK = re.compile(rb"^[ \t]*-?(?:auth|session)[ \t]+optional[ \t]+pam_gnome_keyring\.so(?:[ \t]+auto_start)?[ \t]*(?:\r?\n)?$")
SCHEMA = 1


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def target(root: Path, rel: str) -> Path:
    return root / rel


def read_regular(path: Path) -> tuple[bytes, os.stat_result]:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"refusing non-regular PAM input: {path}")
    return path.read_bytes(), info


def transform(data: bytes, expected: int, name: str) -> bytes:
    lines = data.splitlines(keepends=True)
    matches = [line for line in lines if HOOK.fullmatch(line)]
    if len(matches) != expected:
        raise ValueError(f"{name}: expected {expected} GNOME keyring hooks, found {len(matches)}")
    cleaned = b"".join(line for line in lines if not HOOK.fullmatch(line))
    if cleaned == data:
        raise ValueError(f"{name}: cleanup made no change")
    return cleaned


def write_atomic(path: Path, data: bytes, mode: int, uid: int, gid: int) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(temporary, uid, gid)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def save_file(directory: Path, rel: str, data: bytes, info: os.stat_result) -> dict:
    name = Path(rel).name
    backup = directory / f"{name}.bytes"
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "path": "/" + rel,
        "backup": f"{name}.bytes",
        "sha256": digest(data),
        "mode": stat.S_IMODE(info.st_mode),
        "uid": info.st_uid,
        "gid": info.st_gid,
    }


def sync_directory(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_record(directory: Path, record: dict) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".transaction.", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, directory / "transaction.json")
        sync_directory(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def require_stopped_sddm() -> None:
    result = subprocess.run(["/usr/bin/systemctl", "show", "--property=ActiveState", "--value", "sddm"],
                            capture_output=True, text=True, check=False)
    state = result.stdout.strip()
    if result.returncode != 0 or state != "inactive":
        raise PermissionError(f"SDDM must be verified inactive before editing PAM (state={state or 'unknown'})")


def load_record(checkpoint: Path) -> dict:
    info = checkpoint.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError("checkpoint must be a real directory")
    record = json.loads((checkpoint / "transaction.json").read_text())
    if (record.get("schema") != SCHEMA or record.get("candidate") != "0.4.4-g"
            or set(record.get("files", {})) != set(BASELINE)):
        raise ValueError("checkpoint schema or file set is invalid")
    for rel, expected in BASELINE.items():
        entry = record["files"][rel]
        if (entry.get("path") != "/" + rel or entry.get("backup") != Path(rel).name + ".bytes"
                or entry.get("sha256") != expected["sha256"]
                or not re.fullmatch(r"[0-9a-f]{64}", entry.get("afterSha256", ""))):
            raise ValueError(f"checkpoint metadata is invalid for {rel}")
    return record


def apply(root: Path, checkpoint: Path) -> None:
    if root.resolve() == Path("/") and os.geteuid() != 0:
        raise PermissionError("apply must run as root from the verified recovery console")
    if root.resolve() == Path("/"):
        require_stopped_sddm()
    if checkpoint.is_symlink() or checkpoint.exists():
        record = load_record(checkpoint)
        if record.get("state") not in ("prepared", "partial", "applied"):
            raise ValueError("checkpoint is not an applicable 0.4.4g transaction")
    else:
        prepared = {}
        for rel, expected in BASELINE.items():
            data, info = read_regular(target(root, rel))
            if digest(data) != expected["sha256"]:
                raise ValueError(f"{rel}: baseline hash drift; no files changed")
            after = transform(data, expected["hooks"], rel)
            prepared[rel] = (data, info, after)
        checkpoint.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{checkpoint.name}.", dir=checkpoint.parent))
        os.chmod(temporary, 0o700)
        files = {}
        for rel, (data, info, after) in prepared.items():
            entry = save_file(temporary, rel, data, info)
            entry["afterSha256"] = digest(after)
            files[rel] = entry
        record = {"schema": SCHEMA, "candidate": "0.4.4-g", "state": "prepared", "files": files}
        write_record(temporary, record)
        sync_directory(temporary)
        os.replace(temporary, checkpoint)
        sync_directory(checkpoint.parent)

    # Validate the complete pair before writing either target. An exact after
    # hash is accepted for a retry of an interrupted two-file transaction.
    plans = []
    for rel, original in BASELINE.items():
        path = target(root, rel)
        current, info = read_regular(path)
        entry = record["files"][rel]
        current_hash = digest(current)
        if current_hash == entry["afterSha256"]:
            continue
        if current_hash != entry["sha256"]:
            raise ValueError(f"{rel}: drift since checkpoint; no additional files changed")
        after = transform(current, original["hooks"], rel)
        if digest(after) != entry["afterSha256"]:
            raise ValueError(f"{rel}: derived output differs from checkpoint")
        plans.append((rel, path, after, info))
    for rel, path, after, info in plans:
        write_atomic(path, after, stat.S_IMODE(info.st_mode), info.st_uid, info.st_gid)
        record["state"] = "partial"
        write_record(checkpoint, record)
    record["state"] = "applied"
    write_record(checkpoint, record)


def restore(root: Path, checkpoint: Path, preserve: Path) -> None:
    if root.resolve() == Path("/") and os.geteuid() != 0:
        raise PermissionError("restore must run as root from the verified recovery console")
    if root.resolve() == Path("/"):
        require_stopped_sddm()
    record = load_record(checkpoint)
    if preserve.is_symlink() or not preserve.exists():
        current_files = {}
        for rel in record["files"]:
            current, info = read_regular(target(root, rel))
            current_files[rel] = (current, info)
        preserve.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{preserve.name}.", dir=preserve.parent))
        os.chmod(temporary, 0o700)
        preserved = {}
        for rel, (data, info) in current_files.items():
            preserved[rel] = save_file(temporary, rel, data, info)
        fd, record_path = tempfile.mkstemp(prefix=".preserved.", dir=temporary)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"schema": SCHEMA, "files": preserved}, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(record_path, 0o600)
        os.replace(record_path, temporary / "preserved.json")
        sync_directory(temporary)
        os.replace(temporary, preserve)
        sync_directory(preserve.parent)
    else:
        if not stat.S_ISDIR(preserve.lstat().st_mode):
            raise ValueError("preserve target must be a real directory")
        preserved = json.loads((preserve / "preserved.json").read_text())
        if preserved.get("schema") != SCHEMA or set(preserved.get("files", {})) != set(BASELINE):
            raise ValueError("preserve directory is incomplete or belongs to another transaction")
        for rel, entry in preserved["files"].items():
            data = (preserve / entry["backup"]).read_bytes()
            if digest(data) != entry["sha256"]:
                raise ValueError(f"preserved current-state hash mismatch for {rel}")
    restore_plans = []
    for rel, entry in record["files"].items():
        data = (checkpoint / entry["backup"]).read_bytes()
        if digest(data) != entry["sha256"]:
            raise ValueError(f"checkpoint backup hash mismatch for {rel}")
        current, _ = read_regular(target(root, rel))
        if digest(current) != entry["sha256"]:
            restore_plans.append((rel, data, entry))
    for rel, data, entry in restore_plans:
        write_atomic(target(root, rel), data, entry["mode"], entry["uid"], entry["gid"])
    record["state"] = "restored"
    write_record(checkpoint, record)


def verify(root: Path, checkpoint: Path) -> None:
    record = load_record(checkpoint)
    for rel, entry in record["files"].items():
        data, info = read_regular(target(root, rel))
        value = digest(data)
        state = "before" if value == entry["sha256"] else "after" if value == entry["afterSha256"] else "drift"
        print(f"{entry['path']} {state} sha256={value} mode={stat.S_IMODE(info.st_mode):04o} uid={info.st_uid} gid={info.st_gid}")
        if state == "drift":
            raise ValueError(f"{rel}: current bytes match neither recorded state")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/"), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("apply", help="checkpoint and remove the three exact hooks")
    p.add_argument("--checkpoint", type=Path, required=True)
    p = sub.add_parser("restore", help="save current PAM state, then restore checkpoint bytes")
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--preserve-current", type=Path, required=True)
    p = sub.add_parser("verify", help="compare live files with before/after checkpoint hashes")
    p.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "apply":
            apply(args.root, args.checkpoint)
        elif args.command == "restore":
            restore(args.root, args.checkpoint, args.preserve_current)
        else:
            verify(args.root, args.checkpoint)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        parser.exit(1, f"pam-transaction: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
