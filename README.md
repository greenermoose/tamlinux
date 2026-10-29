# Tamlinux

Tamlinux is an ergonomic, well-appointed, super-efficient workstation environment
for Linux, developed by Fred Horch for his personal and professional work. The goal
is to provide the best possible user experience on any hardware. It is a continuing
project, developed first on Fred's own machines, inspired by the rolling updates of
Arch Linux, AntiX Linux's commitment to ensuring Linux runs on older hardware, the
declarative reproducibility and atomic rollbacks of Nix, and modern desktop ideas
from Wayland, River, Hyprland, Quickshell, and Omarchy.

| Property | Value |
| :-- | :-- |
| **Version** | See [VERSION](VERSION), the [changelog](CHANGELOG.md) and [Releases](https://github.com/greenermoose/tamlinux/releases); [VERSIONING.md](VERSIONING.md) explains the numbers |
| **License** | GPL-3.0-or-later |
| **Desktop** | Hyprland + Quickshell (target: Sway + Quickshell, as one installable workstation package) |
| **Plugin suite** | [Fred's Tamlinux Plugin Suite](https://greenermoose.github.io/plugin-fred-tamlinux/) |
| **Status** | Developed in public and used daily on the developer's workstation. Not an installable image yet |

---

## What Tamlinux is

Tamlinux is a resource-efficient, high-performance, AI-ready user interface
for computers running Linux. Its goal is a responsive, reliable, accessible
daily experience that gets the most from desktop systems, mini PCs, and
laptops that can be kept in delightful, productive use for decades.

On the current Arch-based installation, Arch Linux is the operating system,
while Tamlinux is the installed workstation environment on top of it.
Blue Sparkler is the cultivar name for Tamlinux 0.5: a name for that
version of the environment, not a separate operating system.

*Tam* can mean **tamarack**, **total addressable market**, **the absolute
max**, or **teaching and making**. Like the tamarack's needles, Tamlinux sheds old
packages to make room for new so the project can continually improve. We are moving
from Omarchy toward an installation package that turns an existing Linux distribution
into a lean, ergonomic workstation environment, and then ultimately a package
("cultivar") grafted onto a minimal Void base ("root-stock"), with antiX Core as the
fallback if Void has a showstopper. The aim is a sustainable, feature-complete
workstation environment that runs well on a wide variety of hardware.

Simplifying and minimizing resource use not merely accommodates older computers:
it is a virtue. Removing bloat, resident daemons, and polling loops allows Linux
to run faster and use less power on modern hardware, too.  On older hardware, it
keeps machines in service; on modern hardware, it unlocks blistering speed,
cooler operation, and lower resource consumption to extend the life of components
with finite cycle counts, such as battery cells and non-volatile memory chips.

Arch's rolling updates, AntiX's non-systemd efficiency and hardware longevity,
and Nix's atomic package rollbacks are core technical inspirations. Wayland
and Quickshell power the desktop. The target is a tiling window system
inspired by the UI Omarchy provides, built on Sway and Void Linux.

This repository is a public explainer, not an ISO, installer, or package
repository yet.

## Current base and next steps

The workstation runs Tamlinux's packaged Quickshell shell and eight 2.x
plugins on Arch/Hyprland. The current version and its changes are in
[VERSION](VERSION) and the [changelog](CHANGELOG.md).

1. **0.4.3–0.4.5: leave Omarchy (Gate A).** 0.4.3 proved the desktop on a
   clean Arch/Hyprland host. 0.4.4 cuts this workstation over to Tamlinux's
   own login, boot, update, recovery and sleep handling, with Omarchy's
   packages still installed as the fallback. 0.4.5 replaces the last Omarchy
   calls and removes those packages; its release completes Gate A.
2. **0.5: input and appearance.** Focused input usability starts at 0.5.0;
   Tamarack visual redesign follows in later 0.5.x steps.
3. **0.6: dependable baseline.** Fix the GPU-resume and hibernation faults or
   accept mitigations, pin carried patches with upstream status, establish
   routine updates/rollback, and run a host-safe Arch install on a second laptop.
   Laptop installation may start after the 0.4.4 Run.
4. **0.7–1.0: Sway.** Complete compositor integration and install the package
   beside the dependable Hyprland fallback (0.7). Prove physical daily parity
   (0.8), then remove Hyprland (1.0).
5. **1.1–1.3: other distributions and a minimal base.** Verify a different
   distribution, then Void + runit + seatd + Btrfs and native `xbps-src` source
   delivery; compare musl/glibc. antiX Core/runit is the fallback for a Void
   showstopper. Repeatable installation and terminal-only profiles follow.

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
thermals, extended battery runtimes, and longer component life. We borrow the
rolling update philosophy from Arch Linux so that systems remain continuously
maintained and fresh without disruptive whole-OS re-install cycles, alongside
AntiX Linux's dedicated focus on running efficiently on older hardware without
systemd overhead.

A single desktop across a personal fleet — same keybindings, same package
habits, same shell — removes the maintenance tax of fragmented, end-of-life
operating systems. System efficiency is a design brief, not a review
afterthought: no polling loops, no resident daemons, no chores that need
babysitting.

When a machine becomes unusable, most operating systems cannot tell hardware
failure from software rot. Tamlinux allows introspection: the software can
help diagnose and repair itself.

## Values

- **Hardware longevity & broad compatibility.** Keep existing computers useful
  for longer, running across a wide variety of hardware.
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

Tamlinux's desktop is Hyprland and Quickshell. The `fred.*` plugin suite is
owned here, one directory per plugin under
[`desktop/plugins/`](desktop/plugins/README.md), hosted by the shell in
[`desktop/shell/`](desktop/README.md). History, releases, and development
branches from the earlier independent repositories are preserved as
namespaced `fred.<name>/` refs in this repository.

| Plugin | Source |
| :-- | :-- |
| `fred.workspaces` | [`desktop/plugins/fred.workspaces/`](desktop/plugins/fred.workspaces) |
| `fred.clock` | [`desktop/plugins/fred.clock/`](desktop/plugins/fred.clock) |
| `fred.keyboard` | [`desktop/plugins/fred.keyboard/`](desktop/plugins/fred.keyboard) |
| `fred.sysinfo` | [`desktop/plugins/fred.sysinfo/`](desktop/plugins/fred.sysinfo) |
| `fred.tides` | [`desktop/plugins/fred.tides/`](desktop/plugins/fred.tides) |
| `fred.weather` | [`desktop/plugins/fred.weather/`](desktop/plugins/fred.weather) |
| `fred.monitor` | [`desktop/plugins/fred.monitor/`](desktop/plugins/fred.monitor) |
| `fred.agents` | [`desktop/plugins/fred.agents/`](desktop/plugins/fred.agents) |

The independent `greenermoose/*-fred-tamlinux` plugin repositories are
frozen; their released 1.x Omarchy versions and full history remain there
for reference. The manager CLI is
[`tam-plugin`](https://github.com/greenermoose/plugin-fred-tamlinux).
Carried third-party patches are recorded in
[`ecosystem-fred-tamlinux`](https://github.com/greenermoose/ecosystem-fred-tamlinux).

## License

Tamlinux and its plugins are developed under the GNU General Public License
version 3 or later. See [`LICENSE`](LICENSE).

## AI collaboration

Session prompts, tool versions, and architectural notes are in
[`AI_PROVENANCE.md`](AI_PROVENANCE.md).
