# Tamlinux versioning

Tamlinux uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The published number is the file [`VERSION`](VERSION) in this repository.
The private workstation checkout keeps a matching `VERSION` so the running
machine and this explainer agree.

## What the numbers mean

**The version is the plan.** The minor version names a *stage*, and the patch
names a *step* within it. A step is one change Fred tests on his workstation
and accepts into daily use; its version is its name. The first accepted step
of stage 0.3 is 0.3.0, the next 0.3.1, and so on. Every accepted step raises
the version, so the number shows which stage Tamlinux is in and how far
through it.

- A step's number is fixed when work on it starts. Steps not yet started may
  be split, merged, or renumbered when a stage is re-planned.
- Fixes ship with the step they belong to or the next one; they do not get a
  number of their own. Development work and documentation do not raise the
  version.
- **1.x** means Tamlinux no longer depends on [Omarchy](https://omarchy.com)
  or Hyprland. The 0.x stages remove Omarchy first (0.6), while Hyprland keeps
  running; **1.0.0** removes Hyprland. After 1.0.0 the same rule applies:
  stage 1.N, steps 1.N.k.

This scheme was adopted on 2026-10-05. Before it, minor versions were fixed
milestones and work between them raised no number, so the steps accepted
since 0.0.2 were numbered afterwards, in the order they were accepted
(0.1.0–0.1.22; see [`CHANGELOG.md`](CHANGELOG.md)). An earlier "0.0.3" was
planned but never issued.

| Stage | Tamlinux is there when | Base | Desktop |
| :-- | :-- | :-- | :-- |
| **0.0** | 0.0.1: the first workstation snapshot (Omarchy, Fred's patches, and the released `fred.*` 1.x plugins). 0.0.2: the foundation is owned: Arch's own package mirror and stock `linux` kernel, the Hyprland configuration, the shell environment, the session entry and units, and the login screen. | Arch | Omarchy shell on Hyprland |
| **0.1** | The desktop's session services run in the Tamlinux shell beside the existing bar: notifications, on-screen display, clipboard history, emoji and image pickers, reminders, the command menu, the background, screenshots and screen capture, the polkit agent, media keys, idle and Stay Awake, battery warnings, and the lock screen; and the commands the desktop calls are Tamlinux's own. | Arch | Existing bar, Tamlinux services |
| **0.2** | Every key binding and menu entry runs Tamlinux's own commands, including the keybinding viewer, night light, and the audio, Bluetooth, network, power, and speed-test panels. Only the bar's own keys and settings wait for 0.3, and the theme, branding, and boot-splash entries for 0.5 and the boot work. Reached 2026-10-05 (0.2.0–0.2.6). | Arch | Existing bar, Tamlinux services and panels |
| **0.3** | The Tamlinux shell, with all eight rewritten plugins and its own tray, indicators, and status widgets, is the daily bar. | Arch | Tamlinux shell on Hyprland |
| **0.4** | Plugins and helpers reach the compositor only through the compositor contract; the Hyprland adapter is in daily use and the Sway adapter passes its tests. | Arch | Tamlinux shell on Hyprland |
| **0.5** | Tamlinux's own look and name: one theme source for every application, its own fonts, and its name on the login screen, menus, and About. | Arch | Tamlinux shell on Hyprland |
| **0.6** | Omarchy is removed; Hyprland stays. Its packages, package mirror, repository, and kernel are gone, and nothing running or installed comes from it. | Arch | Tamlinux on Hyprland |
| **0.7** | The `tamlinux` workstation package exists and installs a Sway session beside the Hyprland session. | Arch | Both sessions available |
| **0.8** | The Sway session is the daily driver while the Hyprland session remains the fallback; one step per parity milestone. | Arch | Tamlinux on Sway |
| **1.0** | Hyprland is removed from the workstation. The first installation of the workstation package on an existing distribution. | Arch | Tamlinux on Sway |
| **1.1** | The same package installs on a second, different distribution on another machine. | Arch + one other | Tamlinux on Sway |
| **1.2** | Void pilot: the same sources as native `xbps-src` packages on Void + runit + Btrfs + seatd, with complete recovery proved. antiX Core + runit only if Void has a showstopper. | + Void pilot | Tamlinux on Sway |
| **1.3** | Repeatable live-media base install, single-command workstation activation, and the terminal-only profile. | + Void pilot | + terminal-only |

There is no planned 2.x. Tamlinux is a temporary testbed: after its last 1.x
it freezes, and anything that follows is a separate announcement.

Plugins version separately. Each rewritten plugin becomes `fred.<id>` 2.0.0,
because it drops the Omarchy shell's plugin API; the 1.x lines remain as released. The
workstation package carries the Tamlinux version and records its component
versions in its manifest.

**0.0.1** is the first workstation snapshot: this daily driver, working as
Tamlinux. Installing on a second computer comes at 1.1, after the
workstation package has replaced the inherited desktop on this machine.

When Fred accepts a step, write its version in both `VERSION` files, log it
in [`CHANGELOG.md`](CHANGELOG.md), and keep the two files identical. Tag a
version when Fred asks for one.

## What Tamlinux version is not

Plugin versions (`fred.workspaces`, `fred.clock`, and the rest), the
`tam-plugin` CLI, and the `ecosystem-fred-tamlinux` patch registry stay
independent artifacts. They have their own `VERSION` or `manifest.json`
numbers.

The last overlay-era workstation composite was **1.5.1**. Those git
tags stay. They are no longer the product version. 0.0.1 is that overlay
frozen into Tamlinux.

## Tamlinux version vs Home Manager generation

These are two different counters. Do not set Tamlinux to `0.0.x` where `x` is
the Home Manager generation.

| | Tamlinux version | Home Manager generation |
| :-- | :-- | :-- |
| What it is | Declared product snapshot (portable, tagged, changelogged) | Local activation counter on one machine |
| Source of truth | `VERSION` files | `home-manager generations` / `~/.config/tamlinux/generation` |
| Advances when | Fred decides the product changed | Every successful `home-manager switch` |
| Portable? | Yes — the same number on a second computer | No — a fresh machine starts at 1 |

On a running workstation:

```bash
cat ~/.config/tamlinux/version           # product version of the active generation
echo "$TAMLINUX_VERSION"                 # the same number, as this process saw it
cat ~/.config/tamlinux/generation        # this machine's Home Manager generation
home-manager generations                 # full local rollback list
```

The file is the source of truth: activation writes it with every generation.
`$TAMLINUX_VERSION` is copied from it in three places. Every new bash shell
reads the file, the systemd user manager loads it at login (`environment.d`),
and each activation also sets it in the running user manager, so services
and applications started after a switch see the new number without a new
login. A process that was already running keeps the number it started with.

`$OMARCHY_CONFIG_VERSION` and `~/.config/omarchy/version` remain as
compatibility aliases of `$TAMLINUX_VERSION` until 0.5 removes them. They are
not a second product.
