# AI Sessions

## Session: 2026-09-22 — Marketplace notification security fix (v1.0.4 unreleased)

- **CLI Tool**: Codex CLI `0.155.1`
- **Model**: `gpt-6-sol`
- **Implementation commit**: `58791e0`
- **Transcript Reference**: `01a0cbc5-55fc-7b33-bdea-230b6f8502ed`
- **Prompt**:
  > Please get up to speed on the plan to finish up in-progress omarchy plugin work, then rename my existing GitHub repos from omarchy-fred-* to *-fred-tamlinux. Check to see what plugins we've submitted to the marketplace that are midstream, had security reviews, and have not yet been resubmitted. I want to get those done with the security fixes required, and resubmit them so the review work is not done in vain.
- **Clarification**: Fred chose stem-only naming: `omarchy-fred-clock` becomes `clock-fred-tamlinux`.
- **Changes**: Renamed the GitHub repository and origin; replaced the reviewed shell command in `BarWidget.qml` with a literal argv process, a closed environment, a 4096-character summary cap, and a ten-second watchdog. Prepared version 1.0.4 as unreleased.
- **Verification**: `omarchy plugin validate .` and `git diff --check` passed. Live right-click testing and marketplace resubmission remain pending.

## Session: 2026-09-22 — Release v1.0.4

- **CLI Tool**: Cursor `3.21.16`
- **Model**: `composer`
- **Implementation author**: Codex session above (`58791e0`)
- **Later AI assistance**: Cursor dated the changelog, tagged the release, and resubmitted marketplace #7664
- **Prompts**:
  > I want to do a big rename project for my code. When I'm done, this is what I want to have accomplished: 1) fred.tides and fred.sysinfo will be in normal mode, not test. I have tested them and they are ready to be published to GitHub and used as regular plugins on my system.
- **Clarification**: Fred chose Release (tags, GitHub Releases, Show & Tell, marketplace replies).
- **Verification**: Home Manager generation 92 serves 1.0.4 from the Nix store. `omarchy plugin validate` passed. Test mode off.
