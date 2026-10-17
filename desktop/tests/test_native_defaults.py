"""Native system defaults: exact values, vendor-only paths, recorded origins."""

from __future__ import annotations

import configparser
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
BASE = DESKTOP / "native/defaults"
ROOT = BASE / "root"
INHERITED = ("omarchy", "omacom", "basecamp")


def entries():
    return sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_symlink() or p.is_file())


def ini(relative):
    parser = configparser.ConfigParser(strict=True, interpolation=None)
    parser.optionxform = str
    parser.read_string((ROOT / relative).read_text())
    return parser


def assignments(relative):
    values = {}
    for line in (ROOT / relative).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


class NativeDefaultsTests(unittest.TestCase):
    def test_origins_record_every_entry_exactly(self):
        origins = json.loads((BASE / "origins.json").read_text())
        self.assertEqual(sorted(origins["files"]), entries())
        for relative, entry in origins["files"].items():
            path = ROOT / relative
            if "link" in entry:
                self.assertTrue(path.is_symlink(), relative)
                self.assertEqual(os.readlink(path), entry["link"])
                self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()), relative)
                self.assertTrue(path.resolve().is_file(), relative)
                continue
            self.assertFalse(path.is_symlink(), relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"], relative)
            self.assertEqual(format(path.stat().st_mode & 0o7777, "04o"), entry["mode"], relative)
        self.assertTrue((BASE / origins["license"]).is_file())

    def test_vendor_locations_and_tamlinux_names_only(self):
        origins = json.loads((BASE / "origins.json").read_text())["files"]
        previous = {"/" + entry.get("derivedFrom", "").lstrip("/") for entry in origins.values()}
        for relative in entries():
            self.assertTrue(relative.startswith(("usr/lib/", "usr/share/")), relative)
            self.assertNotIn("/" + relative, previous, relative)
            name = relative.rsplit("/", 1)[1]
            self.assertTrue("tamlinux" in name or name in {"tam-fcitx5.service", "tam-bt-agent.service", "tam-hibernate-swap"}, relative)
            for word in INHERITED:
                self.assertNotIn(word, relative.lower())
                if not (ROOT / relative).is_symlink():
                    self.assertNotIn(word, (ROOT / relative).read_text().lower(), relative)

    def test_memory_and_swap_values(self):
        zram = ini("usr/lib/systemd/zram-generator.conf.d/90-tamlinux.conf")["zram0"]
        self.assertEqual(dict(zram), {"zram-size": "ram", "compression-algorithm": "zstd", "swap-priority": "100"})
        self.assertEqual(assignments("usr/lib/sysctl.d/70-tamlinux.conf"), {
            "kernel.sysrq": "244",
            "net.ipv4.tcp_mtu_probing": "1", "vm.swappiness": "150", "vm.vfs_cache_pressure": "50",
            "vm.page-cluster": "0", "vm.watermark_boost_factor": "0", "vm.watermark_scale_factor": "125",
            "vm.dirty_background_bytes": "67108864", "vm.dirty_bytes": "268435456",
            "vm.dirty_writeback_centisecs": "1500"})
        lines = [line for line in (ROOT / "usr/lib/tmpfiles.d/tamlinux-zswap.conf").read_text().splitlines()
                 if line and not line.startswith("#")]
        self.assertEqual(lines, ["w! /sys/module/zswap/parameters/enabled - - - - N"])
        self.assertEqual(dict(ini("usr/lib/systemd/oomd.conf.d/10-tamlinux.conf")["OOM"]),
                         {"DefaultMemoryPressureDurationSec": "20s", "DefaultMemoryPressureLimit": "50%"})
        self.assertEqual(dict(ini("usr/lib/systemd/user/app.slice.d/10-tamlinux-oomd.conf")["Slice"]),
                         {"ManagedOOMMemoryPressure": "kill", "ManagedOOMSwap": "kill"})
        preset = [line for line in (ROOT / "usr/lib/systemd/system-preset/80-tamlinux.preset").read_text().splitlines()
                  if line and not line.startswith("#")]
        self.assertEqual(preset, ["enable systemd-oomd.service"])

    def test_session_manager_and_service_values(self):
        self.assertEqual(dict(ini("usr/lib/systemd/logind.conf.d/10-tamlinux-power-key.conf")["Login"]),
                         {"HandlePowerKey": "ignore", "InhibitDelayMaxSec": "15"})
        for manager in ("system", "user"):
            self.assertEqual(dict(ini(f"usr/lib/systemd/{manager}.conf.d/20-tamlinux-nofile.conf")["Manager"]),
                             {"DefaultLimitNOFILE": "65536:524288"})
        self.assertEqual(dict(ini("usr/lib/systemd/system.conf.d/10-tamlinux-faster-shutdown.conf")["Manager"]),
                         {"DefaultTimeoutStopSec": "5s"})
        self.assertEqual(dict(ini("usr/lib/systemd/system/user@.service.d/10-tamlinux-faster-shutdown.conf")["Service"]),
                         {"TimeoutStopSec": "5s"})
        self.assertEqual(dict(ini("usr/lib/NetworkManager/conf.d/tamlinux-wifi-powersave.conf")["connection"]),
                         {"wifi.powersave": "2"})
        updatedb = (ROOT / "usr/lib/systemd/system/plocate-updatedb.service.d/10-tamlinux.conf").read_text()
        self.assertIn("ExecStart=\nExecStart=/usr/bin/updatedb --prune-bind-mounts=no --add-prunepaths=/.snapshots\n", updatedb)
        self.assertEqual(dict(ini("usr/lib/systemd/system/plocate-updatedb.service.d/20-tamlinux-ac-only.conf")["Unit"]),
                         {"ConditionACPower": "true"})
        self.assertEqual(dict(ini("usr/lib/systemd/system/docker.service.d/10-tamlinux-no-block-boot.conf")["Unit"]),
                         {"DefaultDependencies": "no"})

    def test_input_method_and_pairing_agent_ship_enabled(self):
        self.assertEqual(assignments("usr/lib/environment.d/10-tamlinux-fcitx.conf"), {
            "INPUT_METHOD": "fcitx", "QT_IM_MODULE": "fcitx", "XMODIFIERS": "@im=fcitx", "SDL_IM_MODULE": "fcitx"})
        for unit, binary in (("tam-fcitx5.service", "/usr/bin/fcitx5"), ("tam-bt-agent.service", "/usr/bin/bt-agent")):
            parsed = ini("usr/lib/systemd/user/" + unit)
            self.assertEqual(parsed["Unit"]["ConditionPathExists"], binary)
            self.assertTrue(parsed["Service"]["ExecStart"].startswith(binary + " "))
            self.assertEqual(parsed["Install"]["WantedBy"], "graphical-session.target")
            link = ROOT / "usr/lib/systemd/user/graphical-session.target.wants" / unit
            self.assertEqual(os.readlink(link), "../" + unit)
        agent = ini("usr/lib/systemd/user/tam-bt-agent.service")
        self.assertEqual(agent["Service"]["ExecStart"], "/usr/bin/bt-agent -c NoInputNoOutput")
        # A user's or the previous owner's bt-agent.service wins; never two agents.
        self.assertIn("bt-agent.service", agent["Unit"]["After"].split())
        self.assertIn("! /usr/bin/systemctl --user is-active --quiet bt-agent.service", agent["Service"]["ExecCondition"])

    def test_sleep_hook_is_executable_bash(self):
        hook = ROOT / "usr/lib/systemd/system-sleep/tamlinux-unmount-fuse"
        self.assertTrue(hook.stat().st_mode & 0o111)
        self.assertIn('[[ -x /usr/lib/systemd/system-sleep/unmount-fuse ]] && exit 0', hook.read_text())
        self.assertTrue(hook.read_text().startswith("#!/bin/bash\n"))
        subprocess.run(["/usr/bin/bash", "-n", str(hook)], check=True)

    def test_font_rules(self):
        tree = ElementTree.parse(ROOT / "usr/share/fontconfig/conf.avail/50-tamlinux.conf")
        strong = {}
        for match in tree.getroot().iter("match"):
            test, edit = match.find("test"), match.find("edit")
            if test is not None and test.get("name") == "family" and edit.get("mode") == "assign":
                strong[test.findtext("string")] = edit.findtext("string")
        self.assertEqual(strong, {"sans-serif": "Liberation Sans", "serif": "Liberation Serif",
                                  "monospace": "JetBrainsMono Nerd Font"})
        aliases = {alias.findtext("family"): alias for alias in tree.getroot().iter("alias")}
        for family in ("system-ui", "-apple-system", "BlinkMacSystemFont"):
            self.assertEqual(aliases[family].findtext("prefer/family"), "Liberation Sans")
        accepted = [f.text for f in aliases["sans-serif"].find("accept")]
        self.assertIn("Noto Color Emoji", accepted)
        self.assertEqual(os.readlink(ROOT / "usr/share/fontconfig/conf.default/50-tamlinux.conf"),
                         "../conf.avail/50-tamlinux.conf")

    @unittest.skipUnless(shutil.which("fc-match") and Path("/usr/share/fontconfig/conf.default").is_dir(),
                         "fontconfig not installed")
    def test_font_rules_resolve_with_real_fontconfig(self):
        with tempfile.TemporaryDirectory(prefix="tamlinux-fonts-") as directory:
            # A clean host's conf.d: Arch's default rule set plus this rule.
            confd = Path(directory) / "conf.d"
            confd.mkdir()
            for default in Path("/usr/share/fontconfig/conf.default").iterdir():
                if default.name == "50-tamlinux.conf":
                    continue  # The host may already have Tamlinux installed.
                (confd / default.name).symlink_to(default.resolve())
            (confd / "50-tamlinux.conf").symlink_to(ROOT / "usr/share/fontconfig/conf.avail/50-tamlinux.conf")
            config = Path(directory) / "fonts.conf"
            config.write_text(
                '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
                "<dir>/usr/share/fonts</dir>"
                f"<cachedir>{directory}/cache</cachedir>"
                f"<include>{confd}</include>"
                "</fontconfig>")
            env = {"FONTCONFIG_FILE": str(config), "PATH": "/usr/bin", "HOME": directory}
            available = subprocess.run(["fc-list", ":family=Liberation Sans", "family"], env=env,
                                       capture_output=True, text=True, check=True).stdout
            if not available.strip():
                self.skipTest("Liberation Sans not installed")
            for family in ("sans-serif", "system-ui", "-apple-system"):
                result = subprocess.run(["fc-match", "-f", "%{family[0]}", ":family=" + family], env=env,
                                        capture_output=True, text=True, check=True).stdout
                self.assertEqual(result, "Liberation Sans", family)


if __name__ == "__main__":
    unittest.main()
