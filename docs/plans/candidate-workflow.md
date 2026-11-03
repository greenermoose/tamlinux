# Fast development and candidate testing

Status: implemented in Develop, 2026-11-02. Automated package checks and development smoke trials passed; packaged candidate acceptance remains pending.

Develop components with native builds and focused checks. Try commands through an explicit development prefix, and apps, plugins and shell components through interactive previews or deliberate reversible live trials. Candidate preparation gathers selected work, commits sources, pins exact revisions and builds the reproducible assembly once.

The delivery helper owns a locked, resumable transaction: selection, source finalization, publication, pinning, native preparation, verification, building and freezing. A retry uses the same reserved version and immutable source selection. Completed work is reused only while its inputs remain valid. Source changes, ambiguous ownership and inconsistent installation state stop the workflow with a specific action.

Separate identities cover source checks, native payload compatibility, Nix derivations, consumer readiness and installed observations. Candidate metadata must not invalidate expensive native compilation. An unchanged compatible native package can be pinned by a later candidate; it keeps its original version and source provenance. The native console welcome is generic; the user assembly supplies candidate identity.

Test uses the prepared generation, a recorded recovery baseline and exact package outputs. Development handover preserves later work. Installation, physical observations, energy measurement and human acceptance have separate states. Run and Release remain explicit promotions of the tested assembly.

Acceptance requires cold, unchanged, interrupted and single-component preparation trials; no repeated expensive work for unchanged inputs; fault injection around commits and activation; interactive command/app/plugin/shell trials; and a complete operator rehearsal using only documented commands. Physical hardware proof is recorded separately from automated tests.

Implementation owners: product development trials and deployment in this repository; source collection, package boundaries and candidate freezing in tamlinux-packages; consumer-specific authorization and records in the operator integration.

Implementation verification and its limits are recorded in [the development record](../ai/2026-11-02-candidate-workflow.md). The next candidate still requires an explicit packaging request and digest-bound Test approval.
