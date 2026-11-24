# KDE Plasma (openSUSE, Fedora KDE, Kubuntu)

*Reference notes from documented KDE Human Interface Guidelines (Plasma 6),
`KStandardShortcut`, and `KGlobalAccel`.*

## What it is

- **Scope:** KDE Plasma is the primary desktop environment of openSUSE
  Tumbleweed/Leap, Fedora KDE Plasma Desktop, Kubuntu, KDE neon, and
  SteamOS desktop mode.
- **Why it matters:** KDE has the most mature **centralized action catalog**
  and user-customizable shortcut architecture in the Linux ecosystem.

## Modifier semantics and chord grammar

| Modifier | Role in KDE Plasma |
| --- | --- |
| `Meta` | Explicitly named **`Meta`** in KDE (not `Super`!). Desktop shell & KWin window management: `Meta` app launcher, `Meta+Left/Right/Up/Down` quick-tile, `Meta+T` tile editor, `Meta+W` overview, `Meta+D` peek desktop, `Meta+L` lock, `Meta+E` Dolphin, `Meta+V` Klipper clipboard history, `Meta+1..9` task manager |
| `Ctrl` + letter | CUA application standard defined centrally in `KStandardShortcut` (`Ctrl+X/C/V/Z`, `Ctrl+Shift+Z` redo, `Ctrl+S` save, `Ctrl+F` find, `Ctrl+Q` quit, `Ctrl+W` close) |
| `Ctrl+Shift` + letter | Konsole terminal actions (`Ctrl+Shift+C/V` copy/paste, `Ctrl+Shift+F` find) and secondary app variants (`Ctrl+Shift+S` save as) |
| `Alt` + key | Window/app legacy (`Alt+Tab` task switcher, `Alt+F4` close, `Alt+Space` KRunner, `Alt+F2` KRunner) and Qt menu accelerators |
| `Ctrl+Alt` + key | Global session/desktop actions (`Ctrl+Alt+T` Konsole, `Ctrl+Alt+Del` leave, `Ctrl+Alt+L` lock) |

## Ideas worth taking

- **Using the name `Meta` everywhere — `adopt`.**
  KDE calls the key `Meta` across UI, docs, and config, matching Tamlinux's
  own settled decision (D217).
- **Centralized standard action registry (`KStandardShortcut`) — `adopt`.**
  Every KDE app binds *named standard actions* (`Copy`, `Paste`, `Undo`,
  `Find`, `Help`, `Quit`) rather than hardcoding raw keycodes. Changing a
  standard shortcut in one place updates every conforming app. This maps
  directly to Tamlinux's `libtam` canonical widget names in
  `arch/keybindings.md`.
- **Global conflict detection and searchable shortcut editor — `adopt`.**
  KDE's System Settings warns immediately when a chord collides across
  components and lets users search by either action name or key press.
- **KRunner (`Alt+Space`) as a universal command/action runner — `consider`.**
  A single fast launcher reduces pressure to assign rare actions to obscure
  3-modifier chords.

## Things to avoid

- **Sprawling default bindings across four modifier prefixes (`Meta`, `Alt`, `Ctrl+Alt`, `Ctrl+Shift`).**
  KDE's default map has accumulated decades of aliases (`Meta+L` and
  `Ctrl+Alt+L`, `Alt+Space` and `Alt+F2`), creating unnecessary overlap
  with terminal and editor bindings.
- **Konsole's `Ctrl+Shift+C/V` split.**
  Same CUA-vs-terminal inconsistency as GNOME.
- **Over-configurability without a strong default narrative.**
  KDE lets you rebind almost anything, but rarely explains *why* a default
  key was chosen or gives a mnemonic (unlike Tamlinux's P14 rationale and
  mnemonic catalog).

## Where to look

- KDE Human Interface Guidelines, *Keyboard Navigation* and *Shortcuts*.
- KDE Frameworks `KConfig` (`KStandardShortcut`) and `KGlobalAccel`
  documentation.
