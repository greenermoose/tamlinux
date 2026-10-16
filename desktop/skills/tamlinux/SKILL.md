---
name: tamlinux
description: >-
  Inspect Tamlinux system status and health, or customize its Hyprland desktop,
  Quickshell shell, fred.* plugins, themes, displays and keybindings. Discover
  tam and tam-* commands and distinguish packaged defaults from user overrides.
  Replaces the Omarchy desktop skill on Tamlinux installations.
---

# Tamlinux desktop

Tamlinux supplies the desktop and user tools on an Arch Linux host. Hyprland
and UWSM start the graphical session; the Tamlinux Quickshell service supplies
the bar, panels and desktop services. Check installed versions and running
processes rather than inferring ownership from an inherited logo or filename.

## Establish the effective installation

- Use `tam-deploy status` for the selected assembly and user generation.
- Read `systemctl --user status tamlinux-shell.service` and its unit definition
  to identify the actual executable, package revision and resource paths.
- For a health report, inspect the relevant journal, compositor configuration
  errors and failed units. Report evidence and remaining uncertainty; do not
  restart the desktop, change settings or trigger sleep as part of inspection.
- Use `tam --help` and installed command help to discover available interfaces.
  Inspect a command before invoking it if its effect is unclear. Product
  executables use `tam` or `tam-*`; `fred-*` commands are personal additions.

## Boot, unlock and login are separate

A boot-menu choice selects an operating system. The encrypted-filesystem
password unlocks storage. A display manager can then log in automatically, so
the user may never see a session selector. Logout can reveal a greeter that
was skipped during startup.

Read the actual display-manager unit, its configuration and its running login
command before suggesting a different session. A `.desktop` session entry on
disk does not prove that it was used or that the user can select it. Record
the effective automatic-login user and entry. Prepare a recoverable change
before asking the user to exercise a new path.

## Configuration ownership

The selected immutable package supplies defaults under
`~/.local/share/tamlinux/`; Home Manager supplies links, units and the session
entry under `~/.config/tamlinux/session/`. User Hyprland overrides belong under
`$XDG_CONFIG_HOME/tamlinux/hypr/` (normally `~/.config/tamlinux/hypr/`). A
consumer can still have a live-linked legacy `~/.config/hypr/` configuration;
resolve links and inspect the running compositor command before choosing
which file to change.

Shell layout and settings live under `$XDG_CONFIG_HOME/tamlinux/shell/`.
Mutable selections live under `$XDG_STATE_HOME/tamlinux/`. Trace the relevant
reader and preserve existing selections before changing them. Never edit
Nix-store files or package-managed defaults in `/usr`. Modify the product
source for defaults, the deployment configuration for managed links and units,
or the user's override for personal changes.

During the transition, inherited Omarchy packages may remain installed as a
read-only fallback. Do not use their update, refresh or reset commands to
manage the Tamlinux desktop. Their removal belongs to the reviewed cutover.

## Verify and promote

For Hyprland changes, inspect the effective configuration and run
`hyprctl configerrors` after the requested reload. For shell changes, inspect
the selected service's journal and verify the affected surface and IPC action.
Preserve display geometry, user settings and later writes through recovery.
Static checks do not establish a successful physical login, boot or resume.

Develop changes in the owning source repository. A requested development
version does not authorize activation. Test installs an exact candidate with
a recorded way back; Run makes an accepted candidate the normal installation;
Release endorses that exact version. Each transition requires the user's
instruction. Boot, encrypted-root and package-removal work need a concrete
transaction and recovery record before execution. Follow repository-specific
instructions for concurrency, validation and promotion.
