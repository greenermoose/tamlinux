"""Build and install Tamlinux from the local component checkouts."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import BUILD_ENV, build, revisions
from preflight import build_problems, ownership_problems, runtime_problems
from transaction import inventory, read_json


def selected_stage(work, repos):
    stage = (work / "build").resolve(strict=True)
    if stage.parent != work / "stages":
        raise ValueError("selected stage is outside the build directory")
    manifest = stage / "manifest.json"
    receipt = read_json(manifest)
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if digest != stage.name:
        raise ValueError("selected stage manifest changed")
    if not receipt or receipt["components"] != revisions(repos):
        raise ValueError("run make before installing the selected revisions")
    return stage, digest, receipt


def preflight(work, repos, root):
    problems = build_problems(BUILD_ENV)
    problems.extend(runtime_problems(root))
    selection = work / "build"
    if selection.exists() or selection.is_symlink():
        stage, _, receipt = selected_stage(work, repos)
        files = inventory(stage / "payload")
        if not files or files != receipt["files"]:
            raise ValueError("stage files differ from the manifest")
        problems.extend(ownership_problems(root, files))
    if problems:
        raise ValueError("preflight found problems:\n  " + "\n  ".join(problems))
    print("Native build and runtime prerequisites passed.")
    if selection.exists():
        print("No Pacman-owned destinations in the selected stage.")
    else:
        print("Run make to stage the files, then repeat preflight to check destination ownership.")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=["preflight", "build", "install"])
parser.add_argument("--work", type=Path, required=True)
parser.add_argument("--repos", type=Path, default=Path(".."))
parser.add_argument("--root", type=Path)
args = parser.parse_args()
try:
    if args.action == "build":
        build(args.repos.resolve(), args.work.resolve())
    elif args.action == "preflight":
        preflight(args.work.resolve(), args.repos.resolve(), (args.root or Path("/")).resolve(strict=True))
    else:
        if args.root is None:
            raise ValueError("live installation is pending migration and candidate integration")
        stage, digest, _ = selected_stage(args.work.resolve(), args.repos.resolve())
        installer = Path(__file__).resolve().with_name("transaction.py")
        command = ["/usr/bin/python3", "-I", installer, "install", "--stage", stage,
                   "--digest", digest, "--root", args.root]
        subprocess.run(command, check=True)
except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
    raise SystemExit(f"Tamlinux source install: {exc}")
