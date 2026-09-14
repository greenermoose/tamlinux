# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the AI tools, models, prompts, and architectural decisions that shaped `fred.workspaces`.

---

## 1. Fred's Multi-Agent AI Toolchain

| Tool & Interface | Backing Models | Primary Role |
| :-- | :-- | :-- |
| **Claude Code & Codex** | Claude 3.7 Sonnet, o3-mini | Planning, workspace indicator design, and multi-monitor desktop mode architecture. |
| **Antigravity CLI (`agy`)** | Gemini 3.8 Flash (High), Gemini 2.5 Pro | Implementation partner: QML workspace indicators, `omarchy-desktop-mode` helper CLI, atomic config management, security hardening for marketplace listing. |
| **OpenCode** | Open-source models | Hyprland IPC, Quickshell event binding, and workspace rule diagnostics. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Initial Implementation** | `v1.0.0` | Claude & Antigravity | Cloned stock `omarchy.workspaces`, added dynamic visual indicators and multi-monitor desktop switching. |
| **In-Place Replacement** | `v1.1.0` | Claude & Antigravity | Stamped `omarchy.clonedFrom: "omarchy.workspaces"` to preserve relative layout anchors (`findRelativeBarLocation`) and enable clean in-place replacement. |
| **Security Hardening** | `v1.2.0` | Antigravity (Gemini) | Sanitized process execution, eliminated arbitrary code execution in configuration parsing, and implemented atomic JSON state writes. |
| **Marketplace Verification** | `v1.2.1` | Antigravity (Gemini) | Successfully verified and listed on the official [Omarchy Plugin Marketplace](https://github.com/omacom/omarchy-plugin-marketplace) with an automated security baseline rating of **Passed**. |

Detailed session logs and prompts are documented in [`docs/ai/sessions.md`](docs/ai/sessions.md).
