# Development plans

Tamlinux is an independent, continuing Linux workstation environment. The
package remains `tamlinux`; its terminal command is `tam`. A plan describes
work and acceptance, not an installed component. **Reviewed 2026-10-13:**
accepted Run is **0.4.2-d**, product `8056bd9`, delivery `6486037`;
0.4.1 is the latest release. **0.4.3 remains in Develop.** Helper, capture and
theme/font/assets transfers are implemented, but a complete independent
assembly, effective fresh-login defaults, migration/recovery and clean-host
proof remain. [Current implementation and acceptance](non-theme-compatibility.md).
Protocol IPC remains authoritative; historical shadow disagreements/gaps are
unresolved. No new continuous observation period is established here.

**Sequence revised 2026-10-07:** first prove Tamlinux on Hyprland without
Omarchy, then prove Tamlinux on Sway. Arch stays the workstation base.

| Plan | Current scope and next work |
| --- | --- |
| [Targeted text-console monitors](console-monitor-control.md) | Design approved by Fred, 2026-10-25, targeting 0.5.5: C command and optional modular display library, sustained per-output blanking with a usable shell, recovery and resource measurements. Next: C feasibility slice. |
| [Tamlinux 0.5.5 delivery](../../../tamlinux-packages/docs/plans/0.5.5.md) | Plan approved by Fred, 2026-10-25: matching runtime/development libraries, native monitor control and Fred's pending tam command/corpus selection; separate Test, Run and Release gates. |
| [0.4.4h readiness](0.4.4h-readiness.md) | Develop preparation complete; exact Test proposal ready for review. Generator-aware hibernate restoration, bounded recovery notice integration, tam command 0.30.0 / corpus 0.31.0. Installation and physical acceptance require separate instruction. |
| [Desktop decoupling](desktop-decoupling.md) | 0.4.3 independent packaged Arch/Hyprland desktop, including required session/native/boot ownership and recovery; independent Hyprland acceptance. |
| [Theme system](theme-system.md) | Retained theme/fonts/assets ownership is required in 0.4.3; Tamarack/Atkinson visual redesign follows at 0.5. |
| [Compositor protocol layer](compositor-protocol-layer.md) | Milestone B accepted at 0.4.1; historical differences/gaps remain authority blockers. Sway adapter integration remains 0.7.0. |
| [Sway integration](sway-integration.md) | Prepared adapters retained; integration/package 0.7 after 0.6 acceptance, physical daily proof 0.8, Hyprland removal 1.0. |
| [Installation framework](installation-framework.md) | Clean Arch/Hyprland package/native adapter and repeatable provisioning proof in 0.4.3; general portable installer and Sway integration remain later. |
| [`tam` command](tamlinux-command.md) | Milestones 1–5 implemented at tam 0.9.1; corpus search, content depth, read-only self-inspection and grounded ask remain in the component plan. Inherited host-profile recognition needs 0.4.3 classification/cutover. |
| [Base operating system](base-operating-system.md) | Second distribution 1.1, then Void/runit/Btrfs/native-source pilot 1.2 and repeatable activation/terminal profile 1.3; antiX Core fallback if needed. |
| [Operating-system horizons](operating-system-horizons.md) | Research only: roles for the Linux and non-Linux systems Tamlinux watches for fixes and ideas, and the Tam 2.0 microkernel exploration (Redox first). Chooses no base and authorizes no migration. |

Boot work and reliability continue alongside ownership work. Final removal
requires independently maintained kernel/initramfs/boot hooks and tested
encrypted boot, update, fallback/snapshot recovery and sleep/resume. A boot
delay leaves independence pending; it does not move Sway integration ahead.
Existing prototypes, legal attribution and dated records stay as evidence.

Product behavior and generic defaults belong here. Reusable Nix modules,
package recipes and exact assemblies belong in `tamlinux-packages`; personal
selections belong in consumer config. The accepted daily consumer uses the
packaged 0.4.2-d assembly. New Develop source needs its own exact delivery
selection and evidence; moving source does not establish runtime parity.

The stage meanings and accepted-step version rules are in
[VERSIONING.md](../../VERSIONING.md). Publication and release remain separate
from local planning and implementation.
