# Session: 2026-09-20 — Development to Pre-Release (`0.1.0`–`1.0.0`)

- **Date**: 2026-09-20
- **Tool**: `opencode` (OpenCode `1.18.31`)
- **Model**: Big Pickle (`big-pickle`)
- **Scope**: `fred.agents` from scratch through milestone D, plus the
  pre-release prep phase of milestone E
- **Transcript**: opencode store session `ses_f40a47824ffeTRjyEoDjuA9NUj`
  (`~/.local/share/opencode/opencode.db`)
- **Attribution**: verified. Tool and model were read live.

## Prompts

This session ran the milestones in sequence; guiding prompts read verbatim:

> Clarify that the public GitHub repo will be omarchy-fred-agents and we'll have a local copy of the repo at ~/Code/omarchy-fred-agents. The development work should start in that repo.

> Please add a fred.agents version message on hover over the agents icon. I'm not seeing that.

> Continue toward milestone B.

> Continue to milestone C.

> Continue to milestone D.

> Continue if you have next steps, or stop and ask for clarification if you are unsure how to proceed.

## What was built

- **Swap & Rebrand (A)**: replaced the stock `omarchy.agents` bar plugin in
  place via `omarchy.clonedFrom`; display label "Claude Code" → "Claude";
  dropped Fireworks from the defaults; vendored the collector pipeline
  (`omarchy-agent-usage-update` + `-claude`, `-codex`) with descriptor-relative
  resolution and a closed environment, so no files under `/usr/share/omarchy/`
  are touched. Records land in `~/.local/state/omarchy/agents/usage/`.
- **Version hover (A5)**: `pluginVersion` shown on hover over the bar icon;
  tooltip reads "fred.agents v<version>".
- **Cursor collector (B)**: `bin/omarchy-agent-usage-cursor` — prompts from
  `~/.cursor/projects/*/agent-transcripts/<uuid>/<uuid>.jsonl` (top-level =
  one session; `subagents/` files folded into the parent session, never their
  own sessions), plus legacy composer sessions from `conversation-search.db`
  (rows matching transcript ids skipped to avoid double counting). Day = the
  first `<timestamp>` element parsed from the top-level transcript, else mtime.
  Cache: flock + atomic 0644 + `scanDate` staleness in
  `~/.cache/omarchy/agent-usage/cursor-scan-<digest>.json`, stdlib only.
- **Antigravity collector (C)**: `bin/omarchy-agent-usage-antigravity` —
  prompts from `~/.gemini/antigravity-cli/history.jsonl` (177 slash-command
  rows excluded so only real prompts count), sessions/days from
  `conversation_summaries.db` (`last_user_input_time`, `last_modified_time`
  fallback; the single zero-timestamp row counts as a session without a day).
- **Prompt-mode panel (D)**: `tokensAvailable: false` propagates from each
  record through `Main.qml`'s sync aggregation (`displayProvider`,
  `providerAcc`, aggregate merge, output providers, `providerSnapshot`).
  Prompt-mode agents render **PROMPTS BY DAY** with raw counts (no
  `formatTokenCount` shorthand) and "N prompts · M sessions" tooltips; the
  TOKENS BY MODEL section is suppressed. Added marks `assets/cursor.svg` and
  `assets/antigravity.svg` (+ `-light` dark twins).
- **Pre-release prep (E, partial)**: synced the deployed copy into this public
  repo (no machine-specific paths), registered `fred.agents` in both copies of
  the CLI catalog (`CATALOG_REPOS`/`CATALOG_DESC`) with the real
  `omarchy-fred-agents` URL, added the suite README row and example output,
  added the showcase card with a placeholder preview, updated the suite plan,
  and wrote this provenance. **Push, current version 1.0.0, remains pending
  Fred's review.**

## Verification

- `omarchy plugin validate` passed on the public and deployed copies.
- Collector numbers verified exactly against independent recounts (Cursor:
  21 prompts today / 155 total / 46 sessions / 9 active days; Antigravity:
  10 today / 534 total / 81 sessions / 15 active days).
- Live shell checks: `omarchy-shell shell listPlugins` → `fred.agents`
  enabled, `clonedFrom: omarchy.agents`; after each deploy the shell was
  restarted newer than the deploy and `omarchy-agent-usage-update` wrote the
  expected records. Only the benign duplicate-`IpcHandler` warning from the
  clone override appears in the journal.
- `omarchy-fred-plugin info fred.agents` resolves the real repo URL and
  description in both source catalog copies.