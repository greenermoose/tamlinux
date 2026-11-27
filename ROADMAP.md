# Tamlinux roadmap

Tamlinux is developed in public on branch `dev`; `test`, `main`, tags, and
releases move only on Fred's word (`VERSIONING.md`). Cultivar names identify
minor versions of the workstation environment.

## 0.4.8: Gate A — standalone Tamlinux (released 2026-10-22)

Removed all Omarchy packages and paths. Tamlinux stands alone on Arch Linux
with Hyprland and Quickshell.

## 0.5.12: Blue Sparkler — input and appearance (released 2026-11-01)

Input usability, console-first startup, start menu, monitor control, and
Tokyo Night / JetBrains Mono defaults.

## 0.6.x: KBN WB — dependable baseline

Fix GPU-resume and hibernation faults or accept mitigations, pin carried
patches with upstream status, establish routine updates and rollback, move
from `tam-bundle` to locked source installs (`make` / `make install`), and
prove host-safe installs across the fleet (`plans/P21-source-install.md`).

## 0.7.x: Northern Torch — tam-pane everywhere and complete Hyprland removal (current)

Move the workstation and fleet laptops onto `tam-pane` (alongside `tam-last`,
`tam-clam`, `tam-edit`, `tam-view`, and `tam-hide`), replace every Hyprland
helper and ecosystem tool, delete all Hyprland code and configuration from
`tamlinux`, and remove the Hyprland package tree and every superseded
dependency. Northern Torch is done when we count on `tam-pane` as our only
compositor and Hyprland is completely gone.

### Phase 1 — Bosgame desktop bring-up and default switch (0.7.0–0.7.1)

Fred can log in at a text console, select the graphical desktop in `start`,
and work all day across bosgame's three monitors with `tam-pane` as the
compositor while keeping an independent recovery path during initial trials.
These steps lead from the nested `tam-pane` 0.2.x trials through the
[0.3.x session and shell work](https://github.com/greenermoose/tam-pane/blob/dev/plans/P4-dogfood-tamlinux-0.7.md).

1. **Account for every app.** Build a checklist from the installed manifest,
   component pins, console activities, desktop entries, Start menu, Quick
   Launch, bindings, shell services and plugin manifests. Include bosgame's
   personal launchers and overrides. Give each entry its normal launch path,
   one real task, its compositor dependencies and a result. Identify the
   recovery commands so every everyday action has a `tam-pane` path.
2. **Deliver a reproducible session.** Pin `tam-pane`, `tam-hide`, `tam-last`,
   `tam-clam`, `tam-edit`, `tam-view`, and compatible `libtam` in the
   [source delivery](plans/P21-source-install.md). Stage the Make install,
   Arch dependencies, Wayland session entry and versioned defaults. Honor
   local development builds on PATH (via `make install` or
   `tam-dev try tam-pane`) while falling back to the packaged cultivar binary
   and verifying the packaged binary by its absolute cultivar path. Build with
   native Wayland (`XWAYLAND=0`, zero-`xcb`).
3. **Provide guarded console launches.** Add `tam-desktop tam-pane` (alias
   `pane`) and `tam-desktop hyprland` while keeping the graphical activity in
   `start` routed through bare `tam-desktop`. Extend local VT,
   duplicate-session and shutdown checks to `tam-pane`. On normal exit,
   startup failure and crash, release the console only when graphics has
   stopped.
4. **Bring up the complete session.** Use a UWSM session target. Publish the
   desktop identity, Wayland display and `tam-pane` socket to systemd and
   D-Bus before starting Quickshell, portals (`xdg-desktop-portal-wlr` via
   authorized capture) and helpers. Verify one shell and polkit agent, file
   chooser and PipeWire screen sharing.
5. **Connect the shell to tam-pane.** Extend the compositor facade with
   `TamPaneAdapter`. Use `ProtocolState` for standard Wayland facts and
   `tam-pane` Unix-socket IPC for missing state and actions. Represent
   multiple visible tags per output and windows on several tags. Verify focus,
   tag changes, output power, pointer location, bindings and keyboard layout,
   including initial state, event updates and automatic reconnection across
   outputs ([shared protocol plan](plans/P6-compositor-protocol-layer.md)).
6. **Port bosgame's controls and desktop ergonomics.** Translate effective
   monitor geometry and scale, input settings, focus-follows-mouse, three-pixel
   bright green focus border, window rules, shortcuts, mouse bindings
   (`Meta + right-drag` window move with background Start-menu fallback),
   autostart and macros into `tam-pane.lua`. Preserve personal overrides across
   reloads. Exercise launch-or-focus, terminal working directory, window
   placement, monitor controls, brightness, night light, screenshots, recording,
   one-handed chords, layout switching and guarded macro paste.
7. **Prove the shell, plugins and C17 apps.** Exercise the bar, menus, panels,
   popup focus, notifications, OSD, clipboard, authorization and theme changes.
   Check all nine shipped `fred.*` plugins with per-display tags on `tam-pane`.
   With Hyprland stopped, run `tam-clam` in `tam-last`, save edits in
   `tam-edit`, review docs in `tam-view`, and verify GTK, Qt, browsers and
   webapps.
8. **Automate repeatable checks and benchmarks.** Run the
   [desktop test battery](plans/P10-desktop-test-battery.md) and offscreen
   panel/menu suites on headless `tam-pane` in place of Sway. Compare startup
   latency, memory (PSS/RSS/VRAM), and idle power between compositors with
   `tam-session-bench`.
9. **Prove hardware, locking and recovery on bosgame.** On Fred's Test word
   for the exact candidate, record the previous source stage and Snapper
   snapshot before login changes. From a physical VT, prove switching away and
   back, emergency exit, three-monitor window dragging and movement,
   floating-window centering, unplug/replug, blank/wake, restored tag layouts,
   authenticated multi-output lock/unlock with `tam-hide`, idle inhibition,
   suspend, hibernate/resume and GPU renderer-loss recovery.
10. **Accept daily use and make tam-pane the default.** Fred works a full day
    on `tam-pane` without falling back. On Fred's Run word for the accepted
    candidate, switch bare `tam-desktop` and the graphical activity in `start`
    to launch `tam-pane` by default.

### Phase 2 — Replace Hyprland ecosystem helpers and port fleet controls (0.7.2–0.7.x)

11. **Move all locking, idle and sleep/wake paths to `tam-hide` and `tam-pane`.**
    Update `tam-system-lock`, `tam-system-sleep-lock` (logind `PrepareForSleep`
    delay-inhibitor verification), `tam-system-lid-close`, `tam-system-wake`,
    `tam-suspend-unless-stay-awake` and the shell's idle service to lock, query
    lock state and manage DPMS exclusively through `tam-pane` and `tam-hide`
    (`ext-session-lock-v1` + PAM). Delete `src/desktop/lock/hyprlock.conf` and
    retire `hyprlock` and `hypridle`.
12. **Replace `hyprsunset` and `hyprpicker` with native `tam-pane` gamma and capture.**
    Drive screen colour temperature (`tam-toggle-nightlight` and the shell
    nightlight service) through `tam-pane`'s gamma control without
    `hyprsunset`, and retire `tam-restart-hyprsunset`. Replace `hyprpicker`
    screen freeze and colour picking in `tam-capture-region`,
    `tam-capture-screenshot` and the `Meta + Print` colour picker with native
    Wayland screencopy / pixel sampling on `tam-pane`.
13. **Port laptop display, clamshell, input and window commands off `hyprctl`.**
    Port internal/external display detection, clamshell mode, panel toggle,
    display mirroring, scaling, modeless EDID recovery, touchpad/touchscreen
    toggling (`tam-toggle-input-device`), logout window close
    (`tam-system-logout`), layout/gap toggles and region-capture cursor warp
    (`tam-capture-region --select-window`) to `tam-pane` IPC and
    `~/.config/tamlinux/tam-pane/` state. Prove `tam-pane` on the fleet
    laptops (`slowhp` and `toughbook`).
14. **Decouple themes, menus and Tensaku from Hyprland.**
    Update `tam-theme-set-templates` and `desktop/theme/engine.py` to style
    `tam-pane` directly and drop `hyprland.lua.tpl`, `hypr_gradient` and
    `tam-restart-hyprctl`. Update `src/desktop/menu/default.jsonc` so Style,
    Setup, Learn and Update entries target `tam-pane` configuration and live
    services rather than `tamlinux/hypr/*.lua` or `hyprsunset`. Update
    vendored Tensaku (`src/hypr.rs`, `src/hypr_bind.rs`) to use `tam-pane` IPC
    and `tam-pane` binding drop-ins.

### Phase 3 — Purge Hyprland code and remove dependencies (0.7.x completion)

15. **Delete all Hyprland code, adapters, configs, commands and hooks from `tamlinux`.**
    Remove `tam-hyprland-session`, `src/desktop/session/Hyprland`,
    `src/desktop/session/entry.lua`, `src/desktop/session/hypr/`,
    `hyprland-portals.conf`, `50-tamlinux-hyprland-*.hook`,
    `tam-hyprland-reload-guard`, `tamlinux-monitor-watch.service`,
    `src/desktop/native/providers/display/` patches, and all 25
    `tam-hyprland-*` and `tam-restart-hypr*` command directories. Remove
    `HyprlandAdapter.qml`, `Quickshell.Hyprland` imports, `ProtocolShadow.qml`,
    `tam-protocol-shadow`, `tamlinux-protocol-shadow-collect.{service,timer}`
    and all `hyprctl` code paths from `Compositor.qml`, `hyprland_backend.py`,
    `compositor_commands.py`, `session_start.py`, `console.py`,
    `session_settings.py`, `fred.workspaces` and `fred.monitor`. Make
    `tam-desktop` launch `tam-pane` exclusively.
16. **Remove Hyprland, Aquamarine and superseded dependencies across the fleet.**
    Remove `hyprland`, `hyprland-plugin-hyprbars`, `hypridle`, `hyprlock`,
    `hyprsunset`, `hyprpicker`, `xdg-desktop-portal-hyprland`,
    `hyprland-guiutils`, `hyprland-preview-share-picker`, `aquamarine`,
    `hyprcursor`, `hyprgraphics`, `hyprlang`, `hyprtoolkit`, `hyprutils`,
    `hyprwire`, `hyprwayland-scanner` and test-only `sway` / `swaybg` from
    `src/desktop/source-install/arch-packages`, `preflight.py`,
    `install-product.py` and every fleet host. Retire superseded terminal and
    editor fallback dependencies as `tam-last`, `tam-clam`, `tam-edit` and
    `tam-view` complete their dogfooding gates, and advance `tam-pane` toward
    its minimal `libc` + `libtam` + Mesa dependency footprint
    ([own the stack](https://github.com/greenermoose/tam-pane/blob/dev/plans/P6-own-the-stack.md)).
17. **Verify clean builds, fleet-wide operation and Northern Torch closure.**
    Prove `make`, `make preflight`, `make install`, `tests/check-all` and
    `tam-desktop-test` with zero Hyprland references in the runtime tree and
    zero `hypr*` / `aquamarine` packages installed on `bosgame`, `slowhp` and
    `toughbook`. Complete sustained daily use across the fleet on `tam-pane`
    alone to close Northern Torch.

## 1.0.0: fresh-install path and GitLab

Prove the repeatable fresh-install path and transition to fresh GitLab
repositories (`plans/P2-1.0.0-gitlab-and-source-install.md`).

## 1.1–1.3: other distributions and a minimal base

Verify a second distribution, then pilot Void Linux + runit + seatd + Btrfs
with native `xbps-src` delivery (antiX Core/runit as fallback), comparing
musl and glibc, followed by repeatable installation and terminal-only
profiles (`plans/P3-base-operating-system.md`).
