# Micro configuration migration and recovery

- **CLI Tool:** Codex CLI `0.165.0`
- **Model:** `gpt-6.1-sol`
- **Transcript:** Retained privately by the author.
- **Guiding requests:**

> Cursor is done. Finish up Tamlinux 0.5.7 and get it ready to test.

> Why not just use regular JSON? Why JSON5?

> Prepare 0.5.8 with the recovery and JSON5 fixes

The already recorded 0.5.7 assembly stays unchanged. This follow-up prepares
0.5.8 without activation. Defaults remain ordinary JSON; existing Micro
configurations are validated as JSON5 and edited without discarding comments.
Scoped buffer bindings agree with top-level mouse bindings. Duplicate keys
are an explicit conflict. The assembly supplies the JSON5 dependency.

The finite settings recovery scope now includes Micro bindings, restoring both
original contents and original absence while archiving later writes. Existing
checkpoints made with the previous manifest cannot supply this new coverage.

Validation: 81 migration, application-default and settings-recovery tests pass,
including isolated DBus/dconf recovery, JSON5 comments/trailing commas, scoped
bindings, repeat conversion and byte-for-byte migration rollback.
