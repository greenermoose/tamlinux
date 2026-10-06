# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the AI tools, models, prompts, and architectural decisions that shaped `fred.sysinfo`.

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
| **Antigravity CLI** (`agy`) | `1.2.2` / `1.2.6` | Gemini 3.8 Flash (High) | **Coding, Refactoring & Implementation**: Primary coding partner for multi-file pair-programming, security remediation, bash/Python/QML engineering, and git release workflow. |
| **OpenCode** (`opencode`) | `1.18.30` | Big Pickle | **Distro & System Q&A**: Efficient lookups for Arch Linux / Omarchy package specifics and shell configuration, conserving frontier-model token budgets. |
| **Grok CLI** (`grok`) | `1.0.25` (`f7e67d6988e2`, stable) | Grok 4.6 | **Workstation Support**: Additional debugging, hardware diagnostics, and alternative implementation analysis. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Universal Linux Telemetry Engine & Popout Panel** | `v1.0.0` | Antigravity CLI (`agy 1.2.2`, `Gemini 3.8 Flash (High)`) | Designed pure-Python telemetry probe querying sysfs, procfs, hwmon, and PCI; built responsive Quickshell QML bar widget and popout panel with power profile switching and btop integration. |
| **Multi-Monitor Focus Isolation & Per-Monitor Dismissal** | `v1.1.0` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Implemented per-monitor focus isolation via custom `SysinfoPanel.qml` and `SysinfoStore.js`; eliminated cross-monitor dismiss twins and focus-stealing so background terminals/conversations retain focus; captured tightly cropped MSI monitor screenshot. |
| **Version Footers & Visual Status** | `v1.1.1` | Antigravity CLI (`agy 1.2.6`, `Gemini 3.8 Flash (High)`) | Embedded running version in bar icon hover tooltip and as a centered, styled footer at the bottom of the open telemetry panel (`Panel.qml`). |
| **Fresh Resource Hover & MSI Screenshots** | `v1.1.2` pre-release | Codex CLI (`codex 0.155.1`, `gpt-5.6-sol`) | Replaced the stale temperature/frequency hover with freshly probed CPU usage, available RAM, and free disk space; verified kernel hwmon temperature sources; captured updated hover and panel screenshots on the MSI display. |
| **Marketplace cache security fix** | `v1.1.2` | Codex CLI (`codex 0.155.1`, `gpt-6-sol`) implementation; Cursor `3.21.16` (`composer`) release | Removed shared scratch cache paths, added private runtime storage with descriptor-relative no-follow atomic writes and checked reads, and added cache attack tests; released after Fred's live test. |

Detailed session logs and prompts are documented in [`docs/ai/sessions.md`](docs/ai/sessions.md).

## 2026-09-22 Tamlinux branding

Cursor `3.21.16` (`composer`) replaced current-facing `Omarchy Linux` platform wording in the README and `sysinfo-probe.py` header with Tamlinux.

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

Cursor `3.23.12` (`composer`) rewrote `fred.sysinfo` to 2.0.0 on
`develop/2.0.0`. Opening the monitor is a host terminal action. Not tagged
or released.
[Session record](docs/ai/2026-10-03-shell-independent-2.0.0.md).

## 2026-10-03 compositor facade reads

Cursor `3.23.12` (`composer`) pointed fred.sysinfo 2.0.0 QML at the Tamlinux
compositor facade. IPC uses the facade's focused output name. `SysinfoPanel` takes keyboard focus only when that output is the panel's screen. Not tagged or released.
[Session record](docs/ai/2026-10-03-compositor-facade.md).

## 2026-10-06 Tamlinux-only dependencies

Claude Code `2.1.291` (`claude-opus-5-5`) removed the last Omarchy dependencies on `develop/2.0.0` and added a test that keeps them out. The panel layer is `tamlinux-sysinfo-panel`. Not tagged or released.
[Session record](docs/ai/2026-10-06-tamlinux-only-dependencies.md).
