# Helper Hyprland commands use the named backend

- **Date**: 2026-10-03. Status notes were completed on 2026-10-04.
- **CLI Tool**: Cursor `3.23.12`, from `cursor --version`. `detect-runtime.sh` reported Antigravity CLI (`agy`) `1.2.16` in this environment; that does not match this session.
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred asked for the next Tamlinux step and then to implement the Hyprland-command plan. Cursor implemented the Develop candidate.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Continue with the next step for the tamlinux project.

> Move helper Hyprland commands into the adapter
>
> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

> finish the plan status, the proof README, and the provenance notes

## Work and decisions

`compositor_commands.py` builds the remaining helper argv. `hyprland_backend.py` is the only Python that starts `hyprctl`, and only for a named operation. Reads run. Mutations record unless `TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. The layout helper does not write `monitors.lua` unless that flag is set.

`tam-desktop-mode` and the three monitor helpers on `develop/2.0.0` call that backend. They no longer embed Hyprland command text. Brightness still uses the Omarchy helper. The running bar was not replaced. Tamlinux stays 0.0.1. A Sway adapter is the next slice.

## Verification

- `desktop/tests/test_compositor.py` passed (17). `test_host.py` passed (11). `test_ui.py` passed (8).
- Workspace desktop-mode tests passed (42). Monitor layout tests passed (10). Monitor state tests passed (3).
- `launch-clock-proof --plugins --selftest` at scale 1 and 1.25 registered all eight plugins. The proof rejected any live compositor action.
