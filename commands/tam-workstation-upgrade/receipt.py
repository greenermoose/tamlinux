"""Durable upgrade receipts and a single-host lock."""
from __future__ import annotations

import fcntl
import json
import os
import time
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
        if not isinstance(data, dict) or "id" not in data:
            raise ReceiptError("current upgrade receipt is malformed")
        return data

    def write(self, receipt: dict) -> dict:
        if receipt.get("phase") not in PHASES:
            raise ReceiptError(f"invalid receipt phase {receipt.get('phase')!r}")
        self.root.mkdir(parents=True, exist_ok=True)
        self.history.mkdir(parents=True, exist_ok=True)
        receipt = dict(receipt)
        receipt["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        temporary = self.current_path.with_suffix(".tmp")
        temporary.write_text(payload)
        temporary.replace(self.current_path)
        archived = self.history / f"{receipt['id']}.json"
        archived.write_text(payload)
        return receipt

    def new_id(self) -> str:
        return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + f"-{os.getpid()}"
