# Session: 2026-10-08 — Shared compositor protocol layer, milestone A

- **CLI Tool**: Codex CLI (`codex`) `0.161.0`, dynamically checked.
- **Model**: `gpt-6.1-sol`, verified from the runtime transcript.
- **Authorship**: Fred directed selection of useful available work. Codex selected
  the accepted protocol-layer development milestone and wrote the implementation,
  fixtures, proof runner and delivery record.
- **Commit**: The commit introducing this record contains the implementation.
- **Product version**: Unchanged at accepted 0.3.3; development only.
- **Transcript**: Retained privately by the author.

## Guiding prompt

> Another codex session is working follow ups from a claude session, but you should be able to take a look at the tamlinux plan and find something useful to do. Choose the highest-impact task you can work on next, and start on it now.

## Decisions and implementation

Implemented milestone A of the accepted
[compositor protocol layer plan](../plans/compositor-protocol-layer.md), which
is scheduled alongside settings migration and deploys nothing. Used the free
existing checkout; the concurrent session's reserved files were left alone.

`ProtocolState.qml` binds the standard workspace and output models and
observes nested changes through a snapshot binding. Numeric workspace names
identify facade workspaces; opaque protocol ids do not. Ambiguous projection
ownership and malformed/bounded lists are rejected for authoritative use.
Activation respects the compositor's capabilities and handles active
workspaces that cannot activate without sending an unnecessary request.

Added shared snapshot composition and bounded comparison helpers. Hyprland's
IPC publication remains unchanged; a disabled-by-default development flag
loads protocol facts only for an isolated comparison. Sway's development
adapter consumes the shared layer reactively; fixture mode stays independent
of the real protocol source. Global focus, window membership, keyboard,
bindings, special workspaces and display power stay compositor-specific.

The dedicated live proof has an isolated home, creates no windows, sends no
actions, and terminates within 15 seconds. No shell deployment, user settings,
fault trials, version bump or public push was performed.

## Verification

- Checked the installed Quickshell 0.3.1 QML type descriptions for the workspace,
  projection, capability and screen APIs.
- 398 desktop tests passed, including offscreen execution of the actual QML
  bindings with mutable fixtures: late discovery, groups, active workspace,
  urgency/capabilities, workspace/group movement, nested projection changes,
  output removal/return, geometry, ambiguous ownership, bounds, snapshot merge
  and difference detection.
- Isolated live proof matched IPC on three outputs and four workspaces.
- Existing Sway fixture proof passed, with actions recorded rather than sent.
- No physical lifecycle event testing or daily shadow acceptance; those remain
  later milestones under the accepted schedule.
