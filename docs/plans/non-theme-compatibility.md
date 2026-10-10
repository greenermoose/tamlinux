# Tamlinux 0.4.3 — Independent packaged installation

**Status:** Scope settled during review, 2026-10-09. Development continues
2026-10-10: ten desktop helpers now have maintained source and package install
interfaces; notification endpoints and plugin discovery use owned names/sources. Complete assembly construction and clean-host installation proof
remain pending. No new candidate has been installed.

## Outcome

Graft Tamlinux as a desktop environment onto another Linux host. Prove the
first supported installation on a clean Arch/Hyprland machine that has never
had Omarchy; additional host adapters are separate follow-ups.
The selected assembly must supply its own desktop software and configuration,
with independently maintained dependencies. It must bring no active Omarchy
package, command, runtime path, environment variable, UI label or protocol name.
Installation, updates and normal operation must make no request to Omarchy
servers, repositories, registries or package channels. Product software and
defaults come from the maintained Tamlinux GitHub source; standalone utilities
keep their declared Tamlinux utility source owner. Standard Linux/desktop
dependencies come from declared independent host or delivery providers.
Historical provenance, license notices and dated records retain factual names.

This is the acceptance boundary for 0.4.3. Existing hostnames, partition labels,
encrypted-root identifiers and old recovery records are historical machine
identity; renaming them is outside this work. New installations must obtain
machine-specific identifiers from the host rather than inherit them from the
original workstation.

Preserve current desktop behavior and appearance while replacing software
ownership and names. The later Tamarack theme redesign and Sway integration
remain separate work. Preserve workspace placement and compositor layout
semantics; no general capture-coordinate redesign or speculative portability
work is required here. A defect joins the work only with a reproducer and a
specific user impact.

Baseline: product `8056bd9`, assembly `6486037`, accepted for Run with installed
version `0.4.2-d`. The new work changes neither this installation nor the separate
plain 0.4.2 release record.

## Source and package ownership

| Software | Maintained implementation source | Delivery |
| --- | --- | --- |
| Desktop shell, plugins, menus and desktop integration commands | `tamlinux/desktop/` and `tamlinux/commands/` | Product package outputs selected by the exact assembly |
| Standalone reusable utilities | `tamlinux-tools/src/` | Utility package output selected by the assembly |
| Theme/background/font assets, application templates and required integration services | Product-owned resources under `tamlinux/desktop/` and new `tamlinux/system/` integration source | Explicit package outputs and installed manifests |
| Host integration, including privileged service/drop-in and boot support needed on Arch | `tamlinux/system/`, with a documented build/install interface | Native Arch host package from pinned source; delivery recipe records its exact identity |
| Package recipes, dependencies, Nix/Home Manager modules and selected component revisions | `tamlinux-packages` | Builds and assembles the source packages; owns delivery verification |
| User selections and machine identifiers | Consumer configuration | Values passed to packaged software, never a substitute for missing implementation source |

Every renamed software component must have a maintained source, a build/install
interface, a package owner and a recorded replacement for its old callers.
Moving files to a new name without establishing ownership does not satisfy the
requirement. Retain source licenses and ancestry in historical records. Do not
copy personal configuration or credentials into public product defaults.

## Proven dependency inventory

The inspected reference workstation has six packages with inherited names:
`omarchy`, `omarchy-settings`, `omarchy-nvim`, `omarchy-keyring`,
`linux-omarchy` and `linux-omarchy-headers`. None belongs in a new Tamlinux
installation. The reference workstation already runs a stock Arch kernel;
that observation alone does not establish independent boot/update ownership.

| Dependency found in current software | Required replacement |
| --- | --- |
| Menu About/branding, theme and boot actions invoke `omarchy-*` commands | Package maintained product implementations and retarget their callers together; preserve retained functions |
| Shell/menu consumers use the `omarchy` icon font; background/theme consumers read inherited trees | Package owned assets and theme/background support with Tamlinux names; preserve current appearance before later visual redesign |
| Bash and session bootstrap export `OMARCHY_*` or read packaged bootstrap paths | Package owned defaults and environment; fresh login resolves commands without inherited paths or variables |
| Notification writers/readers use inherited wire names | Rename both endpoints in the product packages; preserve validated argv and action behavior |
| Browser callers and native registrations use `com.omarchy.*` | Package both ends as `com.tamlinux.*`; verify real extension IDs, origin permissions and copy/download behavior |
| Settings package supplies system drop-ins, services, session defaults and resources | Classify its file manifest; transfer required behavior to owned host/desktop packages or standard native owners before removal |
| Editor config/bootstrap is supplied by the inherited Neovim package | Package the required editor integration with an independent source; preserve user data and settings |
| Plugin tooling uses the inherited marketplace registry; developer inspection reads the installed inherited version/tree | Use the maintained product catalog and owned provenance or explicit unavailable source; retire inherited network lookups and old-checkout requirements |
| Boot/default configuration and package hooks retain inherited software entry points | Package their maintained replacements and verify generated boot/update behavior; preserve actual machine identifiers |

Package contents, actual readers and effective configuration determine which
parts are required. The settings package has 429 non-directory files, and the
main package has 1,613; these include templates, resources and inactive skeleton
files, not that many independent runtime dependencies. Inspect package scripts
and ownership before building the replacement manifest. Many desktop helper
implementations still live outside the delivered product source, so the clean
installation must also prove their complete packaged command closure. Third-party applications
keep their real upstream identities; confirm independent sources for dependencies
that were previously supplied by the inherited repository.

[Initial command-ownership inventory](evidence/0.4.3-package-closure.json)
records baseline direct shell calls to `tam-theme-payload`,
`tam-notification-send`, `tam-agent` and `tam-menu-timezone` whose implementations
were absent from product package source. The first transfer is now at
[`commands/tam-theme-payload`](../../commands/tam-theme-payload/README.md):
29 theme tests pass, including two path regressions that fail against the prior
helper. The other baseline direct calls now also have product source: notification
sending, agent launching and timezone selection. Their transitive IPC/menu/terminal
and plugin reload helpers are packaged with the same command output.

The notification writer, receiver and reminder writer use `tamlinux-action`,
`tamlinux-glyph` and `tamlinux-exec-argv` together. Ten installed sender/model
checks cover wire receipt, persistence/restored clicks, urgency/replacement IDs
and data that resembles options. Fourteen installed helper-chain checks cover
IPC, menu/timezone behavior, agent launch arguments and scoped cache/restart
operations. The model/source service checks pass. These checks record effectful
boundaries and do not replace a real desktop installation test.

Plugin `list`, `info` and `search` use the catalog included in the command
package. All eight source links point into the maintained product repository;
no inherited marketplace lookup or old registry cache is used. The former
upstream installation comparison reports retirement in favor of product-source
`verify`. Four discovery checks and the existing lifecycle checks pass.
Delivery recipes provide each transferred helper's runtime tools and resolve
helper-to-helper calls from the same command output and paired shell menu output. Quickshell, UWSM/terminal/session
authorization facilities and optional selected-agent adapters still need the
complete host/assembly contract. Theme/assets, broader menu command closure,
settings/editor/native ownership and clean-host proof remain pending.


[Development build and installed-output evidence](evidence/0.4.3-installed-helpers.json)
records a successful command build and Nix installed-component integration check.
Eight probes run the real outputs with isolated home/XDG state and a minimal
PATH, using recorded host IPC and unavailable buses. They exercise packaged
interpreter/tools and helper resolution without activating the desktop. The
build also exposed and repaired the menu's unpatched interpreter and missing
menu-output dependency for agent selection. Baseline version text is retained
in this development snapshot; no letter or assembly has been prepared.

## Delivery sequence

1. **Define the clean-host contract.** Use a standard Arch base and Hyprland
   session, with no inherited distribution packages, repository, keyring or
   checkout. Record the required native host facilities and supplied package
   outputs. Establish an installation smoke environment and a consumer example
   that has no dependency on the reference workstation's configuration.
2. **Own the active desktop software.** Trace keys, menus, shell services,
   application entries and their transitive helpers. Move implementation into
   the appropriate public source owner, retain licenses, and package it.
   Rename active software identifiers and update readers/writers together.
   Supply theme/assets/editor behavior needed for today's desktop; defer visual
   redesign and new compositor abstractions.
3. **Own required host integration.** Build a manifest of necessary system
   files and services from inspected effective behavior. Preserve sleep,
   hibernation, encrypted boot, recovery, PAM and audio behavior. Package root
   integration instead of installing loose files. Keep existing storage UUIDs,
   mapper names and labels on upgrades; new hosts supply their own values.
4. **Build a complete assembly.** Pin exact product, utility and host sources
   and dependencies in delivery definitions. Build packages from those pins.
   Check outputs, generated configuration and runtime resolution for active
   inherited software names and missing helpers. Allocate unused candidate
   letters when assemblies are prepared; no letter is reused.
5. **Prove installation and transition.** Install on the clean host and check
   desktop/login workflows. Before any reference-machine Test, record immutable
   package and mutable-state recovery, boot backups and native ownership.
   Retire old packages only after their required files have maintained owners
   and the removal transaction has been inspected. No recursive dependency
   removal or changing device identity to make an audit pass.

The work may use several Test candidates within 0.4.3. New native/root/boot
integration requires its own exact artifact and recovery record. Test, Run and
Release remain explicit transitions; scope agreement does not activate packages
or request a reboot.

## Acceptance evidence

- The clean host has no installed or required inherited distribution package.
  The assembly brings all required Tamlinux implementation from maintained
  source packages and declares its standard third-party dependencies.
- Installation and package activation succeed using the documented consumer
  example without the reference workstation checkout, personal overrides or
  pre-existing theme/state/browser configuration. Missing prerequisites produce
  a clear result rather than an inherited fallback.
- Observe installation and desktop workflows with inherited domains and
  repositories unavailable. No request or fallback attempts to those services
  occur; plugin discovery and assets come from the maintained product sources.
- Package/output and effective-runtime audits cover executables, services,
  templates, menus, assets, environment, browser registrations and protocol
  identifiers. Every remaining inherited spelling is identified as historical
  provenance/license data or an existing machine identifier; no blanket
  exception hides an active software dependency.
- Verify startup/login, menu navigation and launching, all eight plugins,
  notifications/actions/reminders, editor, theme/background/font behavior,
  screenshots, recording, OCR/QR and browser helpers. Test renamed endpoints
  together. Hardware-only cases remain explicitly pending where unavailable.
- Native ownership and update/remove behavior preserve installed configuration.
  Check fresh boot, generated boot entries, independent kernel/initramfs update,
  fallback and recovery, and sleep/resume for any changed host integration.
  Preserve reference-machine identifiers and user data through rollback.
- Do not claim success from a source string scan or mocked filesystem alone.
  Record exact package/assembly revisions and clean-host installation results.

## Retained capture evidence

[Eleven comparison fixtures](evidence/0.4.3-capture-reproduction.json) reproduce
four disagreements between the region picker and monitor helper: reflected
quarter-turns and floor-versus-round fractional dimensions. They do not prove
that an actual compositor layout or captured image is wrong. The current
physical outputs divide evenly at their selected scales.

Retain that evidence without making a shared geometry API, a mirroring redesign
or a comprehensive image-conversion matrix prerequisites for 0.4.3. Make a
small capture fix only after identifying the authoritative expected result and
specific effect; carry broader compositor reconciliation into the Sway work.
