# Latest accepted desktop intent and native logger probe

- **Date:** 2026-11-10.
- **CLI Tool:** Codex CLI (`codex`) `0.167.0` (checked live).
- **Model:** `gpt-6.1-sol` (verified in current runtime metadata).
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted code, tests and documentation directed by Fred.
- **Prompt:**
  > Continue Develop from Plan 54.

Advances `fred.workspaces` to 2.0.9 in Develop. Persist desired desktop
intent separately from observed completion, accept explicit switch intent
before waiting for the command lock, reject stale completion/follow events
and bound superseding attempts. Failed CLI switches return nonzero. Added
isolated regressions with temporary state and fake compositor operations.

Added a small C++ probe of the installed Hyprutils logger and named backend
connection. Synthetic errors reached the journal with native subsecond wall
timestamps; the small output file remained buffered until logger destruction.
Probe payload clocks do not establish monotonic emission in production logs.
Source inspection identifies the current Lua workspace-selection focus
limitation. No compositor dispatch, activation, native install, session
restart, candidate change or log deletion was performed.

Verification and limits are recorded in the
[development handoff](../plans/steady-active-monitor.md#latest-accepted-desktop-intent-209).

- 32 isolated workspace timeline/intent tests pass (19 new intent cases).
- 69 existing workspace plugin tests pass.
- The broad desktop run executed 836 tests with 14 skipped. Its single
  failure was the QML version declaration; after correcting it to 2.0.9,
  all 35 host/metadata tests pass in the affected-suite rerun.
- The widget offscreen render passes at 126.5 × 26 with no problems.
- The C++ logger probe compiles against Hyprutils 0.14.2 and runs through
  the user journal; debug records are filtered and all three synthetic
  errors appear on stdout/journal and, on destruction, in the output file.
- `git diff --check` and the public provenance scan pass.

Active-output-first placement, focus-preserving side repair, bar queue
coalescing and native logging corrections remain open. Physical continuity
requires a future exact packaged candidate and Fred's Test instruction.
