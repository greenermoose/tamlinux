# Session: 2026-10-03 — Hardware floor, open compositor, and workstation requirements

- **CLI tool:** Claude Code `2.1.288` (`claude --version`, checked live)
- **Model:** Claude Opus 5.5 (`claude-opus-5-5`)
- **Transcript**: Retained privately by the author.
- **Scope:** Documentation only; no runtime code changed and nothing installed.

## User direction

> Please update the appropriate repos to capture this additional thinking about tamlinux:
>
> 1) I want to run on hardware that is 20 years old (starting circa 2006), but older than that is beyond our remit. This should allow us to run on Wayland instead of X11.
> 2) I am not sure about river. I am sure that I want to build on antiX Linux core and then install a tiling windowing system inspired by the UI Omarchy provides.
> 3) I want to be able to run Chrome and vscode on [redacted: unannounced plans].
> 4) I also want to provide a good terminal experience on [redacted: unannounced plans] so that you can do most things using a terminal and keyboard.

## Changes

- `README.md`: new **Targets** section (circa-2006 floor, antiX Core plus an
  Omarchy-inspired tiling window system, Chrome and VS Code, terminal first);
  River no longer named as the target compositor.
- `VERSIONING.md`, `CHANGELOG.md`, `docs/plans/installation-framework.md`, and
  `docs/plans/desktop-decoupling.md`: compositor reopened; pilot milestones now
  name near-floor x86-64 hardware, Chrome, VS Code, and terminal workflows;
  open decisions listed.
- The approved one-line public description, which lists River among the
  desktop inspirations, was left unchanged.

## Agent contributions to check

These follow from Fred's statements but are the agent's analysis:

- Chrome and VS Code ship only x86-64 and ARM64 Linux builds, and Chrome needs
  an SSE3 CPU, so 32-bit-only machines from the same era cannot run them. The
  agent recorded the resulting 32-bit profile as an open question.
- The compositor must run on circa-2006 graphics hardware (software renderer or
  OpenGL ES 2), and the terminal emulator must run without GPU acceleration.

## Follow-up: compositor field survey

> I have updated the doc. Survey the field for a Tamlinux compositor and update accordingly.

- Wrote [`upstream/2026-10-03-compositor.md`](../../upstream/2026-10-03-compositor.md)
  and linked it from `UPSTREAM.md`, the README, the installation framework,
  and the changelog. Its recommendation (Sway, with conditions) is marked
  proposed; Fred has not decided.
- Fred's review edits decided that 32-bit machines are terminal only; the
  README and installation framework now say so.
- Evidence came from project documentation, release coverage, Debian package
  metadata, and antiX's own `trixie` package indexes, which were downloaded and
  searched directly. No compositor was run on old hardware.

## Follow-up: Sway and the Nix-built package

> Let's choose sway and we will bulid it ourselves and manage it with nix. My current thinking is that we'll install core antiX Linux on systems that don't already boot to any flavor of linux, then have a [redacted: unannounced plans] package managed with nix that we install on top of it. We can build all the dependencies we need to include for the [redacted: unannounced plans] package. Does this makes sense?

> Yes, record these decisions: 1) sway chosen, 2) Nix-build [redacted: unannounced plans] package on antiX Core or existing Linux. As far as machines without enough RAM to compile packages, let's make those terminal only and not try to shoehorn Chrome and VS Code onto them. So terminal-only [redacted: unannounced plans] include two kinds of machines: 1) very old hardware that doesn't have the drivers necessary to run Wayland, and 2) very memory constrained machines that can't compile code or comfortably run Chrome and nix. Record the five adjustments and open design points to be determined as we begin building systems on older hardware.

- The decisions are Fred's. The five design points and their wording (root
  layer, binary cache, graphics userspace, Chrome/VS Code redistribution,
  terminal-only machines without Nix) are the agent's, accepted by Fred as
  direction with details open.
- Updated the survey outcome, `UPSTREAM.md`, `README.md`, `VERSIONING.md`,
  `CHANGELOG.md`, the installation framework, and the desktop decoupling plan.

## Verification

- Chrome's Linux requirement (SSE3-capable x86-64 or 64-bit ARM) was checked
  against Google's published Chrome system requirements.
- antiX 26.1 (Debian 13 based) still publishes 32-bit and 64-bit Core images,
  per its release coverage.
- Public-repository check: no session IDs, session-store paths, local paths, or
  private repository names in this record.
