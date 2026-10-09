# AI Collaboration Session Archive: `tamlinux`

Individual session records documenting prompt history, tools, models, and key
architectural decisions for Tamlinux. One file per session; there is no
monolithic `sessions.md` here, matching `plugin-fred-tamlinux`.

Tool and model versions are verified against local transcript stores. An entry
whose attribution has not been checked against a local transcript says so
explicitly.

## Delegated work

Tasks one AI agent assigned to another, with the harness and model on each
side and any rework: [`delegations.md`](delegations.md).

## Session Records

| Date | Topic | Primary Tool | Model | Session Document |
| :-- | :-- | :-- | :-- | :-- |
| 2026-10-09 | tam-deploy and tam-plugin 3.0.0 deploy packaged assemblies | Claude Code `2.1.295` | `claude-opus-5-5` | [Session](2026-10-09-tam-deploy.md) |
| 2026-10-09 | Lifecycle tools move into Tamlinux | Claude Code `2.1.295` | `claude-opus-5-5` | [Session](2026-10-09-lifecycle-tools-move.md) |
| 2026-10-09 | `tam-work` moves into Tamlinux | Claude Code `2.1.295` / agy `1.3.2` | `claude-opus-5-5` / `gemini-3.8-flash-high` | [Session](2026-10-09-tam-work.md) |
| 2026-10-09 | 0.4.2 menu ownership and bounded reloads | Codex CLI `0.162.0` | `gpt-6.1-sol` | [Session](2026-10-09-0.4.2-menu.md) |
| 2026-10-09 | Deployment state and current plan review | Codex CLI `0.162.0` | `gpt-6.1-sol` | [Session](2026-10-09-status-review.md) |
| 2026-10-09 | Plugin suite consolidation into Tamlinux | OpenCode `1.18.35` / agy `1.2.16` | `big-pickle` / `gemini-3.8-flash-high` | [`2026-10-09-plugins-consolidation.md`](2026-10-09-plugins-consolidation.md) |
| 2026-10-09 | Public package-delivery ownership | Codex CLI `0.162.0` | `gpt-6.1-sol` | [2026-10-09-package-ownership.md](2026-10-09-package-ownership.md) |
| 2026-10-09 | Daily compositor protocol shadow monitoring | Codex CLI `0.162.0` | `gpt-6.1-sol` | [2026-10-09-protocol-shadow.md](2026-10-09-protocol-shadow.md) |
| 2026-10-08 | 0.4.0 login, normal Run and tested acceptance | Codex CLI `0.162.0` | `gpt-6.1-sol` | [2026-10-08-0.4.0-acceptance.md](2026-10-08-0.4.0-acceptance.md) |
| 2026-10-08 | Shared compositor protocol layer, milestone A | Codex CLI `0.161.0` | `gpt-6.1-sol` | [2026-10-08-protocol-layer-development.md](2026-10-08-protocol-layer-development.md) |
| 2026-10-08 | Compositor protocol layer and base-plan additions | Claude Code `2.1.294` | `claude-opus-5-5` | [`2026-10-08-compositor-protocol-layer.md`](2026-10-08-compositor-protocol-layer.md) |
| 2026-10-07 | Independence-first replanning | Codex CLI `0.161.0` | `gpt-6.1-sol` | [2026-10-07-independence-first-replanning.md](2026-10-07-independence-first-replanning.md) |
| 2026-10-06 | Monitor power re-read | Claude Code `2.1.292` | `claude-opus-5-5` | [`2026-10-06-dpms-reread.md`](2026-10-06-dpms-reread.md) |
| 2026-10-06 | 0.3.3 cutover: the daily bar | Claude Code `2.1.292` | `claude-opus-5-5` | [`2026-10-06-0.3.3-cutover.md`](2026-10-06-0.3.3-cutover.md) |
| 2026-10-06 | Complete 0.3.2 readiness | Codex CLI `0.160.1` | `gpt-6.1-sol` | [2026-10-06-0.3.2-completion.md](2026-10-06-0.3.2-completion.md) |
| 2026-10-06 | Independent, continuing Tamlinux identity | Codex CLI `0.160.1` | `gpt-6.1-sol` | [2026-10-06-independent-continuing-project.md](2026-10-06-independent-continuing-project.md) |
| 2026-10-06 | The proof launcher addresses its own instance | Claude Code `2.1.291` | `claude-opus-5-5` | [`2026-10-06-proof-ipc-by-pid.md`](2026-10-06-proof-ipc-by-pid.md) |
| 2026-10-05 | Bar widget ports merged; provenance for delegated work | Claude Code `2.1.290` | `claude-opus-5-5` | [`2026-10-05-delegation-provenance.md`](2026-10-05-delegation-provenance.md) |
| 2026-10-05 | Shared theme and typography integration (Develop) | Codex CLI `0.160.1` | `gpt-6.1-sol` | [2026-10-05-style-theme-integration.md](2026-10-05-style-theme-integration.md) |
| 2026-10-05 | Omarchy's packages frozen (0.2.0) | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-05-freeze-omarchy-packages.md`](2026-10-05-freeze-omarchy-packages.md) |
| 2026-10-05 | Every accepted step is a version | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-05-version-keyed-plan.md`](2026-10-05-version-keyed-plan.md) |
| 2026-10-04 | Notifications service in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-notifications-service.md`](2026-10-04-notifications-service.md) |
| 2026-10-04 | OSD service in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-osd-service.md`](2026-10-04-osd-service.md) |
| 2026-10-04 | Clipboard service in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-clipboard-service.md`](2026-10-04-clipboard-service.md) |
| 2026-10-04 | Reminders in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-reminders.md`](2026-10-04-reminders.md) |
| 2026-10-04 | Milestones before 0.1 | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-milestones-before-0.1.md`](2026-10-04-milestones-before-0.1.md) |
| 2026-10-04 | Battery warning in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-battery.md`](2026-10-04-battery.md) |
| 2026-10-04 | Stay Awake in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-idle.md`](2026-10-04-idle.md) |
| 2026-10-04 | Media keys in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-media.md`](2026-10-04-media.md) |
| 2026-10-04 | Polkit agent in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-polkit.md`](2026-10-04-polkit.md) |
| 2026-10-04 | Desktop background in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-background.md`](2026-10-04-background.md) |
| 2026-10-04 | Command menu in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-menu.md`](2026-10-04-menu.md) |
| 2026-10-04 | Image picker in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-image-picker.md`](2026-10-04-image-picker.md) |
| 2026-10-04 | Emoji picker in the host | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-emoji-picker.md`](2026-10-04-emoji-picker.md) |
| 2026-10-04 | Omarchy removed before Hyprland (0.3) | Claude Code `2.1.289` | `claude-opus-5-5` | [`2026-10-04-omarchy-before-hyprland.md`](2026-10-04-omarchy-before-hyprland.md) |
| 2026-10-04 | Sway adapter, first slice | Cursor `3.23.12` | `composer` | [`2026-10-04-sway-adapter.md`](2026-10-04-sway-adapter.md) |
| 2026-10-03 | Helper Hyprland commands use the named backend | Cursor `3.23.12` | `composer` | [`2026-10-03-hyprland-command-ownership.md`](2026-10-03-hyprland-command-ownership.md) |
| 2026-10-03 | Plugin QML reads the compositor facade | Cursor `3.23.12` | `composer` | [`2026-10-03-compositor-facade.md`](2026-10-03-compositor-facade.md) |
| 2026-10-03 | Shell-independent 2.0.0 | Cursor `3.23.12` | `composer` | [`2026-10-03-shell-independent-2.0.0.md`](2026-10-03-shell-independent-2.0.0.md) |
| 2026-10-03 | Shared UI closure and typed actions | Cursor `3.23.12` | `composer` | [`2026-10-03-shared-ui-closure.md`](2026-10-03-shared-ui-closure.md) |
| 2026-10-03 | Workstation package route and version series | Claude Code `2.1.288` | `claude-opus-5-5` | [`2026-10-03-workstation-package-route-and-versions.md`](2026-10-03-workstation-package-route-and-versions.md) |
| 2026-10-03 | Compositor contract and Hyprland adapter | Cursor `3.23.12` | `composer` | [`2026-10-03-compositor-contract.md`](2026-10-03-compositor-contract.md) |
| 2026-10-03 | Void-first target base and repository alignment | Codex CLI `0.160.0` | `gpt-6.1-sol` | [2026-10-03-void-first-target-base.md](2026-10-03-void-first-target-base.md)
| 2026-10-03 | runit for system initialization and service management | Antigravity CLI (`agy`) `1.2.16` | `gemini-3.8-flash-high` | [`2026-10-03-runit-system-initialization-and-service-management.md`](2026-10-03-runit-system-initialization-and-service-management.md) |
| 2026-10-03 | Shell host contract for the other plugins | Cursor `3.21.18` | `composer` | [`2026-10-03-shell-host-contract.md`](2026-10-03-shell-host-contract.md) |
| 2026-10-03 | Independent clock shell proof | Cursor `3.21.18` | `composer` | [`2026-10-03-independent-clock-shell.md`](2026-10-03-independent-clock-shell.md) |
| 2026-10-03 | Hardware floor, open compositor, and workstation requirements | Claude Code `2.1.288` | `claude-opus-5-5` | [`2026-10-03-hardware-floor-and-workstation-requirements.md`](2026-10-03-hardware-floor-and-workstation-requirements.md) |
| 2026-10-03 | Desktop dependency inventory and agy handoff | Codex CLI `0.160.0` | `gpt-6.1-sol` | [`2026-10-03-desktop-dependency-inventory-and-handoff.md`](2026-10-03-desktop-dependency-inventory-and-handoff.md) |
| 2026-09-22 | Public explainer and suite branding | Cursor `3.21.16` | composer | [`2026-09-22-public-explainer.md`](2026-09-22-public-explainer.md) |
| 2026-09-22 | Product version 0.0.1 | Cursor `3.21.16` | composer | [`2026-09-22-version-0.0.1.md`](2026-09-22-version-0.0.1.md) |
| 2026-09-23 | Installation and `tamlinux` command plans | Codex CLI `0.156.1` | `gpt-6-sol` | [`2026-09-23-installation-and-command-plans.md`](2026-09-23-installation-and-command-plans.md) |
| 2026-09-28 | AntiX base layer, Arch rolling updates, and product vision | Antigravity CLI (`agy`) `1.2.12` | Gemini 3.8 Flash (High) | [`2026-09-28-antix-base-and-product-vision.md`](2026-09-28-antix-base-and-product-vision.md) |

## Related

- [`../../AI_PROVENANCE.md`](../../AI_PROVENANCE.md) — toolchain and milestone table.

## 2026-09-23 upstream survey foundation

- [Codex session record](2026-09-23-upstream-survey-foundation.md).

## 2026-09-28 private session IDs

- [Claude Code session record](2026-09-28-private-session-ids.md).

## 2026-09-28 provenance audit and publish

- [Claude Code session record](2026-09-28-provenance-audit-and-publish.md).
