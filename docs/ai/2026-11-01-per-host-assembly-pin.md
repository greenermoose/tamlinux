# Per-host assembly pin for tam-deploy

- **Date**: 2026-11-01
- **CLI Tool**: Claude Code (`claude`) `2.1.316`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > We need to be able to do work on [two fleet laptops], so it's unrealistic to expect no diverging commits. We need a better plan to clean up divergent repos on those systems.

  > Yes

- **Problem**: In a fleet configuration every host shared one consumer `flake.lock`, and `tam-deploy` rewrote and committed it on whichever host it ran. Hosts on different accepted versions therefore always conflicted, and a host following the shared configuration was silently retargeted to another host's assembly.
- **Implementation**: A registered host may record one assembly revision in `hosts/<hostname>/state/assembly`. When present, `tam-deploy` reads, pins, restores and commits that file instead of the lock; candidate builds stage it only for the build and always restore it. Hosts without the file behave as before. The consumer flake reads the same file for that host's profile (consumer-side change, not in this repository).
- **Delivery boundary**: Develop only. No assembly or deployment includes this change yet.
- **Verification**: 96 deployment tests pass, including four new host-pin tests (selection and isolated recording, invalid and symlinked pins refused, candidate build staging and restoration). With the consumer change, every existing host profile evaluated to an unchanged derivation, and a test pin to an older assembly changed only that host's shell version.
