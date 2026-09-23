# AI Collaboration Session Archive: `omarchy-fred-workspaces`

Individual session records documenting prompt history, tools, models, and key
architectural decisions for `omarchy-fred-workspaces`.

> [!NOTE]
> All entries were verified against local transcript stores during migration on
> 2026-09-20. Where a transcript could not be found locally, this is noted explicitly
> in the session file. See [`docs/agent-guides/ai-session-stores.md`](../../docs/agent-guides/ai-session-stores.md)
> for the store inventory and verification methodology.

## Session Records

| Date | Topic | Primary Tool | Model | Session Document |
| :-- | :-- | :-- | :-- | :-- |
| 2026-09-11 | Workspace Indicator & Multi-Monitor Desktop Modes (v1.0.0) | `agy` | Gemini 3.8 Flash (High) | [`2026-09-11-workspace-indicator-desktop-modes-v1.0.0.md`](2026-09-11-workspace-indicator-desktop-modes-v1.0.0.md) |
| 2026-09-12 | `clonedFrom` Integration & Upstream Provenance (v1.1.0) | `agy` | Gemini 3.8 Flash (High) | [`2026-09-12-clonedfrom-integration-upstream-provenance-v1.1.0.md`](2026-09-12-clonedfrom-integration-upstream-provenance-v1.1.0.md) |
| 2026-09-12 | Marketplace Security Hardening & Official Listing (v1.2.0, v1.2.1) | `agy` + `claude` (audit) | Gemini 3.8 Flash (High) + Claude Opus 5 | [`2026-09-12-marketplace-security-hardening-v1.2.0.md`](2026-09-12-marketplace-security-hardening-v1.2.0.md) |
| 2026-09-15 | Dynamic All-Monitor Windows Sets (v1.3.0) | `codex` (`0.154.0`) | `gpt-5.6-sol` | [`2026-09-15-dynamic-all-monitor-windows-sets-v1.3.0.md`](2026-09-15-dynamic-all-monitor-windows-sets-v1.3.0.md) |
| 2026-09-15 | Center Monitor Indicator Desync & Atomic File Watch (v1.3.1) | `agy` | Gemini 3.8 Flash (High) | [`2026-09-15-center-monitor-indicator-desync-v1.3.1.md`](2026-09-15-center-monitor-indicator-desync-v1.3.1.md) |
| 2026-09-16 | Hardware Resilience, Topology-Anchored Slots & Gap Compression (v1.4.0, v1.4.1) | `agy` | Gemini 3.8 Flash (High) | [`2026-09-16-hardware-resilience-topology-slots-v1.4.0.md`](2026-09-16-hardware-resilience-topology-slots-v1.4.0.md) |
| 2026-09-16 | Split Monitor Sets: Partial State & Follow Focus (v1.4.2) | `claude` (`2.1.273`) | Claude Opus 5 | [`2026-09-16-split-monitor-sets-follow-focus-v1.4.2.md`](2026-09-16-split-monitor-sets-follow-focus-v1.4.2.md) |
| 2026-09-17 | ECOSYSTEM.md: Patched Hyprland Dependencies (v1.4.3) | `claude` (`2.1.274`) | Claude Opus 5 (`claude-opus-5`) | [`2026-09-17-ecosystem-md-patched-dependencies-v1.4.3.md`](2026-09-17-ecosystem-md-patched-dependencies-v1.4.3.md) |
| 2026-09-17 | Per-Monitor Idle Blanking of Unused Monitors (v1.5.0) | `agy` | Gemini 3.8 Flash (High) | [`2026-09-17-per-monitor-idle-blanking-v1.5.0.md`](2026-09-17-per-monitor-idle-blanking-v1.5.0.md) |
| 2026-09-18 | Settled Idle Tracking, DPMS Sync & Version Footers (v1.5.1) | `agy` | Gemini 3.8 Flash (High) | [`2026-09-18-settled-idle-tracking-dpms-sync-v1.5.1.md`](2026-09-18-settled-idle-tracking-dpms-sync-v1.5.1.md) |
| 2026-09-22 | Rename the workspace helper to tam-desktop-mode | Cursor `3.21.16` | composer | [`2026-09-22-tam-desktop-mode.md`](2026-09-22-tam-desktop-mode.md) |

## Corrections vs. prior `sessions.md`

| Session | Error | Correction |
| :-- | :-- | :-- |
| Sep 15 (v1.3.0) | No Codex transcript UUID cited | Found: `01a0a5ed` in `.codex/session_index.jsonl` |
| Sep 15 (v1.3.1) | Transcript `348c2c39` cited | Not found locally; content marked unverified |
| Sep 16 (v1.4.2) | Transcript `348c2c39` cited | Not found locally; content marked unverified |
| Sep 16 (v1.4.0/1.4.1) | Several prompts missing | Added from transcript `f6fed9ce` |
| Sep 17 (v1.5.0) | Several prompts missing | Added from transcript `b406cca2` |
| Sep 18 (v1.5.1) | Three prompts missing | Added from transcript `322664c3` |
| All agy sessions | agy version presented as fact | Not self-reported in transcripts; noted per session |
