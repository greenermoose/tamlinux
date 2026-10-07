# Session: 2026-10-06 — Optional Sway helper executor (Develop)

- **CLI Tool**: Codex CLI (`codex`) `0.160.1`, checked against the live binary.
- **Model**: `gpt-6.1-sol`, verified against current turn metadata.
- **Implementation**: AI-assisted development by Fred and Codex.
- **Code commit**: `17f032f`.
- **Transcript**: Retained privately by the author.
- **Stage**: Develop on an isolated branch; existing helpers do not select this executor.

## Guiding prompt

> Claude is back and working on 0.3.2 for tamlinux. Keep going with your 0.4.0 work. Communicate and coordinate with claude so you don't step on each others' toes.

## Implementation and decisions

The existing pure request planner and typed output facts now have an optional
executor in `desktop/shell/host/sway_helper_executor.py`. Callers provide a
socket path and opt into mutations explicitly. Socket selection does not use
ambient compositor variables. Endpoint checks require a same-user socket in
a private immediate parent and reject symlinks at those two final components.
They do not defend against replacement by processes owned by the same user.

Each child runs an absolute executable with a closed environment, no stdin,
and no shell. Both output streams are capped at 256 KiB during collection.
Reads share one monotonic deadline across their subprocesses; child process
groups are killed and reaped after deadlines or cap failures. Facts from
inconsistent reads fail rather than supplying a guessed monitor snapshot.

Results distinguish recorded plans, success, failure, and unsupported
operations. A recorded mutation is not compositor success. Interrupted or
failed mutations indicate possible delivery and are never replayed
automatically. A batch preserves successful and failed command indexes.

The private Sway IPC check exposed an assumption in the earlier candidate:
a three-command batch stopped after command two failed, returning only two
replies. The contract now preserves that failed prefix and explicitly lists
unreported indexes. It does not infer whether those remaining commands ran.
A short all-success reply still fails validation. This correction was to
Codex's prior candidate, not delegated work.

The [Sway IPC manual](https://man.archlinux.org/man/sway-ipc.7.en) documents
responses for parsed commands; the [swaymsg manual](https://man.archlinux.org/man/swaymsg.1.en)
documents explicit socket selection and error exit statuses. Both were checked
during implementation. Installed Sway and swaymsg were version `1.12`.

## Verification

- 20 new executor tests passed: closed child environment, explicit endpoint
  selection, shared read deadline, malformed and inconsistent responses,
  partial command outcomes, uncertain delivery, socket refusals, concurrent
  pipe draining, byte caps, hung children, slow output, inherited pipes,
  invalid UTF-8, and unavailable binaries.
- Six opt-in IPC checks passed against a new headless Sway with two virtual
  outputs and its own home, runtime directory, configuration, and socket:
  output/focus joins, repeated focus of workspace 160, workspace/output moves,
  pixel mode versus fractional-scale layout coordinates, record-only
  behavior, disabled-output reads, and an aborted batch.
- One contract regression check covers failed prefixes and unreported
  indexes. The earlier planner and fact checks also passed.
- Full desktop suite: **450 tests run, one skipped, no failures**, using
  `TAMLINUX_TEST_SWAY_HELPERS=1 python3 -m unittest discover -s desktop/tests -q`.
- Public provenance privacy scan and Git whitespace checks passed.

The first sandboxed executor run could not bind its test sockets. Verification
therefore ran with approval outside that sandbox. An initial test assertion
also used the wrong pixel width for the existing synthetic fixture; it was
corrected to check physical mode and layout fields separately.

## Limits and remaining work

This verifies optional execution and IPC behavior. Existing helper loaders,
plugin code, version files, configuration and daily deployment are unchanged.
There is no `.run()` compatibility shim or persistent Sway config writer.
Headless checks do not prove physical display retraining, desktop-mode helper
parity, rollback persistence, or hardware power behavior. Preferred-mode
selection, numeric rotated transforms, log queries and config-error queries
retain the earlier candidate's explicit unsupported results. Shared provenance
index and private ledger rows were handed to their current owner for later
integration before public publication.
