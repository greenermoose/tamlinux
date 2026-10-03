# Development plans

These plans track work being developed in Tamlinux. A plan is a design for
review, not an installed component or a promise that a feature already works.
The [project README](../../README.md) describes the current released state.

| Work | Status | Next step |
| :-- | :-- | :-- |
| [Base operating system](base-operating-system.md) | Void first, antiX Core fallback decided 2026-10-03 | Prove the runit/Btrfs pilot and compare musl/glibc. |
| [Desktop decoupling](desktop-decoupling.md) | Step 1 accepted on the visible bar, 2026-10-03; still Develop | Step 2: widen the host contract for the other plugins. |
| [Installation framework](installation-framework.md) | Direction updated 2026-10-03; Void + runit + Btrfs first; antiX Core fallback | Use the measured dependency sequence; select pilot hardware and prove the host/session boundary. |
| [`tamlinux` command](tamlinux-command.md) | First slice and first-use welcome approved, 2026-09-23 | Implement the command skeleton and minimal offline guide. |

The initial delivery order is: describe the current system, decouple dependencies
top-down on the existing Omarchy base, prove the Void Linux base layer (or antiX Core fallback) on a
secondary computer, and graduate to Suspra Linux and the Tier 3 Suspra Workstation.
A plan moves to implementation after its open decisions are resolved. Progress
and evidence are recorded in the matching plan; version changes follow
[VERSIONING.md](../../VERSIONING.md).
