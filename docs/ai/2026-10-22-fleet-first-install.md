# Fleet delivery and first-install handling

- **Date**: 2026-10-22–2026-10-23.
- **CLI Tool**: Codex CLI (`codex`) `0.163.0`, checked from the running tool.
- **Model**: `gpt-6.1-sol`.
- **Transcript**: Retained privately by the author.
- **Prompt** (excerpt; private machine name redacted):
  > - Package the fleet tools and supported first-install handling; activate [redacted: personal detail]’s host profile.
- **Further direction**:
  > I want to boot every machine to a usable text login as quickly as possible for that machine. Then I want to be able to run tam from the shell. And then if I want, I can run a graphical shell.

## Result

Develop the first Blue Sparkler candidate, 0.5.0, carrying the existing fleet
workflow and registered local-host deployment selection. Add `tam-deploy init`
for an account with no user generation, without requiring a graphical session
or ambient Home Manager CLI. It builds the exact consumer generation, checks
all installed package endpoints and records the initial deployment without a
fictional rollback generation. The selected assembly/components must already
be on main, or test with the explicit option; no branch is moved.

A build failure restores the lock before activation. A partial activation or
verification failure preserves its attempt record and blocks unreviewed retries.
Existing installations continue through the ordinary rollback-preserving path.
The assembly build also exposed a bootstrap helper that discarded its Nix
provider PATH. Preserve the caller/package environment and declare its
inspection providers in delivery instead of assuming a native /usr/bin.
Console-first boot policy and optional native features are separate upcoming
work; this change neither enables nor disables a display manager.

## Verification

56 deployment tests and 18 fleet tests pass. The first-install cases cover text
installation without graphical commands, refusal of existing/dangling profiles,
registered identity, explicit Test selection, dirty input, lock restoration,
partial-failure records and blocked retries. Package and physical acceptance
remain separate. No Test, Run, Release or native package removal is performed.
