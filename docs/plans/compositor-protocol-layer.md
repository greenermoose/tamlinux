# Compositor protocol layer

**Status — 2026-10-09:** milestone B's daily logger and durable evidence collector
are developed and verified in isolation; daily Test deployment is being prepared.
Development tests do not establish the 14-day period. Milestone A and product
step 0.4.0 were completed on 2026-10-08. Fred accepted the approach, schedule,
acceptance period and display-power boundary on 2026-10-08.

The shell gets its compositor facts from standard Wayland protocols wherever
a protocol exists. Compositor IPC fills only the remaining gaps. The shared
code runs first beside the existing Hyprland backend on the daily desktop and
changes nothing. When the two agree over a period Fred accepts, the protocol
source becomes authoritative on Hyprland. At 0.7 the Sway adapter is rebuilt
on the same layer, so Sway starts from code that is already in daily use.

## Problem

`desktop/shell/host/Compositor.qml` is the right boundary. Widgets read one
compositor-neutral facade, and exactly one adapter fills it. Behind that
boundary, each adapter is self-contained:

- `HyprlandAdapter.qml`, used daily, gets everything from Hyprland IPC.
- `SwayAdapter.qml` is meant to prefer `ext-workspace-v1` through
  `Quickshell.WindowManager` (Step 5 in
  [desktop decoupling](desktop-decoupling.md)). It runs only when
  `TAMLINUX_COMPOSITOR=sway`, so its protocol path has never run against a
  live compositor.

A review on 2026-10-08 found three gaps in that path. A standalone probe with
Quickshell 0.3.1 on Hyprland 0.56.2 supported the first two:

1. **One-time reads see no workspaces.** `publishLive()` reads
   `WindowManager.windowsets` imperatively, once, at startup. In the probe,
   imperative reads returned an empty list even six seconds after the
   compositor had sent every workspace and `done`. A QML property **bound**
   to `WindowManager.windowsets` received them all. As written, the adapter
   would always fall back to Sway IPC.
2. **Workspace-to-output assignment is discarded.** The adapter sets each
   workspace's `output` to `""` on the protocol path. The protocol provides
   it through `Windowset.projection.screens` and
   `WindowManager.screenProjection(screen)`; the probe returned the correct
   output for every workspace on a three-output desktop. The multi-monitor
   modes in `fred.workspaces` need this assignment.
3. **No updates after startup.** The adapter publishes once and has no change
   handlers. This was expected for a slice tested against fixtures, but it is
   not yet a working backend.

Hyprland 0.56.2 implements `ext-workspace-v1`,
`wlr-output-management-unstable-v1`, `wlr-output-power-management-unstable-v1`,
`ext-foreign-toplevel-list-v1`, `wlr-foreign-toplevel-management-unstable-v1`,
`ext-idle-notify-v1`, `ext-session-lock-v1` and `ext-image-copy-capture-v1`.
Sway 1.12 implements `ext-workspace-v1`. The protocol path can therefore run
on the current desktop now.

## Approach

**Sources for each facade need:**

| Facade need | Standard source | Quickshell API | Remaining gap |
| --- | --- | --- | --- |
| Outputs: name, position, size, make and model | `wl_output`, `xdg-output` | `Quickshell.screens` (`ShellScreen`) | — |
| Workspaces: list, active, urgent, owning output | `ext-workspace-v1` | `WindowManager.windowsets`, `Windowset.projection.screens`, `WindowManager.screenProjection()` | Numbering rules, if a compositor's workspace names are not numbers |
| Focus a workspace | `ext-workspace-v1` activate | `Windowset.activate()` when `canActivate` | — |
| Move a workspace to another output | `ext-workspace-v1` assign | `Windowset.setProjection()` when `canSetProjection` | Compositors that do not advertise assign |
| Focused output | none | — | Adapter IPC |
| Display power | `wlr-output-power-management-unstable-v1` | none found in 0.3.1 | Adapter IPC until 0.7.0 (see Decided) |
| Output mode, position, scale | `wlr-output-management-unstable-v1` | none found in 0.3.1 | Live apply may use a client later; persistence stays in compositor configuration |
| Windows per workspace | none (foreign-toplevel lists windows, not their workspace) | `ToplevelManager` lists only | Adapter IPC |
| Keyboard layout, bindings | none | — | Adapter IPC; bindings from generated configuration |
| Popup focus grab | Hyprland-only | `HyprlandFocusGrab` | None on Sway (already handled) |

**Shape:**

1. **`ProtocolState.qml`**, a compositor-neutral component in
   `desktop/shell/host/`. It imports `Quickshell.WindowManager`, uses
   `Quickshell.screens`, and holds **bound** properties with change handlers,
   never one-time reads. It produces the workspace and output part of a facade
   snapshot, including each workspace's output. It applies the existing
   bounds: workspace ids 1–10, validated output names, list caps. It starts no
   process.
2. **Adapters become gap fillers.** `HyprlandAdapter.qml` and
   `SwayAdapter.qml` each combine `ProtocolState` with only their own gaps
   from the table. Adapter files keep their existing import boundaries.
   `Compositor.qml` and the facade fields do not change; `workspaces[].output`
   already exists.
3. **Shadow mode** (environment flag, read-only). `HyprlandAdapter` keeps
   publishing its IPC snapshot. It also builds the protocol snapshot,
   compares the two, and emits a bounded `TAMLINUX_EVIDENCE` line for each
   difference, debounced so that a burst of changes produces one comparison.
   Shadow mode changes no behaviour and dispatches nothing.
4. **Authoritative mode** (Hyprland). The workspace list, active state, owning
   output and workspace focus come from `ProtocolState`. Hyprland IPC remains
   for the gaps. A single flag returns to the IPC snapshot as the rollback.

## Boundaries

- Independence on Hyprland (0.4–0.6) remains the focus. This plan does not
  start Sway integration, packaging or a Sway session.
- No new plugin contract. The plugins keep reading the existing facade;
  `fred.workspaces` and `fred.monitor` 2.1.0 work is unaffected.
- Closed execution is unchanged. The protocol layer runs no commands.
  Existing adapter commands keep their fixed argv, closed environment and
  deadlines.
- Output configuration persistence stays compositor-specific, as the Sway
  plan already sets out.

## Milestones

Each step that changes the deployed shell is a Tamlinux step, numbered when it
starts ([VERSIONING.md](../../VERSIONING.md)). Milestone A deploys nothing and
runs alongside 0.4.0. Milestone B is the next step after 0.4.0 is accepted.

| Milestone | Work | Acceptance evidence |
| --- | --- | --- |
| **A. Develop** (alongside 0.4.0) | `ProtocolState.qml`; adapter refactor with no behaviour change on Hyprland; fixtures for per-output workspace groups, `canActivate` false on active workspaces, a workspace that moves between outputs, hotplug add/remove, and an empty initial list that fills later | Unit and fixture tests; isolated proof shell on Hyprland shows protocol and IPC snapshots equal; Sway fixture mode still passes |
| **B. Shadow on the daily desktop** (the step after 0.4.0) | Deploy with shadow mode on; no behaviour change | A Tamlinux step accepted by Fred: no regression, and the comparison log is being written |
| **C. Authoritative on Hyprland** | Protocol source drives workspaces; IPC fills gaps; rollback flag retained | The shadow period below is met. A Tamlinux step accepted by Fred; all eight plugins behave unchanged |
| **D. Sway on the shared layer** | Rebuild `SwayAdapter.qml` as a gap filler; remove its one-time reads | Part of 0.7.0 in the [Sway plan](sway-integration.md); real IPC tests on Sway 1.12 |

## Shadow period before milestone C

Milestone C may start when shadow mode has run for **at least 14 consecutive
days with no unexplained difference**. During those days, each of these
events must have occurred **at least three times** with no difference:

- a display sleeping and waking
- suspend and resume
- an output disconnected and reconnected
- a workspace moved to another output
- a desktop-mode change
- a cold boot

Any change to the shadow code restarts the count. A difference counts only
if it persists past a short settle time after the last compositor change,
because the two sources update at slightly different moments. An agent
summarizes the log for Fred, who does not need to read evidence lines.
Hotplug occurrences that need someone's hands are arranged with Fred.

## Milestone A evidence — 2026-10-08

`ProtocolState.qml` binds the windowset and screen lists; its snapshot binding
also observes nested active, urgent, capability, projection-screen and geometry
properties. Workspace numbers come from numeric names, never opaque protocol
ids. A workspace's projection must identify exactly one current output;
missing or ambiguous projections and duplicate names leave the snapshot
unready. Input scans cap at 64 entries, output names at 64 characters, and
workspace names at 1–10. Unknown protocol readiness falls back to IPC.

Hyprland still publishes its unchanged IPC snapshot. Only the isolated proof
sets `TAMLINUX_PROTOCOL_PROOF=1` to load a parallel protocol source and compare
workspace ownership, per-output active workspace and output positions after a
750 ms settle interval. This is a development check, not milestone B's daily
shadow logger or its acceptance clock. No protocol object is instantiated on
the default Hyprland path. Global focus, windows, keyboard, bindings, display
power and special workspaces remain adapter facts. Protocol activation checks
`canActivate`; an already-active workspace succeeds without a request.

The Sway development adapter uses the shared source and a bound combined
snapshot instead of one-time protocol reads. Its fixture mode leaves the
protocol component unloaded. Real Sway gap completion and session integration
remain milestone D at 0.7.0.

Verification:

- All **398 desktop tests passed**, including actual offscreen QML fixtures
  for initially empty lists, per-output groups, urgency/capabilities, active
  workspace changes, movement between groups, nested projection changes,
  output removal/return, geometry, ambiguous ownership, bounds and comparison.
- `python3 desktop/launch-protocol-proof`: protocol and IPC snapshots agreed
  for **three outputs and four workspaces** on Hyprland with Quickshell 0.3.1.
  The isolated shell creates no surfaces, dispatches no actions, and exits
  within 15 seconds. It reads only through the existing adapter commands.
- `python3 desktop/launch-clock-proof --selftest --compositor sway`: passed;
  fixed fixture snapshots and recorded-action checks still work.

No physical hotplug, suspend, desktop-mode change or daily shadow trial was
performed by this milestone. The reactive tests use mutable fixture objects;
the live proof checks the current connected desktop. Make/model description
format, urgency and out-of-contract workspaces are not compared to IPC, which
does not currently expose corresponding facade fields. ShellScreen exposes
`model`, but no separate manufacturer field in the installed Quickshell API.

## Decided 2026-10-08

- **Schedule.** Milestone A runs alongside 0.4.0, because it deploys nothing.
  Milestone B is the next step after 0.4.0 is accepted, and the menu step
  follows it. This gives shadow mode the longest daily use before 0.7, keeps
  it out of 0.4.0's baseline and rollback, and leaves independence work first.
  Rejected: B before 0.4.0, which would put two changes in flight during the
  baseline capture; B at the end of 0.6 or at 0.7, which would lose most of
  the shadow period.
- **Shadow period.** A minimum time plus required events, as above. A time
  limit alone could pass without the intermittent wake and hotplug paths;
  events alone could be met by forcing them in an afternoon. Rejected:
  staying in shadow until 0.7. Shadow mode tests reads only, so workspace
  activation through the protocol would then first run on Sway.
- **Display power.** Stays on adapter IPC until 0.7.0. The development
  workstation's display-fault mitigations depend on Hyprland's own
  display-power handling, and the standard protocol's path inside Hyprland
  has not been shown to be the same. At 0.7.0, when Sway needs the same
  function, evaluate `wlopm` (packaged on Arch and Void) as one client for
  both compositors. Rejected for now: switching to `wlopm` during the
  independence stages; a resident helper to read display power for the
  shadow comparison.

## Daily shadow evidence

Enable `TAMLINUX_PROTOCOL_SHADOW=1`. IPC remains authoritative, and
`ProtocolShadow.qml` cannot dispatch actions. It compares the shared facts
after 750 ms without a comparable change, logs status transitions, and emits
a health heartbeat every minute. Repeated equal states do not flood the log.
Sustained churn is reported as `settling`; loss of readiness is explicit.
Records contain bounded reason identifiers and counts, never window titles.

Set `TAMLINUX_SHELL_REVISION` to the deployed Git revision and
`TAMLINUX_PROTOCOL_SHADOW_ID` to the SHA-256 of the concatenated contents of
these files, in this order:

1. `desktop/shell/host/ProtocolState.qml`
2. `desktop/shell/host/protocol_model.js`
3. `desktop/shell/host/ProtocolShadow.qml`
4. `desktop/shell/host/HyprlandAdapter.qml`
5. `desktop/protocol-shadow`

An unrelated menu revision preserves the trial identity. Changing trial code,
including the collector's interpretation, starts a new period; returning to
an earlier identity also starts a new period. Development records without
production identity/revision are refused by the collector.

`desktop/protocol-shadow collect` archives the daily unit's journal records
under `$XDG_STATE_HOME/tamlinux/protocol-shadow/evidence.sqlite3` (default
`~/.local/state/tamlinux/protocol-shadow/`). It rereads a five-minute overlap,
deduplicates journal cursors, and commits only a complete valid capture. The
desktop deployment runs collection every five minutes and after user-manager
startup. Archive failures remain visible in the collection unit's journal.

Collect immediately before requesting a current summary:

```sh
tam-protocol-shadow collect
tam-protocol-shadow summary
```

The summary gives the evidence span, revisions, disagreements, missing journal
sequences, logging gaps and six event counts. It never treats calendar age or
an absent log as agreement. A stale heartbeat or unexplained gap blocks
readiness. Initial startup before the first equal comparison is excluded;
later unready/different/settling records require review. Such records are kept
even after agreement returns. The initial implementation is conservative:
explaining a disagreement requires a later explicit evidence review; there is
no command that silently dismisses it. `readyForAuthority` reports evidence
readiness only; Fred's milestone acceptance is still required.

Physical event notes use timezone-qualified start/end times and a concise
description of what was observed:

```sh
tam-protocol-shadow event workspace-move \
  --start '2026-10-09T12:00:00-04:00' --end '2026-10-09T12:00:20-04:00' \
  --note 'Observed workspace 5 move between two connected displays'
```

Kinds are `display-sleep-wake`, `suspend-resume`,
`output-disconnect-reconnect`, `workspace-move`, `desktop-mode-change` and
`cold-boot`. Notes are attestations, not generated proof of physical success.
They count only with equal comparisons within three minutes before and after
the interval, and no non-equal record inside it. Overlapping/repeated notes
cannot inflate the three-occurrence requirement. Supported suspend/boot notes
can explain the corresponding heartbeat gap; other gaps remain visible.
No physical event is forced to fill the matrix.

Verification before deployment: all 408 desktop tests pass, including actual
QML settling/heartbeat fixtures, journal retry/deduplication, missing-record
detection, code-identity resets, stale/gapped evidence, supported/unsupported
events, and a complete 14-day fixture with three of each event. The isolated
`desktop/launch-protocol-proof --shadow` recorded agreement on three outputs
and four workspaces, with no surfaces or dispatches.
