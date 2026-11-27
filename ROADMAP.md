# tamlinux roadmap

`tamlinux` is the Tamlinux workstation environment and desktop product
repository, developed in public on branch `dev`.

- **Current version:** `0.7.3` (branch `dev`; latest released cultivar `0.5.12`)
- **Progress:** 3 of 6 phases done (P32 and P1 complete/in closeout; P33 Northern Torch in progress; P2–P3 planned)
- **Versioning:** Cultivar names identify minor workstation releases
  (`VERSIONING.md`); `test`, `main`, tags, and releases move only on
  Fred's word.

## Phase summary

| Phase | Versions | Goal | Plan | Status |
| --- | --- | --- | --- | --- |
| **P32** | 0.4.8–0.5.12 | Gate A standalone Tamlinux and Blue Sparkler input/appearance baseline | [P32-early-releases.md](plans/P32-early-releases.md) | Done (2026-11-01) |
| **P1** | 0.6.x | KBN WB: dependable Arch/Hyprland baseline and locked source installs across fleet | [P1-0.6.28.md](plans/P1-0.6.28.md) | Done |
| **P33** | 0.7.x | Northern Torch: `tam-pane` everywhere, C17 app suite, and complete Hyprland removal | [P33-northern-torch.md](plans/P33-northern-torch.md) | In progress |
| **P2** | 1.0.0 | Postus: repeatable fresh-install path and transition to fresh GitLab repositories | [P2-1.0.0-gitlab-and-source-install.md](plans/P2-1.0.0-gitlab-and-source-install.md) | Planned |
| **P3** | 1.1–1.3 | Bear Swamp / Craftsbury Flats / Girard Dwarf: second distro, Void/runit pilot, repeatable minimal base | [P3-base-operating-system.md](plans/P3-base-operating-system.md) | Planned |

## Phases and milestones

### Phase P32: Gate A and Blue Sparkler (0.4.8–0.5.12) — [P32-early-releases.md](plans/P32-early-releases.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **0.4.8** | Gate A: remove all Omarchy packages and paths; standalone Tamlinux on Arch/Hyprland/Quickshell | Done (2026-10-22) |
| **0.5.12** | Blue Sparkler: input usability, console-first startup, start menu, monitor control, Tokyo Night defaults | Done (2026-11-01) |

### Phase P1: KBN WB dependable baseline (0.6.x) — [P1-0.6.28.md](plans/P1-0.6.28.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **0.6.x** | GPU-resume/hibernation mitigations, pinned upstream patches, routine updates/rollback, locked source installs (`plans/P21-source-install.md`) | Done |

### Phase P33: Northern Torch — tam-pane everywhere (0.7.x) — [P33-northern-torch.md](plans/P33-northern-torch.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **0.7.0–0.7.1** | Stage 1 (M1–M8): app checklist, reproducible `tam-pane` session, guarded launches, UWSM/portals, `TamPaneAdapter`, controls, shell/plugin proof, headless test battery | Done (2026-11-26) |
| **0.7.1–0.7.2** | Stage 1 (M9–M10): physical hardware/lock/recovery proof on bosgame and switch default desktop to `tam-pane` (awaits Test/Run) | In progress |
| **0.7.3** | Stage 2 (M11–M14): move lock/idle to `tam-hide`, replace `hyprsunset`/`hyprpicker`, port fleet commands off `hyprctl`, decouple themes/menus/Tensaku | In progress |
| **0.7.x** | Stage 3 (M15–M17): delete all Hyprland code/configs/adapters, remove `hypr*`/`aquamarine` packages across fleet, close Northern Torch | Planned |

### Phase P2: Fresh install and GitLab (1.0.0) — [P2-1.0.0-gitlab-and-source-install.md](plans/P2-1.0.0-gitlab-and-source-install.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **1.0.0** | Prove repeatable fresh-install path from `tam-bud` and transition to fresh GitLab repositories | Planned |

### Phase P3: Other distributions and minimal base (1.1–1.3) — [P3-base-operating-system.md](plans/P3-base-operating-system.md)

| Version | Milestone | Status |
| --- | --- | --- |
| **1.1** | Verify Tamlinux on a second systemd distribution | Planned |
| **1.2** | Pilot Void Linux + runit + seatd + Btrfs with native `xbps-src` delivery (comparing musl and glibc) | Planned |
| **1.3** | Repeatable live-media installation and terminal-only profile for constrained hardware | Planned |

## How a milestone is done

A milestone is done when its acceptance checks in the phase plan pass and
Fred has accepted the candidate through his Test, Run, or Release words.
Update `VERSION`, the phase plan, and this roadmap in the same change.
