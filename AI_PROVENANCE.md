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
for the 2026-10-03 clock-shell candidate, and as `3.23.12` for the compositor
contract, the shared UI slice, the plugin facade reads the same day, and the
Sway adapter on 2026-10-04. Claude Code was checked as `2.1.288` (`claude-opus-5-5`)
for the 2026-10-03 workstation-package route, and as `2.1.289` for the
2026-10-04 milestone change that removes Omarchy before Hyprland.

| Tool & Interface | CLI Version | Backing Models | Primary Role in the Ecosystem |
| :-- | :-- | :-- | :-- |
| **Void-first target base** | 0.0.1 planning | Codex CLI `0.160.0` (`gpt-6.1-sol`) | Void first, antiX Core if Void has a showstopper; runit/Sway retained, Btrfs pilot, libc and native packaging evaluation. Active documents rewritten directly. [Session record](docs/ai/2026-10-03-void-first-target-base.md). |
| **Claude Code** (`claude`) | `2.1.289` | Claude Opus 5.5 (`claude-opus-5-5`); earlier: Claude Opus 5 (`claude-opus-5`) | **Architecture & System Planning**: Authoring durable system specifications, multi-step runbooks, and cross-cutting policies. |
| **Codex CLI** (`codex`) | `0.160.0` | `gpt-6.1-sol`; earlier sessions: `gpt-6-astra`, `gpt-6-sol`, `gpt-5.6-sol` | **Architecture & System Planning**: Second opinion on plans and specifications alongside Claude. |
| **Antigravity CLI** (`agy`) | `1.2.16` | Gemini 3.8 Flash (High) | **Coding, Refactoring & Implementation**: Primary coding partner for multi-file pair-programming, security hardening, and git release workflow. |
| **Cursor** (`cursor`) | `3.21.16` | composer | **Implementation in this repository**: public explainer, suite branding, and 0.0.1 versioning. |
| **OpenCode** (`opencode`) | `1.18.31` | Big Pickle | **Distro & System Q&A**: Efficient lookups for Arch Linux package specifics and shell configuration. |
| **Grok CLI** (`grok`) | `1.0.25` | Grok 4.6 | **Workstation Support**: Additional debugging and hardware diagnostics. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Notifications service in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The host gained session services (`TAMLINUX_SERVICES`) and a bar-less mode (`TAMLINUX_BAR=0`). The notification service is vendored with its MIT notice and owns `org.freedesktop.Notifications`; focus-on-click uses a new `focusApp` facade operation on both adapters. [Session record](docs/ai/2026-10-04-notifications-service.md) |
| **OSD service in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The on-screen display (volume, brightness, and status overlays) is vendored into the host as a second session service with its MIT notice. It runs beside the notifications in services-only mode. [Session record](docs/ai/2026-10-04-osd-service.md) |
| **Clipboard service in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | Clipboard history, its two `wl-paste` watchers, and the full-screen picker are vendored into the host as a third session service with the MIT notice. The paste and open helpers ship beside the service, so the host calls nothing outside its own tree. [Session record](docs/ai/2026-10-04-clipboard-service.md) |
| **Emoji picker in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The emoji picker, its search, its emoji list, and its insert helper are vendored into the host as a fourth session service with the MIT notice. [Session record](docs/ai/2026-10-04-emoji-picker.md) |
| **Image picker in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The full-screen image carousel, its row model, and its list helper are vendored into the host as a fifth session service with the MIT notice. Answer and done files are now written by argument rather than as shell text. [Session record](docs/ai/2026-10-04-image-picker.md) |
| **Omarchy removed before Hyprland** | 0.0.1 planning | Claude Code `2.1.289` (`claude-opus-5-5`) | Recorded Fred's change of order: 0.3 now means Omarchy is gone while Hyprland stays (functions replaced; packages, package mirror and kernel removed; Tamlinux's own name and look), 0.4–0.9 fall back to Hyprland, and 1.0.0 removes Hyprland. Fred chose Arch's stock kernel after a comparison. Documentation only. [Session record](docs/ai/2026-10-04-omarchy-before-hyprland.md). |
| **Sway adapter, first slice** | 0.0.1 Develop candidate | Cursor `3.23.12` (`composer`) | The shell Sway adapter prefers ext-workspace workspaces, then i3 IPC, and reads bindings from a generated fragment. It loads only when selected. The Hyprland proof stays the default. No `swaymsg` process is started. The daily bar is unchanged. Not a Test promotion. [Session record](docs/ai/2026-10-04-sway-adapter.md). |
| **Helper Hyprland commands use the named backend** | 0.0.1 Develop candidate | Cursor `3.23.12` (`composer`) | Workspace and monitor helpers call named compositor operations. Reads run. Mutations record unless the live flag is set. The daily bar is unchanged. Not a Test promotion. [Session record](docs/ai/2026-10-03-hyprland-command-ownership.md). |
| **Plugin QML reads the compositor facade** | 0.0.1 Develop candidate | Cursor `3.23.12` (`composer`) | Weather, tides, sysinfo, keyboard, monitor DPMS, and workspaces QML read `bar.compositor`. Output snapshots include a bounded description. `tam-desktop-mode` and the monitor layout helpers still call Hyprland. The daily bar is unchanged. Not a Test promotion. [Session record](docs/ai/2026-10-03-compositor-facade.md). |
| **Shared UI closure and typed actions** | 0.0.1 Develop candidate | Cursor `3.23.12` (`composer`) | The proof host now has the border, style, and control types the plugins bind, plus typed actions that record a request and do not start a process. `bar.run` stays refused. A fixture proves the types. The eight plugins are not rewritten, and the daily bar is unchanged. Not a Test promotion. [Session record](docs/ai/2026-10-03-shared-ui-closure.md). |
| **Workstation package route and version series** | 0.0.1 planning | Claude Code `2.1.288` (`claude-opus-5-5`) | Recorded Fred's route: the workstation package installs on existing distributions first (Nix flake + host adapter), Fred's Arch workstation reaches 1.0.0 when Omarchy and Hyprland are removed, then a second distribution and the Void base (native `xbps-src`). Set the 0.0.x–1.3 version series and renumbered the desktop milestones. Documentation only. [Session record](docs/ai/2026-10-03-workstation-package-route-and-versions.md). |
| **Compositor contract and Hyprland adapter** | 0.0.1 Develop candidate | Cursor `3.23.12` (`composer`) | Shell UI in `desktop/` reads a compositor facade. The Hyprland adapter is the only new file that imports Hyprland or starts hyprctl. Focus and DPMS stay record-only in the proof. The seven plugins are unchanged. Not a Test promotion. [Session record](docs/ai/2026-10-03-compositor-contract.md). |
| **runit for init and service management** | 0.0.1 planning | Antigravity CLI (`agy`) `1.2.16` (`gemini-3.8-flash-high`) | Recorded Fred's decision to use runit for system initialization (PID 1) and service supervision on the target workstation, aligning with antiX Linux Core's default runit base. Documentation only. [Session record](docs/ai/2026-10-03-runit-system-initialization-and-service-management.md). |
| **Shell host contract** | 0.0.1 Develop candidate | Cursor `3.21.18` (`composer`) | The clock host now covers the other plugins' bar and shell calls: per-output popouts, settings, manifests, tooltips, panel focus, and IPC. A fixture widget proves the contract. The other seven plugins are not loaded. Not a Test promotion. [Session record](docs/ai/2026-10-03-shell-host-contract.md). |
| **Independent clock shell** | 0.0.1 Develop candidate | Cursor `3.21.18` (`composer`) | Separate Quickshell host loads pinned `fred.clock` through owned modules and isolated fixture data. Automated checks passed; manual hover and output checks remain. Not a Test promotion. [Session record](docs/ai/2026-10-03-independent-clock-shell.md). |
| **Hardware floor and workstation requirements** | 0.0.1 planning; local draft | Claude Code `2.1.288` (`claude-opus-5-5`) | Recorded Fred's circa-2006 hardware floor (Wayland, not X11), antiX Core with an Omarchy-inspired tiling window system and the compositor reopened, and the Chrome, VS Code, and terminal-first requirements; then ran Fred's compositor field survey and recorded his decisions: Sway, a Nix-built workstation package on antiX Core or existing Linux, and terminal-only machines. Documentation only. [Session record](docs/ai/2026-10-03-hardware-floor-and-workstation-requirements.md). |
| **Desktop dependency inventory and handoff** | 0.0.1 planning; approved 2026-10-03 | Codex CLI `0.160.0` (`gpt-6.1-sol`) | Classified desktop dependencies; ordered the shell/compositor/session/pilot work and specified the independent clock proof. No desktop implementation or migration. [Session record](docs/ai/2026-10-03-desktop-dependency-inventory-and-handoff.md). |
| **Public explainer (first version)** | first description | Cursor `3.21.16` (`composer`) | Public one-liner, etymology, values, plugin-suite links, GPL-3.0-or-later. Not an installable image. [Session record](docs/ai/2026-09-22-public-explainer.md). |
| **Product version 0.0.1** | 0.0.1 | Cursor `3.21.16` (`composer`) | First Tamlinux version. 0.x is Omarchy-based; 1.x is independent. Home Manager generation is recorded separately. [Session record](docs/ai/2026-09-22-version-0.0.1.md). |
| **Installation and command plans** | 0.0.1 planning | Codex CLI `0.156.1` (`gpt-6-sol`), with Fred's direct edits and review | Omarchy first installation profile; NixOS pilot next; approved first `tamlinux` command slice, first-use welcome, and Lynx fallback. No installer or command implementation yet. [Session record](docs/ai/2026-09-23-installation-and-command-plans.md). |
| **AntiX base layer & product vision** | 0.0.1 refinement | Antigravity CLI (`agy`) `1.2.12`, Gemini 3.8 Flash (High) | Clarified Arch rolling update appeal, AntiX older hardware commitment, universal resource minimization, AntiX Core + River target base layer, and a temporary-testbed graduation path. [Session record](docs/ai/2026-09-28-antix-base-and-product-vision.md). |

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

## 2026-10-03 shell-independent plugins

Cursor `3.23.12` (`composer`) taught the proof host to load the eight
`fred.*` 2.0.0 checkouts and to start typed actions only when that flag is
set. The daily shell was not replaced. Product version stays 0.0.1.
[Session record](docs/ai/2026-10-03-shell-independent-2.0.0.md).
