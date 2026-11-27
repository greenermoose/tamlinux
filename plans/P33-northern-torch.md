# P33: Northern Torch — tam-pane everywhere and complete Hyprland removal

- **Status:** in progress (version 0.7.2 on branch `dev`; Milestones 1–8 done on `dev`, 9–17 remaining)
- **Versions:** 0.7.0 to 0.7.x

## Goal

Move the workstation and fleet laptops onto `tam-pane` (alongside
`tam-last`, `tam-clam`, `tam-edit`, `tam-view`, and `tam-hide`), replace
every Hyprland helper and ecosystem tool, delete all Hyprland code and
configuration from `tamlinux`, and remove the Hyprland package tree and
every superseded dependency. Northern Torch is done when we count on
`tam-pane` as our only compositor and Hyprland is completely gone.

## Versions and milestones

### Stage 1 — Bosgame desktop bring-up and default switch (0.7.0–0.7.1)

1. **Account for every app (done, W26):** Build a checklist of all apps,
   launchers, bindings, shell services, and plugin manifests with
   `tam-pane` recovery paths.
2. **Deliver a reproducible session (done, W31):** Pin `tam-pane`,
   `tam-hide`, `tam-last`, `tam-clam`, `tam-edit`, `tam-view`, and
   `libtam` in `plans/P21-source-install.md` with `XWAYLAND=0`.
3. **Provide guarded console launches (done, W33):** Add
   `tam-desktop pane` and `tam-desktop hyprland` with local VT,
   duplicate-session, and clean shutdown checks.
4. **Bring up the complete session (done, W34):** UWSM session target,
   systemd/D-Bus env export, Quickshell, `xdg-desktop-portal-wlr`,
   polkit, file chooser, and PipeWire screen sharing.
5. **Connect the shell to `tam-pane` (done, W36):** `TamPaneAdapter` +
   `ProtocolState` (`plans/P6-compositor-protocol-layer.md`) supporting
   multi-tag per-output views and automatic reconnect.
6. **Port bosgame's controls and ergonomics (done, W37):** Translate
   monitor geometry/scale, focus-follows-mouse, focus border, window
   rules, shortcuts, mouse bindings, autostart, and macros into
   `tam-pane.lua`.
7. **Prove the shell, plugins, and C17 apps (done, W38):** Exercise bar,
   menus, notifications, themes, all nine `fred.*` plugins, and
   `tam-last`/`tam-clam`/`tam-edit`/`tam-view` with Hyprland stopped.
8. **Automate repeatable checks and benchmarks (done, W39):** Run
   `plans/P10-desktop-test-battery.md` on headless `tam-pane` and compare
   latency/memory/power via `tam-session-bench`.
9. **Prove hardware, locking, and recovery on bosgame (next, awaits Test):**
   Physical VT switch, multi-monitor drag, unplug/replug, blank/wake,
   `tam-hide` lock/unlock, suspend/hibernate, and GPU renderer-loss
   recovery.
10. **Accept daily use and make `tam-pane` the default (awaits Run):**
    Full-day use without fallback; switch bare `tam-desktop` and `start`
    to `tam-pane`.

### Stage 2 — Replace Hyprland helpers and port fleet controls (0.7.2–0.7.x)

11. **Locking, idle, and sleep/wake to `tam-hide` + `tam-pane`:**
    Retire `hyprlock`, `hypridle`, and `hyprlock.conf`.
12. **Replace `hyprsunset` and `hyprpicker`:** Native `tam-pane` gamma
    control and Wayland screencopy/pixel sampling.
13. **Port laptop display, clamshell, input, and window commands off
    `hyprctl`:** Prove `tam-pane` on the fleet laptops.
14. **Decouple themes, menus, and Tensaku from Hyprland:** Style
    `tam-pane` directly and remove `hyprland.lua.tpl` and `hypr_gradient`.

### Stage 3 — Purge Hyprland code and remove dependencies (0.7.x completion)

15. **Delete all Hyprland code, adapters, configs, commands, and hooks
    from `tamlinux`:** `tam-desktop` launches `tam-pane` exclusively.
16. **Remove Hyprland, Aquamarine, and superseded dependencies across
    the fleet:** Strip `hypr*`, `aquamarine`, and test-only `sway` from
    `arch-packages`, `preflight.py`, and fleet hosts.
17. **Verify clean builds, fleet-wide operation, and Northern Torch
    closure:** `make`, `make preflight`, `make install`, `tests/check-all`,
    and `tam-desktop-test` pass with zero Hyprland references.

## Acceptance

- Headless and physical desktop suites pass on `tam-pane` alone.
- Zero `hypr*` or `aquamarine` packages remain on the fleet.
- Fred's Test, Run, and Release words govern every stage move.

## Dependencies

`tam-pane`, `tam-hide`, `tam-last`, `tam-clam`, `tam-edit`, `tam-view`,
`libtam`, Quickshell, `xdg-desktop-portal-wlr`, UWSM.

## Risks

- Hardware display/resume regressions on physical GPUs; mitigated by
  keeping Hyprland fallback until Milestone 10 and Snapper rollback
  points before login or package-removal steps.

## Open points

- Exact candidate authorization for Milestone 9 hardware Test and
  Milestone 10 default switch.
