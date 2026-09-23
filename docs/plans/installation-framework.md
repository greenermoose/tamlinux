# Installation framework

**Status:** Initial direction reviewed positively by Fred on 2026-09-23;
second-computer and disk choices remain open. No installer has been implemented.

## Goal

Make a fresh computer reproducibly become Tamlinux without copying the state of
one workstation. The first milestone is an installation framework that can say
what it would change, apply the Tamlinux layer, and report what succeeded. A
bootable image and disk installer come after that framework works on a second
computer.

## Recommended base sequence

1. **Current base: Omarchy.** The existing 0.x workstation already runs it.
   Use it to identify and package the Tamlinux layer: user configuration,
   desktop behavior, tools, documentation, and version metadata. This gives us
   a short path to a reproducible first install without rebuilding the OS now.
2. **Next base to prove: NixOS.** Try it on a second computer. Declarative
   system configuration and generation rollback fit the goal of applying a
   reviewed set of changes together. Existing Home Manager work provides a
   starting point for the user layer. NixOS is the preferred experiment, not a
   commitment to migrate the working computer before the pilot succeeds.
3. **Alternative: plain Arch Linux.** Keep the Tamlinux layer separable so it
   could be applied to Arch if NixOS proves unsuitable. Arch is familiar and
   lightweight, but matching NixOS-style rollback and fleet reproducibility
   would require extra machinery. Choose it on evidence from the pilot.

Removing the Omarchy runtime dependency is the criterion for Tamlinux 1.x, as
described in [VERSIONING.md](../../VERSIONING.md). Changing the base name alone
does not meet it: the desktop shell and plugin loading must work without
Omarchy's modules and conventions.

## Layers and ownership

```text
Base OS (Omarchy now; candidate NixOS or Arch later)
  -> system services, boot, graphics, packages
Tamlinux system profile
  -> system policy, required packages, desktop session, version
Tamlinux user profile
  -> Home Manager configuration, commands, shell, documentation
Tamlinux shell and plugins
  -> Hyprland + Quickshell, shared UI, fred.* widgets
Host profile
  -> hardware-specific settings and explicitly local state
```

The install source must state which layer owns every setting. A host profile
contains only values needed for that machine; secrets and observed machine
state stay outside the public install source. Third-party components retain
their own repositories and licenses. The installation manifest pins or records
their source versions, so a result can be reconstructed.

The current `fred.*` widgets use Omarchy's Quickshell `qs.Commons`, `qs.Ui`,
and plugin loader. An independent base needs Tamlinux-owned equivalents before
those widgets can be considered portable. This is an explicit dependency of
the NixOS and plain Arch paths.

## Proposed repository shape

This is the initial target structure, subject to review. The first implementation
should be small and should reuse existing maintained sources rather than copy
their contents into this repository.

```text
tamlinux/
  bin/tamlinux                 # command entry point
  installer/                   # inspect, plan, apply, verify orchestration
  profiles/omarchy/            # current base adapter
  profiles/nixos/              # second-machine pilot, when ready
  manifests/                   # component sources and pinned versions
  knowledge/                   # offline command and onboarding content
  docs/plans/                  # decisions, milestones, and evidence
```

The public manifest should describe the product components. Local machine
configuration is supplied separately at install time. The installer must not
assume every machine has the same monitors, storage layout, or credentials.

## Installation contract

The first command surface is `tamlinux install`:

- `tamlinux install inspect` reports the OS, architecture, current Tamlinux
  version, available package tools, and the profile it can use.
- `tamlinux install plan --profile omarchy` prints the exact intended changes,
  required inputs, source revisions, privileges, and a rollback route. It makes
  no changes.
- `tamlinux install apply --profile omarchy` performs only the reviewed plan,
  with clear checkpoints and a recorded result. A mismatched or stale plan
  requires a new review.
- `tamlinux install verify` checks the installed components, versions, command
  resolution, desktop integration, and any failed or skipped steps.

Use structured step results so the same framework can gain a NixOS adapter.
Each step declares its prerequisites, owner, expected state, action, and
verification. Re-running an already satisfied step must be safe. A failure
stops before later dependent steps and tells the operator how to recover.
The framework must never partition a disk or switch the active OS as a hidden
side effect of `apply`.

For 0.x, system packages remain native Arch packages; user tools can remain
under Home Manager or Mise according to their declared owner. The framework
does not silently transfer package ownership. For a NixOS pilot, the system
profile becomes NixOS configuration and the user profile can still use Home
Manager. A bootable image and storage layout require a separate reviewed plan.

## Milestones

| Milestone | Deliverable | Evidence to record here |
| :-- | :-- | :-- |
| A. Inventory | Component/owner manifest for the current 0.0.1 workstation; portability gaps and required licenses. | Source revision and classification of each component. |
| B. Framework | `inspect`, read-only `plan`, bounded `apply`, and `verify` for the Omarchy profile. | Plan output, applied steps, versions, and recovery path. |
| C. Fresh install | Use the framework on a second computer with a supported base image. | Installation transcript, missing inputs, and any manual steps. |
| D. Independent base | NixOS pilot with Tamlinux-owned shell integration. | Boot, desktop, widgets, rollback, and maintenance observations. |
| E. Delivery | Decide whether an image, guided installer, or both are justified. | Install time, failure recovery, and maintenance cost. |

The daily workstation remains on its working installation while B–D are
developed and checked on a separate computer. A product version changes only
when a reviewed product snapshot is ready; installer iterations do not equal
Home Manager generations.

## Review record and remaining decisions

- **2026-09-23:** Fred reviewed this framework and said the installation
  direction looks good. The proposed base sequence and command contract are
  the starting design for implementation.
- **Open:** Choose the second computer and whether its first pilot may erase
  its disk. Disk layout and migration instructions follow that choice.

## References

- [Omarchy manual](https://omarchy.org/manual/) — current base and desktop stack.
- [NixOS manual: rolling back configuration changes](https://nixos.org/manual/nixos/stable/) — system generations and rollback.
- [Home Manager manual: NixOS module](https://nix-community.github.io/home-manager/installation/nixos.html) — managing user configuration with NixOS.
