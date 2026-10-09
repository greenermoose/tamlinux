# Development plans

Tamlinux is an independent, continuing Linux workstation environment. The
package remains `tamlinux`; its terminal command is `tam`. A plan describes
work and acceptance, not an installed component. Current accepted workstation
version: **0.4.0**, non-theme storage and a shared key/bar helper on the daily
Tamlinux desktop on Hyprland. The 0.4.1 shadow Test was interrupted, then restored and verified on
2026-10-09. Fresh comparisons agree; historical disagreements/gaps remain
authority blockers. Fred acceptance is pending; no continuous period is claimed.

**Sequence revised 2026-10-07:** first prove Tamlinux on Hyprland without
Omarchy, then prove Tamlinux on Sway. Arch stays the workstation base.

| Plan | Current scope and next work |
| --- | --- |
| [Desktop decoupling](desktop-decoupling.md) | 0.4 settings/state and menus, 0.5 themes/fonts/identity, 0.6 native ownership and boot-dependent final removal; independent Hyprland acceptance. |
| [Theme system](theme-system.md) | Chosen Tamarack/Atkinson direction; deterministic owned generation, fonts and visible identity at 0.5. |
| [Compositor protocol layer](compositor-protocol-layer.md) | Milestone B restored and verified; 0.4.1 acceptance pending. Historical differences/gaps need investigation. Authority requires a continuous period and event coverage; Sway adapter rebuilt on it at 0.7.0. |
| [Sway integration](sway-integration.md) | Prepared adapters retained; integration/package 0.7 after 0.6 acceptance, physical daily proof 0.8, Hyprland removal 1.0. |
| [Installation framework](installation-framework.md) | Existing-distribution Nix + native host adapter; bounded inspect/plan/apply/verify for 0.7, using independent component ownership. |
| [`tam` command](tamlinux-command.md) | Foundation and offline browse implemented in the command repository; further work remains there. Orientation/explanation/installation remain future work. Supporting work for 0.7. |
| [Base operating system](base-operating-system.md) | Second distribution 1.1, then Void/runit/Btrfs/native-source pilot 1.2 and repeatable activation/terminal profile 1.3; antiX Core fallback if needed. |

Boot work and reliability continue alongside ownership work. Final removal
requires independently maintained kernel/initramfs/boot hooks and tested
encrypted boot, update, fallback/snapshot recovery and sleep/resume. A boot
delay leaves independence pending; it does not move Sway integration ahead.
Existing prototypes, legal attribution and dated records stay as evidence.

Product behavior and generic defaults belong here. Reusable Nix modules,
package recipes and exact assemblies belong in `tamlinux-packages`; personal
selections belong in consumer config. The guarded first consumer is active in restored Test.
Consolidated plugin source must be reconciled with tested deployed payloads
before delivery selection; moving source does not establish runtime parity.

The stage meanings and accepted-step version rules are in
[VERSIONING.md](../../VERSIONING.md). Publication and release remain separate
from local planning and implementation.
