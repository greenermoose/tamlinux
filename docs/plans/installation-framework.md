# Installation framework

**Project scope (2026-10-06):** Tamlinux is an independent, continuing Linux
workstation environment aimed at the best possible user experience on any
hardware. The workstation package remains `tamlinux`; the terminal command is `tam`
(named 2026-10-07). Existing-distribution
Nix delivery and native Void packaging are Tamlinux engineering work. Hardware
profiles are capability-based; circa-2006 machines are validation examples,
not a universal age cutoff.

**Status:** Installation contract approved on 2026-09-23; target updated on
2026-10-03 to Void first, antiX Core fallback; route updated on 2026-10-03 to
install the workstation package on existing distributions first. No installer
has been implemented. Pilot machine and disk boundaries remain open.

## Goal

Make a computer reproducibly become Tamlinux without copying one
workstation's state. First implement inspect, plan, apply, and verify for the
workstation package on an existing distribution; develop bootable media and a
disk installer for the Void base after the package works on a second
distribution. The [base operating system plan](base-operating-system.md) defines
the target and acceptance criteria.

## Base sequence

Version numbers are in [VERSIONING.md](../../VERSIONING.md).

1. **Independent Hyprland baseline.** On the current Arch workstation,
   accept settings/state/menu ownership (0.4), independent themes/fonts/identity
   (0.5), then native package/system ownership and boot-dependent final removal
   (0.6). Keep Hyprland and prove daily behavior, boot/update/recovery and sleep.
   No portable installer or Sway backend is needed to establish this baseline.
2. **Sway integration and workstation package.** Only after 0.6 acceptance,
   complete both compositor adapters/helpers and install a verified Sway
   package/session beside the independent Hyprland fallback (0.7). Daily-drive
   and accept physical workflow parity (0.8), then remove Hyprland (1.0).
   Arch/pacman remain the base. Prototype code is retained preparation.
3. **A second distribution.** Install the same package on another machine
   running a different distribution with systemd, to exercise the host adapter
   away from Arch (1.1).
4. **Void Linux target.** Try a minimal Void base with runit and Btrfs on
   secondary hardware. Compare musl and glibc; XBPS owns the native operating
   system, and the workstation package is built from the same sources with
   `xbps-src` (1.2). Then repeatable media, single-command activation, and the
   terminal-only profile (1.3).
5. **antiX Core fallback.** If Void has a showstopper, try antiX Core with runit.
   A musl-only problem should first be tested on Void glibc. On antiX, APT/dpkg
   owns native packages; do not mix native managers in the same root.

Stage 0.6 supplies the first independent component/file/update-owner manifest.
Build package automation from that proved baseline; do not require a portable
installer before adopting the current host's files. Existing platform-specific
ownership remains native; observed state and secrets are external to package
defaults. Sway packaging must preserve a recoverable Hyprland login.

## Layers and ownership

```text
Application and environment
  -> independent shell, fred.* plugins, commands, knowledge, AI harnesses
Packaging and recovery
  -> existing distributions: Nix flake + Home Manager module + native host adapter
  -> Void base: native xbps-src packages from the same sources
  -> Btrfs system checkpoints paired with kernel/initramfs/boot selection
Windowing and session
  -> Sway + seatd; session bus, runtime directory, PAM, login, native runit services
Base operating system
  -> Void first; antiX Core with runit if Void has a showstopper
  -> native kernel, modules, firmware, networking, filesystems and boot
Host profile
  -> hardware-specific settings; secrets and observed state kept external
```

Each component and setting has one declared owner. Native packages and user
configuration are distinct from service activation. Root-owned `/etc/sway`
plumbing includes a generated, validated user fragment. Invalid configuration
must have a demonstrated recovery path.

Pin or record component versions and source revisions. One set of sources
feeds two delivery adapters:

| Owner on an existing distribution | Owns |
| :-- | :-- |
| Host distribution | Kernel, firmware, graphics drivers, PAM, logind or seatd, PipeWire, NetworkManager, BlueZ, Chrome, VS Code |
| Host adapter (native package, e.g. a PKGBUILD on Arch) | Wayland session entry, locker PAM file, groups and udev rules, graphics-driver bridge for Nix-built Sway |
| Workstation flake (Nix) | Sway, Qt/Quickshell closure, shell, plugins, selected third-party desktop tools, `tam` command, knowledge corpus |
| User | Validated declarative settings only |

On the Void base, native `xbps-src` packages replace the flake and the host
adapter, and runit services supply the session. At stage 0.7, prove early on existing
distributions: Nix-built Sway and Mesa against host kernel drivers, locker
authentication through host PAM, and portal and keyring startup under the host
session manager. Chrome and VS Code come from their vendors' packages and are
checked, never redistributed. Nix profile rollback alone does not restore the
host kernel or native package database.

## Proposed repository shape

```text
tamlinux/
  bin/tam                      # command entry point
  flake.nix                    # workstation package for existing distributions
  installer/                   # inspect, plan, apply, verify orchestration
  host-adapters/arch/          # native host adapter (PKGBUILD) for Arch
  profiles/arch-hyprland/      # independent Hyprland baseline; legacy import separate
  profiles/arch/               # existing-distribution profile, first host
  profiles/void/               # first target base adapter, native xbps-src
  profiles/antix/              # fallback base adapter
  manifests/                   # source and package versions/owners
  knowledge/                   # offline command and onboarding content
  docs/plans/                  # decisions, milestones, evidence
```

This is a proposed structure, not an implemented installer. Do not copy
third-party source trees into the repository when pinned maintained inputs
can be composed. Hardware layouts and credentials are supplied separately.

## Installation contract

- `tam install inspect` reports OS, architecture, version, package tools,
  and supported profile.
- `tam install plan --profile <profile>` prints exact changes, inputs,
  revisions, privileges, checkpoints, and recovery steps without changing anything.
- `tam install apply --profile <profile>` applies only the reviewed plan;
  a stale or mismatched plan requires a new review.
- `tam install verify` checks components, versions, command resolution,
  desktop integration, and failed or skipped steps.

Every step declares prerequisites, owner, expected state, action, and verification.
Re-running a satisfied step is safe. Failure stops dependent steps and reports
recovery. Applying a workstation layer never partitions storage or switches the
active OS as a hidden side effect. Native host packages remain authoritative
on the current Arch workstation throughout independence and Sway integration.

## Pilot and recovery requirements

Select hardware and disk boundaries before installation. Measure installation
steps, boot/idle memory, workload peaks, disk growth, and power where practical.
Void's standard installer requires manual partitioning; additional deployment
work may be needed for the eventual community-install workflow.
[Void installer](https://docs.voidlinux.org/installation/live-images/guide.html).

Compare musl and glibc with matched workload/build settings and count any glibc
compatibility environment. Chrome and VS Code remain required graphical
applications. Keep terminal-only profiles for 32-bit, unsuitable graphics, and
memory-constrained machines. Resource thresholds are measured acceptance criteria.

Checkpoint system files, configuration, and the native package database together.
Pair the checkpoint with kernel/modules, firmware, initramfs, and boot selection;
handle separate boot/EFI partitions and nested subvolumes explicitly. Preserve
user documents outside system rollback, keep an accepted fallback, bound
retention, and verify offline rescue restoration after a failed update.
Snapshots supplement an external backup.
[Btrfs subvolumes](https://btrfs.readthedocs.io/en/latest/btrfs-subvolume.html).

## Milestones

| Milestone | Deliverable | Acceptance evidence |
| :-- | :-- | :-- |
| A. Inventory | Current component/owner manifest and dependency classification | Recorded source revisions and ownership. |
| B. Framework | Inspect, plan, bounded apply, verify for 0.7 delivery, using the accepted independent Hyprland ownership manifest | Plans, idempotent steps, recovery; does not block earlier ownership transfers. |
| C. Package on this workstation | Workstation flake and Arch host adapter; Sway session beside Hyprland, then Hyprland removed (0.7–1.0.0) | `install verify` passes; required workflows and parity checks; rollback route recorded before removal. |
| D. Second distribution | Same package on a different distribution (1.1) | Install, verify, and a recorded list of host-adapter differences. |
| E. Void pilot | Minimal runit/Btrfs base, native `xbps-src` packages, libc comparison on secondary hardware (1.2) | BIOS/UEFI installation, hardware checks, resource measurements; Chrome, VS Code, terminal workflow, kernel/userspace update and full recovery. |
| F. Distribution | Repeatable media, single-command activation, terminal-only profile (1.3) | Multi-hardware installation and recovery verification. |

Try antiX Core if Void fails an essential requirement at acceptable maintenance
cost. The daily workstation's base stays Arch until the pilot has evidence;
its desktop is packaged at 0.7, accepted on Sway at 0.8, and drops Hyprland
at 1.0. Documentation changes do not bump the product version.

## Decision record

- **2026-09-23:** Installation contract and general command structure approved.
- **2026-09-28:** antiX Core was selected as the base direction.
- **2026-10-03:** Circa-2006 floor, Sway, runit, Chrome/VS Code, terminal-first,
  and terminal-only profiles selected; Nix-built delivery was the initial design.
- **2026-10-03, latest:** Try Void first; try antiX Core if Void has a showstopper.
  Prefer Btrfs for the pilot, compare musl/glibc, and evaluate native XBPS packaging.
  Mandatory Nix delivery is reopened; portable delivery remains a goal.
- **2026-10-03, route:** Install the workstation package on existing
  distributions first, with a Nix flake and a native host adapter; Fred's Arch
  workstation is the first host and reaches 1.0.0 when Omarchy and Hyprland are
  removed. On Void, build the same sources as native `xbps-src` packages.

- **2026-10-07:** Independent Hyprland acceptance at 0.6 now precedes integrated
  Sway/package work at 0.7. The terminal command is named `tam`; the package
  remains `tamlinux`. Prior approved install operations retain their behavior.

Open: pilot hardware, disk layout, libc choice, supported existing
distributions, the graphics bridge for Nix-built Sway, signed binary delivery, application licensing, graphics drivers/renderer,
session services, resource thresholds, retention, and tested boot recovery.

## References

- [Base operating system plan](base-operating-system.md).
- [Desktop decoupling](desktop-decoupling.md).
- [Void Linux](https://voidlinux.org/) — first target.
- [antiX Linux](https://antixlinux.com/) — fallback.
- [Sway](https://swaywm.org/), [seatd](https://git.sr.ht/~kennylevinsen/seatd),
  [runit](http://smarden.org/runit/) — compositor, seat access, supervision.
