# Sway integration after the independent Hyprland baseline

**Status — 2026-10-07:** prepared compositor candidates retained; integrated
Sway work deferred until stage 0.6 is accepted. First prove Tamlinux on Hyprland
without Omarchy; then prove Tamlinux on Sway. Arch remains the host distribution
through 1.0. Existing adapter prototypes are not an accepted package/session.

## Stage 0.7 — Integration and installable session

| Proposed step | Work and required evidence |
| --- | --- |
| **0.7.0** | Workspace/monitor helper contract on both adapters; unchanged Hyprland behavior; Sway layout preview/keep/revert/timeout and bounded failure/restoration. |
| **0.7.1** | Night light on both adapters with key/menu/indicator agreement and clear tool failure/unsupported results. |
| **0.7.2** | Screenshots, region/window selection, recording, OCR/QR and color picking; compositor geometry and image-pixel conversion tested at fractional scales/transforms. |
| **0.7.3** | Nix package plus native Arch host adapter; installed Sway session beside Hyprland; `tam install verify`, login, driver bridge, PAM, portals/keyring and update/rollback proof. |
| **0.7.4** | Bounded monitor recovery and physical verification of restored working outputs; unsupported/unverified outcomes explicit. |

Finalize or split these boundaries before implementation starts. Reuse the
accepted Tamlinux settings/state migration from 0.4, with compositor-specific
topology validation; no second legacy-data migration. Workspace/monitor Sway
functionality uses the chosen plugin 2.1.0 line, carrying forward accepted fixes.

Select helpers through the common compositor contract, with unknown adapters
rejected, bounded execution, validated facts and explicit partial failure.
Preserve each compositor's authoritative logical layout; do not impose uniform
rounding. Workspace helper IDs and output facts must satisfy actual helper
requirements rather than the smaller shell-UI snapshot. Real IPC tests exercise
multi-output layout/movement/power and failed persistence/restoration paths.

Sway persistence uses explicitly included
`~/.config/sway/config.d/tamlinux-outputs.conf`, with rule precedence, validated
atomic save and a preserved prior layout. Preview never replaces the saved
layout; Keep persists verified state; Revert/timeout restore previous live
state. Mutable files are included separately in rollback.

Interim Reset changes to another supported refresh rate, verifies reported
state, restores the original mode/layout and reports that physical link
retraining remains unverified. No alternative rate means unavailable; failures
trigger bounded restoration and retain evidence. Stronger recovery remains
required: command acceptance, mode read-back and a compositor log do not prove
that a display is working correctly.

## Package and physical proof

The Nix flake contains pinned Sway/Qt/Quickshell, shell/plugins, fonts, selected
desktop tools and `tam`/knowledge. The native host adapter supplies session
entry, locker PAM, groups/udev and graphics-driver integration. Native host
kernel/firmware, graphics, audio/network services and vendor apps retain their
owners. The [installation framework](installation-framework.md) defines bounded
inspect/plan/apply/verify and recovery.

After software checks, test the delivered session on physical outputs: scale,
rotation, disconnect/reconnect, DPMS/input wake, saved layouts, sleep/resume
and applicable faults. Distinguish configured state, link status, presentation
and observable stability over a defined interval. Visible jitter may require
user confirmation. Headless tests cannot establish physical recovery.

## Stage 0.8 — Daily Sway proof; 1.0 — removal

Daily-drive Sway with the accepted independent Hyprland session available for
fallback. Acceptance requires all eight plugins, keyboard/workspace/display
behavior, menus, themes/fonts, applications, capture, popup focus/dismissal,
idle/Stay Awake, sleep/resume and applicable reliability hooks to work. Resolve
required parity gaps and record secondary-hardware limits explicitly.

Preserve exact deployed payloads, live configuration, mutable layouts/state and
native/boot recovery. Switching sessions must not copy Sway topology blindly
into Hyprland. After accepted daily use and a recorded backup/rescue route,
plan 1.0 removal of Hyprland, its portal/config and carried patches. A mode-only
or headless result cannot authorize that removal. Publication/releases remain
separate lifecycle actions; this planning change does not deploy code.
