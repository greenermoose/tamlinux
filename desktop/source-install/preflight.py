"""Inspect native prerequisites and package ownership without changing the target."""
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess

BUILD_COMMANDS = {
    "ar": "binutils", "cc": "gcc", "file": "file", "git": "git", "make": "make",
    "pkg-config": "pkgconf", "python3": "python",
}
BUILD_HEADERS = (
    ("dbus-1", "dbus/dbus.h", "dbus"),
    ("libdrm", "drm_mode.h", "libdrm"),
    ("libsystemd", "systemd/sd-device.h", "systemd-libs"),
    ("libcpuid", "libcpuid.h", "libcpuid"),
    ("libarchive", "archive.h", "libarchive"),
    ("ncursesw", "curses.h", "ncurses"),
    ("zlib", "zlib.h", "zlib"),
    (None, "magic.h", "file"),
)

# Source equivalents of the native prerequisites in the workstation recipe.
RUNTIME_COMMANDS = {
    "sh": "bash", "bash": "bash", "env": "coreutils", "python3": "python>=3.12",
    "Hyprland": "hyprland>=0.56", "start-hyprland": "hyprland",
    "quickshell": "quickshell>=0.3", "qs": "quickshell", "uwsm": "uwsm", "jq": "jq",
    "nft": "nftables", "mandb": "man-db", "systemctl": "systemd",
    "foot": "foot", "xdg-terminal-exec": "xdg-terminal-exec",
}
RUNTIME_FILES = {
    "usr/lib/qt6/qml/Quickshell/Wayland/qmldir": "quickshell",
    "usr/share/icons/Adwaita/cursors/left_ptr": "adwaita-cursors",
    "usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf": "ttf-jetbrains-mono-nerd",
    "usr/lib/libhyprbars.so": "hyprland-plugin-hyprbars",
    "lib64/ld-linux-x86-64.so.2": "glibc", "usr/lib/libc.so.6": "glibc",
    "usr/lib/libm.so.6": "glibc", "usr/lib/libmagic.so.1": "file",
    "usr/lib/libcpuid.so.18": "libcpuid", "usr/lib/libdbus-1.so.3": "dbus",
    "usr/lib/libsystemd.so.0": "systemd-libs", "usr/lib/libz.so.1": "zlib",
    "usr/lib/libncursesw.so.6": "ncurses",
}
ARCH_PACKAGES = Path(__file__).resolve().with_name("arch-packages")


def declared_packages(path=ARCH_PACKAGES):
    packages = []
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            packages.append(line)
    return packages


def missing_pacman_packages(root, path=ARCH_PACKAGES):
    if not path.is_file():
        return []
    specs = declared_packages(path)
    missing = pacman_query(root, "-T", "--", *specs, missing=specs)
    return [spec.split(">=", 1)[0].split("=", 1)[0] for spec in missing]


def build_problems(env):
    tools = {name: shutil.which(name, path=env["PATH"]) for name in BUILD_COMMANDS}
    problems = [f"{name} (Arch package: {package})" for name, package in BUILD_COMMANDS.items()
                if tools[name] is None]
    for module, header, package in BUILD_HEADERS:
        flags = []
        if module:
            if tools["pkg-config"] is None:
                continue
            probe = subprocess.run([tools["pkg-config"], "--cflags", module],
                                   env=env, capture_output=True, text=True)
            if probe.returncode:
                problems.append(f"pkg-config:{module} (Arch package: {package})")
                continue
            flags = shlex.split(probe.stdout)
        if tools["cc"] and subprocess.run(
            [tools["cc"], *flags, "-fsyntax-only", "-x", "c", "-"],
            input=f"#include <{header}>\n", text=True, env=env, capture_output=True,
        ).returncode:
            problems.append(f"header {header} (Arch package: {package})")
    if tools["python3"] and subprocess.run(
        [tools["python3"], "-I", "-B", "-c", "from fontTools.ttLib import TTFont"],
        env=env, capture_output=True,
    ).returncode:
        problems.append("fontTools.ttLib (Arch package: python-fonttools)")
    return problems


def pacman_query(root, *args, missing=()):
    db = root / "var/lib/pacman"
    local = db / "local"
    version = local / "ALPM_DB_VERSION"
    if (not local.is_dir() or not os.access(local, os.R_OK | os.X_OK)
            or not version.is_file() or not os.access(version, os.R_OK)):
        raise ValueError(f"cannot read the local Pacman database at {db}")
    result = subprocess.run(
        ["/usr/bin/pacman", "--config", "/dev/null", "--dbpath", db, *args],
        env={"PATH": "/usr/bin", "LC_ALL": "C"}, capture_output=True, text=True,
    )
    lines = result.stdout.splitlines()
    valid = result.returncode == 0 or (
        result.returncode == 127 and lines and set(lines) <= set(missing)
    )
    if not valid or result.stderr:
        detail = result.stderr.strip() or f"query exited with status {result.returncode}"
        raise ValueError(f"cannot query the local Pacman database at {db}: {detail}")
    return lines


def native_file(root, path, mode):
    # A system provider may use symlinks within /usr (for example qs).
    resolved = (root / path).resolve()
    return (resolved.is_relative_to(root / "usr") and resolved.is_file()
            and os.access(resolved, mode))


def runtime_problems(root):
    release = root / "usr/lib/os-release"
    if (platform.machine() != "x86_64" or not native_file(root, "usr/lib/os-release", os.R_OK)
            or not any(line in ('ID=arch', 'ID="arch"') for line in release.read_text().splitlines())):
        return ["runtime preflight requires x86_64 Arch Linux with systemd"]
    requirements = sorted(set(RUNTIME_COMMANDS.values()) | set(RUNTIME_FILES.values()))
    missing = pacman_query(root, "-T", "--", *requirements, missing=requirements)
    problems = [f"missing Arch package dependency: {package}" for package in missing]
    for name, package in RUNTIME_COMMANDS.items():
        path = f"usr/bin/{name}"
        if not native_file(root, path, os.X_OK):
            problems.append(f"missing native executable /{path} (Arch package: {package})")
    for path, package in RUNTIME_FILES.items():
        if not native_file(root, path, os.R_OK):
            problems.append(f"missing native file /{path} (Arch package: {package})")
    return problems


def destination_owners(root, destinations):
    paths = {f"/{name}" for name in destinations}
    owners = {}
    for line in pacman_query(root, "-Ql"):
        package, separator, path = line.partition(" ")
        if not separator or not path.startswith("/"):
            raise ValueError(f"unexpected Pacman file listing: {line}")
        if path.rstrip("/") in paths:
            owners.setdefault(path.strip("/"), set()).add(package)
    return owners


def ownership_problems(root, destinations):
    # Listing the database also detects owned files that are absent on disk.
    return sorted(f"source destination /{path} is owned by Arch package {package}"
                  for path, packages in destination_owners(root, destinations).items()
                  for package in packages)
