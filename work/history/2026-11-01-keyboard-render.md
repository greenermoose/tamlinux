# Keyboard rendering and press/release verification

- **Date**: 2026-11-01
- **CLI Tool**: Codex CLI (`codex`) `0.166.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.

## Prompt

> [Image #1] Fix the missing keyboard problem. I should see a physical representation of the keyboard on this system so I can test keypresses.

## Findings and changes

The installed 2.0.2 widget resolves an unknown keyboard to an OS geometry
name but loads no JSON layout. Its board therefore stays empty. The bundled
104-key fallback in the existing 2.0.3 development source fixes that loading
path; it had not yet reached the installed package.

- Rendered both bundled layouts with the real `KeyboardView`, `FileView`
  and native scan-code conversion using Quickshell's offscreen platform.
  These checks never connect to the desktop or read keystrokes.
- Fixed a second rendering defect: `Loader` overwrote the keycap's size,
  eliminating the intended gutters. An intermediate `Item` now accepts the
  loader's dimensions while the keycap keeps its inset dimensions.
- Changed the fallback caption to name the actual bundled board. Corrected
  the layout documentation: OS geometry names are discovered, but their
  geometry files are not rendered.

The fallback is a physical keyboard diagram with key highlighting, but its
arrangement is generic. An exact laptop layout still needs a transcription
of the physical keycaps; an input-device name and capability bitmap cannot
establish their positions.

## Verification

- Offscreen regression check passes for the generic 104-key board and the
  existing transcribed layout: six rows, all keycaps present, nonzero size,
  a maximum width of 1000 pixels, preserved gutters, only K highlighted
  after native scan code 45, and its original color restored on release.
- Inspected an offscreen image of the fallback: alphanumeric keys,
  function row, navigation cluster, arrows and number pad are visible.
- All four keyboard JavaScript test scripts pass.
- Desktop bar-contract checks: 18 passed. Keyboard dependency checks:
  3 passed. `git diff --check` passes.
- The full desktop suite requires isolated session-bus access and was not
  run in this restricted environment.
- No packaged Test or live physical keypress acceptance was performed.
  The installed package still needs a stage-authorized candidate containing
  these development changes.
