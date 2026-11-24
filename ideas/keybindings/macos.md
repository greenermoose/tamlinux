# macOS (Apple Human Interface Guidelines)

*Reference notes from documented Apple Human Interface Guidelines (1984–present),
Cocoa text system defaults, and macOS Terminal.app.*

## What it is

- **Scope:** Apple's system-wide keybinding architecture across the desktop,
  every native AppKit/SwiftUI application, the standard text-editing widget,
  and the built-in UNIX terminal.
- **Why it matters:** macOS has arguably the cleanest modifier separation in
  mainstream computing because it never forced POSIX `Ctrl` and GUI editing
  shortcuts onto the same physical key.

## Modifier semantics and chord grammar

| Modifier | Role in macOS |
| --- | --- |
| `Command` (`⌘`, thumb key next to Space) | Primary application commands everywhere (`⌘X/C/V/Z`, `⌘S` save, `⌘F` find, `⌘W` close tab/window, `⌘Q` quit app, `⌘N` new, `⌘,` settings, `⌘Space` Spotlight, `⌘Tab` switch app, ``⌘` `` switch window within app) |
| `Control` (`⌃`) | Preserved cleanly for POSIX terminal signals (`⌃C` SIGINT, `⌃Z` SIGTSTP, `⌃D` EOF) **and** basic Emacs-style line editing in every native Cocoa text field (`⌃A`/`⌃E` line start/end, `⌃K` kill to end, `⌃F`/`⌃B`/`⌃P`/`⌃N` move) |
| `Option` (`⌥`, Alt) | Word-level navigation and deletion (`⌥Left/Right`, `⌥Backspace`), alternate characters/diacritics, and alternate variants of menu items (`⌥` held reveals hidden menu options) |
| `Shift` (`⇧`) | Extend selection (`⇧Arrows`, `⌥⇧Arrows`, `⌘⇧Arrows`), reverse direction (`⌘⇧G` find previous, `⌘⇧Tab` reverse switch), or secondary variant (`⌘⇧Z` redo, `⌘⇧S` save as) |
| `Command` + navigation | Line/document boundaries (`⌘Left/Right` line start/end, `⌘Up/Down` document start/end) |
| `Fn` / `Globe` | System-level hardware and emoji/dictation shortcuts |

## Ideas worth taking

- **Strict separation of application commands from POSIX terminal signals — `consider`.**
  macOS proves how liberating it is when Copy (`⌘C`) and Interrupt (`⌃C`)
  do not collide, even inside a terminal emulator. On PC keyboards, `Meta`
  is owned by the compositor (`tam-pane`), so Tamlinux cannot copy `⌘`
  literally without losing compositor separation — but the lesson stands:
  every layer needs unambiguous ownership.
- **`Shift` consistently meaning "reverse" or "extend" — `adopt`.**
  `⌘Z` undo / `⌘⇧Z` redo, `⌘G` find next / `⌘⇧G` find previous, `Tab` /
  `⇧Tab`, `Left` / `⇧Left`. One rule predicts dozens of pairs.
- **Universal text-editing bindings across every text box in the OS — `adopt`.**
  Because Cocoa's standard text view implements one shared binding set,
  users learn movement and deletion once and it works in every app. In
  Tamlinux, `libtam` can play the exact same unifying role across `tam-clam`,
  `tam-edit`, `tam`, and `tam-file`.
- **Standardized `⌘,` for Preferences and `⌘?` for Help — `consider`.**
  Having one reserved key for help (`Ctrl+G` in Tamlinux) and one for
  settings across every app builds instant predictability.

## Things to avoid

- **Overloading `Command` for both app actions and OS window/app switching.**
  `⌘Tab`, `⌘Space`, and `⌘Q` share `Command` with in-app chords; a tiling
  compositor needs its own dedicated modifier (`Meta`) so window/workspace
  chords never collide with applications.
- **Requiring a thumb-positioned `Command` key.**
  PC keyboards place `Alt` (not `Meta`/`Win`) beside the spacebar, and
  Linux text consoles (`TERM=linux`) do not transmit `Meta` to applications.
  Any Tamlinux standard must be comfortable on standard PC keyboards and
  usable on `TERM=linux`.
- **Hidden `Option`-revealed menu items.**
  Undiscoverable shortcuts violate Tamlinux's commitment to transparent
  guidance (`Ctrl+G` / `tam`).

## Where to look

- Apple Developer Documentation, *Human Interface Guidelines: Keyboards*.
- Apple Support, *Mac keyboard shortcuts* and Cocoa `DefaultKeyBinding.dict`.
