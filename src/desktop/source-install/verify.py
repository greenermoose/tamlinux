#!/usr/bin/python3 -I
"""Verify an installed Tamlinux source workstation as the regular user."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight import runtime_problems
from transaction import CULTIVAR_LINKS, Installation, PAYLOAD_CURRENT, read_json


def cursor_problems(root):
    icons = root / "usr/share/icons"
    themes = []
    index = icons / "default/index.theme"
    if index.is_file() and os.access(index, os.R_OK):
        for line in index.read_text().splitlines():
            if line.strip().startswith("Inherits="):
                themes.extend(item.strip() for item in line.split("=", 1)[1].split(",") if item.strip())
    if not themes:
        themes = ["Adwaita"]
    for theme in themes:
        candidate = icons / theme / "cursors/left_ptr"
        if candidate.is_file() and os.access(candidate, os.R_OK):
            return []
    return [f"default cursor theme chain ({', '.join(themes)}) has no readable cursors/left_ptr"]


def notes_problems(root):
    runtime = root / PAYLOAD_CURRENT
    version_file = runtime / "VERSION"
    bundle_file = runtime / "BUNDLE"
    notes_file = runtime / "share/tamlinux/version-notes.txt"
    version = None
    if version_file.is_file() and os.access(version_file, os.R_OK):
        version = version_file.read_text().strip() or None
    elif bundle_file.is_file() and os.access(bundle_file, os.R_OK):
        for line in bundle_file.read_text().splitlines():
            if line.startswith("version "):
                version = line.split(" ", 1)[1].strip()
                break
    else:
        return [f"missing or unreadable runtime identity: {version_file}"]
    if not version:
        return [f"missing version in {version_file if version_file.exists() else bundle_file}"]
    if not notes_file.is_file() or not os.access(notes_file, os.R_OK):
        return [f"missing or unreadable version notes: {notes_file}"]
    lines = notes_file.read_text().splitlines()
    expected_header = f"Tamlinux {version} version notes"
    if not lines or lines[0].strip() != expected_header:
        actual = lines[0] if lines else "<empty>"
        return [f"version notes header is {actual!r}, expected {expected_header!r}"]
    body = "\n".join(lines[1:]).strip()
    if not body:
        return [f"version notes body is empty in {notes_file}"]
    return []


def terminal_problems(root):
    problems = []
    for name in ("xdg-terminal-exec", "foot"):
        path = root / "usr/bin" / name
        if not (path.is_file() and os.access(path, os.X_OK)):
            problems.append(f"terminal command not executable: /{path.relative_to(root)}")
    if problems or root != Path("/"):
        return problems
    result = subprocess.run(
        ["/usr/bin/xdg-terminal-exec", "--print-cmd"],
        capture_output=True, text=True, timeout=10,
    )
    cmd = (result.stdout.strip().splitlines() or [""])[0].strip()
    if result.returncode != 0 or not cmd:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        return [f"xdg-terminal-exec could not resolve a terminal ({detail})"]
    if not (Path(cmd).is_absolute() and os.access(cmd, os.X_OK)) and not shutil.which(cmd, path="/usr/bin:/bin"):
        return [f"xdg-terminal-exec resolved {cmd!r}, which is not executable"]
    return []


def browser_problems(root):
    path = root / "usr/bin/chromium"
    if not (path.is_file() and os.access(path, os.X_OK)):
        return [f"default browser command not executable: /{path.relative_to(root)}"]
    return []


def permission_problems(system):
    problems = []
    if system.pending.exists():
        return [f"unfinished source transaction present: {system.pending}"]
    active = system.current()
    digest = active.get("current")
    if not digest:
        return [f"no active source installation recorded in {system.active}"]
    manifest_path = system.manifest_path(digest)
    if not manifest_path.is_file() or not os.access(manifest_path, os.R_OK):
        return [f"active manifest is unreadable by current user: {manifest_path}"]
    receipt = read_json(manifest_path)
    runtime = system.root / PAYLOAD_CURRENT
    if not runtime.is_dir() or not os.access(runtime, os.R_OK | os.X_OK):
        problems.append(f"active runtime is not readable/traversable: {runtime}")
    for rel, expected_target in CULTIVAR_LINKS:
        link = system.root / rel
        if not link.is_symlink() or link.readlink().as_posix() != expected_target:
            problems.append(f"cultivar symlink missing or unexpected: {link}")
    for relative, (mode, _) in sorted(receipt.get("files", {}).items()):
        target = system.root / relative
        needed = os.R_OK | (os.X_OK if mode & 0o111 else 0)
        if not target.is_file() or not os.access(target, needed):
            problems.append(f"installed path unreadable or not executable: {target}")
            if len(problems) >= 20:
                problems.append("... (more permission errors omitted)")
                break
    return problems


def session_problems(system):
    if system.root != Path("/"):
        return []
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path(os.environ["HOME"]) / ".config")
    problems = []
    for rel in ("tamlinux/session/hyprland.lua", "uwsm/env.d/10-tamlinux.sh"):
        target = config / rel
        if not target.is_file() or not os.access(target, os.R_OK):
            continue
        text = target.read_text()
        if "/nix/store/" in text:
            problems.append(f"session setting still references retired runtime: {target}")
    return problems


def verify_root(root, check_runtime=True):
    system = Installation(root)
    problems = []
    problems.extend(permission_problems(system))
    problems.extend(cursor_problems(root))
    problems.extend(notes_problems(root))
    problems.extend(terminal_problems(root))
    problems.extend(browser_problems(root))
    if check_runtime:
        problems.extend(runtime_problems(root))
    problems.extend(session_problems(system))
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--skip-runtime", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve(strict=True)
    if root == Path("/") and os.geteuid() == 0:
        raise ValueError("run make verify as your regular user, not root")
    problems = verify_root(root, check_runtime=not args.skip_runtime)
    if problems:
        raise ValueError("post-install verification failed:\n  " + "\n  ".join(problems))
    print("Tamlinux source verification passed (permissions, cursor, version notes, terminal, browser, prerequisites).")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"Tamlinux source verify: {exc}")
