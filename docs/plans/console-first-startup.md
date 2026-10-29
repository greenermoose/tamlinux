# Text boot, terminal work, desktop on request

Status: approved by Fred, 2026-10-23; implementation in Develop.

2026-10-29: The developer requested concise pre-login guidance to `hi` (an
alias for `tam hi`) and `tam-desktop`, and visible boot logging that explains
what commands are running. The packaged welcome text and Bash alias are in
development. Normal progress is retained; command-level visibility still
needs an implementation and physical verification. Changes to installed boot
or login configuration require their own recorded rollback and approval.

The explicit launcher and console guard are implemented. Focused session
tests include a real pseudo-terminal: suspension keys cannot expose the
parent shell, queued input is discarded, and the console stays held through
unknown cleanup status. This is development evidence; physical VT switching,
locking, desktop exit/relaunch and text boot remain unproven.

Review boundary: use the selected minimal root-stock and `tam-nut`; do not
redesign upstream boot media, firmware or the host's boot-selection chain.
The managed text-boot path begins after selecting Tamlinux. Prove the change
on the first workstation before trying it on the second machine.

## Intended experience

Every Tamlinux machine boots through a visible text sequence to a text login.
Show normal kernel, initramfs, disk-unlock and service-startup progress from
the earliest point the operating system controls. Display errors and failed
services. Remove graphical boot presentation, splash software, graphical
login managers and session choosers from the product and its installation.

After signing in, the user can run `tam`, terminal tools and terminal agents
without starting graphics. Proposed command: `tam-desktop`. It starts the
installed Tamlinux Hyprland desktop directly. Closing the desktop returns to
a usable text terminal. Another virtual console remains available throughout.

Ordinary text-login authentication remains in place. Encrypted disks unlock
through a text prompt. Neither login nor shell startup launches graphics.
There is no decorative replacement for the removed boot and login screens.

## Design

### 1. Make text startup the installation default

Use the system's `multi-user.target` as the default and provide a getty on
VT1. Ensure a second text console is available. Audit enablement links and
dependencies so no display manager starts through another target or service.
Remove SDDM dependencies, greeter assets, vendor settings, session-choice
registration and automatic-login setup from current packaging and provisioning.
Retire the SDDM-specific login/PAM transaction from the new installation path.
Preserve historical evidence as history, not as an active installation recipe.

Remove Plymouth, its themes, splash hooks and splash-only tooling from
Tamlinux's selected package set and boot configuration. Existing installations
need a dependency-reviewed native package removal after their text boot path
is prepared. Merely disabling the software does not complete this change.
Retain libraries and GPU drivers used by the optional desktop and by the
Linux text console; they are not boot artwork or login managers.

### 2. Show normal boot progress

Remove `splash`, `quiet`, `loglevel=0`, `systemd.show_status=false`,
`rd.udev.log_level=0` and cursor-hiding settings from the effective generated
boot command line. Enable normal kernel console output and explicit systemd
startup status where systemd runs. Inspect the actual initramfs implementation
before choosing its settings; a BusyBox initramfs and a systemd initramfs have
different unlock hooks and output controls. Do not enable global debug logging.

Keep the boot menu and recovery entries readable in text mode. Remove
OS-supplied backgrounds, logos and UKI splash images; ensure generation tools
and subsequent kernel updates do not restore them. Preserve input drivers,
keymap/font support, encrypted root, resume and snapshot recovery. Rebuild and
inspect the generated images; editing a source setting alone proves nothing.

Do not add `nomodeset` or remove KMS solely to avoid pictures: a framebuffer
can render text, and readable early consoles and the optional desktop still
need working display drivers. Check external and built-in displays physically.
Any picture produced by firmware before the OS starts requires a separate,
machine-specific firmware setting and approval; Tamlinux cannot universally
override firmware presentation. Record that earliest controllable boundary.

### 3. Start the installed desktop explicitly

Add a documented `tam-desktop` command in the public product and deliver it
through the package assembly. Reuse the owned Hyprland/UWSM session and its
immutable generation, theme initialization and session initialization.
Do not invoke a display manager, desktop selector or checkout executable.

The existing launcher runs `uwsm start` without overriding its wait for the
system's `graphical.target`. Installed UWSM defaults to a 60-second wait and
then a further five-second warning delay. Explicit console launch must use
the supported no-wait behavior (`uwsm start -g -1` in the inspected provider)
and must not activate the system graphical target. The system target and the
user's `graphical-session.target` are separate: desktop services may follow
the latter only while graphics is requested.

Validate a local foreground console, an available user bus and absence of an
existing graphical session before initialization. Fail promptly on duplicate,
remote, unsupported or broken-session launches and leave the terminal usable.
Do not use `uwsm select`, `start default`, or unmodified profile examples:
they can introduce selection, automatic launch or a graphical-target wait.

Keep the login shell when a desktop command is run, and verify UWSM shutdown,
VT return and environment cleanup on normal exit and failed startup. Check
that switching from the desktop to a VT cannot expose an unlocked underlying
authenticated shell; settle the shell/VT-lock arrangement in implementation
before calling this path ready for Test. Protecting that console must not
add a graphical login requirement to boot.

The launcher holds the foreground console job until UWSM exits and both
graphical units and the compositor have stopped. It disables terminal signal
keys and echo while holding the console, ignores job-control suspension,
and disconnects the launcher's standard input from the console. Before
returning to the original shell it flushes queued input and restores terminal
settings. External termination requests UWSM shutdown; an unknown shutdown
state keeps the console held and directs recovery to another VT. Normal
desktop use blocks on UWSM without a periodic polling job. This protects
against keyboard suspension and queued commands; it is not protection against
an already authenticated process deliberately killing the guard.

Audit user services so a text login does not start the shell, portals,
graphical agents or desktop autostart processes. Check desktop input, keyring
unlock, polkit, portals, idle/locking and logout in the explicit-launch path;
they currently have graphical-login assumptions that a wrapper alone may miss.

### 4. Provide terminal tools before graphics

Provision `tam`, Claude, Codex, OpenCode, agy, Ollama and their terminal
dependencies and instructions before graphical setup. Use each machine's own
sign-ins. Distinguish a working terminal agent from a GUI-only application
with a command-line launcher; document and resolve any unsupported text-only
interface instead of claiming its executable's presence proves usability.

Ensure a fresh text login receives the installed command paths and guidance.
Keep shell startup bounded: no network probes, agent startup, model loading,
desktop initialization or graphical keyring prompt before a useful prompt.
Ollama's installation does not enable an always-running server or load a model.

## Ownership and implementation slices

1. Product (`tamlinux`): explicit desktop command, session lifecycle checks,
   removal of boot/login presentation and automatic-launch product paths,
   terminal instructions and meaningful launcher tests.
2. Delivery (`tamlinux-packages`): remove SDDM from the native recipe and
   source bundle; remove splash/login providers from selected contracts;
   update fresh-install ordering, session modules, package checks and clean
   install proof. Record exact native and user package identities together.
3. Consumer configuration: stage the host-specific initramfs and bootloader
   settings and reviewed migration/removal steps. Keep disk identifiers and
   credentials private. Apply the same text-first contract to every registered
   machine, including machines still being installed; collect their own proof.

These are development slices, not independently authorized deployments. Plan
approval precedes implementation. A source version is not a prepared candidate.

## Migration and recovery

Before proposing Test, prepare the actual files, native package transaction,
generated-image checks and a short ordered procedure for the exact candidate.
Record one previous Home Manager generation and one pre-change Snapper
snapshot. Keep the accepted recovery anchor and its existing routes until
separately retired; do not ship graphical-login software in the new normal
installation just to keep an old recovery option reachable.

Boot, login and package-removal steps need individual approval. Rebuild usable
text-unlock images before removing a package whose hook they previously used.
Review package dependencies; do not recursively remove shared desktop libraries.
Preserve bootloader/UKI/snapshot update hooks and verify the regenerated paths.
Changing the next-boot default does not require stopping the current desktop.
Do not isolate targets, terminate the live session or reboot as preparation.

Recovery covers native packages and boot artifacts as well as the user
generation. Verify the previous boot route remains usable and the second VT
can recover a failed desktop launch. No workstation installation, reboot or
package removal is authorized by this draft.

## Evidence required

| Trial | Required result |
| --- | --- |
| Package and generated-boot inspection | No selected display manager, greeter, Plymouth, splash artwork, splash hook or automatic graphics startup; normal boot messages are enabled. |
| Clean encrypted install and reboot | Text progress and text unlock lead to VT1 login; keyboard works; no graphical screen or chooser. Test both generated normal and retained recovery paths. |
| Fresh text sign-in | Usable prompt, `tam`, tools and authenticated terminal agents work; no graphics or Ollama server/model starts. |
| Explicit desktop start and exit | One packaged desktop starts without target wait or selector; normal exit and failed initialization return to usable text. Repeat start after exit. |
| Recovery and locking | Another VT works; switching VTs does not expose an unlocked underlying shell; desktop locking, logout and recovery work. |
| Update and rollback | A regenerated boot image retains text progress/unlock; the accepted boot and desktop recovery path remains usable. |
| Physical fleet measurements | Baseline and three cold boots per machine; separately time boot-to-login, successful-sign-in-to-useful-prompt and requested desktop startup. Record credential-entry time separately. |

Use boot IDs and journal time windows rather than copied logs. Record firmware,
loader, kernel/initramfs and userspace timing where available; target completion
does not establish that a login prompt was visible or a desktop was usable.
Investigate the critical path and shell initialization, not just the longest
entry in `systemd-analyze blame`. Preserve fault instrumentation unless its
owner approves a change. Set performance expectations from each host's baseline
and record acceptance after physical trials; make no unsupported speed claim.

## Next actions

1. Deliver the multiple-source settings checkpoint fix through the next
   candidate when Fred requests preparation. Preserve the prepared 0.5.0 and
   0.5.1 assemblies; development fixes do not replace their identities.
2. With that delivered operator, capture fresh preserving user/boot checkpoints
   and a root snapshot, with the required individual approvals.
3. On the exact Test instruction, use the assembly-bound stage runner and
   candidate-bound boot/login/removal steps. Collect physical startup, desktop,
   recovery and timing evidence; development checks pass none of those trials.

References: [systemd targets](https://freedesktop.org/software/systemd/man/latest/systemd.special.html),
[UWSM startup and shell integration](https://github.com/Vladimir-csp/uwsm/blob/master/README.md),
[mkinitcpio configuration](https://man.archlinux.org/man/mkinitcpio.conf.5),
[Plymouth's initramfs role](https://wiki.freedesktop.org/www/Software/Plymouth/).
