"""Durable upgrade receipts and a single-host lock."""
from __future__ import annotations

import fcntl
import json
import os
import time
import re
import tempfile
import uuid
from pathlib import Path


class ReceiptError(Exception):
    pass


PHASES = (
    "planned",
    "confirmed",
    "applying",
    "verifying",
    "complete",
    "failed",
    "recovering",
    "recovered",
)

IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}\Z')


def atomic_write(path: Path, payload: str) -> None:
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Store:
    def __init__(self, root: Path | None = None):
        state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        self.root = Path(root) if root else state / "tamlinux/workstation-upgrade"
        self.lock_path = self.root / "upgrade.lock"
        self.current_path = self.root / "current.json"
        self.history = self.root / "receipts"
        self._lock_fd = None

    def acquire(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock_fd = open(self.lock_path, "a+", encoding="utf-8")
        try:
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self._lock_fd.close()
            self._lock_fd = None
            raise ReceiptError("another workstation upgrade is already in progress") from exc
        self._lock_fd.seek(0)
        self._lock_fd.truncate()
        self._lock_fd.write(f"{os.getpid()}\n")
        self._lock_fd.flush()

    def release(self) -> None:
        if self._lock_fd is None:
            return
        try:
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
        finally:
            self._lock_fd.close()
            self._lock_fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False

    def read_current(self) -> dict | None:
        if not self.current_path.is_file():
            return None
        try:
            data = json.loads(self.current_path.read_text())
        except (OSError, ValueError) as exc:
            raise ReceiptError("current upgrade receipt is unreadable") from exc
        if (not isinstance(data, dict) or not isinstance(data.get('id'), str)
                or not IDENTIFIER.fullmatch(data['id']) or data.get('phase') not in PHASES):
            raise ReceiptError("current upgrade receipt is malformed")
        return data

    def write(self, receipt: dict) -> dict:
        if receipt.get("phase") not in PHASES:
            raise ReceiptError(f"invalid receipt phase {receipt.get('phase')!r}")
        if not IDENTIFIER.fullmatch(receipt.get('id', '')):
            raise ReceiptError('invalid transaction ID')
        self.root.mkdir(parents=True, exist_ok=True)
        self.history.mkdir(parents=True, exist_ok=True)
        receipt = dict(receipt)
        receipt["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        archived = self.history / f"{receipt['id']}.json"
        atomic_write(archived, payload)
        atomic_write(self.current_path, payload)
        return receipt

    def new_id(self) -> str:
        return uuid.uuid4().hex
