"""Build and install Tamlinux from the local component checkouts."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import BUILD_ENV, build, revisions
from preflight import build_problems, missing_pacman_packages, runtime_problems
from transaction import Installation, verified_stage


def selected_stage(work, repos):
    stage = (work / "build").resolve(strict=True)
    if stage.parent != work / "stages":
        raise ValueError("selected stage is outside the build directory")
    digest = stage.name
    receipt = verified_stage(stage, digest)
    if receipt["components"] != revisions(repos):
        raise ValueError("run make before installing the selected revisions")
    return stage, digest, receipt


def preflight(work, repos, root):
    problems = build_problems(BUILD_ENV)
    problems.extend(runtime_problems(root))
    selection = work / "build"
    if selection.exists() or selection.is_symlink():
        _, _, receipt = selected_stage(work, repos)
        files = receipt["files"]
        system = Installation(root)
        try:
            system.check_ownership(files)
        except ValueError as error:
            problems.extend(str(error).splitlines())
    if problems:
        hint = ""
        try:
            missing = missing_pacman_packages(root)
        except ValueError:
            missing = []
        if missing:
            hint = "\nInstall missing Arch packages with:\n  pacman -S --needed " + " ".join(missing)
        raise ValueError("preflight found problems:\n  " + "\n  ".join(problems) + hint)
    print("Native build and runtime prerequisites passed.")
    if selection.exists():
        print("Destination ownership checks passed for the selected stage.")
    else:
        print("Run make to stage the files, then repeat preflight to check destination ownership.")


os.umask(0o022)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=["preflight", "build", "delivery", "install", "verify"])
parser.add_argument("--work", type=Path, required=True)
parser.add_argument("--repos", type=Path, default=Path(".."))
parser.add_argument("--root", type=Path)
args = parser.parse_args()
try:
    if args.action == "build":
        build(args.repos.resolve(), args.work.resolve())
    elif args.action == "preflight":
        preflight(args.work.resolve(), args.repos.resolve(), (args.root or Path("/")).resolve(strict=True))
    elif args.action == "verify":
        from verify import verify_root
        root = (args.root or Path("/")).resolve(strict=True)
        if root == Path("/") and os.geteuid() == 0:
            raise ValueError("run make verify as your regular user, not root")
        problems = verify_root(root)
        if problems:
            raise ValueError("post-install verification failed:\n  " + "\n  ".join(problems))
        print("Tamlinux source verification passed (permissions, cursor, version notes, terminal, browser, prerequisites).")
    elif args.action == "delivery":
        _, _, receipt = selected_stage(args.work.resolve(), args.repos.resolve())
        print(json.dumps({"format": 1, "backend": "source-install", "rootstock": "arch-systemd",
                          "version": receipt["version"], "components": receipt["components"]},
                         sort_keys=True))
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
