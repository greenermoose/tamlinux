# Tamlinux versioning

Tamlinux uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The published number is the file [`VERSION`](VERSION) in this repository.
The private workstation checkout keeps a matching `VERSION` so the running
machine and this explainer agree.

## What the numbers mean

Two anchors were set with 0.0.1: **0.x** is Tamlinux running on
[Omarchy](https://omarchy.com) plus Fred's patches and `fred.*` plugins, and
**1.x** means the Omarchy and Hyprland dependencies are gone. The steps in
between were set on 2026-10-03. On 2026-10-04 the order changed: Omarchy is
removed at **0.3** while Hyprland keeps running, so from 0.3 on, Tamlinux runs
on Hyprland without Omarchy, and 1.0.0 removes Hyprland. A minor version is a
milestone Fred accepts into daily use on his workstation, not a merged
development candidate. On 2026-10-04 the road to 0.1 was split into smaller
0.0.x steps, so that progress toward the first minor shows in the number.

| Version | Milestone | Base | Desktop |
| :-- | :-- | :-- | :-- |
| **0.0.1** | The first workstation snapshot: Omarchy, Fred's patches, and the released `fred.*` 1.x plugins. | Arch | Omarchy shell on Hyprland |
| **0.0.2** | Tamlinux owns the foundation: Arch's own package mirror and the stock Arch `linux` kernel, the Hyprland configuration, the shell environment, the session entry and session units, and the login screen. | Arch | Omarchy shell on Hyprland |
| **0.0.3** | The shell's session services run in the Tamlinux host beside the existing bar: notifications, on-screen display, clipboard history, the emoji and image pickers, reminders, the command menu, the desktop background, screenshots, and the polkit agent. Screen recording and text and QR-code capture use Tamlinux's own commands. Only the bar is left to replace. | Arch | Existing bar and Tamlinux services on Hyprland |
| **0.1** | The independent Tamlinux shell replaces Omarchy's bar in daily use, carrying all eight rewritten plugins. | Arch | Tamlinux shell on Hyprland |
| **0.2** | Plugins reach the compositor only through the compositor contract; the Hyprland adapter is in daily use and the Sway adapter passes its tests. | Arch | Tamlinux shell on Hyprland |
| **0.3** | Omarchy is removed; Hyprland stays. Its functions (menus, launcher, notifications, lock, idle, themes, sleep hooks, bindings) are replaced by owned code or selected third-party tools; its packages, package mirror, and kernel are removed; and the desktop carries Tamlinux's own name and look. | Arch | Tamlinux on Hyprland |
| **0.4** | The `tamlinux` workstation package exists and installs a Sway session beside the Hyprland session. | Arch | Both sessions available |
| **0.5–0.9** | Release candidates: the Sway session is the daily driver while the Hyprland session remains the fallback. | Arch | Tamlinux on Sway |
| **1.0.0** | Hyprland is removed from the workstation (Omarchy left at 0.3). The first installation of the workstation package on an existing distribution. | Arch | Tamlinux on Sway |
| **1.1** | The same package installs on a second, different distribution on another machine. | Arch + one other | Tamlinux on Sway |
| **1.2** | Void pilot: the same sources as native `xbps-src` packages on Void + runit + Btrfs + seatd, with complete recovery proved. antiX Core + runit only if Void has a showstopper. | + Void pilot | Tamlinux on Sway |
| **1.3** | Repeatable live-media base install, single-command workstation activation, and the terminal-only profile. | + Void pilot | + terminal-only |

There is no planned 2.x. Tamlinux is a temporary testbed: after its last 1.x
it freezes, and anything that follows is a separate announcement.

Plugins version separately. Each rewritten plugin becomes `fred.<id>` 2.0.0,
because it drops the Omarchy host API; the 1.x lines remain as released. The
workstation package carries the Tamlinux version and records its component
versions in its manifest.

**0.0.1** is the first workstation snapshot: this daily driver, working as
Tamlinux. Installing on a second computer comes at 1.1, after the
workstation package has replaced Omarchy on this machine.

**Patch numbers.** Before 0.1, each 0.0.x patch is a named milestone on the
way to 0.1 (the table above), and Fred accepts it the same way as a minor.
Fixes made inside a 0.0.x step do not bump the number; they ship with the
next milestone. From 0.1 on, patch bumps are for fixes within a milestone. If
the road to 0.1 needs another step, it takes the next 0.0.x number, and the
milestones after it keep their order.

Bump the product version when Fred decides Tamlinux itself changed, not on
every Home Manager switch. Write the new number in both `VERSION` files, log
it in [`CHANGELOG.md`](CHANGELOG.md), and keep the two files identical.

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
cat ~/.config/tamlinux/version           # product version (0.0.2) of the active generation
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
compatibility aliases of `$TAMLINUX_VERSION` until 0.3 removes them. They are
not a second product.
