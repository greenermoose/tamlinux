# Plain text README conversion

- **Date:** 2026-11-13
- **Time:** 20:15 to 20:38 -0500 (session window).
- **Stage:** Develop; documentation and its filename consumers.
- **CLI Tool:** Codex CLI 0.169.0, checked from the running binary.
- **Model:** GPT-6.1 Sol (`gpt-6.1-sol`), verified from the session runtime.
- **Transcript:** Retained privately by the author.
- **Commits:** The commit adding this record.
- **Authorship:** Fred approved the conversion plan; Codex converted 62
  tracked README files and updated affected consumers under his direction.
- **Checked against:** The tracked originals at `d74e85be6dc7`,
  the converted README files, active references and affected build/test files.

## Guiding prompt

> Read the approved plan at [redacted: local path] and implement it.

## Decisions

Use relative repository links and readable section names. Preserve original
commands, factual claims, attribution, historical filename records and upstream
filenames. This conversion does not change component versions or source pins.

## Verification

Plugin lifecycle and scaffolding checks (12 unit tests); deployment fixtures (103 tests); staged product installer (4 tests); user defaults (8 tests); shell helpers (43 tests); six command Makefiles staged to a temporary DESTDIR and start uninstall; uninstalled Nix shell build and documentation checks.

Original prose, table cells, URLs and fenced examples were compared with the
replacements; filename edits inside examples were limited to converted targets.
The link audit found no newly missing targets. Pre-existing missing targets
remain outside this conversion. Historical Markdown filenames remain in
immutable-source compatibility code and tests where applicable.

The ordinary whitespace check reports two original code lines with trailing
spaces; those bytes are retained to preserve the examples exactly. The check
with end-of-line whitespace excluded passes.
