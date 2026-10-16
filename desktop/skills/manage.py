#!/usr/bin/env python3
"""Register and verify the two delivered agent skills; preserve personal entries."""

import argparse
import json
import os
from pathlib import Path
import sys
import uuid

SKILLS = ("tamlinux", "diagnose-crash")
DIRECTORIES = (".agents/skills", ".claude/skills", ".codex/skills",
               ".pi/agent/skills", ".hermes/skills")
INHERITED = Path("/usr/share/omarchy")


def resolves(path):
    try:
        return path.resolve()
    except (OSError, RuntimeError):
        return None


def inherited(path):
    target = resolves(path)
    return path.is_symlink() and target is not None and target.is_relative_to(INHERITED)


def owned(path, target):
    # A direct stable link is recognizable even after an older generation
    # removes the data-directory endpoint. Do not adopt another personal link.
    if not path.is_symlink():
        return False
    raw = Path(os.readlink(path))
    return (raw if raw.is_absolute() else path.parent / raw) == target


def inspect(home, data_home, store):
    issues = []
    root = data_home / "tamlinux/skills"
    expected = store.resolve()
    if resolves(root) != expected:
        issues.append(f"Skill data root does not match the selected package: {root}")
    for name in SKILLS:
        if not (root / name / "SKILL.md").is_file():
            issues.append(f"Missing delivered skill: {root / name / 'SKILL.md'}")
    for relative in DIRECTORIES:
        directory = home / relative
        if not directory.is_dir():
            issues.append(f"Missing agent skill directory: {directory}")
            continue
        for entry in directory.iterdir():
            if entry.name == "omarchy" or inherited(entry):
                issues.append(f"Inherited agent skill: {entry}")
        for name in SKILLS:
            entry = directory / name
            if (not (entry / "SKILL.md").is_file()
                    or resolves(entry) != expected / name):
                issues.append(f"Agent skill does not match the selected package: {entry}")
    return issues


def install(home, data_home, managed):
    """Preflight every registration before removing or replacing any entry."""
    root = data_home / "tamlinux/skills"
    for name in SKILLS:
        if not (root / name / "SKILL.md").is_file():
            raise ValueError(f"Install the selected skill data first: {root / name}")
    directories = [home / relative for relative in DIRECTORIES]
    for directory in directories:
        target = resolves(directory)
        if target is not None and target.is_relative_to(INHERITED):
            raise ValueError(f"Preserving inherited whole-directory link: {directory}")
        entry = directory / "omarchy"
        if os.path.lexists(entry) and not inherited(entry):
            raise ValueError(f"Preserving personal entry named omarchy: {entry}")
    for relative in managed:
        directory = home / relative
        # Check existing ancestors too: mkdir must not fail halfway through
        # installation because a personal regular file occupies an ancestor.
        for parent in (directory, *directory.parents):
            if parent == home.parent:
                break
            if os.path.lexists(parent) and not parent.is_dir():
                raise ValueError(f"Preserving non-directory agent path: {parent}")
        for name in SKILLS:
            entry = directory / name
            if os.path.lexists(entry) and not (inherited(entry) or owned(entry, root / name)):
                raise ValueError(f"Preserving personal skill entry: {entry}")
    # Whole-directory managers supply the two links themselves. Verify them
    # before cleanup so a missing consumer link cannot produce a partial cutover.
    for relative in set(DIRECTORIES) - set(managed):
        for name in SKILLS:
            entry = home / relative / name
            if not (entry / "SKILL.md").is_file() or resolves(entry) != resolves(root / name):
                raise ValueError(f"Whole-directory manager must supply Tamlinux skill: {entry}")
    for directory in directories:
        if directory.is_dir():
            for entry in directory.iterdir():
                if inherited(entry):
                    entry.unlink()
                    print(f"Removed inherited skill link: {entry}")
    for relative in managed:
        directory = home / relative
        directory.mkdir(parents=True, exist_ok=True)
        for name in SKILLS:
            entry, target = directory / name, root / name
            if owned(entry, target):
                continue
            temporary = directory / f".tamlinux-skill-{uuid.uuid4().hex}"
            try:
                temporary.symlink_to(target)
                os.replace(temporary, entry)
            finally:
                temporary.unlink(missing_ok=True)
            print(f"Registered Tamlinux skill: {entry}")


def uninstall(home, data_home, managed):
    for relative in managed:
        for name in SKILLS:
            entry = home / relative / name
            if owned(entry, data_home / "tamlinux/skills" / name):
                entry.unlink()
                print(f"Removed Tamlinux skill registration: {entry}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--uninstall", action="store_true")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--data-home", type=Path)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--managed-directory", nargs="*", choices=DIRECTORIES)
    args = parser.parse_args()
    home = args.home.absolute()
    data = (args.data_home or Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))).absolute()
    managed = DIRECTORIES if args.managed_directory is None else args.managed_directory
    try:
        if args.install:
            # Check the immutable endpoint before allowing any link changes.
            if resolves(data / "tamlinux/skills") != args.store.resolve():
                raise ValueError("Skill data root does not match the selected package")
            install(home, data, managed)
        if args.uninstall:
            uninstall(home, data, managed)
            return 0
        issues = inspect(home, data, args.store)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps({"ok": not issues, "issues": issues}, indent=2))
    return bool(issues)


if __name__ == "__main__":
    sys.exit(main())
