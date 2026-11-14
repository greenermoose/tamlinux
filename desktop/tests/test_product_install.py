"""Native product installation stays under its prefix and is reproducible."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("install_product", SOURCE / "desktop/install-product.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
bundle_spec = importlib.util.spec_from_file_location("install_bundle_layout", SOURCE / "desktop/install-bundle-layout.py")
bundle_layout = importlib.util.module_from_spec(bundle_spec)
bundle_spec.loader.exec_module(bundle_layout)


class ProductInstall(unittest.TestCase):
    def test_bundle_layout_renders_private_paths_and_real_vendor_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            installer.install("/usr", tmp)
            command = stage / "usr/bin/tam-shell"
            command.write_bytes((SOURCE / "commands/tam-shell/tam-shell").read_bytes())
            command.chmod(0o755)
            dns_command = stage / "usr/bin/tam-dns"
            dns_command.write_bytes((SOURCE / "commands/tam-dns/tam-dns").read_bytes())
            dns_command.chmod(0o755)
            for name in ("hi", "start", "suspend-unless-stay-awake", "tam-nut"):
                original = stage / "usr/bin" / name
                original.write_text("#!/bin/sh\n")
                original.chmod(0o755)
            bundle_layout.install(stage)
            current = stage / "usr/lib/tamlinux/current"
            defaults = current / "defaults/home"
            self.assertEqual((defaults / ".config/tamlinux/session/hyprland.lua").read_text(),
                'dofile("/usr/lib/tamlinux/current/share/tamlinux/session/entry.lua")\n')
            environment = (defaults / ".config/uwsm/env.d/10-tamlinux.sh").read_text()
            self.assertIn('export TAMLINUX_QUICKSHELL=/usr/bin/quickshell\n', environment)
            self.assertNotIn('/nix/store', environment)
            for browser in ('chromium', 'google-chrome', 'BraveSoftware/Brave-Browser', 'microsoft-edge-dev'):
                import json
                host = json.loads((defaults / f'.config/{browser}/NativeMessagingHosts/org.tamlinux.copy_url.json').read_text())
                self.assertEqual(host['path'], '/usr/bin/tam-chromium-copy-url-host')
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
            self.assertIn("/usr/bin/tam-dns", dns_rendered)
            for name in ("hi", "start", "suspend-unless-stay-awake", "tam-session", "tam-nut"):
                self.assertFalse((stage / "usr/bin" / name).exists(), name)
            self.assertTrue(os.access(stage / "usr/bin/tam-start", os.X_OK))
            self.assertTrue(os.access(stage / "usr/bin/tam-suspend-unless-stay-awake", os.X_OK))
            desktop = (stage / "usr/bin/tam-desktop").read_text()
            self.assertIn("/usr/bin/tam-bundle session-activate", desktop)
            self.assertIn('exec /usr/bin/tam-desktop "$@"', desktop)
            unit = stage / "usr/lib/systemd/user/tamlinux-shell.service"
            self.assertIn("/usr/lib/tamlinux/current/share/tamlinux/shell", unit.read_text())
            wants = unit.parent / "graphical-session.target.d/50-tamlinux-services.conf"
            self.assertIn("Wants=tam-bt-agent.service tam-fcitx5.service", wants.read_text())
            fonts = stage / "usr/share/fontconfig/conf.default/50-tamlinux.conf"
            self.assertTrue(fonts.is_file() and not fonts.is_symlink())
            self.assertFalse((stage / "usr/share/tamlinux").exists())
            self.assertFalse((stage / "etc").exists())
            for value in ("", "/", "/usr", "relative"):
                with self.assertRaises(ValueError):
                    bundle_layout.staging_root("/usr", value)

    def test_native_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            installer.install("/usr/lib/tamlinux/current", str(stage))
            root = stage / "usr/lib/tamlinux/current"
            self.assertFalse((stage / "etc").exists())
            self.assertFalse((stage / "home").exists())
            for name in ("tam-menu", "tam-hyprland-session", "tam-desktop", "tam-protocol-shadow"):
                self.assertTrue(os.access(root / "bin" / name, os.X_OK), name)
            self.assertTrue((root / "share/tamlinux/shell/shell.qml").is_file())
            self.assertTrue((root / "share/tamlinux/plugins/fred.clock/manifest.json").is_file())
            self.assertEqual((root / "share/tamlinux/README").read_bytes(),
                             (SOURCE / "desktop/README").read_bytes())
            self.assertEqual((root / "share/tamlinux/plugins/README").read_bytes(),
                             (SOURCE / "desktop/plugins/README").read_bytes())
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


if __name__ == "__main__":
    unittest.main()
