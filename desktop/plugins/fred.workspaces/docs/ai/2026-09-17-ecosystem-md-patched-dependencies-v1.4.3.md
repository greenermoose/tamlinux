# Session: 2026-09-17 — ECOSYSTEM.md: Patched Hyprland Dependencies (v1.4.3)

- **Primary AI Agent**: Claude Code (`claude`)
- **Primary Model**: Claude Opus 5 (`claude-opus-5`) — model confirmed from `"model"` field in transcript
- **Claude version**: `2.1.274` — confirmed from `"version"` field in transcript
- **Transcript**: Claude Code `d6c65ea2-7efb-41ed-bae1-86bc3f78d651`
- **Session start**: 2026-09-17T12:09:57-04:00 (from transcript timestamp)
- **Commits**: `74437e9` (2026-09-17 12:52 — ECOSYSTEM.md),
  `8a4233d` (2026-09-17 12:52 — provenance docs)

## Prompts (verbatim from transcript)

> **Fred:** "We provided PRs for some packages we had to patch to fix bugs on this system. See these replies from those package maintainers. Create a plan for how we will keep our own fork and note the patches required for our system to work well. [...] In the repos of our own software that requires patched versions of third-party software we will keep track of that. I'm thinking of something like an ecosystem folder or the like."

## Key Decisions & Implementation Notes

- Fred chose a single `ECOSYSTEM.md` at the repo root (not a folder) for repos that depend
  on a patched package; the full patch matrix lives in the public registry
  `greenermoose/omarchy-fred-ecosystem`.
- Documentation-only bump to 1.4.3.
