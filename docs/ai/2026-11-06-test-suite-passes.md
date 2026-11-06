## Session: 2026-11-06 — Make the whole test suite pass and add check-all

- **CLI Tool**: `claude` `2.1.318`
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Commits**: `0ba1e10`, `f5b2ab3`, `d7e36dc`, `8965737`, `0374d9a`, `acd6a77`
- **Authorship**: AI-assisted, directed by Fred. `0ba1e10` was written by opencode,
  which ran out of tokens before committing; Claude Code reviewed and committed it.
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Run the full test suite, record any problems, then create a plan to fix them.
  >
  > Answers to open questions:
  >
  > 1 yes
  > 2 skip with a clear reason
  > 3 delete them
  > 4 a failing suite should stop a candidate
  >
  > Update the plan. Close it if you have no further questions for me. With those questions answered, I approve the plan and authorize you to proceed.
  >
  > take care of the leftovers. Do you need anything from me to finish them up?

### Work

- A first full run found 7 of 287 units failing. Causes were tests left behind by
  D220, tests depending on the session or the machine, and a stale development
  `libtam`. None showed a defect that stops the desktop working.
- `desktop/check-all` runs the whole suite from a clean clone with session variables
  removed, and reports failures, skip reasons and core dumps left by the run.
- An imported Omarchy layout keeps its Go icon, because the person chose it.
- Tests that need `json5` skip with a clear reason where Python lacks it.
- Comparisons against `/usr/share/omarchy`, which cannot run since D200, are deleted.
  Reading the code showed that 73 of the 74 bar model skips did check our own model
  first, so they stay and now pass as ordinary tests.
- The portal proof kills the portal on its private bus before it exits, because
  `xdg-desktop-portal-hyprland` 1.4.1 segfaults during `exit()`. Retire this once the
  portal exits cleanly.
- Text people read in Explorer and `fred.keyboard` (2.0.5) no longer names the
  compositor.
- The clock proof copies the in-tree plugin, so its pinned-revision fallback,
  `clock-step1.patch` and `build_patch.py` are removed as dead code.

### Verification

At `8965737`, `desktop/check-all` passed with 290 units, no failures and no core dumps:

- In a desktop session with `--proofs`: 9 skips.
- With an empty environment: 14 skips.

At `acd6a77`, after the last two commits, it passed again with an empty-session run:
290 units, no failures, no core dumps, 14 skips; the clock proof also passed.

All skips are the `json5` tests or the opt-in proofs. The first run of this work
caused a portal crash in a private headless session, which led to the proof change.
