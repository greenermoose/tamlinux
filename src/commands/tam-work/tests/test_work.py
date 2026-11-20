"""Exercise checkout leases and clone identity against disposable real Git repos."""

import concurrent.futures
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parent.parent / "tam-work"
loader = importlib.machinery.SourceFileLoader("work_claims", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
work = importlib.util.module_from_spec(spec)
spec.loader.exec_module(work)


class Work(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.registry = self.workspace / "register"
        self.repo = self.workspace / "example"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q")
        self.git(self.repo, "config", "user.name", "Test")
        self.git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / "a").write_text("original\n")
        (self.repo / "b").write_text("original\n")
        self.git(self.repo, "add", "a", "b")
        self.git(self.repo, "commit", "-qm", "baseline")

    def git(self, root, *args):
        return work.git(root, *args)

    def begin(self, session="s1", scopes=None, cwd=None, **kwargs):
        kwargs.setdefault("exclusive", scopes is None)
        return work.begin(self.registry, self.workspace, cwd or self.repo,
                          "codex", session, scopes, "fix", **kwargs)

    def cli(self, *args, cwd=None, session="s1"):
        env = os.environ.copy()
        env.update(TAM_WORK_OWNER="codex", TAM_WORK_SESSION=session)
        return subprocess.run([sys.executable, str(SCRIPT), "--registry", str(self.registry),
                               "--workspace", str(self.workspace), *args],
                              cwd=cwd or self.repo, env=env, capture_output=True, text=True, timeout=30)

    def clone(self, name):
        root = self.workspace / "clones" / name
        root.parent.mkdir(exist_ok=True)
        self.git(self.workspace, "clone", "-q", str(self.repo), str(root))
        return root

    def test_default_claim_and_idempotent_resume_preserve_git(self):
        index = (self.repo / ".git/index").read_bytes()
        branch = self.git(self.repo, "symbolic-ref", "HEAD")
        row, resumed = self.begin()
        self.assertFalse(resumed)
        self.assertEqual(row["scopes"], ["example"])
        (self.repo / "a").write_text("ongoing\n")
        resumed_row, resumed = self.begin(scopes=["a"])
        self.assertTrue(resumed)
        self.assertEqual(resumed_row["id"], row["id"])
        self.assertEqual((self.repo / ".git/index").read_bytes(), index)
        self.assertEqual(self.git(self.repo, "symbolic-ref", "HEAD"), branch)

    def test_disjoint_files_share_a_checkout_but_overlaps_and_exclusive_conflict(self):
        first, _ = self.begin(scopes=["a"])
        self.assertEqual(first["mode"], "shared")
        second, _ = self.begin(session="s2", scopes=["b"])
        self.assertEqual(second["checkout"], first["checkout"])
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.begin(session="s3", scopes=["a"])
        with self.assertRaisesRegex(ValueError, "checkout held by"):
            self.begin(session="s3")

    def test_scope_or_exclusive_is_required(self):
        with self.assertRaisesRegex(ValueError, "--scope"):
            self.begin(scopes=None, exclusive=False)

    def test_exclusive_claim_blocks_shared_neighbours(self):
        self.begin()
        with self.assertRaisesRegex(ValueError, "held exclusively"):
            self.begin(session="s2", scopes=["b"])

    def test_session_grows_and_upgrades_its_own_claim(self):
        row, _ = self.begin(scopes=["a"])
        (self.repo / "a").write_text("mine\n")
        grown, resumed = self.begin(scopes=["b"])
        self.assertTrue(resumed)
        self.assertEqual(grown["id"], row["id"])
        self.assertEqual(grown["scopes"], ["example/a", "example/b"])
        neighbour, _ = self.begin(session="s2", scopes=["c"])
        with self.assertRaisesRegex(ValueError, "checkout held by"):
            self.begin(exclusive=True)
        work.finish(self.registry, str(self.repo), "codex", "s2", "done", neighbour["id"])
        upgraded, _ = self.begin(exclusive=True)
        self.assertEqual(upgraded["mode"], "exclusive")
        self.assertEqual(len([r for r in work.records(self.registry) if r["status"] == "active"]), 1)

    def test_dirty_preflight_covers_only_requested_paths(self):
        self.begin(scopes=["a"])
        (self.repo / "a").write_text("s1 in progress\n")
        (self.repo / "stray").write_text("unclaimed\n")
        self.begin(session="s2", scopes=["b"])
        with self.assertRaisesRegex(ValueError, "existing changes in the requested paths: example/stray"):
            self.begin(session="s3", scopes=["stray"])
        row, _ = self.begin(session="s3", scopes=["stray"], allow_dirty=True)
        self.assertTrue(row["dirty_at_start"])
        (self.repo / "fresh").mkdir()
        (self.repo / "fresh/x").write_text("untracked directory\n")
        with self.assertRaisesRegex(ValueError, "example/fresh/x"):
            self.begin(session="s4", scopes=["fresh/x"])

    def test_records_without_mode_keep_their_meaning(self):
        self.registry.mkdir()
        for ident, scopes in (("whole", ["example"]), ("paths", ["example/a"])):
            work.write_record(self.registry, dict(id=ident, owner="codex", session=ident, scopes=scopes,
                                                  checkout=str(self.repo), worktree=str(self.repo), repo="example",
                                                  note="pre-mode", status="active", created_at="x"))
        self.assertEqual(work.mode(work.records(self.registry)[0]), "shared")
        self.assertEqual(work.mode(work.records(self.registry)[1]), "exclusive")
        work.release(self.registry, "whole", "codex", "done", "whole")
        self.begin(session="s2", scopes=["b"])

    def test_path_limited_commit_leaves_neighbour_changes_out(self):
        self.begin(scopes=["a"])
        self.begin(session="s2", scopes=["b"])
        (self.repo / "a").write_text("s1\n")
        (self.repo / "b").write_text("s2 staged\n")
        self.git(self.repo, "add", "b")
        self.git(self.repo, "commit", "-qm", "s1 only", "--", "a")
        self.assertEqual(self.git(self.repo, "show", "--name-only", "--format=", "HEAD"), "a")
        self.assertEqual(self.git(self.repo, "diff", "--cached", "--name-only"), "b")

    def test_cli_begin_names_neighbours(self):
        self.begin(session="s2", scopes=["b"])
        result = self.cli("begin", "--scope", "a", "--note", "share")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Shared checkout; other sessions here:", result.stdout)
        self.assertIn("example/b", result.stdout)
        self.assertIn("shared]", result.stdout)

    def test_clone_scopes_share_namespace_but_disjoint_clones_can_work(self):
        clone = self.clone("codex-example")
        self.begin(scopes=["a"])
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.begin(session="s2", scopes=["a"], cwd=clone)
        row, _ = self.begin(session="s2", scopes=["b"], cwd=clone)
        self.assertEqual(row["scopes"], ["example/b"])
        self.assertEqual(row["checkout"], str(clone))

    def test_worktree_and_checkout_symlink_are_inferred(self):
        tree = self.workspace / "trees" / "task"
        self.git(self.repo, "worktree", "add", "-qb", "task", str(tree))
        row, _ = self.begin(cwd=tree, scopes=["a"])
        self.assertEqual(row["scopes"], ["example/a"])
        alias = self.workspace / "alias"
        alias.symlink_to(tree, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "checkout held"):
            self.begin(session="s2", cwd=alias)

    def test_workspace_root_clone_does_not_create_a_new_scope_namespace(self):
        clone = self.workspace / "example-copy"
        self.git(self.workspace, "clone", "-q", str(self.repo), str(clone))
        self.begin(scopes=["a"])
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.begin(session="s2", cwd=clone, scopes=["a"])
        row, _ = self.begin(session="s2", cwd=clone, scopes=["b"])
        self.assertEqual(row["scopes"], ["example/b"])

    def test_dirty_checkout_requires_acknowledgement_and_is_preserved(self):
        (self.repo / "a").write_text("someone else's work\n")
        with self.assertRaisesRegex(ValueError, "existing changes"):
            self.begin()
        self.assertEqual(work.records(self.registry), [])
        row, _ = self.begin(allow_dirty=True)
        self.assertTrue(row["dirty_at_start"])
        self.assertEqual((self.repo / "a").read_text(), "someone else's work\n")

    def test_finish_checks_session_and_leaves_uncommitted_work(self):
        row, _ = self.begin()
        (self.repo / "a").write_text("unfinished\n")
        with self.assertRaisesRegex(ValueError, "unique claim"):
            work.finish(self.registry, str(self.repo), "codex", "s2", "done", row["id"])
        with self.assertRaisesRegex(ValueError, "session"):
            work.release(self.registry, row["id"], "codex", "wrong")
        released = work.finish(self.registry, str(self.repo), "codex", "s1", "accepted")
        self.assertEqual(released["status"], "released")
        self.assertEqual((self.repo / "a").read_text(), "unfinished\n")
        self.begin(session="s2", allow_dirty=True)

    def test_legacy_checkout_reservation_cannot_be_adopted_by_tool_name(self):
        old = work.claim(self.registry, "old", "codex", ["example/a"], str(self.repo), "older session")
        self.assertNotIn("session", old)
        with self.assertRaisesRegex(ValueError, "legacy/see note"):
            self.begin(scopes=["b"])
        work.release(self.registry, "old", "codex", "explicit handoff")
        self.begin(scopes=["b"])

    def test_status_is_current_only_with_explicit_json_history(self):
        row, _ = self.begin()
        work.finish(self.registry, str(self.repo), "codex", "s1", "accepted")
        result = self.cli("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(row["id"], result.stdout)
        rows = json.loads(self.cli("status", "--all", "--json").stdout)
        self.assertEqual(rows[0]["id"], row["id"])
        self.assertEqual(json.loads(self.cli("status", "--json").stdout), [])

    def test_claim_race_gives_each_path_exactly_one_writer(self):
        def attempt(index):
            return self.cli("begin", "--scope", "a" if index % 2 else "b", "--note", "race", session=f"s{index}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(8)))
        self.assertEqual(sum(r.returncode == 0 for r in results), 2, results)
        self.assertEqual(sum("overlap" in r.stderr for r in results), 6)
        self.assertEqual(sorted(s for r in work.records(self.registry) for s in r["scopes"]), ["example/a", "example/b"])

    def test_scope_escape_and_symlink_aliases(self):
        outside = self.workspace / "outside"
        outside.mkdir()
        (self.repo / "escape").symlink_to(outside, target_is_directory=True)
        (self.repo / "alias").symlink_to("a")
        (self.repo / "metadata").symlink_to(".git")
        for value in ("../outside", "/absolute", ".git/index", "escape/file", "metadata/index"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                work.local_scopes(self.repo, "example", [value])
        self.assertEqual(work.local_scopes(self.repo, "example", ["alias"]), ["example/a", "example/alias"])

    def test_mismatched_clone_origin_cannot_override_repo_identity(self):
        clone = self.clone("clone")
        self.git(clone, "remote", "set-url", "origin", "https://example.invalid/other.git")
        with self.assertRaisesRegex(ValueError, "origin does not match"):
            self.begin(cwd=clone, repo="example")

    def test_remote_url_forms_map_to_same_repository(self):
        clone = self.clone("clone")
        self.git(self.repo, "remote", "add", "origin", "git@example.invalid:team/example.git")
        self.git(clone, "remote", "set-url", "origin", "https://example.invalid/team/example.git")
        row, _ = self.begin(cwd=clone)
        self.assertEqual(row["repo"], "example")

    def test_session_identity_requires_real_session_or_explicit_label(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "session identity required"):
                work.identity("claude")
            self.assertEqual(work.identity("claude", "fix-session"), ("claude", "fix-session"))
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}, clear=True):
            self.assertEqual(work.identity(), ("codex", "thread"))

    def test_additional_claims_require_explicit_finish_id(self):
        first, _ = self.begin(scopes=["a"])
        second, _ = self.begin(scopes=["b"], ident="second")
        with self.assertRaisesRegex(ValueError, "unique claim"):
            work.finish(self.registry, str(self.repo), "codex", "s1", "done")
        work.finish(self.registry, str(self.repo), "codex", "s1", "done", first["id"])
        self.begin(session="s2", scopes=["a"])
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.begin(session="s3", scopes=["b"])
        work.finish(self.registry, str(self.repo), "codex", "s1", "done", second["id"])
        self.begin(session="s3", scopes=["b"])


if __name__ == "__main__":
    unittest.main()
