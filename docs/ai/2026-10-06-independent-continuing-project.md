# Independent, continuing Tamlinux project

- **Date:** 2026-10-06.
- **CLI Tool:** Codex CLI (`codex`) `0.160.1`, checked live and against session metadata.
- **Model:** `gpt-6.1-sol`, verified against logged turn metadata.
- **Authorship:** Fred supplied the project direction; Codex authored the documentation reconciliation.
- **Transcript:** Retained privately by the author.

## Guiding prompts

> Tamlinux is an independent project, with a goal of providing the best possible user experience on any hardware.

(Excerpt; other product plans remain private.)

> Make it so

> Commit your changes. I'll review and then push.

## Changes and decisions

- Describe Tamlinux as independent and continuing, with user experience across
  modern and older hardware as its goal.
- Remove the temporary-project and final-1.x freeze from active versioning.
- Retain the existing-distribution Nix/host-adapter route and native Void
  packaging as Tamlinux engineering work.
- Use capability-based profiles and measured support; circa-2006 hardware remains
  a validation example rather than a universal age cutoff.
- Mark older provenance records containing superseded product framing as historical,
  preserving their original prompts and attribution.

Documentation only. No runtime, version, release, or deployment change.

## Verification

- Changed-document relative links: PASS.
- Git whitespace check: PASS.
- Public provenance check: no private-repository names, local paths, session IDs,
  store paths, or unannounced product names in the public record.
- Active wording reviewed: remaining temporary-project/graduation references
  are explicitly historical or rejected assumptions.
- No runtime or desktop tests needed for the Tamlinux documentation-only edits.
