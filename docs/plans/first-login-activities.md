# First text-login orientation and activities (hi and start)

Status: Draft for Tamlinux 0.6.1; follows decisions D214 and D215.

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
- **Execution:** Runs in text mode in any Linux VT (`/dev/tty1`–`/dev/tty6`)
  or terminal emulator.
- **Behavior:**
  - Displays a clean text banner and an organized menu of actionable choices.
  - Divided into three clear sections:
    1. **Orientation & Learning:**
       - Welcome & orientation (`hi` / `tam hi`)
       - Offline Knowledge Guide (`tam`)
       - Knowledge search (`tam search`)
       - System reference (`tam man`, `tam tldr`, `tam info`)
    2. **Curated Games & Simulations (0.6.1, D214):**
       - Cataclysm: Dark Days Ahead (`cataclysm-dda`)
       - Frotz Interactive Fiction (`frotz`, prompting for a `.z3`/`.z5`/`.z8` story file)
       - BSD Games (`trek`, `adventure`, `atc`, `wump`)
       - Astroterm Celestial Mechanics (`astroterm`)
       - Curse of War Real-Time Logistics (`curseofwar`)
       - GNU Go Spatial Strategy (`gnugo --mode curses`)
       - pMARS Core War VM (`pmars -e` with bundled sample Redcode warriors)
       - Bastet Adversarial Minimax (`bastet`)
       - cbonsai Procedural Botany (`cbonsai`)
       - VMS Empire Strategic 4X (`vms-empire`)
       - NetHack Emergent Physics (`nethack`)
    3. **Desktop Environment:**
       - Launch Graphical Desktop (`tam-desktop`)
    4. **Exit:**
       - Return to shell prompt cleanly (`q` or `0`).
  - **Invariants:**
    - Opening `start` or browsing the menu **never** starts the graphical desktop.
    - Choosing any terminal activity or game **never** starts the graphical desktop.
    - The desktop launches **only** when the user explicitly selects the desktop option.
    - If a game or tool is not yet installed in the current environment, `start`
      shows it as unavailable and provides helpful instructions rather than crashing.
    - When a chosen terminal tool or game finishes, `start` either returns cleanly to
      the menu or exits cleanly back to the login shell prompt without terminal corruption.
    - Supports non-interactive flags:
      - `--help` / `-h`: Displays usage, flags, and exits.
      - `--version` / `-V`: Displays product version and exits.
      - `--list`: Prints available activities in machine- or script-readable format.
  - **Licensing:** GPL-3.0-or-later.

## Packaging and Delivery

Both commands are packaged as part of `tamlinux-commands` in `tamlinux-packages`.
They install to `$PREFIX/bin/hi` and `$PREFIX/bin/start`.

## Verification and Acceptance

- Unit tests in `commands/hi/tests/` verify argument forwarding and fallback.
- Unit tests in `commands/start/tests/` verify argument handling (`--help`, `--version`,
  `--list`), menu rendering, selection execution, non-graphical invariants, and exit behavior.
- Real VT execution proof on supported hardware before launching graphics.
