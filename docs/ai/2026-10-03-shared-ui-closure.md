# Shared UI closure and typed actions

- **Date**: 2026-10-03
- **CLI Tool**: Cursor `3.23.12`, from `cursor --version`. `detect-runtime.sh` reported Antigravity CLI (`agy`) `1.2.16` in this environment; that does not match this session.
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred asked for the next Tamlinux step and then to implement the shared UI plan. Cursor implemented the Develop candidate.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Take the next step in the tamlinux project.

> Shared UI closure and typed actions
>
> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

> Why did you stop here and not finish the rest of this step?

> Let me test what you've done so far for this step.

> Done, please stop it. Then commit and push the work you've done so far on this step.

## Work and decisions

This slice grows the Develop proof host with the shared border, style, and
control types the plugins already bind, and with typed actions that record
a request and do not start a process. `bar.run` still refuses the string.
A `tamlinux.ui` fixture proves the types. It is not a plugin and does not
join the panel switch. The eight plugins are not rewritten, and the daily
bar is unchanged. Product version stays 0.0.1.

## Verification

`desktop/tests/test_ui.py` passed (8 tests). `desktop/tests/test_host.py`
passed (11 tests). `desktop/tests/test_compositor.py` passed (9 tests).
`desktop/launch-clock-proof --selftest` passed at scale 1 and 1.25. Fred
looked at the interactive proof on the first screen and asked to stop it.
The candidate stays in Develop.
