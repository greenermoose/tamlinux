# elementary OS (Pantheon / Gala)

*Reference notes from documented elementary OS 7/8 (Pantheon desktop, Gala
window manager) Human Interface Guidelines.*

## What it is

- **Scope:** elementary OS is an actively maintained Linux distribution
  famous for its strict, cohesive Human Interface Guidelines (HIG) modeled
  in spirit on macOS — emphasizing simplicity, consistency, and built-in
  discoverability across all first-party apps.
- **Why it matters:** Shows how a Linux desktop can enforce a rigorous
  app-wide HIG and make keybindings self-teaching.

## Modifier semantics and chord grammar

| Modifier | Role in elementary OS (Pantheon) |
| --- | --- |
| `Super` (`Meta`) tap | Opens the **Shortcut Overlay** (a clean, full-screen cheat sheet of desktop shortcuts) or Application Menu (configurable; shortcut overlay was long the default) |
| `Super` + key | Desktop & Gala window management: `Super+Space` Applications menu, `Super+Down` Multitasking view, `Super+Up` maximize, `Super+Left/Right` switch workspaces, `Super+1..9` workspace N, `Super+A` Picture-in-Picture, `Super+L` lock, `Super+W` show all windows |
| `Super+Alt` + Left/Right | Tile window left/right |
| `Ctrl` + letter | Strict CUA across all Pantheon apps (`Ctrl+X/C/V/Z`, `Ctrl+Shift+Z` redo, `Ctrl+N` new, `Ctrl+W` close tab/window, `Ctrl+Q` quit, `Ctrl+F` find, `Ctrl+,` preferences) |
| `Ctrl+Shift` + letter | Pantheon Terminal (`io.elementary.terminal`) copy/paste — though elementary's terminal famously added **smart `Ctrl+C`/`Ctrl+V`** (if text is selected, `Ctrl+C` copies; if nothing is selected, `Ctrl+C` sends `SIGINT`)! |

## Ideas worth taking

- **Smart `Ctrl+C` / `Ctrl+V` in the terminal — `consider`.**
  elementary Terminal was one of the first Linux terminals to tackle the
  `Ctrl+C` collision directly: when text is selected, `Ctrl+C` copies;
  otherwise it passes `Ctrl+C` (`SIGINT`) through. Worth comparing closely
  against Tamlinux's `arch/keybindings.md` rule (`Ctrl+C` = Copy at the
  `tam-clam` prompt, `SIGINT` while a foreground child runs).
- **First-class Shortcut Overlay on demand — `adopt`.**
  Making the cheat sheet a primary OS feature rather than a buried wiki
  page aligns directly with Tamlinux's `Meta+K` explorer and `Ctrl+G`
  (`guidance`).
- **Strict HIG consistency across all native apps — `adopt`.**
  Every Pantheon app obeys the exact same `Ctrl+Q` / `Ctrl+W` / `Ctrl+,` /
  `Ctrl+Shift+Z` contract.

## Things to avoid

- **Overloading `Super+Left/Right` for workspaces instead of window focus/tiling.**
  When `Super+Left/Right` switches workspaces, window tiling gets pushed
  to `Super+Alt+Left/Right`, breaking the simple directional hierarchy
  (and in Tamlinux, `Meta+Alt` is reserved for text macros under P29).
- **Ambiguity in smart `Ctrl+C` when a user expects `SIGINT` with an accidental selection.**
  If a user accidentally highlighted a word and hits `Ctrl+C` to stop a
  runaway command, swallowing `SIGINT` can be surprising. Clear state
  separation (prompt vs. running child) is safer than selection-dependent
  interception during a running command.

## Where to look

- elementary OS Human Interface Guidelines, *Keyboard Shortcuts*.
- `io.elementary.terminal` (Natural Copy/Paste feature) and `gala`
  shortcut schemas.
