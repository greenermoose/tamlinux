# Tamlinux versioning

Tamlinux uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The published number is the file [`VERSION`](VERSION) in this repository.
The private workstation checkout keeps a matching `VERSION` so the running
machine and this explainer agree.

## What the numbers mean

Two anchors were set with 0.0.1: **0.x** is Tamlinux running on
[Omarchy](https://omarchy.com) plus Fred's patches and `fred.*` plugins, and
**1.x** means the Omarchy and Hyprland dependencies are gone. The steps in
between were set on 2026-10-03. A minor version is a milestone Fred accepts
into daily use on his workstation, not a merged development candidate.

| Version | Milestone | Base | Desktop |
| :-- | :-- | :-- | :-- |
| **0.0.x** | Today's workstation snapshot: Omarchy, Fred's patches, and the released `fred.*` 1.x plugins. Patch bumps for fixes only. | Arch | Omarchy shell on Hyprland |
| **0.1** | The independent Tamlinux shell replaces Omarchy's bar in daily use, carrying all eight rewritten plugins. | Arch | Tamlinux shell on Hyprland |
| **0.2** | Plugins reach the compositor only through the compositor contract; the Hyprland adapter is in daily use and the Sway adapter passes its tests. | Arch | Tamlinux shell on Hyprland |
| **0.3** | The remaining Omarchy functions (menus, launcher, notifications, lock, idle, themes, sleep hooks, bindings) are replaced by owned code or selected third-party tools. | Arch | Tamlinux shell on Hyprland |
| **0.4** | The `tamlinux` workstation package exists and installs a Sway session beside the Omarchy session. | Arch | Both sessions available |
| **0.5–0.9** | Release candidates: the Sway session is the daily driver while Omarchy remains the fallback session. | Arch | Tamlinux on Sway |
| **1.0.0** | Omarchy and Hyprland are removed from the workstation. The first installation of the workstation package on an existing distribution. | Arch | Tamlinux on Sway |
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
echo "$TAMLINUX_VERSION"                 # product version (0.0.1)
cat ~/.config/tamlinux/version           # same number
cat ~/.config/tamlinux/generation        # this machine's Home Manager generation
home-manager generations                 # full local rollback list
```

`$OMARCHY_CONFIG_VERSION` and `~/.config/omarchy/version` remain as 0.x
compatibility aliases of `$TAMLINUX_VERSION`. They are not a second product.
