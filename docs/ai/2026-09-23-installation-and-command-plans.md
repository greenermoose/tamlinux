# Session: 2026-09-23 — Installation and `tamlinux` command plans

- **CLI tool:** Codex CLI `0.156.1` (checked on 2026-09-23)
- **Model:** `gpt-6-sol` (verified in the Codex session transcript)
- **Plan commit:** `6524407`
- **Transcript reference:** Codex session `01a0cecc-2ca6-7790-a727-110f64b918da`
- **Scope:** Planning and review. No installer or `tamlinux` command was implemented.

## User direction

These are verbatim excerpts of Fred's prompts relevant to the public work. The
initial prompt also named a private planning source, which is omitted here.

> For the tamlinux repo, begin work on the tamlinux command.

> In the tamlinux repo, start building the framework for installation.

> I believe a good way to start is to pick a base linux distro (such as omarchy for now, but we should strive to switch to another distro, such as NixOS or Arch Linux as soon as we can) and then install the tamlinux stuff on top of that.

> Start with plans and then let me review. Keep track of the work on this in the tamlinux repo.

Fred directly added this requirement to the command plan:

> The command
> must also check if lynx is available and if not fall back gracefully to displaying
> text and instructions for installing lynx so that HTML can be rendered.

Fred then decided:

> I confirm the first slice of the plan for the tamlinux command.

> The bare tamlinux command should show welcome automatically on first use.

> I approve this plan. Go ahead and close the window. Let's commit and publish what we've done in this session.

## Decisions and authorship

- Codex drafted the installation and command plans. Fred edited the Lynx
  fallback sentence in nano and reviewed both plans.
- The installation direction starts with an Omarchy profile, then probes
  NixOS on a second computer. Plain Arch remains an alternative. Machine and
  disk choices remain open.
- The first command slice is approved: help, version, installation entry
  point, local guide, welcome, and curated explanation topics.
- The first interactive bare invocation shows welcome. Lynx is optional at
  runtime; readable text and installation guidance are available without it.
- The plans are documentation for future implementation. Version `0.0.1`
  still describes the current workstation and has not changed.

## Verification

- Fred reviewed the installation direction and approved the command plan.
- The staged plan diff passed `git diff --cached --check`.
- The public plan files were checked for private repository names and local
  machine paths before publication.
