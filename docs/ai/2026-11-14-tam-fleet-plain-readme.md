# Read the fleet registry README without a file extension

The fleet registry's folder README is now a plain-text file named
`README-systems` rather than `README-systems.md`, matching the repository's
other folder READMEs. `tam-fleet` hardcoded the old name in five places, so
`index`, `index --check` (via `check`) and `reconcile` looked for a missing
file.

The command and its tests now use `README-systems`. The generated Markdown
index block inside that file is unchanged; `tam-fleet index` still rewrites
only the text between its two markers.

Verification: `python3 -m unittest discover -s commands/tam-fleet/tests`
(19 tests, OK), and `tam-fleet check` against the real registry and
configuration passes.

- **Date:** 2026-11-14
- **CLI Tool:** OpenCode (`opencode`) `2.2.5`
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted fix with regression tests.

## Guiding prompts

> Try again. Codex is done.
