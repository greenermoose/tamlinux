# Changelog

All notable changes to `fred.workspaces` (`omarchy-fred-workspaces`) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] (v1.4.0)

### Added
- **Topology-Anchored Workspace Grid ($K=3$)**:
  - Anchored workspace calculations to fixed physical workstation slots (Slot 0 = Left/MSI, Slot 1 = Center/Dell, Slot 2 = Right/HP).
  - Workspace IDs and desktop mappings never re-index when displays drop or reconnect.
  - Intermediate and endpoint monitors drop gracefully: missing slot workspaces remain parked in Hyprland without disturbing existing windows or spawning phantom desktops.
- **Automatic Geometric Gap Compression**:
  - Implemented `ensure_contiguous_layout()` to detect gaps ($X_i > X_{i-1} + W_{i-1}$) when intermediate monitors disconnect.
  - Dynamically repositions downstream displays (e.g. HP moved from $x=3840$ to $x=1280$) so pointer movement across screens is never blocked by Wayland coordinate geometry.
  - Automatically restores canonical monitor coordinates (`monitors.lua`) upon display return.
- **Resilient Two-Stage Switching**:
  - Replaced fatal all-or-nothing assertion crashes with two-stage verification and individual monitor retry fallbacks in `switch_windows`.
  - Guaranteed `desktop-current` recording so user intent is always preserved even during partial hardware lag.
- **Dynamic Hotplug Recovery & Reconcile**:
  - Hooked Hyprland `monitoradded` / `monitorremoved` socket2 events in `Workspaces.qml` with a 350ms debounce triggering `omarchy-desktop-mode reconcile`.
  - Returning monitors automatically attach to their slot's active workspace with zero manual intervention.
- **Bar UI Degraded Mode Feedback**:
  - `Workspaces.qml` evaluates under fixed `topologySize` ($K=3$).
  - Bar buttons 1–5 remain fixed across all bars.
  - Added degraded display state indication (`[X/Y Displays Active]`) to the mode button tooltip.

## [1.3.1] - 2026-09-15

### Fixed
- **Center Monitor Indicator Desync & Atomic State Watch**:
  - Enabled `atomicWrites: true` on `modeFile` and `monitorsFile` `FileView` watchers in `Workspaces.qml` to prevent orphaned inotify watches across atomic file replacements.
  - Fixed monitor coordinate extraction in `quickshellMonitorNames()` and `isLeftMonitor()` to read `monitor.x` / `monitor.y`.
  - Added proactive `loadMonitors()` call on status process finish.
  - Bound `workspaceIds()` to `windowsRevision` for reactive workspace rendering.

## [1.3.0] - 2026-09-15

### Added
- **Dynamic All-Monitor Windows Sets**:
  - Sized desktop sets dynamically to the number of active monitors, replacing 2-monitor hardcoding with multi-display set synchronization.
  - Verified batch dispatch and complete-set bar focus, occupancy, and tooltip presentation.

## [1.2.1] - 2026-09-13

### Security
- **Marketplace Verification**:
  - Verified and listed on the official [Omarchy Plugin Marketplace](https://github.com/omacom/omarchy-plugin-marketplace) with an automated security baseline rating of **Passed**.

## [1.2.0] - 2026-09-12

### Security
- **Strict Configuration & Process Hardening**:
  - Replaced shell execution and arbitrary sourcing of `desktop-mode.conf` with a strict key-value parser and monitor name validation regex.
  - Enforced closed process execution environments, argument parameterization, bounded outputs, and atomic state writes.

## [1.1.0] - 2026-09-12

### Added
- **`clonedFrom` Integration & Upstream Provenance**:
  - Declared `omarchy.clonedFrom: "omarchy.workspaces"` for clean in-place replacement and automatic rollback.
  - Documented upstream diff command and provenance in `UPSTREAM.md`.

## [1.0.0] - 2026-09-11

### Added
- **Initial Release**:
  - Dynamic workspace indicator bar widget and multi-monitor desktop switcher (`omarchy`, `mac`, `windows` modes).
