#!/usr/bin/python3 -I
"""Install a verified source stage and retain the exact previous payload."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight import destination_owners, ownership_problems, runtime_problems

PAYLOAD_CURRENT = "usr/lib/tamlinux/source/current"
STATE = "var/lib/tamlinux/source"
BUNDLE_CURRENT = "usr/lib/tamlinux/current"
BOOTSTRAP_LAUNCHERS = {
    "usr/bin/hi": ("tam", " hi"),
    "usr/bin/start": ("tam-start", ""),
}
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


def verified_stage(stage, digest):
    if not re.fullmatch("[0-9a-f]{64}", digest or "") or stage.is_symlink():
        raise ValueError("a stage and its SHA-256 manifest digest are required")
    manifest = stage / "manifest.json"
    if not fingerprint(manifest):
        raise ValueError("stage manifest is missing")
    data = manifest.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("stage manifest changed")
    receipt = json.loads(data)
    if not receipt or not receipt.get("files") or inventory(stage / "payload") != receipt["files"]:
        raise ValueError("stage files differ from the manifest")
    return receipt


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


def bootstrap_launchers(root):
    owners = destination_owners(root, BOOTSTRAP_LAUNCHERS)
    secure_directory(root, "usr/bin")
    for path, (command, arguments) in BOOTSTRAP_LAUNCHERS.items():
        contents = (f'#!/bin/sh\nif [ -x /usr/bin/{command} ]; then\n'
                    f'    exec /usr/bin/{command}{arguments} "$@"\nfi\n'
                    'exec /usr/bin/tam-nut welcome\n')
        expected = [0o755, hashlib.sha256(contents.encode()).hexdigest()]
        if owners.get(path) != {"tam-nut"} or fingerprint(root / path) != expected:
            raise ValueError(f"expected intact tam-nut launcher /{path}")
    return sorted(BOOTSTRAP_LAUNCHERS)


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
        receipt = verified_stage(stage, digest)
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
                copy_file(stage / "manifest.json", candidate / "manifest.json", 0o644)
                if fingerprint(candidate / "manifest.json")[1] != digest:
                    raise ValueError("stage manifest changed during import")
                for directory, _, _ in os.walk(candidate, topdown=False):
                    sync_dir(directory)
                candidate.rename(saved)
                sync_dir(self.state)
        if verified_stage(saved, digest) != receipt:
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
        current = self.current()
        self.check_switch(old, self.manifest(new)["files"], current.get("external", []))
        if old == new:
            return
        write_json(self.pending, {"from": old, "to": new} | self.migration_fields(current))
        self.complete()

    def check_switch(self, old, after, external):
        self.require_detached_slot()
        before = self.manifest(old)["files"]
        self.check_ownership(before.keys() | after.keys(), external)
        self.check_runtime(self.runtime_id(old), None, False)
        self.check(self.placed(before, external), self.placed(after, external))

    def preview(self, args, root_info):
        secure_directory(self.root, STATE)
        if os.path.lexists(self.pending):
            raise ValueError("resume or roll back the pending installation")
        if not args.stage:
            raise ValueError("preview requires a source stage")
        receipt = verified_stage(args.stage, args.digest)
        problems = runtime_problems(self.root)
        if problems:
            raise ValueError("runtime preflight found problems:\n  " + "\n  ".join(problems))
        current = self.current()
        old = current["current"]
        bundle_args = (args.bundle_archive, args.bundle_sha256, args.bundle_hash, args.bundle_id)
        if any(value is not None for value in bundle_args):
            if not all(bundle_args):
                raise ValueError("preview requires the exact recovery bundle and archive")
            from migration import BundleMigration
            rollback = BundleMigration(self).inspect(
                receipt["files"], args.bundle_archive, args.bundle_sha256,
                args.bundle_hash, args.bundle_id)
            rollback = {"kind": "bundle", **rollback}
        else:
            if old is not None:
                verified_stage(self.state / old, old)
            self.check_switch(old, receipt["files"], current.get("external", []))
            rollback = {"kind": "clean"} if old is None else {"kind": "source", "manifest": old}
        if os.path.lexists(self.pending) or self.current() != current:
            raise ValueError("the target changed during preparation; try again")
        return {"version": receipt["version"], "components": receipt["components"],
                "manifest": args.digest, "root": str(self.root),
                "rootIdentity": [root_info.st_dev, root_info.st_ino], "rollback": rollback}

    def require_detached_slot(self):
        secure_directory(self.root, Path(BUNDLE_CURRENT).parent)
        if os.path.lexists(self.root / BUNDLE_CURRENT):
            raise ValueError("the legacy bundle is installed; use the migration operation")
        if os.path.lexists(self.state.parent / "transaction"):
            from migration import BundleMigration
            if BundleMigration(self).status().get("state") != "complete":
                raise ValueError("finish the pending legacy bundle transaction")

    def check_ownership(self, files, external):
        if external and external != bootstrap_launchers(self.root):
            raise ValueError("unexpected external launcher record")
        if os.path.lexists(self.root / "var/lib/pacman"):
            problems = ownership_problems(self.root, set(files) - set(external))
            if problems:
                raise ValueError("\n".join(problems))

    @staticmethod
    def migration_fields(record):
        return {name: record[name] for name in ("bundle", "external") if name in record}

    def runtime_id(self, identity):
        if identity and (self.state / identity / "payload" / PAYLOAD_CURRENT).is_dir():
            return identity
        return None

    @staticmethod
    def placed(files, external=()):
        return {name: value for name, value in files.items()
                if name not in external and not name.startswith(PAYLOAD_CURRENT + "/")}

    def complete(self, reverse=False):
        pending = read_json(self.pending)
        if pending is None:
            raise ValueError("no pending source installation")
        if "migration" in pending:
            from migration import BundleMigration
            BundleMigration(self).complete(pending, reverse)
            return
        self.require_detached_slot()
        old, new = pending["from"], pending["to"]
        if reverse:
            old, new = new, old
        self.switch_files(old, new, pending.get("external", []))
        self.finish({"current": new, "previous": old} | self.migration_fields(pending))

    def switch_files(self, old, new, external):
        before = self.manifest(old)["files"]
        after = self.manifest(new)["files"]
        if new is not None and inventory(self.state / new / "payload") != after:
            raise ValueError("retained recovery files changed")
        self.check_ownership(before.keys() | after.keys(), external)
        self.check_runtime(self.runtime_id(old), self.runtime_id(new), True)
        before, after = self.placed(before, external), self.placed(after, external)
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

    def finish(self, active):
        write_json(self.active, active)
        self.pending.unlink()
        sync_dir(self.state)

    def current(self):
        return read_json(self.active) or {"current": None, "previous": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "migrate", "preview", "status", "resume",
                                           "rollback", "rollback-bundle"])
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--digest")
    parser.add_argument("--bundle-archive", type=Path)
    parser.add_argument("--bundle-hash")
    parser.add_argument("--bundle-sha256")
    parser.add_argument("--bundle-id")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    if args.plan is not None:
        if args.action != "install" or any((args.root, args.stage, args.digest, args.bundle_id,
                                            args.bundle_archive, args.bundle_hash, args.bundle_sha256)):
            raise ValueError("an install plan supplies the destination and stage")
        install_plan(args.plan)
        return
    if args.root is None:
        raise ValueError("an isolated root or an approved install plan is required")
    root = args.root.resolve(strict=True)
    if not root.is_dir() or args.root.is_symlink() or (root == Path("/") and args.action != "preview"):
        raise ValueError("this development installer requires an isolated test root")
    root_info = root.stat()
    if root_info.st_uid != os.geteuid() or root_info.st_mode & 0o022:
        raise ValueError("test root must be owned by you and privately writable")
    system = Installation(root)
    if args.action == "preview":
        print(json.dumps(system.preview(args, root_info), sort_keys=True))
        return
    if args.action == "status":
        print(json.dumps(system.current() | {"pending": read_json(system.pending)}, sort_keys=True))
        return
    with system.locked():
        current = system.current()
        pending = system.pending.exists()
        if args.action in ("install", "migrate"):
            if pending:
                raise ValueError("resume or roll back the pending installation")
            if not args.stage or not re.fullmatch("[0-9a-f]{64}", args.digest or ""):
                raise ValueError("install requires a stage and its SHA-256 manifest digest")
            system.retain(args.stage, args.digest)
            if args.action == "migrate":
                from migration import BundleMigration
                BundleMigration(system).start(args.digest, args.bundle_archive,
                                              args.bundle_sha256, args.bundle_hash)
            else:
                system.start(current["current"], args.digest)
        elif args.action == "resume":
            system.complete()
        elif args.action == "rollback-bundle":
            from migration import BundleMigration
            BundleMigration(system).rollback()
        elif pending:
            system.complete(reverse=True)
        elif current["current"] is not None:
            if current.get("bundle") and not current["previous"]:
                raise ValueError("use rollback-bundle to restore the previous bundle")
            system.start(current["current"], current["previous"])
        else:
            raise ValueError("no source installation to roll back")


def check_console():
    command = ["/usr/bin/loginctl", "--no-pager"]
    sessions = subprocess.check_output([*command, "list-sessions", "--no-legend"], text=True)
    for entry in sessions.splitlines():
        if not entry.strip():
            continue
        session = entry.split()[0]
        kind = subprocess.check_output(
            [*command, "show-session", "-p", "Type", "--value", "--", session], text=True,
        ).strip()
        if kind not in {"tty", "unspecified", ""}:
            raise ValueError("end the graphical session before installing")


def install_plan(path):
    # The operator imports the reviewed plan and its stage into a private
    # directory before invoking Make. No code or payload is read as root
    # from the regular user's checkout or build directory.
    system_root = Path("/")
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("use the absolute path to the approved install plan")
    if os.geteuid() == 0:
        secure_directory(system_root, path.parent.relative_to(system_root))
    else:
        secure_directory(path.parent.parent, path.parent.name)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o022:
        raise ValueError("the install plan must be a privately writable regular file")
    plan = read_json(path)
    target = plan["target"]
    root = Path(target["root"])
    if not root.is_dir() or root != root.resolve(strict=True):
        raise ValueError("the approved target must be a canonical root directory")
    info = root.stat()
    if (plan["host"] != os.uname().nodename or target["rootIdentity"] != [info.st_dev, info.st_ino]
            or info.st_uid != os.geteuid() or info.st_mode & 0o022):
        raise ValueError("the approved target host or root identity changed")
    if root == system_root and os.geteuid() != 0:
        raise ValueError("the running root requires root approval")
    if target["rollback"] != {"kind": "clean"}:
        raise ValueError("the approved operation requires a clean source install")
    digest = target["manifest"]
    if not re.fullmatch("[0-9a-f]{64}", digest):
        raise ValueError("the approved manifest digest is invalid")
    stage = path.with_name(digest)
    secure_directory(path.parent, digest)
    if not stage.is_dir():
        raise ValueError("the approved stage is missing")
    for entry in stage.rglob("*"):
        info = entry.lstat()
        if (not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))
                or info.st_uid != os.geteuid() or info.st_mode & 0o022):
            raise ValueError(f"unsafe staged entry: {entry}")
    receipt = verified_stage(stage, digest)
    if any(receipt[field] != target[field] for field in ("version", "components")):
        raise ValueError("the staged version or Git revisions differ from approval")
    problems = runtime_problems(root)
    if problems:
        raise ValueError("runtime preflight found problems:\n  " + "\n  ".join(problems))
    if root == system_root:
        check_console()
    system = Installation(root)
    with system.locked():
        if root == system_root and os.path.lexists(system.state.parent / "transaction"):
            raise ValueError("retire the legacy bundle transaction before the clean install")
        current = system.current()
        pending = read_json(system.pending)
        if current not in ({"current": None, "previous": None},
                           {"current": digest, "previous": None}):
            raise ValueError("the approved target already has a different source install")
        if pending is not None:
            if pending != {"from": None, "to": digest}:
                raise ValueError("a different source transaction is pending")
            system.complete()
            return
        system.check_switch(current["current"], receipt["files"], [])
        system.retain(stage, digest)
        system.start(current["current"], digest)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, tarfile.TarError) as exc:
        raise SystemExit(f"Tamlinux source install: {exc}")
