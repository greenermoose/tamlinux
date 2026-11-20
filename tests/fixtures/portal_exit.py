"""Decide whether the proof must kill the Hyprland portal before it exits.

xdg-desktop-portal-hyprland before 1.5.0 can segfault during exit() and leave a
core dump, even when the proof passed. Upstream change 443 in 1.5.0 is expected
to fix it, so from that version the proof lets the portal exit normally. A crash
then shows as a core dump in `desktop/check-all --proofs`.

Retire this file and stop_hyprland_portal once the installed portal is 1.5.0 or
later and that run leaves no core dump.
"""
import re
import subprocess

PORTAL = '/usr/lib/xdg-desktop-portal-hyprland'
FIRST_CLEAN_VERSION = (1, 5, 0)


def installed_version_text(env=None):
    """Return what the portal says its version is, or '' if it cannot say."""
    try:
        return subprocess.run([PORTAL, '--version'], env=env, capture_output=True, text=True,
                              timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ''


def exits_cleanly(version_text):
    """Only a version known to have the fix counts; anything unclear keeps the kill."""
    match = re.search(r'\bv?(\d+)\.(\d+)\.(\d+)\b', version_text)
    return bool(match) and tuple(map(int, match.groups())) >= FIRST_CLEAN_VERSION
