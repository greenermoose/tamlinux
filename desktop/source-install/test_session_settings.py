"""Exercise source session preparation with isolated user and system paths."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from build import COMPONENTS, PRODUCT
from migration import SESSION_HELPER
from transaction import Installation, PAYLOAD_CURRENT, inventory, write_json

sys.path.append(str(PRODUCT / "desktop/migration"))
from session_settings import REQUIRED, SessionSettings


def source_fixture(stage):
    runtime = stage / "payload" / PAYLOAD_CURRENT
    session = runtime / SESSION_HELPER
    session.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PRODUCT / "desktop/source-install/session_settings.py", session)
    defaults = runtime / "defaults/home/.config"
    for relative, text in zip(REQUIRED, (
        'dofile("/usr/lib/tamlinux/source/current/share/tamlinux/session/entry.lua")\n',
        '. /usr/lib/tamlinux/source/current/share/tamlinux/session/uwsm-env\n',
    ), strict=True):
        path = defaults / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    shutil.copytree(PRODUCT / "desktop/user-defaults", runtime / "share/tamlinux/user-defaults")
    # Use regular staged files with safe modes, as the product install does.
    for path in runtime.rglob("*"):
        if path.is_file():
            path.chmod(0o644)


def local_make_install(base, root, stage):
    """Verify the public Make entry with a complete, disposable lock."""
    base.mkdir()
    checkout = base / "tamlinux"
    rules = checkout / "desktop/source-install"
    rules.mkdir(parents=True)
    shutil.copyfile(PRODUCT / "Makefile", checkout / "Makefile")
    for file in ("main.py", "build.py", "transaction.py", "preflight.py", "migration.py"):
        shutil.copyfile(PRODUCT / "desktop/source-install" / file, rules / file)

    def commit(directory):
        def git(*args):
            return subprocess.check_output(["/usr/bin/git", "-C", directory, "-c",
                                            "user.name=Test", "-c", "user.email=test@example.invalid",
                                            "-c", "commit.gpgsign=false", *args], text=True).strip()
        git("init", "--quiet")
        git("add", "--all")
        git("commit", "--quiet", "--allow-empty", "-m", "Fixture")
        return git("rev-parse", "HEAD")

    commits = {}
    for name in COMPONENTS:
        (base / name).mkdir()
        commits[name] = commit(base / name)
    (checkout / "components.lock").write_text("".join(f"{name} {rev}\n" for name, rev in commits.items()))
    commits["tamlinux"] = commit(checkout)
    manifest = stage / "manifest.json"
    write_json(manifest, {"version": stage.name, "components": commits, "files": inventory(stage / "payload")})
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    build = base / "build"
    (build / "stages").mkdir(parents=True)
    stage.rename(build / "stages" / digest)
    (build / "build").symlink_to(build / "stages" / digest)
    subprocess.run(["/usr/bin/make", "install", f"SOURCE_ROOT={root}", f"SOURCE_BUILD={build}"],
                   cwd=checkout, check=True, stdout=subprocess.PIPE)
    return digest


class SourceSessionTests(unittest.TestCase):
    def test_clean_make_install_and_retry_reload(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / "home"
            home.mkdir()
            config = home / "settings"
            config.mkdir()
            shell = home / ".bashrc"
            shell.write_text("# existing shell setup\n")
            flags = config / "chromium-flags.conf"
            flags.symlink_to(home / "external-flags")
            root = base / "root"
            root.mkdir()
            stage = base / "first"
            source_fixture(stage)
            system = Installation(root)
            local_make_install(base / "clones", root, stage)
            env = {"HOME": str(home), "XDG_CONFIG_HOME": str(config)}
            with patch.dict(os.environ, env, clear=True):
                defaults = system.runtime / "defaults/home"
                settings = SessionSettings()
                with patch("session_settings.reload_units", side_effect=subprocess.CalledProcessError(1, "reload")):
                    with self.assertRaises(subprocess.CalledProcessError):
                        settings.ready(defaults, system.active, system.pending)
                with patch("session_settings.reload_units") as reload_units:
                    settings.ready(defaults, system.active, system.pending)
                    settings.ready(defaults, system.active, system.pending)
                reload_units.assert_called_once()
                self.assertTrue(flags.is_symlink())
                self.assertEqual(shell.read_text().count("# existing shell setup"), 1)
                self.assertEqual(shell.read_text().count("# >>> tamlinux env >>>"), 1)
                self.assertEqual((config / REQUIRED[0]).stat().st_uid, os.getuid())
                write_json(system.pending, {"test": True})
                with self.assertRaisesRegex(ValueError, "installation is incomplete"):
                    settings.ready(defaults, system.active, system.pending)

    def test_cli_prepare_apply_rollback_round_trip(self):
        from session_settings import run_cli
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / "home"
            config = home / ".config"
            state = home / ".local/state"
            (config / "tamlinux/session").mkdir(parents=True)
            (config / "uwsm/env.d").mkdir(parents=True)
            hypr = config / "tamlinux/session/hyprland.lua"
            envf = config / "uwsm/env.d/10-tamlinux.sh"
            hypr_before = 'dofile("/usr/lib/tamlinux/current/share/tamlinux/session/entry.lua")\n'
            envf_before = '. /usr/lib/tamlinux/current/share/tamlinux/session/uwsm-env\n'
            hypr.write_text(hypr_before)
            envf.write_text(envf_before)
            defaults = base / "defaults"
            (defaults / ".config").mkdir(parents=True)
            digest = "a" * 64
            bhash = "sha256:" + "b" * 64
            env = {"HOME": str(home), "XDG_CONFIG_HOME": str(config), "XDG_STATE_HOME": str(state)}
            with patch.dict(os.environ, env, clear=True):
                run_cli(["prepare", "--digest", digest, "--bundle-hash", bhash,
                         "--defaults", str(defaults), "--skip-bundle-check"])
                self.assertEqual(hypr.read_text(), hypr_before)
                run_cli(["apply", "--digest", digest, "--bundle-hash", bhash])
                self.assertIn("/usr/lib/tamlinux/source/current/", hypr.read_text())
                self.assertIn("/usr/lib/tamlinux/source/current/", envf.read_text())
                run_cli(["rollback", "--digest", digest, "--bundle-hash", bhash])
                self.assertEqual(hypr.read_text(), hypr_before)
                self.assertEqual(envf.read_text(), envf_before)
