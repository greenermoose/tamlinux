# Keep the active monitor steady during desktop changes

**Status — 2026-11-11:** Focus-preserving placement, shared bar ingress and
persisted per-output retry/completion gates are implemented in Develop.
Complete Arch packages now build for Hyprland 0.56.2-4.2 and Aquamarine
0.15.1-1.2, retaining the existing DPMS/idle/connector guards. Native/user-package integration passes against exact committed sources;
service routing and physical continuity remain exact-candidate Test gates. Delivery candidate unassigned; the
existing 0.6.22 Test candidate stays frozen.

## User problem and required result

Changing desktops on an already lit Dell must keep that display lit, show
the requested desktop's windows and preserve keyboard focus there. Sleeping
HP and MSI side monitors may take longer to wake and display their windows.
Their recovery must not interrupt work on the Dell.

Keep unused-monitor power saving. Also make display failures diagnosable:
timestamps and output identity must let us correlate a desktop switch with
power requests, output changes, DRM failures and kernel events. Remove logs
from Tamlinux 0.4.x and earlier only after preserving the evidence still
needed by active faults.

## Starting evidence

Two incidents were reported on 2026-11-10 during 0.6.22 Test. The first
followed desktop 3 → 2; the second repeated the visible glitch, but its
starting desktop was not recorded. Switching was reported normal with all
three monitors awake. The following shell-journal times are **UTC**; the
recorded local times were EST (UTC−05:00).

| Shell event | First incident | Second incident |
| --- | --- | --- |
| HP wake requested for windows on its workspace | 17:07:58.871918 | 17:22:12.487043 |
| HP bar destroyed as the output disappeared | 17:07:59.472442 | 17:22:13.084913 |
| HP bar created again | 17:08:00.232330 | 17:22:14.011118 |
| MSI wake requested | 17:08:00.900845 | 17:22:14.468351 |

Both incidents occurred in an active, unlocked session without a shell
restart. The recorded kernel-journal review found no matching GPU errors
in the inspected windows. After the second event, the Dell was lit and
focused on workspace 5, its slot in desktop 2, with unchanged geometry.
That observation does not establish continuous scanout during the glitch.

The first compositor capture contained two page-flip-awaiting errors near
an HP disconnect/reconnect, without a Dell disable or modeset in that
sequence. The second contained an HP disconnect and a disconnected-output
commit error, without a fresh page-flip-awaiting error in the inspected tail.
Those compositor lines have **no timestamps**: their ordering is evidence,
but their exact incident timing, output attribution for the commit errors,
and causal connection to the Dell disturbance remain unproven. Do not
assign reconstructed timestamps to them.

The journal events above were rechecked while preparing this draft. Keep
the boot ID, exact queries, selected versions and useful original excerpts
in the incident's local evidence record; publish only a relevant, reviewed
excerpt when it supports an implementation result. Preserve the useful
untimed excerpt before its temporary capture disappears.

Source inspection at product revision `19db334` identifies a plausible
disturbance path, rather than a proven cause of physical blanking:

- [Workspaces.qml](../../desktop/plugins/fred.workspaces/Workspaces.qml)
  debounces output-set reconciliation by 350 ms. Its separate 300 ms
  follow timer can request a set switch when split sets are disabled.
- [tam-desktop-mode](../../desktop/plugins/fred.workspaces/tam-desktop-mode)
  calls `ensure_contiguous_layout()` before `reconcile()` checks whether
  the workspaces are aligned. On a mismatch, `switch_windows()` builds
  placement steps for every present output. `placement_steps()` focuses
  each output and workspace, including otherwise correct ones.
- A command lock serializes helper calls, but hardware hotplug can still
  occur during a batch. An incomplete reconciliation can currently return
  the generic `reconciled` result after ignoring a failed switch.

Native source inspection also confirms separate logger paths: Hyprland's
`src/debug/log/Logger.cpp` applies `setTime(!disable_time)`, while
Aquamarine's `src/backend/Logger.cpp` can write directly to the connected
logger. The inspected `src/backend/drm/DRM.cpp` emits the page-flip-awaiting
and disconnected-output errors without an output name. These findings
must be checked against the exact packaged sources before a native patch.

## 1. Establish a trustworthy display timeline

First resolve the effective packaged compositor configuration, running
unit, logger connection and dependency versions. The incident inspection
recorded `debug:disable_time=true`, `debug:disable_logs=true` and
`debug:enable_stdout_logs=false`. Its service routed stdout to the journal,
but no compositor entries were found there in the first inspected window.
Backend messages still appeared in the compositor file. Verify ordinary
Hyprland and Aquamarine emission separately; a configured stdout route
alone does not prove either path works.

Prefer native time support and the existing service journal route. Verify
its precision, severity handling and buffering before choosing settings.
If that cannot meet the following contract, propose the smallest logger or
native-package correction; do not permanently enable a general debug flood.

| Record | Required information |
| --- | --- |
| Relevant display transition or error | Subsecond emission time, emission-time monotonic value or demonstrated equivalent, severity, component and connector/output identity |
| DRM commit failure | Output name at the emitting site; available CRTC ID, commit flags and pending-flip/disconnected state; explicit unavailable values when necessary |
| Desktop request and completion | Switch sequence, requested desktop, originating output, affected outputs, reason and per-output result |
| Wake, removal, return and reconciliation | Output, transition/reason, current request sequence and outcome, including deferred, superseded or incomplete work |
| Journal envelope | Boot ID, service/process identity and journal receive time, distinguishable from emission time |

Use one documented boot-relative monotonic clock, or a measured mapping
between clocks, across the producers. Receive time alone cannot establish
event order when buffering delays a record or wall time changes. Keep
output identity in each failure itself; an adjacent connector line is not
attribution. Record unknown context honestly rather than guessing.

Emit compact switch start, active-output completion and final
complete/partial/failure events. Keep normal logging to errors and meaningful
state changes, with bounded record sizes and existing journal retention.
Keep the existing compositor file useful, with the same timestamps where
that route is retained. Do not log window titles, keystrokes, cursor motion
or every frame. Any extra trace must be explicitly enabled, finite and
documented; add no resident log-watching service and suppress no errors.

**Milestone evidence:** isolated logger/error-path tests demonstrate usable
timestamps and output identity in journal and file routes. A coordinated
switch/wake aligns compositor, backend, shell and kernel time, documents
precision and buffering limits, and confirms quiet ordinary idle. Do not
induce a GPU failure in the daily session to test logging.

## 2. Apply the active desktop first; repair only affected outputs

Keep the existing workspace plugin, helper and named compositor adapter
boundary. Introduce one authoritative latest desktop intent shared by
explicit switches, output reconciliation and the follow timer. Preserve
canonical output slots through temporary loss; do not compress workspace
numbering because a sleeping panel drops its connection.

1. Capture the originating lit output and requested desktop. Prepare its
   workspace ownership, apply that desktop promptly and retain keyboard
   focus there. Do not wait for side-monitor wake to finish. Do not change
   the active output's DPMS, mode, scale, position or geometry.
2. Record desired desktop separately from observed per-output completion.
   A side-monitor failure must not roll back the active output or leave
   reconciliation using an obsolete `desktop-current`. Report partial
   completion truthfully to callers and in diagnostics.
3. Request wake only for side outputs that need it. On removal/return or
   completion events, compare each affected output with the latest intent
   and repair only its mismatched workspace. An already aligned Dell gets
   no redundant focus/workspace cycle. An already satisfied request is a
   no-op. Gate layout repair too: transient wake churn must not invoke
   set-wide geometry rewrites before the alignment check.
4. Keep input focus on the originating output throughout side repair.
   Verify output-targeted operations through the adapter before relying
   on them; a batch that focuses a side monitor and restores focus later
   does not by itself prove uninterrupted input. If existing primitives
   cannot meet this contract, review the necessary narrow adapter change
   before physical acceptance.
5. Serialize execution while allowing newer explicit intent to supersede
   pending work. Give each request a generation/sequence. A delayed retry,
   returning output or follow-timer event must reread that generation and
   must never restore an older desktop. Busy/timeout paths must not silently
   drop the latest explicit request. Coalesce duplicate reconciliation.
6. Retry only on relevant events with a bounded deadline and attempt budget;
   report the remaining outputs at expiry. If the originating output
   disappears, choose a surviving usable output deterministically, record
   the change and stop targeting the absent output. Preserve real
   unplug/replug handling and the user's deliberate layout changes.

Preserve independent workspace mode, intentional split sets, window
placement and the existing idle/suspend behaviour. Keep the MSI wake
workaround scoped to the MSI, with no Dell or whole-set reset. Passive
reconciliation must not keep resetting idle timers or keep every output
awake. Any wake-specific workaround gets a documented retirement condition:
the underlying correction or replacement compositor passes these same cases.

**Milestone evidence:** extend the existing isolated helper/model/idle
tests with event sequences covering HP removal/return during a switch,
aligned Dell, layout-repair suppression, delayed/out-of-order events,
duplicate timers, rapid successive requests, lock contention, partial
failure/timeout, loss of the origin and real unplug/replug. Assert the
commands sent to each output and the final desired/observed state. Fixtures
must use temporary state and fake compositor endpoints; they must not
dispatch into the real session or signal processes they did not start.

## 3. Preserve useful fault evidence, then remove obsolete logs

This is a one-time version-based cleanup of journal ranges and loose
diagnostic logs, not a permanent retention policy. Keep it operationally
separate from the desktop correction so its evidence can be reviewed before
irreversible deletion.

1. Establish installed-version intervals from deployment and acceptance
   records. A release date is not an installation boundary; a boot or log
   file can span multiple versions. Protect 0.5-and-later records, both
   current incidents and all ranges whose version is uncertain.
2. Review every active fault, including worked-around faults and fixes still
   on trial. Identify each old range still needed to establish its trigger,
   mechanism or recovery. Preserve the smallest sufficient excerpt and
   context in that fault's existing evidence location, with original
   timestamps, boot ID, installed versions, source/query and integrity
   information. Reopen the retained evidence, check completeness, and repair
   references before allowing deletion of its source. Preserve relevant
   untimed display excerpts as untimed; do not archive the whole journal.
3. Produce a local dry-run table: exact file or journal-file set, version/time
   coverage, bytes eligible, protected boundary, active-fault exception and
   preservation result. Include both system and user journals where relevant.
   Exclude conversation histories, source/provenance, acceptance receipts,
   recovery artifacts and files currently being written.
4. Use supported journal retention operations only after proving that their
   actual removal set is contained in the reviewed set. `journalctl` vacuum
   operates on whole archived journal files, not version-selected lines.
   Inspect file headers and coverage; retain mixed or unknown-version files.
   Do not edit journal binaries, use a broad size vacuum or rotate the
   current journal merely to force deletion. If no safe vacuum threshold
   exists, retain the affected files and state why. Remove separable loose
   old logs individually after the same evidence check.
5. Revalidate identities and coverage immediately before execution. Obtain
   the exact cleanup and any necessary filesystem/privilege approvals, then
   apply only the reviewed set. Report actual bytes reclaimed and deliberate
   exceptions. Recheck newer/current incident queries and preserved fault
   excerpts. Deleted logs have no promised rollback.

**Milestone evidence:** obsolete logs are removed wherever safely separable;
every retained old-log exception names an active-fault need or a mixed/unknown
boundary. Old lines inside mixed files are an explicit exception. Retained
fault excerpts retire when no longer needed. Any future age/size retention
policy requires its own explicit decision. No deletion occurs at plan review.

## 4. Package and prove physical continuity

After isolated checks pass, select exact committed product sources and any
native correction through a recorded package assembly. Fred's Test word
must name that candidate. Before activation, record the previous user
generation; add one Snapper snapshot for any native-package or login step.
Retain the accepted 0.5.12 recovery anchor. Native installation and any
necessary logout/login require their individual approvals; explain that
interruption before scheduling it. No reboot is currently justified.

Proposed physical acceptance is **20 switches: four in each case below**,
including 3 → 2 and 2 → 3, using the same windows and layout:

| Starting condition | Expected result |
| --- | --- |
| All three monitors awake | Prompt normal desktop switch |
| Dell lit, HP blanked; requested desktop has HP windows | Dell switches immediately; HP may finish later |
| Dell lit, MSI blanked; requested desktop has MSI windows | Dell stays steady through the MSI wake workaround |
| Dell lit, both side monitors blanked | Dell switches without waiting for either side monitor |
| Another switch while a side monitor is waking | Latest request wins everywhere; no stale return |

Fred observes **zero Dell blanks, unintended desktop changes, visible window
displacement or lost input focus**. Side monitors eventually show the latest
requested desktop or produce an explicit bounded failure. A post-event IPC
snapshot alone cannot pass this gate. Also verify genuine hotplug, independent
and split modes, unused-monitor blanking, whole-session idle/suspend, no shell
restart/error loop and no material logging overhead. Include the normal idle
energy reading in the candidate report.

If the Dell still blanks, use the timestamped timeline to distinguish
workspace/focus disturbance from a compositor/backend or GPU-wide stall.
Do not declare the workspace change sufficient or alter page-flip scheduling
from nearby errors alone. A further native correction needs evidence,
isolated regression coverage and preserved disconnect/CRTC protections.

## Ownership, boundaries and review decisions

Product changes belong in `tamlinux`: primarily the workspace plugin/helper,
their tests and, only as required, the named adapter and session logging
integration. Package assembly belongs in `tamlinux-packages`. Personal
configuration and original incident/fault records stay local. A necessary
upstream-native patch follows the native Arch package path, with an exact
base, narrow diff and explicit upstream retirement condition.

This work does not replace the compositor or reopen the established lock,
MSI jitter, stale-HPD resume or hibernation faults without new identifying
evidence. Keep their mitigations intact. An unlocked page-flip error alone
does not identify the lock-screen fault. No live reset, forced blanking,
cable change or automated desktop switching occurs outside a coordinated
trial. Run and Release remain separate decisions after Test acceptance.

Fred approved this approach and physical matrix on 2026-11-10: “Looks good.”
During implementation, resolve native timestamp precision/severity/routing
and the adapter's ability to repair a side output without stealing focus.
Choose the exact candidate after those results; do not modify the frozen
Test candidate or promise a root cause the present evidence cannot establish.

## Development handoff

The first slice advances `fred.workspaces` to **2.0.8**. It adds structured
helper records and reports failed reconciliation as `incomplete: workspace
placement`, with exit status 1. Set-wide placement, focus cycling, layout
repair and the existing `desktop-current` semantics are unchanged. This
slice establishes observations; it does not claim to correct Dell blanking.

Each helper record is a single JSON line prefixed `tam-desktop-mode event `:

- `wall_ns`: Unix UTC nanoseconds, sampled at emission; representation does
  not claim that the hardware clock is accurate to a nanosecond.
- `monotonic_ns`: Linux `CLOCK_MONOTONIC` nanoseconds since boot, excluding
  suspend, for comparison with the journal's monotonic timestamp in the same
  boot. Wall-clock corrections cannot reverse this ordering.
- `component`, `severity`, `pid`, `event`, `action`, `sequence`, `reason`:
  switch/reconciliation/power start and end, placement and busy outcomes.
  The process/monotonic sequence correlates observations only; it is **not**
  the shared latest-intent generation required by milestone 2. Busy records
  have no accepted sequence. Direct internal placement calls outside an
  action context also have no sequence yet.
- `requested`, `origin`, `outputs` or `assignments`: requested desktop or
  power state, known originating output, affected outputs and per-output
  observed/expected workspace. Unknown origins are null. Batch rejection
  reports `batch-failed`; it does not assert that no commands were applied.

Records flush to stderr immediately. The bar forwards lines through its
existing shell logger using `SplitParser`, without retaining process output.
The maximum supported topology fits the 4096-byte forwarding bound. Stdout
remains the short command response. Passive `status` emits no diagnostic
record and makes no compositor query. No new file sink or daemon is added.
Power completion means the command was accepted, not that a panel visibly
woke or the detached MSI retrain finished. Placement completion describes an
IPC snapshot, not continuous physical scanout or input focus.

Isolated tests cover successful switches, HP removal during a batch,
failed repair on return, an already aligned returning HP, dark-session
deferral, failure pairing, wall-clock reversal, record-size bounds, a closed
log sink, quiet status, busy requests, power failure and CLI failure status.
Every backend call is fake; direct process launches fail the new tests.
The existing workspace tests and offscreen widget render also pass.
The full desktop suite passes: 817 tests, 14 skipped; the separate workspace
plugin suite passes all 69 tests. The initial 120-second run was interrupted;
the successful full rerun took 209 seconds.

Native source archives matching the installed Hyprland 0.56.2 and
Aquamarine 0.15.1 were inspected. Hyprland still configures time separately
from ordinary/stdout logging; the two Aquamarine commit errors still omit
the connector name. No native settings or packages changed. The helper's
offscreen render does not prove its journal forwarding under a running
candidate. Journal/file route, native emission precision, severity filtering,
buffering and backend error attribution remain open gates.

Next actions:

1. Finish candidate prerequisites: full Hyprland package build, native recipe
   integration and the remaining bar ingress-order/completion gates below.
2. Prepare the separately reviewable old-log cleanup set.
3. Select a packaged candidate on Fred's instruction, verify its real service
   logging route and idle behavior, then run the physical continuity matrix.

### Latest accepted desktop intent (2.0.9)

The next slice adds `desktop-intent` under the existing Tamlinux state
directory. It stores a bounded versioned record: increasing `generation`,
desired `desktop`, originating output and `complete`. A short state-only
lock serializes publication and completion independently of the compositor
command lock. An explicit Windows-mode switch publishes before waiting for
that command lock. A busy exit (75) now reports `pending` and preserves the
request; it does not assert placement or arrange an unbounded retry loop.

`desktop-current` remains the last successfully observed desktop. A partial
switch leaves it unchanged; reconciliation and realignment use desired
intent instead. Compare-and-set completion prevents an older in-flight
switch from writing over a newer request. A command holder can apply up to
three superseding generations, with a three-second budget checked between
IPC attempts. Existing individual IPC timeouts still apply; this is not a
hard three-second wall-clock deadline. Exhaustion or failure leaves the
latest request pending for the next relevant event or explicit retry.

A follow timer rereads the generation after acquiring the command lock.
An intervening explicit request supersedes it; an incomplete request takes
precedence over a transient focused-workspace observation. Following a
deliberate window focus after completion remains supported, with a fresh
focused-workspace check and publication compare-and-set. Non-silent window
moves use the same switching path; independent modes retain their behavior.
Incomplete CLI switches now return 1 as well as emitting a warning.

Isolated regressions cover failure then reconnect, newer requests during a
batch, stale completion and follow events, concurrent publication, real
command-lock contention, bounded supersession, mode changes, invalid state
and symlinks. These use fake compositor operations and temporary state, and
reject direct process launches. The existing workspace tests and widget
render pass. There are 32 isolated timeline/intent cases (19 new), plus
69 workspace plugin cases. The broad desktop run executed 836 tests with
14 skipped and one QML/manifest version mismatch; correcting the QML
declaration to 2.0.9 passes all 35 affected host/metadata tests on rerun.

The generation orders requests **when the helper accepts them**. A bar's
local action queue still needs coalescing and an ingress-order contract
before the whole latest-user-intent milestone can close. `complete` still
describes the present outputs' IPC snapshot, not an absent side output or
physical continuity. Set-wide placement/focus cycling and layout repair
remain unchanged in this slice. Do not select it as a continuity fix yet.

### Native logger probe

The isolated [C++ probe](../../desktop/proofs/native-display-logging.cpp)
links the installed Hyprutils logger and a named `CLoggerConnection`, the
same connection mechanism used by Aquamarine. It never opens a DRM device
or contacts a compositor. Error records are explicitly synthetic. Its
payload clock samples are supplied by the probe; they are **not** evidence
that existing compositor records contain monotonic emission time.

With Hyprutils **0.14.2**, native `setTime(true)` formats local wall time as
`HH:MM:SS.nnnnnnnnn` on both stdout and file records. Two backend records
20 ms apart retain distinct subsecond times. That is representation
precision, not clock-accuracy evidence. Explicit warning thresholds on both
the parent and connection suppress the synthetic debug records. No
equivalent production severity setting has yet been established.

Routing this separate process through `systemd-cat` delivers the ordinary
and connection error records, retaining PID, boot ID and receive-time wall
and monotonic journal fields. The journal envelope uses priority 6 for this
stdout stream; error severity remains in the native text. This proves the
library-to-journal mechanism, not the running compositor's route. The
small file remained **zero bytes while the logger was alive** after those
emissions; its contents appeared on logger destruction. File timestamps
then matched stdout. Prompt retained-file availability remains unsatisfied.
Native records still need a common monotonic emission value, connector
identity at the DRM failure site and a bounded production severity policy.

Source inspection of Hyprland **0.56.2** also confirms that `hl.dsp.focus`
selects either the monitor or workspace path: supplying both does not
select a side workspace without focus. Workspace selection calls
`Actions::changeWorkspace`, which changes the focus monitor. The existing
named workspace-move action does not provide general focus-preserving
activation. The ext-workspace activation route calls a monitor directly,
but creation, assignment and its focus behavior need separate verification
before choosing it or a narrow native adapter extension. No guessed Lua
operation or focus-and-restore batch is treated as satisfying this contract.


### Focus-preserving placement and native logging (2.0.10)

Windows-mode switch and repair now use a bounded named
`select-output-workspace` operation. The originating output is ordered first;
only mismatched outputs receive commands. Side repair has no focus/restore
fallback. A rejected or unavailable native action leaves the request pending
and reports partial completion. Known-panel removal and return no longer
compress or restore geometry; canonical slots and the user's geometry survive
wake churn. A new connector retains the existing topology path. Independent
and split modes keep their existing behavior.

The native action resolves an exact monitor and numeric normal workspace
(1–160), creates or moves that named workspace, and calls the monitor's
no-pointer/no-focus path for a side output. It refuses to move the keyboard
owner's active workspace away. The no-focus path no longer releases held
mouse buttons. If the origin disappears, a later reconciliation adopts the
surviving compositor focus rather than restoring the absent output.

Native source branches retain the existing DPMS, idle and connector guards:

- Hyprland: `develop/plan54-output-workspace-logging`, head `3b1b3f15`.
- Aquamarine: `develop/plan54-commit-attribution`, commit `25f5e5d`.

The [native provider contract](../../desktop/native/providers/display/README.md)
contains the source patches, retirement conditions and reproduction notes.
These are development corrections, not selected or installed native packages.
The helper must not be packaged for use without the matching native action.

The common sink emits subsecond wall and CLOCK_MONOTONIC clocks at emission,
component, severity and PID. Warnings/errors and selected backend transitions
reach the journal plus promptly flushed `display.log` in the compositor
instance directory. Existing verbose logging settings and the original
Hyprland file remain independent. Synchronous commit messages carry output,
CRTC, connection and frame state; terminal asynchronous worker failures carry
output, CRTC, commit ID and errno. No scheduling/recovery guard was changed.

Verification: 41 isolated workspace timeline/intent/focus cases, 69 existing
plugin cases, 24 compositor adapter cases, 35 host/metadata cases and two
compiled sink cases pass. The widget render passes. Aquamarine builds with
its existing connector guard and passes attachments, output and commitThread
(fake-backend tests; the real-window test was not run). All four modified
Hyprland translation units pass syntax checks; the complete Hyprland package
has not been built or linked.

The final synthetic proof links the rebuilt Aquamarine library and exercises
its real logger callback plus the exact common sink. Five payloads match
between file and journal, with priorities 3,3,3,6,4; debug records are absent.
The file is readable before logger destruction, records stay below 4096 bytes,
and the 20 ms backend emission gap is preserved. Boot, PID and journal clock
fields remain available. One journal envelope preceded its payload emission
sample by about 2 microseconds, so envelope time is not used as an exact
per-line emission clock. Payload monotonic clocks determine emission order.
Flushing establishes reader visibility, not power-loss durability.

This does not establish continuous physical input focus or scanout. The bar
queue can still drop/coarsely order ingress, and per-output retry/completion
budgets remain open as recorded above. Actual candidate helper forwarding,
compositor service routing, ordinary idle overhead and the coordinated
switch/wake timeline must still pass before physical acceptance. No native
installation, session restart, display dispatch, old-log deletion or stage
move occurred in this source slice.

### Shared ingress and output budgets (2.0.11)

All bars share an engine-wide publication/work queue. A fast helper accepts
explicit clicks serially, using the facade's captured input output without
compositor IPC or the worker lock. New pending clicks replace older
unaccepted clicks. Publication proceeds while a worker is busy; applying
work always reads persistent latest intent. Bar destruction transfers queued
work to a surviving/new bar. Repairs, follow observations and per-output
power requests coalesce. Saturation and exhausted retries report failure.
Direct command callers continue to order at the short persistent state lock.

Each generation stores canonical output outcomes, including absent panels.
Present mismatches get at most three attempts and a three-second monotonic
budget from their first attempt. Missing panels spend no attempts. A late
return can repair its own slot without disturbing aligned outputs. Progress
is saved before IPC; duplicate events, process death and realignment cannot
reset it. Each placement invocation also caps compositor IPC at three
seconds. `retry-intent` is an explicit new generation with fresh budgets.
The bar retries busy/incomplete application at most three times, 150 ms
apart. Expiry retains the desired desktop and reports incomplete work.

A full-set completion requires every canonical output's observed assignment
and a surviving input owner. It never asserts physical scanout. Independent
and intentional split modes keep their existing behavior. A side failure
does not prevent another output's progress or undo the active desktop.

Verification: 57 isolated workspace cases, 69 existing plugin cases, 25
adapter cases, 35 host/metadata cases and the widget render pass. The full desktop suite
passes 872 tests (14 skipped) from source `ea21f86`. Full native
packages link, and the three Aquamarine fake-backend tests pass. Exact native
archives/recipe hashes and user-package correspondence belong to the
[delivery integration procedure](https://github.com/greenermoose/tamlinux-packages/blob/develop/docs/display-integration.md).
The package integration uses product `ea21f86`, delivery recipe `9a309a9`,
libtam `67cffd5` and tools `b92c4f5`, without changing frozen candidate pins.
The shell, plugin and standalone helper packages match the selected source;
both packaged entry points share temporary intent in a smoke test without
compositor IPC. The exact tools sources also pass their full Arch host suite
with private PID/mount guards.
No source trial is installed. The remaining physical gates are actual helper
and compositor service journal routing, quiet idle, genuine hotplug,
independent/split behavior and the approved Dell matrix after an exact Test.
