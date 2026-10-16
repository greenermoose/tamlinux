# Retire agent-to-agent delegation

- **Date:** 2026-10-16
- **Time:** First explicit clock check 13:18 -0400; documentation complete 13:24 -0400. Earlier read-only audit start was not captured.
- **Stage:** Develop; agent workflow documentation only
- **CLI Tool:** Codex CLI `0.163.0` (runtime detector)
- **Model:** `gpt-6.1-sol` (runtime detector)
- **Transcript:** Retained privately by the author.
- **Commits:** The commit containing this record and its accompanying documentation changes.
- **Authorship:** Fred set the direct-agent policy; Codex audited and edited the guidance.
- **Checked against:** `docs/ai-provenance-standard.md`, `docs/ai/README.md`, `AI_PROVENANCE.md`, and the developer's instruction.

## Guiding prompts

> I have tried to have codex and claude delegate tasks to opencode and agy. That failed. Review all the delegation machinery and develop a plan to retire it. Going forward, I (Fred) will simply work with every AI agent directly. Make sure that any skills, guides, runbooks, and memories are updated so no agents think that we are still doing delegation. It wasted time and tokens and I could never get it to work. Furthermore, Google has just released argon for agy, so agy is much smarter now that it used to be.

## Key decisions

Fred now directs every AI agent himself. Existing assignment trailers and
records remain historical evidence. His report about Argon does not supply
an installed model ID; provenance continues to detect actual session models.

## Verification

Documentation-only diff and whitespace review; new local links resolve. Historical delegation records and trailers retained. No deployment or code test was needed.
