# Changelog

All notable changes to `fred.agents` (`agents-fred-tamlinux`) will be documented in this file.

## [1.1.2] - Unreleased

### Added
- Bar hover now shows a per-agent limits summary ("AI Agent Usage") through
  the standard themed bar tooltip (`tooltipText`): each agent's binding-window
  percent (the fullest limit, the one that stops the next prompt) and its
  reset stamp (`yyyy-mm-dd hh:mm`, local time), one line per agent. Providers
  with no limits — Antigravity until live limits land, synced-only agents —
  read "unknown". The text ends with the `fred.agents vX.Y.Z` footer.
- The panel's limit rows now pair the countdown with the absolute stamp:
  `Resets in Xd Yh Zm on yyyy-mm-dd hh:mm`, hiding the leading zero day/hour
  when the window rolls sooner than a day or an hour.

## [1.1.1] - Unreleased

### Added
- Cursor limits show both meters from the dashboard RPC: the included-total
  percent (`totalPercentUsed`) and the separate auto-model percent
  (`autoPercentUsed`) that Cursor's in-app Plan view surfaces (61% vs 56% with
  untouched API-model spend). Each is its own row in the Limits section, both
  resetting with the billing cycle. The binding window is now the fullest of
  the two, so the meter that actually throttles first drives the hero.

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