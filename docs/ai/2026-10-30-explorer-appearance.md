# Explorer appearance and deployment test isolation

- **CLI Tool**: Codex CLI (`codex`) `0.166.0`
- **Model**: `gpt-6.1-terra`
- **Transcript**: Retained privately by the author.
- **Prompts** (excerpts):
  > Begin with the source audit and known fixes.

  > Carefully consider the plan for 0.5.12. Choose the most important next step, then work on it.

  > Carefully consider the plan for 0.5.12 in light of what you have just done. Update the plan as necessary. Then choose the most important next step and work on it.

  > In this session, when I say continue, do the following: Carefully consider the plan for 0.5.12 in light of what you have just done. Update the plan as necessary. Then choose the most important next step and work on it. Now continue.

- **Work**: Replaced fixed dark Explorer surfaces and unsuitable text colours with palette roles. Added checks for key field pairs and selected translucent states in both Tamarack variants. Isolated a rollback test from the host graphical-session state.
- **Verification**: 44 keybinding tests and 62 deployment tests passed. Rendered appearance and remaining surface contrast require further verification.

## Micro appearance

Added a token-derived Micro scheme and fresh-account selection while preserving existing settings and same-named personal schemes. Expanded desktop checkpoints to cover the scheme and Micro settings; existing-account migration remains open.

Six application-default tests, 33 theme ownership tests and 33 recovery tests passed. An isolated Micro 2.0.15 true-colour launch loaded the generated light scheme without a reported scheme-load error. Rendered dark/light and reduced-colour checks remain open.

An explicit existing-account migration now adds the Micro scheme only when no selection exists and the generated scheme link is ready. It preserves JSON5 content and uses the migration journal for rollback. All 47 migration tests passed with the packaged JSON5 Python environment; no migration was applied to the workstation.
