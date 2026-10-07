# Monitor power re-read for wake on cursor entry

- **Date**: 2026-10-06
- **CLI Tool**: Claude Code (`claude`) `2.1.292`, from `detect-runtime.sh`.
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Authorship**: Fred reported that blanked monitors no longer wake and asked for both fixes Claude proposed. Claude diagnosed and implemented them. This repository has the shell half, and `fred.workspaces` 2.0.1 has the plugin half.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> How do I wake up monitors that have gone to sleep? I used to be able to move my mouse into them or focus them, but that isn't waking them up now.

> Do both. Get the fix you just made to workspaces working. I want to test it!

## Cause

`HyprlandAdapter.qml` read `hyprctl -j monitors` once, when the shell
started, and Hyprland sends no event when an output's power changes. The
facade kept publishing `dpmsOn: true` for every monitor. `fred.workspaces`
blanked an unused monitor and recorded it as dark. On the next snapshot
revision it read the stale `dpmsOn` and dropped its dark state. Moving the
pointer into the monitor then stopped its blank timer but sent no wake.

## Work and decisions

- `rereadMonitors()` follows `rereadDevices()`. A request made while a read
  is in flight is kept and run when that read exits.
- Triggers: a focused-monitor change (pointer entry focuses the output), the
  `monitoradded` and `monitorremoved` events, and the end of the adapter's
  own `set-dpms` dispatch. A focus change starts one bounded `hyprctl`
  read. There is no polling.
- `desktop/tests/test_compositor.py` checks the triggers.

## Verification

- `desktop/tests`: 396 tests OK (one skipped).
- `qmllint` reports no errors. The isolated selftest loads the shell and
  registers all eight plugins. Its panel-order checks also fail on unmodified
  `main`.
