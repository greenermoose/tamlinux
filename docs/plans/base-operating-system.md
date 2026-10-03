# Target base operating system

**Decided:** 2026-10-03. **State:** pilot target; installation and hardware validation pending.

## Target and fallback

We will try **Void Linux** as the base distribution, using **runit** for init
and service supervision and **Btrfs** as the preferred pilot filesystem.
If Void presents a showstopper, we will try **antiX Linux Core with runit**.
The existing Omarchy-based workstation remains the working development system
while the target is proved on secondary hardware.

Void is the first implementation target, not a demonstrated hardware winner.
A showstopper means an essential hardware, application, installation, update,
or recovery requirement cannot be met at acceptable maintenance cost. Investigate
configuration and supported kernel/firmware choices before attributing a failure
to the distribution. A musl-only incompatibility calls for testing Void glibc
before switching the base to antiX.

## Why try Void first

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

Sway remains the selected compositor, with seatd and an independent Quickshell
host. On Void, the workstation package is built as native `xbps-src`
packages; on existing distributions, the same sources are delivered as a Nix
flake with a native host adapter (decided 2026-10-03). The workstation does not
need Nix on the Void base. No base migration is implied for the current
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

Prove installation, unprivileged Sway/seatd startup, required applications,
network/audio, graphics, sleep, native services, and offline recovery after a
failed kernel/userspace update. Test older BIOS hardware near the circa-2006
floor and modern UEFI hardware. Measure terminal-only and graphical profiles.
The fallback decision follows this evidence, not a first configuration error.

The [installation framework](installation-framework.md) and
[desktop decoupling plan](desktop-decoupling.md) carry the implementation order.
Installation on existing distributions comes first, through the Nix flake and
host adapter; native Void packaging serves the Void base.
