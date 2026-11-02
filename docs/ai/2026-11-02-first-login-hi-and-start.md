# First text-login commands: hi and start

- **Date**: 2026-11-02
- **CLI Tool**: Antigravity CLI (`agy`) `1.4.12`
- **Model**: `gemini-3.8-flash`
- **Transcript**: Retained privately by the author.

## Prompts

> Read /home/fred/Code/tamlinux/improvements-fred-tamlinux/reports/2026-11-02-0.6-development-handoff.md and follow plans 49/50. Continue your curated 0.6.1 work, including hi and the start activities menu. Preserve existing work and follow D212–D215. Begin with the repository-state checks in the handoff.

## Changes

Antigravity implemented the two bare console entry points requested in D215 for first text login before graphics:

1. **`hi` command (`commands/hi/`)**:
   - Packaged executable command installed to `$PREFIX/bin/hi`.
   - Executes `tam hi "$@"` directly to present the existing Tamlinux welcome orientation.
   - Forwards all arguments transparently (such as `--pipe`) and provides clean error reporting if `tam` is missing.

2. **`start` activities menu (`commands/start/`)**:
   - Packaged executable command installed to `$PREFIX/bin/start`.
   - Runs in text mode directly in any Linux virtual terminal (`/dev/tty1`–`/dev/tty6`) without X11, Wayland, or Quickshell.
   - Categorizes actionable CLI exploration into Orientation & Learning, Curated Games & Simulations (targeting 0.6.1, D214), and Graphical Desktop (`tam-desktop`).
   - Strictly enforces D215 invariants: opening the menu never launches graphics, selecting a terminal activity never launches graphics, and the desktop launches only on explicit user choice (`d`). Exits cleanly back to the shell prompt on `q` or `0`.
   - Provides non-interactive flags `--help`, `--version`, `--list`, and `--check`.

3. **Public Plan**:
   - Created `docs/plans/first-login-activities.md` documenting the design, behavior, and invariants, and indexed it in `docs/plans/README.md`.

## Verification

- `make -C commands/hi check`: unit tests verify shell syntax, argument forwarding to `tam hi`, and missing command handling.
- `make -C commands/start check`: 9 unit tests verify Python syntax, non-interactive flags (`--help`, `--version`, `--list`, `--check`), menu rendering, non-graphical activity execution, explicit desktop launch, and clean exit.
- Live CLI trials verify `hi --pipe` displays the orientation guide and `start --list` / `start --check` correctly query available and missing tools.
