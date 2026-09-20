# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the
AI tools, models, prompts, and architectural decisions that shaped
`fred.agents`.

---

## 1. Tools, Models & Sessions

| Tool & Interface | CLI Version | Backing Models | Primary Role in the Ecosystem |
| :-- | :-- | :-- | :-- |
| **OpenCode** (`opencode`) | `1.18.31` | Big Pickle (`big-pickle`) | **Implementation** across this repository: panel swap & rebrand, both new collectors (Cursor, Antigravity), and the prompt-mode panel. |

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Swap & Rebrand** | `0.1.0` | OpenCode (`big-pickle`) | Replaced the stock `omarchy.agents` bar plugin in place via `omarchy.clonedFrom`, renamed the display label "Claude Code" → "Claude", dropped Fireworks from the defaults, and added a version hover on the bar icon. |
| **Cursor collector** | `0.2.0` | OpenCode (`big-pickle`) | `bin/omarchy-agent-usage-cursor`: prompts from Cursor agent transcripts (`~/.cursor/projects/*/agent-transcripts/<uuid>/<uuid>.jsonl`, subagent files folded into their parent session), plus older composer sessions from `conversation-search.db`. Cached with the lock+atomic scheme shared by the other collectors. Verified exactly against an independent recount (21 prompts today, 5 sessions, 155 total, 46 sessions, 9 active days). |
| **Antigravity collector** | `0.2.0` | OpenCode (`big-pickle`) | `bin/omarchy-agent-usage-antigravity`: prompts from `~/.gemini/antigravity-cli/history.jsonl` (slash-command rows excluded), sessions and days from `conversation_summaries.db`. Verified exactly against an independent recount (10 prompts today, 1 session, 534 total, 81 sessions, 15 active days). |
| **Prompt-mode panel** | `1.0.0` | OpenCode (`big-pickle`) | Token-less agents (`tokensAvailable: false` — Cursor, Antigravity) render **PROMPTS BY DAY** with raw counts and "N prompts · M sessions" tooltips; the TOKENS BY MODEL section stays suppressed for them. `tokensAvailable` propagates end-to-end through `Main.qml` sync aggregation. Added bar marks `assets/cursor.svg` and `assets/antigravity.svg` (+ `-light` twins). Live shell verified: only the benign duplicate-`IpcHandler` warning from the clone override remains. |

---

## 3. Session Records

Individual session records are archived under [`docs/ai/`](docs/ai/). The
design plan lives in `omarchy-fred-config` (`~/docs/plans/fred-agents-plan.md`)
and records every decision with its date and rationale.