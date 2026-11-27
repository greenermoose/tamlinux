# P33: Northern Torch — tam-pane everywhere and complete Hyprland removal

- **Phase:** PH03
- **Status:** In progress. At `0.7.5` (Test accepted 2026-11-27; `0.6.42`
  released as the KBN WB recovery anchor), Stage 1 bring-up (M1–M8) and
  Stage 2 helper-replacement wiring and dogfood polish (`0.7.3–0.7.5`)
  are done. Fleet-wide physical acceptance (M9 and M11–M14 hardware
  proof), daily-use default switch (M10), and complete Hyprland removal
  (M15–M17) remain open.
- **Versions:** 0.7.0 to 0.7.x

## Goal

Move the workstation and fleet laptops onto `tam-pane` (alongside
`tam-last`, `tam-clam`, `tam-edit`, `tam-view`, `tam-data`, `tam-knox`,
and `tam-hide`), replace every Hyprland helper and ecosystem tool, delete
all Hyprland code and configuration from `tamlinux`, and remove the
Hyprland package tree and every superseded dependency. Northern Torch is
done when we count on `tam-pane` as our only compositor and Hyprland is
completely gone.

## Versions and milestones

### Stage 1 — Desktop bring-up and C17 suite (0.7.0–0.7.2, Done 2026-11-26)

M1–M8 landed across `0.7.0–0.7.2` with automated and headless proofs
passing and Hyprland kept as an independent recovery session.

1. **Account for every app (W26, Done):** Built a checklist of all apps,
   launchers, bindings, shell services, and plugin manifests with
   `tam-pane` recovery paths.
2. **Deliver a reproducible session (W31, Done):** Pinned `tam-pane`,
   `tam-hide`, `tam-last`, `tam-clam`, `tam-edit`, `tam-view`, `tam-data`,
   `tam-knox`, and `libtam` for the [locked source install](P21-source-install.md)
   with `XWAYLAND=0`.
3. **Provide guarded console launches (W33, Done):** Added
   `tam-desktop pane` and `tam-desktop hyprland` with local VT,
   duplicate-session, and clean shutdown checks.
4. **Bring up the complete session (W34, Done):** Wired the UWSM session
   target, systemd/D-Bus env export, Quickshell, `xdg-desktop-portal-wlr`,
   polkit, file chooser, and PipeWire screen sharing.
5. **Connect the shell to `tam-pane` (W36, Done):** Built `TamPaneAdapter`
   and `ProtocolState` ([protocol layer](P06-compositor-protocol-layer.md))
   supporting multi-tag per-output views and automatic reconnect.
6. **Port daily-use controls and ergonomics (W37, Done):** Translated
   monitor geometry/scale, focus-follows-mouse, focus border, window
   rules, shortcuts, mouse bindings, autostart, and macros into
   `tam-pane.lua`.
7. **Prove the shell, plugins, and C17 apps (W38, Done):** Exercised the
   bar, menus, notifications, themes, all nine `fred.*` plugins, and
   `tam-last`/`tam-clam`/`tam-edit`/`tam-view` with Hyprland stopped.
8. **Automate repeatable checks and benchmarks (W39, Done):** Migrated
   the [desktop test battery](P10-desktop-test-battery.md) onto headless
   `tam-pane` and added `tam-session-bench` for startup and resource
   comparison.

### Stage 2 — Helper-replacement wiring and dogfood polish (0.7.3–0.7.5, Done 2026-11-27)

Replacement workflows were wired in `0.7.3` ahead of the default switch,
followed by cultivar metadata hardening in `0.7.4` and `tam-pane 0.4.1`
dogfood ergonomics and optional visuals in `0.7.5`. Physical fleet proof
of these workflows runs in Stage 3 before Hyprland fallback is retired.

- **0.7.3 (Done 2026-11-27, W45) — M11–M14 development wiring on `tam-pane 0.3.0` and `tam-hide 0.3.1`:**
  11. **Locking, idle, and sleep/wake to `tam-hide` + `tam-pane`:**
      Wired `tam-system-sleep-lock` to `tam-pane msg lock_state` and
      updated `tam-hide` (`0.3.1`) toward retiring `hyprlock` and `hypridle`.
  12. **Replace `hyprsunset` and `hyprpicker`:** Wired `tam-toggle-nightlight`
      to native `tam-pane` gamma IPC and capture/color-picking tools to
      native `freeze`/`capture`/`pixel` IPC.
  13. **Port laptop display, clamshell, input, and window commands off `hyprctl`:**
      Wired ten laptop, display, input, and window commands to `tam-pane` IPC
      (and updated `tam-last` for Right Alt synthetic modifiers).
  14. **Decouple themes, menus, and Tensaku from Hyprland:** Styled
      `tam-pane` directly via `tam-pane.lua.tpl` and live-reloaded borders
      on theme switches; `hyprland.lua.tpl` and `hypr_gradient` removal
      follows in Stage 4.
- **0.7.4 (Done 2026-11-27) — Cultivar identity fix and guard:**
  Updated `CULTIVAR` to `Northern Torch` so the pre-login console banner
  and installed cultivar metadata match, and added a build-time
  `VERSION`/`CULTIVAR` consistency guard in `src/desktop/install-product.py`.
- **0.7.5 (Done 2026-11-27, Test accepted, W47) — `tam-pane 0.4.1` dogfood polish and visuals:**
  Packaged `tam-pane 0.4.1`, preserving focus-follows-mouse, preventing
  release-bound macro keys from repeating in clients, opening default
  Dwindle windows to the right or below within 8 logical pixels of the
  split midpoint, and including optional Mesa GLES2 rounded corners and
  drop shadows (off by default).

### Stage 3 — Physical and fleet acceptance and default switch (0.7.x, In progress)

9. **Prove hardware, locking, recovery, and M11–M14 workflows on the fleet:**
   Record physical checks for the tested candidate: VT switch,
   multi-monitor drag, unplug/replug, blank/wake, `tam-hide` lock/unlock,
   suspend/hibernate, GPU renderer-loss recovery, and physical verification
   of the M11–M14 replacement workflows across the primary workstation and
   fleet laptops, incorporating any daily-use bugfixes from `0.7.5` onward.
10. **Accept daily use and make `tam-pane` the default (awaits Run):**
    Complete sustained full-day use without Hyprland fallback, then switch
    bare `tam-desktop` and `start` defaults to `tam-pane` on Fred's Run
    instruction.

### Stage 4 — Complete Hyprland removal and Northern Torch closure (0.7.x, Planned)

Start removal after the Stage 3 default switch and fleet acceptance of the
M11–M14 replacement workflows.

15. **Delete all Hyprland code, adapters, configs, commands, and hooks
    from `tamlinux`:** `tam-desktop` launches `tam-pane` exclusively;
    remove `hyprland.lua.tpl`, `hypr_gradient`, and `hyprlock.conf`.
16. **Remove Hyprland, Aquamarine, and superseded dependencies across
    the fleet:** Strip `hypr*`, `aquamarine`, and test-only `sway` from
    `arch-packages`, `preflight.py`, and fleet hosts (each package-removal
    step with Fred's approval and a recorded rollback point).
17. **Verify clean builds, fleet-wide operation, and Northern Torch
    closure:** `make`, `make preflight`, `make install`, `tests/check-all`,
    and `tam-desktop-test` pass with zero Hyprland runtime or build
    dependencies; release Northern Torch on Fred's word.

## Acceptance

- Headless and physical desktop suites pass on `tam-pane` alone.
- Zero `hypr*` or `aquamarine` packages remain on the fleet.
- Fred accepts daily use on `tam-pane` and separately authorizes Release.

## Dependencies

`tam-pane`, `tam-hide`, `tam-last`, `tam-clam`, `tam-edit`, `tam-view`,
`tam-data`, `tam-knox`, `libtam`, Quickshell, `xdg-desktop-portal-wlr`,
UWSM.

## Risks

- Hardware display/resume regressions on physical GPUs; mitigated by
  keeping Hyprland fallback through the fleet trials and Snapper rollback
  points before login or package-removal steps.

## Open points

- Fleet laptop proof of M11–M14 replacement workflows and remaining
  Stage 3 hardware/recovery checks.
- Exact candidate authorization for the M10 default switch and Stage 4
  Hyprland package removal.
