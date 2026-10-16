# Tamlinux version

Shows the running shell's packaged Tamlinux version, such as `Tamlinux 0.4.4a`.
The session launcher reads the version beside its resolved shell payload and
passes it as `TAMLINUX_VERSION`. The label does not use the plugin version,
the development checkout or a newer deployment selected after shell startup.
Missing metadata displays `Tamlinux unknown`.

The default center order is indicators (including stay awake), this label,
then `fred.clock`. The clock remains the center anchor. Existing custom bar
layouts can insert `{ "id": "fred.tamversion" }` immediately before the clock.

Original Tamlinux code, licensed GPL-3.0-or-later under the repository license.
