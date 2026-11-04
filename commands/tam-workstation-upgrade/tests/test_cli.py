import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CliTest(unittest.TestCase):
    def setUp(self):
        self.cli = load("cli")
        self.sha = "a" * 40
        self.product = "b" * 40
        self.inputs = {
            "tamlinux": {"owner": "greenermoose", "repo": "tamlinux", "rev": self.product}
        }
        self.docs = {
            f"{self.cli.release.API}/releases/tags/0.5.12": {
                "tag_name": "0.5.12",
                "draft": False,
                "prerelease": False,
            },
            f"{self.cli.release.API}/git/ref/tags/0.5.12": {
                "object": {"sha": self.sha, "type": "commit"}
            },
            f"{self.cli.release.RAW}/{self.sha}/deliveries/tamlinux-0.5.12.json": {
                "schemaVersion": 1,
                "id": "tamlinux-0.5.12",
                "version": "0.5.12",
                "components": self.inputs.copy(),
                "nativePackage": {
                    "name": "tamlinux-native",
                    "version": "0.5.12-0.1",
                    "sha256": "c" * 64,
                },
                "readiness": {"nativeInstallationRequired": True},
            },
            f"{self.cli.release.RAW}/{self.sha}/flake.lock": {
                "root": "root",
                "nodes": {
                    "root": {"inputs": {"tamlinux": "tamlinux"}},
                    "tamlinux": {"locked": self.inputs["tamlinux"]},
                },
            },
        }
        self.profile = {
            "hostname": "bosgame-tamlinux",
            "username": "fred",
            "architecture": "x86_64-linux",
            "config": "/tmp/config",
            "profile": "fred@bosgame-tamlinux",
            "capabilities": [],
            "assembly": "d" * 40,
            "generation": "/nix/store/fake-generation",
            "deployStage": "test",
            "native": {"name": "tamlinux-native", "version": "0.5.12-0.1"},
        }

    def fetch(self, url):
        return self.docs[url]

    def test_check_ready_json(self):
        with mock.patch.object(self.cli.host, "local_profile", return_value=self.profile):
            plan = self.cli.build_plan("0.5.12", fetch=self.fetch)
        self.assertEqual(plan["outcome"], "ready")
        self.assertEqual(plan["version"], "0.5.12")

    def test_revision_mismatch_refused(self):
        with mock.patch.object(self.cli.host, "local_profile", return_value=self.profile):
            with self.assertRaises(self.cli.UpgradeError):
                self.cli.build_plan("0.5.12", revision="e" * 40, fetch=self.fetch)

    def test_status_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            store = self.cli.receipt.Store(Path(temp))
            store.write({"id": "demo", "phase": "complete", "version": "0.5.12"})
            code = self.cli.status(store)
            self.assertEqual(code, 0)

    def test_concurrent_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            first = self.cli.receipt.Store(Path(temp))
            second = self.cli.receipt.Store(Path(temp))
            first.acquire()
            with self.assertRaises(self.cli.receipt.ReceiptError):
                second.acquire()
            first.release()


if __name__ == "__main__":
    unittest.main()
