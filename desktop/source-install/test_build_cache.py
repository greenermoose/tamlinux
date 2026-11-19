"""Verify per-component build cache hits, pruning, and collision guards."""
from pathlib import Path
import tempfile
import time
import unittest

import build


class BuildCacheTests(unittest.TestCase):
    def test_cache_hit_skips_builder_and_prunes_stale_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_root = Path(tmp) / "cache"
            calls = []

            def make_builder(payload_text):
                def _builder(tmp_dir, _target):
                    calls.append(payload_text)
                    out = tmp_dir / "dest"
                    out.mkdir()
                    (out / "usr/bin").mkdir(parents=True)
                    f = out / "usr/bin/demo"
                    f.write_text(payload_text)
                    f.chmod(0o755)
                    return out
                return _builder

            p1, hit1 = build.ensure_cached(cache_root, "tam", "key1", make_builder("v1"))
            self.assertFalse(hit1)
            self.assertEqual(calls, ["v1"])

            p1_again, hit2 = build.ensure_cached(cache_root, "tam", "key1", make_builder("v1-rebuilt"))
            self.assertTrue(hit2)
            self.assertEqual(p1, p1_again)
            self.assertEqual(calls, ["v1"])
            self.assertEqual((p1_again / "usr/bin/demo").read_text(), "v1")

            time.sleep(0.01)
            p2, hit3 = build.ensure_cached(cache_root, "tam", "key2", make_builder("v2"))
            self.assertFalse(hit3)
            time.sleep(0.01)
            p3, hit4 = build.ensure_cached(cache_root, "tam", "key3", make_builder("v3"))
            self.assertFalse(hit4)

            # Only last 2 revisions are retained (key2, key3); key1 is pruned.
            self.assertFalse(p1.exists())
            self.assertTrue(p2.is_dir())
            self.assertTrue(p3.is_dir())

    def test_clone_tree_merges_and_rejects_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            c1 = root / "c1"
            c2 = root / "c2"
            stage = root / "stage"
            stage.mkdir()
            (c1 / "usr/bin").mkdir(parents=True)
            (c1 / "usr/bin/a").write_text("alpha")
            (c1 / "usr/bin/a").chmod(0o755)
            (c2 / "usr/bin").mkdir(parents=True)
            (c2 / "usr/bin/b").write_text("beta")
            (c2 / "usr/bin/b").chmod(0o755)

            build.clone_tree(c1, stage)
            build.clone_tree(c2, stage)
            self.assertEqual((stage / "usr/bin/a").read_text(), "alpha")
            self.assertEqual((stage / "usr/bin/b").read_text(), "beta")
            self.assertEqual((stage / "usr/bin/a").stat().st_mode & 0o777, 0o755)

            with self.assertRaisesRegex(ValueError, "collision"):
                build.clone_tree(c1, stage)


if __name__ == "__main__":
    unittest.main()
