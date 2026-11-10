# Workspace helper timeline and initial continuity regressions

- **Date:** 2026-11-10.
- **CLI Tool:** Codex CLI (`codex`) `0.167.0` (checked live).
- **Model:** `gpt-6.1-sol` (checked in current runtime metadata).
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted implementation, tests and documentation directed
  by Fred after approval of the public implementation plan.
- **Prompt:**
  > begin Develop from Plan 54

Implemented `fred.workspaces` 2.0.8: compact helper events with emission wall
and monotonic time, observational sequences, reasons and output context;
line forwarding through the shell logger; and truthful incomplete
reconciliation results with nonzero exit status. Existing placement, layout
and desktop-state semantics remain for the next implementation slice.

Added isolated event regressions using temporary state and a fake backend.
They reject direct process launches and clear inherited session variables.
Read-only native inspection confirmed the logger settings and the connector
identity gap in both Aquamarine commit errors. No native patch, activation,
candidate change, physical display trial or log deletion was performed.

Verification:

- 13 new workspace timeline tests pass.
- Full desktop suite: 817 tests pass, 14 skipped.
- 69 existing workspace plugin tests pass.
- `desktop/widget-proof fred.workspaces`: passes, 126.5 × 26, no problems.
- 148 panel model tests pass in isolation after the first broad suite was
  interrupted by its 120-second wrapper; that run returned 124 and reported
  one Node-process failure in an unrelated keyboard-label test.
  The full rerun without that wrapper passed in 209 seconds.
- `git diff --check`: passes.

This slice does not establish native journal/file timestamps, physical
continuity or shared latest intent. See the
[development handoff](../plans/steady-active-monitor.md#development-handoff).
