# 2026-10-05 — Bar widget ports merged, and provenance for delegated work

- **CLI Tool**: Claude Code `2.1.290`.
- **Model**: `claude-opus-5-5`.
- **Role**: orchestrator. It assigned and reviewed delegated work; it did not
  write the widget ports.
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Start on 0.2.5 for tamlinux. agy is almost done with T12. Do you have anything for opencode to do? Any lessons learned from the mediocre work opencode did for T11?

  > In our AI provenance and record keeping, make a note of which agents are delegating tasks to other agents. I should be able to look at the repo and know which AI agents were assigning tasks and which were accepting tasks. The work product should be clearly labeled so I know which agent and harness produced the work. And if work had to be redone, that should be noted, too.

## Decisions and implementation

- **T12, the bar's indicators, keyboard layout and tray widgets.**
  Antigravity `agy 1.2.17` (`gemini-3.8-flash-high`) made the ten ports and
  their tests from Claude's brief (`242cc8a`). Claude checked every file
  against its own application of the brief's substitution rules (all ten
  byte-identical) and merged it unchanged as `0c617d9`. The brief had required
  a verbatim keyboard-layout widget, which talks to Hyprland directly and so
  breaks the compositor-boundary test. Claude exempted that one file until
  plan step 0.3.1 moves it onto the compositor facade (`2a26ea7`); the
  exemption fails once the file is clean.
- **Provenance for delegated work.** The
  [standard](../ai-provenance-standard.md#work-one-ai-assigned-to-another)
  now defines the delegate trailers (`AI-Role: delegate`, `AI-Assigned-By`,
  `AI-Task`) and the rework trailer (`AI-Reworks`). [`delegations.md`](delegations.md)
  lists this repository's delegated tasks (T9, T10, T12) with who assigned
  them, who did them, and the commits that corrected them. Delegate commits
  are never amended, so the tasks before this change are recorded only in
  that table.

## Verification

Desktop tests: 110 passed, including the nine new widget-port tests. The
public provenance check (no session IDs, store paths or private repository
names) finds nothing in `AI_PROVENANCE.md`, `docs/ai/` or the standard.

## Follow-up: 0.2.5 accepted

The network and Wi-Fi QR panels needed no shell change; Claude loaded them
and pointed the key and the menu row at them in the configuration
repository. Prompt:

> I did tam-shell tamlinux.network showQr and saw the QR code. I accept 0.2.5.
