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

The Micro template now derives its green and gold roles and selection fill by mixing the shared tokens toward foreground. The 33 theme ownership tests passed. An isolated Micro 2.0.15 256-colour probe exercised each of 22 explicit colour pairs in both variants using the standard xterm palette; minimum contrast was 6.71:1 dark and 5.21:1 light. Actual selection composition, terminal palettes and physical rendering remain unverified.

Added a repeatable pseudo-terminal test that launches Micro and checks the emitted 256-colour indices for each generated pair against the standard xterm palette. It passed with Micro 2.0.15 and skips if Micro is absent; it does not validate selection composition or physical display output.

Added a separate selection test that sends Shift-right to Micro in a pseudo-terminal and checks the selected character's emitted foreground and background in both Tamarack variants and both true-colour and 256-colour modes. Both Micro output tests pass. Other terminal palettes and physical rendering remain open.

An opt-in isolated Sway/GTK 4/libadwaita feasibility test creates a temporary user stylesheet from both Tamarack variants, then checks a label's foreground and a fullscreen window's screenshot background. It passed with GTK 4.24.1 and libadwaita 1.10.0. This is not a shipped adapter and does not verify other controls, application-specific styling, user CSS recovery or physical appearance.

The theme generator now produces an inert GTK 4 prototype stylesheet from the shared foreground/background tokens; a personal theme's file takes precedence. The opt-in GTK test now consumes the generated stylesheet and passes in both variants. All 34 theme ownership tests passed. No user GTK configuration is changed, and broader GTK/Qt coverage and recovery remain open.

The GTK 4 prototype now also derives the accent fill and its text from shared tokens. The isolated GTK proof checks a real suggested-action button's text colour and rendered fill in both variants; selection, focus, errors and other controls remain open. The all-theme generation test initially exposed an unavailable alias in older themes; using the existing selection foreground alias restored all 34 tests.

An isolated focused GtkEntry selection did not initially use the accent fill. The prototype now specifies text-selection foreground and background explicitly. The GTK proof checks the selected bounds and rendered colours in both variants. Other selection surfaces, focus indicators, error states and application behavior remain open.

The prototype now supplies error colours from the danger token. The isolated GTK proof verifies that an error label uses the token in both variants; filled error controls and other error states remain open.

The isolated GTK proof now verifies a destructive-action button's foreground and rendered fill in both variants. Setting colour variables alone did not yield the intended foreground, so the prototype includes an explicit button rule. Suggested and destructive fills are checked within their own widget bounds. Hover, pressed, disabled and other application states remain open.

The theme generator now supplies an inert GTK 3 window stylesheet as well. An opt-in isolated GTK 3.24.52 proof verifies the basic label foreground and window background in both variants, and all 34 theme ownership tests passed. This does not establish real application controls, selection, focus or personal CSS recovery.

The deployment rollback now checks that graphical-session state is knowable before activating the previous generation, and checks again afterward before any shell restart. A focused test verifies an unavailable session leaves the generation activation, lock and deployment record untouched; all 63 deployment tests passed using temporary fixture repositories. A state change or other failure after activation can still leave recovery incomplete; physical VT proof remains open.

Rollback failures after activation is attempted now explicitly report that the generation, lock and record may disagree and direct inspection before retrying. Failure-injection tests cover a failed session recheck and failed pin restoration; all 64 deployment tests pass in fixture repositories. This does not automatically reconcile a partial rollback or prove recovery from an interrupted process.

Ordinary installation now reports both the original failure and any failed recovery; failures while recording after successful activation also identify the possibly inconsistent state. The README no longer promises every failure restores the previous generation. Failure-injection tests and all 66 deployment tests pass in fixture repositories. Interrupted-process recovery and physical VT proof remain open.

Automatic recovery and explicit rollback now verify that the requested previous generation is actually active before continuing. Failure-injection tests cover activation commands that return successfully without selecting that generation; all 68 deployment tests pass in fixture repositories. This check does not verify all restored endpoints or solve interrupted-process recovery.

Explicit rollback now also verifies installed endpoints against the recorded previous assembly before updating the pin or saving a restored record. A mismatch reports incomplete rollback and leaves those records untouched; all 69 deployment tests pass in fixture repositories. Automatic recovery after an installation failure does not yet verify those endpoints, and a physical VT trial remains open.

Automatic recovery now checks installed endpoints against the previously active assembly as well, including when the consumer lock was already staged for a different assembly. Mismatches report both the original deployment failure and the recovery failure. All 70 deployment tests pass in fixture repositories; this requires the old assembly to be available for Nix evaluation and does not prove interrupted or physical recovery.

The inert GTK 3 prototype now specifies entry selection foreground and fill from shared tokens. An isolated GTK 3.24.52/headless Sway proof checks the selected text and rendered colours for both variants, with logical widget focus; all 34 theme ownership tests pass. This does not establish physical desktop focus, browser controls, other GTK widgets or settings recovery.
