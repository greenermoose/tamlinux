# Independent clock shell proof

- **Date**: 2026-10-03
- **CLI Tool**: Cursor `3.21.18`, from `cursor --version`
- **Model**: Composer (`composer`). This session identified itself as Auto, powered by Composer; no finer model id was logged by the CLI.
- **Authorship**: Fred set the antiX direction and asked for the next project step. Cursor implemented the Develop candidate. Fred then ran the proof bar and accepted it.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> We are working to move tamlinux from depending on omarchy linux to being based on antiX Linux Core. Please see the plan and start working on the next step of the tamlinux project. Ask if you have questions.

> I don't understand how I can test this. What is running now and how can I see the clock you've made?

> Okay, I see it and it looked fine. I could not create local events, but I assume that it because you did not implement that feature?

> Great, everything works. Now what?

> Commit it and push it. I'll start step 2 in a separate session.

## Work and decisions

The approved next step was the independent Quickshell host in
[desktop-decoupling.md](../plans/desktop-decoupling.md), not a compositor
backend and not an OS migration. The candidate is `desktop/`: owned
`Tam.Commons` and `Tam.Ui` modules, a bottom bar that does not reserve
exclusive space, and a patched load of pinned `fred.clock` 1.3.3
(`ed5140ccefc83c0a2fdd5f899bbd290acc35d88a`).

The adapter keeps the clock's date logic and helper limits, switches imports
to the owned modules, uses the IPC target `tamlinux.clock`, suppresses the
startup fetch and refresh timer when `TAMLINUX_CLOCK_OFFLINE=1`, and refuses
timezone and event-edit actions in both the UI and IPC. Fixture state stays
under an isolated home in `XDG_RUNTIME_DIR`.

Automated checks covered registry rejection, settings writes, calendar
open/close, format persistence across restart, the offline fetch gate, and
tooltip sizing at scales 1 and 1.25. Fred started the proof bar, said it
looked fine, and then said everything works. Local event creation stayed
disabled in this slice on purpose. The candidate stays in Develop. Step 2
starts in a later session.

## Verification

`desktop/tests/test_host.py` passed (8 tests). `desktop/launch-clock-proof
--selftest` passed at scale 1 and 1.25 on Quickshell 0.3.1 and Qt 6.11.2.
Existing clock `test_fetch.py` and `test_manage.py` passed. `test_limits.py`
failed one pre-existing remote-feed case in this environment; the proof does
not change those helpers.
