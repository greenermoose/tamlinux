# Changelog

All notable changes to Tamlinux are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
as defined in [`VERSIONING.md`](VERSIONING.md).

## [Unreleased]

### Added

- **`tam-work` for shared checkouts** (2026-10-09). The command that lets
  several sessions, people or AI agents, work in the same Git checkouts
  without overwriting each other is now part of Tamlinux, in
  [`commands/tam-work/`](commands/tam-work/README.md). Sessions claim the
  paths they will edit and overlapping claims are refused.
  `TAM_WORK_WORKSPACE` and `TAM_WORK_REGISTRY` override the default
  workspace (`~/Code/tamlinux`) and claim registry
  (`<workspace>/worktrees/coordination`). `make check` runs its tests and
  `make install` honours `PREFIX` and `DESTDIR`.

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

## 0.4.2-a - Unreleased

- Product-owned menu defaults and `tam-menu`, with personal extensions at
  `tamlinux/menu/extension.jsonc`. Retained rows, routes, aliases and actions
  survive the ownership split.
- Bounded JSONC parsing and file reads preserve quoted comment/comma text.
  Failed reads, parses and invalid merged routes retain the last valid menu;
  status and refresh IPC expose reload state.
- The candidate is delivered as a pinned `tamlinux-packages` assembly through
  the same Nix/Home Manager endpoint used for Run. Physical Test acceptance
  remains pending.

## 0.4.1 - 2026-10-09

- Fred accepted daily compositor protocol shadow observation on the current Hyprland desktop: “I accept tamlinux 4.0.1. Make a note of that.” This identifies the planned product step 0.4.1.
- Retain the exact tested shell and its passive comparison logging; IPC still supplies authoritative compositor facts and display power.
- Repair monitor runtime-permission handling in `fred.monitor` 2.0.3 and add regression tests. Deployment guards protect pending Test from accidental replacement or promotion of a different candidate.
- Historical output disagreements and observation gaps remain open before protocol authority. Menu ownership and parser safety are next at 0.4.2.
- The 0.4.1 package: the accepted plugin payloads now live in `desktop/plugins/`, and the product commands `tam-work`, `tam-deploy` and `tam-plugin` in `commands/`, so `tamlinux-packages` can assemble and deploy 0.4.1 from this revision. The shell is unchanged from the accepted `a0d7737`.

## 0.4.0 - 2026-10-08

### Changed

- Non-theme user settings, state and caches use Tamlinux paths. Readers,
  writers, watchers and collectors agree; migration respects XDG homes,
  retains originals and valid existing destinations, and supports validated
  rollback and resume. Desktop keys and bar actions share one active helper.
- The eight exercised plugins use normal immutable Run payloads with all
  temporary overrides removed. Theme, menu, branding and host exceptions
  remain assigned to their later steps; the daily shell pin is unchanged.

### Verification

- Fred: “Yes, I've tested the current desktop and accept 0.4.0.”
- All 494 workstation configuration tests passed. Three-display desktop
  modes, movement and blank/wake, saved weather/tides choices, agent refresh
  and sysinfo passed. Sixteen preference checks and all eight plugin payloads
  survived physical logout/login and remained unchanged in normal Run.
- 0.4.1 daily protocol shadow testing can now proceed as the next step.

## 0.3.3 - 2026-10-06

The Tamlinux shell is the daily bar on all three screens. Stage 0.3 is
complete when a day's use is accepted.

### Changed

- The session unit runs the whole shell: the bar on every screen with the
  eight deployed 2.0.0 plugins, placed by the layout document, plus the
  session services and panels. Plugin actions are live.

### Fixed

- The daily bar reserves its own height, so tiled windows no longer slide
  under it.
- Clicking a workspace number on the bar switches workspaces again. The
  session start script now exports `TAMLINUX_COMPOSITOR_COMMANDS` (the
  shell's `host/` directory); without it the `fred.workspaces` and
  `fred.monitor` helpers could not load the compositor backend and did
  nothing. Only the isolated proof had set it.
- The bar's monitor power state stays current. The Hyprland adapter read
  `hyprctl monitors` once at startup, and Hyprland sends no event when an
  output's power changes, so `dpmsOn` stayed true for a monitor that
  `fred.workspaces` had blanked, and moving the pointer into it did not
  wake it. The adapter now reads the monitors again when focus moves to
  another output, when an output is added or removed, and after its own
  DPMS change.

### Removed

- `desktop/launch-daily-bar`; the session unit starts the daily bar.

## 0.3.2 - 2026-10-06

Daily-bar readiness; the daily bar cutover is the separate 0.3.3 step.

### Added

- Top/bottom bars, focused-output IPC routes and numbered panel routes,
  hide/show and saved transparency/position, and broadcast indicator refresh.
- A validated plugin map and session starter. Rejected plugins are named
  in the log and omitted while valid widgets continue to load.
- A one-time shell.json converter for layout and per-widget settings at
  `~/.config/tamlinux/shell/`.
- The isolated selftest covers all three outputs, bar controls, converted
  clock settings, and an invalid plugin at scales 1 and 1.25. Its two-copy
  primary fixture stays on one output when `--output all` is requested.

### Changed

- Shell-owned actions invoke Tamlinux commands. Tests and proof launchers
  find their sources when running from a Git worktree.
- Session deployment pins a committed main revision in an immutable store
  tree; checkout edits stay in Develop/Test. The launcher uses an isolated
  state directory as well as home/config/cache directories.

## 0.3.1 - 2026-10-06

The Tamlinux bar's own widgets.

### Added

- **The bar draws a layout.** Left, center, and right sections with a center
  anchor, as on Omarchy's bar, from `TAMLINUX_BAR_LAYOUT`. The default
  layout is today's Omarchy bar order. Omarchy's layout model is ported
  (`BarModel.js`).
- **The shell's own widgets:** the menu button, the indicators (screen
  recording, reminders, night light, Do Not Disturb, Stay Awake), the
  keyboard layout, the tray, and the audio, Bluetooth, network, and power
  icons that open the 0.2 panels.
- **A night light session service** that reads and flips the night light
  through `tam-toggle-nightlight`.
- `Tam.Ui` gains `BarIndicator` and `PopupCard`.

### Changed

- The keyboard layout widget and the popups' outside-click grab go through
  the compositor facade; no widget imports the compositor.
- Panel settings (the tray's pins, the battery percentage) are saved.
- Bar tooltips center on their item and stay inside the screen.

### Verification

- Fred checked the layout, hovers, every widget and panel, the center
  reveal, one popup per screen, closing on an outside click, and scale
  1.25, and accepted this step. Automated checks: the proof selftest with a
  layout stage and a tooltip edge probe, and 260 desktop tests.

## 0.3.0 - 2026-10-06

The first step of stage 0.3, the Tamlinux bar.

### Changed

- **The eight 2.0.0 plugins depend only on Tamlinux.** No plugin calls an
  `omarchy-*` command, reads `/usr/share/omarchy` or an `OMARCHY_*` variable
  (except `fred.workspaces` reading its old configuration keys), or names an
  `omarchy-*` layer. They run Tamlinux's own commands as
  `TAMLINUX_BIN + "/tam-..."`, falling back to `~/.local/bin`. Each plugin
  repository has a test that keeps it that way.
- **The proof launcher talks only to the shell it started.** It sends IPC by
  process ID, because the session's own Tamlinux shell shares its
  configuration directory, and it passes `TAMLINUX_BIN` into the isolated
  home.

### Verification

- Fred opened every plugin in the isolated Tamlinux shell, checked the clock
  and tides notifications, a weather location, Text Size and brightness, and
  accepted this step. Automated checks: the proof selftest at scale 1 and
  1.25 with all eight plugins, and 258 desktop tests.

## 0.2.6 - 2026-10-05

Stage 0.2 is complete: every key binding and menu entry runs Tamlinux's own
commands, except the bar's own keys and settings (0.3), the theme and
branding entries (0.5), and the boot-splash entries.

### Changed

- **Power panel and speed tests in the Tamlinux shell.** `SUPER + CTRL + P`
  opens the power panel; Trigger → Speed Test → Network and Disk open the
  speed-test cards, and the network panel's speed-test row now works.
- The power panel opens on machines without a battery, showing only the
  power-profile picker; the battery sections and the bar button still need a
  battery.
- The panel host answers `tam-shell tamlinux.panels summon <id>` and
  `hide <id>`, for cards without an IPC target of their own.

### Verification

- Fred opened the power panel from its key, changed the profile and back,
  ran both speed tests from the menu and the network test from the network
  panel, and accepted this step. Automated checks: 110 desktop tests, and
  all seven panels and the summon route in a headless compositor.

## 0.2.5 - 2026-10-05

### Changed

- **Network panel and Wi-Fi QR card in the Tamlinux shell.** `SUPER + CTRL +
  W` opens the network panel (connection, Wi-Fi networks, band, DNS); the
  QR card shares the connected Wi-Fi network with a phone. No new shell code:
  both panels were ported at 0.2.4 and are now loaded.

### Verification

- Fred opened the panel from its key, changed Wi-Fi and back, opened the QR
  card, and accepted this step. Automated checks: 110 desktop tests, and both
  panels loading in a headless compositor.

## 0.2.4 - 2026-10-05

### Changed

- **Audio and Bluetooth panels in the Tamlinux shell.** `SUPER + CTRL + A` and
  `SUPER + CTRL + B` open them as cards at the top of the focused output:
  output and input devices, volume, per-application mixer, and Bluetooth
  power, pairing, connection and forgetting (x). A panel host gives the
  ported panels their bar services without the Tamlinux bar; the shared
  controls gained the keyboard-cursor, password and spacing features the
  panels use.

### Verification

- Fred opened both panels from their keys, changed the output and volume,
  changed a Bluetooth connection and closed them with Escape, then accepted
  this step. Automated checks: 306 configuration tests, 101 desktop tests,
  12 real QML checks, and all seven ported panels loading in a headless
  compositor.

## 0.2.3 - 2026-10-05

### Changed

- **Night light on Tamlinux commands.** `SUPER + CTRL + N` and Trigger →
  Toggle → Nightlight toggle the screen temperature through Hyprland's
  `hyprsunset`; Setup → Config → Hyprsunset and Update → Process →
  Hyprsunset restart it. The reset-to-default row is dropped: the
  configuration file is under version control.

### Verification

- Fred toggled the night light from the key and the menu, edited and
  restarted it from Setup and Update, and accepted this step. Automated
  checks: 301 configuration tests and 93 desktop tests.

## 0.2.2 - 2026-10-05

### Changed

- **Keybinding viewer in the Tamlinux shell.** `SUPER + K` and Learn →
  Keybindings list every binding from the compositor facade, searchable,
  alphabetical by what each binding does (numbers in number order). Enter
  runs the chosen binding's command. The facade reads the bindings again
  whenever Hyprland reloads its configuration.

### Verification

- Fred opened the viewer from the key and the menu, searched, closed it with
  Escape, and ran a binding with Enter, then accepted this step. The live
  rows match the inherited viewer's 252, commands included. Automated
  checks: 301 configuration tests and 66 desktop tests.

## 0.2.1 - 2026-10-05

### Changed

- **Style controls update the Tamlinux shell.** Theme, background and unlock
  use its pickers. Theme changes apply the selected palette and surface
  colors; font selection updates terminal configurations and restarts only
  the existing Tamlinux services shell. Font installation and theme removal
  use the owned helpers. Existing Foot windows need reopening after a font
  change.
- **Shared typography follows the theme.** Validated text size and spacing
  settings scale controls with the text. Theme reloads coalesce, and failed
  or malformed reads preserve the current appearance. Full design and
  typeface changes remain in their separately planned milestone.

### Verification

- Fred tested Theme, Background, Unlock and Font, each and back, and accepted
  this step. Automated checks: 301 configuration tests, 66 desktop tests and
  12 real QML checks at normal and fractional scale.

## 0.2.0 - 2026-10-05

The first step of stage 0.2: nothing Omarchy ships changes underneath the
workstation while Tamlinux replaces it.

### Changed

- **Omarchy's package repository is frozen.** It is no longer in
  `pacman.conf`, so its packages stay installed and get no updates until
  Tamlinux gives each one an owner or removes it. Arch updates continue
  through `tam-update`, which also keeps the AUR from replacing the frozen
  packages, among them the boot loader's hooks.

## 0.1.23 - 2026-10-05

The last step of stage 0.1: the desktop's session services run in the
Tamlinux shell, and the remaining commands its keys and menus call are
Tamlinux's own.

### Changed

- **Update menu and keys use Tamlinux's own commands.** Time sync, the
  timezone picker (now through `timedatectl` and the polkit prompt), the
  Wi-Fi, Bluetooth, and trackpad restarts, drive encryption, the time
  notification, and the window keys for pop-out, tiled full screen,
  transparency, saved width, and monitor scaling.

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
