# Tamlinux

Fred's Tamlinux is a bespoke personal Linux workstation environment aimed at
getting the best possible performance from the computing resources you already own.
It is inspired by the rolling updates of Arch Linux, AntiX Linux's commitment to
ensuring Linux runs on older hardware, the declarative reproducibility and atomic
rollbacks of Nix, and modern desktop ideas from Wayland, River, Hyprland,
Quickshell, and Omarchy.

| Property | Value |
| :-- | :-- |
| **Version** | [0.2.4](VERSION) — see [VERSIONING.md](VERSIONING.md) |
| **License** | GPL-3.0-or-later |
| **Desktop** | Hyprland + Quickshell (target: Sway + Quickshell, as one installable workstation package) |
| **Plugin suite** | [Fred's Tamlinux Plugin Suite](https://greenermoose.github.io/plugin-fred-tamlinux/) |
| **Status** | 0.2.4 — Style, fonts, keybinding viewer, night light, and the audio and Bluetooth panels run on Tamlinux; stage 0.2 continues with the remaining keys and menu entries. Not an installable image yet |

---

## What Tamlinux is

Tamlinux is a resource-efficient, high-performance workstation environment
for Linux. Its job is to get the most from hardware that already exists:
desktop systems, mini PCs, and laptops that have decades of useful life.

*Tam* can mean **tamarack**, **total addressable market**, or **the absolute
max**. Like the tamarack's needles, Tamlinux sheds old packages to make room
for new. In the transitional phase, we are moving from Omarchy toward an
installation package that turns an existing Linux distribution into a lean,
high-efficiency workstation environment, and then ultimately a system grafted
onto a minimal Void base, with antiX Core as the fallback if Void has a
showstopper. The aim is a sustainable workstation environment that runs well
on a wide variety of hardware.

Simplifying and minimizing resource use is not merely an accommodation for
older computers: it is a virtue. Removing bloat, resident daemons, and polling
loops allows Linux to run faster and use less energy on modern hardware, too.
On older hardware, it keeps viable machines in service; on modern hardware, it
unlocks blistering speed, cooler operation, and lower energy consumption.

Arch's rolling updates, AntiX's non-systemd efficiency and hardware longevity,
and Nix's atomic package rollbacks are core technical inspirations. Wayland
and Quickshell power the desktop. The target is a tiling window system
inspired by the UI Omarchy provides, built on Sway and Void Linux.

This repository is a public explainer, not an ISO, installer, or package
repository yet.

## Current base

Tamlinux 0.0 through 0.6 is built on Omarchy, plus Fred's patches and plugins.
We are porting some Omarchy code piece by piece, while Hyprland keeps running
and the machine stays in daily use. Once we have ported over all the Omarchy
code, then the roadmap continues in two moves:

1. **A workstation package for existing distributions.** Sway, the
   independent Quickshell shell, the rewritten `fred.*` plugins, selected
   third-party tools, and the `tamlinux` command, delivered as a Nix flake
   with a small native host adapter. Fred's Arch workstation installs it,
   then removes Hyprland: that is **Tamlinux 1.0.0**.
2. **A minimal base for the same package.** **Void Linux with runit, seatd,
   Wayland, Sway, and Btrfs**, with the package built from the same sources as
   native `xbps-src` packages. If Void has a showstopper, we will try
   **antiX Linux Core with runit**. Compare musl and glibc. See the
   [base operating system plan](docs/plans/base-operating-system.md).

0.0.1 was the first workstation snapshot.
0.0.2 (2026-10-04) owns the foundation: Arch's own package mirror and stock
kernel, the Hyprland configuration, the shell environment, and the session
entry and login screen.
Since then every step Fred accepts is a version: 0.1.0–0.1.23 moved the
desktop's session services into the Tamlinux shell, and 0.2.0 froze
Omarchy's packages. 0.2.1 moves Style and font controls onto the Tamlinux
shell, 0.2.2 adds its keybinding viewer, 0.2.3 owns the night light, and 0.2.4 adds the audio and Bluetooth panels. The stages and their
rules are in [`VERSIONING.md`](VERSIONING.md).

The [development plans](docs/plans/README.md) track the reviewed installation
direction and the approved first slice of the `tamlinux` command. Neither is
part of the installation yet.

## Targets

Set on 2026-10-03 for Tamlinux:

- **Hardware from circa 2006 onward.** Computers up to about 20 years old are
  in scope; older ones are not. That floor is what makes Wayland, rather than
  X11, a realistic display stack.
- **Void Linux first; antiX Core fallback.** Try Void as the base distribution.
  If it has a showstopper, try antiX Core. Btrfs is the preferred pilot filesystem.
- **Sway plus seatd.** Provide a keyboard-driven tiling Wayland desktop inspired
  by the UI Omarchy provides. Sway remains the selected compositor after the
  [field survey](upstream/2026-10-03-compositor.md); test its rendering paths
  on the oldest supported graphics hardware.
- **runit for init and service supervision.** The target workstation uses runit
  for PID 1 and native services, without systemd.
- **One workstation package, two deliveries.** On existing distributions,
  a Nix flake with a Home Manager module and a small native host adapter; on
  Void, native `xbps-src` packages built from the same sources.
- **Tracked packages and complete recovery.** Btrfs checkpoints of the system
  and package database, paired with the boot artifacts, on the Void base.
- **musl versus glibc.** Compare full workloads and compatibility requirements;
  lower disk/memory use and better security are hypotheses to test.
- **Chrome and VS Code run.** Both ship only 64-bit x86 (and ARM) Linux
  builds.
- **Terminal-only machines.** Three kinds of machine get a terminal-only
  system without Chrome or VS Code: 32-bit machines, very old machines without
  the graphics drivers Wayland needs, and machines with too little memory to
  compile code or run Chrome and Nix comfortably.
- **Terminal first.** Most things can be done from a terminal with a keyboard,
  starting with the console on a fresh minimal Void install. Graphical menus and
  bar widgets call the same commands.

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
