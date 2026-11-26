"""Shared headless Wayland compositor helper for offscreen Tamlinux tests.

Prefers headless tam-pane (zero Sway dependency, works inside sandboxes) and
falls back to headless Sway only if tam-pane is unavailable.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class HeadlessCompositorInfo:
    backend: str
    wayland_display: str
    tam_pane_socket: str
    log_path: Path


def find_tam_pane(repo_root: Path = REPO_ROOT) -> str | None:
    candidates = [
        os.environ.get("TAM_PANE_BIN", ""),
        str(repo_root.parent / "tam-pane/build/tam-pane"),
        str(Path.home() / ".local/bin/tam-pane"),
        "/usr/bin/tamlinux/tam-pane",
        shutil.which("tam-pane") or "",
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def compositor_available(repo_root: Path = REPO_ROOT) -> bool:
    return bool(find_tam_pane(repo_root) or shutil.which("sway"))


@contextmanager
def start_headless_compositor(
    runtime_dir: Path,
    work_dir: Path,
    outputs: list[dict[str, object]] | None = None,
    base_env: dict[str, str] | None = None,
    repo_root: Path = REPO_ROOT,
) -> Iterator[HeadlessCompositorInfo]:
    """Start headless tam-pane (or sway fallback) with the requested outputs."""
    out_specs = outputs or [{"name": "HEADLESS-1", "mode": "1280x720@60", "position": (0, 0), "scale": 1.0}]
    env = dict(base_env or {})
    env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
    env.pop("WAYLAND_DISPLAY", None)
    env.pop("TAM_PANE_SOCKET", None)
    env["XDG_RUNTIME_DIR"] = str(runtime_dir)
    env["WLR_BACKENDS"] = "headless"
    env["WLR_HEADLESS_OUTPUTS"] = str(len(out_specs))
    env["WLR_LIBINPUT_NO_DEVICES"] = "1"
    env["WLR_RENDERER"] = "pixman"

    tam_pane = find_tam_pane(repo_root)
    if tam_pane:
        lua_lines = []
        for spec in out_specs:
            name = spec["name"]
            mode = spec.get("mode", "1280x720@60")
            pos = spec.get("position", (0, 0))
            scale = spec.get("scale", 1.0)
            lua_lines.append(
                f'tp.monitor{{ output = "{name}", mode = "{mode}", '
                f'position = {{ {int(pos[0])}, {int(pos[1])} }}, scale = {scale} }}'
            )
        config = work_dir / "tam-pane-headless.lua"
        config.write_text("\n".join(lua_lines) + "\n", encoding="utf-8")
        log_path = work_dir / "tam-pane.log"
        cmd = [tam_pane, "-c", str(config)]
        backend = "tam-pane"
    else:
        sway = shutil.which("sway")
        if not sway:
            raise RuntimeError("neither tam-pane nor sway is available")
        sway_lines = []
        for spec in out_specs:
            name = spec["name"]
            mode = str(spec.get("mode", "1280x720")).split("@", 1)[0]
            pos = spec.get("position", (0, 0))
            scale = spec.get("scale", 1.0)
            sway_lines.append(
                f"output {name} resolution {mode} scale {scale} position {int(pos[0])} {int(pos[1])}"
            )
        config = work_dir / "sway.conf"
        config.write_text("\n".join(sway_lines) + "\n", encoding="utf-8")
        log_path = work_dir / "sway.log"
        cmd = [sway, "-c", str(config)]
        backend = "sway"

    with log_path.open("w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 8.0
            wl_sock: Path | None = None
            ipc_sock: Path | None = None
            while time.monotonic() < deadline and proc.poll() is None:
                if wl_sock is None:
                    wl_sock = next(
                        (p for p in runtime_dir.glob("wayland-*") if not p.name.endswith(".lock")),
                        None,
                    )
                if backend == "tam-pane" and ipc_sock is None:
                    sock_dir = runtime_dir / "tam-pane"
                    if sock_dir.is_dir():
                        socks = sorted(sock_dir.glob("wayland-*.sock"))
                        if socks:
                            ipc_sock = socks[0]
                if wl_sock is not None and (backend != "tam-pane" or ipc_sock is not None):
                    break
                time.sleep(0.05)
            if wl_sock is None:
                raise AssertionError(
                    f"headless {backend} did not create Wayland socket:\n"
                    + log_path.read_text(encoding="utf-8", errors="replace")
                )
            yield HeadlessCompositorInfo(
                backend=backend,
                wayland_display=wl_sock.name,
                tam_pane_socket=str(ipc_sock) if ipc_sock else "",
                log_path=log_path,
            )
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
