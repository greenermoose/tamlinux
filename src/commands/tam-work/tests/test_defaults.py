"""Tests for default path resolution and CLI error reporting."""

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tam-work"
loader = importlib.machinery.SourceFileLoader("tam_work", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
tam_work = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tam_work)
resolve_paths = tam_work.resolve_paths


class Defaults(unittest.TestCase):
    """Default, environment and flag resolution for the registry and workspace."""

    def test_d1_defaults(self):
        registry, workspace = resolve_paths(None, None, {}, Path("/h"))
        self.assertEqual(
            (registry, workspace),
            (Path("/h/Code/tamlinux/worktrees/coordination"), Path("/h/Code/tamlinux")),
        )

    def test_d2_workspace_override(self):
        registry, workspace = resolve_paths(None, None, {"TAM_WORK_WORKSPACE": "/w"}, Path("/h"))
        self.assertEqual(
            (registry, workspace),
            (Path("/w/worktrees/coordination"), Path("/w")),
        )

    def test_d3_registry_override(self):
        registry, workspace = resolve_paths(None, None, {"TAM_WORK_REGISTRY": "/r"}, Path("/h"))
        self.assertEqual(
            (registry, workspace),
            (Path("/r"), Path("/h/Code/tamlinux")),
        )

    def test_d4_both_env_overrides(self):
        registry, workspace = resolve_paths(
            None, None, {"TAM_WORK_REGISTRY": "/r", "TAM_WORK_WORKSPACE": "/w"}, Path("/h")
        )
        self.assertEqual(
            (registry, workspace),
            (Path("/r"), Path("/w")),
        )

    def test_d5_flags_win_over_env(self):
        registry, workspace = resolve_paths(
            Path("/fr"), Path("/fw"), {"TAM_WORK_REGISTRY": "/r", "TAM_WORK_WORKSPACE": "/w"}, Path("/h")
        )
        self.assertEqual(
            (registry, workspace),
            (Path("/fr"), Path("/fw")),
        )

    def test_d6_flag_workspace_and_env_registry(self):
        registry, workspace = resolve_paths(None, Path("/fw"), {"TAM_WORK_REGISTRY": "/r"}, Path("/h"))
        self.assertEqual(
            (registry, workspace),
            (Path("/r"), Path("/fw")),
        )

    def test_d7_empty_env_falls_back_to_defaults(self):
        registry, workspace = resolve_paths(
            None, None, {"TAM_WORK_REGISTRY": "", "TAM_WORK_WORKSPACE": ""}, Path("/h")
        )
        self.assertEqual(
            (registry, workspace),
            (Path("/h/Code/tamlinux/worktrees/coordination"), Path("/h/Code/tamlinux")),
        )

    def test_d8_tilde_expansion_under_home(self):
        registry, workspace = resolve_paths(None, None, {"TAM_WORK_WORKSPACE": "~/ws"}, Path("/h"))
        self.assertEqual(
            (registry, workspace),
            (Path("/h/ws/worktrees/coordination"), Path("/h/ws")),
        )

    def test_d9_status_no_current_claims(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["HOME"] = temp_dir
            env["TAM_WORK_REGISTRY"] = str(Path(temp_dir) / "register")
            env.pop("TAM_WORK_WORKSPACE", None)
            env.pop("TAM_WORK_OWNER", None)
            env.pop("TAM_WORK_SESSION", None)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "status"],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "No current claims\n")

    def test_d10_release_unknown_id_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["HOME"] = temp_dir
            env["TAM_WORK_REGISTRY"] = str(Path(temp_dir) / "register")
            env.pop("TAM_WORK_WORKSPACE", None)
            env.pop("TAM_WORK_OWNER", None)
            env.pop("TAM_WORK_SESSION", None)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "release", "nope", "--owner", "x", "--note", "y"],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 1)
            self.assertTrue(result.stderr.startswith("tam-work: "))


if __name__ == "__main__":
    unittest.main()
