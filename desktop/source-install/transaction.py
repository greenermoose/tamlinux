#!/usr/bin/python3 -I
"""Install a verified source stage and retain the exact previous payload."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight import ownership_problems

PAYLOAD_CURRENT = "usr/lib/tamlinux/source/current"
STATE = "var/lib/tamlinux/source"
PLACEMENTS = (
    "usr/bin", "usr/lib/issue.d", "usr/lib/environment.d", "usr/lib/NetworkManager/conf.d",
    "usr/lib/sysctl.d", "usr/lib/systemd", "usr/lib/tmpfiles.d",
    "usr/share/applications", "usr/share/bash-completion/completions", "usr/share/doc",
    "usr/share/fontconfig", "usr/share/icons/hicolor", "usr/share/libalpm/hooks",
    "usr/share/licenses", "usr/share/man", "usr/share/polkit-1/actions", "usr/share/start",
    PAYLOAD_CURRENT,
)


def allowed(relative):
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        return False
    return (
        relative == "usr/share/fonts/truetype/TamlinuxIcons.ttf"
        or any(relative.startswith(base + "/") for base in PLACEMENTS)
    )


def fingerprint(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o7022:
        raise ValueError(f"unexpected file type or mode: {path}")
    with path.open("rb") as stream:
        return [stat.S_IMODE(info.st_mode), hashlib.file_digest(stream, "sha256").hexdigest()]


def inventory(stage):
    if not stage.is_dir() or stage.is_symlink():
        raise ValueError(f"expected a staging directory: {stage}")
    entries = {}
    for path in sorted(stage.rglob("*")):
        if stat.S_ISDIR(path.lstat().st_mode):
            continue
        relative = path.relative_to(stage).as_posix()
        if not allowed(relative):
            raise ValueError(f"path is outside the cultivar install locations: {relative}")
        entries[relative] = fingerprint(path)
    return entries


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_file(path, mode, writer):
    fd, name = tempfile.mkstemp(prefix=".tamlinux-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            writer(stream)
            os.fchmod(stream.fileno(), mode)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        sync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path, value):
    data = (json.dumps(value, sort_keys=True) + "\n").encode()
    write_file(path, 0o644, lambda stream: stream.write(data))


def read_json(path):
    try:
        with path.open() as stream:
            return json.load(stream)
    except FileNotFoundError:
        return None


def copy_file(origin, target, mode):
    with origin.open("rb") as incoming:
        write_file(target, mode, lambda stream: shutil.copyfileobj(incoming, stream))


def secure_directory(root, relative, create=False):
    current = root
    for part in Path(relative).parts:
        if part in ("/", ".."):
            raise ValueError(f"invalid system path: {relative}")
        current = current / part
        if create and not current.exists() and not current.is_symlink():
            current.mkdir(mode=0o755)
            sync_dir(current.parent)
        try:
            info = current.lstat()
        except FileNotFoundError:
            if create:
                raise
            break
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o022:
            raise ValueError(f"unsafe system directory: {current}")


class Installation:
    def __init__(self, root):
        self.root = root
        self.state = root / STATE
        self.active = self.state / "active.json"
        self.pending = self.state / "pending.json"
        self.runtime = self.root / PAYLOAD_CURRENT

    def check_runtime(self, old, new, resuming):
        secure_directory(self.root, self.runtime.parent.relative_to(self.root))
        target = self.runtime.readlink().as_posix() if self.runtime.is_symlink() else None
        if target is None and self.runtime.exists():
            raise ValueError(f"unmanaged runtime directory: {self.runtime}")
        permitted = {f"versions/{old}" if old else None}
        if resuming:
            permitted.add(f"versions/{new}" if new else None)
        if target not in permitted:
            raise ValueError(f"unexpected runtime link: {self.runtime}")
        if target:
            identity = target.split("/")[1]
            self.verify_runtime(identity, self.runtime.parent / target)

    def verify_runtime(self, identity, directory):
        secure_directory(self.root, directory.relative_to(self.root))
        expected = {
            name.removeprefix(PAYLOAD_CURRENT + "/"): value
            for name, value in self.manifest(identity)["files"].items()
            if name.startswith(PAYLOAD_CURRENT + "/")
        }
        actual = {
            path.relative_to(directory).as_posix(): fingerprint(path)
            for path in sorted(directory.rglob("*"))
            if not stat.S_ISDIR(path.lstat().st_mode)
        }
        if actual != expected:
            raise ValueError(f"runtime differs from its recorded files: {directory}")

    def select_runtime(self, identity):
        if identity is None:
            if self.runtime.is_symlink():
                self.runtime.unlink()
                sync_dir(self.runtime.parent)
            return
        source = self.state / identity / "payload" / PAYLOAD_CURRENT
        if not source.is_dir():
            return
        versions = self.runtime.parent / "versions"
        secure_directory(self.root, versions.relative_to(self.root), create=True)
        generation = versions / identity
        if not generation.exists():
            with tempfile.TemporaryDirectory(prefix=".incoming-", dir=versions) as tmp:
                tree = Path(tmp) / "tree"
                for path in sorted(source.rglob("*")):
                    if path.is_dir():
                        continue
                    target = tree / path.relative_to(source)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    copy_file(path, target, fingerprint(path)[0])
                self.verify_runtime(identity, tree)
                for directory, _, _ in os.walk(tree, topdown=False):
                    sync_dir(directory)
                tree.rename(generation)
                sync_dir(versions)
        self.verify_runtime(identity, generation)
        with tempfile.TemporaryDirectory(prefix=".switch-", dir=self.runtime.parent) as tmp:
            link = Path(tmp) / "current"
            link.symlink_to(f"versions/{identity}")
            link.replace(self.runtime)
            sync_dir(self.runtime.parent)

    @contextmanager
    def locked(self):
        secure_directory(self.root, STATE, create=True)
        with (self.state / "lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def manifest(self, identity):
        if identity is None:
            return {"files": {}}
        return read_json(self.state / identity / "manifest.json")

    def retain(self, stage, digest):
        source = stage / "payload"
        receipt = read_json(stage / "manifest.json")
        if hashlib.sha256((stage / "manifest.json").read_bytes()).hexdigest() != digest:
            raise ValueError("stage manifest changed")
        if not receipt or not receipt.get("files") or inventory(source) != receipt["files"]:
            raise ValueError("stage files differ from the manifest")
        saved = self.state / digest
        if not saved.exists():
            with tempfile.TemporaryDirectory(prefix="retaining-", dir=self.state) as tmp:
                candidate = Path(tmp) / digest
                for relative, (mode, _) in receipt["files"].items():
                    target = candidate / "payload" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    copy_file(source / relative, target, mode)
                if inventory(candidate / "payload") != receipt["files"]:
                    raise ValueError("stage changed during import")
                write_json(candidate / "manifest.json", receipt)
                for directory, _, _ in os.walk(candidate, topdown=False):
                    sync_dir(directory)
                candidate.rename(saved)
                sync_dir(self.state)
        if inventory(saved / "payload") != receipt["files"] or self.manifest(digest) != receipt:
            raise ValueError("retained stage differs from the manifest")

    def check(self, before, after, resuming=False):
        for relative in sorted(before.keys() | after.keys()):
            if not allowed(relative) or ".." in Path(relative).parts:
                raise ValueError(f"invalid destination: {relative}")
            secure_directory(self.root, Path(relative).parent)
            target = self.root / relative
            found = fingerprint(target)
            alternatives = (before.get(relative), after.get(relative)) if resuming else (before.get(relative),)
            if found not in alternatives:
                raise ValueError(f"unmanaged or modified destination: {target}")

    def start(self, old, new):
        before = self.manifest(old)["files"]
        after = self.manifest(new)["files"]
        self.check_runtime(self.runtime_id(old), self.runtime_id(new), False)
        self.check(self.placed(before), self.placed(after))
        if old == new:
            return
        write_json(self.pending, {"from": old, "to": new})
        self.complete()

    def runtime_id(self, identity):
        if identity and (self.state / identity / "payload" / PAYLOAD_CURRENT).is_dir():
            return identity
        return None

    @staticmethod
    def placed(files):
        return {name: value for name, value in files.items()
                if not name.startswith(PAYLOAD_CURRENT + "/")}

    def complete(self, reverse=False):
        pending = read_json(self.pending)
        if pending is None:
            raise ValueError("no pending source installation")
        old, new = pending["from"], pending["to"]
        if reverse:
            old, new = new, old
        before = self.manifest(old)["files"]
        after = self.manifest(new)["files"]
        if new is not None and inventory(self.state / new / "payload") != after:
            raise ValueError("retained recovery files changed")
        self.check_runtime(self.runtime_id(old), self.runtime_id(new), True)
        before, after = self.placed(before), self.placed(after)
        self.check(before, after, resuming=True)
        for relative in sorted(before.keys() | after.keys()):
            target = self.root / relative
            if fingerprint(target) == after.get(relative):
                continue
            if relative in after:
                secure_directory(self.root, Path(relative).parent, create=True)
                copy_file(self.state / new / "payload" / relative, target, after[relative][0])
            else:
                target.unlink()
                sync_dir(target.parent)
        self.select_runtime(self.runtime_id(new))
        write_json(self.active, {"current": new, "previous": old})
        self.pending.unlink()
        sync_dir(self.state)

    def current(self):
        return read_json(self.active) or {"current": None, "previous": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "status", "resume", "rollback"])
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--digest")
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if root == Path("/") or not root.is_dir() or args.root.is_symlink():
        raise ValueError("this development installer requires an isolated test root")
    root_info = root.stat()
    if root_info.st_uid != os.geteuid() or root_info.st_mode & 0o022:
        raise ValueError("test root must be owned by you and privately writable")
    system = Installation(root)
    if args.action == "status":
        print(json.dumps(system.current() | {"pending": read_json(system.pending)}, sort_keys=True))
        return
    with system.locked():
        current = system.current()
        pending = system.pending.exists()
        if args.action == "install":
            if pending:
                raise ValueError("resume or roll back the pending installation")
            if not args.stage or not args.digest or len(args.digest) != 64 or any(
                char not in "0123456789abcdef" for char in args.digest
            ):
                raise ValueError("install requires a stage and its SHA-256 manifest digest")
            system.retain(args.stage, args.digest)
            if os.path.lexists(root / "var/lib/pacman"):
                problems = ownership_problems(root, system.manifest(args.digest)["files"])
                if problems:
                    raise ValueError("\n".join(problems))
            system.start(current["current"], args.digest)
        elif args.action == "resume":
            system.complete()
        elif pending:
            system.complete(reverse=True)
        elif current["current"] is not None:
            system.start(current["current"], current["previous"])
        else:
            raise ValueError("no source installation to roll back")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"Tamlinux source install: {exc}")
