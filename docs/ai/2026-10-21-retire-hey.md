# Session: 2026-10-21 — Retire the inherited HEY integration

- **CLI Tool**: Codex CLI (`codex`) `0.163.0`
- **Model**: `gpt-6.1-sol`
- **Implementation commit**: `701ad68`
- **Transcript**: Retained privately by the author.
- **Guiding prompt**:
  > Do the most important next step to finish Tamlinux 0.4 Incipiens. Try to get something checked off the 0.4-CHECKLIST.
- **Changes**: Implement the accepted retirement plan: remove the handler's
  executable/install interface while retaining its license; remove three
  default shortcuts and their fixture rows; remove forwarding migration.
  A fixed launcher-retirement row accepts only the exact inherited/owned
  template and records an absent post-state. MIME cleanup covers generic and
  desktop-specific user config/data lists, changing only exact HEY tokens.
  Refuse custom launchers, symlinks and owner mismatches. Preserve original
  bytes/modes and later writes through retryable rollback. Refresh the desktop
  database after explicit apply/rollback. Move Zoom tests to its own command.
- **Verification**: 25 migration, 27 settings-recovery, 27 shortcut-viewer
  and three installed Zoom tests pass (82 focused tests). The delivery
  development-snapshot build, installed-component integration and all 81
  isolated package probes pass. They exercise the actual packaged migration,
  MIME preservation, desktop-cache removal/restoration, later-write recovery,
  handler/shortcut absence and Zoom/browser dispatch. A fixture-scope mistake
  in the first package probe run was corrected before the passing build.
- **Limits**: This is Develop work after frozen 0.4.6. No candidate is minted
  or installed. Existing 0.4.6 recovery journals retain their old manifest and
  use their original package for recovery. Controlled consumer-copy cleanup,
  current mutable checkpoints and installed workflow proof belong to the next
  selected candidate's Test. No email replacement is selected.
