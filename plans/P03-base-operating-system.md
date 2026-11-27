# P03 · Target base operating system

- **Phase:** PH05
- **Versions:** 1.1–1.3
- **Status:** Planned, after the 1.0 source-install proof.

**Project scope (2026-10-06):** Tamlinux is an independent, continuing Linux
workstation environment aimed at the best possible user experience on any
hardware. The workstation package remains `tamlinux`; the terminal command is `tam`
(named 2026-10-07). Existing-distribution
source delivery and native Void packaging are Tamlinux engineering work. Hardware
profiles are capability-based; circa-2006 machines are validation examples,
not a universal age cutoff.

**Decided:** 2026-10-03. **State:** pilot target; installation and hardware validation pending.

## Target and fallback

We will try **Void Linux** as the base distribution, using **runit** for init
and service supervision and **Btrfs** as the preferred pilot filesystem.
If Void presents a showstopper, we will try **antiX Linux Core with runit**.
The Arch workstation remains the working development system. Build on
the [Postus fresh-install path](P02-1.0.0-gitlab-and-source-install.md).
The second systemd distribution comes first, followed by the Void pilot
on secondary hardware. Hardware selection can begin earlier.

## Milestones

1. **1.1 · Bear Swamp.** Install and run the source-delivered workstation
   on a second systemd distribution. Verify native dependency ownership,
   the console and graphical profiles, and upgrade and rollback.
2. **1.2 · Craftsbury Flats.** Pilot Void with runit, seatd, Btrfs, and
   native `xbps-src` packages. Compare glibc and musl, prove update and
   recovery, and return to plain Void with user documents intact.
3. **1.3 · Girard Dwarf.** Repeat live-media base installation and prove
   one-command Tamlinux activation. Validate a terminal-only profile on
   constrained hardware, including the planned older and 32-bit targets.


## Why try Void first

Void is the first implementation target, not a demonstrated hardware winner.
A showstopper means an essential hardware, application, installation, update,
or recovery requirement cannot be met at acceptable maintenance cost. Investigate
configuration and supported kernel/firmware choices before attributing a failure
to the distribution. A musl-only incompatibility calls for testing Void glibc
before switching the base to antiX.

Void's independent minimal base and native runit design may fit the project
better than a Debian-derived base adapted to exclude systemd. XBPS and
`xbps-src` offer a native path from source builds to dependency-tracked binary
packages. Void's glibc and musl options allow a measured comparison of footprint
and compatibility. These are reasons to run the pilot; they do not establish
better security, smaller complete workloads, or higher hardware reliability.
[Void overview](https://voidlinux.org/),
[Void libc options](https://docs.voidlinux.org/installation/musl.html).

antiX Core remains the fallback for its minimal, Debian-derived foundation,
runit default, and older-hardware focus.
[antiX release](https://antixlinux.com/antix-26-1-released/).

## Package and service ownership

XBPS owns Void's native kernel, libraries, firmware, and service packages.
Evaluate packaging the workstation components through `xbps-src` and a signed
project repository. Source compilation is acceptable; slower clients can use
binary packages. Keep one declared owner for each package and setting.
[Void custom repositories](https://docs.voidlinux.org/xbps/repositories/custom.html).

Plan to carry Tamlinux's `xbps-src` templates in the project repository
permanently, not as future `void-packages` submissions. Void's project-wide
[contribution policy](https://github.com/void-linux/.github/blob/master/CONTRIBUTING.md)
(2026-06-12) expects contributions in all Void spaces, including issues and
comments, to originate from humans, and requires every use of AI tools to be
disclosed. Void maintainers also expect new projects to show a history of
reliable maintenance before packaging them. Tamlinux is developed largely
with AI agents. Any contact with Void is written by Fred and discloses AI use;
agents do not post in Void spaces. Count the ongoing maintenance of these
templates in the packaging evaluation.

tam-pane, Tamlinux's own compositor, is the selected compositor (D263), with
seatd and an independent Quickshell host. On Void, the workstation package is
built as native `xbps-src` packages; on existing distributions, the same
sources use the locked Make-based installation with native dependencies. No base migration is implied for the current
workstation, which stays on Arch.
[Void Wayland support](https://docs.voidlinux.org/config/graphical-session/wayland.html).

## C library evaluation

Compare musl and glibc using matched application versions, features, build flags,
services, hardware, and workloads. Measure complete dependency and compatibility
footprints, installed disk usage, idle and peak memory, performance, energy,
maintenance effort, and hardening. Smaller libc code alone does not establish
better security or lower application memory consumption.

Google Chrome and VS Code remain graphical workstation requirements. Test their
actual supported execution paths. Proprietary NVIDIA drivers do not support
musl; glibc-only software may require a compatibility environment whose costs
must count in the measurements. Keep separate libc test roots/images, rather
than replacing libc under an installed system. A musl host does not rebuild
vendor binaries or glibc-based Nix packages against musl.
[Void musl compatibility](https://docs.voidlinux.org/installation/musl.html).

## Recovery and acceptance

Btrfs checkpoints should capture native system files, configuration, and the
package database together, paired with kernel/modules, firmware, initramfs,
and boot selection. Keep user documents outside system rollback. Account for
separate boot partitions and nested subvolumes; snapshots are not recursive
and do not replace an external backup. Bound retention and measure free space
across repeated upgrades.
[Btrfs snapshots](https://btrfs.readthedocs.io/en/latest/btrfs-subvolume.html).

XBPS 0.60.7 had no transaction hooks. Check
[the hooks proposal](https://github.com/void-linux/xbps/pull/666) and the
selected XBPS release before the pilot. If there are no hooks, have the
Tamlinux update command create pre-update checkpoints and prove detection
and recovery when a direct `xbps-install` transaction bypasses that command.

The pilot also proves the **route back to plain Void**: Tamlinux packages
uninstall to a working stock Void system, with the user's documents intact.

Prove installation, unprivileged tam-pane/seatd startup, required applications,
network/audio, graphics, sleep, native services, and offline recovery after a
failed kernel/userspace update. Test older BIOS hardware from the circa-2006
validation cohort and modern UEFI hardware. Measure terminal-only and graphical profiles.
The fallback decision follows this evidence, not a first configuration error.

Use the [locked source-install plan](P21-source-install.md) for the
existing-distribution path. Native Void packaging serves the pilot base.
