# Desktop dependency inventory and implementation handoff

- **Date**: 2026-10-03; the conversation began 2026-10-02 and crossed midnight EDT.
- **CLI Tool**: Codex CLI (`codex`) `0.160.0`, checked live and against session metadata.
- **Model**: `gpt-6.1-sol`, verified against the current turn metadata.
- **Authorship**: Fred set the goal; Codex inspected sources and authored the
  dependency classification, product plan and implementation handoff.
- **Concurrent contribution**: Claude Code `2.1.288` (`claude-opus-5-5`)
  clarified the reopened compositor choice in the plan; tool/model verified
  against that contributing session's transcript. Codex reconciled the final
  handoff and milestone wording with the recorded requirements.
- **Commit**: This record accompanies the desktop dependency plan publication commit.
- **Approval**: Fred authorized commit and push on 2026-10-03.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> What's the next task we should tackle for our tamlinux project? Suggest what to work on and explain why that makes sense to do next.

> Make it so. Then create a step-by-step project plan that I can hand over to agy to take the next step after that.

> Go ahead and commit and push.

## Work and decisions

Prepared [desktop-decoupling.md](../plans/desktop-decoupling.md), indexed the
plan and linked it from the installation framework. The inventory covers
shared QML modules, plugin helpers, host settings and manifests, compositor
operations, stock desktop controls, session/host services and packaging.
Machine-specific hashes, package/service details and operational instructions
are retained privately.

The first implementation slice is a standalone Quickshell host demonstrating
the actual pinned clock and read-only calendar with owned modules and isolated
fixture state. It is planned, not implemented or deployed by this session.
Python/shell backends with Hyprland calls are explicitly treated as integration
work rather than assumed portable.

Official upstream checks found that current River separates compositor and
window manager, while river-classic retains the older tag/riverctl design.
Concurrent workstation requirements reopened the compositor choice; the handoff
was aligned with that recorded decision before publication. The plan requires
selecting and pinning a compositor/WM before backend implementation. Non-systemd
session, Nix installation/service ownership and package closure require pilot
evidence. No field survey or upstream communication was undertaken.

## Verification

- Ran the read-only source evidence collector; validated 522 recorded source
  hashes against their files and checked its Python syntax and help interface.
- Compared all 56 scanned plugin source files across active, deployed and local
  public copies; no differences were found. Eight manifests agreed on versions.
- Checked local Markdown link targets in the inventory, handoff, product plan,
  plan index, installation plan and backlog.
- Checked the public plan for private repository names, local paths and full
  session identifiers; no matches. Public provenance and the complete draft
  diff are reviewed separately before any commit or push.
- No shell prototype, graphical behavior, antiX package closure or hardware
  migration was tested. Existing desktop configuration and power trials were
  not changed.
