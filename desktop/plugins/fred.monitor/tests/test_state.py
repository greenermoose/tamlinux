import importlib.machinery
import importlib.util
import json
import os
import pathlib
import stat
import subprocess
import tempfile
import unittest


PLUGIN = pathlib.Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("fred_monitor_state", str(PLUGIN / "fred-monitor-state"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
STATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STATE)


class StateCacheTests(unittest.TestCase):
    def test_runtime_cache_is_private_atomic_and_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            previous = os.environ.get("XDG_RUNTIME_DIR")
            os.environ["XDG_RUNTIME_DIR"] = temp
            try:
                dir_fd = STATE.private_runtime_dir()
                self.assertIsNotNone(dir_fd)
                runtime = pathlib.Path(temp) / "fred.monitor"
                self.assertEqual(stat.S_IMODE(runtime.stat().st_mode), 0o700)

                filename = STATE.cache_name("DP-1")
                STATE.write_cache(dir_fd, filename, {"percent": 75, "available": True, "timestamp": 1})
                self.assertEqual(stat.S_IMODE((runtime / filename).stat().st_mode), 0o600)
                self.assertEqual(STATE.read_cache(dir_fd, filename)["percent"], 75)

                victim = pathlib.Path(temp) / "victim.json"
                victim.write_text(json.dumps({"untouched": True}))
                (runtime / filename).unlink()
                (runtime / filename).symlink_to(victim)
                self.assertIsNone(STATE.read_cache(dir_fd, filename))
                STATE.write_cache(dir_fd, filename, {"percent": 80})
                self.assertEqual(json.loads(victim.read_text()), {"untouched": True})
                self.assertFalse((runtime / filename).is_symlink())
                os.close(dir_fd)
            finally:
                if previous is None:
                    os.environ.pop("XDG_RUNTIME_DIR", None)
                else:
                    os.environ["XDG_RUNTIME_DIR"] = previous

    def test_transient_probe_failure_preserves_last_known_brightness_support(self):
        with tempfile.TemporaryDirectory() as temp:
            previous_runtime = os.environ.get("XDG_RUNTIME_DIR")
            original_command = STATE.command_output
            os.environ["XDG_RUNTIME_DIR"] = temp
            try:
                dir_fd = STATE.private_runtime_dir()
                filename = STATE.cache_name("HDMI-A-1")
                STATE.write_cache(dir_fd, filename, {
                    "percent": 90,
                    "available": True,
                    "lastSuccess": True,
                    "timestamp": 1,
                })
                STATE.command_output = lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    subprocess.TimeoutExpired("ddc", 3)
                )
                percent, available = STATE.get_brightness("HDMI-A-1", dir_fd)
                self.assertEqual(percent, 90)
                self.assertTrue(available)
                self.assertTrue(STATE.read_cache(dir_fd, filename)["stale"])
                os.close(dir_fd)
            finally:
                STATE.command_output = original_command
                if previous_runtime is None:
                    os.environ.pop("XDG_RUNTIME_DIR", None)
                else:
                    os.environ["XDG_RUNTIME_DIR"] = previous_runtime

    def test_set_brightness_accepts_silent_success_and_updates_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            previous_runtime = os.environ.get("XDG_RUNTIME_DIR")
            original_command = STATE.command_output
            os.environ["XDG_RUNTIME_DIR"] = temp
            try:
                STATE.command_output = lambda *_args, **_kwargs: ""
                STATE.set_brightness("HDMI-A-1", "90")

                dir_fd = STATE.private_runtime_dir()
                entry = STATE.read_cache(dir_fd, STATE.cache_name("HDMI-A-1"))
                self.assertEqual(entry["percent"], 90)
                self.assertTrue(entry["available"])
                self.assertTrue(entry["lastSuccess"])
                os.close(dir_fd)
            finally:
                STATE.command_output = original_command
                if previous_runtime is None:
                    os.environ.pop("XDG_RUNTIME_DIR", None)
                else:
                    os.environ["XDG_RUNTIME_DIR"] = previous_runtime


if __name__ == "__main__":
    unittest.main()
