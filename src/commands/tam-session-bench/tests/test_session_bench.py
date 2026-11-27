"""Unit tests for tam-session-bench."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tam-session-bench"
loader = importlib.machinery.SourceFileLoader("tam_session_bench", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)


class SessionBenchParsingTests(unittest.TestCase):
    def test_unescape_systemd_instance(self):
        self.assertEqual(mod.unescape_systemd_instance(r"tam\x2dpane"), "tam-pane")
        self.assertEqual(mod.unescape_systemd_instance("Hyprland"), "Hyprland")
        self.assertEqual(mod.escape_systemd_instance("tam-pane"), r"tam\x2dpane")

    def test_parse_smaps_rollup(self):
        text = (
            "56171a141000-7ffce6412000 ---p 00000000 00:00 0 [rollup]\n"
            "Rss:              126204 kB\n"
            "Pss:               61040 kB\n"
            "Pss_Anon:          23772 kB\n"
            "Pss_Shmem:         21404 kB\n"
            "Private_Dirty:     23772 kB\n"
        )
        parsed = mod.parse_smaps_rollup(text)
        self.assertEqual(parsed["rss_bytes"], 126204 * 1024)
        self.assertEqual(parsed["pss_bytes"], 61040 * 1024)
        self.assertEqual(parsed["pss_anon_bytes"], 23772 * 1024)
        self.assertEqual(parsed["private_dirty_bytes"], 23772 * 1024)

    def test_parse_drm_fdinfo_deduplicates_client_id(self):
        fd14 = (
            "drm-driver:\tamdgpu\n"
            "drm-client-id:\t130\n"
            "drm-resident-gtt:\t2 MiB\n"
            "drm-resident-vram:\t12 KiB\n"
        )
        # Duplicate fd for client 130 must not double count
        fd15 = fd14
        fd16 = (
            "drm-driver:\tamdgpu\n"
            "drm-client-id:\t131\n"
            "drm-resident-gtt:\t16400 KiB\n"
            "drm-resident-vram:\t205168 KiB\n"
            "drm-shared-vram:\t171136 KiB\n"
            "drm-engine-gfx:\t12688467793 ns\n"
        )
        # Duplicate fd for client 131
        fd17 = fd16

        drm = mod.parse_drm_fdinfo_entries([fd14, fd15, fd16, fd17])
        self.assertEqual(drm["drm_clients"], 2)
        self.assertEqual(drm["vram_bytes"], (12 + 205168) * 1024)
        self.assertEqual(drm["shared_vram_bytes"], 171136 * 1024)
        self.assertEqual(drm["gtt_bytes"], 2 * 1024 * 1024 + 16400 * 1024)
        self.assertEqual(drm["gfx_ns"], 12688467793)

    def test_parse_systemctl_show(self):
        text = (
            "Id=wayland-wm@tam\\x2dpane.service\n"
            "ActiveState=active\n"
            "SubState=running\n"
            "MainPID=859534\n"
            "MemoryCurrent=40013824\n"
            "MemoryPeak=88653824\n"
            "MemorySwapCurrent=0\n"
            "CPUUsageNSec=16426661000\n"
            "TasksCurrent=18\n"
        )
        parsed = mod.parse_systemctl_show(text)
        self.assertEqual(parsed["main_pid"], 859534)
        self.assertEqual(parsed["memory_current_bytes"], 40013824)
        self.assertEqual(parsed["memory_peak_bytes"], 88653824)
        self.assertEqual(parsed["cpu_usage_nsec"], 16426661000)
        self.assertEqual(parsed["tasks_current"], 18)

    def test_parse_journal_sessions_and_compare(self):
        entries = [
            # Hyprland session (completed)
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "wayland-session-envelope@Hyprland.target",
                "MESSAGE_ID": mod.MSG_UNIT_STARTED,
                "__MONOTONIC_TIMESTAMP": "10000000",
                "__REALTIME_TIMESTAMP": "1795638000000000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "wayland-wm@Hyprland.service",
                "MESSAGE_ID": mod.MSG_UNIT_STARTING,
                "__MONOTONIC_TIMESTAMP": "10160000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "wayland-wm@Hyprland.service",
                "MESSAGE_ID": mod.MSG_UNIT_STARTED,
                "__MONOTONIC_TIMESTAMP": "11160000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "graphical-session.target",
                "MESSAGE_ID": mod.MSG_UNIT_STARTED,
                "__MONOTONIC_TIMESTAMP": "11560000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "tamlinux-shell.service",
                "MESSAGE_ID": mod.MSG_UNIT_STARTED,
                "__MONOTONIC_TIMESTAMP": "11580000",
            },
            {
                "_BOOT_ID": "boot1",
                "_SYSTEMD_USER_UNIT": "tamlinux-shell.service",
                "MESSAGE": "TAMLINUX_EVIDENCE ipc-owner tamlinux-shell",
                "__MONOTONIC_TIMESTAMP": "12360000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "tamlinux-shell.service",
                "MESSAGE_ID": mod.MSG_UNIT_RESOURCES,
                "__MONOTONIC_TIMESTAMP": "111580000",
                "CPU_USAGE_NSEC": "5000000000",
                "MEMORY_PEAK": str(500 * 1024 * 1024),
                "MEMORY_SWAP_PEAK": "0",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "wayland-wm@Hyprland.service",
                "MESSAGE_ID": mod.MSG_UNIT_STOPPED,
                "__MONOTONIC_TIMESTAMP": "110160000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "wayland-wm@Hyprland.service",
                "MESSAGE_ID": mod.MSG_UNIT_RESOURCES,
                "__MONOTONIC_TIMESTAMP": "110160500",
                "CPU_USAGE_NSEC": "3000000000",
                "MEMORY_PEAK": str(240 * 1024 * 1024),
                "MEMORY_SWAP_PEAK": str(10 * 1024 * 1024),
            },
            # tam-pane session (completed, with internal startup phase log)
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": r"wayland-session-envelope@tam\x2dpane.target",
                "MESSAGE_ID": mod.MSG_UNIT_STARTED,
                "__MONOTONIC_TIMESTAMP": "200000000",
                "__REALTIME_TIMESTAMP": "1795640000000000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": r"wayland-wm@tam\x2dpane.service",
                "MESSAGE_ID": mod.MSG_UNIT_STARTING,
                "__MONOTONIC_TIMESTAMP": "200170000",
            },
            {
                "_BOOT_ID": "boot1",
                "_SYSTEMD_USER_UNIT": r"wayland-wm@tam\x2dpane.service",
                "MESSAGE": "tam-pane startup: lua=4.2ms init=310.5ms start=15.1ms total=329.8ms",
                "__MONOTONIC_TIMESTAMP": "200500000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": r"wayland-wm@tam\x2dpane.service",
                "MESSAGE_ID": mod.MSG_UNIT_STARTED,
                "__MONOTONIC_TIMESTAMP": "200650000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "graphical-session.target",
                "MESSAGE_ID": mod.MSG_UNIT_STARTED,
                "__MONOTONIC_TIMESTAMP": "200990000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": "tamlinux-shell.service",
                "MESSAGE_ID": mod.MSG_UNIT_STARTED,
                "__MONOTONIC_TIMESTAMP": "201010000",
            },
            {
                "_BOOT_ID": "boot1",
                "_SYSTEMD_USER_UNIT": "tamlinux-shell.service",
                "MESSAGE": list(b"\x1b[32m DEBUG\x1b[0m qml: TAMLINUX_EVIDENCE ipc-owner tamlinux-shell"),
                "__MONOTONIC_TIMESTAMP": "201760000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": r"wayland-wm@tam\x2dpane.service",
                "MESSAGE_ID": mod.MSG_UNIT_STOPPED,
                "__MONOTONIC_TIMESTAMP": "300170000",
            },
            {
                "_BOOT_ID": "boot1",
                "USER_UNIT": r"wayland-wm@tam\x2dpane.service",
                "MESSAGE_ID": mod.MSG_UNIT_RESOURCES,
                "__MONOTONIC_TIMESTAMP": "300170500",
                "CPU_USAGE_NSEC": "1500000000",
                "MEMORY_PEAK": str(80 * 1024 * 1024),
                "MEMORY_SWAP_PEAK": "0",
            },
        ]

        sessions = mod.parse_journal_sessions(entries)
        self.assertEqual(len(sessions), 2)

        hypr, pane = sessions
        self.assertEqual(hypr["compositor"], "Hyprland")
        self.assertEqual(hypr["stages_ms"]["env_preload_ms"], 160.0)
        self.assertEqual(hypr["stages_ms"]["compositor_ms"], 1000.0)
        self.assertEqual(hypr["stages_ms"]["session_target_ms"], 400.0)
        self.assertEqual(hypr["stages_ms"]["shell_ready_ms"], 800.0)
        self.assertEqual(hypr["stages_ms"]["total_ms"], 2360.0)
        self.assertEqual(hypr["resources"]["compositor"]["avg_cpu_pct"], 3.0)

        self.assertEqual(pane["compositor"], "tam-pane")
        self.assertEqual(pane["stages_ms"]["compositor_ms"], 480.0)
        self.assertEqual(pane["stages_ms"]["total_ms"], 1760.0)
        self.assertEqual(pane["tam_pane_phases_ms"]["lua_ms"], 4.2)
        self.assertEqual(pane["tam_pane_phases_ms"]["init_ms"], 310.5)
        self.assertEqual(pane["resources"]["compositor"]["avg_cpu_pct"], 1.5)

        agg = mod.aggregate_comparison(sessions)
        self.assertEqual(agg["compositors"]["Hyprland"]["compositor_ms"]["median"], 1000.0)
        self.assertEqual(agg["compositors"]["tam-pane"]["compositor_ms"]["median"], 480.0)
        self.assertEqual(agg["compositors"]["Hyprland"]["wm_mem_peak_mib"]["median"], 240.0)
        self.assertEqual(agg["compositors"]["tam-pane"]["wm_mem_peak_mib"]["median"], 80.0)

        table = mod.format_compare_human(agg)
        self.assertIn("Hyprland", table)
        self.assertIn("tam-pane", table)
        self.assertIn("-520 ms (-52.0%)", table)

    def test_save_and_load_sample_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = {
                "kind": "sample",
                "compositor": "tam-pane",
                "duration_s": 10.0,
                "components": {
                    "compositor": {
                        "delta_cpu_pct": 1.25,
                        "delta_gpu_gfx_pct": 0.4,
                        "pss_mib": {"n": 5, "median": 60.0, "min": 59.0, "max": 61.0},
                        "vram_mib": {"n": 5, "median": 200.0, "min": 200.0, "max": 200.0},
                    }
                },
                "system_power_w": {"n": 5, "median": 3.1, "min": 2.9, "max": 3.4},
            }
            path = mod.save_sample_record(rec, directory=Path(tmp))
            self.assertTrue(path.is_file())
            loaded = mod.load_saved_samples(directory=Path(tmp))
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["compositor"], "tam-pane")
            agg = mod.aggregate_comparison([], saved_samples=loaded)
            self.assertEqual(agg["saved_samples"]["tam-pane"]["wm_cpu_pct"]["median"], 1.25)
            self.assertEqual(agg["saved_samples"]["tam-pane"]["power_w"]["median"], 3.1)


class TrialFilteringTest(unittest.TestCase):
    def test_wm_ready_without_shell_ready_does_not_count_as_total(self):
        entries = [
            {"MESSAGE_ID": mod.MSG_UNIT_STARTED, "USER_UNIT": "wayland-session-envelope@Hyprland.target",
             "__MONOTONIC_TIMESTAMP": "1000"},
            {"MESSAGE_ID": mod.MSG_UNIT_STARTING, "USER_UNIT": "wayland-wm@Hyprland.service",
             "__MONOTONIC_TIMESTAMP": "2000"},
            {"MESSAGE_ID": mod.MSG_UNIT_STARTED, "USER_UNIT": "wayland-wm@Hyprland.service",
             "__MONOTONIC_TIMESTAMP": "3000"},
        ]
        result = mod.aggregate_comparison(mod.parse_journal_sessions(entries))
        self.assertEqual(result["compositors"]["Hyprland"]["compositor_ms"]["n"], 1)
        self.assertIsNone(result["compositors"]["Hyprland"]["total_ms"])

    def test_comparison_time_uses_record_offsets(self):
        since = mod.comparison_time("2026-11-26T15:00:00-05:00")
        self.assertTrue(mod.at_or_after("2026-11-26T20:00:00Z", since))
        self.assertFalse(mod.at_or_after("2026-11-26T19:59:59Z", since))
        self.assertFalse(mod.at_or_after("", since))


if __name__ == "__main__":
    unittest.main()
