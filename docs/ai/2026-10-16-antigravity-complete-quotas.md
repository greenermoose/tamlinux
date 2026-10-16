# Complete Antigravity quotas in fred.agents

- **Date**: 2026-10-16
- **CLI Tool**: Codex CLI (`codex`) `0.163.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted implementation and verification directed by Fred.
- **Prompt**:
  > Please fix fred.agents so I get a complete view of my agy quota remaining.

## Problem and change

The direct Google quota-summary endpoint returned HTTP success but contained
only the Claude/GPT group. agy 1.4.0's structured `/usage` report contained
Gemini, Claude/GPT, and a separately metered Gemini 4 Argon weekly group.
The collector previously accepted the partial HTTP report without invoking
its CLI fallback, hiding Google model quotas from the panel.

Use `agy --output-format json -p /usage` as the quota source, retaining the
existing 12-second command deadline and 15-second debounce. The keyring and
HTTP endpoint are now used only for subscription metadata, after agy has
handled any credential refresh. Do not invent a Pro plan if tier metadata is
unavailable. Quota retrieval still succeeds independently of tier retrieval.

Preserve distinct model group names such as Gemini 4 Argon; normalize only
the generic Gemini group. Prefer explicit window identifiers over digits in
model names. Validate quota fractions and reject empty or malformed reports
instead of caching invented full allowances. Mark cache source versions so
the previous partial HTTP cache cannot debounce away the first complete
refresh. Retain only unexpired cached windows after failure, marked last
known with the original reading time using the panel's existing contract.

Plugin 2.0.5 is development source for a future Tamlinux candidate. No
deployment or stage promotion is part of this change.

## Verification

- Plugin suite: 29 tests passed, including 10 new quota regressions covering
  all five windows, Argon's distinct label, future Gemini group names, invalid
  reports, cache migration, debounce/force behavior, and refresh failures.
- Isolated live collector diagnostic against agy 1.4.0: all five uniquely
  labeled windows, reset timestamps, subscription tier, and the complete
  cache source marker were returned in 4.56 seconds. Diagnostic cache was
  temporary; the running plugin and its caches were not changed.
- Desktop regression suite: 599 tests passed (one skipped).
- `git diff --check`, public provenance privacy scan, and new record links passed.
