# Changelog

All notable changes to Tamlinux are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
as defined in [`VERSIONING.md`](VERSIONING.md).

## [Unreleased]

### Changed

- **Every accepted step is a version** (2026-10-05). The minor version names
  a stage and the patch a step, so each change Fred accepts into daily use
  raises the version. The stages after 0.1 are re-planned: 0.2 moves every key
  binding and menu entry to Tamlinux's own commands, 0.3 is the Tamlinux bar,
  0.4 the compositor contract, 0.5 Tamlinux's own look and name, 0.6 Omarchy
  removed, 0.7 the workstation package beside Hyprland, and 0.8 the Sway
  session as the daily driver; 1.0.0 still removes Hyprland.
  [`VERSIONING.md`](VERSIONING.md) has the rules and the table. The planned
  0.0.3 was never issued; its work is 0.1.0–0.1.22 below.
- **"The Tamlinux shell"** (2026-10-05). The program that draws the bar and
  runs the session services is called the Tamlinux shell, as its
  predecessor was the Omarchy shell. "Host" now names only the part plugins
  talk to (the host contract) and, for the workstation package, the
  distribution it is installed on and its host adapter. Earlier records say
  "the Tamlinux host" for the shell. See [`desktop/README.md`](desktop/README.md).
- **"Ported"** (2026-10-05). Code taken over from Omarchy is *ported*:
  copied with its MIT notice, adapted to Tamlinux, and maintained here.
  Headers and docs say "Ported from"; earlier records say "vendored".

## 0.1.0 to 0.1.22 - 2026-10-04 to 2026-10-05

Numbered on 2026-10-05, in the order each step was accepted into daily use.
Not tagged.

| Version | Accepted | Step |
| :-- | :-- | :-- |
| 0.1.0 | 2026-10-04 | Notifications in the Tamlinux shell |
| 0.1.1 | 2026-10-04 | On-screen display; a microphone-mute key for the Calliope keyboard |
| 0.1.2 | 2026-10-04 | Clipboard history |
| 0.1.3 | 2026-10-04 | Emoji picker |
| 0.1.4 | 2026-10-04 | Image picker for theme, background, and unlock screen |
| 0.1.5 | 2026-10-04 | Reminders |
| 0.1.6 | 2026-10-04 | The command menu |
| 0.1.7 | 2026-10-04 | Desktop background |
| 0.1.8 | 2026-10-04 | Screenshots |
| 0.1.9 | 2026-10-04 | Polkit agent |
| 0.1.10 | 2026-10-04 | Screen recording, text and QR-code capture, webcam overlay |
| 0.1.11 | 2026-10-04 | Media keys, idle and Stay Awake, battery warnings and power profiles |
| 0.1.12 | 2026-10-04 | Browser extensions |
| 0.1.13 | 2026-10-04 | Monitor watch |
| 0.1.14 | 2026-10-05 | Audio and brightness commands |
| 0.1.15 | 2026-10-05 | Update and recovery commands |
| 0.1.16 | 2026-10-05 | Lock screen with `hyprlock` |
| 0.1.17 | 2026-10-05 | Shared menu terminal and helpers |
| 0.1.18 | 2026-10-05 | System menu, crash capture, and session units |
| 0.1.19 | 2026-10-05 | Trigger menu |
| 0.1.20 | 2026-10-05 | Menu entries for dropped features removed |
| 0.1.21 | 2026-10-05 | Setup menu: defaults, DNS, security |
| 0.1.22 | 2026-10-05 | App install and remove, launchers, and app keys |

### Added

- **Media keys in the Tamlinux shell** (2026-10-04). The
  [Tamlinux shell](desktop/README.md) runs a media service that picks the
  playing MPRIS player for play, pause, stop, next, previous, and the source
  switch, and shows each action on the shell's on-screen display.
- **Stay Awake and the idle cycle in the Tamlinux shell** (2026-10-04). The
  [Tamlinux shell](desktop/README.md) runs an idle service with the Stay Awake
  switch, kept in one state file that idle suspend can honour, and
  an idle cycle that starts the screensaver and then the lock. Each stage is
  off unless its timeout is set.
- **Low-battery warning and power profiles in the Tamlinux shell**
  (2026-10-04). The [Tamlinux shell](desktop/README.md) runs a
  battery service that warns once when a draining battery reaches 10% and
  sets the power profile for battery or mains power when the source
  changes. On a machine without a battery it does nothing.

### Changed

- **Browser extensions are Tamlinux's own** (2026-10-04). The
  three Chromium extensions (copy URL, download video, and the slim WhatsApp
  window) and their two native-messaging helpers load from Tamlinux's
  configuration.
- **The monitor watch is Tamlinux's own** (2026-10-04). The
  service that reacts to displays appearing and disappearing, and the helpers
  it calls, run from Tamlinux's configuration; the display recovery hooks still
  fire after resume.
- **The lock screen is Tamlinux's own** (2026-10-05, 0.1.16). The lock key
  and menu entry use Tamlinux's own command, which starts `hyprlock`.

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
- **Session services in the Tamlinux shell** (2026-10-04; numbered 0.1.0–0.1.8
  on 2026-10-05). The [Tamlinux shell](desktop/README.md) runs notifications,
  the on-screen display, clipboard history, the emoji and image pickers,
  reminders, the command menu, the desktop background, and the polkit agent
  as session services beside the existing bar. Screenshots use Tamlinux's own
  commands.

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
