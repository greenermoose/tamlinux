# Pop!_OS and System76 COSMIC

*Reference notes from documented Pop!_OS (Pop Shell) and System76 COSMIC
Epoch 1 (Rust/Wayland `cosmic-comp`) defaults.*

## What it is

- **Scope:** Pop!_OS is an actively maintained Linux distribution by
  System76; COSMIC is its clean-slate Rust/Wayland desktop environment and
  compositor (`cosmic-comp`), designed from the ground up to unify floating,
  auto-tiling, and tabbed window stacking under one coherent keybinding map.
- **Why it matters:** COSMIC is one of the very few modern Linux desktops
  to rethink desktop keybindings from first principles rather than
  inheriting 1990s X11 defaults.

## Modifier semantics and chord grammar

| Modifier | Role in COSMIC / Pop!_OS |
| --- | --- |
| `Super` (`Meta`) + navigation | Focus window (`Super+Arrows` and `Super+H/J/K/L`), switch workspace (`Super+1..9`, `Super+Ctrl+Up/Down` or `Super+Ctrl+Left/Right`) |
| `Super+Shift` + navigation | Move window in direction (`Super+Shift+Arrows` / `HJKL`), move window to workspace (`Super+Shift+1..9`) |
| `Super` + letter/symbol | Cohesive compositor actions: `Super+/` launcher, `Super+Q` close window, `Super+M` maximize, `Super+G` toggle floating/tiling, `Super+Y` toggle auto-tiling, `Super+O` toggle split orientation, `Super+S` toggle window stacking (tabs), `Super+T` terminal, `Super+F` files, `Super+B` browser, `Super+W` workspaces overview, `Super+Escape` lock |
| `Super+Enter` | Enter **Adjustment Mode** (modal submap: arrows resize, `Shift+Arrows` swap, `Enter`/`Escape` exit) |
| `Ctrl` + letter | Standard CUA inside applications |
| `Ctrl+Shift` + letter | COSMIC Terminal (`cosmic-term`) copy/paste and tabs |

## Ideas worth taking

- **Pure `Super`/`Meta` ownership of the compositor — `adopt`.**
  COSMIC moves nearly all window, tiling, stacking, and workspace control
  onto `Meta` (+ `Shift` for move, + `Ctrl` for workspaces/monitors),
  eliminating most `Alt+F4` / `Ctrl+Alt` sprawl.
- **Clean directional symmetry (`Meta` = focus, `Meta+Shift` = move) — `adopt`.**
  One modifier rule (`Shift` = "carry the window with me") applies
  uniformly to arrows and numbered workspaces.
- **First-class mnemonic single-letter compositor chords — `consider`.**
  `Meta+Q` close, `Meta+T` terminal, `Meta+F` files, `Meta+B` browser,
  `Meta+O` orientation, `Meta+S` stack — short (2-key) and easy to recall.
- **Modal Adjustment Mode (`Meta+Enter`) for resizing — `consider`.**
  Entering a brief, clearly indicated resize mode with plain arrows avoids
  burning 6–12 permanent global chords on fine/coarse resizing (compare
  Tamlinux's current `Meta+,/./;/'` + `Alt`/`Ctrl` resize family).

## Things to avoid

- **Overloading `Super+H/J/K/L` alongside arrows as permanent defaults.**
  Binding `H/J/K/L` to directional focus steals four prime mnemonic
  letters (`H` help/history, `L` lock/layout, `K` keybindings) from users
  who use physical arrow keys.
- **Keeping `Ctrl+Shift+C/V` in `cosmic-term`.**
  Even a clean-slate Rust desktop left the terminal copy/paste split
  unresolved.

## Where to look

- System76 `cosmic-comp` and `cosmic-settings-daemon` default shortcut
  tables (`github.com/pop-os/cosmic-comp`).
- Pop!_OS Support, *Keyboard Shortcuts*.
