# Install and upgrade Tamlinux from local Git clones

**Develop status.** The locked-source build staged 3,280 files in a test
checkout. Installation, upgrade, and rollback passed in a temporary root
with administrator and user-local software present. Read-only native
preflight passed on an Arch workstation with a complete source stage.
The source stage provides `hi` and `start`, and both passed console command
checks in an isolated root without the bundle tools. The installer checks
destination ownership when the target has a Pacman database. An isolated
format-2 migration now retains the exact recovery archive before detach,
preserves the Pacman-owned console launchers, and restores the bundle and
its documentation selection after source rollback. The source desktop
launcher prepares fresh user defaults and checks settings before UWSM.
Isolated migration rewrites the required bundle references and recovers
the prior settings and a launch-ready bundle. Candidate preparation now
binds a committed source delivery to the exact staged manifest and rollback
target in an isolated Arch root. Graphical proof on fresh Arch and an
approved deployment contract remain before live installation.

Target the next unused 0.6.x candidate on Arch/systemd. Run `make` to build the complete workstation from local Git clones, then `make install` to install the staged files directly. Use the same two commands for subsequent upgrades. Keep earlier bundle deliveries usable for recovery.

## Build and install

- Run both targets from the `tamlinux` checkout. Pin `libtam`, `tam`, `tamlinux-tools`, `tam-edit`, and `tam-data` in a component lock. Resolve commits from sibling clones by default, with a clone-directory override. Build from committed snapshots without fetching, switching branches, or changing any supplied clone. Uncommitted component work can stay in those clones during a cultivar upgrade. Report missing commits and build prerequisites before staging.
- Run `make preflight` before building to check the native build tools and Arch runtime providers. Repeat after `make` to compare the verified stage's destinations against the local Pacman file database. Reports identify missing prerequisites by Arch package and show each conflicting path and its owner. `SOURCE_ROOT` selects a test root for runtime and ownership checks while build probes still inspect the build host.
- Run the build unprivileged in private staging. Reuse component Makefiles and product staging for commands, desktop files, services, defaults, documentation, and version notes. Record the product and component commits and the modes and hashes of the staged files. Preserve explicit `PREFIX` and `DESTDIR` staging for component and distribution builds.
- Have `make install` consume the completed stage and reject stale or altered output. Check native runtime prerequisites and destination ownership. Apply system changes through one privileged transaction with the desktop inactive. The cultivar installs under `/usr/`, with commands in `/usr/bin` and versioned runtime data under `/usr/lib/tamlinux/source/`. Apply fresh-user defaults as that user and preserve existing settings.
- Preserve all files that administrators install under `/usr/local/` and all files users install under their own `~/.local/`, including commands, libraries, documentation, and data with the same names as cultivar files. Apply this boundary to installation, migration, upgrade, cleanup, and rollback, including through symlinked destinations. Select cultivar build inputs from the locked sources and declared native providers. Verify installed commands by their absolute system paths so local overrides can coexist. Leave command lookup under the administrator's and each user's control.
- Record active and previous installs in root-owned state. Refuse package-owned, unmanaged, or locally modified file conflicts. Remove obsolete files only when their recorded contents match. Journal changes before applying them and support console recovery without the Git clones. Reinstalling an intact stage is a no-op.

## Migration and candidate delivery

For a clean source install, use the verified delivery and record the
read-only transaction preview for the target. The approved install plan
contains `host` (the system hostname) and `target` (the JSON object from
`transaction.py preview`). It binds the root identity, version, Git
revisions, and manifest digest to a clean starting point.

After approval, place the plan and the stage directory (named by its
manifest digest) side by side under a private root-owned directory. Use
a root-owned operator export of the committed Makefile and installer
modules and invoke `make install SOURCE_PLAN=/absolute/path/to/plan.json`
from that export. Build and inspect the source stage as the regular user
before the privileged install. The installer rechecks the plan, payload,
native prerequisites, package ownership and inactive desktop. A repeat
uses the same stage and can finish its own interrupted transaction.

- On an existing bundle installation, verify the exact live bundle and its recovery material before changing files. Stage the source build first, then use the installed `tam-bundle detach` once, bound to the verified hash. Update only the session references needed to reach the new runtime path and journal their undo. Keep package-owned bootstrap paths available during the transition. Prove recovery can remove the source installation, restore the previous bundle and recover affected settings.
- The isolated-root installer takes the stage and manifest digest with
  `migrate --bundle-archive PATH --bundle-sha256 HEX --bundle-hash sha256:HEX`.
  The retained installer in `var/lib/tamlinux/source/recovery` can run
  `resume` or `rollback-bundle` with the same explicit test root. After
  an upgrade, use source rollback to return to the initial source stage
  before restoring the bundle. Run migration and recovery with the same
  isolated-root owner, home, and XDG roots. The handoff journals changes
  to the Hyprland entry, UWSM environment and Chromium extension flags.
  Rollback keeps later edits in the private `tamlinux/source-session`
  state directory, then binds the user settings to the restored bundle's
  transaction.
- The source launcher checks for an unfinished install, prepares fresh
  defaults as the logged-in user, and reloads the user manager before
  starting UWSM. Retry the launch from the text console if the reload fails.
- Record the locked sources, staged manifest, installed status and rollback target in the existing candidate workflow. Promote the same staged bytes from Test to Run on a host. Each additional host builds the same locked commits and records its manifest before activation. Keep separate candidate, host and privileged-operation approvals.
- For a rehearsal, `make source-delivery` emits the version and Git pins
  from the verified stage for a delivery record. Host preparation checks
  that record against the committed source lock and records the manifest
  digest with the target and recovery baseline. Replanning rechecks the
  stage and target. The source rehearsal exposes preparation and planning.
- Document clone setup, native prerequisites, installation, upgrade and recovery. Update the deployment contract before cutover. The 1.0 GitLab repository split retains its existing schedule.

## Acceptance

- In a temporary root, exercise clean and repeated installs, a two-version upgrade, obsolete-file removal, path conflicts, stale output, concurrent attempts, and interruption during detach and file replacement. Seed `/usr/local/` and two users' `~/.local/` trees with same-name commands, libraries, documentation, and data. Verify that contents, modes, and links survive install, migration, upgrade, and rollback. Reject any destination redirect into those trees. Verify that the cultivar builds and passes its installed checks while local copies shadow command names and component clones contain uncommitted work.
- Prove a clean Arch installation without Nix or the legacy installer in a VM. Separately prove migration from a recorded bundle, legacy recovery, and a subsequent Make-only upgrade. Check console login, desktop start and exit, shell and plugins, version notes, and preservation of settings and locally installed software.
- In the clean graphical session, check the default pointer on the desktop and in an application, then click the version label and confirm it shows the candidate's changes. Run the widget proof with notes produced by the Make build. An inherited theme or a readable notes file alone can hide a regression until first login.

## Workstation rollout

1. **Clean-install pilot.** Prove the clean install on a fresh Arch system. A wipe and fresh Arch install are acceptable for this proof, subject to the separate disk and install approvals. Start from a minimal Arch installation, exercise the prerequisite check, and record exactly what had to be installed before `make` and `make install`. Fix the declared prerequisites if the proof finds a gap.
2. **Upgrade pilot.** Prove the data-preserving transition from the existing bundle while the daily workstation remains available. Check recovery to the prior bundle, the subsequent Make-only upgrade, and preservation of local Tamlinux installs and component work.
3. **Daily workstation.** Upgrade the daily workstation after both pilots pass. Use the proven preserving procedure and verify the installed cultivar, local Tamlinux installs, and developer checkouts.

Record each host's exact source revisions, installed manifest, prerequisite checks, and recovery point before promotion.
