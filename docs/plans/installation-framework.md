# Installation framework

**Status:** Initial direction reviewed positively by Fred on 2026-09-23;
second-computer and disk choices remain open. No installer has been implemented.

## Goal

Make a fresh computer reproducibly become Tamlinux without copying the state of
one workstation. The first milestone is an installation framework that can say
what it would change, apply the Tamlinux layer, and report what succeeded. A
bootable image and disk installer come after that framework works on a second
computer.

## Recommended base sequence

1. **Transitional base: Omarchy (0.x).** The existing workstation already
   runs it. Use it as a top-down decoupling testbed: cataloging Omarchy and
   Hyprland dependencies, isolating `fred.*` plugins, and extracting user
   configurations, commands, and documentation.
2. **Target Base Layer: antiX Linux Core + `seatd` + Wayland + River (under Nix).**
   - **antiX Linux Core:** Based directly on Debian stable without `systemd`.
     Boots to a clean terminal with network access in under 100 MB RAM,
     leaving maximum resources available for user workflows and local AI.
     Its mature live-USB system enables rapid deployment (e.g. at Maker Fests).
   - **`seatd`:** Minimal seat/session management without `systemd-logind` or `elogind`.
   - **Hardened River:** Lean Zig-based Wayland dynamic tiling compositor.
     Hardened by strictly separating user declarative configuration files
     from root-owned system scripting and compositor plumbing.
   - **Nix determinism & rollbacks:** Deployed on top of antiX Core as the
     package and environment manager, providing atomic generations and instant
     rollback to previous known-good states.
3. **Graduation to Suspra Linux & Tier 3 Suspra Workstations:** Once the system
   runs cleanly on the AntiX Linux base layer, Tamlinux completes its transitional
   purpose and launches as **Suspra Linux**, the operating system powering the
   Tier 3 Suspra Workstation designed to run across a wide variety of hardware
   (from revived legacy computers to modern high-performance machines).

## Layers and ownership

```text
Application & Environment Layer (Tamlinux/Suspra user environment, fred.* plugins, AI harnesses)
  -> user profile, commands, local knowledge, shell
Packaging & Rollback Layer (Nix standalone)
  -> pinned flakes, deterministic packages, atomic generations, rollbacks
Windowing & Compositor Layer (Hardened River + seatd)
  -> user declarative configs, root-owned compositor plumbing, Wayland IPC
Base OS Host (Omarchy 0.x transitional; target antiX Linux Core)
  -> Debian stable package pool, sysvinit/runit (no systemd), tuned kernel, boot
Host profile
  -> hardware-specific settings and explicitly local state
```

The install source must state which layer owns every setting. A host profile
contains only values needed for that machine; secrets and observed machine
state stay outside the public install source. Third-party components retain
their own repositories and licenses. The installation manifest pins or records
their source versions, so a result can be reconstructed.

The current `fred.*` widgets use Omarchy's Quickshell `qs.Commons`, `qs.Ui`,
and plugin loader. An independent base needs Tamlinux-owned equivalents before
those widgets can be considered portable. This decoupling is an explicit milestone
of the AntiX Linux base layer path.

## Proposed repository shape

This is the initial target structure, subject to review. The first implementation
should be small and should reuse existing maintained sources rather than copy
their contents into this repository.

```text
tamlinux/
  bin/tamlinux                 # command entry point
  installer/                   # inspect, plan, apply, verify orchestration
  profiles/omarchy/            # transitional base adapter (0.x)
  profiles/antix/              # target antiX Core base adapter
  manifests/                   # component sources and pinned versions
  knowledge/                   # offline command and onboarding content
  docs/plans/                  # decisions, milestones, and evidence
```

The public manifest should describe the product components. Local machine
configuration is supplied separately at install time. The installer must not
assume every machine has the same monitors, storage layout, or credentials.

## Installation contract

The first command surface is `tamlinux install`:

- `tamlinux install inspect` reports the OS, architecture, current Tamlinux
  version, available package tools, and the profile it can use.
- `tamlinux install plan --profile <profile>` prints the exact intended changes,
  required inputs, source revisions, privileges, and a rollback route. It makes
  no changes.
- `tamlinux install apply --profile <profile>` performs only the reviewed plan,
  with clear checkpoints and a recorded result. A mismatched or stale plan
  requires a new review.
- `tamlinux install verify` checks the installed components, versions, command
  resolution, desktop integration, and any failed or skipped steps.

Use structured step results so the framework can transition from the Omarchy
profile to the antiX Core adapter. Each step declares its prerequisites, owner,
expected state, action, and verification. Re-running an already satisfied step
must be safe. A failure stops before later dependent steps and tells the
operator how to recover.
The framework must never partition a disk or switch the active OS as a hidden
side effect of `apply`.

For 0.x, system packages remain native host packages; user tools can remain
under Home Manager or Mise according to their declared owner. For the antiX
target, the host is antiX Core, while desktop tools and user applications
are managed deterministically via Nix flakes with instant rollback.

## Milestones

| Milestone | Deliverable | Evidence to record here |
| :-- | :-- | :-- |
| A. Inventory | Component/owner manifest for current 0.0.1 workstation; catalog Omarchy/Hyprland dependencies. | Source revision and classification of each component. |
| B. Framework | `inspect`, read-only `plan`, bounded `apply`, and `verify` for the Omarchy profile. | Plan output, applied steps, versions, and recovery path. |
| C. Decoupling Pilot | Test antiX Linux Core + `seatd` + River baseline on a secondary computer. | Installation transcript, boot time, memory footprint (<100MB). |
| D. AntiX Base Layer | Deploy Nix flakes, River hardening, and ported `fred.*` plugins on antiX Core. | River session, declarative configs, Nix atomic generations and rollback. |
| E. Graduation to Suspra Workstation | Transition Tamlinux to Suspra Linux; package Tier 3 Suspra Workstation. | Turnkey USB installer (Maker Fest model), single-command setup, multi-hardware verification. |

The daily workstation remains on its working installation while C–D are
developed and checked on a separate computer. A product version changes only
when a reviewed product snapshot is ready; installer iterations do not equal
Home Manager generations.

## Review record and remaining decisions

- **2026-09-23:** Fred reviewed this framework and approved the installation
  contract and general command structure.
- **2026-09-28:** Fred refined the base layer strategy to **antiX Linux Core +
  `seatd` + Wayland + River**, with Nix for package determinism and atomic
  rollbacks. Clarified the vision: Tamlinux works from Omarchy toward this AntiX
  Linux base layer, at which point it launches as **Suspra Linux** to build the
  Tier 3 Suspra Workstation for diverse hardware.
- **Open:** Choose the secondary machine for the antiX Core pilot and define
  its disk boundaries before installation.

## References

- [antiX Linux](https://antixlinux.com/) — lean, systemd-free Debian-based Linux.
- [River compositor](https://github.com/riverwm/river) — dynamic tiling Wayland compositor written in Zig.
- [seatd](https://git.sr.ht/~kennylevinsen/seatd) — minimal seat management daemon.
- [NixOS manual: rolling back configuration changes](https://nixos.org/manual/nixos/stable/) — generations and rollback concepts.
- [Home Manager manual](https://nix-community.github.io/home-manager/) — managing user configuration with Nix.
