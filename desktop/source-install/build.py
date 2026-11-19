"""Stage a workstation from committed, local Git objects."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

from preflight import build_problems
from transaction import PAYLOAD_CURRENT, inventory, write_json

PRODUCT = Path(__file__).resolve().parents[2]
COMPONENTS = ("libtam", "tam", "tamlinux-tools", "tam-edit", "tam-data")
BUILD_ENV = {
    "PATH": "/usr/bin:/bin",
    "LC_ALL": "C.UTF-8",
    "PKG_CONFIG_LIBDIR": "/usr/lib/pkgconfig:/usr/share/pkgconfig",
    "GIT_NO_LAZY_FETCH": "1",
}


def git(repo, *args):
    return subprocess.check_output(["/usr/bin/git", "-C", repo, *args], env=BUILD_ENV)


def revisions(repos):
    product = git(PRODUCT, "rev-parse", "HEAD").decode().strip()
    lock = git(PRODUCT, "show", f"{product}:components.lock").decode()
    pins = {}
    for line in lock.splitlines():
        name, revision = line.split()
        if name not in COMPONENTS or name in pins or not re.fullmatch("[a-f0-9]{40}", revision):
            raise ValueError(f"invalid component pin: {line}")
        pins[name] = revision
    for name in COMPONENTS:
        if name not in pins or not (repos / name / ".git").exists():
            raise ValueError(f"{name}: local clone and locked commit required in {repos}")
        try:
            git(repos / name, "cat-file", "-e", f"{pins[name]}^{{commit}}")
        except subprocess.CalledProcessError as error:
            raise ValueError(f"{name}: fetch locked commit {pins[name]} into the local clone") from error
    return {"tamlinux": product, **pins}


def snapshot(repo, revision, target):
    target.mkdir()
    with tempfile.TemporaryFile() as archive:
        subprocess.run(["/usr/bin/git", "-C", repo, "archive", revision],
                       stdout=archive, env=BUILD_ENV, check=True)
        archive.seek(0)
        with tarfile.open(fileobj=archive) as tree:
            tree.extractall(target, filter="data")


def render_version_notes(changelog, version):
    notes = changelog.split("\n## ")[1:]
    release = next((body for heading, _, body in (note.partition("\n") for note in notes)
                    if heading.split(" ", 1)[0].strip("[]") == version), None)
    if release is None:
        raise ValueError(f"CHANGELOG.md has no '## [{version}]' section")
    body = release.strip()
    if not body:
        raise ValueError(f"CHANGELOG.md section '## [{version}]' is empty")
    return f"Tamlinux {version} version notes\n\n{body}\n"


def build(repos, work):
    if os.geteuid() == 0:
        raise ValueError("run make as your regular user")
    problems = build_problems(BUILD_ENV)
    if problems:
        raise ValueError("missing build prerequisites:\n  " + "\n  ".join(problems))
    pins = revisions(repos)
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="build-", dir=work) as name:
        build_root = Path(name)
        stage = build_root / "payload"
        stage.mkdir()
        home = build_root / "home"
        home.mkdir()
        library = build_root / "libtam-built"
        env = BUILD_ENV | {
            "HOME": str(home),
            "GIT_CEILING_DIRECTORIES": str(build_root),
            "PKG_CONFIG_PATH": str(library / "lib/pkgconfig"),
        }

        def make(component, *args):
            subprocess.run(["/usr/bin/make", "-C", build_root / component, "-j2", *args],
                           env=env, check=True)

        for component, revision in pins.items():
            snapshot(PRODUCT if component == "tamlinux" else repos / component,
                     revision, build_root / component)

        make("libtam", "install", "install-display", "install-session", f"PREFIX={library}")
        link = f"LIBTAM_PREFIX={library}"
        placed = ("PREFIX=/usr", f"DESTDIR={stage}")
        make("tamlinux", "install-product", *placed, link, "TAM_SOURCE_INSTALL=1")
        product = build_root / "tamlinux"
        subprocess.run(["/usr/bin/python3", "-I", product / "desktop/install-bundle-layout.py",
                        "--source", "--prefix", "/usr", "--destdir", stage], env=env, check=True)

        private = "/" + PAYLOAD_CURRENT
        make("tam", "install", "install-tldr", *placed, link,
             f"BUNDLE_ROOT={private}", f"DATADIR={private}/share/tamlinux/knowledge",
             "DOCDIR=/usr/share/doc")
        make("tamlinux-tools", "install-file-select", "install-journal", *placed, link)
        make("tam-edit", "install", *placed, f"PKG_CONFIG_PATH={library}/lib/pkgconfig")
        make("tam-data", "install", *placed, link, f"TD_BUILD_ID={pins['tam-data'][:12]}")

        version = (product / "VERSION").read_text().strip()
        # The pinned tam reads cultivar identity through this record format.
        (stage / PAYLOAD_CURRENT / "BUNDLE").write_text(
            f"format 2\nname tamlinux\nversion {version}\n"
        )
        (stage / PAYLOAD_CURRENT / "share/tamlinux/version-notes.txt").write_text(
            render_version_notes((product / "CHANGELOG.md").read_text(), version)
        )
        receipt = {"version": version, "components": pins, "files": inventory(stage)}
        ready = build_root / "ready"
        ready.mkdir()
        write_json(ready / "manifest.json", receipt)
        digest = hashlib.sha256((ready / "manifest.json").read_bytes()).hexdigest()
        stage.rename(ready / "payload")
        stages = work / "stages"
        stages.mkdir(exist_ok=True)
        destination = stages / digest
        if destination.exists():
            if inventory(destination / "payload") != receipt["files"]:
                raise ValueError("an existing stage differs from its manifest")
        else:
            ready.rename(destination)
        link = build_root / "selected"
        link.symlink_to(destination.relative_to(work))
        link.replace(work / "build")
        print(f"Staged Tamlinux {version} in {destination}")
