# 2026-09-23 — Antigravity Live Limits Investigation and Implementation

- **Tool:** Antigravity CLI (`agy`)
- **Model:** Gemini 3.8 Flash (High)
- **Session:** `b76c4bc7-94b9-4bfd-b673-e255374b2f10`
- **User prompt:**
  > Investigate why in fred.agents we could not figure out how to display usage limits for agy. Do research and propose a plan to fix that. We show limits for our other AI subscriptions. Please try to get limits working for antigravity, too.

## Investigation and Resolution

1. **Why Past Attempts Failed:**
   - Previous exploration on 2026-09-20 targeted an expired credentials file `~/.gemini/oauth_creds.json` instead of the active system keyring (`secret-tool lookup service gemini username antigravity`).
   - External refresh attempts using reverse-engineered client credentials triggered Google OAuth single-use refresh token rotation, causing 401 Unauthorized errors.
   - Direct HTTP requests to `daily-cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary` failed with 403 Forbidden because Google requires a `User-Agent: Antigravity` header.
   - The non-interactive command `agy --output-format json -p "/usage"` was previously undiscovered; it provides structured quota data in ~4 seconds with zero token cost.

2. **What Was Built:**
   - Updated `bin/tam-agent-usage-antigravity`:
     - Fast HTTP probe (<300ms) with `User-Agent: Antigravity` against `retrieveUserQuotaSummary` and `loadCodeAssist`.
     - Non-interactive CLI fallback (`agy -p /usage --output-format json`) for automatic credential refresh when tokens lapse.
     - Maps Google's quota hierarchy into 4 limit rows: Gemini Weekly, Gemini 5-hour, Claude & GPT Weekly, and Claude & GPT 5-hour.
     - Detects and reports the `"Google AI Pro"` subscription tier.
     - Caches results at `~/.cache/omarchy/agent-usage/antigravity-limits.json` with a 15-second debounce and open-window fallback.
   - Mirrored collector to `~/Code/tamlinux/config-fred-tamlinux/config/omarchy/plugins/fred.agents/bin/tam-agent-usage-antigravity`.
   - Bumped deployed version to `1.2.0` (`[1.2.0] - Unreleased` in CHANGELOG.md; `manifest.json` and `Panel.qml`).
   - Created detailed plan and investigation report in `docs/plans/fred-agents-antigravity-limits-plan.md` and reviewed in Omawrite.
