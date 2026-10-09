# Upstream sources and field surveys

`fred.sysinfo` is a Tamlinux hardware telemetry plugin. The current
implementation probes Linux kernel interfaces such as `/proc` and `/sys`,
uses PCI utilities, and follows the Omarchy/Quickshell plugin interface.
[Omarchy](https://github.com/omacom/omarchy), the
[Linux kernel documentation](https://docs.kernel.org/), and the
[Quickshell project](https://quickshell.outfoxxed.me/) are starting references
for those interfaces. The root [README.md](README.md) describes current
behavior and security choices.

No direct code clone is documented here. A requested survey should check
upstream interfaces, forks, and independent telemetry tools for more robust
or efficient designs. Save dated evidence in [upstream/](upstream/) and link
it here. If code is later adapted, record the exact source and license.
