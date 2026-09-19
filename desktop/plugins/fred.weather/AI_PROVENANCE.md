# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the AI tools, models, prompts, and architectural decisions that shaped `fred.weather`.

---

## 1. Fred's Multi-Agent AI Toolchain

Rather than relying on a single AI model or interface, Fred uses a specialized toolchain tailored to each tool's strengths. CLI versions below reflect the environment captured during development (`<tool> --version`).

| Tool & Interface | CLI Version | Backing Models | Primary Role in the Ecosystem |
| :-- | :-- | :-- | :-- |
| **Claude Code** (`claude`) | `2.1.267` | Claude Opus 5 (`claude-opus-5`) | **Architecture & System Planning**: Authoring durable system specifications, multi-step runbooks, and cross-cutting policies. |
| **Codex CLI** (`codex`) | `0.154.0` | `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra` | **Architecture & System Planning**: Second opinion on plans and specifications alongside Claude. |
| **Antigravity CLI** (`agy`) | `1.2.6` | Gemini 3.8 Flash (High) | **Coding, Refactoring & Implementation**: Primary coding partner for multi-file pair-programming, security remediation, bash/Python/QML engineering, and git release workflow. |
| **OpenCode** (`opencode`) | `1.18.30` | Big Pickle | **Distro & System Q&A**: Efficient lookups for Arch Linux / Omarchy package specifics and shell configuration, conserving frontier-model token budgets. |
| **Grok CLI** (`grok`) | `1.0.25` (`f7e67d6988e2`, stable) | Grok 4.6 | **Workstation Support**: Additional debugging, hardware diagnostics, and alternative implementation analysis. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Initial Implementation & Focus Isolation** | `v1.0.0` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Designed multi-monitor focus-isolated weather panel with 48h timeline curve, 10-day forecast, Font Awesome Sun glyph (`\uf185`), hover tooltip briefing, and closed-environment security baseline. |
| **Location Header & Tooltip Reordering** | `v1.0.1` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Added city/state location formatting and reordered tooltip lines with version at bottom separated by blank line. |
| **Custom Hover Popup, IPC Control & Preview Assets** | `v1.0.2` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Implemented custom `PopupWindow` in `BarWidget.qml` with styled dimmed caption version footer, programmatic `showHover`/`hideHover` IPC methods, and HP monitor preview screenshot composite. |
| **Multi-Monitor Broadcast, Retry Hardening & Resume Sync** | `v1.0.3` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Added `refreshAll` and payload broadcast across monitors via `WeatherStore.js`, implemented `scheduleDailyForecastRetry()` with exponential backoff in `Panel.qml`, and wired resume hook in `msi-mp161-resume-workaround`. |
| **Daily Forecast Local Timezone Alignment** | `v1.0.4` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Fixed off-by-one daily forecast date bug where late-evening local time in western timezones rolled to UTC tomorrow; added `forecastTodayString`, cache rollover filtering, and dynamic today index resolution. |

Detailed session logs and prompts are documented in [`docs/ai/sessions.md`](docs/ai/sessions.md).
