# Compositor contract and Hyprland adapter

- **Date**: 2026-10-03
- **CLI Tool**: Cursor `3.23.12`, from `cursor --version`. `detect-runtime.sh` reported Antigravity CLI (`agy`) `1.2.16` in this environment; that does not match this session.
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred asked for the next Tamlinux step and then to implement the compositor-contract plan. Cursor implemented the Develop candidate.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Take the next step on the tamlinux project.

> Step 3: compositor contract and Hyprland adapter
>
> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## Work and decisions

Step 3 adds a compositor facade the shell and a fixture read. The Hyprland
adapter is the only new shell file that imports `Quickshell.Hyprland` or
starts `/usr/bin/hyprctl`. Commands are a fixed argv list, a closed
environment, and a short deadline. Output names and workspace ids are checked
before they are placed in a command. There is no generic `hyprctl` argument
list.

`focusWorkspace`, `focusOutput`, and `setDpms` record the request unless
`TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. The proof launcher removes that
variable. `tamlinux.compositor` reads the facade and does not import
Hyprland. The seven plugins are unchanged. Layout rewrite, reload, monitor
reset, and a Sway backend stay later.

## Verification

`desktop/tests/test_compositor.py` passed (9 tests) without running
`hyprctl`. `desktop/tests/test_host.py` passed (11 tests).
`desktop/launch-clock-proof --selftest` passed at scale 1 and 1.25 on
Quickshell 0.3.1. The clock checks stayed green, including tooltip probes of
132×42 at 11px and 168×54 at 14px. The same runs compared output names, the
focused output, and active workspace ids with one `hyprctl -j monitors`
snapshot. Bindings text and the keymap were non-empty and within their caps.
Recorded focus and DPMS lines appeared. Live action lines did not. The
candidate stays in Develop.
