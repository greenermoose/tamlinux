# Changelog

All notable changes to `fred.agents` (`omarchy-fred-agents`) will be documented in this file.

## [1.1.0] - Unreleased

### Added
- Cursor live plan usage: `omarchy-agent-usage-cursor` reads the sign-in token
  Cursor keeps in `state.vscdb` (read-only, in-memory only) and probes its
  dashboard RPC (`api2.cursor.sh` `DashboardService/GetCurrentPeriodUsage`) for
  the percent of the monthly plan used plus the billing-cycle reset time. The
  panel's Limits section now renders Cursor alongside Claude and Codex, with a
  `tierLabel` from the stored membership plan. Failures fall back to the last
  known limits and say so. (Endpoint is unofficial and may change.)

## [0.1.0] - Unreleased

### Added
- Clone of `omarchy.agents` (as `fred.agents`), replacing the stock panel on the bar.
- Rename display label "Claude Code" to "Claude"; drop Fireworks from the defaults.
- Vendored collector pipeline inside the plugin (`omarchy-agent-usage-update` + `-claude`, `-codex`) with descriptor-relative resolution, so no files under `/usr/share/omarchy/` are touched.
- Track Antigravity and Cursor by prompt, session, and active-day counts (these two expose no local token usage).

## [0.2.0] - Unreleased

### Added
- `bin/omarchy-agent-usage-cursor` collector: prompt counts from Cursor agent transcripts (`~/.cursor/projects/*/agent-transcripts/*/<uuid>.jsonl`, subagent files folded into their parent session) plus older composer sessions from `conversation-search.db`, cached with the same lock+atomic scheme as the other collectors.
- `bin/omarchy-agent-usage-antigravity` collector: prompt counts from `~/.gemini/antigravity-cli/history.jsonl` (slash-command rows excluded), with per-conversation session counts and days from `conversation_summaries.db`.

## [1.0.0] - Unreleased

### Added
- Prompt-mode panel: token-less agents (`tokensAvailable: false` — Cursor, Antigravity) render **PROMPTS BY DAY** with raw counts and "N prompts · M sessions" tooltips; the TOKENS BY MODEL section stays suppressed for them.
- Bar marks for Cursor and Antigravity (`assets/cursor.svg` + `-light`, `assets/antigravity.svg` + `-light`).