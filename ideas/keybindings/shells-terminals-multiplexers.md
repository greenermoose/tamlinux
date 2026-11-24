# Shells, Terminal Emulators, Multiplexers, and Pagers / TUIs

*Reference notes from documented POSIX `termios` (`n_tty`), shells
(`bash`, `zsh`, `fish`, `nushell`/`reedline`), terminal emulators
(`xterm`, `foot`, `kitty`, `ghostty`, `wezterm`), multiplexers (`tmux`,
`screen`, `zellij`), and pagers/TUIs (`less`, `mc`, `yazi`).*

## What it is

- **Scope:** The entire text-interface stack that sits between the
  compositor and interactive terminal programs — the exact layers owned
  by `tam-last` (terminal), `tam-clam` (shell), `tam` / `tam-view`
  (guide/pager), and `tam-file` (file manager).
- **Why it matters:** Most keybinding collisions in Linux happen right
  here, where four layers (compositor, terminal emulator, kernel TTY
  line discipline, and TUI program) fight over the same `Ctrl` and `Alt`
  keys.

## Modifier semantics and chord grammar across the stack

### 1. Kernel TTY line discipline (`termios` / `n_tty`)
- When a **foreground child command** runs in cooked/signal mode (`ISIG`),
  the kernel intercepts `Ctrl+C` (`SIGINT`), `Ctrl+Z` (`SIGTSTP`), and
  `Ctrl+\` (`SIGQUIT`).
- When an interactive Tamlinux program (`tam-clam` prompt, `tam-edit`,
  `tam-view`) runs in **raw mode** (`ISIG`/`IXON` off), those bytes arrive
  as ordinary keystrokes — cleanly freeing `Ctrl+C` (Copy), `Ctrl+Z`
  (Undo), `Ctrl+S` (Save/Search), and `Ctrl+Q` (Quit).

### 2. Interactive Shells (`bash`, `zsh`, `fish`, `nushell`)
- **`bash` / `zsh`:** Default to Emacs/Readline (`Ctrl+A/E/K/U/W/R/L`,
  `Alt+B/F/D/Backspace/.`). `Ctrl+C` cancels the prompt line; `Ctrl+D`
  exits on empty prompt.
- **`fish`:** Breaks from strict Readline for better ergonomics:
  `Right` or `Ctrl+F` accepts autosuggestion, `Alt+Right` accepts one
  suggested word, `Alt+Left/Right` navigates directory history / words,
  `Alt+Up/Down` token history search, `Alt+E` edits command in `$EDITOR`,
  `Alt+S` prepends `sudo`, `Shift+Tab` / `Tab` completion.
- **`nushell` (`reedline`):** Configurable keybindings with structured
  hints, `Ctrl+R` history search, `Alt+Enter` insert newline in
  multiline prompts.

### 3. Terminal Emulators (`xterm`, `foot`, `kitty`, `ghostty`, `wezterm`)
- **The terminal-layer dilemma:** Because TUI programs own `Ctrl+<letter>`,
  Linux terminals avoid `Ctrl+<letter>` and put terminal actions
  (copy/paste, scrollback, zoom, search) on:
  - `Ctrl+Shift+<letter>` (`foot`, `kitty`, `alacritty`, `gnome-terminal`),
  - `Shift+PageUp/PageDown` (scrollback),
  - `Ctrl+=` / `Ctrl+-` / `Ctrl+0` (font zoom — clean because `=`/`-`/`0`
    are not letters!),
  - or `Super` on macOS (`ghostty`, `kitty`, `wezterm`).
- **Kitty keyboard protocol (`CSI u`):** Eliminates legacy terminal
  ambiguities (`Ctrl+H/I/J/M/[`, `Ctrl+Shift+<letter>`, key release
  events) for programs that opt in (`tam-last` P2), while `TERM=linux`
  remains bound by legacy encoding.

### 4. Terminal Multiplexers (`tmux`, `screen`, `zellij`)
- **`tmux` / `screen`:** Use a single **prefix key** (`Ctrl+B` in tmux,
  `Ctrl+A` in screen) so multiplexer commands never collide with inner
  programs (`Ctrl+B %` split, `Ctrl+B c` new window, `Ctrl+B [` copy
  mode). Cost: extra keystroke on every action, and steals `Ctrl+B`/`Ctrl+A`.
- **`zellij`:** Mode-based with an **always-visible bottom hint bar**
  (`Ctrl+P` Pane mode, `Ctrl+T` Tab mode, `Ctrl+S` Search/Scroll mode,
  `Ctrl+O` Session mode) plus **`Ctrl+G` Locked mode** (passes 100% of
  keys straight through to the inner program).

### 5. Pagers & TUI Tools (`less`, `Midnight Commander`, `yazi` / `ranger`)
- **`less`:** Read-only single-key navigation (`Arrows`/`j`/`k`,
  `Space`/`PageDown`, `b`/`PageUp`, `g`/`G` top/bottom, `/` search,
  `n`/`N` next/prev match, `h` help, `q` quit).
- **Midnight Commander (`mc`):** `F1`–`F10` function-key footer (`F1`
  Help, `F3` View, `F4` Edit, `F5` Copy, `F6` Move, `F7` Mkdir, `F8`
  Delete, `F10` Quit) — zero `Ctrl`/`Alt` collisions, works identically on
  `TERM=linux` and graphical terminals!
- **`yazi` / `ranger`:** Single-key navigation + `g` "go to" mnemonic
  prefix (`g h` home, `g c` config, `g d` downloads).

## Ideas worth taking

- **Clean raw-mode vs. foreground-child split (already in `arch/keybindings.md`) — `adopt`.**
  Letting `Ctrl+C`/`Ctrl+Z` act as Copy/Undo inside `tam-clam` (raw mode)
  while preserving kernel `VINTR`/`VSUSP` when a foreground child runs
  solves the 40-year Linux terminal CUA collision cleanly.
- **Fish's `Alt+Enter` multiline newline & autosuggestion acceptance (`Right` / `Alt+Right`) — `adopt`.**
  Natural, ergonomic, and works on both graphical terminals and `TERM=linux`.
- **Non-letter terminal chords (`Ctrl+=`/`-`/`0` zoom, `Shift+PageUp/Down` scrollback) — `adopt`.**
  Zero collision with application `Ctrl+<letter>` bindings!
- **Zellij's pass-through / locked concept — `consider`.**
  When running nested SSH or third-party TUI apps inside `tam-last`, a
  clear way to pass keys untouched avoids layer fights.
- **Midnight Commander's `F1`–`F10` reliability on `TERM=linux` — `consider`.**
  Function keys are completely free of legacy ASCII `Ctrl` collisions and
  work identically on every text console and graphical terminal.

## Things to avoid

- **Stealing `Ctrl+A` or `Ctrl+B` as a multiplexer prefix.**
  With `tam-pane` handling window tiling and grouping natively, Tamlinux
  does not need a terminal multiplexer prefix eating primary `Ctrl` keys.
- **Terminal emulators binding `Ctrl+Shift+<letter>` as the *only* way to copy/paste.**
  Creates an inconsistent experience with GUI apps and cannot survive
  legacy encoding.
- **Divergent search/quit keys between pagers (`less`) and editors.**
  In `tam` and `tam-view`, `Ctrl+F` (find), `Ctrl+G` (guidance), and
  `Ctrl+Q` / `Escape` (quit/back) should work alongside any convenient
  read-only single-key shortcuts (`/` and `q`).

## Where to look

- `tam-last/arch/key-path.md`, `tam-last/ideas/synthesis.md`, and
  `tam-clam/ideas/synthesis.md`.
- Kitty Keyboard Protocol specification (`sw.kovidgoyal.net/kitty/keyboard-protocol/`).
- Fish Shell, Zellij, `less(1)`, and `mc(1)` documentation.
