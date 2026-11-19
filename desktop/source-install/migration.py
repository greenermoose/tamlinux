"""Coordinate the format-2 bundle and source journals in an isolated root."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

from transaction import (PAYLOAD_CURRENT, bootstrap_launchers, copy_file, fingerprint, inventory,
                         read_json, secure_directory, sync_dir, write_json)

BUNDLE_TOOL = "/usr/bin/tam-bundle"
SESSION_HELPER = "share/tamlinux/session/session_settings.py"
DOCS = {"info": "info", "tldr": "tldr", "archwiki": "arch-wiki"}


def archive_records(archive, bundle_hash):
    records = {}
    with tarfile.open(archive, "r|*") as packed:
        for item in packed:
            if item.name == "capture" or item.name.startswith("capture/"):
                raise ValueError("recovery requires a public bundle archive")
            if item.name in ("BUNDLE", "MANIFEST"):
                if not item.isfile() or item.name in records or item.size > 32 * 1024 * 1024:
                    raise ValueError("invalid bundle archive records")
                records[item.name] = packed.extractfile(item).read().decode().splitlines()
    metadata = records.get("BUNDLE", [])
    if "format 2" not in metadata or f"hash {bundle_hash}" not in metadata:
        raise ValueError("archive does not contain the exact format-2 bundle")
    return metadata, records["MANIFEST"]


def legacy_files(manifest, metadata, selected, borrowed):
    declared = {line.removeprefix("optional-doc ") for line in metadata
                if line.startswith("optional-doc ")}
    omitted = tuple("usr/share/doc/" + DOCS[name] + "/" for bit, name in enumerate(DOCS)
                    if name in declared and not (selected & ~borrowed & (1 << bit)))
    files = {}
    for line in manifest:
        if line.startswith("p f "):
            _, _, mode, digest, path = line.split(" ", 4)
            if not path.startswith(omitted):
                files[path] = [int(mode, 8), digest.removeprefix("sha256:")]
    return files


class BundleMigration:
    def __init__(self, installation, manage_session=True):
        self.system = installation
        self.manage_session = manage_session

    def command(self, *args, codes=(0,), settings=None):
        command = [BUNDLE_TOOL, "--root", str(self.system.root), *map(str, args)]
        env = {"PATH": "/usr/bin", "LC_ALL": "C"}
        if settings:
            env["HOME"] = str(settings.home)
        result = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE)
        if result.returncode not in codes:
            raise subprocess.CalledProcessError(result.returncode, command)
        return result.stdout

    def status(self):
        fields = {}
        for line in self.command("status", codes=(0, 4)).splitlines():
            key, separator, value = line.partition(": ")
            if separator and key in ("live", "bundle-hash", "state", "transaction",
                                     "from", "to", "target-hash"):
                if key in fields:
                    raise ValueError("ambiguous bundle status")
                fields[key] = value
        if "live" not in fields:
            raise ValueError("missing bundle status")
        return fields

    def documentation(self):
        path = self.system.root / "var/lib/tamlinux/documentation"
        if fingerprint(path) is None:
            return [0, 0]
        lines = path.read_text().splitlines()
        values = []
        for key in ("selected", "borrowed"):
            matches = [line for line in lines if line.startswith(key + " ")]
            if len(matches) != 1 or not re.fullmatch(key + r" [0-7]", matches[0]):
                raise ValueError("invalid bundle documentation receipt")
            values.append(int(matches[0][-1]))
        if values[1] & ~values[0]:
            raise ValueError("invalid borrowed bundle documentation")
        return values

    def archive(self, checksum):
        return self.system.state / f"bundle-{checksum}.tbundle"

    def live_matches(self, status, bundle):
        return (status["live"] == bundle["id"] and status.get("bundle-hash") == bundle["hash"]
                and status.get("state", "complete") == "complete")

    def user_settings(self):
        # In recovery the original checkout may be gone.
        sys.path.append(str(Path(__file__).resolve().parents[1] / "migration"))
        from session_settings import SessionSettings
        settings = SessionSettings()
        if any(path.is_relative_to(self.system.state.parent) for path in
               (settings.home, settings.config, settings.state)):
            raise ValueError("session settings must stay outside system state")
        return settings

    def inspect(self, after, archive, checksum, bundle_hash, bundle_id=None):
        if self.system.current()["current"] is not None:
            raise ValueError("a source installation is already active")
        if (archive is None or not re.fullmatch("[0-9a-f]{64}", checksum or "")
                or not re.fullmatch("sha256:[0-9a-f]{64}", bundle_hash or "")):
            raise ValueError("migration requires the recorded archive SHA-256 and full bundle hash")
        secure_directory(self.system.root, "usr/lib/tamlinux")
        status = self.status()
        bundle = {"id": status["live"] if bundle_id is None else bundle_id,
                  "hash": bundle_hash, "archive": checksum}
        if not self.live_matches(status, bundle):
            raise ValueError("the live bundle differs from the requested recovery bundle")
        self.command("check")
        selected, borrowed = self.documentation()
        bundle["documentation"] = [selected, borrowed]

        if (fingerprint(archive) or [None, None])[1] != checksum:
            raise ValueError("recovery archive checksum differs")
        self.command("needs", archive)
        metadata, manifest = archive_records(archive, bundle_hash)
        if (fingerprint(archive) or [None, None])[1] != checksum:
            raise ValueError("recovery archive changed while checking it")
        before = legacy_files(manifest, metadata, selected, borrowed)
        external = bootstrap_launchers(self.system.root)
        if not set(external) <= after.keys():
            raise ValueError("the source stage must provide both console launchers")
        self.system.check_ownership(before.keys() | after.keys(), external)
        self.system.check_runtime(None, None, False)
        placed = self.system.placed(after, external)
        self.system.check({path: before[path] for path in placed.keys() & before.keys()}, placed)
        if self.manage_session and f"{PAYLOAD_CURRENT}/{SESSION_HELPER}" in after:
            settings = self.user_settings()
            self.command("session-ready", settings=settings)
            bundle["session"] = settings.identity
        return bundle

    def start(self, target, archive, checksum, bundle_hash):
        after = self.system.manifest(target)["files"]
        bundle = self.inspect(after, archive, checksum, bundle_hash)
        saved = self.archive(checksum)
        if not os.path.lexists(saved):
            copy_file(archive, saved, 0o600)
        self.verify_archive(bundle)
        external = bootstrap_launchers(self.system.root)

        prefix = self.system.state / target / "payload" / PAYLOAD_CURRENT
        if self.manage_session and "session" in bundle:
            settings = self.user_settings()
            with settings.locked():
                self.command("session-ready", settings=settings)
                settings.prepare(target, bundle_hash, prefix / "defaults/home")

        self.retain_recovery_program()
        pending = {"from": None, "to": target, "migration": "detach",
                   "bundle": bundle | {"source": target}, "external": external}
        write_json(self.system.pending, pending)
        self.complete(pending)

    def retain_recovery_program(self):
        # Publish the cooperating modules together before arming detach.
        source = Path(__file__).resolve().parent
        destination = self.system.state / "recovery"
        secure_directory(self.system.root, destination.relative_to(self.system.root))
        modules = ("transaction.py", "preflight.py", "migration.py", "session_settings.py", "engine.py")
        origins = {name: source / name for name in modules}
        if not origins["engine.py"].exists():
            origins["engine.py"] = source.parent / "migration/engine.py"
        if destination.exists():
            if any((fingerprint(destination / name) or [None, None])[1] !=
                   fingerprint(origins[name])[1] for name in modules):
                raise ValueError("retained recovery program differs from this installer")
            return
        with tempfile.TemporaryDirectory(prefix="recovery-", dir=self.system.state) as temporary:
            for name in modules:
                copy_file(origins[name], Path(temporary) / name, 0o600)
            Path(temporary).rename(destination)
            sync_dir(self.system.state)

    def verify_archive(self, bundle):
        archive = self.archive(bundle["archive"])
        if fingerprint(archive) != [0o600, bundle["archive"]]:
            raise ValueError("retained recovery archive checksum differs")
        # needs also verifies the archive before checking its native contract.
        self.command("needs", archive)

    def detach(self, bundle):
        status = self.status()
        if (status["live"] == "-" and status.get("state") == "complete"
                and status.get("from") == bundle["id"] and status.get("to") == "-"):
            self.system.require_detached_slot()
            return
        if not (self.live_matches(status, bundle) or
                (status.get("from") == bundle["id"] and status.get("to") == "-"
                 and status["live"] in (bundle["id"], "-"))):
            raise ValueError("unexpected bundle transaction during detach")
        self.command("detach", bundle["hash"])
        self.system.require_detached_slot()

    def restore(self, bundle):
        status = self.status()
        if not self.live_matches(status, bundle):
            phase = status.get("state", "complete")
            if phase == "complete":
                if status["live"] != "-":
                    raise ValueError("another bundle is active during recovery")
            elif (status.get("to") != bundle["id"] or status.get("from") != "-"
                  or phase != "staging" and status.get("target-hash") != bundle["hash"]):
                raise ValueError("unexpected bundle transaction during recovery")
            if phase in ("complete", "staging"):
                selected = bundle["documentation"][0]
                docs = ",".join(name for bit, name in enumerate(DOCS) if selected & (1 << bit))
                self.command("restore", self.archive(bundle["archive"]), "--expect-bundle",
                             bundle["hash"], "--docs", docs or "none")
                status = self.status()
            self.command("apply", status["transaction"])
        if not self.live_matches(self.status(), bundle) or self.documentation() != bundle["documentation"]:
            raise ValueError("the exact bundle and documentation selection did not return")
        self.command("check")

    def advance(self, pending, phase):
        updated = pending | {"migration": phase}
        write_json(self.system.pending, updated)
        return updated

    def complete(self, pending, reverse=False):
        bundle = pending["bundle"]
        if not self.manage_session or "session" not in bundle:
            self.complete_system(pending, reverse, None)
            return
        settings = self.user_settings()
        if settings.identity != bundle["session"]:
            raise ValueError("resume this migration as the original user with the same XDG roots")
        with settings.locked():
            self.complete_system(pending, reverse, settings)

    def complete_system(self, pending, reverse, settings):
        bundle = pending["bundle"]
        target = bundle["source"]
        external = pending["external"]
        phase = pending["migration"]
        self.verify_archive(bundle)
        files = self.system.manifest(target)["files"]
        self.system.check_ownership(files, external)
        if phase == "detach":
            if inventory(self.system.state / target / "payload") != files:
                raise ValueError("retained stage changed before detach")
            if settings and not reverse:
                settings.verify_prepared(target, bundle["hash"])
            self.detach(bundle)
            phase = "remove" if reverse else "install"
            pending = self.advance(pending, phase)
        if phase == "install" and reverse:
            phase = "remove"
            pending = self.advance(pending, phase)
        if phase == "install":
            self.system.require_detached_slot()
            self.system.switch_files(None, target, external)
            if settings:
                settings.apply(target, bundle["hash"])
            self.system.finish({"current": target, "previous": None,
                                "bundle": bundle, "external": external})
            return
        if phase == "remove":
            self.system.require_detached_slot()
            self.system.switch_files(target, None, external)
            self.advance(pending, "restore")
            phase = "restore"
        if phase != "restore":
            raise ValueError("unknown source migration phase")
        if settings:
            settings.rollback(target, bundle["hash"])
        self.restore(bundle)
        if settings:
            if not self.bundle_session_ready(settings):
                # Rebind exact restored settings to the new bundle system ID.
                capture = pending.get("restoredCapture")
                if capture is None:
                    output = self.command("capture", settings=settings)
                    match = re.search(r"^private settings capture: ([A-Za-z0-9@_.-]+)(?: \(incomplete\))?$",
                                      output, re.MULTILINE)
                    if not match:
                        raise ValueError("bundle settings capture has no recovery identity")
                    capture = match[1]
                    write_json(self.system.pending, pending | {"restoredCapture": capture})
                self.command("prepare-settings", capture, settings=settings)
                self.command("apply-settings", settings=settings)
                self.command("session-ready", settings=settings)
        self.system.finish({"current": None, "previous": None})

    def bundle_session_ready(self, settings):
        try:
            self.command("session-ready", settings=settings)
        except subprocess.CalledProcessError as error:
            if error.returncode != 4:
                raise
            return False
        return True

    def rollback(self):
        pending = read_json(self.system.pending)
        if pending is None:
            current = self.system.current()
            bundle = current.get("bundle")
            if not bundle or current["current"] != bundle["source"]:
                raise ValueError("return to the first source installation before bundle rollback")
            self.system.require_detached_slot()
            external = current["external"]
            files = self.system.manifest(bundle["source"])["files"]
            self.verify_archive(bundle)
            self.system.check_ownership(files, external)
            self.system.check_runtime(self.system.runtime_id(bundle["source"]), None, False)
            self.system.check(self.system.placed(files, external), {})
            pending = {"from": bundle["source"], "to": None, "migration": "remove",
                       "bundle": bundle, "external": external}
            write_json(self.system.pending, pending)
        elif "migration" not in pending:
            raise ValueError("finish the pending source upgrade before bundle rollback")
        self.complete(pending, reverse=True)
