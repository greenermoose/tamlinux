# Session: 2026-11-17 — GitLab and source installation plan

- **CLI Tool**: Codex CLI (`codex`) `0.169.1`
- **Model**: `gpt-6.2-sol`
- **Authorship**: AI-assisted documentation directed by Fred.
- **Commit**: The documentation commit introducing this record and the [1.0.0 plan](../../docs/plans/1.0.0-gitlab-and-source-install.md).
- **Transcript**: Retained privately by the author.

## Prompts

> I want a clean break. No history in the GitLab repos. Everything starts fresh with the 1.0.0 releases. We'd clean everything up so there is not a huge git history. We want the git clones to be small and fast and easy.

> Would it make sense to move tam-last to tam-gooee since it requires Wayland and is intended to be run only from the graphical desktop, not from a kernel console? tam-tooee could be for things that can run in a kernel console (tty).

> Good. How do we document this?

> Implement the plan.

> commit

## Decisions and verification

Documented the four repositories, the kernel-console rule, and the fresh-clone build and install workflow. Checked the plan against the agreed repository map and checked the documentation diff for whitespace and private references.
