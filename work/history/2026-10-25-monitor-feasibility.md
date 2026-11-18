# Native monitor inspection foundation

- **Date**: 2026-10-25
- **CLI Tool**: Codex CLI `0.164.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted implementation directed by Fred.
- **Commit**: The commit introducing this record contains the product changes.

## Guiding prompt

> Find the plan for tam-monitor and work on improving that command. Ask if you have questions.

## Result

Started the approved C feasibility work with an optional inspection CLI and
modular `libtam-display.a` in the foundation library repository. The prototype
accepts an authorized borrowed DRM descriptor, enumerates connectors/CRTCs/
planes and properties, and analyzes retaining one output. It does not open a
device, acquire master or perform display mutations. Opening a primary device
can implicitly acquire master, so acquisition remains a separate gate. The
Python command remains installed while native ownership/recovery are developed.

## Verification and limits

- Seven native CLI tests and all 25 existing monitor tests pass. Local-socket
  recovery tests require running outside the sandbox. No display is contacted.
- ASan/UBSan-instrumented display objects pass fake-device routing, bounds,
  resource/property/plane churn, interruption, unsupported atomic capability,
  device loss and failure injection at every query. Core/portal tests pass.
- Scratch builds pass explicit-prefix and pkg-config discovery. Manual checks
  confirm no-op stability, relink after archive/header/flag changes and useful
  failure for missing metadata. Core/display install avoids portal dependencies.
- ELF inspection finds libc as the only needed runtime library, with
  `.debug_info` and `.symtab` retained. The unstripped executable is 64,792
  bytes; the display archive is 46,990 bytes on this build. This does not
  establish the resource budget or performance relative to the Python command.

No package pins, candidate versions, installed endpoints, boot/login state or
hardware display state changed. Feasibility still needs authorized VT/device
acquisition, owned framebuffer/blob references, atomic TEST_ONLY/commit,
independent recovery and physical fbcon/standby proof. The full C migration,
TUI and 0.5.5 development-package integration remain open.
