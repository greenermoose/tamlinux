# How Tamlinux Records AI Provenance

Fred builds Tamlinux and its plugin suite with the help of AI coding
assistants. Every public Tamlinux repository records how AI was used, so that
anyone can see how Fred works with AI and trace a piece of code back to the
tools, models, and human decisions behind it.

This page explains where that record lives, how to read it, and what is
deliberately left out. It applies to this repository and every
`*-fred-tamlinux` repository.

## Where to look

| Source | What it tells you |
| :-- | :-- |
| **Commit trailers** | A commit made with AI help carries `AI-Tool: <tool> <version>`, `AI-Model: <model-id>`, and a `Co-authored-by:` line for the assistant. |
| **`AI_PROVENANCE.md`** | The AI tools Fred uses and what each is for, plus a table of the repository's milestones and which AI partner worked on each. |
| **`docs/ai/`** | One record per working session, indexed in `docs/ai/README.md`. Some older repositories still keep these in a single `docs/ai/sessions.md`. |
| **The commits and diffs themselves** | The ground truth. Every record cites the commits it produced, so you can check its claims against the code. |

Each session record gives:

- the date and topic;
- the AI tool and its exact version, checked with `<tool> --version` at the
  time of the session;
- the model, by name and by the ID the tool logged, e.g. Claude Opus 5
  (`claude-opus-5`);
- Fred's guiding prompts, quoted verbatim;
- the commits made, the key decisions, and how the work was verified;
- a transcript status line (see below).

## Tracing a line of code

1. Run `git blame <file>` to find the commit that introduced the line.
2. Run `git show -s --format='%h %ad %s%n%(trailers)' <commit>` to see its date
   and AI trailers.
3. Find the `docs/ai/` record for that date or commit. It shows the prompt that
   led to the change and the decisions behind it.

## Human-authored work

When Fred writes code without AI assistance, the commit carries no AI
trailers, and the session record says so explicitly: implementation by Fred,
with any later AI help (review, documentation, publication) described
separately. A missing trailer on its own is not proof of human authorship;
check the session record.

## What is deliberately left out, and why

**Session IDs and transcript locations.** Each AI tool gives a session an ID
and stores its transcript on Fred's computer or in his account with the AI
provider. Only Fred can look those up. Publishing the private session ID would
link a public commit to a private transcript which contains far more than the
public record, including unrelated work, local file paths, and raw tool output.

**Full transcripts.** For privacy reasons, full transcripts are not published.
Fred retains them, along with a private index that maps each public record to
its transcript, so he can re-check any record against its source. A record
whose transcript was found says:

> **Transcript**: Retained privately by the author.

**Private details inside prompts.** Prompts are quoted verbatim. Anything
private within them, such as a token, a private URL, a local path, or someone
else's personal detail, is replaced by a marker like `[redacted: private URL]`.
No other words are changed. An excerpt is labelled as one.
