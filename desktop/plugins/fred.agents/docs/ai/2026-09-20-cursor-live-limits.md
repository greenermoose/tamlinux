# Session: 2026-09-20/21 — Cursor live plan limits (research → `1.1.0`)

- **Date**: 2026-09-20 (research + implementation, interrupted) /
  2026-09-21 (completion, verification, docs)
- **Tool**: `opencode` (OpenCode `1.18.31`)
- **Model**: Big Pickle (`big-pickle`)
- **Scope**: milestone F — give the prompt-only Cursor collector live plan
  usage, following the Claude/Codex limits pattern; assess the same for
  Antigravity (blocked, milestone G)
- **Transcript**: opencode store sessions `ses_f3e75eee5ffeE0pG9EyMwWx8oF`
  (implementation, interrupted mid-file) and `ses_f3c853dceffecnb5epXXfdUJDG`
  (this continuation)
- **Attribution**: verified. Tool and model were read live.

## Prompts

> Explain how fred.agents determines how much usage is left for claude and
> codex.

> Don't cursor and google (for agy) provide an API for their agents, just like
> Anthropic and OpenAI do? Do some web research on this. In the agy app I can
> run the /usage command, so I know there's a way for that client to query an
> API endpoint.

> Are you okay? It seems like you stopped in the middle of the project.

> You were developing fred.agents. Please check your last session to see what
> you were doing and continue if you can.

## What was built

- **Cursor live limits (`bin/omarchy-agent-usage-cursor`)**: the collector now
  reads Cursor's stored sign-in from `state.vscdb` (`cursorAuth/accessToken`,
  `cursorAuth/stripeMembershipType`) **read-only**, decodes the JWT for expiry,
  and probes `POST https://api2.cursor.sh/aiserver.v1.DashboardService/
  GetCurrentPeriodUsage` (unofficial dashboard RPC) for the percent of the
  monthly plan used and the billing-cycle reset. The token exists only inside
  the probe's `Authorization` header — it is never printed or written; the
  record and the limits cache (`cursor-limits.json`, descriptor-relative,
  atomic) carry only percentages and reset times. `tierLabel` comes from the
  stored membership plan. Failures (429 / 401 / transport) fall back to cached
  limits that are still within their windows and say so; expired sign-ins read
  "Sign-in expired" with a hint. `--force` bypasses the 15 s probe-reuse
  window. Record keeps `tokensAvailable: false` / `hasPromptStats: true` /
  `scope: "device"` and now adds `limits` + `tierLabel`, which the panel's
  record-driven Limits section renders with no QML changes.
- **Antigravity live limits (milestone G) — blocked, not built**: end-to-end
  validation failed. The stored access token is expired and refresh at
  `https://oauth2.googleapis.com/token` returns 401 (client creds extracted
  from the agy binary do not match), and
  `daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist` returns 403
  with the expiry-touched token. Needs a fresh sign-in via the agy client
  (`/usage`) or a working credential path before the collector is worth
  writing.

## Verification

- `omarchy plugin validate` exits 0 on the published and deployed copies.
- Live run: `bin/omarchy-agent-usage-cursor --force` emits a valid record with
  `"tierLabel":"pro"` and `"limits":[{"label":"Monthly (billing cycle)",
  "percent":0.55,"resetsAt":"<iso>"}]`.
- Panel renders the new limits with no code change: `limitWindows()` reads
  `{label, percent, resetsAt}`, and `windowTitle("Monthly (billing cycle)")`
  maps to "Monthly" (Panel.qml:96-127).
- Deployment mirrored into the config repo; both copies at `1.1.0`.
- Not yet done: live shell restart + on-screen check (deferred under the
  multi-monitor/session-lock rules); commit and pre-release push pending Fred.