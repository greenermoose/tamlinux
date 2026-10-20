# Plain patch versions replace candidate letters — 2026-10-20

- Tool: Claude Code `2.1.305`; model `claude-sonnet-5-5`, dynamically checked.
- Transcript: Retained privately by the author.
- Prompt:
  > For Tamlinux 0.4.4 we went through a bunch of letters, e.g. 0.4.4a through 0.4.4m. This essential turns our three-position semver into a four-position semver. For future Tamlinux versions, let's stop using letters and bump the patch level. So rather than 0.4.5a and 0.4.5b, do 0.4.5 and then 0.4.6.
- Choices:
  > Tag the accepted candidate (Recommended)

  > Names, not numbers (Recommended)

`VERSIONING.md` now describes the patch as a candidate counter and the minor
as the stage. Steps are named by what they do rather than by number, and the
Omarchy-removal step starts at candidate 0.4.5. A Release tags the accepted
candidate's commits without a final bump or rebuild, so untagged numbers are
normal. The letter spellings (`0.4.4-m`, `0.4.4pre.m`) stay as historical
identifiers.

No code changed. `tamlinux-packages` already accepts a plain version in
`VERSION` and sorts it after earlier letters, so only its wording and tests
follow in that repository.

Checked against: `VERSIONING.md` before and after, and the version parsing in
`tamlinux-packages/tools/prepare-candidate.py` and
`tamlinux-packages/nix/packages/default.nix`.
