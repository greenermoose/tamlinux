#!/usr/bin/python3 -I
"""Install a verified cultivar stage into /usr/lib/tamlinux/versions/<digest>."""
import argparse
from contextlib import contextmanager
import ctypes
import errno
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

_FICLONE = 0x40049409
_SYNCFS = None

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight import ownership_problems, runtime_problems

PAYLOAD_CURRENT = "usr/lib/tamlinux/current"
STATE = "var/lib/tamlinux"
LEGACY_STATE = "var/lib/tamlinux/source"
LEGACY_CURRENT = "usr/lib/tamlinux/source/current"

CULTIVAR_LINKS = (
    ("usr/bin/tam", "/usr/lib/tamlinux/current/bin/tam"),
    ("usr/bin/tamlinux", "/usr/lib/tamlinux/current/bin"),
    ("usr/share/doc/tamlinux", "/usr/lib/tamlinux/current/share/doc"),
)

PLACEMENTS = (
    "etc/profile.d",
    "usr/lib/issue.d",
    "usr/lib/environment.d",
    "usr/lib/NetworkManager/conf.d",
    "usr/lib/sysctl.d",
    "usr/lib/systemd",
    "usr/lib/tmpfiles.d",
    "usr/share/applications/tamlinux",
    "usr/share/fontconfig",
    "usr/share/fonts/tamlinux",
    "usr/share/libalpm/hooks",
    "usr/share/polkit-1/actions",
    PAYLOAD_CURRENT,
)


def allowed(relative):
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        return False
    return (
        relative == "usr/lib/tamlinux/browser-policy-exec"
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


def progress(message):
    print(message, flush=True)


def _load_syncfs():
    global _SYNCFS
    if _SYNCFS is None:
        try:
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
            func = libc.syncfs
            func.argtypes = [ctypes.c_int]
            func.restype = ctypes.c_int
            _SYNCFS = func
        except (OSError, AttributeError):
            _SYNCFS = False
    return _SYNCFS or None


def sync_fs(path):
    syncfs = _load_syncfs()
    if syncfs is None:
        os.sync()
        return
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        if syncfs(fd) != 0:
            err = ctypes.get_errno()
            if err == errno.ENOSYS:
                os.sync()
                return
            raise OSError(err, os.strerror(err), str(path))
    finally:
        os.close(fd)


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _clone_or_copy(src_stream, dst_stream):
    try:
        fcntl.ioctl(dst_stream.fileno(), _FICLONE, src_stream.fileno())
        return
    except OSError:
        pass
    shutil.copyfileobj(src_stream, dst_stream)


def write_file(path, mode, writer, *, sync=True, direct=False):
    if direct:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                writer(stream)
                os.fchmod(stream.fileno(), mode)
                stream.flush()
                if sync:
                    os.fsync(stream.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        if sync:
            sync_dir(path.parent)
        return
    fd, name = tempfile.mkstemp(prefix=".tamlinux-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            writer(stream)
            os.fchmod(stream.fileno(), mode)
            stream.flush()
            if sync:
                os.fsync(stream.fileno())
        temporary.replace(path)
        if sync:
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


def copy_file(origin, target, mode, *, sync=True, direct=False):
    with origin.open("rb") as incoming:
        write_file(
            target,
            mode,
            lambda stream: _clone_or_copy(incoming, stream),
            sync=sync,
            direct=direct,
        )


def mkdir_public(path, stop_at):
    missing = []
    current = path
    while current != stop_at and not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o755, exist_ok=True)
        os.chmod(directory, 0o755)


def secure_directory(root, relative, create=False, *, sync=True):
    expected_uid = 0 if (root == Path("/") and not create) else os.geteuid()
    current = root
    for part in Path(relative).parts:
        if part in ("/", ".."):
            raise ValueError(f"invalid system path: {relative}")
        current = current / part
        if create and not current.exists() and not current.is_symlink():
            current.mkdir(mode=0o755)
            os.chmod(current, 0o755)
            if sync:
                sync_dir(current.parent)
        try:
            info = current.lstat()
        except FileNotFoundError:
            if create:
                raise
            break
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != expected_uid or info.st_mode & 0o022:
            raise ValueError(f"unsafe system directory: {current}")


def atomic_symlink(path, target):
    if path.is_symlink() and path.readlink().as_posix() == target:
        return False
    with tempfile.TemporaryDirectory(prefix=".link-", dir=path.parent) as tmp:
        link = Path(tmp) / path.name
        link.symlink_to(target)
        link.replace(path)
    sync_dir(path.parent)
    return True


class Installation:
    def __init__(self, root):
        self.root = root
        self.state = root / STATE
        self.active = self.state / "active.json"
        self.pending = self.state / "pending.json"
        self.manifests = self.state / "manifests"
        self.integration = self.state / "integration"
        self.runtime = self.root / PAYLOAD_CURRENT
        self.versions = self.runtime.parent / "versions"
        self.legacy_state = root / LEGACY_STATE

    def legacy_active(self):
        return read_json(self.legacy_state / "active.json")

    def legacy_manifest(self, identity):
        if not identity:
            return {"files": {}}
        return read_json(self.legacy_state / identity / "manifest.json") or {"files": {}}

    def manifest_path(self, identity):
        return self.manifests / f"{identity}.json"

    def manifest(self, identity):
        if identity is None:
            return {"files": {}}
        return read_json(self.manifest_path(identity)) or {"files": {}}

    @staticmethod
    def cultivar_files(files):
        prefix = PAYLOAD_CURRENT + "/"
        return {name.removeprefix(prefix): value for name, value in files.items() if name.startswith(prefix)}

    @staticmethod
    def placed(files):
        prefix = PAYLOAD_CURRENT + "/"
        return {name: value for name, value in files.items() if not name.startswith(prefix)}

    def verify_version(self, identity, directory):
        secure_directory(self.root, directory.relative_to(self.root))
        expected = self.cultivar_files(self.manifest(identity)["files"])
        actual = {
            path.relative_to(directory).as_posix(): fingerprint(path)
            for path in sorted(directory.rglob("*"))
            if not stat.S_ISDIR(path.lstat().st_mode)
        }
        if actual != expected:
            raise ValueError(f"cultivar tree differs from its recorded files: {directory}")

    def verify_retained(self, identity):
        mpath = self.manifest_path(identity)
        if not fingerprint(mpath) or hashlib.sha256(mpath.read_bytes()).hexdigest() != identity:
            raise ValueError(f"retained manifest missing or modified: {mpath}")
        receipt = self.manifest(identity)
        cfiles = self.cultivar_files(receipt["files"])
        if cfiles:
            self.verify_version(identity, self.versions / identity)
        ifiles = self.placed(receipt["files"])
        idir = self.integration / identity
        for relative, expected in ifiles.items():
            if fingerprint(idir / relative) != expected:
                raise ValueError(f"retained integration file differs: {idir / relative}")
        return receipt

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
            self.verify_version(identity, self.runtime.parent / target)

    def ensure_cultivar_links(self, present):
        if not present:
            for rel, target in CULTIVAR_LINKS:
                path = self.root / rel
                if path.is_symlink() and path.readlink().as_posix() == target:
                    path.unlink()
                    sync_dir(path.parent)
            return
        for rel, target in CULTIVAR_LINKS:
            path = self.root / rel
            secure_directory(self.root, Path(rel).parent, create=True)
            if rel == "usr/share/doc/tamlinux" and path.is_dir() and not path.is_symlink():
                # Replace initial tam-bud doc directory with the unified scion symlink.
                shutil.rmtree(path)
                sync_dir(path.parent)
            atomic_symlink(path, target)

    def select_runtime(self, identity):
        if identity is None:
            self.ensure_cultivar_links(False)
            if self.runtime.is_symlink():
                self.runtime.unlink()
                sync_dir(self.runtime.parent)
            return
        cfiles = self.cultivar_files(self.manifest(identity)["files"])
        if cfiles:
            generation = self.versions / identity
            if not generation.is_dir():
                raise ValueError(f"cultivar generation is missing: {generation}")
            atomic_symlink(self.runtime, f"versions/{identity}")
            self.ensure_cultivar_links(True)

    @contextmanager
    def locked(self):
        secure_directory(self.root, STATE, create=True)
        with (self.state / "lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def retain(self, stage, digest):
        source = stage / "payload"
        receipt = verified_stage(stage, digest)
        secure_directory(self.root, self.manifests.relative_to(self.root), create=True)
        secure_directory(self.root, self.integration.relative_to(self.root), create=True)

        cfiles = self.cultivar_files(receipt["files"])
        ifiles = self.placed(receipt["files"])
        mpath = self.manifest_path(digest)
        generation = self.versions / digest
        idir = self.integration / digest

        already_retained = (
            mpath.is_file()
            and (not cfiles or generation.is_dir())
            and (not ifiles or idir.is_dir())
        )
        if already_retained:
            progress("Retaining stage (reusing verified generation)...")
            if self.verify_retained(digest) != receipt:
                raise ValueError("retained stage differs from the manifest")
            return

        progress(f"Importing cultivar ({len(cfiles)} cultivar, {len(ifiles)} integration files)...")
        if cfiles and not generation.is_dir():
            secure_directory(self.root, self.versions.relative_to(self.root), create=True)
            with tempfile.TemporaryDirectory(prefix=".incoming-", dir=self.versions) as tmp:
                tmp_path = Path(tmp)
                tree = tmp_path / "tree"
                mkdir_public(tree, tmp_path)
                csrc = source / PAYLOAD_CURRENT
                for relative, (mode, _) in sorted(cfiles.items()):
                    target = tree / relative
                    mkdir_public(target.parent, tmp_path)
                    copy_file(csrc / relative, target, mode, sync=False, direct=True)
                actual = {
                    p.relative_to(tree).as_posix(): fingerprint(p)
                    for p in sorted(tree.rglob("*"))
                    if not stat.S_ISDIR(p.lstat().st_mode)
                }
                if actual != cfiles:
                    raise ValueError("cultivar files changed during import")
                sync_fs(tree)
                tree.rename(generation)
                sync_dir(self.versions)

        if ifiles and not idir.is_dir():
            with tempfile.TemporaryDirectory(prefix=".int-", dir=self.integration) as tmp:
                tmp_path = Path(tmp)
                tree = tmp_path / "tree"
                mkdir_public(tree, tmp_path)
                for relative, (mode, _) in sorted(ifiles.items()):
                    target = tree / relative
                    mkdir_public(target.parent, tmp_path)
                    copy_file(source / relative, target, mode, sync=False, direct=True)
                sync_fs(tree)
                tree.rename(idir)
                sync_dir(self.integration)

        copy_file(stage / "manifest.json", mpath, 0o644, sync=True)
        if hashlib.sha256(mpath.read_bytes()).hexdigest() != digest:
            raise ValueError("stage manifest changed during import")

    def check(self, before, after, resuming=False, legacy_owned=frozenset()):
        for relative in sorted(before.keys() | after.keys()):
            if not allowed(relative) or ".." in Path(relative).parts:
                raise ValueError(f"invalid destination: {relative}")
            secure_directory(self.root, Path(relative).parent)
            target = self.root / relative
            found = fingerprint(target)
            alternatives = [before.get(relative)]
            if resuming:
                alternatives.append(after.get(relative))
            if relative in legacy_owned:
                continue
            if found not in alternatives:
                raise ValueError(f"unmanaged or modified destination: {target}")

    def check_ownership(self, files):
        if os.path.lexists(self.root / "var/lib/pacman"):
            prefix = PAYLOAD_CURRENT + "/"
            placed_paths = {name for name in files if not name.startswith(prefix)} | {rel for rel, _ in CULTIVAR_LINKS}
            problems = ownership_problems(self.root, placed_paths)
            if problems:
                raise ValueError("\n".join(problems))

    def check_switch(self, old, after, legacy_from=None):
        before = self.manifest(old)["files"]
        self.check_ownership(before.keys() | after.keys())
        self.check_runtime(self.runtime_id(old), None, False)
        legacy_owned = set()
        if legacy_from:
            legacy_owned = set(self.legacy_manifest(legacy_from)["files"])
        self.check(self.placed(before), self.placed(after), legacy_owned=legacy_owned)

    def runtime_id(self, identity):
        if identity and self.cultivar_files(self.manifest(identity)["files"]):
            return identity
        return None

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
        legacy_from = None
        if old is not None:
            self.verify_retained(old)
            rollback = {"kind": "source", "manifest": old}
        else:
            legacy = self.legacy_active()
            if legacy and legacy.get("current"):
                legacy_from = legacy["current"]
                rollback = {"kind": "legacy-source", "manifest": legacy_from}
            else:
                rollback = {"kind": "clean"}
        self.check_switch(old, receipt["files"], legacy_from=legacy_from)
        if os.path.lexists(self.pending) or self.current() != current:
            raise ValueError("the target changed during preparation; try again")
        return {"version": receipt["version"], "components": receipt["components"],
                "manifest": args.digest, "root": str(self.root),
                "rootIdentity": [root_info.st_dev, root_info.st_ino], "rollback": rollback}

    def start(self, old, new, legacy_from=None):
        self.check_switch(old, self.manifest(new)["files"], legacy_from=legacy_from)
        if old == new and not legacy_from:
            return
        record = {"from": old, "to": new}
        if legacy_from:
            record["legacy_from"] = legacy_from
        write_json(self.pending, record)
        self.complete()

    def complete(self, reverse=False):
        pending = read_json(self.pending)
        if pending is None:
            raise ValueError("no pending source installation")
        old, new = pending["from"], pending["to"]
        legacy_from = pending.get("legacy_from")
        if reverse:
            old, new = new, old
            legacy_from = None
        self.switch_files(old, new, legacy_from=legacy_from)
        self.finish({"current": new, "previous": old})

    def _cleanup_legacy_files(self, legacy_from, new_placed):
        legacy = self.legacy_active() or {}
        external = set(legacy.get("external", []))
        old_files = self.legacy_manifest(legacy_from)["files"]
        removed = 0
        for relative in sorted(old_files):
            if relative.startswith(LEGACY_CURRENT + "/") or relative in external or relative in new_placed:
                continue
            target = self.root / relative
            if target.is_file() or target.is_symlink():
                target.unlink()
                removed += 1
        legacy_link = self.root / LEGACY_CURRENT
        if legacy_link.is_symlink():
            legacy_link.unlink()
            sync_dir(legacy_link.parent)
        if removed:
            progress(f"Cleaned {removed} retired 0.6.35 scattered files.")

    def switch_files(self, old, new, legacy_from=None):
        before_all = self.manifest(old)["files"]
        after_all = self.manifest(new)["files"]
        if new is not None:
            self.verify_retained(new)
        self.check_ownership(before_all.keys() | after_all.keys())
        self.check_runtime(self.runtime_id(old), self.runtime_id(new), True)
        before, after = self.placed(before_all), self.placed(after_all)
        legacy_owned = set(self.legacy_manifest(legacy_from)["files"]) if legacy_from else frozenset()
        self.check(before, after, resuming=True, legacy_owned=legacy_owned)

        if legacy_from:
            self._cleanup_legacy_files(legacy_from, after)

        changed = False
        updated = 0
        for relative in sorted(before.keys() | after.keys()):
            target = self.root / relative
            if target.exists() and not target.is_symlink() and fingerprint(target) == after.get(relative):
                continue
            if relative in after:
                secure_directory(self.root, Path(relative).parent, create=True, sync=False)
                copy_file(self.integration / new / relative, target, after[relative][0], sync=False)
                updated += 1
            elif target.exists() or target.is_symlink():
                target.unlink()
                updated += 1
            changed = True
        if changed:
            progress(f"Updated {updated} integration files.")
            sync_target = self.root / "usr"
            sync_fs(sync_target if sync_target.is_dir() else self.root)
        self.select_runtime(self.runtime_id(new))

    def prune(self, active):
        keep = {active.get("current"), active.get("previous")} - {None}
        if self.versions.is_dir():
            for entry in self.versions.iterdir():
                if not entry.name.startswith(".") and entry.name not in keep and entry.is_dir():
                    shutil.rmtree(entry)
        if self.integration.is_dir():
            for entry in self.integration.iterdir():
                if not entry.name.startswith(".") and entry.name not in keep and entry.is_dir():
                    shutil.rmtree(entry)
        if self.manifests.is_dir():
            for entry in self.manifests.glob("*.json"):
                if entry.stem not in keep:
                    entry.unlink()

    def finish(self, active):
        write_json(self.active, active)
        self.pending.unlink()
        sync_dir(self.state)
        self.prune(active)

    def uninstall(self):
        current = self.current()
        if current["current"] is not None:
            self.start(current["current"], None)
        self.prune({"current": None, "previous": None})
        self.active.unlink(missing_ok=True)
        sync_dir(self.state)

    def current(self):
        return read_json(self.active) or {"current": None, "previous": None}


def main():
    os.umask(0o022)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "preview", "status", "resume", "rollback", "uninstall"])
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--digest")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--live-recovery", action="store_true")
    args = parser.parse_args()
    if args.plan is not None:
        if args.action != "install" or any((args.root, args.stage, args.digest)):
            raise ValueError("an install plan supplies the destination and stage")
        install_plan(args.plan)
        return
    if args.root is None:
        raise ValueError("an isolated root or an approved install plan is required")
    root = args.root.resolve(strict=True)
    live_recovery = (root == Path("/") and args.live_recovery
                     and args.action in ("resume", "rollback", "uninstall"))
    if not root.is_dir() or args.root.is_symlink() or (
        root == Path("/") and args.action != "preview" and not live_recovery
    ):
        raise ValueError("this development installer requires an isolated test root")
    if live_recovery:
        if os.geteuid() != 0:
            raise ValueError("live recovery requires root approval")
        check_console()
    root_info = root.stat()
    expected_root_uid = 0 if (root == Path("/") and args.action == "preview") else os.geteuid()
    if root_info.st_uid != expected_root_uid or root_info.st_mode & 0o022:
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
        if args.action == "install":
            if pending:
                raise ValueError("resume or roll back the pending installation")
            if not args.stage or not re.fullmatch("[0-9a-f]{64}", args.digest or ""):
                raise ValueError("install requires a stage and its SHA-256 manifest digest")
            legacy = system.legacy_active() if current["current"] is None else None
            legacy_from = legacy.get("current") if legacy else None
            system.retain(args.stage, args.digest)
            system.start(current["current"], args.digest, legacy_from=legacy_from)
        elif args.action == "resume":
            system.complete()
        elif args.action == "uninstall":
            if pending:
                raise ValueError("resume or roll back the pending installation before uninstalling")
            system.uninstall()
        elif pending:
            system.complete(reverse=True)
        elif current["current"] is not None:
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
    os.umask(0o022)
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
    rollback = target["rollback"]
    kind = rollback.get("kind") if isinstance(rollback, dict) else None
    if kind not in ("clean", "source", "legacy-source"):
        raise ValueError("unsupported rollback mode in approved install plan")
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
        current = system.current()
        pending = read_json(system.pending)
        if kind == "clean":
            if current not in ({"current": None, "previous": None},
                               {"current": digest, "previous": None}):
                raise ValueError("the approved target already has a different source install")
            if pending is not None:
                if pending != {"from": None, "to": digest}:
                    raise ValueError("a different source transaction is pending")
                system.complete()
                return
            system.check_switch(current["current"], receipt["files"])
            system.retain(stage, digest)
            system.start(current["current"], digest)
        elif kind == "legacy-source":
            old_legacy = rollback.get("manifest")
            if not re.fullmatch("[0-9a-f]{64}", old_legacy or ""):
                raise ValueError("the approved legacy manifest digest is invalid")
            if current["current"] == digest:
                return
            if current["current"] is not None:
                raise ValueError("the approved target already has a unified cultivar install")
            legacy = system.legacy_active()
            if not legacy or legacy.get("current") != old_legacy:
                raise ValueError("the approved legacy source install changed")
            if pending is not None:
                if pending.get("to") != digest:
                    raise ValueError("a different source transaction is pending")
                system.complete()
                return
            system.check_switch(None, receipt["files"], legacy_from=old_legacy)
            system.retain(stage, digest)
            system.start(None, digest, legacy_from=old_legacy)
        else:
            old = rollback.get("manifest")
            if not re.fullmatch("[0-9a-f]{64}", old or ""):
                raise ValueError("the approved previous manifest digest is invalid")
            if current["current"] not in (old, digest):
                raise ValueError("the approved target source install changed")
            if pending is not None:
                if pending.get("from") != old or pending.get("to") != digest:
                    raise ValueError("a different source transaction is pending")
                system.complete()
                return
            if current["current"] == digest:
                return
            system.check_switch(old, receipt["files"])
            system.retain(stage, digest)
            system.start(old, digest)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, tarfile.TarError) as exc:
        raise SystemExit(f"Tamlinux source install: {exc}")
