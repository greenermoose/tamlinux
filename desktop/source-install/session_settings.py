"""Prepare an installed source session and journal the bundle handoff."""
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import atomic, roots, safe, save, snapshot

LEGACY = b"/usr/lib/tamlinux/current/"
SOURCE = b"/usr/lib/tamlinux/source/current/"
SESSION_FILES = {
    "tamlinux/session/hyprland.lua": ("session/entry.lua",),
    "uwsm/env.d/10-tamlinux.sh": ("session/uwsm-env", "version-notes.txt"),
    "chromium-flags.conf": ("browser/extensions/copy-url", "browser/extensions/yt-dlp",
                            "browser/extensions/whatsapp-slim"),
}
REQUIRED = tuple(SESSION_FILES)[:2]


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

    def journal(self, digest):
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("invalid source settings manifest digest")
        return self.state / f"migration-{digest}.json"

    @staticmethod
    def default(defaults, relative):
        path = defaults / ".config" / relative
        return file_state(path.read_bytes(), path.stat().st_mode & 0o777)

    @staticmethod
    def publish_default(target, default):
        if not os.path.lexists(target):
            safe(target)
            # Serialize with the journal and avoid overwriting a new user file.
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

    def prepare(self, digest, bundle_hash, defaults):
        path = self.journal(digest)
        previous = read_record(path)
        if previous and previous["phase"] != "rolled-back":
            if previous["bundle"] != bundle_hash or previous["phase"] != "prepared":
                raise ValueError("source settings journal belongs to a different migration")
            self.check_changes(previous, before_only=True)
            return
        changes = {}
        for relative, leaves in SESSION_FILES.items():
            target = self.config / relative
            before = snapshot(target)
            if before["kind"] == "link":
                raise ValueError(f"session setting is a link: {target}")
            if before["kind"] == "absent":
                if relative in REQUIRED:
                    changes[relative] = [before, self.default(defaults, relative)]
                continue
            data = base64.b64decode(before["bytes"])
            if len(data) > 64 * 1024 or before["mode"] & 0o7000:
                raise ValueError(f"session setting exceeds safe migration size or mode: {target}")
            rewritten = data
            for leaf in leaves:
                suffix = b"share/tamlinux/" + leaf.encode()
                rewritten = re.sub(re.escape(LEGACY + suffix) + rb"""(?=$|[\s"'),;])""",
                                   SOURCE + suffix, rewritten)
            if LEGACY in rewritten or b"/nix/store/" in rewritten:
                raise ValueError(f"unrecognized runtime reference in {target}")
            if data != rewritten:
                changes[relative] = [before, file_state(rewritten, before["mode"])]
        save(path, {"bundle": bundle_hash, "phase": "prepared", "changes": changes, "armed": []})

    def verify_prepared(self, digest, bundle_hash):
        record = read_record(self.journal(digest))
        if not record or record["bundle"] != bundle_hash or record["phase"] != "prepared":
            raise ValueError("missing prepared source settings journal")
        self.check_changes(record, before_only=True)

    def check_changes(self, record, before_only=False):
        for relative, states in record["changes"].items():
            if relative not in SESSION_FILES:
                raise ValueError("unrecognized settings journal entry")
            if snapshot(self.config / relative) not in (states[:1] if before_only else states):
                raise ValueError(f"session setting changed during migration: {self.config / relative}")

    def apply(self, digest, bundle_hash):
        path = self.journal(digest)
        record = read_record(path)
        if not record or record["bundle"] != bundle_hash or record["phase"] not in ("prepared", "applying", "applied"):
            raise ValueError("missing matching source settings journal")
        self.check_changes(record)
        if record["phase"] == "applied":
            return
        receipt = self.state / "ready.json"
        if read_record(receipt) is not None:
            atomic(receipt, {"kind": "absent"})
        record["phase"] = "applying"
        save(path, record)
        for relative, (before, after) in record["changes"].items():
            target = self.config / relative
            if relative not in record["armed"]:
                record["armed"].append(relative)
                save(path, record)
            actual = snapshot(target)
            if actual == before:
                atomic(target, after)
            elif actual != after:
                raise ValueError(f"session setting changed during migration: {target}")
        record["phase"] = "applied"
        save(path, record)

    def rollback(self, digest, bundle_hash):
        path = self.journal(digest)
        record = read_record(path)
        if not record or record["bundle"] != bundle_hash:
            raise ValueError("missing matching source settings journal")
        if record["phase"] in ("rolled-back", "prepared"):
            return
        record["phase"] = "rolling-back"
        save(path, record)
        for relative in reversed(record["armed"]):
            if relative not in SESSION_FILES:
                raise ValueError("unrecognized settings journal entry")
            before, after = record["changes"][relative]
            target = self.config / relative
            actual = snapshot(target)
            if actual == before:
                continue
            if actual != after:
                key = hashlib.sha256(json.dumps([relative, actual], sort_keys=True).encode()).hexdigest()
                save(self.state / f"preserved-{key}.json", {"path": relative, "value": actual})
            atomic(target, before)
        record["phase"] = "rolled-back"
        save(path, record)

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
            bundle = current.get("bundle")
            if bundle:
                record = read_record(self.journal(bundle["source"]))
                if not record or record["phase"] != "applied" or record["bundle"] != bundle["hash"]:
                    raise ValueError("this user's source settings migration is incomplete")
            elif receipt is None:
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
            for relative in REQUIRED:
                target = self.config / relative
                value = snapshot(target)
                data = base64.b64decode(value["bytes"]) if value["kind"] == "file" else b""
                if not data or LEGACY in data or b"/nix/store/" in data:
                    raise ValueError(f"source session setting is unavailable or still points to the bundle: {target}")
            if receipt != {"current": digest}:
                reload_units()
            if os.path.lexists(pending) or json.loads(active.read_text())["current"] != digest:
                raise ValueError("source installation changed while preparing the session")
            if receipt != {"current": digest}:
                save(receipt_path, {"current": digest})


def rebind_bundle_settings(root=Path("/")):
    bundle_tool = "/usr/bin/tam-bundle"
    env = {"PATH": "/usr/bin", "LC_ALL": "C", "HOME": os.environ["HOME"]}
    for key in ("XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
                "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if key in os.environ:
            env[key] = os.environ[key]
    if "XDG_RUNTIME_DIR" not in env:
        runtime_dir = Path(f"/run/user/{os.getuid()}")
        try:
            if runtime_dir.is_dir() and runtime_dir.stat().st_uid == os.getuid():
                env["XDG_RUNTIME_DIR"] = str(runtime_dir)
        except OSError:
            pass
    check = subprocess.run([bundle_tool, "--root", str(root), "session-ready"],
                           env=env, text=True, capture_output=True)
    if check.returncode == 0:
        return
    if check.returncode != 4:
        raise subprocess.CalledProcessError(check.returncode, check.args, check.stdout, check.stderr)
    output = subprocess.check_output([bundle_tool, "--root", str(root), "capture"],
                                     env=env, text=True)
    match = re.search(r"^private settings capture: ([A-Za-z0-9@_.-]+)(?: \(incomplete\))?$",
                      output, re.MULTILINE)
    if not match:
        raise ValueError("bundle settings capture has no recovery identity")
    capture = match[1]
    subprocess.run([bundle_tool, "--root", str(root), "prepare-settings", capture], env=env, check=True)
    subprocess.run([bundle_tool, "--root", str(root), "apply-settings"], env=env, check=True)
    subprocess.run([bundle_tool, "--root", str(root), "session-ready"], env=env, check=True)


def run_cli(argv=None):
    import argparse
    if os.geteuid() == 0:
        sys.exit("Tamlinux session settings must run as your regular user")
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        program = Path(__file__).resolve()
        SessionSettings().ready(program.parents[3] / "defaults/home",
                                Path("/var/lib/tamlinux/source/active.json"),
                                Path("/var/lib/tamlinux/source/pending.json"))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--digest", required=True)
    prep.add_argument("--bundle-hash", required=True)
    prep.add_argument("--defaults", type=Path, required=True)
    prep.add_argument("--root", type=Path, default=Path("/"))
    prep.add_argument("--skip-bundle-check", action="store_true")
    ap = sub.add_parser("apply")
    ap.add_argument("--digest", required=True)
    ap.add_argument("--bundle-hash", required=True)
    rb = sub.add_parser("rollback")
    rb.add_argument("--digest", required=True)
    rb.add_argument("--bundle-hash", required=True)
    rebind = sub.add_parser("rebind-bundle")
    rebind.add_argument("--root", type=Path, default=Path("/"))
    args = parser.parse_args(argv)
    settings = SessionSettings()
    with settings.locked():
        if args.action == "prepare":
            if not args.skip_bundle_check:
                subprocess.run(["/usr/bin/tam-bundle", "--root", str(args.root), "session-ready"], check=True)
            settings.prepare(args.digest, args.bundle_hash, args.defaults)
        elif args.action == "apply":
            settings.apply(args.digest, args.bundle_hash)
        elif args.action == "rollback":
            settings.rollback(args.digest, args.bundle_hash)
        elif args.action == "rebind-bundle":
            rebind_bundle_settings(args.root)


if __name__ == "__main__":
    try:
        run_cli()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        sys.exit(f"Tamlinux source session: {error}")
