# Session: 2026-10-07 — Independence-first replanning

- **CLI Tool**: Codex CLI (`codex`) `0.161.0`, checked from the running tool.
- **Model**: GPT-6.1 Sol (`gpt-6.1-sol`), verified from session metadata.
- **Authorship**: Fred supplied the direction; Codex reviewed and rewrote planning documents.
- **Commit**: Recorded in Git history for this planning change; no implementation or deployment.
- **Product version**: Unchanged at accepted 0.3.3.
- **Transcript**: Retained privately by the author.

## Guiding prompt

> Finish Omarchy independence before making Sway integration the main focus. Start with settings/state and menu cleanup, then implement Tamlinux’s theme system, fonts, and branding. Follow with package and system-configuration ownership, then final removal once the boot work permits it.
>
> That separates two substantial changes: first prove **Tamlinux on Hyprland without Omarchy**, then prove **Tamlinux on Sway**.
>
> I believe this will require significant re-planning. Carefully review the ROADMAP and all the plans. Rewrite everything as necessary. Ask if you have questions.

## Review and commit authorization

> Roadmap looks good. Please commit all your changes. You can close the micro window.

Fred approved the roadmap and authorized committing all planning changes.

## Decisions and work

First prove Tamlinux on Hyprland without Omarchy, then Tamlinux on Sway.
Settings/state and menu cleanup is stage 0.4; owned theme generation, fonts and
branding is 0.5; package/system ownership and boot-dependent final removal is
0.6. Independent Hyprland acceptance is required before Sway integration and
packaging at 0.7. Physical Sway daily use is the second gate at 0.8. Hyprland
removal stays 1.0, another distribution 1.1, Void pilot 1.2 and repeatability 1.3.

Prepared compositor work and its technical choices remain evidence; its former
0.4 schedule is superseded. Accepted version identifiers and historical records
are preserved. The package remains `tamlinux` and the planned CLI is `tam`.
Boot work and bounded reliability investigations can proceed alongside ownership;
a partition-cleanup result alone does not prove boot/update/recovery independence.

Updated README, VERSIONING and the development-plan index, desktop decoupling,
installation framework, command and base plans. Added explicit theme-system and
deferred Sway plans. Theme planning covers validated deterministic generation,
application reloads, coherent state migration and rollback. This session does
not implement a generator, migrate user data, change running configuration,
remove packages, perform disk operations or publish anything.

## Verification

Documentation review checks relative links, whitespace, agreement of current
stage definitions and unchanged product VERSION. Public provenance is checked
for private identifiers and transcript paths. No application tests or physical
workstation tests are claimed for this planning change. Fred reviewed the
roadmap and authorized local commits; publication remains separate.

Completed: whitespace checks passed; local Markdown file targets resolve;
product VERSION is unchanged at 0.3.3; public provenance and development plans
pass the private-reference scan. The retained compositor plan was checked
against its previous complete body. Current stage order was reviewed across
the roadmap, detailed route and public versioning. No runtime test was run.
