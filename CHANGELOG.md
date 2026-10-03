# Changelog

All notable changes to Tamlinux are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
as defined in [`VERSIONING.md`](VERSIONING.md).

## [Unreleased]

### Changed

- Recorded the decision to use **runit** for system initialization and service
  management for Suspra Workstations in [`README.md`](README.md),
  [`VERSIONING.md`](VERSIONING.md), and the
  [installation framework](docs/plans/installation-framework.md).
- Recorded the 2026-10-03 targets in [`README.md`](README.md): hardware from
  circa 2006 onward (older is out of scope) on Wayland, not X11; antiX Linux
  Core with a tiling window system inspired by the Omarchy UI, with the
  compositor reopened (River is no longer the settled choice); Chrome and VS
  Code must run; and a terminal-first experience. Updated
  [`VERSIONING.md`](VERSIONING.md) and the
  [installation framework](docs/plans/installation-framework.md) to match.
- Added the [compositor field survey](upstream/2026-10-03-compositor.md) and
  recorded its outcome: **Sway**, built by Tamlinux with Nix. River,
  river-classic, and mango are deferred; dwl and niri are rejected for now.
- Recorded the Nix-built workstation package (on antiX Core or an existing
  Linux), the three kinds of terminal-only machine, and the package design
  points in the [installation framework](docs/plans/installation-framework.md).

- Refined architectural vision and public explainer in [`README.md`](README.md):
  clarified that Arch Linux's appealing idea is continuous rolling updates,
  adopted AntiX Linux's inspiration for older hardware support and lean
  non-systemd base layer, and elevated simplifying and minimizing resource use
  as a general principle that allows Linux to run faster and use less energy
  on modern hardware as well.
- Defined the transition roadmap: working from Omarchy (0.x) toward an AntiX
  Linux base layer (`antiX Core` + `seatd` + Wayland + River, with Nix rollbacks),
  graduating to the launch of **Suspra Linux** and the Tier 3 Suspra Workstation.
- Updated [`UPSTREAM.md`](UPSTREAM.md) and [`VERSIONING.md`](VERSIONING.md) to
  align with the AntiX base layer and Suspra Workstation trajectory.
- Updated [`docs/plans/installation-framework.md`](docs/plans/installation-framework.md)
  and [`docs/plans/README.md`](docs/plans/README.md) to replace the exploratory
  NixOS/Arch host sequence with the settled AntiX Linux Core base sequence and
  Maker Fest distribution model.

## [0.0.1] - 2026-09-22

### Added

- First product version. Tamlinux 0.0.1 is the current workstation snapshot:
  Omarchy plus Fred's patches and `fred.*` plugins.
- [`VERSIONING.md`](VERSIONING.md) records the 0.x / 1.x split, the
  workstation-then-installer order, and that Home Manager generations are a
  local rollback handle, not the product number.

[0.0.1]: https://github.com/greenermoose/tamlinux/releases/tag/v0.0.1
