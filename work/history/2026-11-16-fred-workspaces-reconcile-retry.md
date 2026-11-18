# fred.workspaces output-change retry renewal

- **Date:** 2026-11-16
- **Tool:** Claude Code 2.1.325
- **Model:** claude-opus-5-5
- **Transcript:** Retained privately by the author.

## Request

> Yes, look into both of those.

> Codex says it wants you to do the fixes. I'm working with it to the package and test after you land the fixes.

The first prompt followed a report that the HP (HDMI-A-1) had shown
workspace 1 for hours instead of the current desktop's workspace.

## Finding

Each wake, the HP drops HPD and returns about a second later. The output-change
reconcile reapplied the current desktop request, but it also reused that
request's per-output budget (three attempts within three seconds of the
original placement). Hours later every misaligned output was already past its
deadline, so the reconcile logged `retry-expired` and dispatched nothing. The
user journal showed this on every wake from 2026-11-15 19:38 to 2026-11-16
09:56: expected `DP-2:4 DP-1:5 HDMI-A-1:6`, observed `3 2 1`, result partial.

## Change

`switch_windows` now gives an output a fresh bounded budget when its last
recorded result was `aligned` or `missing` and it is now present on the wrong
workspace. That state means something displaced it after it was placed, or it
came back after an absence; neither is a retry of a rejected placement. It
logs `retry-renewed`. Outputs whose result is `pending` or `expired` keep
their spent budget, so duplicate events cannot renew retries of a rejection.
Dark-output deferral, persist-before-IPC, focus-preserving placement and
stale-generation rejection are unchanged. Clicking the bar to realign one
monitor goes through the same path, so it also works after the first three
seconds. `fred.workspaces` is 2.0.12.

## Evidence

New cases in `desktop/tests/test_workspace_retry.py`:

- A drop and return after the deadline gets a fresh budget and ends aligned.
- A renewed budget stays at three attempts per output across eight duplicate
  events.
- A dark desktop still defers.

The first two failed before the change. The 60 `desktop/tests/test_workspace_*`
tests and the 69 plugin tests pass. One plugin test,
`test_aligned_realign_leaves_focus_untouched`, reads the live `desktop-intent`
state file and fails whenever the live desktop is not 1. It fails the same way
without this change, and passes with `XDG_STATE_HOME` set to an empty
directory. The full desktop suite and physical acceptance have not been run.
