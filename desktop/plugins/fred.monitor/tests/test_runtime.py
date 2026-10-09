import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch


PLUGIN = Path(__file__).resolve().parents[1]


def load(name):
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(PLUGIN / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATE = load("fred-monitor-state")
LAYOUT = load("fred-monitor-layout")


class SharedRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(self.root)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.parent = self.root / "tamlinux"
        self.parent.mkdir(mode=0o755)
        self.parent.chmod(0o755)

    def assert_refused(self):
        self.assertIsNone(STATE.private_runtime_dir())
        with self.assertRaises(LAYOUT.LayoutError):
            LAYOUT.runtime_directory()

    def test_shared_readable_parent_and_private_transaction_cache(self):
        fd = STATE.private_runtime_dir()
        self.assertIsNotNone(fd)
        try:
            STATE.write_cache(fd, "proof.json", {"percent": 80})
            self.assertEqual(STATE.read_cache(fd, "proof.json"), {"percent": 80})
        finally:
            os.close(fd)
        path = LAYOUT.runtime_directory()
        self.assertEqual(path, str(self.parent / "monitor"))
        fd = LAYOUT.open_runtime(path)
        try:
            LAYOUT.write_json_at(fd, "proof-layout.json", {"pending": True})
            self.assertEqual(LAYOUT.read_json_at(fd, "proof-layout.json"), {"pending": True})
        finally:
            os.close(fd)
        self.assertEqual(stat.S_IMODE(self.parent.stat().st_mode), 0o755)
        self.assertEqual(stat.S_IMODE(Path(path).stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((Path(path) / "proof.json").stat().st_mode), 0o600)

    def test_private_parent_is_also_supported(self):
        self.parent.chmod(0o700)
        fd = STATE.private_runtime_dir()
        self.assertIsNotNone(fd)
        os.close(fd)
        self.assertEqual(LAYOUT.runtime_directory(), str(self.parent / "monitor"))

    def test_layout_can_create_namespace_first(self):
        self.parent.rmdir()
        self.assertEqual(LAYOUT.runtime_directory(), str(self.parent / "monitor"))
        self.assertEqual(stat.S_IMODE(self.parent.stat().st_mode), 0o700)

    def test_writable_parent_is_rejected(self):
        for mode in (0o775, 0o757, 0o777):
            with self.subTest(mode=oct(mode)):
                self.parent.chmod(mode)
                self.assert_refused()
                self.assertFalse((self.parent / "monitor").exists())

    def test_symlink_parent_is_rejected_without_creating_data(self):
        self.parent.rmdir()
        target = self.root / "victim"
        target.mkdir(mode=0o700)
        self.parent.symlink_to(target, target_is_directory=True)
        self.assert_refused()
        self.assertEqual(list(target.iterdir()), [])

    def test_foreign_owner_parent_is_rejected(self):
        with patch.object(os, "getuid", return_value=os.getuid() + 1):
            self.assert_refused()
        self.assertFalse((self.parent / "monitor").exists())

    def test_symlink_child_is_rejected_without_creating_data(self):
        target = self.root / "victim"
        target.mkdir(mode=0o700)
        (self.parent / "monitor").symlink_to(target, target_is_directory=True)
        self.assert_refused()
        self.assertEqual(list(target.iterdir()), [])

    def test_public_child_is_rejected(self):
        child = self.parent / "monitor"
        child.mkdir(mode=0o755)
        self.assert_refused()
        self.assertEqual(stat.S_IMODE(child.stat().st_mode), 0o755)

    def test_monitor_facts_survive_unavailable_optional_cache(self):
        self.parent.chmod(0o777)
        monitors = [{"name": "DP-1", "width": 1920, "height": 1080, "scale": 1, "focused": True}]
        output = io.StringIO()
        with patch.object(STATE, "read_monitors", return_value=json.dumps(monitors)), contextlib.redirect_stdout(output):
            STATE.main(fast=True)
        data = json.loads(output.getvalue())
        self.assertEqual(data["focusedMonitor"], "DP-1")
        self.assertEqual([item["name"] for item in data["displays"]], ["DP-1"])
        self.assertFalse((self.parent / "monitor").exists())


if __name__ == "__main__":
    unittest.main()
