# HP notebook keyboard diagram

- **Date**: 2026-11-01
- **CLI Tool**: Codex CLI (`codex`) `0.166.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.

## Prompt

> I need a better keyboard diagram.

Excerpt; the user also supplied HP Notebook 15-f233wm identification,
SKU `L0T33UA#ABA`, replacement-part cross-references and the built-in
PS/2 device identity.

## Implementation

Codex transcribed the US notebook key arrangement from the
[HP service guide](https://h10032.www1.hp.com/ctg/Manual/c04763947.pdf),
page 11, and a [compatible replacement-board photograph](https://www.reliablelaptopparts.com/genuine-new-hp-15-f023wm-15-f024wm-us-notebook-keyboard-with-frame/).
The layout names its sources and remains `reference-transcribed` pending
physical confirmation. HP's guide lists US spare `776778-001`; generic
PS/2 metadata does not establish an OEM manufacturer or spare number.

- Match the exact system vendor/SKU together with the built-in device
  name and bus; an unrelated laptop or external USB board cannot inherit it.
- Draw 100 physical keys, a compact function/navigation row, an integrated
  number pad, and half-height Up/Down keys sharing a column.
- Show shifted symbols and secondary action legends, including PrtSc and
  Pause. The firmware-local Fn key has no invented input code.
- Map alternate media/brightness/radio codes to their physical F-keys for
  highlighting, binding lookup, search and tooltip explanations. These are
  standard Linux action codes; physical firmware behavior is not yet accepted.
- Increase the diagram's available key size and fit longer legends.
- Update the independent development app from an exact source archive;
  retire superseded archived trial builds after successful installation.

## Verification

- All five keyboard JavaScript suites pass, including SKU mismatch, external
  device, unique input codes, geometry overlap, numpad alignment and media
  shortcut lookup checks.
- Real-QML offscreen rendering passes for all three bundled layouts. The HP
  checks verify independent Up/Down highlighting, function-row proportions,
  media-key highlighting and release, in addition to keycap gutters and K.
- Desktop bar contracts: 18 checks pass. Keyboard dependency boundary:
  three checks pass. The patch has no whitespace errors.
- The invisible standalone check selects `hp-15-f233wm-us`, detects the
  built-in PS/2 keyboard, and loads 226 shortcuts without opening a panel.
- Inspected an offscreen image of the diagram against the reference photo.
  Physical layout and keypress confirmation remain with the user.
