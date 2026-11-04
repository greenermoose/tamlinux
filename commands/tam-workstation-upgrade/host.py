"""Local workstation identity for upgrade planning. Never mutates the host."""
from __future__ import annotations

import getpass
import json
import os
import re
import socket
import subprocess
from pathlib import Path

REVISION = re.compile(r"[0-9a-f]{40}\Z")


class HostError(Exception):
    pass


def find_config_repo(home: Path | None = None) -> Path:
    if os.environ.get("TAMLINUX_CONFIG_REPO"):
        return Path(os.environ["TAMLINUX_CONFIG_REPO"])
    home = home or Path.home()
    root = home / "Code/tamlinux"
    matches = []
    for lock in sorted(root.glob("*/flake.lock")) if root.is_dir() else []:
        try:
            inputs = json.loads(lock.read_text())["nodes"]["root"].get("inputs", {})
        except (OSError, ValueError, KeyError):
            continue
        if "tamlinux-packages" in inputs:
            matches.append(lock.parent)
    if len(matches) != 1:
        raise HostError("set TAMLINUX_CONFIG_REPO to the Home Manager configuration checkout")
    return matches[0]


def native_package(name: str = "tamlinux-native") -> dict | None:
    result = subprocess.run(
        ["pacman", "-Qi", name], text=True, capture_output=True, timeout=15
    )
    if result.returncode != 0:
        return None
    fields = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    version = fields.get("Version")
    if not version:
        return None
    return {"name": name, "version": version, "installDate": fields.get("Install Date")}


def local_profile(config: Path | None = None) -> dict:
    config = config or find_config_repo()
    hostname = socket.gethostname()
    username = getpass.getuser()
    architecture = os.uname().machine + "-linux"
    hosts = config / "hosts"
    if not hosts.is_dir():
        raise HostError("configuration has no hosts/ registry")
    host_path = hosts / hostname / "host.json"
    if not host_path.is_file():
        raise HostError(f"local hostname has no registered host profile: {hostname}")
    host = json.loads(host_path.read_text())
    if host.get("hostname") != hostname or host.get("username") != username:
        raise HostError("registered host identity does not match this account")
    if host.get("system") and host["system"] != architecture:
        raise HostError(
            f"registered system {host['system']} does not match this machine {architecture}"
        )
    pin_path = hosts / hostname / "state/assembly"
    assembly = pin_path.read_text().strip() if pin_path.is_file() else None
    if assembly is not None and not REVISION.fullmatch(assembly):
        raise HostError("host assembly pin is not a full revision")
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    deploy = {}
    deploy_path = state_home / "tamlinux/deploy.json"
    if deploy_path.is_file():
        try:
            deploy = json.loads(deploy_path.read_text())
        except (OSError, ValueError):
            raise HostError("deployment receipt is unreadable") from None
    generation = None
    profile = state_home / "nix/profiles/home-manager"
    if profile.exists() or profile.is_symlink():
        generation = str(profile.resolve())
    return {
        "hostname": hostname,
        "username": username,
        "architecture": architecture,
        "config": str(config),
        "profile": f"{username}@{hostname}",
        "capabilities": list(host.get("capabilities") or []),
        "assembly": assembly or deploy.get("packages"),
        "generation": generation or deploy.get("generation"),
        "deployStage": deploy.get("stage"),
        "native": native_package(),
    }
