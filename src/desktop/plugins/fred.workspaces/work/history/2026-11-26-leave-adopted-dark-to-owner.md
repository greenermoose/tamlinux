# Leave a monitor dark when the bar did not darken it (2.0.14)

- **Date**: 2026-11-26
- **CLI Tool**: Claude Code (`claude`) `2.1.332`
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Authorship**: Fred reported the toughbook not blanking and asked for the
  root cause and a fix. Claude diagnosed it on the toughbook and implemented
  the change here.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> toughbook is not screen blanking. Find the root cause and fix.

## Cause

The toughbook has one panel, and hypridle owns its blanking (DPMS off at
5 min). At 17:02 hypridle blanked eDP-1. At 18:57 the Tamlinux shell was
killed and restarted by systemd. The new bar found eDP-1 dark and adopted
that state (`probeDpmsState`, added so pointer entry can wake a monitor that
was dark when the bar was created). `trackMonitorIdle()` then took the
single-monitor branch, where per-monitor blanking is off, and woke any
monitor it believed dark: "wake (single-monitor)". Nobody had touched the
machine, so hypridle was still in its idled state and logged no resume; an
idle notification fires once per idle period, so with no input it never ran
its 300 s timeout again. The panel stayed lit from 18:57 until the next
input.

The same path woke a hypridle-blanked monitor on any host with
`unusedMonitorTimeout` 0 ("blanking-disabled"). On several monitors, the
settled in-use check woke the focused output after a restart during a
session-wide blank.

## Decisions

- The bar records whether its dark state is its own or adopted
  (`darkAdopted`). Blanking, waking and `resetIdle` clear it.
- Where the bar does no per-monitor blanking (one monitor, or timeout 0), it
  undoes only its own blank.
- On several monitors an adopted dark monitor that reads as in use is left
  dark while every output reports DPMS off: that is a session-wide blank, and
  hypridle's `on-resume` lights every output on the next input. When only some
  outputs are dark (a per-monitor blank from the previous shell), the existing
  wake on focus or windows is kept, so pointer entry still wakes it.
- The shell restart itself (SIGKILL at 18:56:57) was not diagnosed; Fred
  starts crash diagnosis.

## Verification

- `fred.workspaces` tests: 73 run, three new checks pass. One failure,
  `test_aligned_realign_leaves_focus_untouched`, fails the same way without
  this change.
- `tests.test_host` (plugin version), workspace queue, timeline, compositor
  and panel-router tests: OK. `qmllint` reports no syntax errors.
- Not yet live: the toughbook runs the 2.0.13 plugin from its installed
  Tamlinux; the fix reaches it with the next candidate Fred tests.
