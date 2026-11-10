# Keep the active monitor steady during desktop changes

**Status — 2026-11-10:** Fred approved the implementation plan and physical
acceptance matrix. Develop has not started; logging and logs are unchanged.
Proposed for 0.6 reliability work; delivery candidate unassigned. The existing
0.6.22 Test candidate stays frozen.

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

Next actions: establish the diagnostic timeline and isolated workspace
regressions during Develop, then select a candidate and schedule its physical
Test on Fred's instruction.
