# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the AI tools, models, prompts, and architectural decisions that shaped `fred.tides`.

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
| **Initial Implementation & Provider Architecture** | `v1.0.0` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Built multi-monitor focus-isolated tide widget (`TidesPanelWindow.qml` & `TidesStore.js`) based on `Woogy7/omarchy-tides`, featuring 24h Catmull-Rom tide curve, Open-Meteo Marine integration, glanceable bar hover tooltip, configurable units (`m`/`ft`), and closed-environment security baseline. Planned v1.1 NOAA & harmonic provider architecture. |
| **Panel Range Bar, 4-Tide Layout & Hover Refinements** | `v1.0.1` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Styled location pill like `fred.weather` with province/state and overflow elision; added curve range bar showing extrema and real-time water level indicator; expanded bottom cards to list all 4 daily tides; streamlined hover tooltip formatting without colons or Today's range. |
| **Header Layout Reordering & In-Place Unit Switching** | `v1.0.2` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Reordered header stats so Tide precedes Now; removed redundant Range column; removed standalone M toggle button and moved unit toggle into an interactive box next to the Now value displaying full unit name (`meters`/`feet`); added monitor-targeted IPC handlers. |
| **Legibility Font Refinement (Unslashed Zero)** | `v1.0.3` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Restored panel-wide font to system default (`root.bar ? root.bar.fontFamily : Style.font.family`) to respect user desktop themes; scoped numeric font (`Liberation Sans`) specifically to numeric displays (card times, heights, curve timestamps) for tabular fixed-width digits with clean, unslashed/undotted open zeros, eliminating confusion between 10 and 18 at small font sizes. |
