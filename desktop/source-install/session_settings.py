"""Prepare an installed Tamlinux source session for the regular user."""
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

LIMIT = 1024 * 1024
LEGACY = b"/usr/lib/tamlinux/source/current/"
CURRENT = b"/usr/lib/tamlinux/current/"
SESSION_FILES = {
    "tamlinux/session/hyprland.lua": ("session/entry.lua",),
    "uwsm/env.d/10-tamlinux.sh": ("session/uwsm-env", "version-notes.txt"),
    "chromium-flags.conf": ("browser/extensions/copy-url", "browser/extensions/yt-dlp",
                            "browser/extensions/whatsapp-slim"),
}
REQUIRED = tuple(SESSION_FILES)[:2]
BROWSERS = (
    "chromium", "google-chrome", "google-chrome-beta", "google-chrome-unstable",
    "BraveSoftware/Brave-Browser", "BraveSoftware/Brave-Browser-Beta",
    "BraveSoftware/Brave-Browser-Nightly", "microsoft-edge", "microsoft-edge-dev",
)


def roots(environ):
    home = Path(environ["HOME"])
    result = {
        kind: Path(environ.get(variable) or home / fallback)
        for kind, variable, fallback in (
            ("config", "XDG_CONFIG_HOME", ".config"),
            ("state", "XDG_STATE_HOME", ".local/state"),
            ("data", "XDG_DATA_HOME", ".local/share"),
        )
    }
    if not home.is_absolute() or any(not p.is_absolute() for p in result.values()):
        raise ValueError("HOME and XDG roots must be absolute")
    return result


def safe(path):
    if any(p.is_symlink() for p in path.parents):
        raise ValueError("Redirected parent: " + str(path))
    return path


def snapshot(path):
    safe(path)
    if not path.exists() and not path.is_symlink():
        return {"kind": "absent"}
    info = path.lstat()
    if info.st_uid != os.getuid():
        raise ValueError("Owner mismatch: " + str(path))
    if stat.S_ISLNK(info.st_mode):
        return {"kind": "link", "link": os.readlink(path)}
    if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
        raise ValueError("Expected bounded regular file: " + str(path))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        current = os.fstat(fd)
        if (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("File changed while opening")
        content = os.read(fd, LIMIT + 1)
        if len(content) > LIMIT:
            raise ValueError("File grew beyond limit")
        return {
            "kind": "file",
            "bytes": base64.b64encode(content).decode(),
            "mode": stat.S_IMODE(info.st_mode),
        }
    finally:
        os.close(fd)


def atomic(path, value):
    safe(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if value["kind"] == "absent":
        path.unlink(missing_ok=True)
    else:
        fd, name = tempfile.mkstemp(prefix=".tamlinux-session-", dir=path.parent)
        temporary = Path(name)
        try:
            if value["kind"] == "link":
                os.close(fd)
                fd = -1
                temporary.unlink()
                temporary.symlink_to(value["link"])
            elif value["kind"] == "file":
                data = base64.b64decode(value["bytes"], validate=True)
                if len(data) > LIMIT:
                    raise ValueError("Session bytes exceed limit")
                os.write(fd, data)
                os.fchmod(fd, value["mode"] & 0o777)
                os.fsync(fd)
                os.close(fd)
                fd = -1
            else:
                raise ValueError("Unknown file state kind")
            os.replace(temporary, path)
        finally:
            if fd >= 0:
                os.close(fd)
            temporary.unlink(missing_ok=True)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def save(path, document):
    atomic(
        path,
        {
            "kind": "file",
            "mode": 0o600,
            "bytes": base64.b64encode(
                (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
            ).decode(),
        },
    )


def file_state(data, mode):
    return {"kind": "file", "bytes": base64.b64encode(data).decode(), "mode": mode}


def read_record(path):
    state = snapshot(path)
    if state["kind"] == "absent":
        return None
    if state["kind"] != "file" or state["mode"] != 0o600:
        raise ValueError(f"expected private settings record: {path}")
    return json.loads(base64.b64decode(state["bytes"]))


def reload_units():
    subprocess.run(["/usr/bin/systemctl", "--user", "daemon-reload"], check=True, timeout=15)


class SessionSettings:
    def __init__(self):
        self.home = Path(os.environ["HOME"])
        locations = roots(os.environ)
        self.config = locations["config"]
        self.state = locations["state"] / "tamlinux/source-session"
        if (self.home.stat().st_uid != os.geteuid() or self.home.resolve() != self.home
                or not self.config.is_relative_to(self.home) or not self.state.is_relative_to(self.home)
                or ".." in self.config.parts or ".." in self.state.parts):
            raise ValueError("source session requires owned home and in-home XDG paths")
        for path in (self.config, self.state):
            if path.is_relative_to(self.home / ".local") and not path.is_relative_to(self.home / ".local/state"):
                raise ValueError(f"source settings destination overlaps local software: {path}")
        self.identity = hashlib.sha256(os.fsencode(self.config) + b"\0" + os.fsencode(self.state)).hexdigest()

    @contextmanager
    def locked(self):
        safe(self.state / "lock")
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.state.stat()
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError(f"expected private source session directory: {self.state}")
        fd = os.open(self.state / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    @staticmethod
    def default(defaults, relative):
        path = defaults / ".config" / relative
        return file_state(path.read_bytes(), path.stat().st_mode & 0o777)

    @staticmethod
    def publish_default(target, default):
        if not os.path.lexists(target):
            safe(target)
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".tamlinux-default-", dir=target.parent) as tmp:
                staged = Path(tmp) / "default"
                atomic(staged, default)
                try:
                    os.link(staged, target)
                except FileExistsError:
                    pass
                directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)

    def _migrate_legacy_paths(self):
        """One-time 0.6.35 -> 0.6.36 user config path cutover."""
        candidates = [self.config / rel for rel in SESSION_FILES]
        for browser in BROWSERS:
            for name in ("copy_url", "ytdlp"):
                candidates.append(self.config / browser / "NativeMessagingHosts" / f"org.tamlinux.{name}.json")
        for target in candidates:
            try:
                value = snapshot(target)
            except ValueError:
                continue
            if value["kind"] != "file":
                continue
            data = base64.b64decode(value["bytes"])
            updated = data.replace(LEGACY, CURRENT).replace(
                b'"/usr/bin/tam-chromium-', b'"/usr/bin/tamlinux/tam-chromium-'
            )
            if updated != data:
                atomic(target, file_state(updated, value["mode"]))

    def ready(self, defaults, active, pending):
        with self.locked():
            if os.path.lexists(pending):
                raise ValueError("source installation is incomplete; recover from the console")
            current = json.loads(active.read_text())
            digest = current["current"]
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                raise ValueError("no active source installation")
            receipt_path = self.state / "ready.json"
            receipt = read_record(receipt_path)
            if receipt is None:
                for item in sorted((defaults / ".config").rglob("*")):
                    if item.is_file():
                        relative = item.relative_to(defaults / ".config").as_posix()
                        # The bash integration uses literal ~/.config paths.
                        config = self.home / ".config" if relative.startswith("bash/") else self.config
                        self.publish_default(config / relative, self.default(defaults, relative))
                share = defaults.parents[1] / "share/tamlinux"
                for relative in (self.home / ".bashrc", self.home / ".gnupg/dirmngr.conf",
                                 self.state.parent / "user-defaults/bashrc.original",
                                 self.state.parent / "user-defaults/dirmngr.json"):
                    safe(relative)
                subprocess.run(["/usr/bin/python3", "-I", share / "user-defaults/apply"],
                               check=True, stdout=subprocess.DEVNULL)
            self._migrate_legacy_paths()
            for relative in REQUIRED:
                target = self.config / relative
                value = snapshot(target)
                data = base64.b64decode(value["bytes"]) if value["kind"] == "file" else b""
                if not data or LEGACY in data or b"/nix/store/" in data:
                    raise ValueError(f"source session setting is unavailable or references retired paths: {target}")
            if receipt != {"current": digest}:
                reload_units()
            if os.path.lexists(pending) or json.loads(active.read_text())["current"] != digest:
                raise ValueError("source installation changed while preparing the session")
            if receipt != {"current": digest}:
                save(receipt_path, {"current": digest})


def run_cli(argv=None):
    if os.geteuid() == 0:
        sys.exit("Tamlinux session settings must run as your regular user")
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        raise ValueError("session_settings.py takes no arguments")
    program = Path(__file__).resolve()
    SessionSettings().ready(program.parents[3] / "defaults/home",
                            Path("/var/lib/tamlinux/active.json"),
                            Path("/var/lib/tamlinux/pending.json"))


if __name__ == "__main__":
    try:
        run_cli()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        sys.exit(f"Tamlinux source session: {error}")
