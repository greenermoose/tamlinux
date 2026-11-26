"""Wait briefly for a previous uwsm session to finish; never stop it ourselves."""
import json
import os
import subprocess
import sys
import time


COMPOSITORS = ("Hyprland", "tam-pane")


def busy():
    result = subprocess.run([
        "/usr/bin/systemctl", "--user", "list-units", "--all", "--no-pager", "--output=json",
        "graphical-session*.target", "wayland-session*.target", "wayland-wm@*.service",
    ], capture_output=True, text=True, check=True, timeout=2)
    units = json.loads(result.stdout)
    if not isinstance(units, list):
        raise ValueError("invalid user-manager unit list")
    if any(unit["active"] not in ("inactive", "failed") for unit in units):
        return True
    uid = str(os.getuid())
    for name in COMPOSITORS:
        compositor = subprocess.run(["/usr/bin/pgrep", "-u", uid, "-x", name],
                                    capture_output=True, timeout=2)
        if compositor.returncode == 0:
            return True
        if compositor.returncode != 1:
            raise RuntimeError(f"cannot inspect previous compositor {name}")
    return False


def wait(probe=busy, clock=time.monotonic, sleep=time.sleep, timeout=30):
    deadline = clock() + timeout
    announced = False
    while probe():
        if not announced:
            print("Tamlinux: waiting for the previous graphical session to stop (30 s maximum)",
                  file=sys.stderr, flush=True)
            announced = True
        if clock() >= deadline:
            raise TimeoutError("previous graphical session is still stopping; use the recovery text console")
        sleep(min(0.5, max(0, deadline - clock())))


if __name__ == "__main__":
    try:
        wait()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Tamlinux: cannot start a new graphical session: {error}", file=sys.stderr)
        sys.exit(1)
