# Reset backend import fix (2.0.1)

- **Date**: 2026-10-06
- **CLI Tool**: Claude Code (`claude`) `2.1.292`, from `detect-runtime.sh`.
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Authorship**: Fred reported the failure and asked for the root cause, a fix, and the 2.0.1 bump. Claude found the cause, made the change, and checked it on Fred's MSI display.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompt

> Resetting the MSI monitor failed. Please find the root cause and fix in fred.monitor v2.0.0. Bump to v2.0.1 when you do.

## Cause

`fred-monitor-reset` ran the Tamlinux backend as
`python3 -I <host>/hyprland_backend.py`. Isolated mode leaves the script's
own directory off `sys.path`, so the backend's `import compositor_commands`
raised `ModuleNotFoundError`. The helper sent that error to `/dev/null`,
treated the empty read as `[]`, and reported `Monitor 'DP-2' is not
connected`. The panel showed "Failed — press again". The layout and state
helpers were not affected because they load both modules by file path.

## Work and decisions

- The helper still runs Python in isolated mode. It puts only the backend
  directory on `sys.path` and calls `hyprland_backend.main`. `sway_snapshot.py`
  in Tamlinux does the same. `-B` keeps the run from writing bytecode next to
  the backend.
- The helper now checks that the backend directory is absolute and contains
  both modules.
- A failed monitor read reports `cannot read monitors from the compositor`,
  not `not connected`.
- `tests/test_reset.py` runs the helper against a stand-in backend that
  imports a sibling module. Both tests fail on 2.0.0.

## Verification

- The panel's closed environment reproduced the failure on 2.0.0
  (`Monitor 'DP-2' is not connected`, exit 1).
- With the fix and live actions on, DP-2 modeset to 59.94 Hz and back to
  60.00 Hz. Both modesets were confirmed in the compositor log, and the
  position and scale were unchanged.
- Python suite 19 tests OK; `tests/model.test.cjs` 11 pass.
