# tamlinux roadmap

`tamlinux` is the Tamlinux workstation environment and desktop product
repository, developed in public on branch `dev`.

- **Current version:** `0.7.5` on `dev` · Run baseline `0.6.42` · latest release `0.6.42`
- **Progress:** 2 of 5 phases done. KBN WB (`0.6.42`) is released and Northern Torch is in progress.
- **Versioning:** Cultivars name minor workstation releases. Phase IDs
  follow milestone order and plan IDs are independent. See [VERSIONING.md](VERSIONING.md).

## Phase summary

| Phase | Versions | Goal | Plan | Status |
| --- | --- | --- | --- | --- |
| **PH01** | 0.4.8–0.5.12 | Standalone Tamlinux and the Blue Sparkler input and appearance baseline | [P32-early-releases.md](plans/P32-early-releases.md) | Done (2026-11-01) |
| **PH02** | 0.6.42 | KBN WB dependable Arch/Hyprland baseline and locked source installs across the fleet | [P01-kbn-wb-baseline.md](plans/P01-kbn-wb-baseline.md) | Done (2026-11-27) |
| **PH03** | 0.7.x | Northern Torch adoption of `tam-pane` and the C17 app suite, followed by Hyprland removal | [P33-northern-torch.md](plans/P33-northern-torch.md) | In progress |
| **PH04** | 1.0.0 | Postus fresh-install proof and transition to four GitLab repositories | [P02-1.0.0-gitlab-and-source-install.md](plans/P02-1.0.0-gitlab-and-source-install.md) | Planned |
| **PH05** | 1.1–1.3 | Support another systemd distribution, pilot Void/runit, and prove a repeatable minimal base | [P03-base-operating-system.md](plans/P03-base-operating-system.md) | Planned |

## Phases and milestones

### Phase PH01: Gate A and Blue Sparkler (0.4.8–0.5.12) — [P32-early-releases.md](plans/P32-early-releases.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **0.4.8** | Gate A removes Omarchy packages and paths. Tamlinux stands alone on Arch, Hyprland, and Quickshell. | Done (2026-10-22) |
| **0.5.12** | Blue Sparkler delivers console-first startup, improved input, start menu, monitor control, and Tokyo Night defaults. | Done (2026-11-01) |

### Phase PH02: KBN WB dependable baseline (0.6.42) — [P01-kbn-wb-baseline.md](plans/P01-kbn-wb-baseline.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **0.6.39** | Prove reliability mitigations, retained workflows, and locked source installs and rollback across the fleet. Whole-checklist Test accepted on 0.6.39. | Done (2026-11-25) |
| **0.6.42** | Complete daily-use acceptance of the baseline and release it. Final KBN WB release tagged and published on 0.6.42. | Done (2026-11-27) |

### Phase PH03: Northern Torch compositor transition (0.7.x) — [P33-northern-torch.md](plans/P33-northern-torch.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **0.7.0–0.7.2** | Stage 1, M1–M8. Bring up the reproducible `tam-pane` session, shell and C17 apps. Development and headless checks passed. | In progress |
| **0.7.x** | Stage 1, M9–M10. Prove hardware, locking, and recovery. Accept daily use and switch the default desktop. | In progress |
| **0.7.3 onward** | Stage 2, M11–M14. Lock and idle, gamma and color picking, fleet commands, and themes are wired in development. Prove the replacement workflows on physical fleet hardware. | In progress |
| **0.7.x** | Stage 3, M15–M17. Remove Hyprland code and packages, then verify clean builds and fleet-wide daily use on `tam-pane` alone. | Planned |

### Phase PH04: Fresh install and GitLab (1.0.0) — [P02-1.0.0-gitlab-and-source-install.md](plans/P02-1.0.0-gitlab-and-source-install.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **1.0.0** | Prepare four lean GitLab source trees and measure clone size and checkout time. | Planned |
| **1.0.0** | Prove fresh Arch bootstrap with `tam-bud` and Make in graphical and console-only profiles. Publish the repository map and tested install instructions at cutover. | Planned |

### Phase PH05: Other distributions and minimal base (1.1–1.3) — [P03-base-operating-system.md](plans/P03-base-operating-system.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **1.1** | Bear Swamp verifies installation and operation on a second systemd distribution. | Planned |
| **1.2** | Craftsbury Flats pilots Void with runit, seatd, Btrfs, native `xbps-src` packages, and tested recovery. Compare glibc and musl. | Planned |
| **1.3** | Girard Dwarf proves repeatable live-media installation, one-command activation, and a terminal-only profile for constrained hardware. | Planned |

## How a milestone is done

A milestone is done when its plan's acceptance checks pass and Fred has
accepted the result at the required stage for the exact candidate. Test, Run,
and Release each require their own instruction. Update the plan and
roadmap together, and update `VERSION` when preparing a new candidate.
