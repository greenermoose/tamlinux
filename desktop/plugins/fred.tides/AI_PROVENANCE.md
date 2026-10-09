# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the AI tools, models, prompts, and architectural decisions that shaped `fred.tides`.

---

## How to read this record

This repository follows the Tamlinux [AI provenance standard](https://github.com/greenermoose/tamlinux/blob/main/docs/ai-provenance-standard.md). In
brief: commits made with AI help carry `AI-Tool` and `AI-Model` trailers, and
each session record in [`docs/ai/`](docs/ai/) gives the date, tool version,
model, Fred's guiding prompts verbatim, the commits, and the decisions. Session
transcripts are retained privately by the author, so the records carry no
session IDs or local transcript paths.

---

## 1. Fred's Multi-Agent AI Toolchain

Rather than relying on a single AI model or interface, Fred uses a specialized toolchain tailored to each tool's strengths. CLI versions below reflect the environment captured during development (`<tool> --version`).

| Tool & Interface | CLI Version | Backing Models | Primary Role in the Ecosystem |
| :-- | :-- | :-- | :-- |
| **Claude Code** (`claude`) | `2.1.267` | Claude Opus 5 (`claude-opus-5`) | **Architecture & System Planning**: Authoring durable system specifications, multi-step runbooks, and cross-cutting policies. |
| **Codex CLI** (`codex`) | `0.156.1` | `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-6-sol` | **Architecture & System Planning**: Second opinion on plans and specifications alongside Claude. |
| **Antigravity CLI** (`agy`) | `1.2.6` | Gemini 3.8 Flash (High) | **Coding, Refactoring & Implementation**: Primary coding partner for multi-file pair-programming, security remediation, bash/Python/QML engineering, and git release workflow. |
| **OpenCode** (`opencode`) | `1.18.30` | Big Pickle | **Distro & System Q&A**: Efficient lookups for Arch Linux / Omarchy package specifics and shell configuration, conserving frontier-model token budgets. |
| **Grok CLI** (`grok`) | `1.0.25` (`f7e67d6988e2`, stable) | Grok 4.6 | **Workstation Support**: Additional debugging, hardware diagnostics, and alternative implementation analysis. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Initial Implementation & Provider Architecture** | `v1.0.0` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Built multi-monitor focus-isolated tide widget (`TidesPanelWindow.qml` & `TidesStore.js`) based on `Woogy7/omarchy-tides`, featuring 24h Catmull-Rom tide curve, Open-Meteo Marine integration, glanceable bar hover tooltip, configurable units (`m`/`ft`), and closed-environment security baseline. Planned v1.1 NOAA & harmonic provider architecture. |
| **Panel Range Bar, 4-Tide Layout & Hover Refinements** | `v1.0.1` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Styled location pill like `fred.weather` with province/state and overflow elision; added curve range bar showing extrema and real-time water level indicator; expanded bottom cards to list all 4 daily tides; streamlined hover tooltip formatting without colons or Today's range. |
| **Header Layout Reordering & In-Place Unit Switching** | `v1.0.2` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Reordered header stats so Tide precedes Now; removed redundant Range column; removed standalone M toggle button and moved unit toggle into an interactive box next to the Now value displaying full unit name (`meters`/`feet`); added monitor-targeted IPC handlers. |
| **Legibility Font Refinement (Unslashed Zero)** | `v1.0.3` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Restored panel-wide font to system default (`root.bar ? root.bar.fontFamily : Style.font.family`) to respect user desktop themes; scoped numeric font (`Liberation Sans`) specifically to numeric displays (card times, heights, curve timestamps) for tabular fixed-width digits with clean, unslashed/undotted open zeros, eliminating confusion between 10 and 18 at small font sizes. |
| **Marketplace notification security fix** | `v1.0.4` | Codex CLI (`codex 0.155.1`, `gpt-6-sol`) implementation; Cursor `3.21.16` (`composer`) release | Replaced shell-built right-click notification command with a bounded literal argv call through a closed-environment process and watchdog; released after Fred's live test. |

The 2026-09-22 security work is recorded in [`docs/ai/sessions.md`](docs/ai/sessions.md).

## 2026-09-22 Tamlinux branding

Cursor `3.21.16` (`composer`) replaced the current-facing `for Omarchy Linux` tagline with Tamlinux.

## 2026-09-23 upstream survey foundation

Codex CLI `0.156.1` (`gpt-6-sol`) established the root upstream reference
and dated survey directory for this repository. This was documentation only;
no field survey or runtime change was made.
[Session record](docs/ai/2026-09-23-upstream-survey-foundation.md).

## 2026-09-28 private session IDs

Claude Code `2.1.283` (`claude-opus-5-5`) removed session IDs and local
transcript paths from this repository's AI records and linked the public
provenance standard. Documentation only.
[Session record](docs/ai/2026-09-28-private-session-ids.md).

## 2026-10-03 shell-independent 2.0.0

Cursor `3.23.12` (`composer`) rewrote `fred.tides` to 2.0.0 on
`develop/2.0.0`. The widget no longer calls `bar.run`. Not tagged or
released.
[Session record](docs/ai/2026-10-03-shell-independent-2.0.0.md).

## 2026-10-03 compositor facade reads

Cursor `3.23.12` (`composer`) pointed fred.tides 2.0.0 QML at the Tamlinux
compositor facade. Both IPC targets pass the facade's focused output and output list into the store. `TidesPanelWindow` takes keyboard focus only on the focused output. Not tagged or released.
[Session record](docs/ai/2026-10-03-compositor-facade.md).

## 2026-10-06 Tamlinux-only dependencies

Claude Code `2.1.291` (`claude-opus-5-5`) removed the last Omarchy dependencies on `develop/2.0.0` and added a test that keeps them out. Notifications run `tam-notification-send` by absolute path from `TAMLINUX_BIN`, falling back to `~/.local/bin`. `OMARCHY_PATH` is no longer read or copied into the closed environment. The panel layer is `tamlinux-tides-panel`. Not tagged or released.
[Session record](docs/ai/2026-10-06-tamlinux-only-dependencies.md).
