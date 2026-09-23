# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the
AI tools, models, prompts, and architectural decisions that shaped Tamlinux's
public description and development plans.

---

## 1. Fred's Multi-Agent AI Toolchain

Rather than relying on a single AI model or interface, Fred uses a specialized
toolchain tailored to each tool's strengths. Most CLI versions below were
captured on 2026-09-22 (`<tool> --version` / `cursor --version`); the Codex
version was checked again for the 2026-09-23 planning session.

| Tool & Interface | CLI Version | Backing Models | Primary Role in the Ecosystem |
| :-- | :-- | :-- | :-- |
| **Claude Code** (`claude`) | `2.1.280` | Claude Opus 5 (`claude-opus-5`) | **Architecture & System Planning**: Authoring durable system specifications, multi-step runbooks, and cross-cutting policies. |
| **Codex CLI** (`codex`) | `0.156.1` | `gpt-6-astra`, `gpt-6-sol`, `gpt-5.6-sol` | **Architecture & System Planning**: Second opinion on plans and specifications alongside Claude. |
| **Antigravity CLI** (`agy`) | `1.2.8` | Gemini 3.8 Flash (High) | **Coding, Refactoring & Implementation**: Primary coding partner for multi-file pair-programming, security hardening, and git release workflow. |
| **Cursor** (`cursor`) | `3.21.16` | composer | **Implementation in this repository**: public explainer, suite branding, and 0.0.1 versioning. |
| **OpenCode** (`opencode`) | `1.18.31` | Big Pickle | **Distro & System Q&A**: Efficient lookups for Arch Linux package specifics and shell configuration. |
| **Grok CLI** (`grok`) | `1.0.25` | Grok 4.6 | **Workstation Support**: Additional debugging and hardware diagnostics. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Public explainer (first version)** | first description | Cursor `3.21.16` (`composer`) | Public one-liner, etymology, values, plugin-suite links, GPL-3.0-or-later. Not an installable image. [Session record](docs/ai/2026-09-22-public-explainer.md). |
| **Product version 0.0.1** | 0.0.1 | Cursor `3.21.16` (`composer`) | First Tamlinux version. 0.x is Omarchy-based; 1.x is independent. Home Manager generation is recorded separately. [Session record](docs/ai/2026-09-22-version-0.0.1.md). |
| **Installation and command plans** | 0.0.1 planning | Codex CLI `0.156.1` (`gpt-6-sol`), with Fred's direct edits and review | Omarchy first installation profile; NixOS pilot next; approved first `tamlinux` command slice, first-use welcome, and Lynx fallback. No installer or command implementation yet. [Session record](docs/ai/2026-09-23-installation-and-command-plans.md). |

Detailed session records are indexed in [`docs/ai/sessions.md`](docs/ai/sessions.md).
