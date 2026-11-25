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

## 0.6.x: KBN WB — dependable baseline (current)

Fix GPU-resume and hibernation faults or accept mitigations, pin carried
patches with upstream status, establish routine updates and rollback, move
from `tam-bundle` to locked source installs (`make` / `make install`), and
prove host-safe installs across the fleet (`plans/P21-source-install.md`).

## 0.7.0: Northern Torch — the bosgame desktop on tam-pane

Fred can log in at a text console, select the graphical desktop in
`start`, and work all day across bosgame's three monitors with tam-pane
as the compositor. Hyprland remains an independent recovery session.
These milestones lead from the nested tam-pane 0.2.6 trials through
the [0.3.x session and shell work](https://github.com/greenermoose/tam-pane/blob/dev/plans/P4-dogfood-tamlinux-0.7.md).

1. **Account for every app.** Build a checklist from the installed manifest,
   component pins, console activities, desktop entries, Start menu, Quick
   Launch, bindings, shell services and plugin manifests. Include bosgame's
   personal launchers and overrides. Give each entry its normal launch path,
   one real task, its compositor dependencies and a result. Identify the
   Hyprland recovery commands so every everyday action has a tam-pane path.
2. **Deliver a reproducible session.** Pin tam-pane and compatible libtam
   in the [source delivery](plans/P21-source-install.md). Stage the Make
   install, Arch dependencies, Wayland session entry and versioned defaults.
   Honor local development builds on PATH (via `make install` or `tam-dev try tam-pane`)
   while falling back to the packaged cultivar binary and verifying the packaged
   binary by its absolute cultivar path. Start with native Wayland. Enable and test
   the optional XWayland build if the checklist identifies a required X11 app.
3. **Provide two guarded console launches.** Add `tam-desktop pane` for
   trials and `tam-desktop hyprland` for recovery. Keep the graphical
   activity in `start` routed through bare `tam-desktop`. Extend local VT,
   duplicate-session and shutdown checks to both compositors. On normal
   exit, startup failure and crash, release the console only when graphics
   has stopped. Start Hyprland with the tam-pane configuration unavailable.
4. **Bring up the complete session.** Use a UWSM session target. Publish
   the desktop identity, Wayland display and tam-pane socket to systemd
   and D-Bus before starting Quickshell, portals and helpers. Verify one
   shell and polkit agent, file chooser and PipeWire screen sharing. On
   exit, check service cleanup and start Hyprland with its own environment
   and portals.
5. **Connect the shell to tam-pane.** Extend the existing compositor
   facade with a tam-pane adapter. Use ProtocolState for standard Wayland
   facts and tam-pane IPC for missing state and actions. Represent multiple
   visible tags per output and windows on several tags. Verify focus, tag
   changes, output power, pointer location, bindings and keyboard layout,
   including initial state, event updates and reconnection on two outputs.
   Follow the [shared protocol plan](plans/P6-compositor-protocol-layer.md).
6. **Port bosgame's controls.** Translate effective monitor geometry and
   scale, input settings, window rules, shortcuts, mouse bindings, autostart
   and macros into tam-pane configuration. Preserve personal overrides
   across reloads. Exercise launch-or-focus, terminal working directory,
   window placement, monitor controls, brightness, night light, screenshots
   and recording from their usual menus and keys. Try one-handed chords,
   layout switching and macro paste in real applications.
7. **Prove the shell and apps.** Exercise the bar, menus, panels, popup
   focus, notifications, OSD, clipboard, authorization and theme changes.
   Check all nine shipped fred.* plugins, especially workspaces, monitor
   and keyboard across outputs. With Hyprland stopped, use each app through
   its checklist entry. Run tam-clam in tam-last and save an edit in
   tam-edit. Cover terminal tools, GTK, Qt, browsers and webapps, including
   typing, paste, focus, dialogs and relaunch. Keep Bash, Foot and Micro
   available during the component trials.
8. **Automate repeatable checks.** Run the [desktop test battery](plans/P10-desktop-test-battery.md)
   on headless tam-pane for session selection, shell actions, app launches,
   clipboard, capture and tags. Cover the Hyprland fallback too. Move the
   offscreen suite from Sway once tam-pane serves the same cases. Run the
   packaged shell and clients together in an isolated nested session before
   the first hardware Test.
9. **Prove hardware and recovery on bosgame.** On Fred's Test word for the
   exact candidate, record the previous source stage and Snapper snapshot
   before individually approved login changes. From a physical VT, prove
   switching away and back and emergency exit. Test all three monitors,
   dragging and moving windows between them, floating-window centering,
   unplug/replug, blank/wake and restored layouts. Check authenticated
   lock/unlock on every output, idle inhibition, suspend and hibernate/resume.
   Complete and verify tam-pane's renderer-loss recovery before the day trial.
10. **Accept a working day and switch the default.** Fred works a full day
    on tam-pane without falling back. Require passing results for every
    everyday app, record outstanding defects and prove the Hyprland recovery
    command from a text login. On Fred's separate Run word for the accepted
    candidate, make tam-pane bosgame's default for the graphical activity in
    `start` and bare `tam-desktop`. Verify default and recovery launches
    after fresh text login. Release requires its own instruction.

## 1.0.0: fresh-install path and GitLab

Prove the repeatable fresh-install path and transition to fresh GitLab
repositories (`plans/P2-1.0.0-gitlab-and-source-install.md`).

## 1.1–1.3: other distributions and a minimal base

Verify a second distribution, then pilot Void Linux + runit + seatd + Btrfs
with native `xbps-src` delivery (antiX Core/runit as fallback), comparing
musl and glibc, followed by repeatable installation and terminal-only
profiles (`plans/P3-base-operating-system.md`).
