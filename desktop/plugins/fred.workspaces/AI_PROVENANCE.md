# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the AI tools, models, prompts, and architectural decisions that shaped `fred.workspaces`.

---

## 1. Fred's Multi-Agent AI Toolchain

Rather than relying on a single AI model or interface, Fred uses a specialized toolchain tailored to each tool's strengths. CLI versions below were captured on 2026-09-13 (`<tool> --version`).

| Tool & Interface | CLI Version | Backing Models | Primary Role in the Ecosystem |
| :-- | :-- | :-- | :-- |
| **Claude Code** (`claude`) | `2.1.273` | Claude Opus 5 (`claude-opus-5`) | **Architecture & System Planning**: Authoring durable system specifications, multi-step runbooks, and cross-cutting policies. |
| **Codex CLI** (`codex`) | `0.154.0` | `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra` | **Architecture & System Planning**: Second opinion on plans and specifications alongside Claude. |
| **Antigravity CLI** (`agy`) | `1.2.2` / `1.2.3` | Gemini 3.8 Flash (High) | **Coding, Refactoring & Implementation**: Primary coding partner for multi-file pair-programming, security remediation, bash/Python/QML engineering, and git release workflow. |
| **OpenCode** (`opencode`) | `1.18.30` | Big Pickle | **Distro & System Q&A**: Efficient lookups for Arch Linux / Omarchy package specifics and shell configuration, conserving frontier-model token budgets. |
| **Grok CLI** (`grok`) | `1.0.25` (`f7e67d6988e2`, stable) | Grok 4.6 | **Workstation Support**: Additional debugging, hardware diagnostics, and alternative implementation analysis. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Initial Implementation** | `v1.0.0` | Claude & Antigravity | Cloned stock `omarchy.workspaces`, added dynamic visual indicators and multi-monitor desktop switching. |
| **In-Place Replacement** | `v1.1.0` | Claude & Antigravity | Stamped `omarchy.clonedFrom: "omarchy.workspaces"` to preserve relative layout anchors (`findRelativeBarLocation`) and enable clean in-place replacement. |
| **Security Hardening** | `v1.2.0` | Antigravity (Gemini) | Sanitized process execution, eliminated arbitrary code execution in configuration parsing, and implemented atomic JSON state writes. |
| **Marketplace Verification** | `v1.2.1` | Antigravity (Gemini) | Successfully verified and listed on the official [Omarchy Plugin Marketplace](https://github.com/omacom/omarchy-plugin-marketplace) with an automated security baseline rating of **Passed**. |
| **Dynamic Monitor Sets** | `v1.3.0` | Codex CLI `0.154.0` (`gpt-5.6-sol`) | Replaced hard-coded monitor pairs with runtime-sized all-monitor Windows sets; added complete-set bar state, verified batch dispatch, and 1/2/3/4-monitor tests. |
| **Center Monitor Sync & Atomic Watch Fix** | `v1.3.1` | Antigravity CLI `1.2.3` (Gemini 3.8 Flash (High)) | Fixed active workspace indicator desync on center monitor by enabling `atomicWrites: true` on `FileView` watchers, fixing monitor coordinate probing in fallback routines, and binding workspace list updates to window revision. |
| **Hardware Resilience & Fault Tolerance** | `v1.4.0` *(Unreleased)* | Antigravity CLI `1.2.3` (Gemini 3.8 Flash (High)) | Solved multi-monitor hardware drops: anchored workspaces to fixed physical slots ($K=3$), graceful parking without workspace re-indexing, automatic geometric gap compression to prevent mouse traps, resilient two-stage switching, and debounced hotplug recovery. |
| **Stale Bar State, Cached Plugin Code & Duplicate Helper** | `v1.4.1` *(Unreleased)* | Claude Code `2.1.273` (Claude Opus 5) | Bars now reload the state files on change instead of re-parsing cached text; hotplug `reconcile` fixed (`HyprlandIpcEvent.name`); `topology_size` config honored. Found that Quickshell's in-memory and on-disk QML caches (Nix store mtime = 1970) had kept v1.3.0 running through two deploys, and that the Super+N bindings used a stale second helper — both fixed on the workstation side (`omarchy-qmlcache-purge`, single helper). |

Detailed session logs and prompts are documented in [`docs/ai/sessions.md`](docs/ai/sessions.md). The public v1.3.0 design and acceptance contract are in [`docs/plans/monitor-set-windows-mode.md`](docs/plans/monitor-set-windows-mode.md).
