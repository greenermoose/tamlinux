# Ecosystem: patched software this plugin relies on

`fred.workspaces` runs on stock Omarchy. Three behaviours it depends on, though,
are only correct with Fred's Hyprland patch set; on stock Hyprland the plugin
still works, but the desktop misbehaves in the ways listed. The patches, their
recipes and their retirement rules are published in
[omarchy-fred-ecosystem](https://github.com/greenermoose/omarchy-fred-ecosystem)
(`ECOSYSTEM.md` there is the full matrix).

| Package | Stock behaviour | With the patch | Where |
|---|---|---|---|
| **hyprland** ≥ 0.56.2 — [`patch/idle-notify-inhibit-unchanged-noop`](https://github.com/greenermoose/Hyprland/tree/patch/idle-notify-inhibit-unchanged-noop) | This plugin's hotplug `reconcile` (and anything else that focuses a window) re-evaluates Hyprland's idle-inhibit state; unchanged or not, Hyprland reset every `ext-idle-notify` timer, so a monitor's routine HPD drop ~7 s after DPMS-off counted as user activity and hypridle never reached its suspend rule (85 blank/resume cycles in one night). | An unchanged inhibit state is a no-op; only input and real inhibitor transitions touch the timers. | [registry entry](https://github.com/greenermoose/omarchy-fred-ecosystem/blob/main/packages/hyprland/README.md) · [compare](https://github.com/hyprwm/Hyprland/compare/v0.56.2...greenermoose:Hyprland:v0.56.2-fred.3) |
| **hyprland** ≥ 0.56.2 — [`patch/monitor-inherit-dpms-on-connect`](https://github.com/greenermoose/Hyprland/tree/patch/monitor-inherit-dpms-on-connect) | A monitor that reconnects while DPMS is off (input auto-scan, ~6 s after blanking) is re-created **lit**; the plugin's `monitoradded` → `reconcile` path then runs on a desktop that should have stayed dark. | The new monitor inherits the compositor-wide DPMS state and stays dark until input; `reconcile` runs on a dark desktop, which — with the patch above — costs nothing. | same entry |
| **hyprland** ≥ 0.56.2 — [`patch/dpms-state-per-monitor`](https://github.com/greenermoose/Hyprland/tree/patch/dpms-state-per-monitor) | Blanking an unused monitor via `dpms-off <monitor>` sets the compositor-wide DPMS flag to false; any subsequent pointer move or keypress on an active monitor wakes every monitor (including the blanked one). Also, an HPD drop and reconnect re-creates the monitor lit. | The compositor-wide DPMS flag is derived from monitor state so input on lit monitors leaves blank monitors dark, and blanked outputs stay dark across reconnects. | same entry |

Nothing else this plugin uses is patched. `omarchy-desktop-mode` needs only
stock `hyprctl`. If you run stock Hyprland and see the idle clock reset on
every hotplug, or an unused monitor wake on any mouse move, this is why; the
fixes live on the fork branches above, built with the recipe in the registry.
