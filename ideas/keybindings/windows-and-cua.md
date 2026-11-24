# IBM CUA and Microsoft Windows

*Reference notes from documented IBM CUA (1987–1991) and Microsoft Windows
(Win32, Windows 10/11, Windows Terminal) standards.*

## What it is

- **Scope:** IBM Common User Access (CUA) defined the cross-application
  shortcut standard for OS/2 and Windows 3.x; Microsoft Windows evolved it
  into the world's most widely known desktop keybinding system.
- **Reach:** Billions of users; the de facto muscle-memory baseline for
  text editing, web browsers, and office software across Windows and Linux.

## Modifier semantics and chord grammar

| Modifier | Role in CUA / Windows |
| --- | --- |
| `Ctrl` + letter | Primary application actions (`Ctrl+X` cut, `Ctrl+C` copy, `Ctrl+V` paste, `Ctrl+Z` undo, `Ctrl+Y` redo, `Ctrl+A` select all, `Ctrl+S` save, `Ctrl+F` find, `Ctrl+O` open, `Ctrl+N` new, `Ctrl+W` close tab, `Ctrl+P` print) |
| `Ctrl` + navigation | Scale up movement/deletion from character to word or document (`Ctrl+Left/Right` word jump, `Ctrl+Home/End` document start/end, `Ctrl+Backspace/Delete` word delete) |
| `Shift` + navigation | Extend text selection in the same direction as the unmodified motion; composable with `Ctrl` (`Ctrl+Shift+Right` selects one word right) |
| `Shift` + `Tab` | Reverse focus / reverse completion |
| `Alt` + letter | Menu bar mnemonics (`Alt+F` File, `Alt+E` Edit) |
| `Alt` + special | Window manager legacy (`Alt+Tab` switch window, `Alt+F4` close window, `Alt+Space` window menu) |
| `Win` (`Meta`) | Added in Windows 95 for OS/shell actions (`Win` Start menu, `Win+D` desktop, `Win+E` Explorer, `Win+L` lock, `Win+Arrows` snap/tile, `Win+Tab` task view, `Win+V` clipboard history, `Win+1..9` taskbar) |
| Legacy CUA clipboard | `Ctrl+Insert` copy, `Shift+Insert` paste, `Shift+Delete` cut (still widely supported in Linux terminals because they avoid `Ctrl+C`/`Ctrl+V` collisions) |

## Ideas worth taking

- **Ergonomic bottom-left editing cluster (`Ctrl+Z/X/C/V`) — `adopt`.**
  All four sit under the left hand without moving off home row, and every
  modern user already knows them. Already anchored in `arch/keybindings.md`.
- **Orthogonal `Ctrl` (scale) and `Shift` (select/reverse) composition — `adopt`.**
  `Left` = char, `Ctrl+Left` = word, `Shift+Left` = select char,
  `Ctrl+Shift+Left` = select word. Learning two modifier meanings yields
  an entire matrix of navigation and selection commands with zero memorization.
- **`Meta` (`Win`) for OS/compositor layer — `adopt`.**
  Separating desktop/window management onto `Meta` keeps OS bindings out
  of application space.
- **`F1` for help, `F2` for rename, `Escape` for cancel — `consider`.**
  Consistent plain-key anchors that work on both graphical desktops and
  the Linux console without modifiers.

## Things to avoid

- **`Ctrl` overloaded between CUA editing and POSIX terminal signals.**
  Windows itself suffers from this in Windows Terminal / PowerShell / WSL:
  `Ctrl+C` means both Copy and Interrupt, forcing awkward context-dependent
  hacks or `Ctrl+Shift+C/V` workarounds.
- **Splitting window management across `Alt` and `Win`.**
  Keeping `Alt+Tab` and `Alt+F4` on `Alt` while putting tiling and
  workspaces on `Win` leaves `Alt` fragmented between compositor and apps.
- **Inconsistent redo (`Ctrl+Y` vs. `Ctrl+Shift+Z`).**
  Windows apps disagree on redo; Tamlinux should pick one clear rule and
  apply it everywhere.
- **Menu-bar `Alt+<letter>` hijacking.**
  Pressing and releasing `Alt` alone focuses menu bars in Win32 apps,
  which conflicts with `Alt` as a clean secondary modifier in terminal and
  keyboard-driven apps.

## Where to look

- IBM, *Systems Application Architecture: Common User Access Guide to User
  Interface Design* (1991).
- Microsoft Learn, *Keyboard shortcuts in Windows* and *Windows Terminal
  Actions* documentation.
