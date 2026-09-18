# AI Collaboration Session Archive: `fred.sysinfo`

Chronological records of prompts, tool versions, and architectural decisions for `omarchy-fred-sysinfo`.

---

## Session: 2026-09-13 — Universal Linux Telemetry Probe & System Info Panel (v1.0.0)

- **Date**: 2026-09-13
- **Primary AI Agent**: Antigravity CLI (`agy 1.2.2`)
- **Primary Model**: Gemini 3.8 Flash (High) (`gemini-3.8-flash-high`)
- **Commit**: `0dc548c`
- **Transcript Reference**: `3abd7a9c-0943-487b-84c1-42180771c8ea`
- **Prompts**:
  > "Work on the fred.sysinfo plugin"
  >
  > "Proceed."
  >
  > "Why isn't the displayed panel big enough to show everything? It is clipped and needs scrolling on my system. This makes no sense. Why not just make the panel a little bigger so it doesn't need to scroll?"
  >
  > "Let's stop here and contiue later."

- **Key Decisions & Implementation Notes**:
  - **Kernel Telemetry Architecture (`sysinfo-probe.py`)**: Designed a zero-dependency Python 3 probe script reading raw Linux kernel telemetry directly from `/sys/class/thermal`, `/sys/class/hwmon`, `/sys/devices/system/cpu`, `/proc/stat`, and `/proc/meminfo`. Avoids external CLI dependencies (`sensors`, `lscpu`) for core CPU, memory, and thermal stats.
  - **Hardware Discovery & Sanitization**: Probes connected storage drives via `/sys/block/` and query PCI peripherals (`lspci -mm`) for Ethernet, Wi-Fi, GPU, and audio controllers, with name cleanup for clean UI display.
  - **Secure Subprocess Execution**: Configured Quickshell `Process` launches with a closed environment (`clearEnvironment: true`), bounded `PATH` (`/usr/bin:/usr/local/bin`), and watchdog deadline execution.
  - **Responsive QML Telemetry Panel (`Panel.qml`)**:
    - Designed a two-column layout matching the `fred.*` aesthetic for CPU thermals, memory, storage, and network state.
    - Integrated active power profile toggling using `powerprofilesctl` (Power Saver, Balanced, Performance).
    - Added quick launch button for the system task manager (`btop`).
    - Refined label spacing, text eliding, and dynamic heights in response to Fred's panel sizing feedback.

- **Verification**:
  - Verified real-time telemetry updates against live `/sys` readings and `btop`.
  - Validated plugin schema and manifest conformance with `omarchy plugin validate`.

---

## Session: 2026-09-18 — Multi-Monitor Focus Isolation & Per-Monitor Dismissal (v1.1.0)

- **Date**: 2026-09-18
- **Primary AI Agent**: Antigravity CLI (`agy 1.2.6`)
- **Primary Model**: Gemini 3.8 Flash (High) (`gemini-3.8-flash-high`)
- **Transcript Reference**: `d830646a-a9ee-49d9-ac6a-02934673163e`
- **Prompts**:
  > "Take a new screen of fred.sysinfo on the MSI monitor that is more tightly cropped on the sysinfo display. The current screenshot is too busy. (Not clear what it's showing.) Bump the version, push to GitHub, then make a release of the latest version on GitHub. Write up the submission to omarchy plugin marketplace and let me review. Ask if you have any questions."
  >
  > "Note that when you display (toggle) the fred.sysinfo plugin, this conversation loses focus. I need to close the sysinfo display to use this terminal. Fix that. I want sysinfo to be showing in another monitor and when I'm using a different monitor I don't want to be blocked. The focus should be taken only on the monitor where the sysinfo plugin is showing. So, for example, if you toggle fred.sysinfo to show on the MSI monitor (my left monitor) and I'm typing in a terminal in the center monitor, I should be able to continue to use the terminal in the center monitor even though the sysinfo plugin is displaying in the left monitor. To close the sysinfo plugin, I should need to go into the left monitor and click. Got it?"
  >
  > "Wrong version of agy. Check that and try again with the session file."

- **Key Decisions & Implementation Notes**:
  - **Focus Isolation Architecture (`SysinfoPanel.qml`)**: Replaced stock `KeyboardPanel` with a custom `SysinfoPanel.qml`. Stock `KeyboardPanel` took `WlrKeyboardFocus.Exclusive` for 75ms then `OnDemand`, unconditionally stealing keyboard focus from windows on other monitors when opened. In `SysinfoPanel.qml`, `WlrLayershell.keyboardFocus` evaluates dynamically: only requesting `WlrKeyboardFocus.OnDemand` when the panel's monitor matches `Hyprland.focusedMonitor`; otherwise, `WlrKeyboardFocus.None` is set so background terminals on other monitors retain 100% of their focus.
  - **Removal of Cross-Monitor Dismiss Twins**: Stock `KeyboardPanel` deployed full-screen transparent `Variants` windows over every other monitor to intercept clicks, which broke background window interactivity and closed the panel prematurely. `SysinfoPanel.qml` restricts the dismissal overlay strictly to its own monitor, requiring a click on that monitor to dismiss.
  - **Monitor-Targeted IPC (`SysinfoStore.js`)**: Built a shared `.pragma library` singleton to coordinate panel instances across monitors. Added `openMonitor`, `closeMonitor`, and `toggleMonitor` IPC methods to explicitly summon sysinfo onto named outputs (e.g. `DP-2` / MSI).
  - **Tightly Cropped Screenshot**: Captured live telemetry on the MSI monitor and cropped tightly around the card with clean margins, replacing the previous multi-monitor composite screenshot.

- **Verification**:
  - Opened `fred.sysinfo` on MSI monitor (`DP-2`) while typing in foot terminal on center monitor (`DP-1`); verified zero loss of terminal focus and zero blocking overlays on `DP-1`.
  - Verified outside clicks on `DP-2` cleanly dismiss the panel while clicks on `DP-1` interact directly with windows.
  - Validated plugin schema and manifest conformance with `omarchy plugin validate`.
