# 2026-10-06 — Optional Hyprland helper executor

- **CLI Tool**: Codex CLI (`codex`) `0.160.1`, checked live.
- **Model**: GPT-6.1 Sol (`gpt-6.1-sol`), verified by the runtime detector.
- **Implementation author**: Codex, directed by Fred.
- **Code commit**: `cf93d61`.
- **Stage**: Develop; optional candidate on an isolated branch.
- **Transcript**: Retained privately by the author.
- **Prompt**:
  > Both opencode and agy are busy. Now, find something useful for you to do. Claude is done with 0.3.3.

## Result

`hyprland_helper_executor.py` fills the transport gap in the existing paired
helper candidates. Callers provide the socket explicitly. Valid named plans
become Hyprland IPC requests; normal requests use the flags separator, JSON
queries use `j/`, and batches use `[[BATCH]]` with the existing closed command
builders. The executor does not start hyprctl or discover a running session.

The endpoint must be a socket owned by the caller in a private immediate
parent directory. Symlink endpoints are refused. Linux peer credentials must
also match the caller before sending. These checks do not isolate the executor
from another process owned by the same user changing ancestors or endpoints.

Connect, send and reply collection share one monotonic deadline. Requests are
capped at 16 KiB, replies at 256 KiB while collecting. Invalid UTF-8 or NUL
replies fail. The client half-closes its write side after the request, allowing
the server to finish requests divisible by its 1023-byte read size. Source
inspection verified flags, batch encoding, EOF collection and the triple-newline
batch reply delimiter against locally installed Hyprland 0.56.2 source:
`hyprctl/src/main.cpp` and `src/debug/HyprCtl.cpp`.

Mutations record unless `live=True` is explicitly supplied as a boolean.
Recording is not success. A mutation requires an exact acknowledgement for
each command; partial batch failures retain their indexes. Sending attempts,
including failed or timed-out sends, report potentially changed state without
retrying or automatically selecting a fallback. Acknowledgement does not prove
the final display state: callers must reconcile it using a subsequent read.

Monitor and active-workspace reads use the existing typed normalization.
Configuration errors and non-following logs remain bounded diagnostic text.
Unsupported monitor facts remain unsupported rather than fabricated.

## Verification and remaining integration

- 22 new tests cover closed operation selection, recording, exact wire format,
  request limits, private real-socket facts and acknowledgements, partial batch
  replies, deadline/slow-drip failures, response limits including the exact
  boundary, bad encoding, endpoint/peer checks and uncertain partial sending.
- Full desktop regression outside the sandbox: **500 tests, OK, 7 intentional
  skips**. Private socket fixtures required sandbox escalation. No daily
  compositor was contacted; all socket tests use disposable private servers.
- The branch includes current 0.3.3 main at `16a459b`, including its session
  environment fix, along with the previous Sway and Hyprland helper candidates.

Existing helper loaders and daily deployment remain at their accepted versions.
Integrating the normalized monitor schema, persisting layouts, verifying reset
behaviour and live hardware parity belong to the next integration step. Shared
provenance indexes and the private ledger must be reconciled before a public
push; this record is ready for that handoff.
