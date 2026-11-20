# Remove the traditional screensaver

Status: approved by Fred on 2026-10-29; implementation in progress. Target: Tamlinux 0.5.10.

## Outcome

Tamlinux no longer runs or ships a traditional visual screensaver. When the
session is idle, the display can blank and enter its configured energy-saving
states; waking, optional locking, suspend and Stay Awake continue to work.
This change does not turn automatic locking on or alter the user's power
timeouts.

## Work

1. Remove the screensaver launcher, effect and toggle commands, its terminal
   assets and window rules, menu entries, branding action, and the screensaver
   stage and window tracking in the shell idle service. Retain the lock and
   wake cycle, idle inhibitors and Stay Awake behavior. Remove obsolete
   screensaver-specific lock cleanup and user-facing labels.
2. Remove the screensaver-only ttfx provider, vendored source, package wiring
   and contracts. Keep shared tools such as image-to-text conversion if other
   features use them. Update current documentation and tests; retain historical
   evidence and provenance as records of earlier versions.
3. Review settings migration and recovery: preserve personal files and existing
   recovery anchors, while avoiding new screensaver state or dangling actions.
   Do not delete user artwork or settings as a side effect. Check external
   consumer configuration and installation contracts for stale references.
4. Assemble 0.5.10 with the separately approved 0.5 work that is ready.
   Record exact source and package pins, checks and recovery coverage. Do not
   activate the candidate during development.

## Acceptance evidence

- Source and installed-package checks find no screensaver commands, visual
  assets, menu actions, idle launch path or screensaver-only ttfx provider.
- Focused behavioral tests cover idle lock timing, activity and wake, Stay
  Awake, inhibitors and suspend handling; theme branding for About still works.
- A physical Test verifies blanking and wake, the configured energy-saving
  behavior and retained workflows, with the candidate's idle energy reading.
  Any locking test respects the current workstation lock policy.
- The full 0.5 checklist, including both machines' startup and timing evidence,
  appearance and Fred's acceptance, determines whether 0.5.10 can be the final
  0.5 release. Candidate preparation alone does not establish that result.

## Boundaries

Removal from a package is part of development; removing an installed native
package, changing boot or login, or deploying remains a separately governed
operation. Test, Run and Release require the corresponding instruction for
the exact candidate. Existing historical delivery records remain intact.
