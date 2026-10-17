# SDDM PAM keyring cleanup — 0.4.4g

- **Date**: 2026-10-17
- **CLI Tool**: Codex CLI `0.163.0`
- **Model**: `gpt-6-luna`
- **Implementation commit**: `c0aaeee336874bc15eae0e23f233ac3bd9de2fd9`
- **Transcript**: Retained privately by the author.
- **Prompt**:
  > Implement plan 31, SDDM PAM keyring cleanup.
- **Key decisions**:
  - Package a root-only transaction helper with the native integration, bound
    to the exact two PAM baseline hashes and three expected hook lines.
  - Keep the consumer mirrors byte-for-byte equal to the transformed files;
    preserve KWallet and authentication behavior.
  - Capture both originals before apply and save current bytes before an
    inverse; make apply and restore retryable after interruption.
  - Leave fresh login, Secret Service and credential proof for Fred's exact
    candidate Test.
- **Verification**:
  - Nine transaction fixture tests pass, covering hash drift, exact edits,
    active SDDM refusal, metadata, retries and later-write preservation.
  - Ten native staging tests pass, including the packaged helper payload.
  - The consumer PAM mirrors match the exact transformed live files.
  - Full assembly build and physical login evidence remain pending.
