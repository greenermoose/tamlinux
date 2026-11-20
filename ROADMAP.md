# Tamlinux roadmap

Tamlinux is developed in public on branch `dev`; `test`, `main`, tags, and
releases move only on Fred's word (`VERSIONING.md`). Cultivar names identify
minor versions of the workstation environment.

## 0.4.8: Gate A — standalone Tamlinux (released 2026-10-22)

Removed all Omarchy packages and paths. Tamlinux stands alone on Arch Linux
with Hyprland and Quickshell.

## 0.5.12: Blue Sparkler — input and appearance (released 2026-11-01)

Input usability, console-first startup, start menu, monitor control, and
Tokyo Night / JetBrains Mono defaults.

## 0.6.x: KBN WB — dependable baseline (current)

Fix GPU-resume and hibernation faults or accept mitigations, pin carried
patches with upstream status, establish routine updates and rollback, move
from `tam-bundle` to locked source installs (`make` / `make install`), and
prove host-safe installs across the fleet (`plans/P21-source-install.md`).

## 0.7.0: dogfooding Tamlinux components

Begin dogfooding four separately developed Tamlinux components while keeping
Hyprland available for recovery:

- `tam-pane` (Wayland compositor and window manager)
- `tam-clam` (interactive command shell)
- `tam-last` (terminal emulator)
- `tam-edit` (text editor)

## 1.0.0: fresh-install path and GitLab

Prove the repeatable fresh-install path and transition to fresh GitLab
repositories (`plans/P2-1.0.0-gitlab-and-source-install.md`).

## 1.1–1.3: other distributions and a minimal base

Verify a second distribution, then pilot Void Linux + runit + seatd + Btrfs
with native `xbps-src` delivery (antiX Core/runit as fallback), comparing
musl and glibc, followed by repeatable installation and terminal-only
profiles (`plans/P3-base-operating-system.md`).
