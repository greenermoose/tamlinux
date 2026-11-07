# tam-boot

Status: implemented on `develop` (awaiting packaged assembly delivery).
Command name is `tam-boot`. Startup explainer and diagnostics tool satisfying
0.6 checklist items K60 and K40.

`tam-boot` is a pure C command that analyzes startup timing across boot phases,
distinguishing machine execution time from time spent waiting for user interaction
(such as disk passphrase entry and console login).

## Behaviour

```text
tam-boot [-N] [--json] [--top K]
tam-boot list [--json]
tam-boot --version
tam-boot --help
```

- Explains boot `0` (current boot) or boot `-N` (historical boot).
- Reads boot totals from `journalctl` message IDs / systemd monotonic timestamps.
- Analyzes kernel timeline using `_SOURCE_MONOTONIC_TIMESTAMP`.
- Separates phases into:
  - Machine time: firmware, loader, kernel device initialization, systemd units.
  - Waiting for you: kernel disk unlock gap (LUKS passphrase prompt), login prompt to sign-in.
  - Unexplained gaps: any unexplained delay > 0.3 s in kernel initialization.
- Reports text login (`getty@tty1`) and user session ready (`user@1000.service` reaching `default.target`).

Exit codes: `0` success; `1` CLI usage error; `2` journal records unavailable.

## Data Sources

- `journalctl` filtered output via `tam_exec`.
- Monotonic timestamps for firmware, loader, kernel, and userspace.
- No tracing overhead, no resident daemon, no elevated privileges.

## Delivery

Lives in `commands/tam-boot/`. Discovered automatically by `tamlinux-packages`
when its Makefile exists. Links `libtam` and libc only. Tests use fixture data
(`TAM_BOOT_JOURNAL_FILE`).
