# Sway adapter, first slice

- **Date**: 2026-10-04.
- **CLI Tool**: Cursor `3.23.12`, from `cursor --version`. `detect-runtime.sh` reported Antigravity CLI (`agy`) `1.2.16` in this environment; that does not match this session.
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred asked for the next Tamlinux step. Cursor wrote the Sway-adapter plan, and Fred then asked to implement it. Cursor implemented the Develop candidate.
- **Commit**: This commit.
- **Transcript**: Not found — details unverified. Searched the local Cursor transcript store for this session's prompts.

## Guiding prompts

> Continue with the next step for the tamlinux project.

> Sway adapter, first slice
>
> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## Work and decisions

`SwayAdapter.qml` is the only shell file that imports `Quickshell.WindowManager` or `Quickshell.I3`. The facade loads it only when `TAMLINUX_COMPOSITOR=sway`. The Hyprland proof stays the default.

Workspace lists prefer ext-workspace window sets. Outputs, focus, position, and DPMS come from i3 IPC. Named mutations build one fixed request and are recorded unless `TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. `sway_commands.py` holds the matching `swaymsg` argv and does not run it. This slice does not start `swaymsg`.

Bindings come from a generated `bindsym` fragment. Only workspace-number and focus-output commands are kept. The keymap comes from a bounded `get_inputs` fixture. The workspace and monitor helpers still call the Hyprland backend. The running bar was not replaced. Tamlinux stays 0.0.1.

## Verification

- `desktop/tests/test_sway.py` passed (11). `desktop/tests/test_compositor.py` passed (17).
- `launch-clock-proof --selftest --compositor sway` at scale 1 and 1.25 matched the fixture snapshot. Focus and DPMS were recorded. The log did not contain `hyprctl` or `swaymsg`.
- `launch-clock-proof --selftest` at scale 1 and 1.25 still loaded the Hyprland adapter, checked the physical outputs, and registered all eight plugins.
