# Survey: a tiling Wayland compositor for Tamlinux on antiX Core

**Date:** 2026-10-03.
**Requested by:** Fred ("Survey the field for a Tamlinux
compositor").
**Status:** Fred chose Sway on 2026-10-03 (see Outcome). Nothing has been
installed or implemented.

## Question

Which tiling Wayland compositor should carry the Tamlinux desktop on antiX
Linux Core (no systemd, `seatd`), given these targets:

1. Runs acceptably on hardware from circa 2006: a software renderer or
   OpenGL ES 2, because GPUs from that era offer at most OpenGL 2.1-class
   acceleration.
2. No systemd dependency; works with `seatd`/`libseat`.
3. Tiling and keyboard-driven, able to deliver a UI inspired by Omarchy:
   numbered workspaces, complete keyboard bindings, a slim bar, a launcher and
   keyboard menu, one theme everywhere.
4. Supports `wlr-layer-shell` and the other protocols a Quickshell bar needs.
5. IPC rich enough for `fred.workspaces` and the other plugins. Today they use
   Hyprland's focused monitor, monitor list, workspaces per monitor, focused
   workspace, raw events, dispatch (switch/move), and binding and device
   queries.
6. Configuration that splits into user-owned declarative settings and
   root-owned plumbing shipped with releases, so a user mistake cannot break
   the session.
7. Low idle cost, maintained, and not prone to breaking changes.

Hyprland was rejected earlier (heavy C++ dependencies, rapid breaking changes,
systemd assumptions) and is not reconsidered here.

## Method

Searched on 2026-10-03 for: compositor release notes and repositories (River,
river-classic, Sway, niri, dwl, mango); renderer and GPU requirements (wlroots
`pixman`, niri's EGL requirements, Intel GMA 950 on Wayland); Quickshell's
compositor integrations (`Quickshell.I3`, `Quickshell.WindowManager`); Debian
13 package metadata; and antiX's own `trixie` package indexes
(`repo.antixlinux.com`, `main` and `nosystemd`, amd64, index dated
2026-09-28). The antiX indexes were downloaded and searched directly.

Coverage limit: no candidate was run on 2006 hardware. Renderer and
performance statements come from documentation and reports, not measurement.
Searches stopped when new queries returned the same candidate set.

## Findings that apply to every candidate

### Old GPUs are the main risk, not the compositor

A 2015 Fedora report of GNOME on Wayland with an Intel 945GM (GMA 950) found it
unusable: a Nautilus window took 71 seconds to appear and terminal text did not
render ([Red Hat bug 1205684](https://bugzilla.redhat.com/show_bug.cgi?id=1205684)).
That was a GPU-composited desktop on a 2015 software stack, so it does not
predict how a lightweight compositor using a CPU (`pixman`) renderer performs.
It does show that the GMA 950 class is the weakest point of the 2006 floor, and
that a short measurement on that hardware should come before port work.

wlroots-based compositors can be forced onto the CPU renderer with
`WLR_RENDERER=pixman`, which needs only kernel modesetting. niri, by contrast,
requires hardware GL and rejects software EGL devices by default; an opt-in for
software EGL is proposed for VMs in
[niri PR #4614](https://github.com/niri-wm/niri/pull/4614).

### antiX packages none of the candidates, and Debian's Sway does not install cleanly there

- antiX `trixie` provides `seatd` 0.9.3, `libseat1`, and `turnstile` (a
  session tracker that can start a D-Bus user session without logind). It
  carries no compositor from this list and no `wlroots`.
- Debian 13 `sway` 1.10.1-2 depends on `libsystemd0 (>= 243)`
  ([packages.debian.org](https://packages.debian.org/trixie/sway)). antiX's
  `libsystemd0` is a transitional package for `libelogind0` at version
  `241.4+antix1`, which does not satisfy `>= 243`. antiX rebuilds many Debian
  packages without libsystemd0 in its `nosystemd` component, but not Sway.
- Debian 13 has no `river` or `niri` package (niri's IPC crate is in testing).

So the chosen compositor will be built by Tamlinux, either as a rebuilt Debian
package without libsystemd0 or through Nix. A Nix-built compositor on a non-NixOS
host needs a host-graphics bridge such as
[nixGL](https://github.com/nix-community/nixGL) for its GPU path. The `pixman`
path needs no GL driver. This is a packaging decision for the installation
framework, not a reason to prefer one compositor.

### Quickshell already has a compositor-neutral path coming

Quickshell's development branch adds a `WindowManager` module backed by the
standard `ext-workspace-v1` protocol
([docs](https://quickshell.org/docs/master/types/Quickshell.WindowManager),
[commit](https://git.outfoxxed.me/quickshell/quickshell/commit/e5376f260999a4841150e61f3cec271558846a69)).
Sway 1.12 supports `ext-workspace-v1`
([Phoronix](https://www.phoronix.com/news/wlroots-0.20-Sway-1.12-rc1)), niri
implements it, and River plans an equivalent. A compositor that speaks this
protocol lets the `fred.*` plugins use one workspace backend instead of one per
compositor.

## Candidates

### Sway: proposed

- **What it is:** an i3-compatible tiling compositor on wlroots. Sway 1.12
  (2026-05-25) uses wlroots 0.20; Debian 13 carries 1.10.1. MIT license.
  Developed steadily since 2016 with a conservative stance on breaking changes
  ([Sway 1.11 notes](https://linuxiac.com/sway-1-11-wayland-tiling-window-manager-released/)).
- **2006 floor:** wlroots GLES2 renderer, or `pixman` when forced. Strongest
  position of the candidates, still to be measured.
- **No systemd:** uses `libseat`; works with `seatd`. Debian's build links
  libsystemd0 through sd-bus for the tray, so an antiX build needs another
  sd-bus provider (`basu` or `libelogind`) or the tray disabled. Devuan users
  run Sway with `seatd` without elogind
  ([Dev1 Galaxy forum](https://dev1galaxy.org/viewtopic.php?id=5979)).
- **Omarchy-style UI:** numbered workspaces and `$mod+N` bindings are native,
  and the i3 binding model maps closely onto Omarchy's `SUPER` bindings. Floating
  and scratchpad support covers launcher and menu windows.
- **Quickshell and plugins:** a released `Quickshell.I3` module covers i3 and
  Sway IPC: workspaces, monitors, the focused monitor, `monitorFor(screen)`,
  `dispatch()`, and raw events
  ([docs](https://quickshell.org/docs/types/Quickshell.I3/I3)). That matches
  most of what `fred.workspaces` takes from `Quickshell.Hyprland` today.
  `swaymsg -t get_inputs` and `get_outputs` cover the `hyprctl` device and
  monitor queries. Sway has no binding-list query; `get_config` returns the
  loaded configuration, so `fred.keyboard` would read bindings from the
  generated configuration instead. `ext-workspace-v1` is also
  available.
- **Hardening:** the configuration is declarative, with `include` directives
  and a `sway --validate` check. A root-owned `/etc/sway/config` can hold
  plumbing and include a user-owned, generated fragment that is validated before
  it is applied. `exec` lines are still possible, so the user layer should be
  generated from a smaller declarative file rather than handed over raw.
- **Idle cost:** event-driven with no animations by default.
- **Relationship:** general inspiration and a packaged dependency; no code
  copied.

### River 0.4 plus a window manager: deferred

- **What it is:** since 0.4 (2026-03-16), River is a compositor only. Window
  management runs as a separate process speaking
  `river-window-management-v1`
  ([linuxiac](https://linuxiac.com/river-0-4-wayland-compositor-debuts-pluggable-window-managers/),
  [repository](https://codeberg.org/river/river)). Built with Zig 0.16 and
  wlroots 0.20. GPL-3.0-only. Window managers are young (for example kwm, Rill,
  Canoe, Beansprout).
- **Strengths:** a wlroots base with a `pixman` path, and a clean boundary
  that would let Tamlinux write its own window manager and own the
  Omarchy-style policy outright. That is the ultimate form of the
  user/system split.
- **Why deferred:** bars cannot yet get workspace state from River itself; an
  `ext-workspace` equivalent is planned. Writing and maintaining a window
  manager is a large project, and the WM ecosystem is months old. Revisit once
  River ships its workspace protocol, or if Fred decides Tamlinux should own its
  window manager.

### river-classic: deferred

- **What it is:** a maintained fork of River 0.3, with dynamic tiling, tags,
  `riverctl`, and the `river-status` protocol that Waybar reads
  ([ArchWiki](https://wiki.archlinux.org/title/River_Classic)).
- **Why deferred:** its configuration is an executable `init` script, the
  footgun D25 was written to remove. Its future depends on a fork of a
  superseded design, and there is no Quickshell integration. It is the closest
  match to the 2026-09-28 plan, but no longer a better fit than Sway.

### mango (mangowc): deferred

- **What it is:** a dwl-derived wlroots compositor with a config file, many
  layouts (scroller, master-stack, monocle), Hyprland-like animations, and
  `dwl-ipc-unstable-v2` IPC through the `mmsg` client
  ([repository](https://github.com/DreamMaoMao/mangowc),
  [IPC reference](https://www.mintlify.com/mangowm/mango/reference/ipc-overview)).
  Version 0.16.0. GPL-3.0.
- **Why deferred:** the most Omarchy-like look of the candidates, but young and
  driven by a small group, its IPC is a dwl-specific unstable protocol, and its
  animations cost CPU on a `pixman` renderer. Watch it as a source of design
  ideas.

### dwl: rejected for now

- **What it is:** a dwm-like wlroots compositor configured by editing
  `config.h` and recompiling. v0.8 builds on wlroots 0.19; lead maintainership
  changed hands recently ([releases](https://codeberg.org/dwl/dwl/releases)).
- **Why rejected:** compile-time configuration gives no user-declarative layer,
  and its IPC exists only as an out-of-tree patch. Very light, so it could serve
  as a fallback for the very weakest machines if Sway fails there.

### niri: rejected

- **What it is:** a scrollable-tiling compositor on Smithay (Rust), GPL-3.0,
  with rich JSON IPC and `ext-workspace-v1`.
- **Why rejected:** it requires hardware GL and rejects software rendering by
  default, which fails the 2006 floor. Its scrolling model departs from
  Omarchy's numbered workspaces, and it is not packaged in Debian 13.

### Not assessed in depth

labwc (stacking, not tiling); Wayfire (stacking-first, tiling by plugin);
Qtile on Wayland (Python, heavier runtime); full desktops such as GNOME, KDE
Plasma, and COSMIC (well above the resource budget and oriented toward logind
sessions); SwayFX and other effects forks (GPU effects work against the 2006
floor).

## Comparison

| Criterion | Sway | River 0.4 + WM | river-classic | mango | dwl | niri |
|---|---|---|---|---|---|---|
| 1. 2006 GPUs (pixman/GLES2) | Yes (wlroots) | Yes (wlroots) | Yes (wlroots) | Yes (wlroots) | Yes (wlroots) | No (hardware GL) |
| 2. seatd, no systemd | Yes; rebuild without libsystemd0 | Likely; build ourselves | Likely; build ourselves | Likely; build ourselves | Yes | Yes (libseat) |
| 3. Omarchy-style tiling | Strong (numbered workspaces) | Depends on WM | Tags | Strong | Tags | Scrolling |
| 4. Layer shell | Yes | Yes | Yes | Yes | Yes | Yes |
| 5. IPC for plugins | i3 IPC + `Quickshell.I3` + ext-workspace | Pending | river-status | dwl-ipc-v2 | Patch | JSON + ext-workspace |
| 6. User/system config split | `include` + `--validate` | Own WM | Executable init | Config file | Compile-time | Config file |
| 7. Maturity, idle cost | Mature, low | New | Fork, low | Young, animations | Light, minimal | Mature, animations |

## Recommendation

**Proposed: adopt Sway as the pilot compositor**, with three conditions:

1. **Measure before porting.** On an x86-64 machine near the floor, ideally
   with GMA 950- or X3100-class graphics, run Sway with both its GLES2 and
   `pixman` renderers. Record idle CPU and power, frame responsiveness, a
   Quickshell bar using Qt Quick's software backend, `foot`, Chrome, and VS
   Code. If Sway is unusable there, the floor's graphics assumption needs
   revisiting before any compositor choice matters.
2. **Target `ext-workspace-v1` first and `Quickshell.I3` second** in the
   compositor-neutral plugin backend, so that River or another compositor can
   be swapped in later without rewriting the plugins.
3. **Build Sway for antiX without libsystemd0**, as a rebuilt Debian package or
   through Nix, as a choice for the installation framework.

**Deferred:** River 0.4 with a Tamlinux-owned window manager (revisit when
River's workspace protocol ships or if owning the window manager becomes a
goal), river-classic, and mango.

**Rejected for now:** niri (fails the 2006 floor) and dwl (no declarative user
layer). dwl stays a possible fallback for the weakest machines.

**Doing nothing** is reasonable until the floor measurement is made, because
the shell foundation and compositor-neutral backends do not depend on this
choice.

## Outcome

**2026-10-03: Sway chosen.** Fred decided that Tamlinux builds Sway itself and
manages it with Nix, as part of a Nix-built workstation package. That package
installs on antiX Linux Core, or directly on a machine that already runs
Linux. The three conditions above carry forward into the pilot. Building with
Nix settles condition 3. River 0.4, river-classic, and mango stay deferred;
niri and dwl stay rejected for now. Design points for the package are in the
[installation framework](../docs/plans/installation-framework.md).
