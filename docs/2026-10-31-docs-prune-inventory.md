# 2026-10-31 — Docs prune inventory (public tamlinux)

- **Status:** Executed in working tree; stamp for archived paths is
  `020c8dc` (HEAD before deletes). Filing cards:
  [`plans/FILING-CARD.md`](plans/FILING-CARD.md),
  [`ai/FILING-CARD.md`](ai/FILING-CARD.md),
  [`../desktop/FILING-CARD.md`](../desktop/FILING-CARD.md).
- **Scope:** Public product repo `tamlinux` entry docs, closed Gate A plans,
  desktop README proof dump, closed AI logistics.
- **Method:** Rewrite living entry points → stamp HEAD → delete archives →
  FILING-CARD. Same pattern as private 2026-10-31 prune.
- **Held elsewhere:** `docs/ai/README.md` and
  `docs/ai/2026-10-31-macro-reliability.md` (codex session); inbox note asks
  that session to refresh the AI index. `AI_PROVENANCE.md` and
  `docs/plans/keybinding-usability.md` also held by that session (not edited).

## Summary

| Area | Action |
| --- | --- |
| README, UPSTREAM, VERSIONING, botanical banner, plans README | Rewritten for 0.5.11 / Gate A done |
| Closed 0.4.3–0.4.4 and Gate A framing plans + evidence | Archived |
| desktop/README.md | Shortened; long proof at stamp |
| docs/ai session logistics before console-first | Archived (~117 files); ~42 kept |
| Plugin `docs/ai/README.md` | Historical 1.x banner |

Retrieve archived files with `git show 020c8dc:<path>`. Do not treat
filing-card entries as current guidance.
