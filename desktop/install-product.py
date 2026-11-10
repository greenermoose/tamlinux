#!/usr/bin/env python3
"""Install Tamlinux's own product files under one relocatable prefix.

Command Makefiles install commands; this installs the shell, plugins and
shared data previously assembled by the Nix recipes. It never writes user
configuration, system integration or third-party software.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[1]


def install(prefix: str, destdir: str, source: Path = SOURCE) -> None:
    prefix_path = Path(prefix)
    if not prefix_path.is_absolute() or any(p in (".", "..") for p in prefix.split("/")):
        raise ValueError("PREFIX must be absolute without . or .. components")
    root = Path(destdir) / prefix.lstrip("/") if destdir else prefix_path
    data = root / "share/tamlinux"
    data.mkdir(parents=True, exist_ok=True)

    def tree(src: str, dst: str) -> None:
        shutil.copytree(source / src, root / dst, dirs_exist_ok=True, symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def file(src: str, dst: str, mode: int = 0o644) -> None:
        target = root / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / src, target)
        target.chmod(mode)

    for name in ("shell", "session", "skills", "browser", "assets", "plugins"):
        tree(f"desktop/{name}", f"share/tamlinux/{name}")
    tree("share/nftables", "share/tamlinux/nftables")
    tree("desktop/user-defaults/bash", "share/tamlinux/user-defaults/bash")
    tree("desktop/user-defaults/gnupg", "share/tamlinux/user-defaults/gnupg")
    file("desktop/user-defaults/apply", "share/tamlinux/user-defaults/apply")
    file("desktop/user-defaults/LICENSE-bash", "share/tamlinux/user-defaults/LICENSE-bash")
    file("desktop/README.md", "share/tamlinux/README.md")
    file("desktop/menu/default.jsonc", "share/tamlinux/menu/default.jsonc")
    for src, name in (("desktop/session/start", "tam-hyprland-session"),
                      ("desktop/session/desktop", "tam-desktop"),
                      ("desktop/menu/tam-menu", "tam-menu"),
                      ("desktop/protocol-shadow", "tam-protocol-shadow")):
        file(src, f"bin/{name}", 0o755)
    (data / "session/Hyprland").chmod(0o755)
    for name, src in (("version", "VERSION"), ("cultivar", "CULTIVAR"),
                      ("assets/version", "VERSION")):
        file(src, f"share/tamlinux/{name}")

    # Only the product icon font is bundled. Distribution fonts are native
    # dependencies, rather than copied out of a second package manager.
    font = root / "share/fonts/truetype/TamlinuxIcons.ttf"
    font.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(source / "desktop/theme/rename-font.py"),
                    str(source / "desktop/assets/fonts/source.ttf"), str(font)], check=True)
    (data / "assets/fonts/source.ttf").unlink()
    file("desktop/assets/LICENSE-omarchy", "share/tamlinux/assets/fonts/LICENSE")
    for path in (data / "assets/themes").rglob("vscode.json"):
        path.unlink()
    file("desktop/assets/icons/tamlinux-discord.png", "share/icons/hicolor/256x256/apps/tamlinux-discord.png")

    # Native helper paths replace Nix wrappers. Each command already reads
    # these descriptors from its own installation prefix.
    tools = {name: f"/usr/bin/{name}" for name in
             ("grim", "slurp", "hyprpicker", "gpu-screen-recorder", "wl-copy",
              "tesseract", "zbarimg", "v4l2-ctl", "mpv", "ffmpeg", "ffprobe")}
    tools["englishData"] = "/usr/share/tessdata/eng.traineddata"
    for name, value in (("capture-tools", tools),
                        ("provider-tools", {"tensaku": "/usr/bin/tensaku",
                                            "asdcontrol": "/usr/lib/tamlinux/asdcontrol"})):
        (data / f"{name}.json").write_text(json.dumps(value, sort_keys=True) + "\n")

    console = data / "console"
    console.mkdir(exist_ok=True)
    for name, args in (("welcome-generic.issue", []),
                       ("welcome.issue", ["--version", (source / "VERSION").read_text().strip(),
                                          "--cultivar", (source / "CULTIVAR").read_text().strip()])):
        result = subprocess.run([sys.executable, str(source / "desktop/session/console-welcome.py"), *args],
                                check=True, stdout=subprocess.PIPE)
        (console / name).write_bytes(result.stdout)

    # The native adapter exposes this directory to the user manager. Units
    # are installed here without enabling or restarting anything during build.
    units = root / "share/systemd/user"
    units.mkdir(parents=True, exist_ok=True)
    for template in sorted((source / "desktop/systemd/user").glob("*")):
        if template.is_file():
            (units / template.name).write_text(template.read_text().replace("@PREFIX@", prefix))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--destdir", default="")
    args = parser.parse_args()
    try:
        install(args.prefix, args.destdir)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"install-product: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
