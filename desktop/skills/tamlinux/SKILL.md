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

- On a source-installed host, inspect the active manifest under
  `/var/lib/tamlinux/source/` and use `make verify` as the normal user from
  the product checkout. On a bundle host, use `tam-deploy status` or
  `tam-bundle status` for the selected bundle.
- Read `systemctl --user status tamlinux-shell.service` and its unit definition
  to identify the actual executable, package revision and resource paths.
- For a health report, inspect the relevant journal, compositor configuration
  errors and failed units. Report evidence and remaining uncertainty; do not
  restart the desktop, change settings or trigger sleep as part of inspection.
- Use `tam --help` and installed command help to discover available interfaces.
  Inspect a command before invoking it if its effect is unclear. Product
  executables use `tam` or `tam-*`; `fred-*` commands are personal additions.

## Boot, unlock and login are separate

A boot-menu choice selects the system. Disk unlock, text login, and optional
desktop launch are separate checks. Inspect the actual getty, session unit
and launcher before diagnosing a live host. Prepare a recorded rollback point
and obtain the user’s approval for a login or boot change.

## Configuration ownership

The source-installed runtime lives under `/usr/lib/tamlinux/source/current/`.
The recorded bundle runtime lives under `/usr/lib/tamlinux/current/` on hosts
still using bundles. Resolve the actual service and launch paths before
editing. Personal Hyprland overrides belong under
`$XDG_CONFIG_HOME/tamlinux/hypr/` (normally `~/.config/tamlinux/hypr/`).

Shell layout and settings live under `$XDG_CONFIG_HOME/tamlinux/shell/`.
Mutable selections live under `$XDG_STATE_HOME/tamlinux/`. Trace the relevant
reader and preserve existing selections before changing them. Use the product
checkout for packaged defaults, the recorded delivery for runtime changes,
and the user’s configuration for personal overrides.

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
