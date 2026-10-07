#!/usr/bin/env python3
"""Start the Tamlinux shell for the session (plan 18 step 0.3.2 items 6 and 12).

The systemd unit runs `python3 -I <shell>/host/session_start.py`. With the bar
on, it maps the deployed plugins with registry.py and names the layout
document, then replaces itself with Quickshell on this shell directory. A
plugin that fails validation is left off the bar and named in the journal;
it does not stop the shell. With TAMLINUX_BAR=0 (services only) it only
starts Quickshell.

Anything already set in the environment wins, so a test can point the shell
at other plugins or another layout.
"""

from __future__ import annotations

import json
import os
import sys
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
    env = dict(environ)
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


def main() -> int:
    env, notes = session_environment(dict(os.environ))
    for note in notes:
        print(f"tamlinux-shell: {note}", file=sys.stderr, flush=True)
    os.execve(QUICKSHELL, [QUICKSHELL, "-p", str(SHELL)], env)
    return 1


if __name__ == "__main__":
    sys.exit(main())
