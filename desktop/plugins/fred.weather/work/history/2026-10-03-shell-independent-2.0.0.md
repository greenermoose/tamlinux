# Shell-independent plugin 2.0.0

- **Date**: 2026-10-03
- **CLI Tool**: Cursor `3.23.12`, from `cursor --version`. `detect-runtime.sh` reported Antigravity CLI (`agy`) `1.2.16` in this environment; that does not match this session.
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred asked to rewrite each plugin off the Omarchy shell, then to commit and push. Cursor implemented the Develop candidate.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Continue with the next step for the tamlinux project. Rewrite each plugin as fred.<id> 2.0.0 without depending on the omarchy shell, then replace the daily bar. Ask if you have questions. Update the tamlinux version when you reach a milestone that should trigger a version bump.

> Rewrite the eight plugins as 2.0.0, then replace the bar

> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

> Run the plugins so I can test them.

> Stop the test bar. Why are the bar icons not in the correct place? The clock should be centered, for example, and the workspaces should be on the left.

> Commit and push your work.

## Work and decisions

`fred.weather` 2.0.0 imports Tamlinux shell types. A right-click asks the
host to notify a plain status string built in the panel. The Omarchy IPC
handler is gone. This branch is not tagged or released.

## Verification

The isolated host registered `fred.weather` on each output. This repository
has no separate Python suite.
