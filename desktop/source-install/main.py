"""Build and install Tamlinux from the local component checkouts."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import build, revisions
from transaction import read_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=["build", "install"])
parser.add_argument("--work", type=Path, required=True)
parser.add_argument("--repos", type=Path, default=Path(".."))
parser.add_argument("--root", type=Path)
args = parser.parse_args()
try:
    if args.action == "build":
        build(args.repos.resolve(), args.work.resolve())
    else:
        if args.root is None:
            raise ValueError("live installation is pending migration and candidate integration")
        work = args.work.resolve()
        stage = (work / "build").resolve(strict=True)
        if stage.parent != work / "stages":
            raise ValueError("selected stage is outside the build directory")
        manifest = stage / "manifest.json"
        receipt = read_json(manifest)
        if not receipt or receipt["components"] != revisions(args.repos.resolve()):
            raise ValueError("run make before installing the selected revisions")
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        if digest != stage.name:
            raise ValueError("selected stage manifest changed")
        installer = Path(__file__).resolve().with_name("transaction.py")
        command = ["/usr/bin/python3", "-I", installer, "install", "--stage", stage,
                   "--digest", digest, "--root", args.root]
        subprocess.run(command, check=True)
except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
    raise SystemExit(f"Tamlinux source install: {exc}")
