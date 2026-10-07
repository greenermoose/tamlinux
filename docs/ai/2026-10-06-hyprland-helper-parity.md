# 2026-10-06 — Offline Hyprland helper counterpart and fixture parity

- **CLI Tool**: Codex CLI (`codex`) `0.160.1`, checked against the live binary.
- **Model**: GPT-6.1 Sol (`gpt-6.1-sol`), verified by the runtime detector.
- **Implementation author**: Codex, directed by Fred.
- **Code commit**: `ca21278`.
- **Stage**: Develop; optional candidate, not loaded by existing helpers.
- **Transcript**: Retained privately by the author.
- **Prompt**:
  > Claude has wrapped up 0.3.2 of tamlinux. It is now working on 0.3.3. Is there anything you can be doing for tamlinux? Coordinate with claude to let it know what you are working on.

## Result

`desktop/shell/host/hyprland_helper_backend.py` builds the same 18 named
workspace/monitor helper operations as the earlier Sway candidate. It reuses
existing bounded Hyprland command builders, preserves explicit Lua and legacy
fallback plans, and never starts a process or writes configuration.

Both adapters produce the same `OutputFacts` for equivalent fixtures. Pixel
mode, scaled and rotated logical geometry, workspace identity, focus, enabled
state and power remain distinct. Observed workspace numbers may exceed the
1–160 dispatch range; named workspaces retain an unknown numeric identity.
Disabled Hyprland rows retain stale values in IPC; the adapter clears their
live geometry, mode, scale and workspace rather than presenting them as active.

Hyprland batch replies use a triple-newline separator. Success requires an
exact `ok` acknowledgement for each planned command. Partial failures keep
their indexes; short or malformed replies fail without replay or inference.
An acknowledgement still requires subsequent state verification by an eventual
executor. Recorded text never counts as successful compositor execution.

## Evidence and limits

Inspected the locally built Hyprland 0.56.2 release source (Arch package
0.56.2-4.1, with the published per-monitor DPMS/idle patches): `src/debug/HyprCtl.cpp`
(`getMonitorData`, `availableModesForOutput`, `dispatchBatch`, `evalRequest`)
and `src/output/Monitor.cpp` (transformed pixel dimensions divided by scale,
then rounded). The [upstream monitor guide](https://wiki.hypr.land/configuring/core/monitors/)
documents monitor enable/disable, power control and transform configuration.

Mirrored-output workspace ownership is explicitly unsupported. The shared
candidate cannot hold known physical dimensions, so they remain unknown even
when Hyprland reports them. Advertised mode strings have already lost precision
through Hyprland formatting; they are observed rounded values and cannot alone
prove a hardware retraining mode. Special-workspace overlays are outside the
common normal-workspace fact model.

This change adds only the backend and two test files. The existing helper
loader, plugins, configuration, versions and daily deployment are unchanged.
The existing Sway candidate and executor remain dependencies. Fixture parity
does not establish live compositor or hardware parity. Helper wiring,
persistence/rollback, a Hyprland executor, and hardware reset evidence remain
0.4.0 integration work.

## Verification

- 27 new tests cover common request boundaries, Lua/fallback construction,
  rotated/scaled geometry, C++ half rounding, named and disabled workspaces,
  partial batch acknowledgements, malicious or malformed data, and capability
  differences. All pass.
- Full desktop regression outside the sandbox: 477 tests, no failures,
  7 intentional skips (6 opt-in private Sway IPC checks and 1 existing skip).
- Initial sandboxed regression run: 477 tests, 12 errors caused by the
  sandbox prohibiting private Unix socket creation, 7 intentional skips.
  The approved rerun outside the sandbox passed.
- No live compositor command was issued by this implementation.

The exact final suite result is also included in the integration handoff.
Shared provenance indexes are reserved by the integration owner and
must be updated before any public push.
