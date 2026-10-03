# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the
AI tools, models, prompts, and architectural decisions that shaped Tamlinux's
public description and development plans.

---

## How to read this record

This repository follows the Tamlinux [AI provenance standard](docs/ai-provenance-standard.md). In
brief: commits made with AI help carry `AI-Tool` and `AI-Model` trailers, and
each session record in [`docs/ai/`](docs/ai/) gives the date, tool version,
model, Fred's guiding prompts verbatim, the commits, and the decisions. Session
transcripts are retained privately by the author, so the records carry no
session IDs or local transcript paths.

---

## 1. Fred's Multi-Agent AI Toolchain

Rather than relying on a single AI model or interface, Fred uses a specialized
toolchain tailored to each tool's strengths. Most CLI versions below were
captured on 2026-09-22 (`<tool> --version` / `cursor --version`); the Codex
version was checked again for the 2026-09-23 planning session, the Antigravity
CLI version was updated to `1.2.12` on 2026-09-28 and `1.2.16` on 2026-10-03.

Codex CLI was checked again as `0.160.0` for the 2026-10-03 dependency planning
session, using the logged model `gpt-6.1-sol`. Cursor was checked as `3.21.18`
for the 2026-10-03 clock-shell candidate.

| Tool & Interface | CLI Version | Backing Models | Primary Role in the Ecosystem |
| :-- | :-- | :-- | :-- |
| **Void-first target base** | 0.0.1 planning | Codex CLI `0.160.0` (`gpt-6.1-sol`) | Void first, antiX Core if Void has a showstopper; runit/Sway retained, Btrfs pilot, libc and native packaging evaluation. Active documents rewritten directly. [Session record](docs/ai/2026-10-03-void-first-target-base.md). |
| **Claude Code** (`claude`) | `2.1.280` | Claude Opus 5 (`claude-opus-5`) | **Architecture & System Planning**: Authoring durable system specifications, multi-step runbooks, and cross-cutting policies. |
| **Codex CLI** (`codex`) | `0.160.0` | `gpt-6.1-sol`; earlier sessions: `gpt-6-astra`, `gpt-6-sol`, `gpt-5.6-sol` | **Architecture & System Planning**: Second opinion on plans and specifications alongside Claude. |
| **Antigravity CLI** (`agy`) | `1.2.16` | Gemini 3.8 Flash (High) | **Coding, Refactoring & Implementation**: Primary coding partner for multi-file pair-programming, security hardening, and git release workflow. |
| **Cursor** (`cursor`) | `3.21.16` | composer | **Implementation in this repository**: public explainer, suite branding, and 0.0.1 versioning. |
| **OpenCode** (`opencode`) | `1.18.31` | Big Pickle | **Distro & System Q&A**: Efficient lookups for Arch Linux package specifics and shell configuration. |
| **Grok CLI** (`grok`) | `1.0.25` | Grok 4.6 | **Workstation Support**: Additional debugging and hardware diagnostics. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **runit for init and service management** | 0.0.1 planning | Antigravity CLI (`agy`) `1.2.16` (`gemini-3.8-flash-high`) | Recorded Fred's decision to use runit for system initialization (PID 1) and service supervision on Suspra Workstations, aligning with antiX Linux Core's default runit base. Documentation only. [Session record](docs/ai/2026-10-03-runit-system-initialization-and-service-management.md). |
| **Shell host contract** | 0.0.1 Develop candidate | Cursor `3.21.18` (`composer`) | The clock host now covers the other plugins' bar and shell calls: per-output popouts, settings, manifests, tooltips, panel focus, and IPC. A fixture widget proves the contract. The other seven plugins are not loaded. Not a Test promotion. [Session record](docs/ai/2026-10-03-shell-host-contract.md). |
| **Independent clock shell** | 0.0.1 Develop candidate | Cursor `3.21.18` (`composer`) | Separate Quickshell host loads pinned `fred.clock` through owned modules and isolated fixture data. Automated checks passed; manual hover and output checks remain. Not a Test promotion. [Session record](docs/ai/2026-10-03-independent-clock-shell.md). |
| **Hardware floor and workstation requirements** | 0.0.1 planning; local draft | Claude Code `2.1.288` (`claude-opus-5-5`) | Recorded Fred's circa-2006 hardware floor (Wayland, not X11), antiX Core with an Omarchy-inspired tiling window system and the compositor reopened, and the Chrome, VS Code, and terminal-first requirements; then ran Fred's compositor field survey and recorded his decisions: Sway, a Nix-built workstation package on antiX Core or existing Linux, and terminal-only machines. Documentation only. [Session record](docs/ai/2026-10-03-hardware-floor-and-workstation-requirements.md). |
| **Desktop dependency inventory and handoff** | 0.0.1 planning; approved 2026-10-03 | Codex CLI `0.160.0` (`gpt-6.1-sol`) | Classified desktop dependencies; ordered the shell/compositor/session/pilot work and specified the independent clock proof. No desktop implementation or migration. [Session record](docs/ai/2026-10-03-desktop-dependency-inventory-and-handoff.md). |
| **Public explainer (first version)** | first description | Cursor `3.21.16` (`composer`) | Public one-liner, etymology, values, plugin-suite links, GPL-3.0-or-later. Not an installable image. [Session record](docs/ai/2026-09-22-public-explainer.md). |
| **Product version 0.0.1** | 0.0.1 | Cursor `3.21.16` (`composer`) | First Tamlinux version. 0.x is Omarchy-based; 1.x is independent. Home Manager generation is recorded separately. [Session record](docs/ai/2026-09-22-version-0.0.1.md). |
| **Installation and command plans** | 0.0.1 planning | Codex CLI `0.156.1` (`gpt-6-sol`), with Fred's direct edits and review | Omarchy first installation profile; NixOS pilot next; approved first `tamlinux` command slice, first-use welcome, and Lynx fallback. No installer or command implementation yet. [Session record](docs/ai/2026-09-23-installation-and-command-plans.md). |
| **AntiX base layer & Suspra vision** | 0.0.1 refinement | Antigravity CLI (`agy`) `1.2.12`, Gemini 3.8 Flash (High) | Clarified Arch rolling update appeal, AntiX older hardware commitment, universal resource minimization, AntiX Core + River target base layer, and graduation into Suspra Linux / Tier 3 Suspra Workstation. [Session record](docs/ai/2026-09-28-antix-base-and-suspra-vision.md). |

Detailed session records are indexed in [`docs/ai/README.md`](docs/ai/README.md).

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

## 2026-09-28 provenance audit and publish

Claude Code `2.1.284` (`claude-sonnet-5-5`) audited every public repository's
AI records against the public provenance standard, redacted one private
repository name from a quoted prompt, and published the pending Antigravity
session record. Documentation only.
[Session record](docs/ai/2026-09-28-provenance-audit-and-publish.md).
