#!/usr/bin/env python3
"""Start the Tamlinux shell for the session (plan 18 step 0.3.2 items 6 and 12).

The systemd unit runs `python3 -I <shell>/host/session_start.py`. With the bar
on, it maps the deployed plugins with registry.py and names the layout
document, then replaces itself with Quickshell on this shell directory. A
plugin that fails validation is left off the bar and named in the journal;
it does not stop the shell. With TAMLINUX_BAR=0 (services only) it only
starts Quickshell.

Tamlinux overrides already set in the environment win, so a test can point the
shell at other plugins or another layout. Prior-owner variables are discarded.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HOST = Path(__file__).resolve().parent
SHELL = HOST.parent
sys.path.insert(0, str(HOST))

from registry import plugin_entries  # noqa: E402

QUICKSHELL = "/usr/bin/quickshell"

# Fault H: menu-launched Arch Qt apps must not inherit the shell's Nix Qt
# paths or shell-only PATH / platform overrides. Keys listed in
# TAMLINUX_LAUNCH_HOST_ENV are stripped or restored for every host child.
LAUNCH_HOST_KEYS = (
    "QT_PLUGIN_PATH",
    "NIXPKGS_QT6_QML_IMPORT_PATH",
    "QML_IMPORT_PATH",
    "QT_QPA_PLATFORM",
    "PATH",
)
# Always remove these from host children; Arch Qt resolves its own plugins.
LAUNCH_HOST_UNSET = frozenset({
    "QT_PLUGIN_PATH",
    "NIXPKGS_QT6_QML_IMPORT_PATH",
    "QML_IMPORT_PATH",
})


def config_home(environ: dict[str, str]) -> Path:
    if environ.get("XDG_CONFIG_HOME"):
        return Path(environ["XDG_CONFIG_HOME"])
    return Path(environ.get("HOME", "")) / ".config"


def shell_version(shell: Path = SHELL) -> str:
    """Read this shell's package metadata (or VERSION in a source checkout)."""
    packaged = shell.parent / "version"
    source = shell.parent.parent / "VERSION"
    try:
        return (packaged if packaged.exists() else source).read_text().strip()
    except OSError:
        return "unknown"


def compositor_version(environ: dict[str, str]) -> str:
    """Read the active Hyprland version once for the shared shell process."""
    if not environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return ""
    allowed = ("HOME", "XDG_RUNTIME_DIR", "HYPRLAND_INSTANCE_SIGNATURE")
    try:
        result = subprocess.run(
            ["/usr/bin/hyprctl", "version", "-j"],
            env={key: environ[key] for key in allowed if key in environ},
            capture_output=True, text=True, timeout=2, check=True,
        )
        version = json.loads(result.stdout[:8192]).get("version", "")
        return version if isinstance(version, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", version) else ""
    except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
        return ""

def hyprland_environ(environ: dict[str, str]) -> dict[str, str]:
    """Read the compositor's environment for host-app restores (Fault H)."""
    signature = environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    runtime = environ.get("XDG_RUNTIME_DIR")
    if not signature or not runtime:
        return {}
    # hyprland stores a pid file under XDG_RUNTIME_DIR/hypr/<signature>/hyprland.lock
    # Fallback: scan /proc for Hyprland belonging to this user.
    try:
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                cmdline = (entry / "cmdline").read_bytes().split(b"\0", 1)[0]
            except OSError:
                continue
            base = cmdline.rsplit(b"/", 1)[-1]
            if base != b"Hyprland":
                continue
            try:
                raw = (entry / "environ").read_bytes()
            except OSError:
                continue
            values: dict[str, str] = {}
            for item in raw.split(b"\0"):
                if not item or b"=" not in item:
                    continue
                key, _, value = item.partition(b"=")
                try:
                    values[key.decode()] = value.decode()
                except UnicodeDecodeError:
                    continue
            if values.get("HYPRLAND_INSTANCE_SIGNATURE") == signature:
                return values
    except OSError:
        return {}
    return {}


def host_path(path: str) -> str:
    """Drop Nix store entries so Arch apps resolve /usr binaries first."""
    kept = [entry for entry in path.split(":") if entry and not entry.startswith("/nix/store/")]
    return ":".join(kept) if kept else "/usr/local/bin:/usr/bin"


def save_launch_host_environment(env: dict[str, str], session: dict[str, str]) -> None:
    """Record session values for Util.hostEnvironment to restore into children."""
    present: list[str] = []
    for key in LAUNCH_HOST_KEYS:
        backup = f"TAMLINUX_HOST_{key}"
        env.pop(backup, None)
        if key in LAUNCH_HOST_UNSET:
            continue
        if key == "PATH":
            value = session.get("PATH") or host_path(env.get("PATH", ""))
            env[backup] = host_path(value)
            present.append(key)
        elif key == "QT_QPA_PLATFORM":
            value = session.get("QT_QPA_PLATFORM") or "wayland;xcb"
            env[backup] = value
            present.append(key)
        elif key in session:
            env[backup] = session[key]
            present.append(key)
    env["TAMLINUX_LAUNCH_HOST_ENV"] = " ".join(LAUNCH_HOST_KEYS)
    if present:
        env["TAMLINUX_HOST_PRESENT"] = " ".join(present)
    else:
        env.pop("TAMLINUX_HOST_PRESENT", None)


def session_environment(environ: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """The shell's environment, and what to say in the journal."""
    env = {key: value for key, value in environ.items() if not key.startswith("OMARCHY_")}
    notes: list[str] = []
    session = hyprland_environ(env)
    save_launch_host_environment(env, session)
    env.setdefault("QML_IMPORT_PATH", str(SHELL / "modules"))
    # Plugin helpers (fred.workspaces, fred.monitor) and the Sway adapter load
    # the compositor backend from here; without it they fail closed.
    env.setdefault("TAMLINUX_COMPOSITOR_COMMANDS", str(HOST))
    # Always describe the shell being launched, never an inherited selection.
    env["TAMLINUX_VERSION"] = shell_version()
    env["TAMLINUX_HYPRLAND_VERSION"] = compositor_version(env)
    if env.get("TAMLINUX_BAR") == "0":
        return env, notes
    config = config_home(env)
    env.setdefault("TAMLINUX_BAR_LAYOUT", str(config / "tamlinux" / "shell" / "layout.json"))
    if "TAMLINUX_PLUGIN_ENTRIES" not in env:
        plugins = Path(env.get("TAMLINUX_PLUGINS_DIR") or config / "tamlinux" / "plugins")
        entries, problems = plugin_entries(plugins)
        notes.extend(f"left off the bar: {problem}" for problem in problems)
        notes.append(f"plugins: {', '.join(sorted(entries)) or 'none'}")
        env["TAMLINUX_PLUGIN_ENTRIES"] = json.dumps(entries, sort_keys=True)
    return env, notes


def initialize_defaults(environ: dict[str, str]) -> None:
    """Publish absent mutable defaults atomically, preserving existing files/links."""
    if not environ.get("HOME") and not environ.get("XDG_CONFIG_HOME"):
        raise ValueError("HOME or XDG_CONFIG_HOME is required for mutable defaults")
    config = config_home(environ) / "tamlinux" / "shell"
    layout = Path(environ.get("TAMLINUX_BAR_LAYOUT") or config / "layout.json")
    defaults = [(config / "settings.json", '{"version": 1, "entries": {}}\n')]
    if environ.get("TAMLINUX_BAR") != "0":
        defaults.append((layout, (SHELL / "bar" / "default-layout.json").read_text()))
    if any(not target.is_absolute() for target, _ in defaults):
        raise ValueError("Mutable default destinations must be absolute")
    for target, contents in defaults:
        if target.exists() or target.is_symlink():
            continue
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".tamlinux-default-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "w") as stream:
                stream.write(contents)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                pass  # A concurrent writer owns the destination now.
        finally:
            Path(temporary).unlink(missing_ok=True)


def main() -> int:
    env, notes = session_environment(dict(os.environ))
    for note in notes:
        print(f"tamlinux-shell: {note}", file=sys.stderr, flush=True)
    quickshell = env.get("TAMLINUX_QUICKSHELL") or QUICKSHELL
    if not Path(quickshell).is_absolute():
        print("tamlinux-shell: selected Quickshell executable must be absolute", file=sys.stderr)
        return 2
    initialize_defaults(env)
    os.execve(quickshell, [quickshell, "-p", str(SHELL)], env)
    return 1


if __name__ == "__main__":
    sys.exit(main())
