# Shared plugin hover and panel version footers

- **CLI Tool**: Antigravity CLI (`agy`) `1.3.2`
- **Model**: Gemini 3.8 Flash (High), `gemini-3.8-flash-high`
- **Commit**: `907d46bdf4d6713f12ff35c136e0df538006e28b`
- **Transcript**: Retained privately by the author.
- **Record preparation**: Backfilled by Codex CLI `0.162.1` (`gpt-6.1-sol`)
  from the original transcript and commit; original tool/version trailers
  match the runtime detector output retained in the transcript.
- **Assignment**: Fred directly instructed and approved the work. No AI
  delegation brief or delegation-table row applies.
- **Prompts**:
  > Check the [redacted: private planning repository] repo to see if we have a plan for improving the fred.* plugins to display their version # in a consistent way that I like on hover and in their panel. Report back either way, then let's discuss.

  > Looks good, just make sure to bump the version numbers of all plugins. I think this is just a patch bump; it is just for cosmetic consistency and does not change any features in any of the plugins.

  > fred.monitor was updated to 2.0.3 by codex. Make a note and your version should be 2.0.4

  > Yes, commit our scoped changes now.

Introduced the shared host's two-part hover rendering and `Tam.Ui.VersionFooter`,
replaced per-plugin panel footer markup, added the missing agents panel footer,
and removed the weather/tides custom hover popup implementations. Eight plugin
manifest patch versions were bumped.

The commit also moved clock calendar/local-ICS/cache watchers to XDG-aware
Tamlinux paths and changed workspace state/helper paths, desktop preference
environment propagation and preference polling. These are behavior-bearing
changes included in the commit, beyond the cosmetic footer description.

The original session reported 418 passing desktop tests. Later investigation
of candidate 0.4.2-a found monitor's QML version still at 2.0.3, a parser that
requires a preceding newline, and all eight manifest URLs reverted to frozen
repositories. The structural tooltip test did not exercise parsing. The
original result is not evidence of complete physical visual acceptance.
[0.4.2-b repair](2026-10-09-0.4.2b-repair.md) corrects those defects and adds
behavioral parser and manifest/QML consistency checks. The original commit
has not been amended or rewritten.
