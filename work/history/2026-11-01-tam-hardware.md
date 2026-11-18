# tam-hardware host probe

- **Date**: 2026-11-01
- **CLI Tool**: Cursor (`cursor`) `3.27.22`, as recorded in that day's Cursor commit trailers
- **Model**: `composer`, as recorded in the same trailers; not independently verified for this session
- **Transcript**: Retained privately by the author.
- **Prompts** (paraphrased from the decision record):
  > Add direct assembly and machine-code development and full host instruction-set and hardware ascertainment.

  > Make it so.

- **Implementation**: `tam-hardware`, a C command that reports the host CPU, instruction-set extensions and DMI identity for agents choosing host-native work, with a plan in `docs/plans/tam-hardware.md`. Serial-number fields are never printed; the fixture's serial is a sentinel the tests check for.
- **Delivery boundary**: Develop only. No assembly or deployment includes it yet.
- **Verification**: `make check` passes its 5 tests against fixture sysfs and CPU data.
- **Commit note**: The Cursor session left this work uncommitted after releasing its claims. The bosgame Claude Code session (`claude-opus-5-5`) committed it unchanged, adding only the `build/` ignore rule and this record.
