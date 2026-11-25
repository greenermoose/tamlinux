#!/usr/bin/env python3
"""Arrange a staged cultivar DESTDIR into the unified /usr/lib/tamlinux layout."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys

SOURCE = Path(__file__).resolve().parents[2]
CURRENT = "/usr/lib/tamlinux/current"
BIN_LINK = "/usr/bin/tamlinux"
BROWSER_POLICY_EXEC = "/usr/lib/tamlinux/browser-policy-exec"

# Expressions used by relocatable command scripts; compile to the active cultivar path.
DATA_PATHS = (
    '$(dirname "$(readlink -f "$0")")/../share/tamlinux',
    '$(dirname "$(readlink -f -- "$0")")/../share/tamlinux',
    '$(dirname "$(dirname "$(readlink -f "$0")")")/share/tamlinux',
    '$bin_dir/../share/tamlinux',
    '$base/../share/tamlinux',
    '$prefix/share/tamlinux',
    '$root/share/tamlinux',
)

PROFILE_SCRIPT = """# Tamlinux cultivar commands and shared data (preserves ~/.local/bin precedence).
# Including /usr/lib/tamlinux/current/bin in PATH lets man-db discover
# /usr/lib/tamlinux/current/share/man automatically after /etc/profile unsets MANPATH.
if [ -d /usr/bin/tamlinux ]; then
  case ":${PATH:-}:" in
    *:/usr/bin/tamlinux:*) ;;
    *) PATH="${PATH:+$PATH:}/usr/bin/tamlinux" ;;
  esac
  export PATH
fi
if [ -d /usr/lib/tamlinux/current/bin ]; then
  case ":${PATH:-}:" in
    *:/usr/lib/tamlinux/current/bin:*) ;;
    *) PATH="${PATH:+$PATH:}/usr/lib/tamlinux/current/bin" ;;
  esac
  export PATH
fi
if [ -d /usr/lib/tamlinux/current/share ]; then
  case ":${XDG_DATA_DIRS:-/usr/local/share:/usr/share}:" in
    *:/usr/lib/tamlinux/current/share:*) ;;
    *) XDG_DATA_DIRS="${XDG_DATA_DIRS:-/usr/local/share:/usr/share}:/usr/lib/tamlinux/current/share" ;;
  esac
  export XDG_DATA_DIRS
fi
"""

ENVIRONMENT_D_CONF = """# Expose Tamlinux cultivar commands and shared data to systemd user sessions.
PATH=${PATH}:/usr/bin/tamlinux:/usr/lib/tamlinux/current/bin
XDG_DATA_DIRS=${XDG_DATA_DIRS:-/usr/local/share:/usr/share}:/usr/lib/tamlinux/current/share
"""


def staging_root(prefix: str, destdir: str) -> Path:
    stage = Path(destdir)
    if prefix != CURRENT or not destdir or not stage.is_absolute() or stage.resolve() == Path("/"):
        raise ValueError(f"install-cultivar-layout requires PREFIX={CURRENT} and an absolute staging DESTDIR")
    stage = stage.resolve()
    if stage.is_relative_to(Path("/usr")) or stage.is_relative_to(Path("/etc")):
        raise ValueError("DESTDIR must be a staging directory outside the system installation")
    return stage


def put(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    path.chmod(mode)


def move_tree(source: Path, dest: Path) -> None:
    if not source.is_dir() or source.is_symlink() or dest.exists() or dest.is_symlink():
        raise ValueError(f"Expected a real staged directory and a new destination for {source.name}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    source.rename(dest)


def render_commands(directory: Path, current: str = CURRENT) -> None:
    share = f"{current}/share/tamlinux"
    for command in sorted(directory.iterdir()):
        info = command.lstat()
        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o111:
            raise ValueError(f"Expected a real executable in cultivar bin: {command.name}")
        data = command.read_bytes()
        if not data.startswith(b"#!"):
            continue
        content = data.decode("utf-8")
        for old in DATA_PATHS:
            content = content.replace(old, share)
        content = content.replace(
            'self_dir.parent / "share/tamlinux/desktop/test-battery"',
            f'Path("{share}/desktop/test-battery")',
        )
        if command.name in (
            "tam-desktop", "tam-shell", "tam-hyprland-session", "tam-pane-session", "tam-session-init",
        ):
            first, _, rest = content.partition("\n")
            content = first + (
                '\nif [ -e /var/lib/tamlinux/pending.json ]; then\n'
                '  echo "Tamlinux installation is incomplete. Recover from the console." >&2\n'
                '  exit 1\n'
                'fi\n'
            ) + rest
        if command.name in ("tam-hyprland-session", "tam-pane-session"):
            wait = '/usr/bin/python3 -I "$session_dir/wait-stopped.py" || exit $?'
            config_file = "hyprland.lua" if command.name == "tam-hyprland-session" else "tam-pane.lua"
            config = f'config="${{XDG_CONFIG_HOME:-$HOME/.config}}/tamlinux/session/{config_file}"'
            if content.count(wait) != 1 or content.count(config) != 1:
                raise ValueError("Expected the installed session launch sequence")
            content = content.replace(wait + "\n", "").replace(
                config, wait + '\n/usr/bin/python3 -I -B "$session_dir/session_settings.py" || exit $?\n'
                + config)
            for helper in ("tam-theme-init", "tam-session-init"):
                content = content.replace('"${TAMLINUX_BIN:-$commands}/' + helper + '"',
                                          f'"{BIN_LINK}/{helper}"')
            content = content.replace('commands="$bin_dir"\n'
                                      '[ -x "$commands/tam-theme-init" ] || commands="$HOME/.local/bin"\n', "")
        if "../share/tamlinux" in content:
            raise ValueError(f"Unmapped relative product data path in {command.name}")
        if content.encode() != data:
            command.write_text(content)


def wanted_targets(unit: Path) -> list[str]:
    """Return targets listed under [Install] WantedBy= in a systemd user unit."""
    targets: list[str] = []
    in_install = False
    for raw in unit.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_install = line == "[Install]"
            continue
        if in_install and line.startswith("WantedBy"):
            key, sep, value = line.partition("=")
            if sep and key.strip() == "WantedBy":
                if not value.strip():
                    targets.clear()
                else:
                    targets.extend(value.split())
    return targets


def copy_vendor_defaults(stage: Path, source: Path,
                         wants_by_target: dict[str, set[str]]) -> None:
    base = source / "src/desktop/native/defaults"
    root = base / "root"
    entries = json.loads((base / "origins.json").read_text())["files"]
    for name, record in sorted(entries.items()):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or not name.startswith(("usr/lib/", "usr/share/")):
            raise ValueError(f"Unsafe vendor default path {name}")
        original = root / relative
        if "link" in record:
            target = original.resolve(strict=True)
            if str(original.readlink()) != record["link"] or not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Vendor link differs from its origin record: {name}")
            if name.startswith("usr/lib/systemd/user/") and relative.parent.name.endswith(".wants"):
                unit_target = relative.parent.name[: -len(".wants")]
                wants_by_target.setdefault(unit_target, set()).add(relative.name)
                continue
            if name != "usr/share/fontconfig/conf.default/50-tamlinux.conf":
                raise ValueError(f"Vendor link needs a placement rule: {name}")
            put(stage / relative, target.read_bytes())
            continue
        info = original.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"Vendor default must be a regular file: {name}")
        data = original.read_bytes()
        mode = stat.S_IMODE(info.st_mode)
        if hashlib.sha256(data).hexdigest() != record["sha256"] or f"{mode:04o}" != record["mode"]:
            raise ValueError(f"Vendor default differs from its origin record: {name}")
        put(stage / relative, data, mode)


def install(stage: Path, source: Path = SOURCE, current: str = CURRENT) -> None:
    share = f"{current}/share/tamlinux"
    private = stage / current.lstrip("/")
    if not private.is_dir() or private.is_symlink():
        raise ValueError(f"Expected a staged cultivar directory at {private}")

    usr = stage / "usr"
    # Move rootstock-required drop-ins out of the cultivar tree into integration locations.
    units = usr / "lib/systemd/user"
    move_tree(private / "share/systemd/user", units)
    sys_units = usr / "lib/systemd/system"
    sys_wants_by_target: dict[str, set[str]] = {}
    if (private / "share/systemd/system").is_dir():
        move_tree(private / "share/systemd/system", sys_units)
        for unit in sorted(sys_units.iterdir()):
            if unit.is_file():
                for unit_target in wanted_targets(unit):
                    sys_wants_by_target.setdefault(unit_target, set()).add(unit.name)
    (private / "share/systemd").rmdir()
    wants_by_target: dict[str, set[str]] = {}
    for unit in sorted(units.iterdir()):
        for unit_target in wanted_targets(unit):
            wants_by_target.setdefault(unit_target, set()).add(unit.name)

    font_src = private / "share/fonts/truetype/TamlinuxIcons.ttf"
    if font_src.is_file():
        put(usr / "share/fonts/tamlinux/TamlinuxIcons.ttf", font_src.read_bytes(), 0o644)
        font_src.unlink()
        try:
            font_src.parent.rmdir()
            font_src.parent.parent.rmdir()
        except OSError:
            pass

    commands = private / "bin"
    if (commands / "tam-nut").exists():
        (commands / "tam-nut").unlink()
    if (commands / "hi").exists():
        (commands / "hi").unlink()
    put(commands / "hi", b'#!/bin/sh\nexec /usr/bin/tam hi "$@"\n', 0o755)
    if (commands / "start").exists() and not (commands / "tam-start").exists():
        put(commands / "tam-start", f'#!/bin/sh\nexec {current}/bin/start "$@"\n'.encode(), 0o755)
    render_commands(commands, current)

    session = private / "share/tamlinux/session"
    origin = source / "src/desktop/source-install/session_settings.py"
    put(session / origin.name, origin.read_bytes())
    pane_desktop = (source / "src/desktop/session/tam-pane.desktop").read_bytes().replace(
        b"/usr/lib/tamlinux/current", current.encode(),
    )
    put(usr / "share/wayland-sessions/tam-pane.desktop", pane_desktop, 0o644)

    copy_vendor_defaults(stage, source, wants_by_target)
    for unit_target, unit_names in sorted(wants_by_target.items()):
        dropin = units / f"{unit_target}.d/50-tamlinux-services.conf"
        put(dropin, ("[Unit]\nWants=" + " ".join(sorted(unit_names)) + "\n").encode())
    for unit_target, unit_names in sorted(sys_wants_by_target.items()):
        dropin = sys_units / f"{unit_target}.d/50-tamlinux-services.conf"
        put(dropin, ("[Unit]\nWants=" + " ".join(sorted(unit_names)) + "\n").encode())

    # PATH / XDG_DATA_DIRS / MANPATH integration drop-ins.
    put(stage / "etc/profile.d/tamlinux.sh", PROFILE_SCRIPT.encode(), 0o644)
    put(usr / "lib/environment.d/10-tamlinux-path.conf", ENVIRONMENT_D_CONF.encode(), 0o644)

    native = source / "src/desktop/native"
    integration = native / "integration"
    browser = (native / "theme-browser-policy").read_bytes().replace(
        b"/usr/lib/tamlinux/browser_policy.py", f"{current}/lib/browser_policy.py".encode(),
    )
    put(stage / BROWSER_POLICY_EXEC.lstrip("/"), browser, 0o755)
    put(commands / "tam-theme-set-browser-policy",
        f'#!/bin/sh\nexec {BROWSER_POLICY_EXEC} "$@"\n'.encode(), 0o755)
    put(private / "lib/browser_policy.py", (native / "browser_policy.py").read_bytes())

    guard = source / "src/commands/tam-hyprland-reload-guard/tam-hyprland-reload-guard"
    put(private / "lib/hyprland-reload-guard", guard.read_bytes(), 0o755)
    put(usr / "lib/tmpfiles.d/tamlinux.conf", (integration / "tamlinux.conf").read_bytes())
    policy = (integration / "org.tamlinux.native.policy").read_bytes().replace(
        b"/usr/bin/tam-theme-set-browser-policy", BROWSER_POLICY_EXEC.encode(),
    ).replace(
        b"/usr/lib/tamlinux/asdcontrol", b"/usr/bin/asdcontrol",
    )
    put(usr / "share/polkit-1/actions/org.tamlinux.native.policy", policy)
    for hook in sorted(integration.glob("*.hook")):
        data = hook.read_bytes().replace(
            b"/usr/lib/tamlinux/hyprland-reload-guard", f"{current}/lib/hyprland-reload-guard".encode(),
        )
        put(usr / "share/libalpm/hooks" / hook.name, data)

    console = private / "share/tamlinux/console/welcome.issue"
    put(usr / "lib/issue.d/70-tamlinux.issue", console.read_bytes())

    providers = private / "share/tamlinux/provider-tools.json"
    values = json.loads(providers.read_text())
    values["asdcontrol"] = "/usr/bin/asdcontrol"
    providers.write_text(json.dumps(values, sort_keys=True) + "\n")

    # Shipped common user defaults.
    bash = private / "defaults/home/.config/bash/tamlinux"
    shutil.copytree(source / "src/desktop/user-defaults/bash", bash)
    (bash / "env").write_text("# Tamlinux commands use /etc/profile.d/tamlinux.sh.\n")
    home = private / "defaults/home"
    put(home / ".config/tamlinux/session/hyprland.lua",
        f'dofile("{share}/session/entry.lua")\n'.encode())
    put(home / ".config/tamlinux/session/tam-pane.lua", (
        f'local code, err = tp.read_file("{share}/session/tam-pane.lua")\n'
        f'assert(code, err)\n'
        f'assert(load(code, "@{share}/session/tam-pane.lua", "t"))()\n'
    ).encode())
    put(home / ".config/uwsm/env.d/10-tamlinux.sh", (
        f'. {share}/session/uwsm-env\n'
        'export TAMLINUX_QUICKSHELL=/usr/bin/quickshell\n'
        'export TAMLINUX_QUICKSHELL_IPC=/usr/bin/qs\n'
        f'export TAMLINUX_VERSION_NOTES={share}/version-notes.txt\n'
        'export TAMLINUX_STAY_AWAKE_FILE="${XDG_STATE_HOME:-$HOME/.local/state}/tamlinux/stay-awake"\n'
    ).encode())
    put(home / ".config/autostart/org.fcitx.Fcitx5.desktop",
        b"[Desktop Entry]\nType=Application\nName=Fcitx 5\nHidden=true\n")
    put(home / ".config/xdg-desktop-portal/hyprland-portals.conf",
        b"[preferred]\ndefault=hyprland;gtk\norg.freedesktop.impl.portal.FileChooser=gtk\n")
    put(home / ".config/tamlinux/menu/default.jsonc",
        (source / "src/desktop/menu/default.jsonc").read_bytes())
    shutil.copytree(source / "src/desktop/browser/extensions", home / ".config/tamlinux/chromium/extensions")
    browsers = ("chromium", "google-chrome", "google-chrome-beta", "google-chrome-unstable",
                "BraveSoftware/Brave-Browser", "BraveSoftware/Brave-Browser-Beta",
                "BraveSoftware/Brave-Browser-Nightly", "microsoft-edge", "microsoft-edge-dev")
    for browser_name in browsers:
        for name, command, origin_id in (
            ("copy_url", "tam-chromium-copy-url-host", "bgpiichlckmfanooecilcjemknkcpngb"),
            ("ytdlp", "tam-chromium-ytdlp-host", "dedjgknigfeelejglamclffonmophnfl"),
        ):
            host = {"name": "org.tamlinux." + name, "description": "Tamlinux Chromium native messaging endpoint",
                    "path": f"{BIN_LINK}/{command}", "type": "stdio",
                    "allowed_origins": ["chrome-extension://" + origin_id + "/"]}
            put(home / f".config/{browser_name}/NativeMessagingHosts/org.tamlinux.{name}.json",
                (json.dumps(host, sort_keys=True) + "\n").encode())
    extensions = f"{share}/browser/extensions"
    put(home / ".config/chromium-flags.conf", (
        "--ozone-platform=wayland\n--password-store=gnome-libsecret\n"
        "--enable-features=TouchpadOverscrollHistoryNavigation\n"
        f"--load-extension={extensions}/copy-url,{extensions}/yt-dlp,{extensions}/whatsapp-slim\n"
    ).encode())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", default=CURRENT)
    parser.add_argument("--destdir", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        stage = staging_root(args.prefix, args.destdir)
        if not args.check:
            install(stage, current=args.prefix)
    except (OSError, ValueError) as error:
        print(f"install-cultivar-layout: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
