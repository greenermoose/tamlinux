# Hibernate zram restoration through systemd

- **Date**: 2026-10-17
- **CLI Tool**: Codex CLI `0.163.0`
- **Model**: `gpt-6.1-sol`
- **Commit**: Commit introducing this record (hook, tests and provenance).
- **Transcript**: Retained privately by the author.
- **Guiding prompt**:
  > How can we fix the restoration defect. I don't think it will get better on its own.
- **Observed problem**: Both direct hibernate and the natural 90-minute
  suspend-then-hibernate path resumed, but the post hook's raw swapon raced
  zram-generator teardown and failed after the device lost its swap header.
- **Implementation**:
  - Start defined swap units through the system manager so their setup
    dependency recreates and formats the device before activation.
  - Preserve raw restoration for unmanaged devices and existing retry records.
  - Bound the complete restoration pass to 30 seconds, retaining state on
    query/start failure, timeout, missing swap or priority mismatch. A timed-out
    systemctl client leaves desired activation queued for eventual recovery.
  - Verify actual swap activation and priority before clearing state; refresh
    the native payload hash. Keep the existing drain and sleep policy.
- **Verification**:
  - 22 focused hook tests pass, including real 60-second drain and 30-second
    restoration timeouts, generator header reset, fallback suspend, activation
    failure, missing activation, wrong priority and retry of old state.
  - Eight native-default tests pass, including the exact payload hash.
  - Bash syntax and whitespace checks pass.
- **Delivery boundary**: Source-only correction. A new recorded assembly and
  physical direct-S4/normal-delay trials are required before acceptance. No
  installed hook, swap state or sleep policy was changed in this session.
