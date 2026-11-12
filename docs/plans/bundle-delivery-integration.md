# First bundle delivery and return to Home Manager

The first Nix-to-bundle bridge is implemented in source and verified with
isolated fixtures. It has not been installed or accepted on a workstation.
Nix/Home Manager remains the daily delivery and recovery mechanism.
Fresh-account `init` and subsequent bundle-to-bundle delivery still refuse;
they require the next integration slice.

## Preparation

A recorded assembly selects a portable archive by its SHA-256, full bundle
hash, component commits and frozen recipe commit. Read-only preflight keeps
its existing behavior. Installation preparation additionally:

1. Requires a coherent Nix baseline and a per-host assembly pin.
2. Saves its exact generation, pin bytes, receipt and immutable package
   outputs. Requires `system/bundle-nix-recovery.json` to identify the
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

Before a real migration, complete the generated-file/settings coverage audit
(including menu and browser registrations), package/profile integration and
the reviewed short console activation/return scripts. Subsequent bundle
updates, fresh-account delivery and stage-coordinator completion remain source
gates. Rebuild the approved tool and bootstrap from exact commits before
selecting a candidate. No candidate number or stage word is implied here.

The remaining machine gates include the selected sacrificial workstation,
physical interruption, console authorization/repair, native package replacement
and verified Nix return. Exact Test, Run and Release remain separate decisions;
retain an accepted recovery anchor before any Nix retirement.
