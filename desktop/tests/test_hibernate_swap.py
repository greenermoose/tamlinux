"""Hibernate-time zram drain hook: drains only before hibernating, restores after."""

from __future__ import annotations

import os
import time
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "native/defaults/root/usr/lib/systemd/system-sleep/tam-hibernate-swap"
HEADER = "Filename\t\t\t\tType\t\tSize\t\tUsed\t\tPriority\n"
GIB = 1048576  # KiB

FAKES = {
    # Succeeds by removing the device from the fake /proc/swaps, or fails and
    # leaves it there the way an interrupted kernel swapoff does.
    "swapoff": """
        echo "swapoff $*" >> "$CALLS"
        [[ ${SWAPOFF_FAILS:-0} == 1 ]] && exit 1
        [[ ${SWAPOFF_HANGS:-0} == 1 ]] && sleep 180
        awk -v dev="$1" '$1 != dev' "$TAMLINUX_SWAPS_PATH" > "$TAMLINUX_SWAPS_PATH.new"
        mv "$TAMLINUX_SWAPS_PATH.new" "$TAMLINUX_SWAPS_PATH"
        [[ -n ${SYSTEMD_FRAGMENT:-} ]] && touch "$TAMLINUX_RUN_PATH/header-reset"
        exit 0
    """,
    "swapon": """
        echo "swapon $*" >> "$CALLS"
        [[ ${SWAPON_FAILS:-0} == 1 ]] && exit 1
        [[ -e $TAMLINUX_RUN_PATH/header-reset ]] && exit 1
        prio=-2
        [[ $* == *--priority* ]] && prio=$3
        printf '%s partition 29630864 0 %s\\n' "${!#}" "$prio" >> "$TAMLINUX_SWAPS_PATH"
    """,
    "systemctl": """
        if [[ $1 == show ]]; then
            [[ ${SYSTEMD_SHOW_FAILS:-0} == 1 ]] && exit 1
            printf '%s' "${SYSTEMD_FRAGMENT:-}"
            exit 0
        fi
        echo "systemctl $*" >> "$CALLS"
        [[ $1 == start ]] || exit 1
        [[ ${SYSTEMD_START_FAILS:-0} == 1 ]] && exit 1
        [[ ${SYSTEMD_START_HANGS:-0} == 1 ]] && sleep 180
        [[ ${SYSTEMD_START_NO_SWAP:-0} == 1 ]] && exit 0
        # Model the manager waiting for generator teardown and formatting a
        # fresh header before enabling the generated swap unit.
        rm -f "$TAMLINUX_RUN_PATH/header-reset"
        dev=${2#dev-}; dev=/dev/${dev%.swap}
        awk -v dev="$dev" '$1 != dev' "$TAMLINUX_SWAPS_PATH" > "$TAMLINUX_SWAPS_PATH.new"
        mv "$TAMLINUX_SWAPS_PATH.new" "$TAMLINUX_SWAPS_PATH"
        printf '%s partition 29630864 0 %s\\n' "$dev" "${SYSTEMD_PRIORITY:-100}" >> "$TAMLINUX_SWAPS_PATH"
    """,
    "logger": """
        shift 2; [[ $1 == -- ]] && shift
        echo "$*" >> "$LOG"
    """,
}


class HibernateSwapHookTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for name, body in FAKES.items():
            path = self.bin / name
            path.write_text("#!/bin/bash\n" + textwrap.dedent(body))
            path.chmod(0o755)
        self.swaps = self.tmp / "swaps"
        self.run_dir = self.tmp / "run"
        self.run_dir.mkdir()
        self.calls = self.tmp / "calls"
        self.log = self.tmp / "log"

    def write_swaps(self, *rows):
        self.swaps.write_text(HEADER + "".join(f"{name}\t{kind}\t{size}\t{used}\t{prio}\n" for name, kind, size, used, prio in rows))

    def hook(self, *args, action=None, **extra):
        env = {
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "TAMLINUX_SWAPS_PATH": str(self.swaps),
            "TAMLINUX_RUN_PATH": str(self.run_dir),
            "CALLS": str(self.calls),
            "LOG": str(self.log),
            **extra,
        }
        if action:
            env["SYSTEMD_SLEEP_ACTION"] = action
        result = subprocess.run([str(HOOK), *args], env=env, capture_output=True, text=True, timeout=80)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def calls_made(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def logged(self):
        return self.log.read_text() if self.log.exists() else ""

    def state(self):
        return self.run_dir / "tamlinux-hibernate-swap"

    def standard_swaps(self, zram_used=7 * GIB, disk_used=0):
        self.write_swaps(
            ("/swap/swapfile", "file", 28 * GIB, disk_used, 0),
            ("/dev/zram0", "partition", 28 * GIB, zram_used, 100),
        )

    def test_hook_is_executable_bash(self):
        self.assertTrue(HOOK.stat().st_mode & stat.S_IXUSR)
        self.assertTrue(HOOK.read_text().startswith("#!/bin/bash\n"))

    def test_drains_before_the_hibernate_leg_and_restores_after(self):
        self.standard_swaps()
        self.hook("pre", "suspend-then-hibernate", action="hibernate")
        self.assertEqual(self.calls_made(), ["swapoff /dev/zram0"])
        self.assertEqual(self.state().read_text(), "/dev/zram0 100\n")
        self.assertNotIn("/dev/zram0", self.swaps.read_text())
        self.assertIn("drained 7.0 GiB from /dev/zram0", self.logged())
        self.assertIn("disk swap now holds 0.0 GiB", self.logged())

        self.hook("post", "suspend-then-hibernate", action="hibernate")
        self.assertEqual(self.calls_made()[1:], ["swapon --discard --priority 100 /dev/zram0"])
        self.assertFalse(self.state().exists())
        self.assertIn("/dev/zram0", self.swaps.read_text())

    def test_plain_hibernate_and_hybrid_sleep_drain(self):
        for second in ("hibernate", "hybrid-sleep"):
            with self.subTest(second=second):
                self.standard_swaps()
                self.calls.unlink(missing_ok=True)
                self.hook("pre", second)
                self.assertEqual(self.calls_made(), ["swapoff /dev/zram0"])
                self.hook("post", second)
                self.assertFalse(self.state().exists())

    def test_suspend_leg_leaves_zram_alone(self):
        self.standard_swaps()
        self.hook("pre", "suspend-then-hibernate", action="suspend")
        self.hook("pre", "suspend")
        self.assertEqual(self.calls_made(), [])
        self.assertFalse(self.state().exists())

    def test_ambiguous_suspend_then_hibernate_without_action_does_not_drain(self):
        self.standard_swaps()
        self.hook("pre", "suspend-then-hibernate")
        self.assertEqual(self.calls_made(), [])

    def test_fallback_suspend_after_failed_hibernate_restores_first(self):
        self.standard_swaps()
        self.hook("pre", "suspend-then-hibernate", action="hibernate")
        self.hook("pre", "suspend-then-hibernate", action="suspend-after-failed-hibernate")
        self.assertEqual(self.calls_made(), ["swapoff /dev/zram0", "swapon --discard --priority 100 /dev/zram0"])
        self.assertFalse(self.state().exists())

    def test_skips_when_disk_swap_would_pass_eighty_percent(self):
        self.standard_swaps(zram_used=20 * GIB, disk_used=3 * GIB)
        self.hook("pre", "hibernate")
        self.assertEqual(self.calls_made(), [])
        self.assertFalse(self.state().exists())
        self.assertIn("left zram on: moving its 20.0 GiB would fill disk swap past 80%", self.logged())

    def test_skips_without_disk_swap(self):
        self.write_swaps(("/dev/zram0", "partition", 28 * GIB, GIB, 100))
        self.hook("pre", "hibernate")
        self.assertEqual(self.calls_made(), [])
        self.assertIn("no disk swap is active", self.logged())

    def test_nothing_to_do_without_zram(self):
        self.write_swaps(("/swap/swapfile", "file", 28 * GIB, 0, 0))
        self.hook("pre", "hibernate")
        self.hook("post", "hibernate")
        self.assertEqual(self.calls_made(), [])
        self.assertEqual(self.logged(), "")

    def test_empty_zram_is_still_turned_off_so_reclaim_goes_to_disk(self):
        self.standard_swaps(zram_used=0)
        self.hook("pre", "hibernate")
        self.assertEqual(self.calls_made(), ["swapoff /dev/zram0"])

    def test_interrupted_drain_keeps_zram_on_and_post_does_not_add_it_twice(self):
        self.standard_swaps()
        self.hook("pre", "hibernate", SWAPOFF_FAILS="1")
        self.assertIn("stopped draining /dev/zram0 after", self.logged())
        self.assertIn("with 7.0 GiB still in it; hibernating anyway", self.logged())
        self.hook("post", "hibernate")
        self.assertEqual(self.calls_made(), ["swapoff /dev/zram0"])
        self.assertFalse(self.state().exists())

    def test_second_copy_in_the_same_sleep_does_not_drain_again(self):
        self.standard_swaps()
        self.state().write_text("/dev/zram0 100\n")
        self.hook("pre", "hibernate")
        self.assertEqual(self.calls_made(), [])

    def test_failed_restore_retains_state_and_post_retries(self):
        self.standard_swaps()
        self.hook("pre", "hibernate")
        self.hook("post", "hibernate", SWAPON_FAILS="1")
        self.assertEqual(self.state().read_text(), "/dev/zram0 100\n")
        self.assertNotIn("/dev/zram0", self.swaps.read_text())
        self.assertIn("retained", self.logged())
        self.hook("post", "hibernate")
        self.assertIn("/dev/zram0", self.swaps.read_text())
        self.assertFalse(self.state().exists())
        self.assertEqual(self.calls_made(), ["swapoff /dev/zram0",
                         "swapon --discard --priority 100 /dev/zram0",
                         "swapon --discard --priority 100 /dev/zram0"])

    def test_suspend_pre_retries_failed_restore_without_draining_again(self):
        self.standard_swaps()
        self.hook("pre", "hibernate")
        self.hook("post", "hibernate", SWAPON_FAILS="1")
        self.hook("pre", "suspend")
        self.assertIn("/dev/zram0", self.swaps.read_text())
        self.assertFalse(self.state().exists())
        self.assertEqual(sum(call.startswith("swapoff") for call in self.calls_made()), 1)

    def test_generator_reset_is_restored_through_swap_unit(self):
        for action in ("post", "suspend-after-failed-hibernate"):
            with self.subTest(action=action):
                self.standard_swaps()
                self.calls.unlink(missing_ok=True)
                managed = {"SYSTEMD_FRAGMENT": "/run/systemd/generator/dev-zram0.swap"}
                self.hook("pre", "hibernate", **managed)
                self.assertTrue((self.run_dir / "header-reset").exists())
                if action == "post":
                    self.hook("post", "hibernate", **managed)
                else:
                    self.hook("pre", "suspend-then-hibernate", action=action, **managed)
                self.assertEqual(self.calls_made(), ["swapoff /dev/zram0", "systemctl start dev-zram0.swap"])
                self.assertFalse(self.state().exists())
                self.assertIn("/dev/zram0", self.swaps.read_text())
                self.assertFalse((self.run_dir / "header-reset").exists())

    def test_generator_start_failure_keeps_state_for_retry(self):
        self.standard_swaps()
        managed = {"SYSTEMD_FRAGMENT": "/run/systemd/generator/dev-zram0.swap"}
        self.hook("pre", "hibernate", **managed)
        self.hook("post", "hibernate", SYSTEMD_START_FAILS="1", **managed)
        self.assertEqual(self.state().read_text(), "/dev/zram0 100\n")
        self.assertNotIn("/dev/zram0", self.swaps.read_text())
        self.hook("post", "hibernate", **managed)
        self.assertFalse(self.state().exists())
        self.assertNotIn("swapon", "\n".join(self.calls_made()))

    def test_successful_manager_command_requires_active_swap_and_saved_priority(self):
        for extra in ({"SYSTEMD_START_NO_SWAP": "1"}, {"SYSTEMD_PRIORITY": "50"}):
            with self.subTest(extra=extra):
                self.standard_swaps()
                self.state().unlink(missing_ok=True)
                managed = {"SYSTEMD_FRAGMENT": "/run/systemd/generator/dev-zram0.swap"}
                self.hook("pre", "hibernate", **managed)
                self.hook("post", "hibernate", **managed, **extra)
                self.assertTrue(self.state().exists())
                self.assertIn("could not verify", self.logged())
                self.hook("post", "hibernate", **managed)
                self.assertFalse(self.state().exists())

    def test_manager_query_failure_never_races_raw_swapon(self):
        self.standard_swaps()
        managed = {"SYSTEMD_FRAGMENT": "/run/systemd/generator/dev-zram0.swap"}
        self.hook("pre", "hibernate", **managed)
        self.hook("post", "hibernate", SYSTEMD_SHOW_FAILS="1", **managed)
        self.assertTrue(self.state().exists())
        self.assertEqual(self.calls_made(), ["swapoff /dev/zram0"])

    def test_existing_retry_state_clears_after_manager_already_restored_swap(self):
        self.standard_swaps(zram_used=0)
        self.state().write_text("/dev/zram0 100\n")
        self.hook("post", "hibernate", SYSTEMD_FRAGMENT="/run/systemd/generator/dev-zram0.swap")
        self.assertFalse(self.state().exists())
        self.assertEqual(self.calls_made(), ["systemctl start dev-zram0.swap"])
        self.assertEqual(self.swaps.read_text().count("/dev/zram0"), 1)

    def test_real_timeout_bounds_generator_restore_and_retains_retry_state(self):
        self.standard_swaps()
        managed = {"SYSTEMD_FRAGMENT": "/run/systemd/generator/dev-zram0.swap"}
        self.hook("pre", "hibernate", **managed)
        started = time.monotonic()
        self.hook("post", "hibernate", SYSTEMD_START_HANGS="1", **managed)
        self.assertGreaterEqual(time.monotonic() - started, 29)
        self.assertLess(time.monotonic() - started, 40)
        self.assertTrue(self.state().exists())
        self.assertNotIn("/dev/zram0", self.swaps.read_text())
        self.hook("post", "hibernate", **managed)
        self.assertFalse(self.state().exists())

    def test_negative_kernel_priority_is_restored_without_requesting_it(self):
        self.write_swaps(
            ("/swap/swapfile", "file", 28 * GIB, 0, -2),
            ("/dev/zram0", "partition", 28 * GIB, GIB, -3),
        )
        self.hook("pre", "hibernate")
        self.hook("post", "hibernate")
        self.assertEqual(self.calls_made(), ["swapoff /dev/zram0", "swapon --discard /dev/zram0"])

    def test_real_timeout_stops_drain_and_keeps_zram_on(self):
        self.standard_swaps()
        started = time.monotonic()
        self.hook("pre", "hibernate", SWAPOFF_HANGS="1")
        elapsed = time.monotonic() - started
        self.assertGreaterEqual(elapsed, 59)
        self.assertLess(elapsed, 75)
        self.assertIn("stopped draining /dev/zram0", self.logged())
        self.assertIn("with 7.0 GiB still in it", self.logged())
        self.assertIn("/dev/zram0", self.swaps.read_text())
        self.hook("post", "hibernate")
        self.assertEqual(self.calls_made(), ["swapoff /dev/zram0"])
        self.assertFalse(self.state().exists())


if __name__ == "__main__":
    unittest.main()
