# 2026-10-28 — imv preservation fixes

- **CLI Tool:** Codex CLI `0.165.0` (session version)
- **Model:** `gpt-6.1-terra`
- **Commit:** `bf357d16811579b763e8ce12ee946d563748140d`
- **Transcript:** Retained privately by the author.
- **Guiding request (excerpt):**

> Complete the imv preservation fixes, preserve my corpus work and agy’s keybinding work, and coordinate the final explorer revision after my remaining UI/UX rounds.

Codex implemented and tested preservation of existing Escape bindings in
accepted INI syntax, and avoids shadowing personal imv configuration during
fresh defaults initialization. System fallback is intentionally overridden for
fresh users. The migration and application-default suites passed 34 and 5
tests respectively; the installed libinih parser independently accepted the
three reported syntax variants. No live migration was applied.
