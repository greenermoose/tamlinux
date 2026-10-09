# Ecosystem: patched software this plugin relies on

`fred.monitor` runs on stock Omarchy. Two behaviours it depends on, though,
are only fully reliable with Fred's Hyprland / Aquamarine patch set; on stock
packages the plugin works, but display retraining and hotplugging can expose
upstream regressions. The patches, their recipes, and their retirement rules
are published in [ecosystem-fred-tamlinux](https://github.com/greenermoose/ecosystem-fred-tamlinux)
(`ECOSYSTEM.md` there is the full matrix).

| Package | Stock behaviour | With the patch | Where |
|---|---|---|---|
| **aquamarine** ≥ 0.15.0 — [`patch/disable-kms-before-disconnect`](https://github.com/greenermoose/aquamarine/compare/v0.15.0...greenermoose:aquamarine:v0.15.0-fred.1) | A link reset or hotplug that drops a connector tears down the connector status before disabling the KMS pipeline; `CDRMOutput::commitState()` rejects the disable commit ("Cannot commit a disconnected output"), leaving stale CRTCs bound in the kernel. Subsequent atomic commits fail with `EINVAL` across all outputs ("Fault D"). | Issues a blocking disable-only modeset while the output object is still alive, ensuring CRTCs are freed cleanly before connector teardown. | [registry entry](https://github.com/greenermoose/ecosystem-fred-tamlinux/blob/main/packages/aquamarine/README.md) · [compare](https://github.com/greenermoose/aquamarine/compare/v0.15.0...greenermoose:aquamarine:v0.15.0-fred.1) |
| **hyprland** ≥ 0.56.2 — [`patch/monitor-inherit-dpms-on-connect`](https://github.com/greenermoose/Hyprland/tree/patch/monitor-inherit-dpms-on-connect) | A monitor that reconnects or retrains while DPMS is off is re-created **lit**; the shell's monitor-added path then runs on a desktop that should have stayed dark. | The reconnected monitor inherits the compositor-wide DPMS state and stays dark until user input wakes it. | [registry entry](https://github.com/greenermoose/ecosystem-fred-tamlinux/blob/main/packages/hyprland/README.md) · [compare](https://github.com/hyprwm/Hyprland/compare/v0.56.2...greenermoose:Hyprland:v0.56.2-fred.3) |

Nothing else this plugin uses is patched. Helper scripts use standard `hyprctl` and `jq`.
If you run stock packages and see KMS commit failures after retrains or reconnects,
the fixes live on the fork branches above.
