# Transaction-bound upgrade recovery

- **Date:** 2026-11-09
- **CLI Tool:** Codex CLI (`codex`) `0.167.0`
- **Model:** `gpt-6.1-sol`
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted implementation, tests and documentation under Fred's direction.
- **Implementation commit:** `5d180905ae6355a97b17a27b1589d911b5d8acf2`.

## Guiding prompts

> Refresh your recollection of Tamlinux and the goals for 0.6. Then propose a plan for Tamlinux 0.6.21. I believe we have already included tam-monitor but nothing else. What faults can we correct and what missing functionality can we provide in 0.6.21?

> Implement the plan.

Fred selected a bounded repair of upgrade transactions and offline recovery,
with verification of existing launcher, scheduling and health behavior.
Broader upgrade-design completion and sleep/firewall/fleet changes stay outside
this implementation.

## Implementation

- Bind forward deployment to a unique transaction ID and a digest of the
  confirmed local assembly, profile generation, pin bytes and deployment receipt.
- Serialize deployment mutations, record immutable baseline package identities
  before activation, and recover only the current named transaction. Keep
  ordinary previous-generation rollback separate from failed-upgrade recovery.
- Verify an already restored baseline without a second activation. Retain
  original and recovery errors, block unsafe retries, and report a failed
  upgrade accurately even when recovery succeeded.
- Publish current/history receipts atomically and record file backup intent
  before renames. Preserve later edits and report unresolved backup conflicts.
- Exercise the actual host-launch JavaScript with synthetic private Qt paths
  and execute the resulting detached-child argv to verify environment cleanup.

## Verification and limits

- Focused suites: **30 upgrade tests, 116 deployment tests and 7 launcher tests passed**.
- Complete suite: `desktop/check-all --rev 5d18090`, **292 units, zero failures,
  424 seconds, zero core dumps**. Fourteen checks skipped: five opt-in GTK/D-Bus
  proofs and nine migration checks requiring json5, absent from the runner's
  Python. Those skips are not passes; package integration provides json5 and
  retains its own checks.
- Staged command layout: offline `--status` and backend recovery help passed.
- Later changes in this session update provenance only; implementation and
  executable tests remain those of the tested commit above.

Focused upgrade, deployment and launch-environment suites cover apply success,
failure before activation, successful/failed recovery, interrupted transactions,
stale/foreign receipts, missing generations, later edits and two-process locks.
Offline deployment tests activate isolated temporary generations, verify real
links, and refuse component metadata rediscovery.

The existing monitor 0.3.0 implementation remains selected for the next candidate;
this session does not claim its earlier physical trial as packaged acceptance.
Live baseline inspection confirms the realtime guard is set and health metrics
are readable. Arch and shell Qt versions currently match, so differing-version
physical menu proof remains open. Audio/load, full panel overhead, physical VT
and exact packaged-candidate checks remain pending. No Test, Run or Release
transition, root change, hibernation or desktop restart was performed.

The current forward deployment backend still needs component clones. Full
lock-graph validation, settings checkpoints and native archive verification are
separate unfinished parts of the upgrade design. Recovery depends on retaining
its recorded generation and local consumer configuration; incomplete or edited
identity refuses recovery rather than guessing.
