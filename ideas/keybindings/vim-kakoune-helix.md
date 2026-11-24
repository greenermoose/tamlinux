# vi / Vim / Neovim and Kakoune / Helix

*Reference notes from documented vi/Vim/Neovim, Kakoune, and Helix modal
keybinding systems.*

## What it is

- **Scope:**
  - **vi / Vim / Neovim:** The foundational modal text editor family,
    built around a composable `<operator> <motion/text-object>` language.
  - **Kakoune & Helix:** Modern successors that reverse the grammar to
    **selection-first** (`<motion/selection> -> <action>`) and add
    multi-cursor editing and (in Helix) built-in live **which-key**
    prefix popups.
- **Why it matters:** Modal systems represent the highest-efficiency
  grammar ever designed for text manipulation — and Helix shows how to
  make deep keybinding trees immediately discoverable.

## Modifier semantics and chord grammar

| System | Grammar & key philosophy |
| --- | --- |
| **vi / Vim / Neovim** | Separate modes (**Normal**, **Insert**, **Visual**, **Command-line**) eliminate modifier keys during navigation/editing. Composable grammar: `[count] <verb> <object>` (`d w` delete word, `c i "` change inside quotes, `y a p` yank a paragraph, `/` search, `n`/`N` next/prev match, `u` undo, `Ctrl+R` redo, `Escape` return to Normal). |
| **Kakoune** | Reverses to `<object/selection> -> <verb>`: `w` selects next word (visible on screen immediately), then `d` deletes it or `c` changes it. `Shift` extends the current selection (just like CUA `Shift+Arrows`!). |
| **Helix** | Kakoune's selection-first grammar + **built-in live popup menus** for every prefix key: `g` (go to: `g g` file start, `g e` file end, `g h` line start, `g l` line end), `m` (match/surround), `Space` (picker/workspace/diagnostics), `[` / `]` (prev/next jump). Zero plugins needed for discoverability. |

## Ideas worth taking

- **Selection-first visual confirmation (Kakoune / Helix) — `adopt`.**
  Seeing what is selected *before* pressing Cut (`Ctrl+X`), Copy
  (`Ctrl+C`), or Delete prevents mistakes. CUA `Shift+Arrows` already
  shares this exact mental model!
- **Helix's built-in, zero-config prefix popups — `consider`.**
  If Tamlinux uses any two-step chord or prefix key (in `tam-pane`,
  `tam-edit`, or `tam`), showing a clean live menu of valid continuations
  makes the chord self-teaching.
- **Uniform `Shift` = reverse / extend across read-only and editable surfaces — `adopt`.**
  In Vim/less/Helix, `n` = next match and `N` (`Shift+n`) = previous
  match; in Kakoune/Helix/CUA, `Shift` extends selection.
- **Read-only surfaces (`tam`, `tam-view`, `less`) can safely support plain single-key shortcuts — `consider`.**
  When a surface is *not* accepting typed text (like a pager or help
  browser), plain keys like `/`, `n`/`N`, `q`, `Space`, and `g`/`G` are
  effortless — **provided** the universal `Ctrl` equivalents (`Ctrl+F`,
  `Ctrl+G`, `Ctrl+Q`, `Escape`) also work identically everywhere!

## Things to avoid

- **Making modal editing the default OS-wide input model — `reject`.**
  Modal editing is superb inside a dedicated code editor for users who
  opt into it, but as a universal default across a shell prompt, file
  manager, dialogs, and desktop apps it causes mode confusion and a steep
  cliff for everyday users. Tamlinux's `arch/keybindings.md` rightly ships
  one non-modal standard map (while allowing expressive user rebinding).
- **Unmnemonic or legacy-hardware keys (`h/j/k/l` on modern keyboards).**
  `h/j/k/l` existed because the ADM-3A terminal had arrows painted on
  those four keys. Modern keyboards have dedicated arrow keys.

## Where to look

- Vim `:help usr_04.txt` (motion/operator grammar).
- Kakoune Design Philosophy (`github.com/mawww/kakoune/blob/master/doc/design.asciidoc`).
- Helix Keymap Documentation (`docs.helix-editor.com/keymap.html`).
