# Macro reliability takeover

- **Date**: 2026-10-31
- **CLI Tool**: Codex CLI 0.166.0
- **Model**: `gpt-6-astra`
- **Transcript**: Retained privately by the author.
- **Base**: `730c1a6`, including Antigravity's macro editor and punctuation mapping.

## Guiding prompts

> Take over from agy to get the macro stuff working.

> continue

> Do you want me to do a key combo keypress so you can see how key presses and releases actually work?

## Implementation

Validated canonical XKB key identities, escaped generated Lua/command arguments,
atomic backend saves with stale-editor checks and rollback, cleanup of retired
bindings, a compositor-inhibited key recorder, modifier-release waiting with
focus cancellation, serialized paste dispatch and balanced key cleanup. The
existing native Hyprland clipboard path remains the delivery mechanism.

The development trial checks both the model and macro runner, regenerates
bindings using its exact installed command, and records both installed commands.
The packaged session entry loads user macros after personal bindings.

The clipboard remains the macro text. There is no unverified claim of universal
paste acceptance; layer-shell targets, physical key behavior and application
compatibility require live acceptance. See `commands/tam-macro/README.md`.

## Verification

- 20 macro tests passed, including generated Lua execution, punctuation,
  Backspace, aliases, held modifiers, focus changes, save failure recovery,
  stale writers and injection error cleanup.
- 49 keybinding model/explorer tests passed.
- Invisible Wayland QML proof saved a Backspace macro through the real backend
  into temporary configuration; no reload or keyboard input.
- Physical acceptance pending the updated development trial.
