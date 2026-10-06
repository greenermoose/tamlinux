# 2026-10-05 — Keybinding viewer in the Tamlinux shell

- **CLI Tool**: Claude Code `2.1.290`.
- **Model**: `claude-opus-5-5`.
- **Transcript**: Retained privately by the author.
- **Stage**: Run; Fred tested and accepted 0.2.2 for daily use.
- **Prompts** (excerpt):
  > Work on tamlinux 0.2.2, keybinding viewer. Delegate what you can to opencode and agy. Check the work done so far, and plan ahead so that we are using our time and tokens efficiently to port over functionality to tamlinux from omarchy, without doing unnecessary work but keeping the functionality of this system high. Ask if you have questions.
- **Behaviour chosen by Fred**:
  > Enter should run the shortcut.
  >
  > Don't replicate Omarchy's sorting. I find it impossible to understand their sort order. Alphabetical would be more sensible in my opinion, unless you can come up with a better approach.

## Decisions and implementation

- The rows come from the compositor facade's bindings (`KeybindingsModel.js`,
  pure functions loadable under Node), served over the shell's `keybindings`
  IPC target. The caller supplies each binding's command, because Hyprland's
  Lua bindings do not report it.
- Order: case-insensitive by what the binding does, numbers compared as
  numbers, then by keys.
- Running a binding by simulating its keys was tested and rejected: the
  simulated keyboard's own keymap made Hyprland fire a different binding.
- The Hyprland adapter reads its bindings again on `configreloaded`; reads
  had been one-shot, and the snapshot is republished on every read.

## Verification

Desktop tests: 66 passed; configuration tests: 301 passed. Live rows matched
the inherited viewer's 252 rows, commands included. Fred tested the key, the
menu entry, search, Escape and Enter, and accepted 0.2.2.
