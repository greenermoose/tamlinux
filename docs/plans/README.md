# Development plans

Tamlinux is an independent, continuing Linux workstation environment. The
package remains `tamlinux`; its terminal command is `tam`. A plan describes
work and acceptance, not an installed component. Current accepted workstation
version: **0.3.3**, the daily Tamlinux bar on Hyprland.

**Sequence revised 2026-10-07:** first prove Tamlinux on Hyprland without
Omarchy, then prove Tamlinux on Sway. Arch stays the workstation base.

| Plan | Current scope and next work |
| --- | --- |
| [Desktop decoupling](desktop-decoupling.md) | 0.4 settings/state and menus, 0.5 themes/fonts/identity, 0.6 native ownership and boot-dependent final removal; independent Hyprland acceptance. |
| [Theme system](theme-system.md) | Chosen Tamarack/Atkinson direction; deterministic owned generation, fonts and visible identity at 0.5. |
| [Compositor protocol layer](compositor-protocol-layer.md) | Shared standard-protocol facts for every adapter; shadow then authoritative on Hyprland when Fred schedules it; Sway adapter rebuilt on it at 0.7.0. |
| [Sway integration](sway-integration.md) | Prepared adapters retained; integration/package 0.7 after 0.6 acceptance, physical daily proof 0.8, Hyprland removal 1.0. |
| [Installation framework](installation-framework.md) | Existing-distribution Nix + native host adapter; bounded inspect/plan/apply/verify for 0.7, using independent component ownership. |
| [`tam` command](tamlinux-command.md) | Approved small offline guide/welcome/explain and installation entry point; name updated 2026-10-07, implementation pending. Supporting work for 0.7. |
| [Base operating system](base-operating-system.md) | Second distribution 1.1, then Void/runit/Btrfs/native-source pilot 1.2 and repeatable activation/terminal profile 1.3; antiX Core fallback if needed. |

Boot work and reliability continue alongside ownership work. Final removal
requires independently maintained kernel/initramfs/boot hooks and tested
encrypted boot, update, fallback/snapshot recovery and sleep/resume. A boot
delay leaves independence pending; it does not move Sway integration ahead.
Existing prototypes, legal attribution and dated records stay as evidence.

The stage meanings and unchanged 0.3.3 version are in
[VERSIONING.md](../../VERSIONING.md). Publication and release remain separate
from local planning and implementation.
