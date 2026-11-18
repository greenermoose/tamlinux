# Editor integration test corrections

- **Date:** 2026-11-15
- **Tool:** Codex CLI 0.169.0
- **Model:** gpt-6.1-sol
- **Transcript:** Retained privately by the author.

## Request

> Keep going

Continuation of candidate preparation using tam-bundle.

## Changes and evidence

The frozen source suite found two failing command units. The launcher fixture
still expected micro as the default, although the selected product uses tam-edit.
The tam-open fixtures supplied only micro and inherited a PATH containing a
real development tam-edit. That editor correctly refused nonterminal input.

Update the expected default and supply isolated tam-edit fixtures. Add explicit
checks of tam-edit preference and the micro fallback with a bounded PATH.
No product code changes. `make check` passes all 20 tam-open tests and all 22
launcher tests; launcher sockets require outside-sandbox execution.
The prior frozen suite ran 301 units: 299 passed, two failed, no core dumps.
These corrections are on develop; they do not alter that frozen candidate.
