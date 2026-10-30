# Tamlinux version

Shows the running shell's packaged Tamlinux version, such as `Tamlinux 0.4.4a`.
The session launcher reads the version beside its resolved shell payload and
passes it as `TAMLINUX_VERSION`. The label does not use the plugin version,
the development checkout or a newer deployment selected after shell startup.
Missing metadata displays `Tamlinux unknown`.

To label a completed milestone while retaining the exact package identity,
set this widget's `milestoneVersion` setting to its three-part version, such
as `0.4.4`. The bar then shows `Tamlinux 0.4.4` for packages in that series.
The setting does not affect package versions or deployment records, and it
stops applying when another version series is installed. Missing, malformed
or nonmatching settings retain the normal full version label; missing package
metadata still shows `Tamlinux unknown`.

The default center order is indicators (including stay awake), this label,
then `fred.clock`. The clock remains the center anchor. Existing custom bar
layouts can insert `{ "id": "fred.tamversion" }` immediately before the clock.

Hovering over the version label shows a concise, non-interactive system
identity tooltip: the full cultivar name and version, the active Home Manager
generation rollback point, host platform details (distribution, kernel, and
compositor), and the plugin version footer.

Original Tamlinux code, licensed GPL-3.0-or-later under the repository license.
