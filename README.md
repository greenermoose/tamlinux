# Tamlinux

Tamlinux is an independent workstation environment for Linux, aimed at
providing the best possible user experience on any hardware. It is a continuing
project for modern and older computers, developed first on Fred's own machines.
It is inspired by the rolling updates of Arch Linux, AntiX Linux's commitment to
ensuring Linux runs on older hardware, the declarative reproducibility and atomic
rollbacks of Nix, and modern desktop ideas from Wayland, River, Hyprland,
Quickshell, and Omarchy.

| Property | Value |
| :-- | :-- |
| **Version** | [0.4.0](VERSION) — see [VERSIONING.md](VERSIONING.md) |
| **License** | GPL-3.0-or-later |
| **Desktop** | Hyprland + Quickshell (target: Sway + Quickshell, as one installable workstation package) |
| **Plugin suite** | [Fred's Tamlinux Plugin Suite](https://greenermoose.github.io/plugin-fred-tamlinux/) |
| **Status** | 0.4.0 — Non-theme settings/state/cache and shared key/bar helper accepted on 2026-10-08. The pinned Tamlinux shell and eight exercised 2.x plugins run normally on every screen. Menu/theme/package independence remains in progress. Not an installable image yet |

---

## What Tamlinux is

Tamlinux is a resource-efficient, high-performance workstation environment
for Linux. Its purpose is a responsive, reliable, accessible daily experience
that gets the most from hardware that already exists:
desktop systems, mini PCs, and laptops that have decades of useful life.

*Tam* can mean **tamarack**, **total addressable market**, or **the absolute
max**. Like the tamarack's needles, Tamlinux sheds old packages to make room
for new while the project continues improving. We are moving from Omarchy toward an
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

## Current base and next steps

The current workstation runs Tamlinux's deployed Quickshell shell and eight
2.x plugins on Arch/Hyprland. Step 0.4.0 is accepted; non-theme user storage
and the shared key/bar helper are owned. Next is 0.4.1 compositor protocol
shadow testing, followed by menu cleanup. The remaining Omarchy
dependencies are removed while retaining the working Hyprland desktop:

1. **0.4: settings/state and menus.** Own user data, caches, helper entry points
   and menu extensions, keeping keys and bar actions consistent.
2. **0.5: theme system, fonts and identity.** One validated source generates
   supported app themes; independently owned fonts/glyphs and Tamlinux surfaces.
3. **0.6: packages/system ownership and final removal.** Preserve current
   effective settings and workflows; remove remaining components after the
   independent boot/update/recovery path is verified. Accept Tamlinux on
   Hyprland without Omarchy.
4. **0.7–1.0: Sway.** Complete compositor integration and install the Nix
   workstation package with a native Arch host adapter beside the accepted
   Hyprland fallback (0.7). Prove physical daily parity (0.8), then remove
   Hyprland (1.0). The package includes the planned `tam` terminal command.
5. **1.1–1.3: other hosts and a minimal base.** Verify another distribution,
   then Void + runit + seatd + Btrfs and native `xbps-src` source delivery;
   compare musl/glibc. antiX Core/runit is the fallback for a Void showstopper.
   Repeatable installation and terminal-only profiles follow evidence.

These are two separate desktop proofs. Prepared Sway adapters are retained;
they do not move Sway integration ahead of accepted independence on Hyprland.
The [development plans](docs/plans/README.md) carry detailed acceptance and
recovery. Planning changes do not bump [VERSION](VERSION) or install components.

## Targets

Engineering targets set on 2026-10-03; project identity and hardware scope
updated on 2026-10-06:

- **Best possible experience on any hardware.** Broad hardware support is the
  goal; actual supported architectures, drivers, and workloads require testing.
  Circa-2006 machines remain useful validation examples. Select a graphical or
  terminal profile by capability rather than excluding a machine by age alone.
- **Void Linux first; antiX Core fallback.** Try Void as the base distribution.
  If it has a showstopper, try antiX Core. Btrfs is the preferred pilot filesystem.
- **Sway plus seatd.** Provide a keyboard-driven tiling Wayland desktop inspired
  by the UI Omarchy provides. Sway remains the selected compositor after the
  [field survey](upstream/2026-10-03-compositor.md); test its rendering paths
  on representative older graphics hardware.
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
- **User experience.** Responsive, reliable, accessible tools and a coherent
  daily workflow on each supported hardware profile.
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
