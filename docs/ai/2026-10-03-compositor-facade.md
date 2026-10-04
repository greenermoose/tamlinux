# Plugin QML reads the compositor facade

- **Date**: 2026-10-03
- **CLI Tool**: Cursor `3.23.12`, from `cursor --version`. `detect-runtime.sh` reported Antigravity CLI (`agy`) `1.2.16` in this environment; that does not match this session.
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred asked for the next Tamlinux step and then to implement the compositor-facade plan. Cursor implemented the Develop candidate.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Continue with the next step for the tamlinux project.

> Point the 2.0.0 plugins at the compositor facade
>
> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## Work and decisions

Step 5's first slice points plugin QML at `bar.compositor`. The Hyprland
adapter remains the only file in `desktop/` that imports Hyprland or starts
`hyprctl`. Each output snapshot now includes a description capped at 128
characters, integer coordinates, and whether a special workspace is showing.

`tam-desktop-mode` and the monitor layout, state, and reset helpers still
call Hyprland. A Sway adapter is later in the same step. The running bar was
not replaced. Tamlinux stays 0.0.1.

## Verification

- `desktop/tests/test_host.py` passed (11). `test_compositor.py` passed (10),
  including the plugin-QML boundary. `test_ui.py` passed (8).
- `launch-clock-proof --plugins --selftest` at scale 1 and 1.25 registered
  all eight plugins. The logs did not mention `qs.Commons` or `qs.Ui`.
