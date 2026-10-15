# Desktop Test c preparation

- **Tool**: Codex CLI `0.162.1`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Prompt** (excerpt):
  > Review Claude’s ProtocolState fix and native-defaults implementation, including D145/D146, package conflicts and recovery coverage. Finish any remaining gaps without duplicating Claude’s work.
  >
  > Do not activate Test, remove packages or change boot without proposing the exact action and receiving my explicit okay.

Claude's polling fix and native/per-user defaults are retained. This change
adds explicit checkpointed conversion for paired faillock/sudo, NSS/resolved
and Docker/resolved settings, and CUPS where installed. It validates all
selected destinations before writing, refuses conflicting administrator
settings, supports interrupted retry, and retains later bytes, modes and
ownership before restoration. It changes no service or package itself.

The existing initializer gains preserving MIME defaults. Its terminal list
already supplies the terminal selection. The native sleep hook skips while
the retained host hook owns the effect, avoiding duplicate sleep actions in
an additive installation. The logind delay inhibitor budget is preserved.

Verification: 557 desktop tests pass with one existing skip, including actual
isolated-root fresh/in-place/conflict/interrupted conversion and later-write
rollback. Socket-using fixtures require execution outside the agent sandbox.
Exact immutable/native/runtime evidence is recorded with the prepared assembly.
No normal-account activation or boot operation is part of this commit.
