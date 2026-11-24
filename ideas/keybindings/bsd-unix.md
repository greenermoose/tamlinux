# Actively Maintained BSD UNIX Systems (FreeBSD, OpenBSD, NetBSD, DragonFly BSD)

*Reference notes from documented FreeBSD, OpenBSD, NetBSD, and DragonFly
BSD base systems, consoles (`vt(4)`, `wscons(4)`), `termios(4)`, and
OpenBSD's `cwm(1)`.*

## What it is

- **Scope:** The four major actively maintained BSD UNIX operating
  systems — **FreeBSD**, **OpenBSD**, **NetBSD**, and **DragonFly BSD** —
  each shipped as a complete, cohesive base OS (kernel + console + shell +
  editor + utilities, and in OpenBSD's case, X11 and window managers).
- **Why it matters:** BSD systems preserve classic, clean UNIX terminal
  ergonomics and include two standout ideas that Linux lacks by default:
  `Ctrl+T` (`SIGINFO`) and OpenBSD's minimalist keyboard-first `cwm(1)`.

## Modifier semantics and chord grammar

| Layer | BSD convention |
| --- | --- |
| **Console / VT (`vt(4)` FreeBSD, `wscons(4)` OpenBSD/NetBSD)** | `Ctrl+Alt+F1`..`F8` switch virtual terminals; `ScrollLock` + `Arrows`/`PgUp`/`PgDn` hardware/console scrollback (still supported on FreeBSD `vt(4)` and `wscons`!); `Alt+F*` switches VTs on FreeBSD `vt` |
| **TTY line discipline (`termios(4)`)** | Standard POSIX (`Ctrl+C` `VINTR`, `Ctrl+Z` `VSUSP`, `Ctrl+\` `VQUIT`, `Ctrl+D` `VEOF`, `Ctrl+U` `VKILL`, `Ctrl+W` `VWERASE`, `Ctrl+S`/`Ctrl+Q` `VSTOP`/`VSTART`) **plus `Ctrl+T` (`VSTATUS` -> `SIGINFO`)** |
| **`Ctrl+T` (`SIGINFO`)** | Pressing `Ctrl+T` while *any* foreground command runs (`dd`, `cp`, `tar`, `fsck`, `sleep`, `make`) prints a one-line live kernel + program status report (load, CPU, process state, bytes/progress) without interrupting the command! |
| **Base shells (`ksh` on OpenBSD/NetBSD, `sh`/`tcsh` on FreeBSD)** | Dual line-editing modes (`set -o emacs` default in OpenBSD `ksh`; `set -o vi` optional); `Ctrl+R` reverse history search, `Tab` completion |
| **OpenBSD `cwm(1)` (Calm Window Manager, in base)** | Pure keyboard-driven stacking/grouping WM using `Ctrl+Alt` (`CM-`) as its primary modifier: `CM-Return` terminal, `CM-/` search windows by title, `CM-?` exec program, `CM-M` maximize, `CM-F` fullscreen, `CM-H/J/K/L` move window, `CM-1..9` window groups, `CM-x` close, `M-Tab` cycle windows |

## Ideas worth taking

- **`SIGINFO` / live status key (`Ctrl+T` on BSD) — `consider`.**
  Asking "what is this running command doing right now?" with a single
  non-destructive keystroke is one of the best UX inventions in UNIX
  history. Even though Linux `termios` lacks `VSTATUS`, Tamlinux's
  `tam-last` / `tam-clam` could offer a status/progress inspection chord
  or signal convention.
- **OpenBSD `cwm`'s instant fuzzy window search (`/` for windows, `?` for exec) — `adopt`.**
  Searching open windows by title with one keystroke eliminates hunting
  across workspaces.
- **Cohesive base-system consistency — `adopt`.**
  Because OpenBSD and FreeBSD own their kernel, console, shell, and
  documentation together, `man` pages accurately document every default
  binding. Tamlinux has that same vertical ownership across `tam-pane`,
  `tam-last`, `tam-clam`, and `tam`.

## Things to avoid

- **`cwm`'s `Ctrl+Alt` (`CM-`) as the window-manager modifier.**
  `cwm` predates widespread `Meta`/`Super` usage; putting WM bindings on
  `Ctrl+Alt+<letter>` collides with terminal and editor chords. `Meta` is
  strictly cleaner for `tam-pane`.
- **Shipping two completely different shell keymaps (`emacs` and `vi` modes) by default.**
  Splitting a shell into modes fragments documentation and muscle memory;
  Tamlinux's `arch/keybindings.md` rightly chooses one standard map with
  expressive user rebinding.

## Where to look

- FreeBSD `termios(4)`, `vt(4)`, and Handbook (Consoles and Terminals).
- OpenBSD `cwm(1)`, `cwmrc(5)`, `wscons(4)`, and `ksh(1)` man pages.
- NetBSD `wscons(4)` and `termios(4)`.
