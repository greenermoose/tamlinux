# Focus-preserving workspace repair and native logging

- **Date:** 2026-11-11
- **CLI Tool:** Codex CLI 0.167.0
- **Model:** GPT-6.1 Sol (`gpt-6.1-sol`)
- **Transcript:** Retained privately by the author.
- **Scope:** Develop sources only; no installed candidate change.

## Guiding requests

> For [redacted: private plan reference], make side-monitor workspace repair preserve focus, then finish native logging before the physical Dell trial.

> Proceed

> Continue

## Result

`fred.workspaces` 2.0.10 uses a bounded output-targeted adapter operation in
Windows-mode switching, realignment and reconciliation. It orders the origin
first, skips aligned outputs and avoids focus-and-restore fallback. Known
panels retain their geometry and workspace slots through loss/return; new
connectors and independent/split modes retain their existing paths. Failed
side operations leave the desired desktop pending without undoing successful
placement on the active output.

The required native Hyprland action creates/assigns/activates a named normal
workspace without borrowing side-output focus or moving the pointer, and
refuses to move the keyboard owner's active workspace away. The no-focus path
also leaves held mouse buttons alone. The exported logger layout is preserved
for existing native plugins.

A common native emission sink gives compositor errors/warnings and the real
Aquamarine callback matching journal/file payloads, wall and monotonic
emission clocks, severity and component. Normal backend transition records
use a small allowlist. Synchronous commit failures retain output/CRTC/state;
asynchronous worker failures retain output/CRTC/commit/errno. File records are
bounded and promptly flushed. Existing native verbose controls remain separate.

Native source and retirement conditions are in the
[provider contract](../../desktop/native/providers/display/README).
Hyprland fork head is `3b1b3f15`; Aquamarine fork head is `25f5e5d`.
Both are development feature branches, with the existing safety patches intact.

## Verification and limits

- 41 isolated workspace timeline/intent/focus cases, including side failure,
  origin loss, no-op repair, HP return, geometry preservation and supersession.
- 69 existing workspace plugin cases; 24 compositor adapter cases; 35 host
  and metadata cases; two compiled native sink cases; offscreen widget render.
- Full Aquamarine shared-library build and its attachments/output/commitThread
  tests using fakes. The real-window test was not run.
- Syntax checks of the four changed Hyprland translation units. Full native
  Hyprland package linking is still a separate gate.
- Synthetic proof linked to the rebuilt Aquamarine library: five exact
  file/journal payload matches, priorities 3,3,3,6,4, emission clocks and
  PID/boot/journal clock fields retained, debug filtering and live file visibility.
  The 20 ms emission gap remains distinct. No backend, DRM device or compositor
  was opened by the proof. One journal envelope preceded its payload emission
  clock by about 2 microseconds; payload monotonic clocks determine ordering.

The desktop-wide suite needs a stable integration tree and was not run during
concurrent development. Remaining bar ingress-order/retry gates, frozen native
recipe integration, full Hyprland package build, real candidate helper/service
logging, quiet idle and the physical Dell matrix remain open. No native package
installation, session restart, display dispatch, log deletion or stage move
occurred. The implementation does not claim to prove continuous physical
scanout or keyboard focus.
