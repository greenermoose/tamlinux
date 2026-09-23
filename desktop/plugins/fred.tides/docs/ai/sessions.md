# AI Sessions

## Session: 2026-09-22 — Marketplace notification security fix (v1.0.4 unreleased)

- **CLI Tool**: Codex CLI `0.155.1`
- **Model**: `gpt-6-sol`
- **Transcript Reference**: `01a0cbc5-55fc-7b33-bdea-230b6f8502ed`
- **Prompt**:
  > Please get up to speed on the plan to finish up in-progress omarchy plugin work, then rename my existing GitHub repos from omarchy-fred-* to *-fred-tamlinux. Check to see what plugins we've submitted to the marketplace that are midstream, had security reviews, and have not yet been resubmitted. I want to get those done with the security fixes required, and resubmit them so the review work is not done in vain.
- **Clarification**: Fred chose stem-only naming: `omarchy-fred-clock` becomes `clock-fred-tamlinux`.
- **Changes**: Renamed the GitHub repository and origin; replaced the reviewed shell command in `BarWidget.qml` with a literal argv process, a closed environment, a 4096-character summary cap, and a ten-second watchdog. Prepared version 1.0.4 as unreleased.
- **Verification**: `omarchy plugin validate .` and `git diff --check` passed. Live right-click testing and marketplace resubmission remain pending.
