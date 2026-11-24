# Nano, Micro, and VS Code / JetBrains IDEs

*Reference notes from documented GNU Nano, Micro (the historical ancestor
of `tam-edit`), Visual Studio Code, and JetBrains IDE keybinding systems.*

## What it is

- **Scope:** Three influential non-modal editing systems that bridge
  terminal ergonomics, CUA familiarity, and large-scale discoverability:
  - **GNU Nano:** The default beginner-friendly UNIX terminal editor,
    famous for its always-visible two-line shortcut footer.
  - **Micro:** Modern terminal editor (direct inspiration for `tam-edit`)
    that proved standard desktop CUA works cleanly in a raw-mode terminal.
  - **VS Code & JetBrains IDEs:** Modern CUA + **Command Palette**
    architectures managing hundreds of commands cleanly.

## Modifier semantics and chord grammar

| Program | Modifier & chord model |
| --- | --- |
| **GNU Nano** | `Ctrl` (`^`) for primary actions, `Alt` (`M-`) for secondary toggles; **always-visible bottom hint bar** (`^G` Help, `^O` WriteOut, `^W` Where Is, `^K` Cut, `^U` Paste, `^X` Exit). Non-CUA historical defaults (inherited from Pico). |
| **Micro** | Full desktop CUA inside a raw terminal (`ISIG`/`IXON` off): `Ctrl+S` save, `Ctrl+Q` quit, `Ctrl+C`/`Ctrl+X`/`Ctrl+V` copy/cut/paste, `Ctrl+Z`/`Ctrl+Y` undo/redo, `Ctrl+A` select all, `Ctrl+F` find, `Ctrl+G` **help**, `Ctrl+E` **command bar** (type any named action), `Ctrl+D` duplicate line, `Ctrl+K` cut line, `Alt+Up/Down` move line, `Shift+Arrows` select, `Ctrl+Arrows` word jump. |
| **VS Code** | CUA base (`Ctrl+X/C/V/Z/S/F/A/W/P`) + **`Ctrl+Shift+P` Command Palette** (fuzzy-search every named action and see its bound key) + **two-step chords** (`Ctrl+K Ctrl+S` keyboard shortcuts, `Ctrl+K Ctrl+C` comment, `Ctrl+K Ctrl+W` close all). |
| **JetBrains IDEs** | CUA base + **`Shift Shift` Search Everywhere** + **`Ctrl+Shift+A` Find Action** + contextual `Alt+Enter` ("show intentions / quick actions"). |

## Ideas worth taking

- **Micro's proof that CUA works cleanly in a raw-mode terminal — `adopt`.**
  Disabling `ISIG`/`IXON` in raw mode lets `Ctrl+C/X/V/Z/S/F/Q/G` work
  identically in `tam-edit`, `tam-clam`, `tam-file`, and `tam-view` —
  matching graphical apps with zero mental context switch.
- **`Ctrl+G` for contextual Help / Guidance (Nano & Micro) — `adopt`.**
  Already an anchor in `arch/keybindings.md` (`Ctrl+G` = `guidance`).
- **Command Palette / Action Search over canonical names (VS Code / Micro `Ctrl+E`) — `adopt`.**
  Because every Tamlinux command has a canonical hyphenated name
  (`copy`, `undo`, `word-left`, `guidance`), a universal action palette
  lets users run rare commands by name *and* teaches them the shortcut at
  the same time.
- **Compact optional hint bar on the bottom line (Nano) — `consider`.**
  In text-mode tools (`tam`, `tam-edit`, `tam-view`, `tam-file`), a single
  unobtrusive status/hint line showing `Ctrl+G Guidance` and 4–5 key
  anchors makes every surface immediately usable on first launch without
  memorization.
- **Two-step chords (`Ctrl+K ...` in VS Code) — `consider`.**
  Two-key chords are far easier to press and work on `TERM=linux`, unlike
  `Ctrl+Shift+<letter>` or 3-modifier chords.

## Things to avoid

- **Nano's non-CUA legacy letters (`^O` save, `^W` find, `^K` cut, `^U` paste, `^X` exit).**
  Constant collision with modern muscle memory (`Ctrl+W` closes tabs
  everywhere else; `Ctrl+X` cuts everywhere else).
- **VS Code's heavy reliance on `Ctrl+Shift+<letter>` and `Ctrl+Alt+<letter>`.**
  `Ctrl+Shift+<letter>` fails on `TERM=linux` and legacy terminal encoding.
- **Nano's `^X` / `M-X` notation.**
  Physical key names (`Ctrl+X`, `Alt+X`) are clearer to every user.

## Where to look

- `tam-edit/ideas/micro.md` and Micro's `runtime/help/defaultkeys.md`.
- GNU Nano Manual, *Shortcut Keys*.
- VS Code Documentation, *Key Bindings for Visual Studio Code*.
