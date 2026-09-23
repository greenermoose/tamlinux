# Session: 2026-09-17 — Per-Monitor Idle Blanking of Unused Monitors (v1.5.0)

- **Primary AI Agent**: Antigravity CLI (`agy`)
- **Primary Model**: Gemini 3.8 Flash (High) — confirmed from `USER_SETTINGS_CHANGE` in transcript
- **agy version**: Not self-reported in transcript. `1.2.5` stated in sessions.md; a commit
  `64d77d5` on this date is titled "correct Antigravity CLI version to 1.2.5 in provenance
  records", suggesting the author confirmed 1.2.5 at the time, but it is not confirmed from
  the transcript itself.
- **Transcript**: Antigravity `b406cca2-7398-4b2f-ad9d-0901cd85cbb8`
- **Session start**: 2026-09-17T13:57:54-04:00 (from transcript)
- **Commits**: `d6cdd58` (2026-09-17 17:08 — v1.5.0),
  `64d77d5` (2026-09-17 17:14 — provenance correction),
  `1b3b890` (2026-09-18 10:16 — ecosystem docs)

## Prompts (verbatim from transcript)

> **Fred:** "Update the private priorities backlog. Look to see what we've already done so completed projects don't keep appearing. Determine what more we need to do."

> **Fred:** "For per-monitor blanking, I need more info to know whether to poll hyprctl cursorpos only or trigger strictly on Hyprland events. I need to see the pros and cons of a Quickshell service versus a systemd user daemon."

> **Fred:** "Let's tackle #4 first. I choose Part A option 1, strictly event-driven (socket2), and Part B option 1 Quickshell service plugin. Is this a separate plugin or should it be wrapped up to be part of fred.workspaces? It does seem related to the concern of fred.workspaces, which is managing what my monitors are showing at any given moment."

> **Fred:** "Proceed."

> **Fred:** "A key priority is energy efficiency. Remember that: any solution that involves using more energy or power I will reject unless it is unavoidable."

## Key Decisions & Implementation Notes

- Strictly event-driven: zero background polling, avoiding CPU wakeups and preserving
  deep C-states.
- Wrapped into `fred.workspaces` BarWidget (`Workspaces.qml`); each bar monitors its own
  display's activity (`barMonitor`).
- Screen is "in use" when it has focus or visible workspace has windows
  (`toplevels.values.length > 0`). Empty workspace with focus elsewhere starts
  `idleBlankTimer` (default 300s, configurable via `unusedMonitorTimeout`, 0 to disable).
- DPMS power-down via `omarchy-desktop-mode dpms-off <MON>`.
- Immediate wake on cursor entrance, workspace change, or window creation/movement.
- Fault C protection: cold wake of `DP-2` triggers `msi-mp161-resume-workaround --once`
  in background via `subprocess.Popen`.
- Added `IpcHandler` with `resetIdle` to re-arm countdowns on system S3/DPMS resume.

## Verification

- 39/39 unit tests pass in `tests/test_desktop_mode.py`.
