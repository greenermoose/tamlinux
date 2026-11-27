"""Native product installation stays under its prefix and is reproducible."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install_product", SOURCE / "src/desktop/install-product.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
layout_spec = importlib.util.spec_from_file_location("install_cultivar_layout", SOURCE / "src/desktop/install-cultivar-layout.py")
cultivar_layout = importlib.util.module_from_spec(layout_spec)
layout_spec.loader.exec_module(cultivar_layout)


class ProductInstall(unittest.TestCase):
    def test_cultivar_layout_supplies_console_launchers(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            installer.install(cultivar_layout.CURRENT, tmp)
            runtime = stage / cultivar_layout.CURRENT.lstrip("/")
            commands = runtime / "bin"
            for name in ("hi", "start"):
                (commands / name).write_text("#!/bin/sh\n")
                (commands / name).chmod(0o755)
            cultivar_layout.install(stage)
            self.assertEqual((commands / "hi").read_text(), '#!/bin/sh\nexec /usr/bin/tam hi "$@"\n')
            self.assertTrue(os.access(commands / "hi", os.X_OK))
            self.assertTrue(os.access(commands / "start", os.X_OK))
            self.assertTrue(os.access(commands / "tam-start", os.X_OK))
            self.assertFalse((commands / "tam-nut").exists())
            self.assertTrue((runtime / "share/tamlinux/session/session_settings.py").is_file())
            self.assertTrue((runtime / "share/tamlinux/session/tam-pane.lua").is_file())
            for launcher, session_name in (("tam-hyprland-session", "hyprland"), ("tam-pane-session", "pane")):
                launch = (commands / launcher).read_text()
                self.assertLess(launch.index("wait-stopped.py"), launch.index(f"session_settings.py\" --session {session_name}"))
                self.assertLess(launch.index("session_settings.py"), launch.index("exec /usr/bin/uwsm"))
                self.assertIn('"/usr/bin/tamlinux/tam-session-init"', launch)
                if session_name == "pane":
                    self.assertIn('"/usr/bin/tamlinux/tam-macro" sync --pane-only', launch)
                subprocess.run(["/usr/bin/sh", "-n", commands / launcher], check=True)

    def test_benchmark_installs_in_the_cultivar_bin(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([
                "make", "-s", "-C", SOURCE / "src/commands/tam-session-bench",
                "install", f"PREFIX={cultivar_layout.CURRENT}", f"DESTDIR={tmp}",
            ], check=True)
            command = Path(tmp) / cultivar_layout.CURRENT.lstrip("/") / "bin/tam-session-bench"
            result = subprocess.run([command, "compare", "--help"], check=True,
                                    capture_output=True, text=True)
            self.assertIn("--since", result.stdout)
            self.assertIn("--label", result.stdout)

    def test_cultivar_layout_renders_private_paths_and_integration_dropins(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            installer.install(cultivar_layout.CURRENT, tmp)
            current = stage / cultivar_layout.CURRENT.lstrip("/")
            commands = current / "bin"
            command = commands / "tam-shell"
            command.write_bytes((SOURCE / "src/commands/tam-shell/tam-shell").read_bytes())
            command.chmod(0o755)
            dns_command = commands / "tam-dns"
            dns_command.write_bytes((SOURCE / "src/commands/tam-dns/tam-dns").read_bytes())
            dns_command.chmod(0o755)
            for name in ("hi", "start", "tam-suspend-unless-stay-awake"):
                original = commands / name
                original.write_text("#!/bin/sh\n")
                original.chmod(0o755)
            cultivar_layout.install(stage)
            defaults = current / "defaults/home"
            self.assertEqual((defaults / ".config/tamlinux/session/hyprland.lua").read_text(),
                'dofile("/usr/lib/tamlinux/current/share/tamlinux/session/entry.lua")\n')
            self.assertEqual((defaults / ".config/tamlinux/session/tam-pane.lua").read_text(), (
                'local code, err = tp.read_file("/usr/lib/tamlinux/current/share/tamlinux/session/tam-pane.lua")\n'
                'assert(code, err)\n'
                'assert(load(code, "@/usr/lib/tamlinux/current/share/tamlinux/session/tam-pane.lua", "t"))()\n'
            ))
            wayland_entry = stage / "usr/share/wayland-sessions/tam-pane.desktop"
            self.assertTrue(wayland_entry.is_file())
            self.assertIn("Exec=/usr/lib/tamlinux/current/bin/tam-pane-session\n", wayland_entry.read_text())
            self.assertIn("TryExec=/usr/lib/tamlinux/current/bin/tam-pane\n", wayland_entry.read_text())
            self.assertIn("DesktopNames=tam-pane\n", wayland_entry.read_text())
            environment = (defaults / ".config/uwsm/env.d/10-tamlinux.sh").read_text()
            self.assertIn('export TAMLINUX_QUICKSHELL=/usr/bin/quickshell\n', environment)
            self.assertNotIn('/nix/store', environment)
            hypr_portals = (defaults / ".config/xdg-desktop-portal/hyprland-portals.conf").read_text()
            self.assertIn("default=hyprland;gtk\n", hypr_portals)
            self.assertIn("org.freedesktop.impl.portal.FileChooser=gtk\n", hypr_portals)
            pane_portals = (defaults / ".config/xdg-desktop-portal/tam-pane-portals.conf").read_text()
            self.assertIn("default=gtk\n", pane_portals)
            self.assertIn("org.freedesktop.impl.portal.ScreenCast=wlr\n", pane_portals)
            self.assertIn("org.freedesktop.impl.portal.Screenshot=wlr\n", pane_portals)
            self.assertIn("org.freedesktop.impl.portal.FileChooser=gtk\n", pane_portals)
            self.assertIn("org.freedesktop.impl.portal.Inhibit=none\n", pane_portals)
            for browser in ('chromium', 'google-chrome', 'BraveSoftware/Brave-Browser', 'microsoft-edge-dev'):
                host = json.loads((defaults / f'.config/{browser}/NativeMessagingHosts/org.tamlinux.copy_url.json').read_text())
                self.assertEqual(host['path'], '/usr/bin/tamlinux/tam-chromium-copy-url-host')
                self.assertEqual(host['allowed_origins'], ['chrome-extension://bgpiichlckmfanooecilcjemknkcpngb/'])
            self.assertTrue((defaults / '.config/tamlinux/menu/default.jsonc').is_file())
            self.assertTrue((defaults / '.config/tamlinux/chromium/extensions/copy-url/manifest.json').is_file())
            flags = (defaults / '.config/chromium-flags.conf').read_text()
            self.assertIn('/usr/lib/tamlinux/current/share/tamlinux/browser/extensions/copy-url', flags)
            for path in defaults.rglob('*'):
                if path.is_file():
                    self.assertNotIn(b'/nix/store/', path.read_bytes(), str(path))
            self.assertTrue((current / "share/tamlinux/shell/shell.qml").is_file())
            self.assertIn("/usr/lib/tamlinux/current/share/tamlinux/shell", command.read_text())
            dns_rendered = dns_command.read_text()
            self.assertIn("/usr/lib/tamlinux/current/share/tamlinux/native/dns_recovery.py", dns_rendered)
            self.assertIn("/usr/lib/tamlinux/versions/*/bin/tam-dns", dns_rendered)
            self.assertTrue(os.access(commands / "tam-start", os.X_OK))
            self.assertTrue(os.access(commands / "tam-suspend-unless-stay-awake", os.X_OK))
            desktop = (commands / "tam-desktop").read_text()
            self.assertIn("/var/lib/tamlinux/pending.json", desktop)
            self.assertNotIn("tam-bundle", desktop)
            unit = stage / "usr/lib/systemd/user/tamlinux-shell.service"
            self.assertIn("/usr/lib/tamlinux/current/share/tamlinux/shell", unit.read_text())
            wants = unit.parent / "graphical-session.target.d/50-tamlinux-services.conf"
            self.assertEqual(
                wants.read_text(),
                "[Unit]\nWants=tam-bt-agent.service tam-crash-watch.service tam-fcitx5.service tamlinux-shell.service\n",
            )
            timer_wants = unit.parent / "timers.target.d/50-tamlinux-services.conf"
            self.assertEqual(
                timer_wants.read_text(),
                "[Unit]\nWants=tamlinux-protocol-shadow-collect.timer\n",
            )
            self.assertTrue((stage / "etc/profile.d/tamlinux.sh").is_file())
            profile_text = (stage / "etc/profile.d/tamlinux.sh").read_text()
            self.assertIn("/usr/bin/tamlinux", profile_text)
            self.assertIn("/usr/lib/tamlinux/current/bin", profile_text)
            self.assertNotIn("MANPATH=", profile_text)
            self.assertTrue((stage / "usr/lib/environment.d/10-tamlinux-path.conf").is_file())
            self.assertIn("/usr/lib/tamlinux/current/bin",
                          (stage / "usr/lib/environment.d/10-tamlinux-path.conf").read_text())
            self.assertTrue((current / "share/tamlinux/console/tamlinux-vt.vtrgb").is_file())
            self.assertTrue((current / "share/tamlinux/console/tamlinux-vt-prtsc.map").is_file())
            sys_units = stage / "usr/lib/systemd/system"
            self.assertTrue((sys_units / "kbrequest.target").is_file())
            self.assertTrue((sys_units / "tam-vt-keymap.service").is_file())
            self.assertTrue((sys_units / "tam-vt-screenshot.service").is_file())
            self.assertIn("/usr/lib/tamlinux/current/share/tamlinux/console/tamlinux-vt-prtsc.map",
                          (sys_units / "tam-vt-keymap.service").read_text())
            self.assertIn("/usr/lib/tamlinux/current/share/tamlinux/console/tamlinux-vt.vtrgb",
                          (sys_units / "tam-vt-keymap.service").read_text())
            self.assertIn("/usr/lib/tamlinux/current/bin/tam-vt-screenshot",
                          (sys_units / "tam-vt-screenshot.service").read_text())
            self.assertEqual(
                (sys_units / "multi-user.target.d/50-tamlinux-services.conf").read_text(),
                "[Unit]\nWants=tam-vt-keymap.service\n",
            )
            self.assertEqual(
                (sys_units / "kbrequest.target.d/50-tamlinux-services.conf").read_text(),
                "[Unit]\nWants=tam-vt-screenshot.service\n",
            )
            self.assertTrue((stage / "usr/share/fonts/tamlinux/TamlinuxIcons.ttf").is_file())
            self.assertTrue((stage / "usr/lib/tamlinux/browser-policy-exec").is_file())
            self.assertIn("/usr/lib/tamlinux/browser-policy-exec",
                          (stage / "usr/share/polkit-1/actions/org.tamlinux.native.policy").read_text())
            fonts = stage / "usr/share/fontconfig/conf.default/50-tamlinux.conf"
            self.assertTrue(fonts.is_file() and not fonts.is_symlink())
            self.assertIn(
                "d /var/lib/tamlinux 0755 root root -",
                (stage / "usr/lib/tmpfiles.d/tamlinux.conf").read_text(),
            )
            self.assertFalse((stage / "usr/share/tamlinux").exists())
            self.assertFalse((stage / "usr/bin").exists())
            for value in ("", "/", "/usr", "relative"):
                with self.assertRaises(ValueError):
                    cultivar_layout.staging_root(cultivar_layout.CURRENT, value)

    def test_native_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            installer.install("/usr/lib/tamlinux/current", str(stage))
            root = stage / "usr/lib/tamlinux/current"
            self.assertFalse((stage / "etc").exists())
            self.assertFalse((stage / "home").exists())
            for name in ("tam-menu", "tam-hyprland-session", "tam-pane-session", "tam-desktop", "tam-protocol-shadow"):
                self.assertTrue(os.access(root / "bin" / name, os.X_OK), name)
            self.assertTrue((root / "share/tamlinux/shell/shell.qml").is_file())
            self.assertTrue((root / "share/tamlinux/plugins/fred.clock/manifest.json").is_file())
            self.assertEqual((root / "share/tamlinux/README").read_bytes(),
                             (SOURCE / "src/desktop/README").read_bytes())
            self.assertEqual((root / "share/tamlinux/plugins/README").read_bytes(),
                             (SOURCE / "src/desktop/plugins/README").read_bytes())
            self.assertFalse(list(root.rglob("README.md")))
            self.assertFalse((root / "share/tamlinux/assets/fonts/source.ttf").exists())
            self.assertTrue((root / "share/fonts/truetype/TamlinuxIcons.ttf").is_file())
            self.assertFalse(list(root.rglob("*.pyc")))
            self.assertFalse(list((root / "share/tamlinux/assets/themes").rglob("vscode.json")))
            unit = (root / "share/systemd/user/tamlinux-shell.service").read_text()
            self.assertIn("/usr/lib/tamlinux/current/share/tamlinux/shell/host/session_start.py", unit)
            self.assertNotIn(tmp, unit)
            self.assertNotIn("/nix/store/", unit)
            result = subprocess.run([str(root / "bin/tam-menu"), "--help"], cwd="/", capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_reproducible_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            def contents(stage):
                installer.install("/usr/lib/tamlinux/current", str(stage))
                root = stage / "usr/lib/tamlinux/current"
                return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in root.rglob("*") if p.is_file() and not p.is_symlink()}
            self.assertEqual(contents(Path(tmp) / "a"), contents(Path(tmp) / "b"))

    def test_bad_prefix(self):
        for prefix in ("relative", "/usr/../etc", "/usr/./lib"):
            with self.assertRaises(ValueError):
                installer.install(prefix, "/unused")

    def test_cultivar_identity_and_console_welcome(self):
        version = (SOURCE / "VERSION").read_text().strip()
        cultivar = (SOURCE / "CULTIVAR").read_text().strip()
        self.assertEqual(cultivar, "Northern Torch")
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            installer.install(cultivar_layout.CURRENT, tmp)
            runtime = stage / cultivar_layout.CURRENT.lstrip("/")
            commands = runtime / "bin"
            for name in ("hi", "start"):
                (commands / name).write_text("#!/bin/sh\n")
                (commands / name).chmod(0o755)
            cultivar_layout.install(stage)
            self.assertEqual((runtime / "share/tamlinux/cultivar").read_text().strip(), cultivar)
            issue = (stage / "usr/lib/issue.d/70-tamlinux.issue").read_text()
            self.assertIn(f"Welcome to Tamlinux {version}!", issue)
            self.assertIn(f"Cultivar:  {cultivar}\n", issue)

    def test_validate_cultivar(self):
        for ver, name in (("0.7.3", "Northern Torch"), ("0.6.42", "KBN WB"), ("1.4.0", "Deborah Waxman")):
            installer.validate_cultivar(ver, name)
        for ver, name in (
            ("0.7.3", "KBN WB"),
            ("0.8.0", "Northern Torch"),
            ("1.4.0", "Northern Torch"),
            ("0.7.3", ""),
            ("invalid", "Northern Torch"),
        ):
            with self.subTest(ver=ver, name=name), self.assertRaises(ValueError):
                installer.validate_cultivar(ver, name)


if __name__ == "__main__":
    unittest.main()
