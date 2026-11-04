import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compat = load("compat")


class CompatTest(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "architecture": "x86_64-linux",
            "assembly": "a" * 40,
            "native": {"name": "tamlinux-native", "version": "0.5.12-0.1"},
        }
        self.record = {
            "schemaVersion": 1,
            "version": "0.5.12",
            "nativePackage": {
                "name": "tamlinux-native",
                "version": "0.5.12-0.1",
                "sha256": "b" * 64,
                "archive": "tamlinux-native-0.5.12-0.1-x86_64.pkg.tar.zst",
            },
            "readiness": {"nativeInstallationRequired": True},
        }
        self.selection = {"revision": "c" * 40, "record": self.record}

    def test_adapter_and_ready(self):
        result = compat.assess(self.profile, self.selection)
        self.assertEqual(result["outcome"], "ready")
        self.assertTrue(result["native"]["satisfied"])

    def test_missing_metadata_is_unknown(self):
        self.selection["record"] = {"schemaVersion": 1, "version": "0.5.12"}
        result = compat.assess(self.profile, self.selection)
        self.assertEqual(result["outcome"], "blocked_unknown_native")

    def test_native_mismatch_blocks(self):
        self.profile["native"] = {"name": "tamlinux-native", "version": "0.5.11-0.1"}
        result = compat.assess(self.profile, self.selection)
        self.assertEqual(result["outcome"], "blocked_native")

    def test_exact_assembly_is_no_change(self):
        self.selection["revision"] = self.profile["assembly"]
        result = compat.assess(self.profile, self.selection)
        self.assertEqual(result["outcome"], "no_change")

    def test_declared_compatibility_schema(self):
        self.selection["record"] = {
            "compatibility": {
                "schemaVersion": 1,
                "platforms": ["x86_64-linux"],
                "native": {"required": False},
            }
        }
        result = compat.assess(self.profile, self.selection)
        self.assertEqual(result["outcome"], "ready")


class ReceiptTest(unittest.TestCase):
    def test_lock_and_phases(self):
        receipt = load("receipt")
        with tempfile.TemporaryDirectory() as temp:
            store = receipt.Store(Path(temp))
            with store:
                body = {"id": store.new_id(), "phase": "planned", "version": "0.5.12"}
                written = store.write(body)
                self.assertEqual(store.read_current()["id"], written["id"])
                second = receipt.Store(Path(temp))
                with self.assertRaises(receipt.ReceiptError):
                    second.acquire()


if __name__ == "__main__":
    unittest.main()
