import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import preflight
from transaction import inventory, write_json


@unittest.skipUnless(Path("/usr/bin/pacman").is_file(), "requires native Pacman")
class RuntimePreflightTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.release = self.root / "usr/lib/os-release"
        self.release.parent.mkdir(parents=True)
        self.release.write_text("ID=arch\n")
        self.db = self.root / "var/lib/pacman/local"
        self.db.mkdir(parents=True)
        (self.db / "ALPM_DB_VERSION").write_text("9\n")

    def add_package(self, name, version, paths=()):
        entry = self.db / f"{name}-{version}"
        entry.mkdir()
        (entry / "desc").write_text(f"%NAME%\n{name}\n\n%VERSION%\n{version}\n\n")
        (entry / "files").write_text("%FILES%\n" + "\n".join(paths) + "\n\n")

    def test_missing_and_outdated_providers(self):
        self.add_package("hyprland", "0.55-1")
        problems = preflight.runtime_problems(self.root)
        self.assertIn("missing Arch package dependency: hyprland>=0.56", problems)
        self.assertIn("missing Arch package dependency: quickshell>=0.3", problems)
        self.assertIn("missing native executable /usr/bin/qs (Arch package: quickshell)", problems)

    def test_unsupported_host(self):
        self.release.write_text("ID=debian\n")
        self.assertIn("requires x86_64 Arch Linux", preflight.runtime_problems(self.root)[0])

    def test_default_cursor_needs_a_real_theme(self):
        index = self.root / "usr/share/icons/default/index.theme"
        index.parent.mkdir(parents=True)
        index.write_text("[Icon Theme]\nInherits=Adwaita\n")
        self.add_package("default-cursors", "3-1")
        missing_package = "missing Arch package dependency: adwaita-cursors"
        self.assertIn(missing_package, preflight.runtime_problems(self.root))
        self.add_package("adwaita-cursors", "51.0-1")
        cursor = "usr/share/icons/Adwaita/cursors/left_ptr"
        missing_file = f"missing native file /{cursor} (Arch package: adwaita-cursors)"
        self.assertIn(missing_file, preflight.runtime_problems(self.root))
        (self.root / cursor).parent.mkdir(parents=True)
        (self.root / cursor).touch()
        problems = preflight.runtime_problems(self.root)
        self.assertNotIn(missing_package, problems)
        self.assertNotIn(missing_file, problems)

    def test_native_command_cannot_be_satisfied_by_local_override(self):
        self.add_package("quickshell", "0.3.2-1", ("usr/bin/qs",))
        local = self.root / "home/user/.local/bin"
        local.mkdir(parents=True)
        (local / "qs").touch(mode=0o755)
        system = self.root / "usr/bin"
        system.mkdir()
        (system / "qs").symlink_to(local / "qs")
        with patch.dict(os.environ, {"PATH": str(local)}):
            self.assertIn("missing native executable /usr/bin/qs (Arch package: quickshell)",
                          preflight.runtime_problems(self.root))
        (system / "quickshell").touch(mode=0o755)
        (system / "qs").unlink()
        (system / "qs").symlink_to("quickshell")
        self.assertFalse(any("/usr/bin/qs " in p for p in preflight.runtime_problems(self.root)))

    def test_unreadable_database_fails_closed(self):
        shutil.rmtree(self.db)
        with self.assertRaisesRegex(ValueError, "cannot read the local Pacman database"):
            preflight.ownership_problems(self.root, ["usr/bin/tam"])

    def test_owned_destination_missing_from_disk(self):
        self.add_package("tam-nut", "0.14.0-1", ("usr/bin/start",))
        self.assertFalse((self.root / "usr/bin/start").exists())
        self.assertEqual(preflight.ownership_problems(self.root, ["usr/bin/start", "usr/bin/tam"]),
                         ["source destination /usr/bin/start is owned by Arch package tam-nut"])

    def test_install_refuses_missing_package_owned_console_launchers(self):
        installer = Path(__file__).resolve().with_name("transaction.py")
        stage = self.root / "stage"
        commands = stage / "payload/usr/bin"
        commands.mkdir(parents=True)
        for name in ("hi", "start"):
            (commands / name).write_text("#!/bin/sh\n")
            (commands / name).chmod(0o755)
        manifest = stage / "manifest.json"
        write_json(manifest, {"files": inventory(stage / "payload")})
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        for name in ("hi", "start"):
            with self.subTest(command=name):
                path = f"usr/bin/{name}"
                self.add_package("tam-nut", "0.14.0-1", (path,))
                result = subprocess.run([sys.executable, "-I", "-B", installer, "install",
                                         "--stage", stage, "--digest", digest, "--root", self.root],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn(f"source destination /{path} is owned by Arch package tam-nut",
                              result.stderr)
                self.assertFalse((self.root / "usr/bin").exists())
                shutil.rmtree(self.db / "tam-nut-0.14.0-1")

    def test_preview_is_read_only_and_checks_retained_rollback(self):
        installer = Path(__file__).resolve().with_name("transaction.py")
        providers = set(preflight.RUNTIME_COMMANDS.values()) | set(preflight.RUNTIME_FILES.values())
        for requirement in sorted(providers):
            name, _, version = requirement.partition(">=")
            if version or not any(item.startswith(name + ">=") for item in providers):
                self.add_package(name, (version or "1") + "-1")
        for path, mode in [(f"usr/bin/{name}", 0o755) for name in preflight.RUNTIME_COMMANDS] + [
            (name, 0o644) for name in preflight.RUNTIME_FILES
        ]:
            target = self.root / path
            if path.startswith("lib64/"):
                (self.root / "lib64").symlink_to("usr/lib")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch(mode=mode)
        stage = self.root / "stage"
        binary = stage / "payload/usr/bin/tam-test"
        binary.parent.mkdir(parents=True)
        binary.write_text("one")
        write_json(stage / "manifest.json", {"version": "0.0.1", "components": {},
                                             "files": inventory(stage / "payload")})
        digest = hashlib.sha256((stage / "manifest.json").read_bytes()).hexdigest()
        arguments = ["--stage", stage, "--digest", digest, "--root", self.root]

        def call(action):
            return subprocess.run([sys.executable, "-I", "-B", installer, action, *arguments],
                                  capture_output=True, text=True)

        result = call("preview")
        self.assertEqual(result.returncode, 0, result.stderr)
        target = json.loads(result.stdout)
        self.assertEqual(target["rollback"], {"kind": "clean"})
        state = self.root / "var/lib/tamlinux/source"
        self.assertFalse(state.exists())
        operator = self.root / "operator"
        operator.mkdir()
        checkout = installer.parents[2]
        shutil.copyfile(checkout / "Makefile", operator / "Makefile")
        scripts = operator / "desktop/source-install"
        scripts.mkdir(parents=True)
        for script in ("transaction.py", "preflight.py"):
            shutil.copyfile(installer.with_name(script), scripts / script)
        plan_file = operator / "plan.json"
        plan = {"host": os.uname().nodename, "target": target}
        stage = stage.rename(operator / digest)
        binary = stage / "payload/usr/bin/tam-test"

        def make_install():
            return subprocess.run(["/usr/bin/make", "install", f"SOURCE_PLAN={plan_file}"],
                                  cwd=operator, capture_output=True, text=True)

        write_json(plan_file, plan | {"host": ""})
        self.assertIn("host or root identity changed", make_install().stderr)
        write_json(plan_file, plan)
        binary.chmod(0o755)
        self.assertIn("stage files differ", make_install().stderr)
        binary.chmod(0o644)
        self.add_package("another-owner", "1-1", ("usr/bin/tam-test",))
        self.assertIn("is owned by Arch package another-owner", make_install().stderr)
        self.assertFalse((self.root / "usr/bin/tam-test").exists())
        shutil.rmtree(self.db / "another-owner-1-1")
        for _ in range(2):
            result = make_install()
            self.assertEqual(result.returncode, 0, result.stderr)
        arguments[1] = stage
        self.assertEqual(json.loads(call("preview").stdout)["rollback"],
                         {"kind": "source", "manifest": digest})
        # Also verify in-place source-to-source upgrade via SOURCE_PLAN.
        stage2 = self.root / "stage2"
        binary2 = stage2 / "payload/usr/bin/tam-test"
        binary2.parent.mkdir(parents=True)
        binary2.write_text("two")
        write_json(stage2 / "manifest.json", {"version": "0.0.2", "components": {},
                                              "files": inventory(stage2 / "payload")})
        digest2 = hashlib.sha256((stage2 / "manifest.json").read_bytes()).hexdigest()
        res2 = subprocess.run([sys.executable, "-I", "-B", installer, "preview",
                               "--stage", stage2, "--digest", digest2, "--root", self.root],
                              capture_output=True, text=True)
        self.assertEqual(res2.returncode, 0, res2.stderr)
        target2 = json.loads(res2.stdout)
        self.assertEqual(target2["rollback"], {"kind": "source", "manifest": digest})
        stage2 = stage2.rename(operator / digest2)
        plan2 = operator / "plan2.json"
        write_json(plan2, {"host": os.uname().nodename, "target": target2})
        res_up = subprocess.run(["/usr/bin/make", "install", f"SOURCE_PLAN={plan2}"],
                                cwd=operator, capture_output=True, text=True)
        self.assertEqual(res_up.returncode, 0, res_up.stderr)
        self.assertEqual((self.root / "usr/bin/tam-test").read_text(), "two")
        # Roll back to first stage before remaining checks.
        res_rb = subprocess.run([sys.executable, "-I", "-B", installer, "rollback", "--root", self.root],
                                capture_output=True, text=True)
        self.assertEqual(res_rb.returncode, 0, res_rb.stderr)
        self.assertEqual((self.root / "usr/bin/tam-test").read_text(), "one")
        pending = state / "pending.json"
        pending.write_text("{}")
        self.assertIn("pending installation", call("preview").stderr)
        pending.unlink()
        binary.chmod(0o755)
        self.assertIn("stage files differ", call("preview").stderr)
        binary.chmod(0o644)
        retained = state / digest / "payload/usr/bin/tam-test"
        retained.write_text("changed")
        self.assertIn("stage files differ", call("preview").stderr)
        self.assertFalse((state / "pending.json").exists())


class BuildPreflightTests(unittest.TestCase):
    def test_missing_tools_include_arch_packages(self):
        problems = preflight.build_problems({"PATH": "/nonexistent"})
        self.assertIn("cc (Arch package: gcc)", problems)
        self.assertIn("pkg-config (Arch package: pkgconf)", problems)

    def test_arch_packages_covers_build_and_runtime_providers(self):
        declared = {spec.split(">=", 1)[0].split("=", 1)[0] for spec in preflight.declared_packages()}
        required = (
            set(preflight.BUILD_COMMANDS.values())
            | {pkg for _, _, pkg in preflight.BUILD_HEADERS}
            | {"python-fonttools"}
            | {spec.split(">=", 1)[0] for spec in preflight.RUNTIME_COMMANDS.values()}
            | {spec.split(">=", 1)[0] for spec in preflight.RUNTIME_FILES.values()}
        ) - {"hyprland-plugin-hyprbars"}
        self.assertTrue(required <= declared, f"missing from arch-packages: {sorted(required - declared)}")
        self.assertIn("adwaita-cursors", declared)
        self.assertIn("foot", declared)
        self.assertIn("xdg-terminal-exec", declared)

    def test_render_version_notes_fails_closed_when_section_missing(self):
        import build
        changelog = "# Changelog\n\n## Unreleased\n\n- stale item\n"
        with self.assertRaisesRegex(ValueError, "no '## \\[0.6.32\\]' section"):
            build.render_version_notes(changelog, "0.6.32")
        notes = build.render_version_notes(
            "# Changelog\n\n## [0.6.32]\n\n- real fix\n\n## Unreleased\n\n- stale\n",
            "0.6.32",
        )
        self.assertTrue(notes.startswith("Tamlinux 0.6.32 version notes\n\n- real fix\n"))
