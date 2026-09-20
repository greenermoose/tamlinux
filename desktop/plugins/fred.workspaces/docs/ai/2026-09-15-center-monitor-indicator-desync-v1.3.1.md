# Session: 2026-09-15 — Center Monitor Indicator Desync & Atomic File Watch (v1.3.1)

- **Primary AI Agent**: Antigravity CLI (`agy`)
- **Primary Model**: Gemini 3.8 Flash (High)
- **agy version**: `1.2.3` — stated in sessions.md. **Transcript not found locally.**
- **Transcript**: `348c2c39-df3c-4b6f-aea0-e47c001361fb` — **not present** in
  `~/.gemini/antigravity-cli/brain/`. Prompt and implementation details below are
  taken from the prior `sessions.md` without transcript verification.
- **Commits**: `5e198a9` (2026-09-15 22:47), `20c7b78` (2026-09-15 17:29 — provenance docs)

## Prompts (from sessions.md — transcript not verified)

> **Fred:** "fred.workspaces is not showing the active desktop on the center monitor. The left and right monitors have a dot over 1 but the center one does not. Figure out why and fix."

## Root Cause (from sessions.md — transcript not verified)

- `omarchy-desktop-mode` writes state files atomically via `os.replace()`.
- In `Workspaces.qml`, `monitorsFile` had default `atomicWrites: false`. During a
  post-resume flapping event where DP-2 momentarily disconnected, the file was rewritten.
  When DP-2 reconnected, the file was replaced again. While DP-2 and HDMI-A-1's bars
  reloaded, DP-1's bar remained running on the orphaned inode and was never notified.
- With stale `monitorCount == 2` on DP-1, workspace 2 on DP-1 did not match the expected
  workspace 1 at position 0, preventing the focused dot indicator from appearing.

## Implementation Notes (from sessions.md — transcript not verified)

- Set `atomicWrites: true` on both `modeFile` and `monitorsFile` in `Workspaces.qml`.
