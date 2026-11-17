# Compositor protocol layer

**Status — 2026-10-09:** Fred explicitly accepted milestone B, Tamlinux
**0.4.1**, after restoration and the monitor-plugin regression repair.
The accepted exact shell is `a0d7737`, with unchanged observation identity,
active collection and fresh equal records. The tested monitor fix is 2.0.3;
other plugin payloads are preserved. Normal Run finalization is recorded in
the current session record. Menu ownership follows at 0.4.2.

The interrupted archive contains **25 output disagreements**, 14:05:00–14:28:32
UTC, and two unexplained gaps. Reasons-only logs cannot identify which output
field differed. Preserve this evidence and investigate with bounded snapshot
diagnostics before authority. The original October 23 endpoint is invalid;
one additional output disagreement was retained during this session, bringing
the total to 26. A fresh auditable continuous window is required. Milestone C still requires
14 consecutive days and three of every required event. Fresh agreement alone
cannot dismiss previous differences or gaps.

Milestone B acceptance checks the deployed revision, shadow environment,
collector/timer and fresh comparisons alongside normal desktop use. Package
extraction and unaccepted plugin consolidation remain separate from acceptance.
The initial candidate passed 409 desktop and 494 workstation configuration
checks; guarded restoration passed all 496 current configuration checks and
eight delivery checks. Fred's step acceptance is recorded; no unobserved physical event or protocol-authority acceptance is claimed.

The shell gets its compositor facts from standard Wayland protocols wherever
a protocol exists. Compositor IPC fills only the remaining gaps. The shared
code runs first beside the existing Hyprland backend on the daily desktop and
changes nothing. When the two agree over a period Fred accepts, the protocol
source becomes authoritative on Hyprland. For 0.7.0, tam-pane's adapter is built
on the same layer (D263), so tam-pane starts from code already in daily use.

## Problem

`desktop/shell/host/Compositor.qml` is the right boundary. Widgets read one
compositor-neutral facade, and exactly one adapter fills it. Behind that
boundary, each adapter is self-contained:

- `HyprlandAdapter.qml`, used daily, gets everything from Hyprland IPC.
The workspace protocol source must bind to the live QML properties, retain
workspace-to-output assignments, and update when workspaces or outputs
change. Multi-monitor modes in `fred.workspaces` depend on those assignments.

Hyprland 0.56.2 implements `ext-workspace-v1`,
`wlr-output-management-unstable-v1`, `wlr-output-power-management-unstable-v1`,
`ext-foreign-toplevel-list-v1`, `wlr-foreign-toplevel-management-unstable-v1`,
`ext-idle-notify-v1`, `ext-session-lock-v1` and `ext-image-copy-capture-v1`.
The protocol path can therefore run on the current desktop now, and it
keeps the shell independent of any one compositor's IPC.

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
| Popup focus grab | Hyprland-only | `HyprlandFocusGrab` | None elsewhere (already handled) |

**Shape:**

1. **`ProtocolState.qml`**, a compositor-neutral component in
   `desktop/shell/host/`. It imports `Quickshell.WindowManager`, uses
   `Quickshell.screens`, and holds **bound** properties with change handlers,
   never one-time reads. It produces the workspace and output part of a facade
   snapshot, including each workspace's output. It applies the existing
   bounds: workspace ids 1–10, validated output names, list caps. It starts no
   process.
2. **Adapters become gap fillers.** `HyprlandAdapter.qml`, and tam-pane's
   adapter when it arrives, each combine `ProtocolState` with only their own
   gaps from the table. Adapter files keep their existing import boundaries.
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
  start tam-pane integration, packaging or a tam-pane session.
- No new plugin contract. The plugins keep reading the existing facade;
  `fred.workspaces` and `fred.monitor` 2.1.0 work is unaffected.
- Closed execution is unchanged. The protocol layer runs no commands.
  Existing adapter commands keep their fixed argv, closed environment and
  deadlines.
- Output configuration persistence stays compositor-specific.

## Milestones

Each step that changes the deployed shell is a Tamlinux step, numbered when it
starts ([VERSIONING.md](../../VERSIONING.md)). Milestone A deploys nothing and
runs alongside 0.4.0. Milestone B is the next step after 0.4.0 is accepted.

| Milestone | Work | Acceptance evidence |
| --- | --- | --- |
| **A. Develop** (alongside 0.4.0) | `ProtocolState.qml`; adapter refactor with no behaviour change on Hyprland; fixtures for per-output workspace groups, `canActivate` false on active workspaces, a workspace that moves between outputs, hotplug add/remove, and an empty initial list that fills later | Unit and fixture tests; isolated proof shell on Hyprland shows protocol and IPC snapshots equal |
| **B. Shadow on the daily desktop** (the step after 0.4.0) | Deploy with shadow mode on; no behaviour change | A Tamlinux step accepted by Fred: no regression, and the comparison log is being written |
| **C. Authoritative on Hyprland** | Protocol source drives workspaces; IPC fills gaps; rollback flag retained | The shadow period below is met. A Tamlinux step accepted by Fred; all eight plugins behave unchanged |
| **D. tam-pane on the shared layer** | Build tam-pane's adapter as a gap filler from the start | Part of 0.7.0; real tests on tam-pane |

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

Verification:

- All **398 desktop tests passed**, including actual offscreen QML fixtures
  for initially empty lists, per-output groups, urgency/capabilities, active
  workspace changes, movement between groups, nested projection changes,
  output removal/return, geometry, ambiguous ownership, bounds and comparison.
- `python3 desktop/launch-protocol-proof`: protocol and IPC snapshots agreed
  for **three outputs and four workspaces** on Hyprland with Quickshell 0.3.1.
  The isolated shell creates no surfaces, dispatches no actions, and exits
  within 15 seconds. It reads only through the existing adapter commands.

No physical hotplug, suspend, desktop-mode change or daily shadow trial was
performed by this milestone. The reactive tests use mutable fixture objects;
the live proof checks the current connected desktop. Make/model description
format, urgency and out-of-contract workspaces are not compared to IPC, which
does not currently expose corresponding facade fields. ShellScreen exposes
`model`, but no separate manufacturer field in the installed Quickshell API.

## Display power

Keep display power on adapter IPC through the Hyprland baseline. The current
display-fault mitigations depend on Hyprland's IPC behavior. During 0.7.0
integration, evaluate whether `wlopm` can serve both compositors.

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

Verification before corrected deployment: all 409 desktop tests pass, including actual
QML settling/heartbeat fixtures, journal retry/deduplication, missing-record
detection, code-identity resets, stale/gapped evidence, supported/unsupported
events, journald's byte-array encoding for colored messages, and a complete
14-day fixture with three of each event. The isolated
`desktop/launch-protocol-proof --shadow` recorded agreement on three outputs
and four workspaces, with no surfaces or dispatches.
