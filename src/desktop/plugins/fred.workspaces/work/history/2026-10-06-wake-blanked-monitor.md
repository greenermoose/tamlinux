# Wake a blanked monitor on cursor entry (2.0.1)

- **Date**: 2026-10-06
- **CLI Tool**: Claude Code (`claude`) `2.1.292`, from `detect-runtime.sh`.
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Authorship**: Fred reported that blanked monitors no longer wake and asked for both fixes Claude proposed. Claude diagnosed and implemented them. This repository has the plugin half; the Tamlinux shell has the other.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> How do I wake up monitors that have gone to sleep? I used to be able to move my mouse into them or focus them, but that isn't waking them up now.

> Do both. Get the fix you just made to workspaces working. I want to test it!

## Cause

In 2.0.0 the dark state comes from the shell facade's `dpmsOn`. The shell
read monitor power only at startup and kept reporting every monitor lit.
After this bar blanked its monitor, the next snapshot revision made
`probeDpmsState` log `monitor is lit; dropping stale dark state` and clear
`isMonitorDark`. Focus or pointer entry then stopped the blank timer but
never ran `dpms-on`.

## Work and decisions

- `blankUnconfirmed` is set when this bar blanks its monitor and cleared
  when the facade reports it dark, on wake, and on `resetIdle`. While it is
  set, a lit report is ignored. A lit report after the facade has seen the
  blank still clears the dark state, so a monitor woken by hypridle can
  blank again on schedule.
- The shell now reads monitor power again on focus changes, so the facade
  usually confirms the blank as the pointer enters. The guard covers the
  time before it does.
- `tests/test_idle_dark.py` reads the QML, like `tests/test_mode_watch.py`.
  Its three tests fail on 2.0.0.

## Verification

- `python3 -m unittest discover -s tests`: 53 tests OK.
