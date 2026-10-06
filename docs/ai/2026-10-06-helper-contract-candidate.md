# 2026-10-06 — Offline workspace/monitor helper candidates

- **Tool:** Codex CLI 0.160.1, checked at runtime.
- **Model:** gpt-6.1-sol, verified from the active runtime/rollout.
- **Authorship:** AI-assisted; Codex wrote the candidate code, tests and this
  record. Fred supplied the goal and concurrency constraints.
- **Transcript:** Retained privately by the author.
- **Source base:** `27fcf0d`.
- **Implementation/tests:** `6326de624c6b7850a12c7a770b156405fa9cf89e`.
- **Stage:** Develop-only preparation; no version promotion or deployment.

## Guiding prompts

Fred's original prompt, excerpt verbatim:

> Look ahead at the plan. Find something you can be doing and do it in a way that won't conflict with claude. Figure out worktrees or a communication system so that you can claim some work and claude will know what you are working on.

Fred's continuation prompt, verbatim:

> Claude is out of tokens. Can you keep going without claude for now and just apprise it of your progress? I have handed off the 0.3.2 work that claude was doing to a codex session which is actively working on it now.

## What changed and why

Four new files prepare the helper contract without changing the concurrent
0.3.2 implementation:

- [helper_contract.py](../../desktop/shell/host/helper_contract.py) separates
  physical mode pixels, logical layout bounds, power and enablement;
  preserves unknown values and validates JSON/command outcomes.
- [sway_helper_backend.py](../../desktop/shell/host/sway_helper_backend.py)
  plans named workspace/monitor requests and parses read facts. Dispatch
  numbers reach 160 independently of the shell UI's 1–10 range. Focus
  requests suppress automatic back-and-forth; DPMS uses power, not disable.
- The two new test modules challenge malformed/partial replies, read races,
  scaled/rotated geometry, unknown facts, input bounds and named requests.

The module recognizes the 18 helper operation names. `config-errors` and
`rollinglog` are explicitly unsupported by this candidate; no claim is
made that Sway lacks equivalent mechanisms. Numeric transforms other than
zero and `preferred` mode selection also fail explicitly until their
translations have parity evidence.

The candidate has no executor or `.run()` compatibility shim and is not
selected by existing helpers. It does not choose persistence location,
numeric rotation mappings, recovery policy or hardware reset verification.
Fallback names currently produce equivalent Sway candidate requests;
independent fallback recovery has not been demonstrated. Command sequences
are not atomic; every reply must succeed and partial success remains visible.

## Source evidence

The installed Sway was 1.12. Its output/workspace replies inform the data
join; command replies contain per-command success results.
[Sway 1.12 IPC documentation](https://github.com/swaywm/sway/blob/1.12/sway/sway-ipc.7.scd).

Workspace/move request spelling and automatic back-and-forth suppression
follow the command documentation; output configuration and power operations
follow its output documentation.
[Sway command reference](https://github.com/swaywm/sway/blob/master/sway/sway.5.scd),
[output reference](https://github.com/swaywm/sway/blob/master/sway/sway-output.5.scd).

Refresh units are millihertz; zero is not a measured 60 Hz. Sway reverses
Wayland 90/270 enum labels when producing clockwise transform strings,
so the facts retain strings rather than guessing a numeric correspondence.
[wlroots output types](https://wlroots.pages.freedesktop.org/wlroots/wlr/types/wlr_output.h.html),
[Sway 1.12 serializer](https://github.com/swaywm/sway/blob/1.12/sway/ipc-json.c#L83).

## Validation and remaining integration

```bash
python3 -B -m unittest discover -s desktop/tests -p 'test_*helper*.py' -v
python3 -B -m unittest discover -s desktop/tests -p 'test_*.py'
```

**29 focused tests passed. The full desktop suite ran 423 tests, one skipped,
with no failures.** These are synthetic input/request and existing suite
checks, not live compositor parity or hardware validation.

Later integration still needs selection/loader wiring, a helper-facing
unknown-value policy, bounded execution and retry, both-adapter parity,
transaction rollback/persistence, reset verification and an isolated Sway
test session. Existing versions and running services are unchanged by this
candidate.
