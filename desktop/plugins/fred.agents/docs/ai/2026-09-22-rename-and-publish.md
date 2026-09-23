# Session: 2026-09-22 — Rename and publish fred.agents

- **Tool:** Codex CLI `0.155.1`
- **Model:** GPT-6 Sol (`gpt-6-sol`)
- **Transcript:** Codex session `01a0cbc2-f57e-7571-ae15-aee3f924c840`
- **Scope:** Repository naming and public pre-release. The existing v1.1.2 plugin code was preserved.

## Guiding prompt

> Let's rename the local repo for fred.agents to be agents-fred-tamlinux, then create a GitHub repo for it and publish it there. We will not release this to the omarchy marketplace.

## Work

- Renamed the local checkout to `~/Code/agents-fred-tamlinux` and used `greenermoose/agents-fred-tamlinux` for the public repository.
- Updated the manifest, upstream diff recipe, README install command, and current provenance index.
- Kept the v1.1.2 CHANGELOG section marked Unreleased. No tag, GitHub Release, Show & Tell post, or marketplace issue was created.
- Preserved prior commits and their existing AI attribution.

## Verification

- `omarchy plugin validate` exited successfully for the published checkout.
- The manifest and QML version are both 1.1.2.
- The published tree matches the deployed plugin code aside from repository documentation and provenance files.
