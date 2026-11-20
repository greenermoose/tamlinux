# Count down again after a monitor is lit from elsewhere (2.0.13)

- **Date**: 2026-11-18
- **CLI Tool**: Claude Code (`claude`) `2.1.327`, from `detect-runtime.sh`.
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Authorship**: Fred saw two blanked monitors come on at a wake and asked
  for the causes to be fixed. Claude diagnosed and implemented the plugin and
  shell halves here; the idle daemon change is in Fred's host configuration.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Why did two monitors just come on?

> The wake command switching on every monitor is a bug. Note it and fix it.

> Fix both of those, too.

## Cause

This bar marks its own blank unconfirmed until the shell facade reports the
monitor dark, and until then ignores "lit" reports as stale (2.0.1). Hyprland
sends no DPMS event, so the facade learns of a blank only on its next monitor
read. That read comes with focus moving to another output or an output being
added or removed. Overnight none of those happened, so the blank of DP-2 was
never confirmed. When the idle daemon lit every monitor in the morning, the
lit report was discarded, DP-2 kept a dark state it did not have, and its
unused countdown never started again.

## Decisions

- The helper's completed `dpms-off` is the confirmation. The shared queue
  runs every helper on the first bar, so `ActionQueue.finished` takes the
  helper's success and notifies every bar; the bar whose output it was
  clears `blankUnconfirmed`. A failed helper confirms nothing.
- The shell gains a `compositorRefresh` IPC and `Compositor.refreshOutputs()`,
  which re-read the outputs, so an idle daemon that changes DPMS behind the
  shell's back can say so. No polling was added.

## Verification

- `python3 -B -m unittest discover -s desktop/tests -q`: 870 tests, OK
  (14 skipped), including a new queue test that a completed `dpms-off`
  reaches the bar owning the output and a failed one does not.
- `fred.workspaces` tests: 70 OK, including a new check that helper
  completion confirms the blank.
- Not yet live: the change reaches Fred's session with the next Tamlinux
  candidate.
