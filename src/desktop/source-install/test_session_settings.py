"""Exercise source session preparation with isolated user and system paths."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from build import COMPONENTS, PRODUCT
from session_settings import REQUIRED, SessionSettings, run_cli
from transaction import Installation, PAYLOAD_CURRENT, inventory, write_json

SESSION_HELPER = "share/tamlinux/session/session_settings.py"


def source_fixture(stage):
    runtime = stage / "payload" / PAYLOAD_CURRENT
    session = runtime / SESSION_HELPER
    session.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PRODUCT / "src/desktop/source-install/session_settings.py", session)
    defaults = runtime / "defaults/home/.config"
    for relative, text in zip(REQUIRED, (
        'dofile("/usr/lib/tamlinux/current/share/tamlinux/session/entry.lua")\n',
        'local code, err = tp.read_file("/usr/lib/tamlinux/current/share/tamlinux/session/tam-pane.lua")\n'
        'assert(code, err)\n'
        'assert(load(code, "@/usr/lib/tamlinux/current/share/tamlinux/session/tam-pane.lua", "t"))()\n',
        '. /usr/lib/tamlinux/current/share/tamlinux/session/uwsm-env\n',
    ), strict=True):
        path = defaults / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    shutil.copytree(PRODUCT / "src/desktop/user-defaults", runtime / "share/tamlinux/user-defaults")
    for path in runtime.rglob("*"):
        if path.is_file():
            path.chmod(0o644)


def local_make_install(base, root, stage):
    """Verify the public Make entry with a complete, disposable lock."""
    base.mkdir()
    checkout = base / "tamlinux"
    rules = checkout / "src/desktop/source-install"
    rules.mkdir(parents=True)
    shutil.copyfile(PRODUCT / "Makefile", checkout / "Makefile")
    for file in ("main.py", "build.py", "transaction.py", "preflight.py"):
        shutil.copyfile(PRODUCT / "src/desktop/source-install" / file, rules / file)

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

    def test_hyprland_starts_with_tam_pane_configuration_unavailable(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / "home"
            home.mkdir()
            config = home / "settings"
            config.mkdir()
            root = base / "root"
            root.mkdir()
            stage = base / "first"
            source_fixture(stage)
            # Remove tam-pane.lua from defaults too so recovery works even if defaults lack it.
            (stage / "payload" / PAYLOAD_CURRENT / "defaults/home/.config/tamlinux/session/tam-pane.lua").unlink()
            system = Installation(root)
            local_make_install(base / "clones", root, stage)
            env = {"HOME": str(home), "XDG_CONFIG_HOME": str(config)}
            with patch.dict(os.environ, env, clear=True):
                defaults = system.runtime / "defaults/home"
                settings = SessionSettings()
                pane_cfg = config / "tamlinux/session/tam-pane.lua"
                with patch("session_settings.reload_units"):
                    # Missing tam-pane.lua in both user config and defaults must not block Hyprland.
                    settings.ready(defaults, system.active, system.pending, session="hyprland")
                    # Broken symlink, empty file, or retired path at tam-pane.lua must not block Hyprland.
                    pane_cfg.symlink_to(home / "does-not-exist")
                    settings.ready(defaults, system.active, system.pending, session="hyprland")
                    pane_cfg.unlink()
                    pane_cfg.write_text("")
                    settings.ready(defaults, system.active, system.pending, session="hyprland")
                    pane_cfg.write_text('dofile("/nix/store/retired/tam-pane.lua")\n')
                    settings.ready(defaults, system.active, system.pending, session="hyprland")
                    # Pane session itself still fails closed when tam-pane.lua is invalid.
                    with self.assertRaisesRegex(ValueError, "tam-pane.lua"):
                        settings.ready(defaults, system.active, system.pending, session="pane")
                    # Valid tam-pane.lua allows pane session even if hyprland.lua is empty.
                    pane_cfg.write_text('tp.config{}\n')
                    (config / "tamlinux/session/hyprland.lua").write_text("")
                    settings.ready(defaults, system.active, system.pending, session="pane")
                with self.assertRaises(ValueError):
                    settings.ready(defaults, system.active, system.pending, session="sway")

    def test_run_cli_accepts_optional_session_flag(self):
        for flag, expected in (([], None), (["--session", "hyprland"], "hyprland"), (["--session", "pane"], "pane")):
            with self.subTest(flag=flag), patch.object(SessionSettings, "ready") as ready, \
                    patch("session_settings.SessionSettings.__init__", return_value=None):
                run_cli(flag)
            self.assertEqual(ready.call_args.kwargs["session"], expected)
        for bad in (["--session"], ["--session", "sway"], ["--unknown"]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                run_cli(bad)
