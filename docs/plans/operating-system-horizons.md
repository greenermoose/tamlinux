# Operating-system horizons

**Recorded:** 2026-10-19. **State:** research only. This plan chooses no new
base operating system and implies no migration. The
[base operating system plan](base-operating-system.md) remains the authority
for the current base, the target and the fallback.

Tamlinux watches other operating systems for two reasons: to find fixes and
ideas worth carrying into Tamlinux on its Linux base, and to prepare a later
version, **Tam 2.0**, that explores a microkernel base instead of the Linux
kernel. This plan records which systems are watched, in what role, and what
evidence a later decision will need. The `tam` guide's Operating Systems
reference describes each system offline.

## Roles

A role is a research judgment, not a recommendation to migrate. Listing a
project grants no permission to adopt its code, change the base or post in its
spaces. Evidence that a project is active is not evidence that it is secure,
mature, suited to Tamlinux's hardware, or sustainably maintained.

| Role | Meaning |
| --- | --- |
| Base | Runs the current workstation: Arch Linux. |
| Target | The first planned replacement base: Void Linux with runit. |
| Fallback | Tried if the target has a showstopper: antiX Core with runit. |
| Evaluate | A possible Linux base worth comparing against the target. |
| Integration donor | Close enough to Tamlinux that its fixes and integration work are reviewed directly. |
| Idea donor | Studied for a specific design idea; not a candidate base. |
| Horizon | A non-Linux system studied for architecture and long-range ideas. |
| Tam 2.0 candidate | A microkernel-based system explored as a future base. |

## Linux systems watched

| Family | Systems and roles |
| --- | --- |
| Arch | Arch Linux (base). Omarchy (integration donor; Tamlinux's code ancestor). CachyOS (donor: package and update experience, performance, Hyprland integration). EndeavourOS (donor: installer, recovery, documentation). Manjaro (donor: staged updates, hardware experience). Artix (donor: Arch-family packages with other init systems). |
| Void | Void Linux with glibc (target, evaluated first). Void Linux with musl (evaluated separately for C library compatibility). |
| Debian | antiX (fallback; donor for low-footprint systems without systemd). Debian (evaluate: stable base and security maintenance). Ubuntu (evaluate; donor for desktop and security engineering). Linux Mint and LMDE (donor: desktop integration, update manager, snapshots). Devuan (donor: Debian with other init systems). BunsenLabs (donor: configuration packages layered on an unchanged Debian base). elementary OS (donor: coherent design, accessibility, applications). Pop!_OS (donor: COSMIC, tiling, hardware integration). Vanilla OS (donor: image-based updates). |
| Fedora | Fedora Linux (evaluate; donor for desktop changes and QA). Fedora Atomic Desktops (donor: image lifecycle). Bazzite and Bluefin (donors: hardware enablement and workstation image delivery). Qubes OS (donor: compartmentalization with Xen). |
| openSUSE | Tumbleweed (evaluate rolling base; donor for openQA and the Open Build Service). Leap (evaluate stable base). Slowroll (evaluate once its maturity is confirmed). MicroOS and Aeon (donors: transactional updates and rollback, automated desktop maintenance). Kalpa (donor: immutable KDE integration). |
| Independent | Alpine Linux (evaluate: minimal base, portability). Gentoo (evaluate: configurable source and binary packages). Slackware (evaluate: traditional base). Chimera Linux (evaluate; donor). Solus (donor: curated rolling desktop with tested weekly delivery). KaOS (donor: focused Qt integration). Adélie Linux (not yet assessed). |
| Declarative | NixOS (evaluate; donor for reproducibility). GNU Guix System (evaluate; not yet assessed). |

## Non-Linux horizon

| Family | Systems and what is studied |
| --- | --- |
| BSD | FreeBSD (coherent base system, jails, ZFS, documentation). OpenBSD (security and correctness engineering). NetBSD (portability). DragonFly BSD (HAMMER2 snapshots, virtual kernels, multiprocessor design). |
| illumos | The illumos core and its distributions OpenIndiana (workstation integration), OmniOS (server lifecycle, ZFS, zones, DTrace, SMF) and SmartOS (virtualization). |
| Other | SerenityOS (a cohesive graphical desktop built on its own core). Haiku (personal-computing design from BeOS). ReactOS (Windows application and driver compatibility). |

## Tam 2.0: a microkernel base

After Tamlinux 1.x runs on a Linux base, Fred wants to explore a microkernel
base, with **Redox OS** as the first candidate. Before leaving a monolithic
kernel, the benefits of microkernels need careful study rather than
assumption: a microkernel label alone proves neither safety nor speed.

| Candidate | Status |
| --- | --- |
| Redox OS | First candidate. A Unix-like, microkernel-based system written in Rust with partial POSIX compatibility. Hardware support would likely require Tamlinux to take part in Redox driver development. |
| Fuchsia | Research. Studied for component isolation, diagnostics and its driver framework; whether its Zircon kernel counts as a microkernel or a hybrid is unsettled. |
| SerenityOS | Donor, not a microkernel candidate: its kernel architecture is not established as a microkernel. |
| Linux control | The current and target Linux bases, measured on the same workloads for comparison. |

Systems such as seL4, MINIX 3, Genode, HelenOS, GNU Hurd and QNX are
background for understanding microkernel trade-offs. They are not
candidates.

Tam 2.0 carries forward Tamlinux's outcomes: ergonomics, responsiveness,
reliability, accessibility, hardware longevity, repairability, controllable
updates and recovery, and a maintainable total cost. Whether runit, Sway,
bash, Nix and today's Linux applications carry over unchanged is Fred's
decision, not an automatic reason to exclude a candidate. Tamlinux ideas on
Redox might become a new environment rather than a rebuild of the Linux
desktop.

## Evidence a decision needs

For any candidate base, Linux or not:

- a pinned, bootable image built reproducibly from known sources;
- driver and hardware coverage on real target machines, including graphics,
  input, audio, network, storage, sleep and accessibility;
- a map of required applications and workflows, and how each is met: native,
  newly written, or through a compatibility environment or virtual machine,
  with that environment's costs counted;
- security-response ownership, signed updates, rollback and recovery of user
  data;
- one-time porting cost and recurring maintenance burden for drivers,
  applications and packaging.

For a microkernel candidate, also test what fault containment actually
delivers: which drivers and services run outside the kernel, whether they
restart without data loss, what a compromised service can reach, and what
interprocess communication costs in desktop latency, throughput, memory and
energy on comparable workloads.

"Learn from", "port a component", "prototype a system" and "change the
production base" are separate decisions, each made on Fred's word. No image
has been built or booted and no measurement has been made under this plan.
