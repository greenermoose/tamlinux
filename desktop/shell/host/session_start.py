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
import sys
import tempfile
from pathlib import Path

HOST = Path(__file__).resolve().parent
SHELL = HOST.parent
sys.path.insert(0, str(HOST))

from registry import plugin_entries  # noqa: E402

QUICKSHELL = "/usr/bin/quickshell"


def config_home(environ: dict[str, str]) -> Path:
    if environ.get("XDG_CONFIG_HOME"):
        return Path(environ["XDG_CONFIG_HOME"])
    return Path(environ.get("HOME", "")) / ".config"


def session_environment(environ: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """The shell's environment, and what to say in the journal."""
    env = {key: value for key, value in environ.items() if not key.startswith("OMARCHY_")}
    notes: list[str] = []
    env.setdefault("QML_IMPORT_PATH", str(SHELL / "modules"))
    # Plugin helpers (fred.workspaces, fred.monitor) and the Sway adapter load
    # the compositor backend from here; without it they fail closed.
    env.setdefault("TAMLINUX_COMPOSITOR_COMMANDS", str(HOST))
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
