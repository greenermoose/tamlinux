#!/usr/bin/env python3
"""Arrange a completed private DESTDIR for the format-2 workstation recipe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys

SOURCE = Path(__file__).resolve().parents[1]
CURRENT = "/usr/lib/tamlinux/current"
SHARE = f"{CURRENT}/share/tamlinux"

# These expressions are used by the relocatable installation. Compile their
# private data path into the script that will run directly from /usr/bin.
DATA_PATHS = (
    '$(dirname "$(readlink -f "$0")")/../share/tamlinux',
    '$(dirname "$(readlink -f -- "$0")")/../share/tamlinux',
    '$(dirname "$(dirname "$(readlink -f "$0")")")/share/tamlinux',
    '$bin_dir/../share/tamlinux',
    '$base/../share/tamlinux',
    '$prefix/share/tamlinux',
    '$root/share/tamlinux',
)


def staging_root(prefix: str, destdir: str) -> Path:
    stage = Path(destdir)
    if prefix != "/usr" or not destdir or not stage.is_absolute() or stage.resolve() == Path("/"):
        raise ValueError("install-bundle requires PREFIX=/usr and an absolute staging DESTDIR")
    stage = stage.resolve()
    if stage.is_relative_to(Path("/usr")) or stage.is_relative_to(Path("/etc")):
        raise ValueError("DESTDIR must be a staging directory outside the system installation")
    return stage


def put(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    path.chmod(mode)


def move_tree(source: Path, dest: Path) -> None:
    if not source.is_dir() or source.is_symlink() or dest.exists() or dest.is_symlink():
        raise ValueError(f"Expected a real staged directory and a new destination for {source.name}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    source.rename(dest)


def render_commands(directory: Path) -> None:
    for command in sorted(directory.iterdir()):
        info = command.lstat()
        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o111:
            raise ValueError(f"Expected a real executable in usr/bin: {command.name}")
        data = command.read_bytes()
        if not data.startswith(b"#!"):
            continue
        content = data.decode("utf-8")
        for old in DATA_PATHS:
            content = content.replace(old, SHARE)
        content = content.replace(
            'self_dir.parent / "share/tamlinux/desktop/test-battery"',
            f'Path("{SHARE}/desktop/test-battery")',
        )
        content = content.replace(
            'HERE.parent / "libexec/tam-workstation-upgrade"',
            f'Path("{CURRENT}/libexec/tam-workstation-upgrade")',
        )
        if "../share/tamlinux" in content:
            raise ValueError(f"Unmapped relative product data path in {command.name}")
        if content.encode() != data:
            command.write_text(content)


def copy_vendor_defaults(stage: Path, source: Path) -> None:
    base = source / "desktop/native/defaults"
    root = base / "root"
    entries = json.loads((base / "origins.json").read_text())["files"]
    wants = []
    for name, record in sorted(entries.items()):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or not name.startswith(("usr/lib/", "usr/share/")):
            raise ValueError(f"Unsafe vendor default path {name}")
        original = root / relative
        if "link" in record:
            target = original.resolve(strict=True)
            if str(original.readlink()) != record["link"] or not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Vendor link differs from its origin record: {name}")
            if name.startswith("usr/lib/systemd/user/graphical-session.target.wants/"):
                wants.append(relative.name)
                continue
            if name != "usr/share/fontconfig/conf.default/50-tamlinux.conf":
                raise ValueError(f"Vendor link needs a format-2 placement rule: {name}")
            put(stage / relative, target.read_bytes())
            continue
        info = original.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"Vendor default must be a regular file: {name}")
        data = original.read_bytes()
        mode = stat.S_IMODE(info.st_mode)
        if hashlib.sha256(data).hexdigest() != record["sha256"] or f"{mode:04o}" != record["mode"]:
            raise ValueError(f"Vendor default differs from its origin record: {name}")
        put(stage / relative, data, mode)
    if wants:
        dropin = stage / "usr/lib/systemd/user/graphical-session.target.d/50-tamlinux-services.conf"
        put(dropin, ("[Unit]\nWants=" + " ".join(wants) + "\n").encode())


def install(stage: Path, source: Path = SOURCE) -> None:
    usr = stage / "usr"
    if not usr.is_dir() or usr.is_symlink():
        raise ValueError("Expected a staged usr directory")
    private = stage / CURRENT.lstrip("/")
    move_tree(usr / "share/tamlinux", private / "share/tamlinux")
    if (usr / "libexec").exists():
        move_tree(usr / "libexec", private / "libexec")
    units = usr / "lib/systemd/user"
    move_tree(usr / "share/systemd/user", units)
    (usr / "share/systemd").rmdir()
    for unit in sorted(units.iterdir()):
        unit.write_text(unit.read_text().replace("/usr/share/tamlinux", SHARE))
    render_commands(usr / "bin")
    put(usr / "bin/hi", b'#!/bin/sh\nexec /usr/bin/tam hi "$@"\n', 0o755)

    copy_vendor_defaults(stage, source)
    native = source / "desktop/native"
    integration = native / "integration"
    put(usr / "bin/tam-session", (integration / "session").read_bytes(), 0o755)
    browser = (native / "theme-browser-policy").read_bytes().replace(
        b"/usr/lib/tamlinux/browser_policy.py", f"{CURRENT}/lib/browser_policy.py".encode(),
    )
    put(usr / "bin/tam-theme-set-browser-policy", browser, 0o755)
    put(private / "lib/browser_policy.py", (native / "browser_policy.py").read_bytes())
    guard = source / "commands/tam-hyprland-reload-guard/tam-hyprland-reload-guard"
    put(private / "lib/hyprland-reload-guard", guard.read_bytes(), 0o755)
    put(usr / "lib/tmpfiles.d/tamlinux.conf", (integration / "tamlinux.conf").read_bytes())
    policy = (integration / "org.tamlinux.native.policy").read_bytes().replace(
        b"/usr/lib/tamlinux/asdcontrol", b"/usr/bin/asdcontrol",
    )
    put(usr / "share/polkit-1/actions/org.tamlinux.native.policy", policy)
    for hook in sorted(integration.glob("*.hook")):
        data = hook.read_bytes().replace(
            b"/usr/lib/tamlinux/hyprland-reload-guard", f"{CURRENT}/lib/hyprland-reload-guard".encode(),
        )
        put(usr / "share/libalpm/hooks" / hook.name, data)
    console = private / "share/tamlinux/console/welcome.issue"
    put(usr / "lib/issue.d/70-tamlinux.issue", console.read_bytes())
    providers = private / "share/tamlinux/provider-tools.json"
    values = json.loads(providers.read_text())
    values["asdcontrol"] = "/usr/bin/asdcontrol"
    providers.write_text(json.dumps(values, sort_keys=True) + "\n")

    # Only the shipped common defaults go here. Personal and host settings
    # enter a workstation capture through the separate settings workflow.
    bash = private / "defaults/home/.config/bash/tamlinux"
    shutil.copytree(source / "desktop/user-defaults/bash", bash)
    (bash / "env").write_text("# Tamlinux commands use the system PATH.\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--destdir", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        stage = staging_root(args.prefix, args.destdir)
        if not args.check:
            install(stage)
    except (OSError, ValueError) as error:
        print(f"install-bundle-layout: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
