# Tamlinux keybinding standard

**Status:** Draft (2026-11-23). Initial design notes for Fred to review and
refine before individual programs adopt it.

This document defines the Tamlinux-wide keybinding standard shared across
all Tamlinux programs: the compositor (`tam-pane`), terminal (`tam-last`),
shell (`tam-clam`), editor (`tam-edit`), file manager (`tam-file`), pager
(`tam-view` / `libtam`), and future desktop tools.

Each program's own `arch/keys.md` references this standard and adds only
the bindings specific to that program.

## Design principles

- **First principles, not UNIX inertia.** Keybindings are chosen to be
  ergonomic, mnemonic, and consistent across every Tamlinux program,
  rather than copying readline or traditional UNIX control codes.
- **Familiar anchors.** Common editing actions match the modern standard
  people already know (`x` cut, `c` copy, `v` paste, `z` undo), and `g`
  means guidance (help) everywhere.
- **Physical key names only.** Documentation and configuration always name
  the physical key (`Ctrl`, `Alt`, `Shift`, `Super`, a letter, or a named
  key such as `Enter`, `Backspace`, `Delete`, `Tab`, `Escape`, `Left`,
  `Home`), never placeholders such as `C-`, `M-`, or `^X`.
- **Every action has a name.** Every bindable command has a canonical
  lowercase hyphenated widget name (for example `copy`, `undo`,
  `word-left`, `guidance`), so users can inspect or rebind any key.
- **Works on both graphical terminals and the Linux console.** Primary
  bindings work in `tam-last` (and other ANSI/xterm terminals), and every
  essential action remains reachable on the Linux text console
  (`TERM=linux`).
- **One standard map, expressive rebinding.** Tamlinux ships one default
  key map (no built-in vi or readline modes). The binding format can
  express multi-key chords so an optional user-supplied map (such as a
  readline file) remains possible without adding built-in modes.

## Key ownership across layers

A key press travels through four layers (see `tam-last/arch/key-path.md`).
Separating ownership prevents collisions:

1. **Compositor (`tam-pane` / Hyprland) owns `Super`.**
   Window management, workspaces, launchers, and desktop controls use
   `Super` (Logo/Windows key). Applications never bind `Super`.
2. **Terminal (`tam-last`) passes application keys through cleanly.**
   Terminal-level actions (scrollback, font zoom, terminal-level copy when
   a raw app is not active) avoid stepping on the application `Ctrl`
   anchors.
3. **Interactive Tamlinux programs (`tam-clam`, `tam-edit`, `tam-file`,
   `tam-view`) own `Ctrl`, `Alt`, `Shift+Navigation`, and plain keys.**
   When a program like `tam-clam` runs in raw mode (`ISIG` disabled), the
   kernel does not intercept `Ctrl+C`, `Ctrl+Z`, `Ctrl+D`, `Ctrl+S`, or
   `Ctrl+Q`. They arrive as ordinary keystrokes, so `Ctrl+Z` can be Undo
   and `Ctrl+C` can be Copy inside the prompt or editor.
4. **Running foreground child commands (`termios` `n_tty` line
   discipline).**
   While a child command (such as `make`, `grep`, `sleep`, or `ssh`) runs
   in the foreground of a shell, the kernel watches `termios` `VINTR`
   (default `Ctrl+C` -> `SIGINT`), `VSUSP` (default `Ctrl+Z` ->
   `SIGTSTP`), and `VQUIT` (default `Ctrl+\` -> `SIGQUIT`).
   - Keeping `VSUSP` as `Ctrl+Z` while a child runs has no conflict with
     `Ctrl+Z` = Undo at the prompt: you never undo a prompt while `sleep`
     is running, and you never suspend the shell while editing.
   - Keeping `VINTR` as `Ctrl+C` while a child runs preserves standard
     interrupt behavior for third-party programs, while `Ctrl+C` at the
     `tam-clam` prompt acts as Copy (and a dedicated key cancels the
     current prompt line).

## Modifier tiers and hardware constraints

| Key class | Graphical terminal (`tam-last`, `foot`, `xterm`) | Linux console (`TERM=linux`) | Role in Tamlinux |
|---|---|---|---|
| **Plain special keys** (`Arrows`, `Home`, `End`, `Backspace`, `Delete`, `Tab`, `Enter`, `Escape`, `PageUp/Down`, `F1`-`F12`) | Reliable | Reliable | Everyday single-step navigation, delete, submit, complete, dismiss |
| **`Shift` + navigation** (`Shift+Left/Right/Home/End`, `Shift+Tab`) | Reliable | Not distinguished from unmodified arrows | Text selection (and reverse-Tab) |
| **`Ctrl` + letter** | Reliable (22 free letters) | Reliable (same 22 letters) | Primary command tier (`Ctrl+X/C/V/Z/G`, etc.) |
| **`Ctrl` + navigation** (`Ctrl+Left/Right/Home/End`, `Ctrl+Backspace/Delete`) | Reliable | Not distinguished | Word and buffer jumps, word delete |
| **`Alt` + letter / `Enter` / `Backspace` / punct** | Reliable (`ESC <char>`) | Reliable (`ESC <char>`) | Secondary / program-specific commands and `TERM=linux` equivalents |
| **`Ctrl+Shift` + letter** | Collides with `Ctrl+<letter>` in legacy encoding | Collides with `Ctrl+<letter>` | Avoid in default map (available via Kitty keyboard protocol later) |
| **`Alt` + `Left`/`Right`/`F1`-`F12`** | Reliable | Captured by Linux kernel (switches VTs) | Avoid in default map |
| **`Super`** | Captured by compositor | Not sent | Compositor only |

**The four legacy ASCII `Ctrl` collisions** (true on `TERM=linux` and in
legacy xterm encoding; `tam-last` can distinguish them later when Kitty
keyboard protocol is enabled):

- `Ctrl+H` == `Backspace` (`0x08`)
- `Ctrl+I` == `Tab` (`0x09`)
- `Ctrl+J` and `Ctrl+M` == `Enter` (`0x0A` / `0x0D`)
- `Ctrl+[` == `Escape` (`0x1B`)

That leaves 22 clean `Ctrl+<letter>` slots across every terminal and the
Linux console:

`A B C D E F G K L N O P Q R S T U V W X Y Z`

## Anchor bindings (decided 2026-11-23)

| Key | Action | Meaning |
|---|---|---|
| `Ctrl+X` | `cut` | Cut selection (or current line if nothing is selected) |
| `Ctrl+C` | `copy` | Copy selection (or current line if nothing is selected) |
| `Ctrl+V` | `paste` | Paste from clipboard (replacing selection if any) |
| `Ctrl+Z` | `undo` | Undo last edit |
| `Ctrl+G` | `guidance` | Show keybinding guidance / contextual help |

## Complete command inventory (to be mapped)

### 1. Universal editing and navigation (shell, editor, inputs, pager)

- **Cursor movement:**
  `char-left`, `char-right`, `word-left`, `word-right`,
  `line-start`, `line-end`, `buffer-start`, `buffer-end`,
  `line-up`, `line-down`, `page-up`, `page-down`
- **Selection:**
  `select-char-left`, `select-char-right`,
  `select-word-left`, `select-word-right`,
  `select-line-start`, `select-line-end`, `select-all`
- **Clipboard and undo:**
  `cut` (`Ctrl+X`), `copy` (`Ctrl+C`), `paste` (`Ctrl+V`),
  `paste-prev` (cycle clipboard history),
  `undo` (`Ctrl+Z`), `redo`
- **Direct deletion:**
  `delete-char-left`, `delete-char-right`,
  `delete-word-left`, `delete-word-right`,
  `delete-to-line-start`, `delete-to-line-end`
- **Search, guidance, and mode control:**
  `find`, `find-next`, `find-prev`,
  `guidance` (`Ctrl+G`), `cancel-mode` (`Escape`)

### 2. Shell-specific (`tam-clam`)

- **Line and prompt control:**
  `accept-line` (`Enter`), `insert-newline`,
  `cancel-line` (abandon current prompt buffer),
  `exit-shell` (EOF on empty prompt),
  `clear-screen`, `open-in-editor`, `comment-line`, `insert-verbatim`
- **History:**
  `up-or-history-prev`, `down-or-history-next`,
  `history-search-backward`, `history-search-forward`, `insert-last-arg`
- **Completion and suggestions:**
  `complete-next` (`Tab`), `complete-prev` (`Shift+Tab`),
  `accept-suggestion`, `accept-suggestion-word`

### 3. Editor and file actions (`tam-edit`, `tam-file`, `tam-view`)

- `save`, `save-as`, `open`, `new`, `close`, `quit`
- `replace`, `goto-line`, `duplicate-line`, `toggle-comment`

### 4. Terminal actions (`tam-last`)

- `scroll-up`, `scroll-down`, `scroll-page-up`, `scroll-page-down`
- `zoom-in`, `zoom-out`, `zoom-reset`
- `terminal-copy`, `terminal-paste`, `terminal-search`

## Binding file format (proposal)

Every Tamlinux program that supports user rebinding can share one plain
line-oriented syntax (implementable once in `libtam`):

```text
# Comments start with #
bind Ctrl+X cut
bind Ctrl+C copy
bind Ctrl+V paste
bind Ctrl+Z undo
bind Ctrl+G guidance
bind Shift+Left select-char-left
bind "Ctrl+X Ctrl+E" open-in-editor
unbind Ctrl+T
```

- Canonical modifier order: `Ctrl+Alt+Shift+<Key>`.
- Multi-key sequences are space-separated inside quotes.
- Single-key and multi-key chords both work, so optional user-supplied
  key maps (such as a readline compatibility file) need no special syntax.

## Open questions for Fred

1. **Modifier tiers:** Confirm `Ctrl` for primary commands, `Shift+Nav`
   for selection, `Alt` for secondary / shell-specific commands and
   `TERM=linux` fallbacks, and `Super` reserved for the compositor.
2. **Command inventory:** Any commands to add or remove from the lists
   above before assigning keys?
3. **System clipboard sync:** Should `cut` / `copy` (`Ctrl+X` / `Ctrl+C`)
   in terminal programs like `tam-clam` also push to the Wayland system
   clipboard via OSC 52 (when supported by `tam-last` / `foot`)?
4. **Foreground child commands:** Confirm keeping kernel `termios`
   defaults (`Ctrl+C` interrupt, `Ctrl+Z` suspend) while a child command
   is running, while freeing both inside the `tam-clam` prompt.
5. **Remaining `Ctrl+<letter>` assignments:** Which letters should map to
   `redo`, `select-all`, `find` / `history-search`, `cancel-line`,
   `exit-shell`, `clear-screen`, `open-in-editor`, `save`, `quit`, etc.?
