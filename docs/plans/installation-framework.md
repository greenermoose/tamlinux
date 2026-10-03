# Installation framework

**Status:** Installation contract approved on 2026-09-23; target updated on
2026-10-03 to Void first, antiX Core fallback. No installer has been implemented.
Pilot machine and disk boundaries remain open.

## Goal

Make a fresh computer reproducibly become Tamlinux without copying one
workstation's state. First implement inspect, plan, apply, and verify; develop
bootable media and a disk installer after the framework works on a second
computer. The [base operating system plan](base-operating-system.md) defines
the target and acceptance criteria.

## Base sequence

1. **Omarchy 0.x development system.** Keep the working workstation productive
   while decoupling plugins, configuration, and services from Omarchy/Hyprland.
2. **Void Linux target.** Try a minimal Void base with runit and Btrfs on
   secondary hardware. Compare musl and glibc; use XBPS for the native operating
   system and evaluate `xbps-src` for the workstation packages.
3. **antiX Core fallback.** If Void has a showstopper, try antiX Core with runit.
   A musl-only problem should first be tested on Void glibc. On antiX, APT/dpkg
   owns native packages; do not mix native managers in the same root.
4. **Independent workstation.** Prove Sway, seatd, the Quickshell host, ported
   plugins, required workflows, installation, and complete recovery. Graduation
   to Suspra Linux follows evidence from the selected base.

## Layers and ownership

```text
Application and environment
  -> independent shell, fred.* plugins, commands, knowledge, AI harnesses
Packaging and recovery
  -> native XBPS/xbps-src candidate; portable delivery open, Nix candidate
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

Pin or record component versions and source revisions. Native Void packaging
and portable installation on an existing Linux may need different delivery
adapters; the earlier all-Nix package requirement is reopened. If Nix is used,
prove its runit integration and constrained-client update path. Profile rollback
alone does not restore the host kernel or native package database.

## Proposed repository shape

```text
tamlinux/
  bin/tamlinux                 # command entry point
  installer/                   # inspect, plan, apply, verify orchestration
  profiles/omarchy/            # current 0.x development adapter
  profiles/void/               # first target base adapter
  profiles/antix/              # fallback base adapter
  manifests/                   # source and package versions/owners
  knowledge/                   # offline command and onboarding content
  docs/plans/                  # decisions, milestones, evidence
```

This is a proposed structure, not an implemented installer. Do not copy
third-party source trees into the repository when pinned maintained inputs
can be composed. Hardware layouts and credentials are supplied separately.

## Installation contract

- `tamlinux install inspect` reports OS, architecture, version, package tools,
  and supported profile.
- `tamlinux install plan --profile <profile>` prints exact changes, inputs,
  revisions, privileges, checkpoints, and recovery steps without changing anything.
- `tamlinux install apply --profile <profile>` applies only the reviewed plan;
  a stale or mismatched plan requires a new review.
- `tamlinux install verify` checks components, versions, command resolution,
  desktop integration, and failed or skipped steps.

Every step declares prerequisites, owner, expected state, action, and verification.
Re-running a satisfied step is safe. Failure stops dependent steps and reports
recovery. Applying a workstation layer never partitions storage or switches the
active OS as a hidden side effect. Native host packages remain authoritative
on the current Omarchy workstation.

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
| B. Framework | Inspect, plan, bounded apply, verify on the current base | Plans, step results, versions, recovery route. |
| C. Void pilot | Minimal runit/Btrfs base; libc comparison on secondary hardware | BIOS/UEFI installation, hardware checks, resource measurements. |
| D. Workstation integration | Sway/seatd, native service and package ownership, ported workflows | Chrome, VS Code, terminal workflow, kernel/userspace update and full recovery. |
| E. Distribution | Repeatable media and single-command setup | Multi-hardware installation and recovery verification. |

Try antiX Core if Void fails an essential requirement at acceptable maintenance
cost. The daily workstation stays on its working installation until the pilot
has evidence. Documentation changes do not bump the product version.

## Decision record

- **2026-09-23:** Installation contract and general command structure approved.
- **2026-09-28:** antiX Core was selected as the base direction.
- **2026-10-03:** Circa-2006 floor, Sway, runit, Chrome/VS Code, terminal-first,
  and terminal-only profiles selected; Nix-built delivery was the initial design.
- **2026-10-03, latest:** Try Void first; try antiX Core if Void has a showstopper.
  Prefer Btrfs for the pilot, compare musl/glibc, and evaluate native XBPS packaging.
  Mandatory Nix delivery is reopened; portable delivery remains a goal.

Open: pilot hardware, disk layout, libc choice, native versus portable packaging,
signed binary delivery, application licensing, graphics drivers/renderer,
session services, resource thresholds, retention, and tested boot recovery.

## References

- [Base operating system plan](base-operating-system.md).
- [Desktop decoupling](desktop-decoupling.md).
- [Void Linux](https://voidlinux.org/) — first target.
- [antiX Linux](https://antixlinux.com/) — fallback.
- [Sway](https://swaywm.org/), [seatd](https://git.sr.ht/~kennylevinsen/seatd),
  [runit](http://smarden.org/runit/) — compositor, seat access, supervision.
