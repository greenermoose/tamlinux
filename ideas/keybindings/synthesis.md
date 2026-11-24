# Synthesis: Keybinding Systems Across OSes and Programs

Start here. This document distills the survey in `tamlinux/ideas/keybindings/`
into a modifier comparison matrix, the five recurring failure modes in
existing systems, concrete takeaways (`adopt` / `consider` / `reject`),
and the open design tensions to resolve in [`../../arch/keybindings.md`](../../arch/keybindings.md).

## 1. Cross-system modifier semantics matrix

| System | OS / Compositor | Primary App Actions | Secondary / Larger Unit | Selection / Reverse | Terminal / Kernel TTY |
| --- | --- | --- | --- | --- | --- |
| **Windows / CUA** | `Win` + legacy `Alt+Tab`/`Alt+F4` | `Ctrl+letter` | `Ctrl+Nav` (word/doc), `Alt` menus | `Shift+Nav`, `Shift+Tab` | Collides on `Ctrl+C/V` in terminals |
| **macOS (Apple HIG)** | `Cmd+Tab`/`Space` (shared with apps) | `Cmd+letter` | `Opt+Nav` (word), `Cmd+Nav` (line/doc) | `Shift+Nav`, `Cmd+Shift` (reverse/redo) | `Ctrl` cleanly preserved for POSIX + Emacs line-edit |
| **GNOME (Fedora / Ubuntu)** | `Super` + `Alt+F4` + `Ctrl+Alt+T` | `Ctrl+letter` | `Ctrl+Nav`, `Alt` menus | `Shift+Nav`, `Ctrl+Shift+Z` | Terminal retreats to `Ctrl+Shift+C/V` |
| **KDE Plasma** | `Meta` + `Alt+F4` + `Ctrl+Alt` | `Ctrl+letter` (`KStandardShortcut`) | `Ctrl+Nav`, `Alt` menus | `Shift+Nav`, `Ctrl+Shift+Z` | Konsole retreats to `Ctrl+Shift+C/V` |
| **Linux Mint (Cinnamon)** | `Super` + `Ctrl+Alt+Arrows` + `Alt+F4` | `Ctrl+letter` | `Ctrl+Nav` | `Shift+Nav` | Terminal retreats to `Ctrl+Shift+C/V` |
| **Pop!_OS (COSMIC)** | `Super` (`+Shift` move, `+Ctrl` ws, `+Enter` resize mode) | `Ctrl+letter` | `Ctrl+Nav` | `Shift+Nav` | `cosmic-term` retreats to `Ctrl+Shift+C/V` |
| **elementary OS (Pantheon)** | `Super` (tap = shortcut overlay) | `Ctrl+letter` | `Ctrl+Nav` | `Shift+Nav`, `Ctrl+Shift+Z` | Smart `Ctrl+C` (copy if selected, else `SIGINT`) |
| **Tiling WMs (i3/Sway, Niri, Hyprland, Regolith)** | `Meta`/`Super` exclusively (`+Shift` move, `+Ctrl` group/ws) | App-defined | App-defined | App-defined | Terminal-defined |
| **Linux Rootstocks & VT (`TERM=linux`)** | Kernel steals `Alt+F*`, `Alt+Left/Right`, `Ctrl+Alt+F*`, `Alt+SysRq`; `Meta` not sent | `Ctrl+<22 clean letters>` | `Alt+<char>` (`ESC <char>`) | `Shift+Nav` not distinguished | `termios` (`Ctrl+C/Z/\/D/U/W/S/Q`) |
| **BSD UNIX (FreeBSD, OpenBSD, NetBSD)** | `Ctrl+Alt+F*` VT; OpenBSD `cwm` uses `Ctrl+Alt` | `ksh`/`tcsh` Emacs or vi | `Alt` / `Esc` | App-defined | POSIX `termios` + **`Ctrl+T` (`SIGINFO`)** |
| **illumos / SVR4 / Motif-CDE** | `Alt+F4` / `Alt+Tab` | `Ctrl+Ins`/`Shift+Ins`/`Shift+Del` clipboard | `Alt` menus, Sun dedicated keys | `Shift+Nav` | POSIX `termios` (`Ctrl+V` literal-next) |
| **Lisp Machines (Genera)** | `Super` | `Control` | `Meta` (larger unit), `Hyper` (user) | Dedicated keys | Unified OS command loop |
| **Emacs / Readline / Spacemacs** | — | `Ctrl+letter` / `Space` leader tree | `Alt+letter` (word/larger unit), `Ctrl+X`/`Ctrl+C` prefixes | `Shift` / mark | Collides with CUA (`Ctrl+W/Y/K`) |
| **Vim / Kakoune / Helix** | — | Modal plain keys (`<verb><obj>` or `<obj><verb>`) | Prefix menus (`g`, `m`, `Space`, `[`, `]`) | Visual mode / `Shift` extends | `Escape` returns to Normal |
| **Nano / Micro / VS Code** | — | `Ctrl+letter` (CUA in Micro/VS Code) | `Alt+key`, `Ctrl+K ...` chords, Command Palette | `Shift+Nav` | Micro disables `ISIG`/`IXON` in raw mode |
| **Multiplexers (`tmux`/`zellij`)** | — | Prefix (`Ctrl+B`) or Modes (`zellij`) | Locked pass-through (`Ctrl+G` in zellij) | Copy/scroll mode | Passes inner keys through |

## 2. Five recurring failure modes across existing systems

1. **The CUA-vs-POSIX `Ctrl+C` / `Ctrl+Z` / `Ctrl+S` collision.**
   Every Linux desktop (GNOME, KDE, Mint, COSMIC) and Windows Terminal
   fractures user muscle memory by forcing `Ctrl+Shift+C/V` inside
   terminals while using `Ctrl+C/V` everywhere else. Only **macOS**
   (separate `Command` key) and **Micro** (raw mode with `ISIG`/`IXON`
   off) avoided this split.
2. **Compositor modifier sprawl.**
   Windows, GNOME, KDE, and Mint scatter desktop shortcuts across three
   or four prefixes (`Meta`, `Alt`, `Ctrl+Alt`, `Alt+Shift`), stealing
   application chords and making it impossible to know which layer owns a
   key.
3. **Physical-ergonomics breakdown (3+ modifiers & Emacs pinky).**
   Squeezing Lisp-Machine modifier richness onto a 104-key PC keyboard
   produces 4-key contortions (`Meta+Ctrl+Shift+Arrow` in Niri,
   `Ctrl+Alt+Shift+<letter>` in IDEs) or pinky strain.
4. **`TERM=linux` blindness.**
   Bindings that depend on `Ctrl+Shift+<letter>`, `Meta`, `Alt+Left/Right`,
   or `Alt+F1..F12` break silently on the Linux text console or over SSH.
5. **Undiscoverable bindings and stale docs.**
   Systems without a built-in, live help overlay or named-action search
   force users to memorize arbitrary letters or read outdated wikis.

## 3. Distilled ideas for Tamlinux

### Adopt
- **Strict one-owner-per-layer modifier separation** (`lisp-machines-and-plan9.md`,
  `tiling-distros-and-compositors.md`, `pop-os-cosmic.md`):
  - `Meta` = compositor (`tam-pane`) exclusively. Never bound by apps;
    compositor never steals non-`Meta` chords from apps.
  - `Ctrl` = primary application commands (`tam-clam`, `tam-edit`,
    `tam-file`, `tam-view`, `tam`, and GUI apps), using the 22 clean
    ASCII-safe letters + non-letter chords (`Ctrl+=`/`-`/`0`) for terminal
    zoom.
  - `Alt` = secondary / extended app commands and `TERM=linux` fallbacks
    (never `Alt+Left/Right` or `Alt+F1..F12`, which the Linux kernel VT
    captures).
  - `Shift` = **extend selection** (on navigation) or **reverse / carry**
    (`Shift+Tab`, `Meta+Shift+Arrow` move window, `Meta+Shift+1..0` move
    window to workspace, reverse search).
- **CUA editing anchors in raw-mode terminal apps** (`windows-and-cua.md`,
  `nano-micro-vscode.md`, `shells-terminals-multiplexers.md`):
  `Ctrl+X/C/V/Z` work identically in `tam-clam`, `tam-edit`, `tam-file`,
  and graphical apps (with kernel `ISIG` preserved while a foreground
  child command runs).
- **Orthogonal modifier composition** (`windows-and-cua.md`, `macos.md`,
  `tiling-distros-and-compositors.md`):
  One modifier meaning predicts whole families (`Arrow` = step,
  `Ctrl+Arrow` = word/big step, `Shift+Arrow` = select, `Meta+Arrow` =
  focus window, `Meta+Shift+Arrow` = move window).
- **One centralized standard action catalog in `libtam`** (`kde-plasma.md`,
  `macos.md`, `emacs-and-readline.md`):
  Every action has a canonical lowercase hyphenated name (`copy`, `undo`,
  `guidance`, `word-left`), shared across `tam-clam`, `tam-edit`,
  `tam-file`, `tam-view`, and `tam`.
- **Self-documenting guidance everywhere** (`emacs-and-readline.md`,
  `elementary-os-pantheon.md`, `tiling-distros-and-compositors.md`,
  `nano-micro-vscode.md`):
  `Ctrl+G` (`guidance`) inside every app + `Meta+K` at the compositor
  level, backed by live bindings, plain-English explanations, and
  mnemonics (per Tamlinux P14).
- **Hard 3-physical-key ceiling** (`tiling-distros-and-compositors.md`, P14):
  No default binding requires more than two modifiers plus one primary key.
- **`TERM=linux` reachability floor** (`linux-rootstocks-and-vt.md`):
  Every essential command stays reachable on the Linux text console
  without relying on `Meta`, `Ctrl+Shift+<letter>`, `Alt+Left/Right`, or
  `Alt+F*`.

### Consider
- **Modal submap for window resizing (`Meta+R` or `Meta+Enter`)**
  (`pop-os-cosmic.md`, `tiling-distros-and-compositors.md`) vs. permanent
  punctuation chords (`Meta+,/./;/'` + `Alt`/`Ctrl`). A resize submap
  frees 6–12 global chords and avoids colliding with P29's `Meta+Alt`
  text-macro reservation!
- **Two-step mnemonic chords with live `which-key` popup**
  (`emacs-and-readline.md`, `vim-kakoune-helix.md`, `nano-micro-vscode.md`)
  for secondary command families that don't fit in the 22 `Ctrl+<letter>`
  slots (works cleanly on `TERM=linux` too).
- **Universal Command Palette / Action Search** (`nano-micro-vscode.md`,
  `kde-plasma.md`, `bsd-unix.md`) so rare actions are run by name instead
  of burning obscure chords.
- **Read-only single-key navigation in `tam` / `tam-view`**
  (`vim-kakoune-helix.md`, `shells-terminals-multiplexers.md`):
  Allowing plain `/` (find), `n`/`N` (next/prev), `q` (quit), `Space`/`b`
  (page) *alongside* universal `Ctrl+F` / `Ctrl+G` / `Ctrl+Q` / `Escape`.
- **Compact bottom hint bar on text surfaces** (`nano-micro-vscode.md`,
  `shells-terminals-multiplexers.md`) showing `Ctrl+G Guidance` and key
  anchors on first glance.
- **BSD-style live status inspection (`SIGINFO` / `Ctrl+T` concept)**
  (`bsd-unix.md`) for checking running foreground commands in `tam-last` /
  `tam-clam`.
- **Function keys (`F1`–`F12`)** (`windows-and-cua.md`,
  `shells-terminals-multiplexers.md`) for collision-free `TERM=linux`
  anchors.

### Reject
- **Modal editing as the OS-wide default** (`vim-kakoune-helix.md`):
  High mode-confusion cost outside dedicated code editors.
- **`Ctrl+Shift+C/V` terminal copy/paste split** (`gnome-fedora-ubuntu.md`,
  `kde-plasma.md`, `windows-and-cua.md`):
  Breaks consistency between graphical and text surfaces and fails on
  `TERM=linux`.
- **Dual built-in shell modes (`emacs` vs. `vi`)** (`bsd-unix.md`,
  `emacs-and-readline.md`):
  Fragments docs and muscle memory; keep one strong default map plus
  user-supplied rebinding files.
- **Global compositor grabs without `Meta`** (`linux-mint-and-cinnamon.md`,
  `tiling-distros-and-compositors.md`):
  No `Alt+Shift+Arrows` or `Ctrl+Alt+<number>` stealing application keys.
- **Legacy notation (`C-x`, `M-x`, `^G`)** (`emacs-and-readline.md`,
  `nano-micro-vscode.md`):
  Always use physical key names.

## 4. Open design tensions to resolve next in `arch/keybindings.md`

1. **Naming consistency (`Meta` vs. `Super`):**
   Tamlinux settled on **`Meta`** (D217, `GLOSSARY.md`), while the current
   draft of `arch/keybindings.md` still says `Super`. Updating it to `Meta`
   unifies compositor, terminal, and docs.
2. **Respecting P29 (`Meta+Alt` reserved for text macros):**
   Compositor bindings in `tam-pane` should live cleanly on `Meta`,
   `Meta+Shift`, and `Meta+Ctrl` (keeping `Meta+Alt` free for Fred's text
   macros).
3. **Exact semantic contract for each modifier tier:**
   We need one crisp, memorable sentence per modifier (`Meta`, `Ctrl`,
   `Alt`, `Shift`) that holds across `tam-pane`, `tam-last`, `tam-clam`,
   `tam`, `tam-edit`, `tam-file`, and `tam-view`.
4. **Assigning the remaining 17 free `Ctrl+<letter>` slots:**
   Of the 22 ASCII-clean letters (`A B C D E F G K L N O P Q R S T U V W X Y Z`),
   5 are anchored (`X` cut, `C` copy, `V` paste, `Z` undo, `G` guidance),
   leaving 17 prime slots for `redo`, `select-all`, `find`, `replace`,
   `save`, `open`, `new`, `close`, `quit`, `cancel-line`, `exit-shell`,
   `clear-screen`, `history-search`, `command-palette`, etc.
5. **Terminal (`tam-last`) layer keys without colliding with apps:**
   How should `tam-last` bind scrollback, terminal-level copy/paste (when
   running a third-party app), terminal search, and font zoom so it never
   steals `Ctrl+<letter>` from `tam-clam` / `tam-edit` and avoids awkward
   `Ctrl+Shift+<letter>`?
6. **Read-only (`tam`, `tam-view`) vs. editable (`tam-clam`, `tam-edit`) surfaces:**
   Ensuring universal `Ctrl` chords work identically on both, while
   deciding which plain single-key shortcuts are offered on read-only
   surfaces.
7. **`TERM=linux` equivalents for `Shift+Nav` and `Ctrl+Nav`:**
   Because the Linux console cannot distinguish `Shift+Arrows` or
   `Ctrl+Arrows` from plain arrows, deciding the clean `Alt+<key>`
   equivalents (e.g., word movement, selection toggle/mark) keeps every
   essential action reachable on bare-rootstock text VTs.
