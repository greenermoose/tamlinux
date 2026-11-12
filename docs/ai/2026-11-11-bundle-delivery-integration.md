# First bundle delivery integration

The source checkpoint implements Home Manager link conversion, an exact
bundle preparation/console activation draft and return to the saved Nix
generation. It is uninstalled and not workstation acceptance. The concrete
protocol and remaining gates are in the
[implementation checkpoint](../plans/bundle-delivery-integration.md).

- **Date**: 2026-11-11
- **CLI Tool**: Codex CLI (`codex`) `0.167.1`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted source implementation, tests and records.

## Guiding prompt (excerpts)

> Continue Plan 53 toward making tam-bundle the Tamlinux delivery mechanism on [redacted: workstation].

> Next, finish Home Manager link conversion, dormant-slot handling and tam-deploy bundle preparation, activation and return to the exact saved Nix generation. Bundle install/init currently refuse because this integration is incomplete. Continue afterward through the remaining migration gates.

> Nothing was deployed. Preserve Nix/Home Manager delivery and rollback and the installed tam-bundle 0.5.2 pin. Preserve mandatory PID namespaces/private /proc in tests, with no host-process fallback.

> Implement and verify the authorized source work. Present concrete reviewable checkpoints.

## Changes

- Exact generation-link ownership, bounded switch-time copies, private durable
  journals and restartable conversion/return. Later bundle-era edits are kept
  privately before the original links return. Unrelated home commands remain.
- Carried-list planning, an exact native rollback archive contract and a
  delivery-free Home Manager generation. The latter removes Tamlinux from
  both explicit home endpoints and the Nix package profile, while retaining
  unrelated packages and the original recovery generation.
- The first migration is armed in user state until console conversion. System
  prepare/apply and user settings agree before recording success. Recovery
  retains a separate native package approval gate and can continue after the
  older native package replaces the new tam-bundle executable.
- Bundle defaults for the two generated startup files: Hyprland's entry file
  and UWSM's environment file. Native runtime and product paths replace Nix
  paths in these defaults.

## Verification

- 128 deployment fixtures passed, including seven new home-link cases. The
  new cases interrupt conversion and return after each tested rename, sync
  and journal publication, and retry from the on-disk journal.
- Six cross-layer fixtures passed with the real sanitized C bundle engine,
  temporary roots/homes and mandatory private PID/private-proc isolation.
  They cover exact-artifact console activation, settings edited after prepare,
  original Nix return, four deployment-phase interruptions, stale identities,
  graphical refusal, native recovery gates/corruption, and leftover profile
  commands. Home Manager activation is modeled by a fixture that refuses
  real-file conflicts; no workstation activation is claimed.
- Four product installation fixtures passed, including the actual default
  startup file contents and conventional staged layout.
- A real delivery-free generation was evaluated and built from the pinned
  Home Manager implementation without activation. Inspection found no
  Tamlinux commands in its package profile and neither of its two explicitly
  disabled test endpoints. This is an evaluation/build proof, not a real
  Home Manager activation or recovery proof.

## Remaining boundary

Fresh-account bundle init, subsequent bundle updates, complete settings and
Nix-reference coverage, short console helpers and stage integration remain.
The tool's full migration suite is recorded separately in the
[tam-bundle source record](https://github.com/greenermoose/tamlinux-tools/blob/develop/docs/ai/2026-11-11-bundle-migration.md).
No native package, installed tool pin, user generation, candidate, branch
stage or release was changed by these checks. Real-machine migration remains
behind its approvals and acceptance proofs.
