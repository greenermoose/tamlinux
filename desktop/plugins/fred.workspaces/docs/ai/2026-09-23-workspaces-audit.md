# 2026-09-23 — Workspaces Audit Fixes

- **Tool:** Codex CLI 0.155.1
- **Model:** `gpt-6-sol` (from the Codex session rollout)
- **Session:** `01a0cdfb-e7dd-7ee1-b72e-14d7a9f05eb4`
- **User prompts:**
  > Make it so.

  > Are you there? It seems like you're spinning and not making forward progress.

## Work

The old v1.3 audit was reconciled against v1.5.1. F2 remained: the helper
changed permissions on Omarchy's shared state directory. F3 remained: even
`status` and `indicator` resolved topology and could write monitor state. F6
was already resolved in `load_full_config()`, which follows a config symlink
and checks the opened file's type, owner, and size.

Version 1.5.2 leaves existing state-directory permissions alone, opens state
without creating the directory for reads, and handles `status` and `indicator`
before topology resolution. A regression test covers Home Manager's symlinked
config path.

## Verification

- Python unit tests: 42 passed in the deployed and published checkouts.
- `omarchy plugin validate .`: passed in both checkouts.
- Runtime files matched byte for byte between the two checkouts.
- Home Manager generation 95 activated the new source. Installed helper and QML
  matched it; the QML version was 1.5.2.
- Live `status` and `indicator` returned `windows` and `W` without changing
  the monitor-state file's timestamp or the shared directory mode.
- A live topology query returned DP-2, DP-1, and HDMI-A-1 in slots 0, 1, and 2.
- Extended hotplug and overnight idle observation had not been completed at
  the time of this record.
