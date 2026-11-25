# Tamlinux keybinding standard

**Status:** Draft (2026-11-23). Refined with Fred after the cross-system
survey in [`../ideas/keybindings/synthesis.md`](../ideas/keybindings/synthesis.md).
Individual programs adopt this standard as they implement or update their
input layers.

This document defines the Tamlinux-wide keybinding standard shared across
every Tamlinux program and surface — graphical and text alike: the
compositor (`tam-pane`), terminal (`tam-last`), shell (`tam-clam`),
guide (`tam`), editor (`tam-edit`), file manager (`tam-file`), pager
(`tam-view` / `libtam`), and future desktop tools.

Each program's own `arch/keys.md` references this standard and adds only
the bindings specific to that program.

## Design principles

- **First principles, not UNIX inertia.** Keybindings are chosen to be
  ergonomic, mnemonic, and consistent across every Tamlinux program,
  rather than copying readline or traditional UNIX control codes.
- **No double-acting `Ctrl` codes.** Every `Ctrl` key has **one** single
  meaning everywhere in Tamlinux. If an action does not apply on a given
  surface (for example `Ctrl+R` Replace on a read-only page), it is a
  no-op rather than taking on an unrelated second meaning.
- **Universal editing anchors everywhere.** `Ctrl+Z` (Undo), `Ctrl+X`
  (Cut), `Ctrl+C` (Copy), `Ctrl+V` (Paste), and `Ctrl+G` (Guidance) mean
  the same thing in graphical apps, `tam-last`, `tam-clam`, `tam-edit`,
  `tam-file`, `tam-view`, and `tam`.
- **Three-physical-key ceiling.** No default keyboard chord requires more
  than two modifier keys plus one primary key (including any `Shift`
  needed to type a symbol; see `plans/P14-keybinding-usability.md`).
- **Physical key names only.** Documentation and configuration always name
  the physical key (`Meta`, `Ctrl`, `Alt`, `Shift`, a letter, or a named
  key such as `Enter`, `Backspace`, `Delete`, `Tab`, `Escape`, `Left`,
  `Home`), never legacy notation such as `C-`, `M-`, or `^X`. Tamlinux
  spells the desktop modifier **`Meta`** (not `Super`; see D217).
- **Every action has a canonical name.** Every bindable command has a
  lowercase hyphenated widget name (for example `copy`, `undo`, `update`,
  `word-left`, `guidance`), so users can inspect, search, run by name
  (`Ctrl+E`), or rebind any key.
- **Works on both graphical terminals and the Linux console.** Primary
  bindings work in `tam-last` (and other ANSI/xterm terminals), and every
  essential action remains reachable on the Linux text console
  (`TERM=linux`).
- **One standard map, expressive rebinding.** Tamlinux ships one default
  key map (no built-in vi or readline modes). The binding format can
  express multi-key chords so an optional user-supplied map (such as a
  readline file) remains possible without adding built-in modes.

## Modifier contract (one meaning per modifier)

Every modifier key carries one consistent semantic role across every
Tamlinux surface:

| Modifier | Universal meaning in Tamlinux | Rules and examples |
| --- | --- | --- |
| **`Meta`** | **The Desktop (`tam-pane`)** — windows, workspaces, monitors, launchers, system menus | Owned exclusively by `tam-pane`. Applications never bind `Meta`, and `tam-pane` never steals non-`Meta` chords from applications. **`Meta+Alt` is reserved for user text macros** (`plans/P29-text-macros-and-meta.md`), so compositor bindings live on `Meta`, `Meta+Shift`, and `Meta+Ctrl`. Examples: `Meta+Arrows` focus window, `Meta+Shift+Arrows` move window, `Meta+1..0` switch workspace, `Meta+Space` menu, `Meta+K` keybindings explorer. |
| **`Ctrl`** | **Primary Action / Fine Control** — the main verb inside the focused app, word/document navigation, or **smaller / tighter control** when scaling magnitude | Uses the 22 ASCII-clean letters plus `Ctrl+\` (Break) and non-letter terminal zoom chords (`Ctrl+=`, `Ctrl+-`, `Ctrl+0`). When adjusting magnitude (such as resizing), `Ctrl` means tighter, smaller increments. Examples: `Ctrl+Z/X/C/V/G`, `Ctrl+Left/Right` word jump, `Ctrl+Home/End` buffer start/end, `Ctrl+Backspace/Delete` word delete, `Meta+Ctrl` small resize. |
| **`Shift`** | **Bigger / Extend / Reverse / Carry** — makes things larger (like uppercase letters), extends selection on navigation, reverses direction on cycling/search, or carries the active window (`Meta+Shift`) | Composes cleanly with `Ctrl`, `Alt`, and `Meta`: when adjusting magnitude (such as resizing or jumping from word `Alt+,/.` to buffer `Alt+</>`), `Shift` means **bigger**. Examples: `Shift+Left` select char, `Ctrl+Shift+Left` select word, `Shift+Tab` reverse Tab, `Shift+PageUp/Down` terminal scrollback, `Meta+Shift+1..0` move window to workspace, `Meta+Shift` large resize. |
| **`Alt`** | **Secondary / Alternate & `TERM=linux` Fallback** — secondary app commands, multiline newline, and `TERM=linux` equivalents where `Ctrl+Nav`/`Shift+Nav` are not distinguished | Never bind `Alt+Left/Right` or `Alt+F1`-`F12` in the default map (captured by the Linux kernel VT to switch virtual consoles). Examples: `Alt+Enter` insert newline, `Alt+E` open prompt in `tam-edit`. |

## Key ownership across layers

A key press travels through four layers (see `tam-last/arch/key-path.md`).
Separating ownership prevents collisions:

1. **Compositor (`tam-pane` / Hyprland) owns `Meta`.**
   Window management, workspaces, launchers, and desktop controls use
   `Meta` (`Meta`, `Meta+Shift`, `Meta+Ctrl`; `Meta+Alt` reserved for
   text macros). Applications never bind `Meta`.
2. **Terminal (`tam-last`) passes application keys through cleanly.**
   Terminal-level actions avoid stepping on application `Ctrl+<letter>`
   bindings:
   - Font zoom uses non-letter chords: `Ctrl+=`, `Ctrl+-`, `Ctrl+0`.
   - Scrollback uses `Shift+PageUp` / `Shift+PageDown` (and `Shift+Home`
     / `Shift+End`).
   - When a Tamlinux raw-mode program (`tam-clam`, `tam-edit`, `tam-file`,
     `tam-view`, `tam`) is active, `tam-last` passes `Ctrl+Z/X/C/V`
     straight to the program, which handles selection, undo, and clipboard
     (syncing with Wayland via OSC 52).
   - When a cooked-mode child command (`make`, `grep`, `ping`, `cat`) is
     running, `tam-last` handles `Ctrl+C` (copy terminal selection) and
     `Ctrl+V` (bracketed paste into the PTY) directly.
   - **External compatibility (remote SSH and third-party raw TUIs):**
     Over SSH to a remote host whose PTY still expects `0x03` (`Ctrl+C`)
     for interrupt, or inside a third-party raw TUI (`vim`, `htop`),
     `tam-last` copies if text is selected in the terminal grid and
     otherwise passes `0x03` cleanly so remote and third-party tools keep
     working without fighting the user.
3. **Interactive Tamlinux programs (`tam-clam`, `tam-edit`, `tam-file`,
   `tam-view`, `tam`) own `Ctrl`, `Alt`, `Shift+Navigation`, and plain
   keys.**
   They run in raw mode (`ISIG` and `IXON` disabled via `libtam`'s
   `tam_tty`), so `Ctrl+C`, `Ctrl+Z`, `Ctrl+S`, `Ctrl+Q`, and `Ctrl+P`
   arrive as ordinary keystrokes.
4. **Running foreground child commands (`termios` `n_tty` line
   discipline).**
   POSIX `termios` allows the shell to configure which single-byte
   control characters trigger kernel signals:
   - `tam-clam` configures **`VINTR` = `Ctrl+\` (`0x1C`)** -> **`SIGINT`**
     (**Break**), and disables `VQUIT` (`_POSIX_VDISABLE`) so `Ctrl+\`
     interrupts cleanly without dumping core.
   - `tam-clam` configures **`VSUSP` = `Ctrl+P` (`0x10`)** -> **`SIGTSTP`**
     (**Pause**).
   - Every local child process (`make`, `grep`, `ping`, `sleep`, `python`)
     inherits this PTY `termios` automatically with zero patches required.
     `Ctrl+C` and `Ctrl+Z` are **never** kernel signals locally; they
     belong to Copy and Undo everywhere.

## Hardware and console constraints

| Key class | Graphical terminal (`tam-last`, `foot`, `xterm`) | Linux console (`TERM=linux`) | Role in Tamlinux |
| --- | --- | --- | --- |
| **Plain special keys** (`Arrows`, `Home`, `End`, `Backspace`, `Delete`, `Tab`, `Enter`, `Escape`, `PageUp/Down`, `F1`-`F12`) | Reliable | Reliable | Everyday single-step navigation, delete, submit, complete, dismiss |
| **`Shift` + navigation** (`Shift+Left/Right/Home/End`, `Shift+Tab`) | Reliable | Not distinguished from unmodified arrows | Text selection (and reverse-Tab); `Alt` fallbacks on `TERM=linux` |
| **`Ctrl` + letter / `Ctrl+\`** | Reliable (22 clean letters + `Ctrl+\`) | Reliable (same 22 letters + `Ctrl+\`) | Primary command tier and `termios` Break/Pause |
| **`Ctrl` + navigation** (`Ctrl+Left/Right/Home/End`, `Ctrl+Backspace/Delete`) | Reliable | Not distinguished | Word and buffer jumps, word delete; `Alt` fallbacks on `TERM=linux` |
| **`Alt` + letter / `Enter` / `Backspace` / punct** | Reliable (`ESC <char>`) | Reliable (`ESC <char>`) | Secondary / program-specific commands and `TERM=linux` equivalents |
| **`Ctrl+Shift` + letter** | Collides with `Ctrl+<letter>` in legacy encoding | Collides with `Ctrl+<letter>` | Avoid in default map (available via Kitty keyboard protocol later) |
| **`Alt` + `Left`/`Right`/`F1`-`F12`** | Reliable | Captured by Linux kernel (switches VTs) | Never bind in default map |
| **`Meta`** | Captured by compositor | Not sent | Compositor (`tam-pane`) only |

**The four legacy ASCII `Ctrl` collisions** (true on `TERM=linux` and in
legacy xterm encoding; `tam-last` can distinguish them later when Kitty
keyboard protocol is enabled):

- `Ctrl+H` == `Backspace` (`0x08`)
- `Ctrl+I` == `Tab` (`0x09`)
- `Ctrl+J` and `Ctrl+M` == `Enter` (`0x0A` / `0x0D`)
- `Ctrl+[` == `Escape` (`0x1B`)

That leaves **22 clean `Ctrl+<letter>` slots** across every terminal and
the Linux console:

`A B C D E F G K L N O P Q R S T U V W X Y Z`

### Physical keyboard availability (every key across keyboard classes)

Tamlinux targets everything from full-size 104/105-key desktop keyboards
to compact laptops, Macs, Chromebooks, and vintage hardware. The table
below shows which physical keys can be relied on everywhere versus which
should be treated as optional aliases:

| Key / key group | Full-size PC (104/105) | TKL (87/88) | PC Laptop (13–15") | Mac / MacBook | Chromebook | 60% Compact | Pre-1995 (Model M) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **`A`-`Z`, `0`-`9`, punct, `Space`, `Enter`, `Tab`, `Backspace`, `Escape`** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **`Left Shift` / `Right Shift`** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **`Left Ctrl`** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **`Right Ctrl`** | Yes | Yes | Usually | Often no | Yes | Usually | Yes |
| **`Left Alt`** (`Option` on Mac) | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **`Right Alt`** (`AltGr` on ISO) | Yes (`AltGr` ISO) | Yes (`AltGr` ISO) | Yes (`AltGr` ISO) | Yes (`Option`) | Yes | Usually | Yes |
| **`Left Meta`** (`Win` / `Cmd` / `Search`) | Yes | Yes | Yes | Yes (`Command`) | Yes (`Search` in Caps slot) | Yes | **No** |
| **`Right Meta`** (`Win` / `Cmd`) | Usually | Usually | **Rare** | Yes (`Command`) | **No** | Often no (`Fn`) | **No** |
| **`Caps Lock`** | Yes | Yes | Yes | Yes | **No** (`Search`) | Yes | Yes |
| **`Menu`** (`KEY_COMPOSE`, between Right Alt & Right Ctrl) | Common | Common | **Rare** | **No** | **No** | **No** | **No** |
| **`Arrows`** (`Up`, `Down`, `Left`, `Right`) | Yes | Yes | Yes | Yes | Yes | `Fn` layer | Yes |
| **`Delete`** (forward delete) | Yes | Yes | Yes | `Fn+Backspace` | `Alt+Backspace` | `Fn` layer | Yes |
| **`Insert`** | Yes | Yes | Often `Fn`/no | **No** | **No** | **No** | Yes |
| **`Home`, `End`, `PageUp`, `PageDown`** | Yes | Yes | Mixed (dedicated or `Fn`) | `Fn+Arrows` | `Alt/Search+Arrows` | `Fn` layer | Yes |
| **`F1`-`F12`** | Yes | Yes | Yes (often `Fn`-locked) | Yes (`Fn`-locked) | `Search+1..=` | `Fn` layer | Yes |
| **`PrtSc`** (Print Screen) | Yes | Yes | Usually | **No** | Dedicated key | **No** | Yes |
| **`ScrLk`**, **`Pause` / `Break`** | Yes | Yes | **Rare** | **No** | **No** | **No** | Yes |
| **Numeric Keypad** (`NumLock`, `KP_0`-`KP_9`, `KP_*`, `KP_Enter`) | Yes | **No** | Only 15–17" | Full-size only | **No** | **No** | Yes |
| **Media / Hardware** (`XF86Audio*`, `XF86MonBrightness*`) | Mixed | Mixed | Yes | Yes | Yes | `Fn` layer | **No** |

**What this means for Tamlinux:**

- **Universal core baseline:** Every essential default binding relies
  only on keys present across PC, Mac, Chromebook, and laptop keyboards:
  letters, digits, punctuation, `Space`, `Enter`, `Tab`, `Backspace`,
  `Escape`, `Left Ctrl`, `Left Alt`, `Shift`, `Arrows`, and `Left Meta`
  (compositor only).
- **Never require right-side modifiers:** Do not require `Right Meta`,
  `Right Ctrl`, or `Right Alt` (which is `AltGr` on international ISO
  layouts and needed to type `@`, `{`, `}`, `\`, `|`).
- **Standard nav & function keys (`Delete`, `Home`, `End`, `PageUp`,
  `PageDown`, `F1`-`F12`):** Great for primary ergonomic bindings on
  full-size, TKL, and PC laptops, paired with `Ctrl`/`Alt` equivalents so
  MacBook, Chromebook, 60%, and `TERM=linux` users are never stranded.
- **Full-size-only keys (`Keypad`, `Menu`, `PrtSc`, `Insert`, `ScrLk`,
  `Pause`):** Valuable as convenient **optional aliases** (such as keypad
  workspace switching, `PrtSc` screenshot, or `Menu` for context/Tamlinux
  menu), never the sole binding for an essential action.
- **Never require `Meta` on `TERM=linux`:** The kernel console does not
  transmit `Meta` to applications, matching our rule that `Meta` belongs
  solely to `tam-pane`.
- **Optional `Caps Lock` -> `Meta` remap:** Covers pre-1995 keyboards
  (such as the IBM Model M) cleanly and matches Chromebook ergonomics.
- **Touch Bar MacBooks (2016–2020) and Chromebooks:** Touch Bar MacBooks
  have no physical `F1`–`F12` row (and a touch-strip `Escape`), while
  Chromebooks have no `Caps Lock` (`Search` occupies that slot). One-handed
  chord composing therefore never requires `F1`–`F12` and provides both
  `Caps Lock` (primary) and solo `Right Alt` tap (secondary).

## One-handed chord composing

To make every desktop and application shortcut reachable with one hand,
Tamlinux provides a sequential **Chord Composer & Command Menu** in both
`tam-pane` (compositor-wide) and `tam-clam` (standalone on `TERM=linux` or
other compositors). Instead of holding `Meta+1` or `Ctrl+X` simultaneously,
the user presses a **Chord key**, presses the modifiers and primary key one
at a time, and presses the **Chord key** again to send the chord.

| Role | Default physical key | Notes |
| --- | --- | --- |
| **Primary Chord key** | `Caps Lock` | Three-mode state machine (see below); works on PCs, laptops, all MacBooks (including Touch Bar), and 60% boards. Configurable. |
| **Secondary Chord key** | Solo `Right Alt` (`Option`) tap | Press and release with no intervening key. Enters Chord Builder directly (never toggles Caps Lock); covers Chromebooks and preserves `AltGr` when held with another key. Configurable. |
| **Cancel Chord key** | `Escape` | Cancels immediately from any chord-composing state. Pressing `Backspace` when the chord is empty, or pressing `<Chord key>` when empty, also cancels. Configurable. |

### Three-state `Caps Lock` machine (`tam-pane`)

1. **Pluripotent** (entered on `Caps Lock` press from Idle): opens the chord
   composer overlay showing the full command menu.
   - Pressing a **modifier** (`Meta`, `Ctrl`, `Alt`, `Shift`) or **menu
     navigation** (`Up`/`Down`) transitions to **Chord Builder**.
   - Pressing **`A`–`Z`** transitions to **Regular Caps Lock**, dismisses the
     overlay, and immediately sends that letter uppercase.
   - Pressing **`Escape`**, **`Backspace`**, or **`Caps Lock`** again cancels
     and returns to Idle.
2. **Chord Builder** (entered from Pluripotent via modifier/navigation, or
   directly from Idle via solo `Right Alt` tap):
   - Pressing a modifier toggles it in the pending chord; pressing a primary
     key sets the chord's key and filters the command menu to matching
     bindings.
   - With no modifiers latched, `Up`/`Down` + `Enter` selects and runs any
     available command from the menu (and typing letters filters by command
     name).
   - Pressing `<Chord key>` ends and sends the chord: `tam-pane` checks its
     own bindings first, and otherwise synthesizes the composed chord (both
     modifier keycodes and `wl_keyboard.modifiers`) to the focused client.
3. **Regular Caps Lock**: `A`–`Z` presses behave as if `Shift` were held,
   other keys are unaffected, and pressing `Caps Lock` again turns Regular
   Caps Lock off cleanly.

### Standalone `tam-clam` (`TERM=linux` / SSH)

Over a plain TTY, bare modifier presses send no bytes. Inside `tam-clam`'s
unified chord composer and command menu (`chord-compose` / `Ctrl+E`),
**`Tab`** cycles latched modifiers (`Ctrl+`, `Alt+`, `Shift+`, `Ctrl+Shift+`,
`Alt+Shift+`, none) without relying on function keys, while `Up`/`Down` +
`Enter` or substring filtering runs any named widget.

## Standard `Ctrl` map (decided 2026-11-23)

Every `Ctrl` chord has **one** meaning across all Tamlinux programs (no
double-acting `Ctrl` codes).

| Key | Action | Mnemonic | Meaning across Tamlinux |
| --- | --- | --- | --- |
| `Ctrl+A` | `select-all` | **A**ll | Select entire prompt, buffer, or list |
| `Ctrl+B` | *(reserved)* | — | Reserved for future universal action |
| `Ctrl+C` | `copy` | **C**opy | Copy selection (or current line if nothing selected); terminal selection in `tam-last` |
| `Ctrl+D` | `close` | **D**one | Close current buffer, pane, or tab |
| `Ctrl+E` | `execute` | **E**xecute | Open named-command palette to search and run any action by name |
| `Ctrl+F` | `find` | **F**ind | Find in current surface (buffer, page, file list, or `tam-clam` history) |
| `Ctrl+G` | `guidance` | **G**uidance | Show contextual keybinding guidance / help everywhere |
| `Ctrl+K` | `kill-line` | **K**ill line | Discard current line (clears current prompt in `tam-clam`; deletes line in `tam-edit`) |
| `Ctrl+L` | `clear-screen` | c**L**ear | Clear / redraw screen |
| `Ctrl+N` | `new` | **N**ew | New file, buffer, or item |
| `Ctrl+O` | `open` | **O**pen | Open file or item |
| `Ctrl+P` | `pause` | **P**ause | Suspend running foreground child (`termios` `VSUSP` -> `SIGTSTP`) |
| `Ctrl+Q` | `quit` | **Q**uit | Quit current Tamlinux program (including `tam-clam` on an empty prompt) |
| `Ctrl+R` | `replace` | **R**eplace | Find and replace (editable surfaces only; never reload) |
| `Ctrl+S` | `save` | **S**ave | Save current buffer or document (`IXON` disabled in raw mode) |
| `Ctrl+T` | *(reserved)* | — | Reserved for future universal action |
| `Ctrl+U` | `update` | **U**pdate | Reload / refresh current view from disk or source (`tam-file`, `tam-view`, `tam`, etc.) |
| `Ctrl+V` | `paste` | paste (**V**) | Paste from clipboard (replacing selection if any; bracketed paste in `tam-last`) |
| `Ctrl+W` | *(reserved)* | — | Reserved for future universal action |
| `Ctrl+X` | `cut` | cut (**X**) | Cut selection (or current line if nothing selected) |
| `Ctrl+Y` | `redo` | redo (**Y**) | Redo last undone edit (works on `TERM=linux` where `Ctrl+Shift+Z` collides with `Ctrl+Z`) |
| `Ctrl+Z` | `undo` | undo (**Z**) | Undo last edit |
| `Ctrl+\` | `break` | break (`\`) | Interrupt running foreground child (`termios` `VINTR` -> `SIGINT`; `VQUIT` disabled) |

## Complete command inventory

### 1. Universal editing and navigation (shell, editor, inputs, pager)

- **Cursor movement:**
  `char-left` (`Left`), `char-right` (`Right`),
  `word-left` (`Ctrl+Left`), `word-right` (`Ctrl+Right`),
  `line-start` (`Home`), `line-end` (`End`),
  `buffer-start` (`Ctrl+Home`), `buffer-end` (`Ctrl+End`),
  `line-up` (`Up`), `line-down` (`Down`),
  `page-up` (`PageUp`), `page-down` (`PageDown`)
- **Selection:**
  `select-char-left` (`Shift+Left`), `select-char-right` (`Shift+Right`),
  `select-word-left` (`Ctrl+Shift+Left`), `select-word-right` (`Ctrl+Shift+Right`),
  `select-line-start` (`Shift+Home`), `select-line-end` (`Shift+End`),
  `select-all` (`Ctrl+A`), `toggle-mark` (`Alt+M`, selection toggle for
  `TERM=linux` and keyboard-only selection)
- **Clipboard and undo:**
  `cut` (`Ctrl+X`), `copy` (`Ctrl+C`), `paste` (`Ctrl+V`),
  `paste-prev` (cycle clipboard history),
  `undo` (`Ctrl+Z`), `redo` (`Ctrl+Y`).
  In terminal programs (`tam-clam`, `tam-edit`, `tam-view`, `tam-file`),
  `cut` and `copy` always sync to the Wayland system clipboard via **OSC 52
  write** (when running under `tam-last` / `foot`) and fall back to an
  internal clipboard buffer on `TERM=linux`. `tam-last` keeps **OSC 52
  read** disabled by default; pasting into a terminal uses bracketed paste
  from `tam-last`.
- **Direct deletion:**
  `delete-char-left` (`Backspace`), `delete-char-right` (`Delete`),
  `delete-word-left` (`Ctrl+Backspace`), `delete-word-right` (`Ctrl+Delete`),
  `kill-line` (`Ctrl+K`),
  `delete-to-line-start`, `delete-to-line-end`
- **Search, refresh, palette, guidance, and mode control:**
  `find` (`Ctrl+F`), `find-next`, `find-prev`,
  `replace` (`Ctrl+R`), `update` (`Ctrl+U`),
  `execute` (`Ctrl+E`), `guidance` (`Ctrl+G`),
  `cancel-mode` (`Escape`)

### 2. Shell-specific (`tam-clam`)

- **Line and prompt control:**
  `accept-line` (`Enter`), `insert-newline` (`Alt+Enter`),
  `kill-line` (`Ctrl+K`, clears current prompt buffer),
  `quit` (`Ctrl+Q`, exits `tam-clam` on empty prompt),
  `clear-screen` (`Ctrl+L`), `open-in-editor` (`Alt+E`),
  `comment-line`, `insert-verbatim`
- **Foreground child control (`termios`):**
  `break` (`Ctrl+\` -> `VINTR` / `SIGINT`; `VQUIT` disabled),
  `pause` (`Ctrl+P` -> `VSUSP` / `SIGTSTP`)
- **History:**
  `up-or-history-prev` (`Up`), `down-or-history-next` (`Down`),
  `find` (`Ctrl+F`, history search), `insert-last-arg`
- **Completion and suggestions:**
  `complete-next` (`Tab`), `complete-prev` (`Shift+Tab`),
  `accept-suggestion` (`Right` at end of line),
  `accept-suggestion-word` (`Ctrl+Right` at end of line)

### 3. Editor, file manager, and viewer actions (`tam-edit`, `tam-file`, `tam-view`, `tam`)

- **Shared document actions:** `save` (`Ctrl+S`), `save-as`,
  `open` (`Ctrl+O`), `new` (`Ctrl+N`), `close` (`Ctrl+D`),
  `quit` (`Ctrl+Q`), `update` (`Ctrl+U`), `replace` (`Ctrl+R`),
  `goto-line`, `duplicate-line`, `toggle-comment`
- **Read-only single-key shortcuts (`tam`, `tam-view`):** Alongside
  `PageUp`/`PageDown`, `Arrows`, `Home`/`End`, and all universal `Ctrl`
  bindings, read-only surfaces support:
  - `Space` — page down (`page-down`)
  - `b` — page up / **b**ack (`page-up`)
  - `/` — find (`find`, alias for `Ctrl+F`)
  - `n` / `Shift+n` (`N`) — next / previous search match (`find-next` / `find-prev`)
  - `q` — quit (`quit`, alias for `Ctrl+Q`)

### 4. `TERM=linux` and compact-keyboard `Alt` fallbacks

Because `TERM=linux` cannot distinguish `Ctrl+Nav` or `Shift+Nav` from
plain navigation (and MacBook, Chromebook, and 60% keyboards lack
dedicated `Delete`/`Home`/`End` keys), every Tamlinux text program also
supports these `Alt` equivalents everywhere:

| Action | Graphical primary | `Alt` fallback | Mnemonic |
| --- | --- | --- | --- |
| `word-left` / `word-right` | `Ctrl+Left` / `Ctrl+Right` | `Alt+,` / `Alt+.` | `<` / `>` physical keys |
| `buffer-start` / `buffer-end` | `Ctrl+Home` / `Ctrl+End` | `Alt+<` / `Alt+>` | Same keys with `Shift` |
| `delete-word-left` / `delete-word-right` | `Ctrl+Backspace` / `Ctrl+Delete` | `Alt+Backspace` / `Alt+D` | Backspace / **D**elete word |
| `toggle-mark` (selection) | `Shift+Nav` | `Alt+M` | **M**ark selection anchor |

### 5. Terminal actions (`tam-last`)

- **Scrollback:** `scroll-page-up` (`Shift+PageUp`),
  `scroll-page-down` (`Shift+PageDown`), `scroll-up`, `scroll-down`
- **Zoom:** `zoom-in` (`Ctrl+=`), `zoom-out` (`Ctrl+-`),
  `zoom-reset` (`Ctrl+0`)
- **Clipboard & search:** `copy` (`Ctrl+C`, when cooked child runs or
  terminal selection active), `paste` (`Ctrl+V`, when cooked child runs,
  using bracketed paste), `terminal-search`

### 6. Compositor actions (`tam-pane`)

All compositor bindings live on `Meta`, `Meta+Shift`, and `Meta+Ctrl`
(`Meta+Alt` stays reserved for text macros per P29). Window resizing
supports **both** non-conflicting styles:

- **Modal Resize mode (`Meta+R`):** Enters a visibly highlighted resize
  mode where `Arrows` resize in normal increments, `Shift+Arrows` in
  **large** increments (bigger, like uppercase), and `Ctrl+Arrows` in
  **small** increments (tighter control); `Enter` or `Escape` exits
  Resize mode.
- **Direct punctuation chords:** `Meta+,`/`.` (horizontal) and
  `Meta+;`/`'` (vertical) for normal increments, `Meta+Shift+,`/`.`/`;`/`'`
  for **large** increments, and `Meta+Ctrl+,`/`.`/`;`/`'` for **small**
  increments.

## Binding file format (proposal)

Every Tamlinux program that supports user rebinding can share one plain
line-oriented syntax (implementable once in `libtam`):

```text
# Comments start with #
bind Ctrl+X cut
bind Ctrl+C copy
bind Ctrl+V paste
bind Ctrl+Z undo
bind Ctrl+Y redo
bind Ctrl+G guidance
bind Ctrl+U update
bind Ctrl+Q quit
bind Shift+Left select-char-left
bind "Ctrl+E s" save-as
unbind Ctrl+T
```

- Canonical modifier order: `Meta+Ctrl+Alt+Shift+<Key>`.
- Multi-key sequences are space-separated inside quotes.
- Single-key and multi-key chords both work, so optional user-supplied
  key maps (such as a readline compatibility file) need no special syntax.

## Next steps

All initial standard-level decisions (modifier contract, physical keyboard
baseline, universal `Ctrl` map, `Ctrl+\` Break / `Ctrl+P` Pause, `Alt`
fallbacks, read-only single-key shortcuts, OSC 52 clipboard policy, and
`tam-pane` resize styles) are settled as of 2026-11-23. Individual
programs (`tam-pane`, `tam-last`, `tam-clam`, `tam`, `tam-edit`,
`tam-file`, `tam-view`) can now reference this standard from their own
`arch/keys.md` files and implement the shared `libtam` binding parser and
standard action map.
