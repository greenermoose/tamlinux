# First bundle delivery and return to Home Manager

The first Nix-to-bundle bridge is implemented in source and verified with
isolated fixtures. It has not been installed or accepted on a workstation.
Nix/Home Manager remains the daily delivery and recovery mechanism.
Subsequent bundle updates, registered-account `init` without a Nix profile,
and their undo paths now pass isolated fixtures. The source remains gated
on complete portable desktop-state coverage before workstation migration.

## Continuation checkpoint

The coordinator retains the original Nix recovery identity across later
bundle deliveries. Ordinary `back` returns one bundle and its switch-time
settings; `return-nix ID` selects the original Nix recovery path directly.
Fresh-account preparation records no invented generation, and undo restores
the account's original settings or their absence before detaching the bundle.
It still requires a registered consumer/host record. The independent
`tam-bundle` install path remains the portable bootstrap path.

The native defaults and named capture list now cover the private menu,
Chromium extension files, native messaging registrations in each supported
browser, Chromium flags, portal settings, autostart and additional terminals.
Known generated registrations are validated before replacement. Custom
generated forms and remaining Nix/development-prefix references stop with
the affected path; settings are audited again at switch time.

An additional source gate was found: theme/background selection and desktop
preferences also live beneath `.local/state/tamlinux`. The capture engine
excludes that directory to protect its journals and avoid capture recursion.
Preparation now refuses an installation with these active UX files instead
of silently omitting them. A bounded portable representation, restoration
and interruption proofs for that UX state remain required. Do not relax the
whole-state exclusion or follow arbitrary background symlinks to close it.

The stage coordinator selects the deploy operator carried in the exact
recorded bundle. Its archive and operator bytes are bound to preparation and
the Test digest. Test pauses after preparing the console transaction and
short `bundle-on.sh` / `bundle-undo.sh` helpers. It records installation only
on resume after the exact receipt, product and user settings agree. Helper
checksums bind their executable; foreign scripts are preserved. Each root
operation retains its polkit authorization. Real console authorization is
still a machine proof. Run requires bound user acceptance and energy evidence.
The stage draft also refuses absent or stale frozen suite evidence for every
selected component, including native tools. Recording those native tools
results in the frozen bundle packaging workflow remains an integration gate;
the existing Nix Package/Test route has not been changed to select bundles.

Canceling a prepared update also requires `tam-bundle cancel-settings` from
tool 0.13.0: the completed system must identify the exact retained completed
user record, and the abandoned plan must still be ready. This restores user
readiness without changing settings. Applying settings cannot be abandoned.

## Preparation

A recorded assembly selects a portable archive by its SHA-256, full bundle
hash, component commits and frozen recipe commit. Read-only preflight keeps
its existing behavior. Installation preparation additionally:

1. Requires a coherent Nix baseline and a per-host assembly pin.
2. Saves its exact generation, pin bytes, receipt and immutable package
   outputs. Checks `hosts/<hostname>/bundle-nix-recovery.json` first and
   falls back to `system/bundle-nix-recovery.json` to identify the
   separately reviewed native rollback archive by host, package, version,
   absolute archive path and SHA-256. The archive's package metadata must
   agree. This record does not install anything.
3. Reads the carried settings and placement lists and identifies only home
   links belonging to the saved generation. Foreign links and local commands
   that would shadow the selected product are refused.
4. Builds a Home Manager generation by extending the recorded consumer
   evaluation. Shell, session and tool delivery are disabled; converted home
   paths are disabled; development libraries are withdrawn. Unrelated user
   packages remain. The new generation must supply no `tam`, `tam-*`, `hi`
   or `start` command through `home-path/bin`.
5. Records the immutable target generation and exact target pin bytes. The
   first migration is prepared in user state only: root prepare waits until
   console conversion, so the boot trigger cannot race Home Manager links.

No settings bytes are captured at preparation. The two generated startup
files are checked against their known delivery-module forms; custom forms
require explicit migration.

## Console activation

`activate-bundle ID` is bound to the recorded transaction, account, host,
consumer, saved generation and pin. It requires an inactive graphical target
and unlocked sessions. The exact archive is checked again.

The private home-link journal copies settings at switch time, retains their
original links and publishes real files by same-filesystem renames. Directory
links are materialized as directories, preserving their other contents.
Files, copies and journals are synced. Foreign replacements stop retries.

The privileged tool archives a verified dormant format-1 slot beneath
`legacy-v1`; it does not relabel an old hash as format 2. The old state and
kept payloads remain retained. A busy slot or pending legacy switch refuses.
The first format-2 transaction therefore starts without a current link.

The coordinator prepares the exact carried archive with `--expect-bundle`,
checks the target's full hash and transaction id, prepares the user's plan
and applies the system part. Only after system completion do the old product
links and generated session overrides leave. The delivery-free Home Manager
generation activates, then settings apply and both halves must agree. Full
product checks precede the receipt and pin update. Preparation retries retain
an existing settings plan and its switch-time capture.

The bundle supplies real defaults for the Hyprland entry and UWSM environment
files that Home Manager used to generate. They refer to the versioned product
and native executables.

## Return to the exact saved generation

`recover ID`, or `back` from this first bundle delivery, selects the recorded
Nix baseline. It does not guess a previous generation or reevaluate package
outputs. Console recovery:

1. Finishes an applying system transaction forward, or cancels one that has
   not applied. It refuses unrelated system identities.
2. Detaches only the selected full bundle hash. A durable transaction keeps
   startup blocked while placed files and the current link leave. Corrupt
   rollback copies, live edits, native ownership conflicts and busy processes
   refuse. Archives, version trees and placed-file copies stay retained.
3. Moves later real settings into private `returned/` entries and restores
   the exact original Home Manager links. It never overwrites their original
   mutable source files with bundle-era edits.
4. Stops until the separately approved native package restoration has the
   recorded version and archive identity. No package operation is automatic.
   A durable detachment marker allows retry after that restoration replaces
   tam-bundle with the older tool.
5. Restores the exact saved pin bytes and activates the exact saved Nix
   generation, then verifies endpoints, profile and runtime before restoring
   its receipt.

## Verification and limits

The [implementation record](../ai/2026-11-11-bundle-delivery-integration.md)
separates the real C-engine fixtures from the unactivated Nix build and from
unperformed workstation acceptance. Private PID namespaces and private `/proc`
remain mandatory for all process/signal tests, without a host fallback.

Before a real migration, finish portable mutable desktop-state coverage,
frozen native-tools suite integration and the full carried-UX audit, then
review the concrete source and console
helpers. Rebuild the tool, bootstrap and workstation archive from the reviewed
exact commits. The previous recipe source pins remain frozen; no new bundle
candidate has been selected. No candidate number or stage word is implied.

The remaining machine gates include the selected sacrificial workstation,
physical interruption, console authorization/repair, native package replacement
and verified Nix return. Exact Test, Run and Release remain separate decisions;
retain an accepted recovery anchor before any Nix retirement.
