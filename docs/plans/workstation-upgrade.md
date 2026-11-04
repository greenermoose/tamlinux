# Workstation upgrades from a text login

**Status:** Developing for Tamlinux 0.6.7 (K52). Design accepted 2026-10-30;
implementation resumed 2026-11-04 under the single-theme 0.6.7 inclusion.
**Target:** Upgrade a supported existing workstation to a released Tamlinux
assembly from text login, without reinstalling or keeping component clones.

## Current work (0.6.7)

`commands/tam-workstation-upgrade/` now provides:

- Release selection (`release.py`) with plain/annotated tag resolution
- Local host profile and native package identity (`host.py`)
- Compatibility assessment with a reviewed delivery-record adapter (`compat.py`)
- Durable receipts and a single-host lock (`receipt.py`)
- CLI entry point: `--check`, interactive apply, `--version`/`--revision`/`--yes`,
  `--status`, `--recover`
- Apply through `tam-deploy follow`; recover through `tam-deploy back`
- Makefile install under `libexec` with a `bin` symlink

Compatibility schema version 1 is defined by `compat.py`. Deliveries may carry
an explicit `compatibility` object; otherwise a reviewed adapter synthesizes
one from `nativePackage` + `readiness`. Missing metadata blocks as unknown
native requirements, never as “no native changes”.

Still open for later proof on an exact candidate: physical reboot-to-VT
upgrade/recovery, full lock-graph checks beyond direct inputs, settings
migration checkpoints, and archive sha256 confirmation at apply time.

Separately, `tam-deploy` can skip graphical restart and shell IPC when the
user graphical target is inactive, including during rollback.

## Proposed interface

| Invocation | Result |
| --- | --- |
| `tam-workstation-upgrade --check` | Show installed identity, latest eligible release, prerequisites and native requirements; change no managed configuration or installed state. |
| `tam-workstation-upgrade` | Present the same plan and ask before applying it. |
| `tam-workstation-upgrade --version X.Y.Z` | Plan and confirm that particular released version. |
| `tam-workstation-upgrade --version X.Y.Z --revision SHA --yes` | Apply an exact released selection non-interactively; refuse if the release resolves differently. |
| `tam-workstation-upgrade --status` | Show the last local transaction and recovery needed, without network access. |
| `tam-workstation-upgrade --recover TRANSACTION` | Present and confirm recovery to that transaction's recorded previous state. |

The command name and released-version selection are accepted. The expanded interface was accepted with this plan. Check/plan may use bounded temporary
downloads and existing caches, but must not activate, alter the consumer lock,
restart services, request privileged writes or create settings checkpoints.
No desktop dialogs, resident service, polling or automatic upgrades. Distinct
outcomes identify no change, blocked compatibility, failed upgrade and
incomplete recovery; errors state the next useful action.

## Release selection and trust

Use the official `tamlinux-packages` release source. Default to the latest
eligible non-draft, non-prerelease plain `X.Y.Z` release. Explicit versions
must also be releases. Resolve a tag once to a full immutable commit and fetch
all records/build inputs at that commit. Refuse disagreement between version,
delivery identity, lock and expected component sources.

Extend the prototype's shallow input check to the supported lock graph,
including indirect/follows inputs, schema versions and platform. Validate
expected owners/repositories and immutable revisions for all relevant inputs,
not just the product. Bound responses, redirects, retries and timeouts. Test
malformed records, missing/moved/annotated tags and floating aliases. Never
substitute a branch, candidate, release or host profile after confirmation.

Initial trust rests on the official HTTPS source and exact recorded commits,
not a new signature system. Keep the resolved plan stable through apply and
recheck local starting state before mutation. Exact installed identity is a
no-op; same version with a different revision is an error. Older releases need
explicit downgrade review for schema and migration compatibility; version
selection alone must not authorize an unsafe downgrade.

## Local workstation and compatibility

Establish the registered local user/host profile, supported architecture,
consumer configuration, Nix/Home Manager prerequisites, write ownership and
current generation before building. Refuse missing, ambiguous or foreign
profiles. Use a local consumer configuration and exact remote assembly;
component checkouts are unnecessary. Keep settings and credentials local.
Detect consumer schema changes and customized files; report conflicts without
overwriting them or importing another machine's configuration.

Define a versioned compatibility record in the delivery repository: supported
platforms and starting states, consumer schema, migrations, native package
requirements, boot/login procedures and recovery prerequisites. Compare it
with actual local state. Missing native metadata means unknown compatibility,
never “no native changes”. Legacy releases need a reviewed compatibility
adapter or a clear unsupported result; do not rewrite historical records.

Stop before activation when native, boot, login, disk or firmware work is
required. Show the exact requirement and separately reviewed procedure.
Those actions retain individual approval and a rollback point. Do not bundle
privilege grants or call a user-package activation a complete workstation
upgrade. Detect satisfied native requirements by verified identity, not by
version-number comparison alone.

## Apply and recovery

1. Acquire one local upgrade lock. Record the selected plan, current assembly,
   consumer-lock identity and generation in a small transaction receipt.
2. Verify settings recovery covers the files this migration changes. Reuse
   accepted recovery material when its scope and intended contents still fit.
   Distinguish the immediate previous generation from the accepted anchor.
3. Build and validate the exact assembly before active changes. Stage consumer
   edits/migrations, detect conflicts and revalidate the starting state.
   Cancellation and build failure leave the installed state intact.
4. Confirm version, revision, local profile, settings changes and rollback.
   Apply through the packaged deployment mechanism. Extract a shared internal
   transaction API if needed; do not duplicate activation or invoke stage
   promotion commands.
5. Verify installed command/shell/plugin endpoints and assembly identity.
   On a VT, verify files and text-mode services without launching graphics or
   waiting for shell IPC. With graphics active, use the controlled restart
   and readiness path. Unknown session state is an error, not a guess.
6. Mark success only after verification. On failure restore the previous
   consumer pin, generation and applicable settings, then verify recovery.
   If recovery fails, retain the receipt and give exact offline recovery
   instructions; do not report success or erase evidence.

Write receipt phase boundaries atomically to identify interruption during
pinning, settings migration, activation or verification. Resume only a safe,
validated phase or recover explicitly. Settings restoration preserves later
user edits and reports conflicts. Do not automatically garbage-collect or
delete recovery generations, packages or checkpoints. Keep local receipts
small and limited to useful recovery evidence.

## Milestones and acceptance

| Milestone | Deliverable and proof |
| --- | --- |
| Contract | Review CLI, compatibility schema, supported start states, failure outcomes and ownership across product, delivery and consumer configuration. |
| Read-only planning | Test latest/explicit/no-op selection, malformed records, lock graphs, unknown native requirements, foreign profiles, offline/rate-limited discovery and changed starting state. |
| Transaction | Reuse activation with durable receipts, serialization, preserving migrations and recovery. Inject failures at every phase; prove cancellation, interruption and verification failure preserve or recover the previous state. |
| Packaging | Install entry point and runtime dependencies in the recorded assembly. Test a supported consumer with no component clones and no checkout executables on PATH. |
| Physical proof | Reboot to text login; discover, confirm, upgrade, verify and recover without graphics. Exercise supported older starting installations separately, then an already-active graphical session. Verify settings and native-change stops. |
| Completion | Record exact assemblies, observations and limits. Promote only on separate Test, Run and Release instructions. Routine-update confidence needs subsequent real use. |

Tests must prove no stage branches, tags or releases move, no implicit native
or boot mutation occurs, and text-mode apply/recovery never launches graphics.
A two-process test proves concurrent upgrade refusal. Physical recovery must
work without network access after failed activation.

## Next actions for 0.6.7

1. Local trials: `--check` / `--status` on bosgame; unit tests green.
2. Record inclusion on Fred's Include words; package with the 0.6.7 candidate.
3. Bind physical VT upgrade and recovery evidence to the exact Test candidate.
4. Extend lock-graph validation and settings-migration coverage as needed for
   K52 acceptance.
