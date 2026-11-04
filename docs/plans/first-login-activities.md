# First text-login orientation and activities (hi and start)

Status: Draft for Tamlinux 0.6.x; follows decisions D214 and D215.

## Context and Goal

Tamlinux boots cleanly to a text virtual terminal (VT) before any optional
graphical session. On first login, a new user arrives at a bare shell prompt.
Fred identified this experience as a usability gap:

> "The reason to include games and simulations in 0.6 is that I consider it
> a problem that there is nothing fun to do with your computer from the CLI
> when you first boot it. We should have two commands ready:
>   - hi, which starts tam hi
>   - start, which shows a list of things you can do with your computer
>     (including the games and simulations and starting your desktop shell
>     if you want a GUI)"
> — Fred (D215)

The goal is to provide two bare, packaged entry points directly on `PATH`
at text login before starting any graphical desktop:
1. `hi`: orientation entry point that immediately invokes `tam hi`.
2. `start`: terminal activities menu presenting actionable learning,
   curated terminal games and simulations, and explicit optional desktop launch.

Neither command requires X11, Wayland, or Quickshell to function.

## Specification

### 1. `hi` — Text Orientation Command

- **Location:** `commands/hi/hi`
- **Execution:** When run, it executes `tam hi "$@"` via `exec`.
- **Arguments:** Transparently forwards all options and flags (e.g. `--pipe`,
  `-p`) to `tam hi`.
- **Fallback:** If `tam` is not found on `PATH`, it reports a clear diagnostic
  message to standard error and exits with code 1.
- **Licensing:** GPL-3.0-or-later.

### 2. `start` — Terminal Activities Menu

- **Location:** `commands/start/start`
- **Own version:** `commands/start/VERSION` (semver). The footer row shows
  navigation hints on the left and right-aligned `vX.Y.Z`; `--version` prints
  `start X.Y.Z`.
- **Execution:** Runs in text mode in any Linux VT (`/dev/tty1`–`/dev/tty6`)
  or terminal emulator with a keyboard-driven menu (cbreak input, alternate
  screen). Redraws use row diffs (cursor address + erase-to-EOL), not a full
  clear on every key — the same anti-flicker approach as the `tam` pager.
- **Behavior:**
  - Displays a clean text banner and an organized menu of actionable choices.
  - **First choice** is Start graphical desktop shell (`tam-desktop`), letter `a`.
  - Remaining sections keep orientation/learning and curated games/simulations.
  - **Letters** select commands: sequential `a`…`z` in menu order. There is no
    quit letter.
  - **Attention line** matches `tam`: charcoal background (256-color index 236)
    with pale foreground (15), or reverse video otherwise; ASCII `>` gutter when
    color is off. Up/Down move the attention line. Right Arrow or Enter runs the
    attended choice (same as pressing its letter).
  - **Footer:** `Down/Up Arrow scroll  Home top  End bottom  Backspace quit`
    left-aligned, `vX.Y.Z` right-aligned.
  - **Quit:** Backspace or Delete ends the menu and returns to the shell prompt.
  - **Paging** uses the real terminal height. When there is more than one screen:
    PgDn or Space shows the next screen; PgUp or `` ` `` shows the previous;
    Home shows the first screen and moves attention to the first choice; End shows
    the last screen and moves attention to the last choice.
  - Choosing any activity runs it once, then exits to the shell (does not return
    to the menu).
  - Divided into sections:
    1. **Graphical Desktop:**
       - Start graphical desktop shell (`tam-desktop`) — letter `a`
    2. **Orientation & Learning:**
       - Welcome & orientation (`hi` / `tam hi`)
       - Offline Knowledge Guide (`tam`)
       - Knowledge search (`tam search`)
       - System reference (`tam man`)
    3. **Curated Games & Simulations (D214):**
       - Cataclysm: Dark Days Ahead (`cataclysm-dda`)
       - Frotz Interactive Fiction (`frotz`, prompting for a story file)
       - BSD Games (`trek`, …)
       - Astroterm, Curse of War, GNU Go, pMARS, Bastet, cbonsai, VMS Empire, NetHack
  - **Invariants:**
    - Opening `start` or browsing the menu **never** starts the graphical desktop.
    - Choosing any terminal activity or game **never** starts the graphical desktop.
    - The desktop launches **only** when the user explicitly selects the desktop option.
    - If a game or tool is not yet installed, `start` shows it as unavailable and
      provides helpful instructions rather than crashing.
    - After a chosen tool finishes (or is declined), `start` exits cleanly back to
      the login shell prompt without terminal corruption.
    - Supports non-interactive flags:
      - `--help` / `-h`: Displays usage, flags, and exits.
      - `--version` / `-V`: Displays start's own semver and exits.
      - `--list`: Prints available activities with letters.
      - `--check`: Reports which activities are installed; ends with `vX.Y.Z`.
  - **Licensing:** GPL-3.0-or-later.

## Packaging and Delivery

Both commands are packaged as part of `tamlinux-commands` in `tamlinux-packages`.
They install to `$PREFIX/bin/hi` and `$PREFIX/bin/start`. `start` also installs
`$PREFIX/share/start/VERSION`.

## Verification and Acceptance

- Unit tests in `commands/hi/tests/` verify argument forwarding and fallback.
- Unit tests in `commands/start/tests/` verify argument handling (`--help`,
  `--version`, `--list`, `--check`), letter mapping with desktop first, attention
  / paging / quit keys, single-run-then-exit selection, non-graphical invariants,
  and the `vX.Y.Z` footer.
- Real VT execution proof on supported hardware before launching graphics.
