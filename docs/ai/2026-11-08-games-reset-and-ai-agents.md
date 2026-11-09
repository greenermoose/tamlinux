# Reset games and add the AI Agents menu

- **CLI Tool**: Codex CLI (`codex`) `0.167.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted implementation directed by Fred.

## Guiding prompts

> Let's remove all the games that we installed and start over. Can you do that now? I can't remember which version of Tamlinux added games, but I want to remove the ones we have now and find new ones for 0.6.19.

> I want science simulations and learning games.

> The start menu command should have an AI Agents section. Does it?

> Before downloading any games, make a list and I'll review it later.

> The cellular automata program would be cool to have. Make a list and include where to get games like that.

## Changes

Removed the eleven legacy game entries from the `start` catalog and added an
AI Agents section for Claude Code, Codex, Antigravity CLI, OpenCode and Grok
CLI. Each entry launches the existing PATH command without installing or
reconfiguring it. Updated the command version to 0.2.5 and its catalog checks.
Replacement games remain unselected pending the requested review. The public
provenance check also found a private local path in an earlier session prompt;
redacted that path without changing the earlier authorship record.

## Verification

`make check` in `commands/start` passed. The source command reports all 14
activities available on the development host. No agent was launched. The
running development override and packaged installation were not changed.
