# Session: 2026-10-04 — Clipboard service in the Tamlinux host

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Next is R4.3, clipboard. It moves Omarchy's clipboard history, and the two
  > background wl-paste processes that feed it, into the Tamlinux host. It works
  > like the notifications move: only one clipboard history should run at a
  > time, so Omarchy's is switched off when this one takes over. Please start it
  > now.

## Key decisions and implementation notes

- The clipboard service, its history model, its capture script, and two UI
  helpers (the clear-history confirmation and the pointer-movement filter) are
  vendored from the Omarchy 4.0.4 shell with the MIT notice. Behavior is kept:
  300 entries, text and PNG watchers restarted if they exit, sensitive
  selections skipped, and the picker's keys.
- The paste and open helpers are vendored too and sit beside the service, so
  the host runs nothing outside its own tree. The open helper starts each
  program through `uwsm-app` in its own scope, so it outlives a restart of the
  services unit. It opens URLs with `xdg-open` and text with `$VISUAL` or
  `$EDITOR` through `xdg-terminal-exec`.
- History and images live under `~/.local/state/tamlinux/clipboard/`, which
  the capture script creates with mode 0700. The service finds its helpers
  through `Quickshell.shellDir`, and it reaps only watchers that run its own
  capture script.
- `Tam.Commons` gained `Color.menu` surface tokens, and `Tam.Ui.BorderSurface`
  gained content insets, for this picker and the pickers that follow.
- The IPC target is `clipboard` (`toggle`, `open`, `close`, `count`, `ping`).

## Verification

- `python3 -m unittest discover -s desktop/tests`: 56 tests pass.
- A copy of the host ran in a headless nested Sway session with
  `TAMLINUX_BAR=0 TAMLINUX_SERVICES=clipboard` and a scratch state directory,
  so the workstation's clipboard and keyboard were not touched. Both watchers
  started; copied text was recorded, a repeat moved to the top, a sensitive
  copy was skipped, and a PNG was stored with mode 0600. Through IPC and
  synthetic keys, the picker opened, filtered, pasted a text entry (Enter),
  copied an image entry as `image/png` (Shift+Enter), deleted an entry, and
  showed and cancelled the clear-history confirmation. Screenshots matched the
  source layout.
- With the launcher stubbed, the open helper sent a URL to `xdg-open`, text
  to the editor in a terminal, and an image to the image editor, and it
  rejected out-of-range and non-numeric indexes.
- Stopping that host also stopped its watchers.
