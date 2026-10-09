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

Some work is delegated: one agent assigns a task and another does it. The
delegate's commit names its own harness and model, plus `AI-Role: delegate`
and `AI-Assigned-By:` for the orchestrator; a commit that corrects or redoes
delegated work carries `AI-Reworks:`. [`docs/ai/delegations.md`](docs/ai/delegations.md)
lists every delegated task, who assigned it, who did it, and whether it had to
be redone.

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
| **0.4.1 package** | 0.4.1 Test candidate | Claude Code `2.1.295` (`claude-opus-5-5`) | The accepted 0.4.1 shell with its accepted plugin payloads and the product commands, packaged for deployment through `tamlinux-packages`; plugin digests equal the acceptance record. [Session](docs/ai/2026-10-09-0.4.1-package.md). |
| **Void-first target base** | 0.0.1 planning | Codex CLI `0.160.0` (`gpt-6.1-sol`) | Void first, antiX Core if Void has a showstopper; runit/Sway retained, Btrfs pilot, libc and native packaging evaluation. Active documents rewritten directly. [Session record](docs/ai/2026-10-03-void-first-target-base.md). |
| **Claude Code** (`claude`) | `2.1.289` | Claude Opus 5.5 (`claude-opus-5-5`); earlier: Claude Opus 5 (`claude-opus-5`) | **Architecture & System Planning**: Authoring durable system specifications, multi-step runbooks, and cross-cutting policies. |
| **Codex CLI** (`codex`) | `0.162.0` (verified 2026-10-08) | `gpt-6.1-sol`; earlier sessions: `gpt-6-astra`, `gpt-6-sol`, `gpt-5.6-sol` | **Architecture & System Planning**: Second opinion on plans and specifications alongside Claude; protocol-layer implementation and workstation migration verification. |
| **Antigravity CLI** (`agy`) | `1.2.16` | Gemini 3.8 Flash (High) | **Coding, Refactoring & Implementation**: Primary coding partner for multi-file pair-programming, security hardening, and git release workflow. |
| **Cursor** (`cursor`) | `3.21.16` | composer | **Implementation in this repository**: public explainer, suite branding, and 0.0.1 versioning. |
| **OpenCode** (`opencode`) | `1.18.31` | Big Pickle | **Distro & System Q&A**: Efficient lookups for Arch Linux package specifics and shell configuration. |
| **Grok CLI** (`grok`) | `1.0.25` | Grok 4.6 | **Workstation Support**: Additional debugging and hardware diagnostics. |

---

## 2. Key Architectural Milestones & AI Role

2026-10-09: current plan and shadow Test state reviewed, followed by a
`fred.monitor` 2.0.3 runtime-permission regression repair and Fred's 0.4.1
acceptance, with Codex CLI
`0.162.0`, model `gpt-6.1-sol`; see the [session record](docs/ai/2026-10-09-status-review.md).

2026-10-09: public package-delivery ownership was aligned with the four-repository
split using Codex CLI `0.162.0`, model `gpt-6.1-sol`; see the
[session record](docs/ai/2026-10-09-package-ownership.md).

Rows retain the decisions and proposed schedules at the time of each session.
The 2026-10-07 replanning row and [current versioning](VERSIONING.md) supersede
earlier future-stage schedules without changing accepted version identifiers.

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Packaged deployment tools** | Development (no version change) | Claude Code `2.1.295` (`claude-opus-5-5`) | `tam-deploy` replaces `tam-shell-deploy`: Test pins and verifies a `tamlinux-packages` assembly, Run fast-forwards `main` without rebuilding; `tam-plugin` 3.0.0 reads sources from `desktop/plugins` and leaves Test and Run to `tam-deploy`. 20 tests plus the lifecycle suite, passing in the Nix build. [Session](docs/ai/2026-10-09-tam-deploy.md). |
| **Lifecycle tools in Tamlinux** | Development (no version change) | Claude Code `2.1.295` (`claude-opus-5-5`) | `tam-shell-deploy` and `tam-plugin` become components under `commands/`; Home Manager configuration name and configuration checkout made configurable; 14 and seams tests pass. [Session](docs/ai/2026-10-09-lifecycle-tools-move.md). |
| **`tam-work` in Tamlinux** | Development (no version change) | Claude Code `2.1.295` (`claude-opus-5-5`); agy `1.3.2` (`gemini-3.8-flash-high`, delegate T31) | The shared-checkout claim command becomes the product component `commands/tam-work/` with configurable workspace and registry; 38 tests; inherited test-isolation fault fixed. [Session](docs/ai/2026-10-09-tam-work.md). |
| **Bounded owned menus** | 0.4.2 Develop | Codex CLI `0.162.0` (`gpt-6.1-sol`) | Product defaults/entry point, bounded JSONC and file reads, retained valid source/model on reload failure, and isolated service proof. [Session](docs/ai/2026-10-09-0.4.2-menu.md). |
| **Daily compositor protocol shadow monitoring** | 0.4.1 daily shadow Test | Codex CLI `0.162.0` (`gpt-6.1-sol`) | Bounded read-only comparisons and minute heartbeats; durable journal archive, source identity and conservative time/event summary. 409 desktop and 494 configuration tests passed; isolated equality on three outputs/four workspaces. Daily Test deployed, agreeing records archived and 161 daily checks passed; accepted version remains 0.4.0. [Session record](docs/ai/2026-10-09-protocol-shadow.md). |
| **Non-theme settings/state ownership** | 0.4.0 accepted | Codex CLI `0.161.0` (implementation), `0.162.0` (login/Run verification and acceptance record), `gpt-6.1-sol` | Matching storage consumers and one key/bar helper; data-preserving migration/rollback. Exact eight normal Run digests verified, physical login and 494 configuration tests passed. Fred explicitly accepted the tested desktop; version/status metadata updated. [Session record](docs/ai/2026-10-08-0.4.0-acceptance.md). |
| **Independence-first replanning** | 0.3.3 unchanged; reviewed planning | Codex CLI `0.161.0` (`gpt-6.1-sol`) | Settings/state and menus 0.4, theme/fonts/branding 0.5, package/system ownership and boot-dependent removal 0.6. Independent Hyprland acceptance before Sway integration/package 0.7 and physical daily proof 0.8. No implementation or deployment. [Session record](docs/ai/2026-10-07-independence-first-replanning.md). |
| **Shared compositor protocol layer, milestone A** | 0.3.3 unchanged; Develop | Codex CLI `0.161.0` (`gpt-6.1-sol`) | Bound protocol state and shared adapter composition; 398 desktop tests and Sway fixture proof passed. Isolated Hyprland proof matched three outputs and four workspaces. No deployment. [Session record](docs/ai/2026-10-08-protocol-layer-development.md). |
| **Cutover** | 0.3.3 | Claude Code `2.1.292` (`claude-opus-5-5`) | The Tamlinux shell becomes the daily bar on all three screens; rollback covers live-linked files as well as the generation; the bar's exclusive zone fixed at the switch. [Session record](docs/ai/2026-10-06-0.3.3-cutover.md). |
| **Daily-bar readiness** | 0.3.2 | Codex CLI `0.160.1` (`gpt-6.1-sol`), continuing Claude's committed work | Multi-screen routes and controls, conversion and failed-plugin proof checks, immutable shell/plugin deployments, and recoverable local lifecycle transitions. [Session record](docs/ai/2026-10-06-0.3.2-completion.md). |
| **Every accepted step is a version** | 0.1.22 | Claude Code `2.1.289` (`claude-opus-5-5`) | Recorded Fred's scheme: the minor version is a stage and the patch a step, so every accepted step raises the version. Steps since 0.0.2 numbered 0.1.0–0.1.22 in acceptance order; stages re-planned (0.2 every key binding on owned commands, 0.3 bar, 0.4 compositor contract, 0.5 look, 0.6 removal, 0.7 package, 0.8 Sway daily). Session: [`docs/ai/2026-10-05-version-keyed-plan.md`](docs/ai/2026-10-05-version-keyed-plan.md). |
| **Notifications service in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The host gained session services (`TAMLINUX_SERVICES`) and a bar-less mode (`TAMLINUX_BAR=0`). The notification service is vendored with its MIT notice and owns `org.freedesktop.Notifications`; focus-on-click uses a new `focusApp` facade operation on both adapters. [Session record](docs/ai/2026-10-04-notifications-service.md) |
| **OSD service in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The on-screen display (volume, brightness, and status overlays) is vendored into the host as a second session service with its MIT notice. It runs beside the notifications in services-only mode. [Session record](docs/ai/2026-10-04-osd-service.md) |
| **Clipboard service in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | Clipboard history, its two `wl-paste` watchers, and the full-screen picker are vendored into the host as a third session service with the MIT notice. The paste and open helpers ship beside the service, so the host calls nothing outside its own tree. [Session record](docs/ai/2026-10-04-clipboard-service.md) |
| **Emoji picker in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The emoji picker, its search, its emoji list, and its insert helper are vendored into the host as a fourth session service with the MIT notice. [Session record](docs/ai/2026-10-04-emoji-picker.md) |
| **Image picker in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The full-screen image carousel, its row model, and its list helper are vendored into the host as a fifth session service with the MIT notice. Answer and done files are now written by argument rather than as shell text. [Session record](docs/ai/2026-10-04-image-picker.md) |
| **Reminders in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The reminder card, its minutes model, and its timer helper are vendored into the host as a sixth session service with the MIT notice. The helper sends notifications over D-Bus as typed values and reads minutes as decimal. [Session record](docs/ai/2026-10-04-reminders.md) |
| **Command menu in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The command menu, its model, and the application library behind its Apps list are vendored into the host as a seventh session service with the MIT notice. Menu files are named by environment, actions run in their own scope, and select/input answers are written by argument. [Session record](docs/ai/2026-10-04-menu.md) |
| **Desktop background in the host** | 0.0.1 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The desktop background, its slanted reveal, and its output-move remap are vendored into the host as an eighth session service with the MIT notice. The service now watches its link, so any command that repoints it changes the background, and the desktop double-clicks open the host menu's background and theme routes. [Session record](docs/ai/2026-10-04-background.md) |
| **Polkit agent in the host** | 0.0.2 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The polkit authentication agent and its model are vendored into the host as a ninth session service with the MIT notice. The lid check reads `/proc` itself, the agent registers at a Tamlinux object path, and a read-only IPC target reports whether it is registered. [Session record](docs/ai/2026-10-04-polkit.md) |
| **Media keys in the host** | 0.0.2 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The MPRIS media service and its model are vendored into the host as a tenth session service with the MIT notice. Each media-key action shows its card on the host OSD, which the host injects in place of a shell summon. [Session record](docs/ai/2026-10-04-media.md) |
| **Stay Awake in the host** | 0.0.2 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The idle service and its model are vendored into the host as an eleventh session service with the MIT notice. The Stay Awake file is named by the environment and written by argument, each idle stage is off unless its timeout is set, and screensaver windows are counted from Wayland toplevels in place of compositor events. [Session record](docs/ai/2026-10-04-idle.md) |
| **Battery warning in the host** | 0.0.2 Test candidate | Claude Code `2.1.289` (`claude-opus-5-5`) | The battery service and its model are vendored into the host as a twelfth session service with the MIT notice. It warns once when a draining battery reaches 10% and sets the power profile when the power source changes, through owned commands; a read-only IPC target reports its state. Without a battery it runs nothing. [Session record](docs/ai/2026-10-04-battery.md) |
| **Milestones before 0.1** | 0.0.1 planning | Claude Code `2.1.289` (`claude-opus-5-5`) | Named 0.0.2 (Tamlinux owns the foundation) and 0.0.3 (session services in the Tamlinux host, only the bar left) before 0.1; before 0.1 a patch number marks a milestone. Documentation only. [Session record](docs/ai/2026-10-04-milestones-before-0.1.md) |
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
| **AntiX base layer & product vision** | 0.0.1 refinement | Antigravity CLI (`agy`) `1.2.12`, Gemini 3.8 Flash (High) | Clarified Arch rolling update appeal, AntiX older hardware commitment, universal resource minimization, AntiX Core + River target base layer, and a then-proposed temporary-testbed graduation path (**superseded 2026-10-06**; see [current record](docs/ai/2026-10-06-independent-continuing-project.md)). [Session record](docs/ai/2026-09-28-antix-base-and-product-vision.md). |

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

### Style and fonts — 0.2.1 accepted, 2026-10-05

Codex CLI `0.160.1` (`gpt-6.1-sol`) added palette reloads and responsive
type sizing to the shared shell tokens, reviewed delegated helpers and
completed font-provider routing. Fred tested all four Style controls and
accepted 0.2.1. Automated and live installation checks pass.
[Session record](docs/ai/2026-10-05-style-theme-integration.md).

### Keybinding viewer, night light, audio, Bluetooth, network and power — 0.2.2 to 0.2.6 accepted, 2026-10-05

Claude Code `2.1.290` (`claude-opus-5-5`) wrote the shell's keybinding
service and model, the configuration-reload re-read, and the fixtures; Fred
chose the behaviour (Enter runs the binding; alphabetical order) and tested
and accepted 0.2.2; opencode (`big-pickle`) wrote the model tests, reviewed
and merged by Claude. Claude then ported the night-light commands; Fred
accepted 0.2.3. For 0.2.4, agy (`gemini-3.8-flash-high`) ported the seven
panels from Claude's brief; Claude wrote the panel host and the shared
control additions, reviewed and merged; Fred accepted 0.2.4. Claude wired
the network and Wi-Fi QR panels; Fred accepted 0.2.5. Claude wired the power
and speed-test panels, added the host's summon route, and, at Fred's choice,
let the power panel open without a battery; Fred accepted 0.2.6.
[Session record](docs/ai/2026-10-05-keybinding-viewer.md).

### Proof IPC by PID — 2026-10-06

Claude Code `2.1.291` (`claude-opus-5-5`) made `launch-clock-proof` send IPC to the instance it spawned (`quickshell ipc --pid`), because the session's own Tamlinux shell shares the config directory and was receiving the selftest's calls.
[Session record](docs/ai/2026-10-06-proof-ipc-by-pid.md).

### Plugins on Tamlinux only — 0.3.0 accepted, 2026-10-06

Claude Code `2.1.291` (`claude-opus-5-5`) removed the last Omarchy dependencies from the eight plugins' 2.0.0 candidates and fixed the proof launcher Fred tested them in; Fred accepted 0.3.0.
[Session record](docs/ai/2026-10-06-proof-ipc-by-pid.md).

### The Tamlinux bar's own widgets — 0.3.1 accepted, 2026-10-06

Claude Code `2.1.291` (`claude-opus-5-5`) gave the Tamlinux shell a layout-driven bar with its own menu, indicators, keyboard layout, tray, and panel icons, and fixed the tooltip placement Fred's test found; Fred accepted 0.3.1. agy and opencode wrote test suites for it from Claude's briefs.
[Session record](docs/ai/2026-10-06-tamlinux-bar-widgets.md).

## 2026-10-06 independent, continuing project

Codex CLI `0.160.1` (`gpt-6.1-sol`) reconciled public identity, versioning,
and engineering-plan scope around Fred's independent continuing Tamlinux
direction. Earlier temporary-project and final-1.x assumptions are superseded.
Documentation only. [Session record](docs/ai/2026-10-06-independent-continuing-project.md).

## 2026-10-06 monitor power re-read

Claude Code `2.1.292` (`claude-opus-5-5`) made the Hyprland adapter read
the monitors again on focus changes, output hotplug, and its own DPMS
changes. A monitor blanked by `fred.workspaces` was still reported lit and
could not be woken by pointer entry.
[Session record](docs/ai/2026-10-06-dpms-reread.md).

## 2026-10-09 plugin suite consolidation

OpenCode 1.18.35 (big-pickle) and Antigravity CLI (agy) 1.2.16
(gemini-3.8-flash-high) consolidated the eight independent fred.* plugin
repositories into desktop/plugins/ in the Tamlinux product repository,
preserving git history, branch lines, and namespaced tags. The standalone
repositories are frozen as historical Omarchy 1.x reference.
[Session record](docs/ai/2026-10-09-plugins-consolidation.md).
