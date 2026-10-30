# Workstation upgrades from a text login

**Status:** Expanded plan accepted by Fred, 2026-10-30. Implementation
deferred to 0.6. Plan acceptance authorizes the design; development of this
command resumes in 0.6.
**Target:** Upgrade a supported existing workstation to a released Tamlinux
assembly from text login, without reinstalling or keeping component clones.

## Current work and the 0.5 boundary

The prototype contains `commands/tam-workstation-upgrade/release.py` and five
release-selection tests. It resolves plain release tags and annotated tags,
reads the delivery record and lock at the resolved commit, and compares their
direct inputs. All five tests pass as of 2026-10-30. There is no executable
entry point, installed command, local-host integration, activation transaction
or recovery implementation.

Separately, `tam-deploy` can skip graphical restart and shell IPC when the
user graphical target is inactive, including during rollback. Development
tests do not prove a physical VT upgrade. Retain and verify that existing
console deployment capability for 0.5.12; do not complete the new command
there. Upgrade operations must remain possible after reboot and text login
without starting the desktop.

Keep the selector as unfinished source for 0.6. Do not expose it as a usable
0.5 command or claim that it establishes native compatibility.

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

## Next actions for 0.6

1. Define and review the concrete compatibility schema and supported starting
   states against this accepted interface before implementation.
2. Audit the selector and deployment transaction against the accepted contract.
3. Implement read-only planning, transaction/recovery and packaging in order;
   bind physical evidence to exact candidates.
