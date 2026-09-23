# Session: 2026-09-22 — Rename collectors to tam-agent-usage-*

- **CLI Tool**: Cursor `3.21.16`
- **Model**: `composer`
- **Commit**: `4136c09`
- **Transcript Reference**: `68f9fa04-2323-4102-841a-25ab29a68985`

## Prompts

Name-only sync of the published `fred.agents` collectors after Fred chose daily `tam-*` command names. No new tag, Release, or marketplace submission.

## Key Decisions & Implementation Notes

- Collectors are `tam-agent-usage-{update,claude,codex,cursor,antigravity}`.
- `Main.qml` / `Agent.qml` resolve the new helper names via `Qt.resolvedUrl`.
- Plugin ID stays `fred.agents`.

## Verification

- Name-only `main` sync so `tam-plugin diff fred.agents` does not show a helper-name split.
