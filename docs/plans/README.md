# Development plans

These plans track work being developed in Tamlinux. A plan is a design for
review, not an installed component or a promise that a feature already works.
The [project README](../../README.md) describes the current released state.

| Work | Status | Next step |
| :-- | :-- | :-- |
| [Base operating system](base-operating-system.md) | Void first, antiX Core fallback decided 2026-10-03 | Prove the runit/Btrfs pilot and compare musl/glibc. |
| [Desktop decoupling](desktop-decoupling.md) | Steps 1–3 checked 2026-10-03 (shell, host contract, compositor contract); still Develop | Step 4: full shared UI closure and the eight rewritten plugins (0.1). |
| [Installation framework](installation-framework.md) | Updated 2026-10-03: workstation package on existing distributions first (Nix flake + host adapter), then Void (native `xbps-src`); antiX Core fallback | Build the inspect/plan/apply/verify framework with an Arch profile; select pilot hardware in parallel. |
| [`tamlinux` command](tamlinux-command.md) | First slice and first-use welcome approved, 2026-09-23 | Implement the command skeleton and minimal offline guide. |

The delivery order is: describe the current system; decouple dependencies
top-down on the existing Omarchy base; package the result as one workstation
package and install it on Fred's Arch workstation, removing Omarchy and
Hyprland (1.0.0); install it on a second distribution (1.1); then prove the
Void Linux base layer (or antiX Core fallback) on a secondary computer (1.2,
1.3). See [VERSIONING.md](../../VERSIONING.md) for the series.
A plan moves to implementation after its open decisions are resolved. Progress
and evidence are recorded in the matching plan; version changes follow
[VERSIONING.md](../../VERSIONING.md).
