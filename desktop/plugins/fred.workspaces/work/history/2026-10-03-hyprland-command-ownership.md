# Workspace helper uses the named compositor backend

- **Date**: 2026-10-03
- **CLI Tool**: Cursor `3.23.12`, from `cursor --version`. `detect-runtime.sh` reported Antigravity CLI (`agy`) `1.2.16` in this environment; that does not match this session.
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred asked to move the helper Hyprland commands into the Tamlinux adapter. Cursor implemented the Develop candidate on `develop/2.0.0`.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Move helper Hyprland commands into the adapter
>
> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## Work and decisions

`tam-desktop-mode` no longer builds Hyprland command text. Switch, move, focus, DPMS, and layout repair call named operations on the shell backend. The closed helper environment forwards the command-module path and the live-action flag. Not tagged or released.

## Verification

- `tests/test_desktop_mode.py` passed (42).
