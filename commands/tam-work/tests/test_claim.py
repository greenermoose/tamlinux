"""Check conflict detection and simultaneous writers, using temporary registries."""

import concurrent.futures
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tam-work"
loader = importlib.machinery.SourceFileLoader("claim", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
claim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claim)


class Claims(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.registry = Path(self.temporary.name)

    def add(self, ident, paths, observed=False):
        return claim.claim(self.registry, ident, "codex", paths, f"/worktree/{ident}", "test", observed)

    def test_equal_and_nested_paths_conflict_but_siblings_do_not(self):
        self.add("first", ["tamlinux/desktop/shell"])
        for path in ("tamlinux/desktop/shell", "tamlinux/desktop/shell/host/a.qml", "tamlinux/desktop"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "overlap"):
                self.add("second", [path])
        self.add("sibling", ["tamlinux/desktop/shell-other"])
        self.add("different-repo", ["config/desktop/shell"])

    def test_observation_reserves_scope_without_claiming_acknowledgement(self):
        self.assertEqual(self.add("observed", ["tamlinux"], True)["status"], "observed")
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.add("other", ["tamlinux/a"])

    def test_only_owner_releases_and_history_remains(self):
        self.add("first", ["tamlinux/a"])
        with self.assertRaisesRegex(ValueError, "owner"):
            claim.release(self.registry, "first", "other", "test")
        claim.release(self.registry, "first", "codex", "complete")
        self.add("second", ["tamlinux/a"])
        self.assertEqual(len(claim.records(self.registry)), 2)

    def test_invalid_scope_and_id_are_rejected(self):
        for path in ("../escape", "/absolute", "", ".", "a/../../b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.add("first", [path])
        with self.assertRaises(ValueError):
            self.add("../escape", ["a"])

    def test_bad_record_blocks_new_claim(self):
        (self.registry / "bad.json").write_text("{")
        with self.assertRaises(ValueError):
            self.add("first", ["a"])
        self.assertFalse((self.registry / "first.json").exists())

    def test_concurrent_processes_get_only_one_claim(self):
        # A session inherited from the caller would make all eight writers one session.
        env = {key: value for key, value in os.environ.items()
               if key not in ("TAM_WORK_SESSION", "CODEX_THREAD_ID", "CODEX_SESSION_ID", "CLAUDE_SESSION_ID")}

        def attempt(index):
            return subprocess.run([sys.executable, str(SCRIPT), "--registry", str(self.registry),
                                   "claim", f"writer-{index}", "--owner", "codex",
                                   "--scope", "repo/file", "--worktree", f"/tree-{index}", "--note", "race"],
                                  env=env, capture_output=True, text=True, timeout=10)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(8)))
        self.assertEqual(sum(item.returncode == 0 for item in results), 1)
        self.assertEqual(sum("overlap" in item.stderr for item in results), 7)
        self.assertEqual(len(claim.records(self.registry)), 1)


if __name__ == "__main__":
    unittest.main()
