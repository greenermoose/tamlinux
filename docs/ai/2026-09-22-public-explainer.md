# Session: 2026-09-22 — Tamlinux public explainer and suite branding

- **CLI Tool**: Cursor `3.21.16`
- **Model**: `composer`
- **Commit**: (this repository's initial commit)
- **Transcript Reference**: `88a15629-5548-46a5-9948-f82903a2e6be`

## Prompts

> Create a tamlinux repo that explains what Tamlinux is: Fred's personal linux distro. In all the *-fred-tamlinux repos, replace mentions of Omarchy Linux with Tamlinux.

Fred later set the public one-liner to:

> Fred's Tamlinux is a bespoke Linux distro aimed at getting the best possible performance from the computing resources you already own, inspired by ideas from Arch Linux, Nix, Wayland, Hyprland, Quickshell, and Omarchy.

## Key Decisions & Implementation Notes

- First version is a README explainer, not an ISO or GitHub Pages site.
- License is GNU GPL v3 (`GPL-3.0-or-later`), matching the plugin suite.
- Public posture: lead with what Tamlinux is; credit Omarchy as inspiration; do not mention controversy or later company work.
- *Tam* = tamarack and total addressable market; temporary like tamarack needles.
- User-facing `Omarchy Linux` / `Fred's Omarchy …` branding in the twelve `*-fred-tamlinux` repos becomes Tamlinux. Technical Omarchy (CLI, paths, marketplace, clonedFrom) and historical docs stay.

## Verification

- Public one-liner matches Fred's final wording.
- LICENSE is the full GNU GPLv3 text copied from `plugin-fred-tamlinux`.
