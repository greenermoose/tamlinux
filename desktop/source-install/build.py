"""Stage a workstation from committed, local Git objects with per-component caching."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile

from preflight import build_problems
from transaction import PAYLOAD_CURRENT, _clone_or_copy, inventory, write_json

PRODUCT = Path(__file__).resolve().parents[2]
COMPONENTS = ("libtam", "tam", "tamlinux-tools", "tam-edit", "tam-data")
CACHE_SCHEMA = "v2"
CACHE_KEEP = 2
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


def cache_key(*parts):
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()[:16]


def prune_cache(comp_dir, keep=CACHE_KEEP):
    entries = []
    for entry in comp_dir.iterdir():
        if not entry.name.startswith(".") and entry.is_dir() and not entry.is_symlink():
            entries.append((entry.stat().st_mtime_ns, entry))
    entries.sort(key=lambda item: item[0], reverse=True)
    for _, stale in entries[keep:]:
        shutil.rmtree(stale, ignore_errors=True)


def ensure_cached(cache_root, component, key, builder):
    comp_dir = cache_root / component
    comp_dir.mkdir(parents=True, exist_ok=True)
    target = comp_dir / key
    if target.is_dir() and not target.is_symlink():
        os.utime(target, None)
        prune_cache(comp_dir)
        return target, True
    tmp_dir = Path(tempfile.mkdtemp(prefix=".tmp-", dir=comp_dir))
    try:
        output = builder(tmp_dir, target)
        try:
            output.rename(target)
        except OSError:
            if not target.is_dir():
                raise
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
    os.utime(target, None)
    prune_cache(comp_dir)
    return target, False


def clone_tree(source, destination):
    for root, dirs, files in os.walk(source):
        rel_root = Path(root).relative_to(source)
        target_dir = destination / rel_root
        target_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        for name in dirs:
            d = target_dir / name
            d.mkdir(mode=0o755, exist_ok=True)
            os.chmod(d, 0o755)
        for name in files:
            src_file = Path(root) / name
            dst_file = target_dir / name
            if dst_file.exists() or dst_file.is_symlink():
                raise ValueError(f"component staging collision at {rel_root / name}")
            info = src_file.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"unexpected non-regular file in cache: {src_file}")
            mode = stat.S_IMODE(info.st_mode)
            fd = os.open(dst_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                with src_file.open("rb") as incoming, os.fdopen(fd, "wb") as outgoing:
                    _clone_or_copy(incoming, outgoing)
                    os.fchmod(outgoing.fileno(), mode)
            except BaseException:
                dst_file.unlink(missing_ok=True)
                raise


def build(repos, work):
    if os.geteuid() == 0:
        raise ValueError("run make as your regular user")
    problems = build_problems(BUILD_ENV)
    if problems:
        raise ValueError("missing build prerequisites:\n  " + "\n  ".join(problems))
    pins = revisions(repos)
    arch = os.uname().machine
    work.mkdir(parents=True, exist_ok=True)
    cache_root = work / "cache"
    cache_root.mkdir(exist_ok=True)
    jobs = f"-j{os.cpu_count() or 2}"
    hits = []
    built = []

    def record(name, hit):
        (hits if hit else built).append(name)

    def make_env(build_root, library=None):
        home = build_root / "home"
        home.mkdir(exist_ok=True)
        env = BUILD_ENV | {
            "HOME": str(home),
            "GIT_CEILING_DIRECTORIES": str(build_root),
        }
        if library is not None:
            env["PKG_CONFIG_PATH"] = str(library / "lib/pkgconfig")
        return env

    def run_make(src_dir, env, *args):
        subprocess.run(["/usr/bin/make", "-C", src_dir, jobs, *args], env=env, check=True)

    # 1. Build or reuse libtam (prefix pinned to its final cache directory so pkg-config paths stay valid).
    libtam_key = cache_key(CACHE_SCHEMA, "libtam", pins["libtam"], arch)

    def build_libtam(tmp_dir, target):
        src_dir = tmp_dir / "src"
        dest_root = tmp_dir / "dest"
        snapshot(repos / "libtam", pins["libtam"], src_dir)
        run_make(src_dir, make_env(tmp_dir), "install", "install-display", "install-session",
                 f"PREFIX={target}", f"DESTDIR={dest_root}")
        return dest_root / str(target).lstrip("/")

    library, hit = ensure_cached(cache_root, "libtam", libtam_key, build_libtam)
    record("libtam", hit)

    link = f"LIBTAM_PREFIX={library}"
    private = "/" + PAYLOAD_CURRENT
    component_trees = []

    # 2. Build or reuse tamlinux product + layout + identity/notes.
    tamlinux_key = cache_key(CACHE_SCHEMA, "tamlinux", pins["tamlinux"], libtam_key, arch, PAYLOAD_CURRENT)

    def build_tamlinux(tmp_dir, _target):
        src_dir = tmp_dir / "src"
        dest = tmp_dir / "dest"
        dest.mkdir()
        snapshot(PRODUCT, pins["tamlinux"], src_dir)
        env = make_env(tmp_dir, library)
        run_make(src_dir, env, "install-product", f"PREFIX={private}", f"DESTDIR={dest}",
                 link, "TAM_SOURCE_INSTALL=1")
        subprocess.run(["/usr/bin/python3", "-I", src_dir / "desktop/install-cultivar-layout.py",
                        "--prefix", private, "--destdir", dest], env=env, check=True)
        version = (src_dir / "VERSION").read_text().strip()
        (dest / PAYLOAD_CURRENT / "VERSION").write_text(f"{version}\n")
        (dest / PAYLOAD_CURRENT / "share/tamlinux/version-notes.txt").write_text(
            render_version_notes((src_dir / "CHANGELOG.md").read_text(), version)
        )
        return dest

    tamlinux_tree, hit = ensure_cached(cache_root, "tamlinux", tamlinux_key, build_tamlinux)
    record("tamlinux", hit)
    component_trees.append(tamlinux_tree)

    # 3. Build or reuse sibling components into their own cached DESTDIRs.
    def install_tam_edit(src, dest, env):
        run_make(src, env, "install", f"PREFIX={private}", f"DESTDIR={dest}",
                 f"PKG_CONFIG_PATH={library}/lib/pkgconfig")
        desktop_src = dest / PAYLOAD_CURRENT / "share/applications/tam-edit.desktop"
        if desktop_src.is_file():
            desktop_dst = dest / "usr/share/applications/tamlinux/tam-edit.desktop"
            desktop_dst.parent.mkdir(parents=True, exist_ok=True)
            content = desktop_src.read_text().replace("Exec=tam-edit", "Exec=/usr/bin/tamlinux/tam-edit")
            desktop_dst.write_text(content)
            desktop_dst.chmod(0o644)
            desktop_src.unlink()

    sibling_specs = (
        ("tam", lambda src, dest, env: run_make(
            src, env, "install", "install-tldr", f"PREFIX={private}", f"DESTDIR={dest}", link,
            f"BUNDLE_ROOT={private}", f"CULTIVAR_ROOT={private}",
            f"DATADIR={private}/share/tamlinux/knowledge", f"DOCDIR={private}/share/doc",
        )),
        ("tamlinux-tools", lambda src, dest, env: run_make(
            src, env, "install-file-select", "install-journal", f"PREFIX={private}", f"DESTDIR={dest}", link,
        )),
        ("tam-edit", install_tam_edit),
        ("tam-data", lambda src, dest, env: run_make(
            src, env, "install", f"PREFIX={private}", f"DESTDIR={dest}", link,
            f"TD_BUILD_ID={pins['tam-data'][:12]}",
        )),
    )

    for comp, runner in sibling_specs:
        comp_key = cache_key(CACHE_SCHEMA, comp, pins[comp], libtam_key, arch, PAYLOAD_CURRENT)

        def build_sibling(tmp_dir, _target, _comp=comp, _runner=runner):
            src_dir = tmp_dir / "src"
            dest = tmp_dir / "dest"
            dest.mkdir()
            snapshot(repos / _comp, pins[_comp], src_dir)
            _runner(src_dir, dest, make_env(tmp_dir, library))
            return dest

        comp_tree, hit = ensure_cached(cache_root, comp, comp_key, build_sibling)
        record(comp, hit)
        component_trees.append(comp_tree)

    hit_text = ", ".join(hits) if hits else "none"
    built_text = ", ".join(built) if built else "none"
    print(f"Build cache: hit [{hit_text}]; built [{built_text}]", flush=True)

    version = (tamlinux_tree / PAYLOAD_CURRENT / "VERSION").read_text().strip()
    with tempfile.TemporaryDirectory(prefix="build-", dir=work) as name:
        build_root = Path(name)
        stage = build_root / "payload"
        stage.mkdir()
        for tree in component_trees:
            clone_tree(tree, stage)
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
        link_path = build_root / "selected"
        link_path.symlink_to(destination.relative_to(work))
        link_path.replace(work / "build")
        print(f"Staged Tamlinux {version} in {destination}")
