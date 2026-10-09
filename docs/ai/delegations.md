# Delegated work in `tamlinux`

Work that one AI agent (the **orchestrator**) assigned to another (the
**delegate**). The orchestrator writes a task brief; the delegate does the task
in its own branch and makes one commit, labelled with its own harness and
model; the orchestrator reviews it, merges it unchanged with
`git cherry-pick`, and puts any corrections in its own commits. How to read
the trailers is in the [provenance standard](../ai-provenance-standard.md#work-one-ai-assigned-to-another).
Task briefs and review notes are retained privately by the author.

**Outcome** is one of: *merged unchanged*; *corrected* (a later commit fixes
the delegate's work); *follow-up, brief error* (a later commit fixes a mistake
in the orchestrator's brief, not the delegate's work); *partly redone*;
*discarded*.

| Date | Task | Assigned by | Done by | Delegate commit → merged | Outcome | Rework commits | Session record |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 2026-10-09 | T31: `tam-work` as a Tamlinux command | Claude Code `2.1.295` (`claude-opus-5-5`) | Antigravity `agy 1.3.2` (`gemini-3.8-flash-high`) | `bd631f3` → `07803a3` | Merged unchanged | `cccb641` (Claude: an inherited test let claim processes inherit the caller's session; not a delegate fault) | [tam-work moves into Tamlinux](2026-10-09-tam-work.md) |
| 2026-10-05 | T9: port the audio, Bluetooth, network, Wi-Fi QR, power and speed-test panels | Claude Code `2.1.290` (`claude-opus-5-5`) | Antigravity `agy 1.2.17` (`gemini-3.8-flash-high`) | `69bc352` → `c195b79` | Follow-up, brief error | `9970b70` (Claude: the brief named a directory Quickshell cannot import) | [keybinding viewer, audio and Bluetooth](2026-10-05-keybinding-viewer.md) |
| 2026-10-05 | T10: test the keybinding viewer model | Claude Code `2.1.290` (`claude-opus-5-5`) | OpenCode `opencode 1.18.31` (`big-pickle`) | `4152613` → `54f917e` | Corrected | `4aca994` (Claude: the missing final newline) | [keybinding viewer](2026-10-05-keybinding-viewer.md) |
| 2026-10-05 | T12: port the bar's indicators, keyboard layout and tray widgets | Claude Code `2.1.290` (`claude-opus-5-5`) | Antigravity `agy 1.2.17` (`gemini-3.8-flash-high`) | `242cc8a` → `0c617d9` | Follow-up, brief error | `2a26ea7` (Claude: a verbatim port the brief required breaks the compositor-boundary test until 0.3.1; the commit predates the `AI-Reworks` trailer) | — |
| 2026-10-05 | T14: behaviour tests for the panel and bar-widget models | Claude Code `2.1.290` (`claude-opus-5-5`) | Antigravity `agy 1.2.17` (`gemini-3.8-flash-high`) | `b70e31a` → `fff2c93` | Corrected | `e060661` (Claude: three branches no case covered, found by mutation) | — |
| 2026-10-06 | T17: the bar-widget contract test | Claude Code `2.1.291` (`claude-opus-5-5`) | OpenCode `opencode 1.18.31` (`big-pickle`) | `4871051` → `3814002` | Corrected, brief error | `fb65149` (Claude: optional chaining, which opencode's notes found; K1 skipped whole without Omarchy's Ui, where the brief was ambiguous) | — |
| 2026-10-06 | T18: parity tests for the bar layout model | Claude Code `2.1.291` (`claude-opus-5-5`) | Antigravity `agy 1.3.0` (`gemini-3.8-flash-high`) | `645547a` → `f249f3a` | Merged unchanged | — | — |
| 2026-10-06 | T19: the shell names no Omarchy command | Claude Code `2.1.291` (`claude-opus-5-5`) | OpenCode `opencode 1.18.31` (`big-pickle`) | `a79f9da` → `a81f497` | Follow-up, brief error | `8df0ff0` (Claude: the brief's rule read a `/` after `++` or `--` as a regular expression; opencode's notes found it) | — |

These three delegate commits predate the `AI-Role`, `AI-Assigned-By` and
`AI-Task` trailers, so this table is their only record of who assigned them.
Their `AI-Tool` and `AI-Model` trailers name the delegate correctly.
