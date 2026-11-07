# tam-boot

Startup explainer and diagnostics tool for Tamlinux (K60, K40).

## Usage

```bash
tam-boot            # Explain current boot
tam-boot -1         # Explain previous boot
tam-boot --json     # Output structured JSON
tam-boot list       # List available boots in the journal
```

## Description

Analyzes boot timing across firmware, loader, kernel, and userspace, distinguishing
machine execution time from user interaction (such as LUKS disk passphrase entry
and text login wait).

Links `libtam` and libc only. No root required.
