# Workstation upgrade plan and 0.5 scope review

- **CLI Tool**: Codex CLI `0.166.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted planning and review directed by Fred; no product implementation.

## Guiding prompts

> Take a look at the work done so far for tam-workstation-upgrade. Draft a solid plan for that command, but defer implementation to 0.6. Review the goals for 0.5 and make sure we're on track to get it done with 0.5.12. Let me know exactly what is left to do before we have a candidate 0.5.12 to test that has a good chance at being the last 0.5 versions we make.

> I accept the plan. Step me through the next actions and input you need from me.

## Result and validation

Expanded the upgrade plan with released assembly validation, local profile and
compatibility checks, native-change stops, transaction recovery, packaging and
physical console proof. Fred reviewed the file in Micro and accepted it.
Implementation is deferred to 0.6. Existing console-capable deployment still
needs candidate proof. The existing five selector tests pass; no new command,
activation, stage move or privileged system change was implemented.
