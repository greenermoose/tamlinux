# illumos and System V / SVR4 UNIX (OpenIndiana, OmniOS, SmartOS, Motif/CDE)

*Reference notes from actively maintained illumos distributions
(OpenIndiana, OmniOS, SmartOS), Solaris/SVR4 `termios` conventions, and
the Motif / Common Desktop Environment (CDE) standard.*

## What it is

- **Scope:** **illumos** is the actively maintained open-source descendant
  of OpenSolaris / SunOS / SVR4 UNIX, powering **OpenIndiana** (desktop
  with MATE), **OmniOS** (server/enterprise), and **SmartOS** (hypervisor).
  Commercial SVR4/POSIX UNIX systems (**Solaris**, **AIX**, **HP-UX**) also
  remain in enterprise maintenance.
- **Why it matters:** SVR4 UNIX and its graphical desktop standard
  (**Motif / CDE**) shaped both POSIX `termios` control characters and the
  X11/CUA clipboard conventions (`Ctrl+Insert`, `Shift+Insert`,
  `Shift+Delete`) that still survive inside Linux terminals today.

## Modifier semantics and chord grammar

| Layer | SVR4 / illumos / Motif-CDE convention |
| --- | --- |
| **TTY line discipline (`stty(1)` / `termios(3C)`)** | Canonical POSIX controls: `Ctrl+C` (`intr`), `Ctrl+\` (`quit`), `Ctrl+D` (`eof`), `Ctrl+Z` (`susp`), `Ctrl+U` (`kill`), `Ctrl+W` (`werase`), `Ctrl+S`/`Ctrl+Q` (`stop`/`start`), `Ctrl+V` (`lnext` — literal next character). Historically `erase` was `Ctrl+H` (`0x08`) or `#`, later standardized on `DEL` (`0x7F`) |
| **Motif / CDE (and IBM CUA alignment)** | Adopted CUA's non-`Ctrl+letter` clipboard chords so GUI editing would not collide with UNIX `Ctrl+C`/`Ctrl+V`: `Ctrl+Insert` copy, `Shift+Insert` paste, `Shift+Delete` cut, `Alt+Backspace` undo, `Alt+F4` close, `Alt+Tab` switch window, `F1` help, `F10` menu bar |
| **Sun Type 5/6/7 keyboards (Solaris heritage)** | Dedicated physical keys on the left block: `Stop`, `Again`, `Props`, `Undo`, `Front`, `Copy`, `Open`, `Paste`, `Find`, `Cut`, plus `Help` — proving how ergonomic dedicated action keys are when hardware provides them |
| **OpenIndiana (MATE desktop)** | Modern illumos desktop inherits GNOME 2 / MATE CUA shortcuts (`Ctrl+X/C/V/Z`, `Alt+F2`, `Ctrl+Alt+Arrows` workspaces, `Ctrl+Shift+C/V` in `mate-terminal`) |

## Ideas worth taking

- **`Ctrl+Insert` / `Shift+Insert` / `Shift+Delete` as secondary compatibility aliases — `consider`.**
  Because Motif/CUA placed clipboard actions on `Insert`/`Delete`, they
  never collide with `Ctrl+C` (`SIGINT`) in third-party terminals or remote
  SSH sessions. Worth keeping in mind as optional secondary terminal-level
  aliases even though Tamlinux's primary anchors are `Ctrl+X/C/V`.
- **Literal-next (`lnext`) / verbatim insertion concept — `adopt`.**
  Knowing how to insert a literal keystroke when needed (`insert-verbatim`
  is already listed in `arch/keybindings.md`) is a timeless UNIX escape
  hatch.
- **Dedicated single-press semantics (Sun Type 6 `Help`/`Undo`/`Find`) — `consider`.**
  On standard PC keyboards, `F1`–`F12` are the closest equivalent to
  dedicated action keys and work identically on `TERM=linux` and Wayland.

## Things to avoid

- **Relying on `Insert` / `Delete` chords as the *primary* user-facing clipboard bindings.**
  On modern laptop keyboards, `Insert` is often missing or buried behind
  an `Fn` layer. `Ctrl+X/C/V` is far more ergonomic and universal.
- **`Ctrl+S` / `Ctrl+Q` software flow control (`IXON`) freezing terminals.**
  An artifact of 1970s serial modems that still traps users who press
  `Ctrl+S` expecting "Save." Tamlinux programs in raw mode (`tam-clam`,
  `tam-edit`, `tam-view`) disable `IXON` so `Ctrl+S` is cleanly freed.
- **`Backspace` (`0x08` vs `0x7F`) ambiguity.**
  Historically the worst UNIX terminal papercut; Tamlinux standardizes
  unambiguously via `tam-last` + `libtam` (`tam_key` round-trip tests).

## Where to look

- illumos `termios(4I)` and `stty(1)` manual pages (`illumos.org/man`).
- Open Group, *Motif and CDE Style Guide*.
- OpenIndiana MATE desktop documentation.
