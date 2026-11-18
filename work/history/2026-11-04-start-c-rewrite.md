## Session: 2026-11-04 — Rewrite start as C 0.2.x (D224)

- **CLI Tool**: Cursor (`cursor`) `3.27.22`
- **Model**: `composer`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Rewrite start as a C program for version 0.2.x and on. As with tam, separate the pager from the text the pager displays. The start menu should be either a JSON or a CSV file; something easy to edit and see.
  >
  > Decide which repo should include start.
  >
  > Make a note so that agents know that start is no longer a python script. I do not want any dependencies for start other than our C libraries. start must work on systems that don't have a python interpreter.

### Work

Rewrote `commands/start` from a Python TUI to a pure C binary linked only
against `libtam` (and libc). Menu catalog moved to `menu.json`. Version
landed at 0.2.4 after footer EL truncation fixes and Esc-as-quit.
Orientation entries became Guides & References (`tam show` / `explain` /
glossary / `man` / `info` / `tldr`). Packaging drops the Python runtime wrap
and builds `start` as a native payload. Recorded D224; updated the
first-login plan, component README, and developing-tamlinux-components
runbook note.
