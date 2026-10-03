# Shell host contract

- **Date**: 2026-10-03
- **CLI Tool**: Cursor `3.21.18`, from `cursor --version`
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred asked for the next Tamlinux step and then to implement the host-contract plan. Cursor implemented the Develop candidate.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Take the next step on the tamlinux project.

> Step 2: host contract for the other plugins
>
> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## Work and decisions

Step 2 generalizes the clock proof instead of loading the other seven plugins.
The host records the bar and shell calls those plugins make, keeps Hyprland
and `hyprctl` for the compositor step, and leaves the missing shared widgets
unbuilt.

`tamlinux.fixture` is a second widget with `open`, `close`, and `opened`. It
does not register an IPC target. The real clock stays a single instance so
its `tamlinux.clock` handler is registered once. Each output has its own bar:
one popout, its own click targets, and cleanup when that output is removed.
`bar.run` and `summon("omarchy.osd")` are refused. Settings writes succeed
only for a registered plugin id.

## Verification

`desktop/tests/test_host.py` passed (11 tests). `desktop/launch-clock-proof
--selftest` passed at scale 1 and 1.25 on Quickshell 0.3.1. Tooltip probes
were 132×42 at 11px and 168×54 at 14px. Two host copies on one output proved
popout exclusivity, panel switch, click ownership, and cleanup; that copy
pair is simulated. `--output all` then dropped `HDMI-A-1` and left the `DP-2`
and `DP-1` bars in place. The candidate stays in Develop.
