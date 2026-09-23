# Tamlinux

Fred's Tamlinux is a bespoke Linux distro aimed at getting the best possible
performance from the computing resources you already own, inspired by ideas
from Arch Linux, Nix, Wayland, Hyprland, Quickshell, and Omarchy.

| Property | Value |
| :-- | :-- |
| **License** | GPL-3.0-or-later |
| **Desktop** | Hyprland + Quickshell |
| **Plugin suite** | [Fred's Tamlinux Plugin Suite](https://greenermoose.github.io/plugin-fred-tamlinux/) |
| **Status** | First public description; not an installable image yet |

---

## What Tamlinux is

Tamlinux is Fred's personal Linux distribution. Its job is to get the most
from hardware that already exists: workstations, mini PCs, and older laptops
that still have years of useful silicon left.

*Tam* means both **tamarack** and **total addressable market**. Like the
tamarack's needles, Tamlinux is meant to be temporary. It exists to explore
what it takes to create a distribution and to widen the market for Linux.

It is a Wayland-based system. Arch and Nix are technical inspirations; the
base is not a settled implementation commitment. Hyprland and Quickshell are
the desktop. The `fred.*` plugin IDs stay `fred.*`.

This repository is the public explainer. It is not an ISO, installer, or
package repository yet.

## Why

Software gets bloated, abandoned, and insecure long before physical hardware
fails. Reviving aging machines with a lightweight, efficient Linux keeps
viable silicon in service, cuts electronic waste, and makes a day's work
faster on the computer you already have.

A single desktop across a personal fleet — same keybindings, same package
habits, same shell — removes the maintenance tax of fragmented, end-of-life
operating systems. Energy efficiency is a design brief, not a review
afterthought: no polling loops, no resident daemons, no chores that need
babysitting.

When a machine becomes unusable, most operating systems cannot tell hardware
failure from software rot. Tamlinux aims for introspection: the desktop
should help diagnose and repair itself.

## Values

- **Hardware longevity.** Keep existing computers useful and secure.
- **Energy efficiency.** Event-driven, bounded, self-reporting work.
- **Repairability.** Patches declare how they retire; nothing becomes
  permanent by neglect.
- **Fleet standardization.** One desktop on every machine Fred runs.
- **Community publishing.** The `fred.*` plugins and this description are
  public so others can learn from the work.

## Desktop shell

Tamlinux's desktop is Hyprland and Quickshell. The public plugin suite lives
at [greenermoose.github.io/plugin-fred-tamlinux](https://greenermoose.github.io/plugin-fred-tamlinux/)
and in these repositories:

| Plugin | Repository |
| :-- | :-- |
| `fred.workspaces` | [workspaces-fred-tamlinux](https://github.com/greenermoose/workspaces-fred-tamlinux) |
| `fred.clock` | [clock-fred-tamlinux](https://github.com/greenermoose/clock-fred-tamlinux) |
| `fred.keyboard` | [keyboard-fred-tamlinux](https://github.com/greenermoose/keyboard-fred-tamlinux) |
| `fred.sysinfo` | [sysinfo-fred-tamlinux](https://github.com/greenermoose/sysinfo-fred-tamlinux) |
| `fred.tides` | [tides-fred-tamlinux](https://github.com/greenermoose/tides-fred-tamlinux) |
| `fred.weather` | [weather-fred-tamlinux](https://github.com/greenermoose/weather-fred-tamlinux) |
| `fred.monitor` | [monitor-fred-tamlinux](https://github.com/greenermoose/monitor-fred-tamlinux) |
| `fred.agents` | [agents-fred-tamlinux](https://github.com/greenermoose/agents-fred-tamlinux) |

The manager CLI is [`tam-plugin`](https://github.com/greenermoose/plugin-fred-tamlinux).
Carried third-party patches are recorded in
[`ecosystem-fred-tamlinux`](https://github.com/greenermoose/ecosystem-fred-tamlinux).

## License

Tamlinux and its plugins are developed under the GNU General Public License
version 3 or later. See [`LICENSE`](LICENSE).

## AI collaboration

Session prompts, tool versions, and architectural notes are in
[`AI_PROVENANCE.md`](AI_PROVENANCE.md).
