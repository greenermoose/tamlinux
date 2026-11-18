# Keyboard panel stand-in board

- **Date**: 2026-11-01
- **CLI Tool**: `claude` `2.1.316`
- **Model**: `Claude Sonnet 5.5` (`claude-sonnet-5-5`)
- **Transcript**: Retained privately by the author.

## Prompt

> Keyboard is not drawn correctly. We need to fix this.

Fred reported this from a screenshot taken on a PS/2 laptop keyboard during the 0.5.12 deployment, then confirmed the fix with "yes".

## Work and verification

- Cause: the resolver chose the OS "pc104" geometry for an unknown board but returned no layout file, so `BarWidget.qml` never loaded a layout and the panel drew nothing. The only drawn board was the Lenovo Calliope, which is why the 0.5.12 Test on the developer's main machine did not show it.
- Fix: a generated 104-key ANSI board (`layouts/pc104-standin.json`), a `standIn` key in the layout registry, and a three-line change to load it when the resolution has no file. The resolver is unchanged.
- Verification: JS tests pass, including new checks that the stand-in exists, has 104 unique key codes and unique ids, keeps the lock LEDs, and is named by the registry. Not yet verified on screen; that waits for a candidate that contains this change.
