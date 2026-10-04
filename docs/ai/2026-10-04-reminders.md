# Session: 2026-10-04 — Reminders in the Tamlinux host

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Take the next step on the tamlinux project.

## Key decisions and implementation notes

- The next step in the private plan was reminders, the sixth shell function
  to move into the host. The reminder card and its minutes model are vendored
  from the Omarchy 4.0.4 shell with the MIT notice, and the reminder command
  becomes `reminder.sh` beside the service, so the host calls nothing outside
  its own tree. The IPC target is `reminders` (`toggle`, `open`, `close`,
  `ping`); the layer is `tamlinux-reminders`.
- Behavior is kept: minutes, then an optional message; an invalid number
  shows a notification and keeps the card open; Escape clears, then closes.
  Each reminder is a transient user timer that sends a notification, and
  `show`, `show --json`, and `clear` list or stop them.
- Changes in the helper: timers are named `tamlinux-reminder-*` and messages
  live under `$XDG_RUNTIME_DIR/tamlinux-reminders/`; notifications are sent
  with `busctl` as typed D-Bus values (no `notify-send` argument parsing);
  minutes are read as decimal, so `08` means eight rather than an error, and
  are capped at 99999; the unit name carries the process ID, so two reminders
  set in the same second do not collide; the timer runs the helper's `due`
  step, which deletes only its own message file.
- The search-editing keys are defined in the service, as in the clipboard
  and emoji pickers.

## Verification

- `python3 -m unittest discover -s desktop/tests`: 59 tests pass.
- The helper ran with `systemd-run`, `systemctl`, and `busctl` replaced by
  recording stubs and a scratch runtime directory: set with and without a
  message (a message of `--hint=x $(touch PWNED)` arrived as one typed value
  and nothing ran), rejected `0`, `00`, `abc`, `100000`, `-3`, and an empty
  value, listed two active timers in text and JSON (skipping an elapsed one),
  stopped every timer and its service on `clear`, and refused to delete a
  file outside its directory in `due`.
- A copy of the host ran in a headless nested Sway session with
  `TAMLINUX_BAR=0 TAMLINUX_SERVICES=reminders` and the same stubs. Through
  IPC and synthetic keys: the card opened; `12a` and Enter sent the invalid
  notification and kept the card; Backspace and Enter moved to the message
  step; a message and Enter closed the card and set a 12-minute timer with
  that message; Escape cleared the entry, then closed the card; Enter on an
  empty entry closed it. Screenshots matched the source layout.
