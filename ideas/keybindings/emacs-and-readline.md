# GNU Emacs, GNU Readline, and Spacemacs / Doom Emacs (`which-key`)

*Reference notes from documented GNU Emacs, GNU Readline (used by Bash,
GDB, Python REPL, etc.), and Spacemacs / Doom Emacs (`which-key`)
keybinding architectures.*

## What it is

- **Scope:**
  - **GNU Emacs** is the most influential chorded + prefix-key command
    environment in computing history.
  - **GNU Readline** exported Emacs's core line-editing bindings into
    thousands of UNIX shells and REPLs.
  - **Spacemacs / Doom Emacs** (`which-key`) modernized Emacs with
    discoverable **leader-key mnemonic trees** (`Space` followed by
    categorized single letters).
- **Why it matters:** Emacs invented self-documenting keybindings and
  systematic granularity (`Ctrl` = small unit, `Alt` = larger unit), while
  Spacemacs/Doom proved how mnemonic trees scale to hundreds of commands
  without finger contortions.

## Modifier semantics and chord grammar

| Pattern | Role in Emacs / Readline / Spacemacs |
| --- | --- |
| `Ctrl` + letter (Emacs/Readline) | Single-unit / primary actions, strictly mnemonic: `Ctrl+F` forward char, `Ctrl+B` backward char, `Ctrl+N` next line, `Ctrl+P` previous line, `Ctrl+A` start of line, `Ctrl+E` end of line, `Ctrl+D` delete char, `Ctrl+K` kill to end, `Ctrl+Y` yank (paste), `Ctrl+S` search, `Ctrl+R` reverse search, `Ctrl+G` cancel/quit current operation, `Ctrl+L` recenter/clear |
| `Alt` (`Meta` in Emacs) + letter | Larger-unit / secondary equivalents of the same letter! `Alt+F` forward word, `Alt+B` backward word, `Alt+D` delete word, `Alt+Backspace` delete word left, `Alt+W` copy, `Alt+Y` cycle kill-ring, `Alt+<` / `Alt+>` buffer start/end |
| Prefix trees (`Ctrl+X`, `Ctrl+C`, `Ctrl+H`) | `Ctrl+X` = global/file/window/buffer commands (`Ctrl+X Ctrl+S` save, `Ctrl+X Ctrl+C` quit, `Ctrl+X 2` split); `Ctrl+C` = mode-specific commands; `Ctrl+H` = **help prefix** (`Ctrl+H k` describe-key, `Ctrl+H b` describe-bindings, `Ctrl+H a` apropos) |
| Leader-key tree (Spacemacs / Doom + `which-key`) | Tap `Space` (in normal mode) -> live popup shows top-level categories: `f` file (`Space f s` save, `Space f f` find), `b` buffer (`Space b d` delete), `w` window (`Space w v` vertical split), `s` search, `h` help |

## Ideas worth taking

- **Parallel granularity across `Ctrl` and `Alt` on the same key — `consider`.**
  When `Ctrl+<key>` acts on a small unit and `Alt+<key>` acts on a larger
  or secondary unit (or provides the `TERM=linux` equivalent of
  `Ctrl+Navigation`), users learn half as many letters.
- **Self-documenting help system (`describe-key`, `describe-bindings`, `apropos`) — `adopt`.**
  Every Tamlinux program should be able to answer: "what does this key do,
  what are all my bindings here, and what key does X?" via `Ctrl+G`
  (`guidance`) and `tam`.
- **Mnemonic leader/prefix trees with live `which-key` popups — `consider`.**
  For secondary or less-frequent command families (where 22 `Ctrl+<letter>`
  slots are not enough), a two-key mnemonic sequence with an instant
  on-screen hint popup is far more ergonomic and memorable than
  `Ctrl+Alt+Shift+<letter>`.
- **Every key maps to a named command (`M-x`) — `adopt`.**
  Already a core principle in `arch/keybindings.md`.

## Things to avoid

- **Emacs's CUA-hostile defaults (`Ctrl+W` cut, `Ctrl+Y` paste, `Ctrl+K` kill, `Ctrl+G` cancel).**
  Fighting universal `Ctrl+X/C/V/Z` muscle memory alienates almost every
  non-Emacs user. (And Tamlinux already anchors `Ctrl+X/C/V/Z` and
  `Ctrl+G` = guidance.)
- **Modifier fatigue ("Emacs pinky").**
  Requiring `Ctrl` for basic cursor movement (`Ctrl+F/B/N/P`) was born on
  terminals without arrow keys; physical arrow keys are strictly more
  ergonomic today.
- **Cryptic notation (`C-x`, `M-x`, `^G`).**
  Tamlinux's `arch/keybindings.md` rightly bans `C-`/`M-`/`^` in favor of
  physical key names (`Ctrl`, `Alt`, `Meta`, `Shift`).

## Where to look

- GNU Emacs Manual, *Keys*, *Help*, and *Customizing Key Bindings*.
- GNU Readline Manual, *Readline Interaction*.
- Spacemacs / Doom Emacs documentation and `which-key`.
