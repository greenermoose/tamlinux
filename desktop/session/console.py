"""Start the installed desktop only from an authenticated foreground text VT."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def query(*args):
    result = subprocess.run(args, capture_output=True, text=True, check=True, timeout=3)
    if len(result.stdout) > 65536:
        raise ValueError("unexpectedly large session status")
    return result.stdout


def session_environment(tty, uid, foreground, command=query):
    if uid == 0 or not re.fullmatch(r"/dev/tty[1-9][0-9]*", tty) or not foreground:
        raise ValueError("run tam-desktop as your user from a foreground text console")
    fields = ("Active", "Remote", "Type", "Class", "User", "VTNr", "Seat", "Id")
    output = command("/usr/bin/loginctl", "show-session", "self", "--no-pager",
                     *[f"--property={field}" for field in fields])
    session = dict(line.split("=", 1) for line in output.splitlines() if "=" in line)
    if (session.get("Active") != "yes" or session.get("Remote") != "no"
            or session.get("Type") != "tty" or session.get("Class") not in ("user", "user-early")
            or session.get("User") != str(uid) or session.get("VTNr") != tty[8:]
            or not session.get("Seat") or not session.get("Id")):
        raise ValueError("a local, active text login on this console is required")
    units = json.loads(command(
        "/usr/bin/systemctl", "--user", "list-units", "--all", "--no-pager", "--output=json",
        "graphical-session*.target", "wayland-session*.target", "wayland-wm@*.service"))
    if not isinstance(units, list) or any(unit["active"] not in ("inactive", "failed") for unit in units):
        raise ValueError("a graphical session is active or still stopping; use its console or wait for it to exit")
    # Refresh login identity rather than forwarding stale desktop/SSH values.
    return {"XDG_SESSION_ID": session["Id"], "XDG_SEAT": session["Seat"],
            "XDG_VTNR": session["VTNr"], "XDG_SESSION_TYPE": "tty"}


def main():
    if len(sys.argv) < 2:
        raise ValueError("installed desktop endpoint is missing")
    if sys.argv[2:] in (["--help"], ["-h"]):
        print("Usage: tam-desktop\nStart the installed Tamlinux desktop from your local text login.")
        return
    if sys.argv[2:]:
        raise ValueError("tam-desktop takes no arguments; use --help")
    endpoint = Path(sys.argv[1])
    tty = os.ttyname(0)
    if not all(os.isatty(fd) and os.ttyname(fd) == tty for fd in (1, 2)):
        raise ValueError("run tam-desktop directly in the text console, without redirection")
    identity = session_environment(tty, os.getuid(), os.tcgetpgrp(0) == os.getpgrp())
    if not endpoint.is_file() or not os.access(endpoint, os.X_OK):
        raise ValueError("install the Tamlinux desktop generation before starting graphics")
    env = dict(os.environ)
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "HYPRLAND_INSTANCE_SIGNATURE", "SWAYSOCK"):
        env.pop(key, None)
    env.update(identity)
    os.execve(endpoint, [str(endpoint)], env)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"tam-desktop: {error}", file=sys.stderr)
        sys.exit(1)
