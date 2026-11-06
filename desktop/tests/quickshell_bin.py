"""Resolve the Quickshell binary for offscreen desktop tests.

Prefer the session-selected Nix Quickshell (`TAMLINUX_QUICKSHELL`), then the
user Nix profile, then PATH. The native Pacman package is gone (Plan 32), so
tests must not require `/usr/bin/quickshell`.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def quickshell_bin() -> str:
    env = os.environ.get("TAMLINUX_QUICKSHELL")
    if env and Path(env).is_file():
        return env
    nix_profile = Path.home() / ".nix-profile/bin/quickshell"
    if nix_profile.is_file():
        return str(nix_profile)
    found = shutil.which("quickshell")
    if found:
        return found
    raise FileNotFoundError(
        "quickshell not found; set TAMLINUX_QUICKSHELL or install the Nix package"
    )
