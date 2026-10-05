# Changelog

All notable changes to Tamlinux are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
as defined in [`VERSIONING.md`](VERSIONING.md).

## [Unreleased]

### Added

- **Media keys in the Tamlinux host** (2026-10-04, toward 0.0.3). The
  [desktop host](desktop/README.md) runs a media service that picks the
  playing MPRIS player for play, pause, stop, next, previous, and the source
  switch, and shows each action on the host's on-screen display.

### Fixed

- **`$TAMLINUX_VERSION` is set again** (2026-10-04). It was declared but
  never reached a shell or the session. Each new bash shell now reads it from
  `~/.config/tamlinux/version`, the user manager loads it at login, and each
  activation updates the running session. [`VERSIONING.md`](VERSIONING.md)
  says which surface to trust.

## [0.0.2] - 2026-10-04

### Added

- **Tamlinux owns the foundation** (the 0.0.2 milestone in
  [`VERSIONING.md`](VERSIONING.md)). Packages come from Arch's own mirrors and
  the workstation boots the stock Arch `linux` kernel. Tamlinux owns the
  Hyprland configuration, the shell environment, the session entry and
  session units, and the login screen (theme, greeter, and autologin).
- **Session services in the Tamlinux host**, toward 0.0.3. The
  [desktop host](desktop/README.md) runs notifications, the on-screen
  display, clipboard history, the emoji and image pickers, reminders, the
  command menu, the desktop background, and the polkit agent as session
  services beside the existing bar. Screenshots use Tamlinux's own commands.
  Before 0.0.3: screen recording and text and QR-code capture; media
  controls, night light, idle and Stay Awake, and low-battery warnings; the
  browser extensions; the monitor watch; and every other command the desktop
  calls.

### Changed

- **Smaller steps to 0.1** (2026-10-04). [`VERSIONING.md`](VERSIONING.md)
  now names two milestones before 0.1. **0.0.2**: Tamlinux owns the
  foundation (Arch's own package mirror and stock kernel, the Hyprland
  configuration, the shell environment, the session entry, and the login
  screen). **0.0.3**: the shell's session services run in the Tamlinux host
  and only the bar is left to replace. Before 0.1, a 0.0.x patch number marks
  a milestone, not a fix.
- **Omarchy is removed before Hyprland** (2026-10-04). **0.3** now means
  Omarchy is gone from the workstation while Hyprland keeps running: its
  functions are replaced, its packages, package mirror, and kernel are removed,
  and the desktop carries Tamlinux's own name and look. 0.4 installs the Sway
  session beside the Hyprland session, 0.5–0.9 fall back to Hyprland, and
  1.0.0 removes Hyprland. Updated [`VERSIONING.md`](VERSIONING.md), the
  [README](README.md), and the
  [desktop decoupling plan](docs/plans/desktop-decoupling.md).

- Set the **route and version series** in [`VERSIONING.md`](VERSIONING.md):
  0.1 owned shell with the eight rewritten plugins, 0.2 compositor contract,
  0.3 remaining Omarchy functions replaced, 0.4 workstation package beside
  Omarchy, 0.5–0.9 release candidates, **1.0.0 Omarchy and Hyprland removed**
  from the workstation, 1.1 a second distribution, 1.2 the Void pilot, 1.3
  repeatable installation and the terminal-only profile. The workstation
  package installs on existing distributions with a Nix flake and a native
  host adapter, and on Void as native `xbps-src` packages. Updated the
  [README](README.md), [installation framework](docs/plans/installation-framework.md),
  [desktop decoupling plan](docs/plans/desktop-decoupling.md), and
  [plans index](docs/plans/README.md) to match.
- Set **Void Linux as the first target base**, with antiX Core as the fallback
  if Void has a showstopper. Updated the architecture, installation, and desktop
  plans directly. Btrfs is the preferred pilot filesystem; musl/glibc and native
  XBPS/xbps-src versus portable delivery are evaluated rather than assumed.
  See the [base plan](docs/plans/base-operating-system.md).

The following entries record earlier directions that led to this target:

- Recorded the decision to use **runit** for system initialization and service
  management for the target workstation in [`README.md`](README.md),
  [`VERSIONING.md`](VERSIONING.md), and the
  [installation framework](docs/plans/installation-framework.md).
- Recorded the 2026-10-03 targets in [`README.md`](README.md): hardware from
  circa 2006 onward (older is out of scope) on Wayland, not X11; antiX Linux
  Core with a tiling window system inspired by the Omarchy UI, with the
  compositor reopened (River is no longer the settled choice); Chrome and VS
  Code must run; and a terminal-first experience. Updated
  [`VERSIONING.md`](VERSIONING.md) and the
  [installation framework](docs/plans/installation-framework.md) to match.
- Added the [compositor field survey](upstream/2026-10-03-compositor.md) and
  recorded its outcome: **Sway**, built by Tamlinux with Nix. River,
  river-classic, and mango are deferred; dwl and niri are rejected for now.
- Recorded the Nix-built workstation package (on antiX Core or an existing
  Linux), the three kinds of terminal-only machine, and the package design
  points in the [installation framework](docs/plans/installation-framework.md).

- Refined architectural vision and public explainer in [`README.md`](README.md):
  clarified that Arch Linux's appealing idea is continuous rolling updates,
  adopted AntiX Linux's inspiration for older hardware support and lean
  non-systemd base layer, and elevated simplifying and minimizing resource use
  as a general principle that allows Linux to run faster and use less energy
  on modern hardware as well.
- Defined the transition roadmap: working from Omarchy (0.x) toward an AntiX
  Linux base layer (`antiX Core` + `seatd` + Wayland + River, with Nix rollbacks).
- Updated [`UPSTREAM.md`](UPSTREAM.md) and [`VERSIONING.md`](VERSIONING.md) to
  align with the AntiX base layer trajectory.
- Updated [`docs/plans/installation-framework.md`](docs/plans/installation-framework.md)
  and [`docs/plans/README.md`](docs/plans/README.md) to replace the exploratory
  NixOS/Arch host sequence with the settled AntiX Linux Core base sequence and
  Maker Fest distribution model.

## [0.0.1] - 2026-09-22

### Added

- First product version. Tamlinux 0.0.1 is the current workstation snapshot:
  Omarchy plus Fred's patches and `fred.*` plugins.
- [`VERSIONING.md`](VERSIONING.md) records the 0.x / 1.x split, the
  workstation-then-installer order, and that Home Manager generations are a
  local rollback handle, not the product number.

[Unreleased]: https://github.com/greenermoose/tamlinux/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/greenermoose/tamlinux/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/greenermoose/tamlinux/releases/tag/v0.0.1
