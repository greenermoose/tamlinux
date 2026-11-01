# Deployment state and recovery transactions

- **Date**: 2026-11-01
- **CLI Tool**: Codex CLI (`codex`) `0.166.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Evaluate the current situation. Figure out how to get out of this mess and why you got into it. Fix the process so we don't run into this situation again. We need better scripts to help us make faster and more certain progress preparing a test candidate.

  > Implement the plan.

- **Implementation**: Status compares profile, receipt, lock, immutable endpoints and running shell. Direct generation activation retains Home Manager prerequisite ordering. Transactions preserve deployment and recovery failures and block unsafe retries. Reconciliation is limited to a digest-bound, proven profile-only mismatch.
- **Delivery boundary**: Develop improvements; the prepared 0.5.12 assembly is unchanged. These changes require a later recorded candidate before deployment.
- **Verification**: 86 deployment tests pass, including real temporary-profile writes, verified recovery, explicit partial failure, mismatch refusal and digest-bound reconciliation. The read-only status was also checked against a coherent installed candidate. No physical rollback trial is claimed.
