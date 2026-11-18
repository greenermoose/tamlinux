# Console-startup settings recovery

- **CLI Tool**: Codex CLI (`codex`) `0.164.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted implementation and verification directed by Fred.
- **Commit**: The commit introducing this record contains the implementation.
- **Prompt**:
  > We are working to create a text-only boot for Tamlinux 0.5. Take the next steps toward this goal.

The checkpoint CLI accepts up to eight explicit configuration source roots.
Each adds the same finite manifest paths. It retains the original single-root
journal key and sorts repeated CLI roots so status and restoration accept a
different argument order. Ownership checks, refusal of redirected parents,
scope overlap checks and uncovered mutable-link rejection remain in place.
Restoration archives later writes across all selected roots before mutation.

Verification: 30 recovery tests and 28 migration tests pass, including the
isolated D-Bus check, a shared/host source round trip, interrupted restoration,
retention of later writes, bounded CLI arguments and rejection of unselected
link targets. Candidate identities remain unchanged. No deployment, boot/login
mutation or physical startup acceptance occurred in this development slice.
