# Session: 2026-10-20 — Retain the stock boot/unlock screen for 0.4

- **CLI Tool**: Codex CLI (`codex`) `0.163.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Initial guiding prompt (excerpt)**:
  > Do what you can to advance Tamlinux 0.4 Incipiens.
- **Decision prompt**:
  > Keep today's screen for 0.4.
- **Implementation**: AI-assisted development directed by Fred.
- **Changes**: Remove the obsolete Unlock menu action, whose native picker,
  set and reset commands were never delivered. Amend the compatibility plan:
  0.4 retains stock Plymouth `bgrt`; boot-theme selection/reset is outside
  this version. Matching consumer picker delivery and its obsolete legacy
  menu action are removed in source. Existing test expectations are reconciled,
  including removal of ten already-obsolete inherited-menu exceptions.
- **Verification**: Nine menu parser/reader tests, eight consumer style
  integration tests and eight stage-boundary tests pass. The merged product
  menu and consumer overrides omit the retired action. Stock `bgrt` and its
  configuration have an independent native owner, inspected before this change.
- **Limits**: Source changes only. No candidate was prepared or activated;
  no theme, boot file, initramfs, encryption setting or installed endpoint was
  changed. The old consumer-installed picker disappears only with a later
  approved activation.
