# Session: 2026-10-04 — Emoji picker in the Tamlinux host

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Take the next step on the tamlinux project. Ask if you have questions.

## Key decisions and implementation notes

- The next step in the private plan was the emoji picker, the fourth Omarchy
  shell function to move into the host. The picker, its search module, its
  emoji list, and the insert helper are vendored from the Omarchy 4.0.4 shell
  with the MIT notice. Behavior is kept: keyword search, the grid's arrow,
  Page Up/Down, and Escape keys, and insertion by a sensitive selection and
  Shift+Insert, so the clipboard history does not record the emoji.
- The search-editing keys (Backspace, Ctrl+Backspace, Ctrl+U) are defined in
  the service, as the clipboard picker does, because `Tam.Commons` has no
  shared helper for them.
- The service finds its list and helper through `Quickshell.shellDir`. It uses
  the `Color.menu` tokens the clipboard picker added. The IPC target is
  `emojis` (`toggle`, `open`, `close`, `count`, `ping`); the layer is
  `tamlinux-emojis`.

## Verification

- `python3 -m unittest discover -s desktop/tests`: 57 tests pass.
- A copy of the host ran in a headless nested Sway session with
  `TAMLINUX_BAR=0 TAMLINUX_SERVICES=emojis`, so the workstation's clipboard
  and keyboard were not touched. It loaded 1,870 emojis. Through IPC and
  synthetic keys, the picker opened, filtered on "heart", edited the search
  with Backspace, moved with the arrow keys, and typed the selected emoji
  into a terminal in that session; the bytes matched the selected emoji, and
  the temporary selection process exited. Escape cleared the search, then
  closed the picker. Screenshots matched the source layout.
