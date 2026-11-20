# fred.sysinfo reads the compositor facade

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

fred.sysinfo 2.0.0 on `develop/2.0.0` no longer imports `Quickshell.Hyprland` or
starts `/usr/bin/hyprctl` from QML. IPC uses the facade's focused output name. `SysinfoPanel` takes keyboard focus only when that output is the panel's screen.

The running Omarchy bar was not replaced. This is not a tag or a release.

## Verification

- Plugin QML in this repository contains neither `Quickshell.Hyprland` nor
  `/usr/bin/hyprctl`.
- The isolated host selftest at scale 1 and 1.25 registered this plugin with
  the other seven. The log did not mention `qs.Commons` or `qs.Ui`.
