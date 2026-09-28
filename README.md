# Tamlinux

Fred's Tamlinux is a bespoke personal Linux distribution aimed at getting the best
possible performance from the computing resources you already own. It is
inspired by the rolling updates of Arch Linux, AntiX Linux's commitment to
ensuring Linux runs on older hardware, the declarative reproducibility and atomic
rollbacks of Nix, and modern desktop ideas from Wayland, River, Hyprland,
Quickshell, and Omarchy.

| Property | Value |
| :-- | :-- |
| **Version** | [0.0.1](VERSION) — see [VERSIONING.md](VERSIONING.md) |
| **License** | GPL-3.0-or-later |
| **Desktop** | Hyprland + Quickshell (River target) |
| **Plugin suite** | [Fred's Tamlinux Plugin Suite](https://greenermoose.github.io/plugin-fred-tamlinux/) |
| **Status** | 0.0.1 — first workstation snapshot; not an installable image yet |

---

## What Tamlinux is

Tamlinux is Fred's personal Linux distribution. Its job is to get the most
from hardware that already exists: workstations, mini PCs, and older laptops
that still have years of useful silicon left.

*Tam* can mean **tamarack**, **total addressable market**, or **the absolute
max**. Like the tamarack's needles, Tamlinux is meant to be temporary. Its
vision is to work from Omarchy toward a lean Linux system running on an AntiX
Linux base layer, at which point it will launch as Suspra Linux and begin
building the Tier 3 Suspra Workstation—a sustainable, high-efficiency operating
system and workstation environment envisioned to run on a wide variety of
hardware.

Simplifying and minimizing resource use is not merely an accommodation for
older computers: it is a universal virtue. Removing bloat, resident daemons,
and polling loops allows Linux to run faster and use less energy on modern
hardware, too. On older hardware, it keeps viable machines in service; on modern
hardware, it unlocks blistering speed, cooler operation, and lower energy
consumption.

It is a Wayland-based system. Arch's rolling updates, AntiX's non-systemd
efficiency and hardware longevity, and Nix's atomic package rollbacks are core
technical inspirations. Hyprland and Quickshell power the initial desktop, with
River identified as the target compositor. The `fred.*` plugin IDs stay `fred.*`.

This repository is the public explainer. It is not an ISO, installer, or
package repository yet.

## Current base

Tamlinux 0.x is built on Omarchy, plus Fred's patches and the `fred.*`
plugins. The roadmap is to decouple top-down from Omarchy toward an AntiX Linux
base layer (antiX Core + `seatd` + Wayland + River, with Nix for deterministic
package sets and rollbacks). Once this AntiX-based foundation is achieved,
Tamlinux graduates to Suspra Linux, powering the Tier 3 Suspra Workstation.

0.0.1 is the first workstation snapshot. An installer for a second computer
comes after this workstation is solid. Version rules are in
[`VERSIONING.md`](VERSIONING.md).

The [development plans](docs/plans/README.md) track the reviewed installation
direction and the approved first slice of the `tamlinux` command. Neither is
part of the 0.0.1 installation yet.

## Why

Software gets bloated, abandoned, and insecure long before physical hardware
fails. Reviving aging machines with a lightweight, efficient Linux keeps
viable silicon in service, cuts electronic waste, and makes a day's work
faster on the computer you already have.

At the same time, simplifying and minimizing resource consumption delivers
immediate gains on modern hardware: lower energy use, cooler and quieter
thermals, extended battery runtimes, and reduced idle draw. We borrow the
rolling update philosophy from Arch Linux so that systems remain continuously
maintained and fresh without disruptive whole-OS re-install cycles, alongside
AntiX Linux's dedicated focus on running efficiently on older hardware without
systemd overhead.

A single desktop across a personal fleet — same keybindings, same package
habits, same shell — removes the maintenance tax of fragmented, end-of-life
operating systems. Energy efficiency is a design brief, not a review
afterthought: no polling loops, no resident daemons, no chores that need
babysitting.

When a machine becomes unusable, most operating systems cannot tell hardware
failure from software rot. Tamlinux aims for introspection: the desktop
should help diagnose and repair itself.

## Values

- **Hardware longevity & broad compatibility.** Keep existing computers useful
  and secure, running across a wide variety of hardware.
- **Resource minimization & energy efficiency.** Simplifying and minimizing
  resource use makes modern hardware run faster and cooler while extending the
  life of older devices. Event-driven, bounded, self-reporting work with no
  polling loops.
- **Continuous rolling maintenance.** Keep systems current and sustainable
  through rolling updates, avoiding destructive full-system upgrade cycles.
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
