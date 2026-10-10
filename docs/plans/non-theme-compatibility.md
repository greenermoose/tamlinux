# Tamlinux 0.4.3 — Independent packaged installation

**Status:** Scope settled during review, 2026-10-09. Development continues
2026-10-10: ten desktop helpers now have maintained source and package install
interfaces; notification endpoints and plugin discovery use owned names/sources. Complete assembly construction and clean-host installation proof
remain pending. No new candidate has been installed.

Delivery now has a [clean Arch/Hyprland contract and output audit](https://github.com/greenermoose/tamlinux-packages/blob/develop/docs/clean-host.md).
Its first five-output inventory identifies unresolved helper references and
inherited runtime identifiers; clean installation remains blocked.

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

The initial host contract is recorded in delivery's
[`contracts/arch-hyprland.json`](https://github.com/greenermoose/tamlinux-packages/blob/develop/contracts/arch-hyprland.json).
It assigns native programs and service-level facilities, declares required
output payloads and leaves source/channel, assets, native integration and actual
installation proof as explicit pending requirements. Its auditor checks only
supplied package outputs, with optional offline host-root inspection; personal
PATH tools cannot satisfy missing implementation. Seventeen regression tests
pass locally and in an isolated Nix check.

The [retained output inventory](https://github.com/greenermoose/tamlinux-packages/blob/develop/docs/evidence/0.4.3-clean-host-audit.json)
covers 212 runtime files in the existing development outputs. It finds 108
unresolved custom-command references and 54 inherited-name locations, including
menu launch/theme/capture/control chains, plugin setters and desktop-mode UI/data.
These are conservative lexical review candidates, not proven runtime dependency
or defect counts. All declared baseline payloads are present and observed
absolute tool names have native owners; that does not close the transitive
command, asset or service requirements. This inventory advances step 1 below;
the complete consumer/session contract and fresh-host smoke environment remain
unfinished. No pins, candidate letters or installed state changed.

The [prioritized implementation order and terminal/editor slice](0.4.3-terminal-editor-closure.md)
now close nine more command interfaces. Nineteen installed-chain regressions and
the Nix build pass, including two regressions that reject the original scripts;
fourteen isolated real-output probes and the Nix installed-component check pass.
The repeated five-output audit has 103 unresolved lexical command findings
(previously 108), no newly unresolved command and 54 inherited-name locations.
Terminal preferences honor XDG config, presentation argv is preserved and the
Kitty/theme readers use owned names. Paired Kitty/theme producers and the full
migration/native/clean-host work remain pending. No candidate or installation
was changed.

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

## Fixed behavior and closure boundary

The behavior baseline is the accepted `0.4.2-d` desktop, its shipped menu,
keybindings, eight plugins and the workflow list in gate I07 below. Preserve
those functions and current appearance while changing software ownership and
names. New features or later changes in the upstream parent do not expand this
version's parity target. Upstream security/compatibility changes enter only
through a demonstrated dependency or defect affecting this baseline; unrelated
parent features stay in later work. This is a fixed acceptance target, not a
permanent freeze on maintaining Tamlinux.

An implementation enters 0.4.3 when an inventoried baseline caller needs it,
when it is a transitive dependency of that caller, or when an independently
reproduced defect prevents installation or a baseline workflow. Every addition
records the caller, retained function, public source owner, installed package
interface, runtime dependencies and verification. Classify each lexical audit
hit first: cache/data names and dormant code are not automatically new commands.
Personal extensions and optional selected applications do not make all software
on the reference workstation a mandatory dependency. Required and optional
capabilities must be declared before the candidate is tested; silent removal of
baseline functions cannot make the closure pass.

## Rename and migration contract

Maintain a per-component cutover table alongside the dependency manifest. Each
row records the old interface, new interface, callers/readers/writers, source and
package owner, data conversion, verification and rollback. These rules govern
the rows; the table must be populated from inspected software before Test:

| Interface class | Cutover rule | Migration and rollback |
| --- | --- | --- |
| UI names, menu/icon/font identities and desktop-mode labels | Owned Tamlinux name; preserve behavior/glyphs/layout. Rename readers and assets together. | Convert saved enum/settings values once; retain source values and test all modes. |
| Commands, services, environment and notification/browser protocol names | Package both endpoints under owned names and retarget every baseline caller. | No inherited runtime alias or fallback in the new desktop. The retained old assembly supplies old interfaces on rollback. |
| User theme/background/font choices, menu selections, plugin settings, reminder/notification state and desktop-mode state | Owned XDG destinations and schema; map equivalent choices without replacing user selections with defaults. | Carry over only to absent destinations, validate contents and preserve originals; report conflicts without overwriting them. |
| Internal compatibility keys or old software paths | Remove from normal runtime after conversion; they are not a blanket naming exception. | If conversion needs an old name, confine it to an explicitly inventoried offline upgrade input/converter, outside the fresh-host runtime audit scope. Retire it after migration. |
| Licenses/provenance and inactive recovery artifacts | Retain factual ancestry, with explicit file/role classification. | Never execute or load them as a normal-runtime fallback. |
| Existing hostname, UUID, mapper and partition identity | Preserve the host's values; new machines supply their own. | No cosmetic device rename; boot/recovery checks use the same real identifiers. |

For the reference-machine upgrade, use the already established carry-over
pattern: absent destination only, validation before use, preserved originals and
idempotent retry. Inventory actual mutable readers/writers and old/new paths;
include application/editor settings, browser registrations and theme selections
as well as the desktop-mode files already migrated. Keep credentials and personal
data out of public defaults/evidence. Missing source files use packaged defaults;
existing destination conflicts, malformed data and partial migration produce a
specific result and never an automatic destructive replacement.

Take a protected mutable-state snapshot and record per-path conversion before
Test. Rollback must retain changes made during Test: export new writes, restore
or reverse-convert compatible data for the old assembly, and preserve incompatible
new data separately with a reported disposition. Restoring an old Home Manager
generation must not silently erase newer settings, reminders or history. Prove
fresh installation separately from in-place upgrade, including conflicting
destinations, interruption/retry and rollback after new writes.

## Reusable clean-host recipe

Delivery must commit a repeatable provisioning/test recipe before claiming a
clean-host pass. Record the Arch ISO/image release, download origin, checksum
and verified signature; architecture; native repository snapshot and exact
package versions/signatures; kernel/firmware and Hyprland/Qt/Quickshell/driver
identities; Nix/Home Manager locks; and the consumer example/recipe digest.
Do not use a moving latest image or mirror as the identity of a test.

Provision a fresh disposable host/image with no inherited distribution package,
keyring/repository, checkout, user state or reference-machine configuration.
Stage native archives and Nix closures from declared independent sources, then
install/activate the desktop with that staged set and external egress disabled.
Record the package database and effective repository configuration before and
after. A reusable image recipe is not the later live-media installer milestone.

Run fresh login and the fixed workflows in an isolated network environment.
Capture DNS and attempted connections, black-hole the inventoried inherited
domains/endpoints, and fail on an attempted lookup/connection even when blocked.
Allow other traffic only through a declared workflow allowlist and record it;
disable general egress for installation/offline workflows. Review literals and
configured endpoints too, so a direct-IP request cannot evade a domain denylist.
Monitoring must cover the session, helpers, applications and native services
used by those workflows; absence of a successful connection alone is no proof.

Reset to the recorded empty image for repeat runs. A VM/headless pass establishes
only the cases it exercises; supported physical graphics, sleep/resume, display
and capture cases still require their declared hardware evidence. A container or
the existing workstation cannot substitute for clean graphical-host proof.
The recipe, independent native source selection and actual host run are not yet
implemented; the initial delivery contract and static audit are preparatory work.

## Exact artifacts, promotion and recovery

For each unused `0.4.3-<letter>` candidate, record one artifact tuple:

1. Product revision/version and revisions of `tam`, `libtam`, `tamlinux-tools`
   and every maintained native integration source.
2. Delivery revision, lock digest, build/recipe/dependency identities, all Nix
   output paths/closure identities and native package archives/checksums.
3. Host-image/repository identity, independent provider/signature manifest,
   consumer recipe digest and selected plugins/capabilities.
4. Activation generation, resolved runtime endpoints, native installed ownership
   and changed root/service/boot files.
5. Prior exact assembly/generation and native archives; protected boot/config
   backups; mutable-state snapshot/conversion record; and rollback/retry results.
6. Independence gate result and referenced evidence digests bound to this tuple.

Compute the selection digest from the immutable source/build/host/consumer and
prepared recovery identities before running checks. Activation observations and
gate results are attached evidence referring to that digest, outside the identity
hash; a result must not recursively hash itself. Compare observed generation,
endpoints and native state against the selected artifacts before accepting it.

Private user data, raw environment and boot/credential backups remain protected;
public evidence contains sanitized identities and outcomes. Changing source,
dependencies, recipes, capabilities or runtime payloads creates a new candidate
and invalidates the prior gate result. No prepared letter is reused.
On explicit Test, promote/build/install the exact recorded candidate. On explicit
Run, promote and use the same tested artifacts and managed endpoints. Release
remains a separate explicit instruction after acceptance. Native/root migration
and rollback are part of this record, not implied by Home Manager alone.

## Independence gate — finite required checks

Delivery will emit a versioned, machine-readable gate result with exactly the
following required IDs, the artifact-tuple digest, runner identities, outcomes,
evidence paths/digests and declared capability matrix. Overall pass requires
every ID to pass with valid evidence for the same tuple. Missing evidence,
unrun/blocked checks, unexpected IDs used as substitutes or a changed tuple fail
closed. Required hardware cases stay pending until exercised. Optional capability
exclusions must be declared in the tuple before the run and include the expected
unavailable behavior; they cannot be invented to excuse a failed baseline case.

| ID | Required pass condition | Evidence/check owner |
| --- | --- | --- |
| I01 — Artifact/source identity | Built and installed outputs/native packages equal the exact tuple; required implementation and independent provider origins/signatures are recorded. | Delivery package/closure and native ownership checks. |
| I02 — Clean host/native ownership | Fresh host package DB and effective repo/keyring configuration contain no inherited package/channel; required settings/services/hooks have declared owners. | Provisioning recipe and native manifest audit. |
| I03 — Delivered software audit | Binaries, QML/helpers, menus/templates/assets, registrations and generated config have no active inherited command/path/font/UI/environment/protocol/domain identifiers or missing baseline helper chain. | Delivery static/output checks plus component closure tests. |
| I04 — Effective login/runtime | Fresh login environment, loaded QML/font/assets, unit definitions, command resolution and browser/notification endpoints satisfy the owned interfaces without personal PATH/state or old fallbacks. | Clean graphical session runtime collector and endpoint/workflow checks. |
| I05 — Network independence | Install/offline work succeeds from staged independent artifacts; required workflow observation records zero attempted inherited DNS/endpoint/repository requests, including blocked attempts. | Isolated network recipe/logs and connection/DNS audit. |
| I06 — Data migration | Fresh defaults and in-place conversion both pass, preserve originals/selections, handle conflicts and interruption idempotently, and keep new writes recoverable through rollback. | Migration manifest and fresh/upgrade/rollback tests. |
| I07 — Fixed behavior/appearance | Startup/login, full baseline menu/launches, all eight plugins, notifications/actions/reminders, editor, theme/background/fonts, browser helpers, screenshot/recording/OCR/QR, panels and authorization/portals pass their declared cases. | Component tests and clean-host workflow/visual evidence, with relevant physical cases. |
| I08 — Native update/recovery | Changed native/root integration preserves real IDs and proves boot, kernel/initramfs update, fallback, recovery and sleep/resume; inspected old-package removal has ready replacements. | Native/boot transaction and physical recovery checks. |
| I09 — Promotion/rollback | Exact old/new artifacts and mutable recovery exist; Test installation and rollback resolve the recorded packages through the same endpoints and preserve post-migration writes. | Deployment/recovery verification and reference-machine Test evidence. |

Use an explicit denylist seeded with inherited package/command names, active path
and environment prefixes, font/UI/protocol/browser identities, known domains,
repo/keyring/channel definitions and configured endpoints. Extend it when the
inventory finds another spelling. Classify permissible ancestry/recovery files
and host identifiers by exact file and role; no blanket substring suppression,
whole-directory runtime exception or alias allowance. A static denylist alone
cannot pass I04/I05/I07. The new output auditor supports part of I03; it does not
implement or pass this complete gate. Gate aggregation and runtime collectors
remain delivery work.

I03 includes compiled payload string/byte inspection and declared shared-library
dependencies (for example, `readelf` metadata), and resolved QML imports/modules.
Skipping a binary because it is not UTF-8 cannot count as a passed binary audit.
The current text auditor does not perform those compiled/library checks.

Source/build/output and clean-host checks precede reference-machine Test. I06,
I08 and I09 also require the actual in-place upgrade/native recovery results
where relevant. The full gate must pass before proposing Run/0.4.3 completion;
it does not itself authorize Test, package removal, Run or Release.

The following evidence details clarify those nine checks rather than add an
unbounded second acceptance list:

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
small capture fix only when its issue record includes a failing baseline
workflow, an authoritative expected compositor/image result, an original-code
reproducer and a bounded consumer change. The reproducer must fail before and
pass after; retained capture cases and affected physical scale/transform cases
must pass without changing compositor layout authority. Synthetic disagreement
without demonstrated workflow impact does not meet this gate. A change needing
a shared geometry redesign, new compositor contract or unbounded transform
matrix stays in the later Sway/capture work; scope changes need explicit review.
