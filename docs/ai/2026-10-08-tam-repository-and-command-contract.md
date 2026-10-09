# tam command contract update

- **Date:** 2026-10-08
- **CLI Tool:** Codex CLI 0.162.0
- **Model:** `gpt-6.1-sol`
- **Transcript:** Retained privately by the author.
- **Commits:** Approved command contract and component ownership documentation.
- **Authorship:** Fred supplied command behavior; Codex updated the plan.

## Guiding prompts

> Let's start work on the tam command. I think we should create a new repo called tam and put all of our work in that. Do you agree? If not, where should the development files be stored? How should we start? If you don't know what the tam command is for, read the repos and ask me questions.

> Bare tam should print a concise intro and exit. tam browse should open the guide.

> I approve the plan. Please commit your work and close the window showing the plan.

## Changes and verification

The command plan now specifies concise bare invocation and explicit browsing,
superseding automatic welcome/guide startup. Only successful explicit welcome
records welcome state. C with `libtam` replaces the earlier Python proposal;
the local `tam` component repository owns command source and planning, while
product assembly and the installation framework remain here.
The proposed installer repository layout reflects that ownership split.

Review checks cover whitespace and contract consistency. There is no new
executable, deployment, product version change or publication.
Fred approved the plan on 2026-10-09 and requested committing the prepared work.
