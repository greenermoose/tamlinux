# Retain the d sleep-hook set for the login candidate

- **CLI Tool**: Codex CLI `0.163.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Please continue working toward Tamlinux 0.4.4. Let me know if there are any decisions I need to make.

  > Keep the existing hook for a (recommended)

## Change

The first 0.4.4 candidate tests the greeter, agent skills and manual native
login. Native archive comparison found that the prepared package also added
the newly developed zram-draining hibernate hook. Fred chose to retain the
previous sleep behavior for a. The d package has no zram-draining hook; its
existing unmount hook remains unchanged.

Move the new hook, byte-for-byte and executable, outside the installed
defaults tree into `desktop/native/deferred/`. Keep its actual-hook regression
suite pointed there. Remove its installation manifest entry and correct the
default/changelog descriptions. A later sleep/resume letter selects it with
fresh package, recovery and physical evidence.

No package, sleep setting, login setting or stage reference is activated.

## Verification

- All 14 actual-hook regression cases pass against the preserved deferred hook.
- Nine native staging tests pass with the hook excluded from the installed tree.
- Deferred hook bytes match the prior development source exactly; remaining
  vendor-default bytes and modes match the d product source.
