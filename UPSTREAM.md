# Upstream sources and field surveys

Tamlinux 0.x began on [Omarchy](https://github.com/omacom/omarchy). Gate A
closed with released **0.4.8** (2026-10-22): the workstation no longer depends
on Omarchy packages or servers. The current host is Arch Linux with Tamlinux's
own Hyprland/Quickshell desktop (Blue Sparkler 0.5). The public
[README.md](README.md) credits Arch rolling updates, AntiX's hardware
longevity focus, Nix atomic rollbacks, and modern desktop ideas from Wayland,
River, Hyprland, Quickshell, and Omarchy as technical inspirations. These are
distinct kinds of influence: historical base, system building blocks, and
ideas for the future. Neither an inspiration nor a survey finding commits
Tamlinux to adopting a project's code or design without deliberate review.

Current target: **Void Linux with runit and Btrfs**. If Void presents a
showstopper, try **antiX Linux Core with runit**. See the
[base operating system plan](docs/plans/base-operating-system.md). Historical
surveys describe the target in scope when they were conducted.

For a Fred-requested survey that spans the distribution, start here and in
the relevant component repos' `UPSTREAM.md` files. Compare current upstream,
forks, and independent projects; save dated evidence in
[upstream/](upstream/) and link it here. Chosen product work belongs in a
reviewed plan under [docs/plans/](docs/plans/). Record exact code ancestry,
license, and attribution if a later implementation adapts source code.

## Survey records

- [2026-10-03 — compositor](upstream/2026-10-03-compositor.md): a tiling
  Wayland compositor for antiX Core and circa-2006 hardware. Outcome: Sway
  chosen 2026-10-03. Build/delivery route is now evaluated for the Void target.
