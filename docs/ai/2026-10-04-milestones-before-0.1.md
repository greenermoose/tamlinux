# Session: 2026-10-04 — Milestones before 0.1

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Let's start bumping the VERSION of tamlinux as we make incremental
  > progress toward 0.1.0. Think about what milestone should get 0.0.2 and
  > 0.0.3 before we hit the documented 0.1.0 milestone. Update the
  > VERSIONING.md file accordingly with more granular versions in the 0.0.x
  > series.

## Key decisions and implementation notes

- The work toward 0.1 falls into two groups that Fred accepts one step at a
  time. **0.0.2** is the foundation: Arch's own package mirror and stock
  kernel, the Hyprland configuration, the shell environment, the session
  entry and units, and the login screen. **0.0.3** is the shell's session
  services running in the Tamlinux host, which leaves only the bar for the
  0.1 cutover.
- Before 0.1 a 0.0.x patch number marks a milestone, not a fix; fixes inside
  a step ship with the next milestone. From 0.1 on, patches are fixes again.
- Documentation only: `VERSIONING.md` and `CHANGELOG.md`. `VERSION` is
  unchanged; Fred decides when to bump it.
