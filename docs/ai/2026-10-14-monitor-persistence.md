# 2026-10-14 — Preserve saved monitor geometry during workspace reconciliation

- **CLI Tool**: Codex CLI `0.162.1`, dynamically checked.
- **Model**: `gpt-6.1-sol`, verified from runtime metadata.
- **Transcript**: Retained privately by the author.
- **Prompt**:
  > Resume from the Tamlinux 0.4.3 handoff.

An isolated compositor trace identifies `tam-desktop-mode`, launched by the
workspace widget, as the writer replacing a saved center display position with
0x0. Its layout reader used the prior configuration path. When that path had
no layout, connector names from retained workspace state became invented
1920-pixel geometry and were then applied as monitor rules.

The helper now reads `tamlinux/hypr/monitors.lua`, matching the session and Display
panel. Workspace topology names retain slot identity without claiming physical
coordinates. Geometry reconciliation requires explicit saved positions and
supports signed coordinates; automatic or computed positions stay with the
compositor.

Verification: the original helper fails the new stale-layout and invented-position
regressions. All 57 workspace helper tests pass after correction, including signed
coordinate restoration. Installed-output transition checks are recorded separately.
