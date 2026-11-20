# Give the input method one startup owner

Status: approved by Fred on 2026-10-20; implementation and disposable-VM
verification complete for Develop 0.4.4-l. Workstation installation and stage promotion require
separate authorization. A candidate letter is chosen separately.

## Problem and evidence

A fresh Arch installation of the 0.4.4-k assembly starts Fcitx through two
paths: Arch's `org.fcitx.Fcitx5.desktop` XDG autostart entry and Tamlinux's
`tam-fcitx5.service`. The autostart instance owns `org.fcitx.Fcitx5`; the native
unit exits successfully when that name is occupied, then `Restart=always`
starts it again. The observed restart count increased twice in three seconds.

This is a clean-install integration defect. Installed package ownership and a
working shell do not establish a healthy input-method startup. Existing consumer
configuration can conceal the duplicate, so the repair needs a clean login test.

## Proposed repair

Keep Tamlinux's native user unit as the default owner. It starts Fcitx without
the notification-area item and follows `graphical-session.target`.

1. The Home Manager session module supplies a user-level
   `autostart/org.fcitx.Fcitx5.desktop` entry with `Hidden=true`. This overrides
   the vendor autostart entry for that user; it does not modify Arch's file.
   An explicit consumer definition retains precedence.
2. Change the native unit to `Restart=on-failure`. A successful exit because
   another user-selected Fcitx instance already owns the name must leave the
   unit stopped. Unexpected failures still restart.

Keep the input-method environment, Compose behavior and Fcitx package selection.
Do not terminate or replace an existing user-selected input-method process.
Retire the override if the selected upstream package supplies a compatible,
single-owner systemd startup path and the clean-login proof passes without it.

## Verification and delivery

Before proposing the next Test candidate:

- Check the generated session module and native unit together, including
  consumer override precedence and the successful-exit restart policy.
- Build recorded native/user packages from exact committed sources. Inspect
  their file ownership, source manifest and archive identities.
- On a disposable clean Arch VM, activate the packages and perform two native
  logins. Verify one Fcitx bus owner, no active vendor autostart instance and a
  stable zero-restart native unit. Verify the shell and nine plugins still load.
- Exercise the existing-owner case: a healthy separately selected Fcitx process
  remains the bus owner; starting the native unit does not create a restart loop.
- Bind the new package identities and input-method observations to the unchanged
  independence gate. Preserve the k results under their original identities.

Fred's separate Test instruction is required before changing the workstation.
Prepare its native package rollback and obtain each privileged-step approval.
After Test, collect the affected login/input observation and final-candidate
install/preserving-rollback evidence. Assess earlier boot and sleep evidence by
the actual source/configuration delta; do not repeat unrelated trials for logs.

The normal-delay sleep proof, accepted-Run recovery review and exact-candidate
Run instruction remain separate requirements. This repair authorizes no Test,
Run, tag or Release.

## Develop result — 2026-10-20

Source `1aa4eaf51046d05c74142935c7ed39486315f8d6` and VM assembly
`08db32396673141c3ef731242289b7f67a443315` pass the planned package/module
checks, two native logins and existing-owner test. Both logins have one Fcitx
owner, zero restarts, an inactive vendor autostart instance and nine loaded
plugins. Native archive identity and summary are recorded in the assembly's
`deliveries/tamlinux-0.4.4-l.json`. The consumer override evaluation passes.

The package proof is ready for a separate Test decision. Workstation native
rollback, physical login/input observation and affected preserving rollback
remain to execute under that instruction. Earlier k gate failures remain
recorded under k; l is no full-gate or Run pass.
