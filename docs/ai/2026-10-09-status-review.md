# 2026-10-09 — Deployment state and current plan review

- **CLI Tool**: Codex CLI `0.162.0` (live checked).
- **Model**: `gpt-6.1-sol`.
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted documentation and monitor-plugin repair directed by Fred.
- **Commit**: The review commit carrying this record.

> Take a look at the status of the tamlinux project and the current plan. Are there any deficiencies or mistakes in the plan that should be corrected now? I've got agy working on the tam command, but I want you to get you working on the most important next project to do for the tamlinux project overall. Also, what should I test before accepting Tamlinux version 4.0.1?

Corrected protocol-plan and index status after a live audit found shadow Test
had returned to the accepted source without observation. Historical test evidence
remains; a continuous period is not claimed. Acceptance must verify the actual
candidate and fresh comparisons. Clarified source/delivery ownership and the
need to reconcile consolidated plugins with accepted payloads before selection.
Updated the command pointer to the implemented native offline guide while
leaving command source with its current maintainer.

The exact shadow candidate was subsequently restored through a guarded consumer;
fresh comparisons agree, collection is active, and all eight installed plugin
targets remain unchanged. Full archive review found 25 historical output
disagreements and two gaps; these remain unresolved authority blockers.

Verification: reviewed local source, installed revision, running service
environment, timer state and retained archive; documentation whitespace and
public provenance checks. Separate deployment fixes have their own focused tests.
No product VERSION bump, publication, release or physical acceptance is claimed.

## Monitor regression reported during acceptance

> fred.monitor shows [Image #1]

The attached screenshot showed an empty display panel, headed `Display: No
Monitors`, with plugin version 2.0.2. The compositor still reported three active
outputs. Reproduction with the running shell's closed helper environment showed
that the state helper exited before reading monitors: it required mode 0700 on
the shared `$XDG_RUNTIME_DIR/tamlinux` namespace, which another component had
created as 0755. Layout preview storage had the same incompatible check.

Version 2.0.3 accepts a user-owned shared parent without group/world write
permission, opens it without following symlinks, and creates/validates a private
0700 `monitor` child using descriptor-relative operations. Display facts remain
available when optional cache storage is unavailable; layout transaction storage
still fails closed. The public source now uses the same monitor runtime path.
Other consolidated-source differences remain for separate reconciliation.

Verification: 28 Python tests and 11 model tests pass in each source copy;
nine added regression tests exercise 0755 and 0700 parents, unsafe permissions,
foreign ownership, symlinks, private cache/transaction writes, and display reads
without cache. Both plugin manifests pass registry validation. The running
2.0.3 Test reports all three monitors and brightness values. The immutable plugin
Test preserves the accepted plugin for rollback; no plugin Run or product
acceptance is claimed. The existing 0.4.1 shell Test stays selected, and
post-restart archived comparisons agree. Source/storage tests do not claim a
physical preview/rollback test; that remains a focused user acceptance check.
