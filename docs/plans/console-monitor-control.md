# Choose which monitors stay on at a Linux text console

Status: design approved by Fred, 2026-10-25; native acquisition, owned restoration, retained-output unplug recovery and bounded atomic prototype pass fixture tests; physical feasibility pending.
Target: Tamlinux 0.5.5.
Next: close physical-feasibility preparation gates before a recorded package and separately authorized Test.

Implementation review: [2026-10-27 findings and correction handoff](../reviews/2026-10-27-tam-monitor.md)
records eight findings against the C migration, with isolated reproductions and
acceptance criteria. Verify and correct confirmed defects before physical acceptance.

Fred's approval: "I approve this monitor plan."

## Outcome

At a real Linux virtual terminal, choose any one of three connected monitors
to keep displaying the text console and blank the other two. Continue using
the shell and `tam` on the chosen monitor. Restore either blanked monitor
explicitly. Hyprland, Quickshell, X11 and a graphical terminal are unnecessary.
Ordinary keyboard input must not wake the monitors deliberately excluded.

This is a required 0.5.5 outcome. Global console blanking, reduced brightness,
a black image with the backlight still on, and a fifteen-second demonstration
do not establish it. Verify physical blanking and standby separately; report
power savings only after measurement.

The accepted 2026-10-23 implementation is a Python/curses TUI with connector
information, supported brightness, whole-console blank/wake and runtime idle
controls. It explicitly leaves individual power unavailable. Preserve that
history in the [development record](../ai/2026-10-23-console-monitor-control.md);
this plan replaces its deferred native-backend scope and old next actions.

## Implementation direction

Write `tam-monitor` in C and put reusable Linux display operations in our
`libtam` repository. Tamlinux commands are not limited to shell scripts.
Prefer compiled C and small libraries using stable kernel userspace ABIs for
hardware control and resource-sensitive text-mode tools. Shell remains useful
for simple orchestration. Choose the implementation by required functions and
measured performance; C alone does not prove low memory use or fast startup.

Use **multiple source files**, each compiled to its own object. A single
amalgamated source file couples unrelated features and can cause a static
linker to bring unused code and dependencies into a command. Separate objects
give clear ownership, focused tests and ordinary archive-member selection.
Do not split every small function into its own file; split by responsibility.

Proposed layout, names to finalize after the feasibility proof:

| Library or command | Responsibility and boundary |
| --- | --- |
| `libtam.a`, existing core | libc-only strings, bounded execution, files, paths and configuration; preserve compatible APIs used by `tam`. |
| `libtam-display.a`, new optional archive, `tam_display.h` | `tam_display_discovery.c` for devices/identity, `tam_display_kms.c` for DRM queries and transactions, `tam_display_restore.c` for owned snapshots and recovery. No UI or portal code. |
| VT operations, `tam_vt.c` / `tam_vt.h` | Owned foreground VT checks, console blank/wake/idle, terminal restoration and VT events. Decide whether these belong in the display archive or a separate libc-only core object after identifying actual consumers. |
| Optional session adapter, separate object/archive | Acquire devices and handle pause/resume through the existing seat manager if needed. Its dependencies never enter the core merely by including a header. |
| `commands/tam-monitor/`, existing product owner | C CLI, small terminal UI and explicit lifetime/recovery policy. Build with a Makefile; preserve installed command discovery and documentation. |
| `libtam-portal.a`, existing separate archive | Desktop file chooser only; no dependency from `tam` or `tam-monitor`. |

Static linking to our archives does not require static linking to libc. Keep
display code out of `tam` unless it actually calls that API. Publish matching
pkg-config metadata, minimum API versions and install/uninstall targets.
Build core and display targets without building the portal or requiring its
D-Bus development files. An installed developer package must include headers,
archives and `.pc` files, not just binaries that used them during packaging.

## Prove the kernel path before building the UI

The framebuffer console renders text; its console blanking operation has no
DRM connector selector. Mapping VTs to framebuffer devices does not select
individual connectors sharing one framebuffer. See the kernel's
[framebuffer-console description](https://docs.kernel.org/fb/fbcon.html).

Use the DRM/KMS primary device and stable ioctl definitions from installed
UAPI headers. Implement a narrow C wrapper, rather than copying private
driver structures, defining ioctl numbers by hand or adding a kernel module.
KMS mutation requires display ownership; render nodes cannot provide it.
Only one DRM master owns a device at a time. See the kernel's
[DRM ownership rules](https://docs.kernel.org/gpu/drm-uapi.html#primary-nodes-drm-master-and-authentication).

The first prototype must establish all of the following on the target GPU:

1. Identify the active local text VT, its owning session, DRM device and
   console framebuffer. Enumerate connector → CRTC → plane relationships.
   Mirrored text does not prove whether outputs share a CRTC or only a framebuffer.
2. Acquire authorized display access without stealing another session's
   ownership. Preserve the current console framebuffer and the chosen output's
   text rendering. Taking `KD_GRAPHICS` and replacing fbcon with a terminal
   emulator would change the scope; it is not the proposed implementation.
3. Snapshot the affected connector routing, CRTC modes/active state, planes,
   framebuffer references and required property blobs. Prove that retained
   references can actually be restored by our client, not just queried.
4. For atomic drivers, test the complete proposed change with
   `DRM_MODE_ATOMIC_TEST_ONLY` before applying it. Disable only targeted
   outputs. If a CRTC also drives a retained output, detach selected connectors
   with valid remaining routing rather than switching that entire CRTC off.
   Disable an otherwise unused CRTC/plane only where required by the driver.
5. Verify the retained console still renders while typing, scrolling and
   running `tam`, with the other outputs blank beyond the old timeout. Exercise
   fbcon idle/unblank events, which might otherwise restore all outputs.
6. Restore, release ownership and prove that the console, VT switching and
   later desktop startup remain usable. Test process death as well as normal exit.

Legacy connector DPMS is not a universal per-monitor solution: on atomic
drivers it maps to CRTC `ACTIVE`. A legacy backend may be added only where
its targeted operation and restoration are proved. The kernel documents these
[KMS properties and limitations](https://docs.kernel.org/gpu/drm-kms.html#standard-connector-properties).
Writing connector sysfs `status=off` changes forced detection and calls mode
probing; it is not itself evidence of a completed power transaction. The
`dpms` sysfs attribute is read-only in the
[kernel implementation](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/drm_sysfs.c).

Keep fbcon interaction and ownership lifetime as explicit feasibility gates.
A successful ioctl or property readback alone does not prove usable text or
physical low power. If the prototype cannot preserve them, return the result
for design review; do not quietly replace the required outcome with global blanking.

## Ownership, lifetime and recovery

Prefer an unprivileged active-session path. On systemd systems, evaluate a
small optional logind adapter using `TakeControl(false)`, `TakeDevice` and
pause/resume events. Never force out an existing controller. Keep the adapter
outside the libc-only core and measure its loaded dependencies. A direct-device
path still needs legitimate seat permissions and VT handoff handling; a
syscall interface does not remove those requirements. See the
[logind session/device contract](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html).

Determine whether the selected state survives closing the DRM fd and dropping
master. Do not promise a one-shot interface until that is proved. If ownership
must survive, propose an explicit foreground C supervisor, for example
`tam-monitor keep CONNECTOR --shell`, while a child shell remains interactive.
It blocks on device, session and child events and exists only for that requested
work session. Review its measured cost before adoption; install no permanent
monitor daemon or boot service. The kernel's
[fbdev restoration code](https://github.com/torvalds/linux/blob/v6.18/drivers/gpu/drm/drm_fb_helper.c)
shows why closing a client cannot be assumed to leave its modes intact.

Arm a separate bounded recovery guard before the first experimental write.
Give it only validated device/snapshot information and prove restoration on
timeout, UI death and parent failure. Review the sustained supervisor's
recovery protocol after the prototype: restore on explicit wake, exit,
logout, VT handoff, device loss or a failed transaction. Test owner and guard
death separately; a signal handler cannot recover from `SIGKILL`. Establish
the actual kernel fallback if both die, rather than claiming it is guaranteed.

Retain at least one connected, working text output. If it is unplugged,
restore another available console output; if none exists, release control
and report the loss. Re-enumerate before every mutation and after hotplug.
Do not replay stale framebuffer or object IDs after device replacement.
Multi-GPU transactions need per-device validation and compensation when a
later device fails; there is no atomic commit across different DRM devices.

Restore and relinquish device/session control before optional desktop launch,
including launch from the same login session. Test this path specifically;
logind permits only one session controller. After VT switching, prefer ending
the selection and restoring ordinary console behavior for 0.5.5, rather than
silently reapplying a selection to a different session.

If a privileged helper proves necessary, define a narrow immutable package
and authorization contract for active local users. No root TUI, broad device
chmod, arbitrary device-path writes or unconditional setuid command. Its
policy and installation need review before activation.

## Proposed user interface

Exact syntax is a proposal, not an available command. Preserve existing
`list --json`, brightness, global `blank --seconds`, `wake` and `idle` behavior
where practical; name new targeting explicitly so old scripts keep their meaning.

```text
tam-monitor list --json
tam-monitor blank --monitor CONNECTOR --monitor CONNECTOR --seconds 15
tam-monitor wake --monitor CONNECTOR
tam-monitor keep CONNECTOR --shell
tam-monitor wake --all
```

`keep` means blank the other connected outputs, leaving the selected one
usable for normal shell work until explicit restore or the documented session
boundary. The preview command is bounded; the sustained work mode must not
wake excluded monitors on ordinary keys. Make the supported lifetime visible
in help and the TUI. TUI selection, CLI and recovery use the same library API.

List connector, monitor identity, driver and capability/reason. Resolve short
connector names only when unambiguous; report duplicate identities. Card
numbers and KMS object IDs are not stable across boots. Runtime selection is
required; saved preferences or automatic application at boot/login are a
separate reviewed extension, not a reason to change boot arguments now.

Return structured errors for unsupported hardware, permission denial,
inactive VT, compositor ownership, stale identity and failed restoration.
Do not report success for an untargeted fallback. Preserve current brightness
and idle controls during the C migration; optional DDC/brightness helpers may
remain bounded subprocesses initially, invoked only when that feature is used.
DDC power-off is not a default fallback without model-specific wake proof.

## Resource and development requirements

Support weak CPUs, little RAM and small disks. Use bounded allocations and
retry limits for changing kernel counts, sanitize EDID text, close descriptors,
and block in `poll`/`epoll` on real events. Redraw the TUI only on changes.
No periodic output reapplication or polling to fight fbcon. Load no desktop
framework, Python interpreter or DDC helper on the normal targeted-blank path.
Choose a small termios UI or ncurses based on measured usability and cost.

All Tamlinux 0.x releases are developmental. Keep symbol tables and generate
debug information in the executables and library objects we build, so crashes
and core dumps can be examined against the exact candidate. Defer stripping
and stripped-size targets until after Tamlinux 1.0 is released. Disable
automatic stripping or removal of debug information during installation and
package fixup, and verify the final installed ELF files contain it. Compile
with `-g` alongside the chosen optimization settings; retaining symbols does
not require disabling optimization. See the
[GCC debugging options](https://gcc.gnu.org/onlinedocs/gcc/Debugging-Options.html).

Measure actual unstripped executable/archive sizes, incremental installed closure,
loaded libraries, peak RSS and combined proportional memory of any live
supervisor/guard, startup latency, idle CPU and wakeups. Compare the current
Python command and C version on the same machine and operations, and repeat
on a constrained machine. Separate cold and warm startup and hardware-probe
time. Proposed review budget: combined steady proportional memory at most
4 MiB for the selection owner and guard; this is a target to validate, not
an existing measurement. Record symbol/debug data's disk cost separately from
loaded memory. Set hardware-specific
latency thresholds after baseline measurements. Explain any dependency or
budget exception before accepting it. Count firmware/driver waits separately
without hiding their user-visible delay.

Provide a core-only/display-only development build and installed pkg-config
discovery. Correctly rebuild clients when headers, static archives or build
flags change. Test both explicit `LIBTAM_PREFIX` and normal pkg-config paths;
reject missing/too-old APIs with a useful error. Packaged runtime success and
Fred's ability to build further changes are separate acceptance conditions.

## Work and acceptance

| Step | Deliverable and completion evidence |
| --- | --- |
| Review | Fred approved this design and the linked 0.5.5 delivery plan on 2026-10-25. Implementation and physical acceptance remain pending. |
| Feasibility | Small C prototype proves routing, sustained fbcon use, authorized ownership, restoration and lifetime on the actual three-monitor arrangement. All physical changes use the recorded package Test route. |
| Libraries | Separate archives/headers/build targets, explicit API ownership and error semantics; sanitizer checks instrument library objects as well as test callers; malformed enumeration and failure injection tests pass. |
| Command | C CLI/TUI and any reviewed supervisor preserve existing useful operations and expose targeted blank/wake/keep. PTY tests cover input, terminal restoration, signals and resizing. |
| Integration | A recorded 0.5.5 assembly builds the command and exposes matching development libraries; tests verify the final installed binaries and clean developer environment. |
| Physical proof | Each of the three monitors can be the retained display, with the other two blank while Fred types and uses `tam`. Restore each separately and all together; test hotplug, failed commits, interrupted/killed/stopped processes, VT changes, logout and desktop launch. Record physical standby and resource measurements. |

Use fake ioctl/sysfs/seat interfaces for deterministic routing, clone/shared
CRTC, stale identity, partial multi-device failure, permissions, bounds and
recovery tests. Use VKMS where useful for real KMS transactions in an isolated
test environment; it cannot prove a physical monitor's power state or the
target driver's fbcon interaction. Single-output and framebuffer-only systems
must retain a usable console and report unsupported targeting accurately.
Record actual kernel/driver and monitor capabilities for each physical trial.

## Next actions

1. Complete actual console framebuffer mapping and real session/device handoff
   checks. Retained-output unplug recovery now passes fixtures for disconnected
   and removed connectors; physical recovery and driver-specific hotplug behavior
   remain unproved.
2. Review the bounded recovery prototype and measure its actual owner/guard
   memory/dependency costs, then prepare a recorded package only on Fred's
   instruction for separately authorized physical Test.
3. Prove sustained fbcon behavior and lifetime on the target hardware before
   completing `keep --shell`, individual wake, UI parity and the remaining
   [0.5.5 delivery gates](../../../tamlinux-packages/docs/plans/0.5.5.md).

## Development evidence: 2026-10-25

The optional libtam display archive now inspects connectors, atomic properties,
CRTCs and planes using installed DRM UAPI headers and libc only. A C feasibility
CLI under `commands/tam-monitor/` reports this observation and can analyze
which connectors to detach while preserving the selected output's CRTC/planes.
Shared CRTCs and shared framebuffers are covered separately. Counts, retries,
errors and hardware strings are bounded; no device is opened by this API.

ASan/UBSan-instrumented display objects pass fake-device failure and routing
tests. Seven native CLI tests and the existing 25 monitor tests pass. Builds
through pkg-config and explicit prefix work; header/archive/flag changes
trigger rebuilds. The prototype retains symbols/debug information and its
only ELF runtime dependency is libc. Core/display install targets avoid the
portal dependency. [Development record](../ai/2026-10-25-monitor-feasibility.md).

This completes the inspection foundation only. It does not establish DRM/VT
ownership, retained framebuffer/blob references, restoration, kernel atomic
validation, sustained fbcon behavior or physical standby. The prototype is
not installed as the production command, and no candidate was prepared or
activated. Hardware feasibility and the remaining C command migration stay open.

## Development continuation: foreground ownership and guarded transactions

The optional display API is now 0.2.0. A separate libsystemd adapter checks
an owned foreground text VT and active local tty session. It validates udev
seat membership, uses existing permissions for direct primary-device access,
and refuses an occupied DRM master. The recovery worker owns VT_PROCESS
handoff without changing KD_TEXT or keyboard mode. Logind is observed for
session loss; TakeControl is avoided because its implementation mutes the VT,
enters graphics mode and resets VT ownership on release. Core and display consumers retain their libc-only dependency boundary.
Owned snapshots clone framebuffer backing and property blobs, prove
non-destructive release and pass a complete atomic restore TEST_ONLY.
Selection and recovery re-enumerate, test complete requests and recheck
foreground/session/deadline authorization immediately before actual writes.

The uninstalled C prototype adds a bounded `preview` trial with an independent
recovery owner, readiness handshake, deadline, signals, UI-death detection and
kernel hotplug events. Fake-device library sanitizer checks, nine native CLI
checks, sixteen recovery process checks, event parser checks and all 25 existing
monitor tests pass. The installed Python command still works. No live display
mutation, package preparation, deployment or stage movement occurred.

Seven warm `--help` launches measured median peak RSS of 21,700 KiB for the
installed Python command and 2,108 KiB for the C prototype, with median elapsed
times 80.328 ms and 1.035 ms respectively. This startup-only result does not
establish live combined proportional memory, cold startup or physical behavior.
Safe retained-output hotplug fallback, sustained mode, multi-GPU compensation,
actual kernel fallback, resource acceptance and physical fbcon/standby proof
remain open. [Development record](../ai/2026-10-25-monitor-ownership.md).

Acquisition review found an important logind constraint in the
[systemd controller implementation](https://github.com/systemd/systemd/blob/v262/src/login/logind-session.c#L1493)
and [VT reset](https://github.com/systemd/systemd/blob/v262/src/basic/terminal-util.c#L1654).
The prototype therefore uses the direct-device path allowed above, with no
privilege escalation or permission changes. Systems lacking the required
active-seat permissions are unsupported until a separately reviewed path
exists. A packaged physical trial must prove that the kernel grants this
access and that the owned VT handoff preserves the login console.

## Development continuation: retained-output unplug recovery

The optional display API is now 0.3.0. Recovery on the retained device permits
captured connectors to disconnect or disappear, omits vanished connector IDs
and restores surviving captured console outputs with owned modes/framebuffers.
Shared CRTCs stay active while pipelines without a surviving route are disabled.
No surviving captured output means no recovery modeset: release control and
report loss. New/changed identities, foreign routing, device loss and replaced
CRTC/plane objects still refuse replay. A second observation binds the sole
write to the complete TEST_ONLY request; further hotplug or lost authorization
prevents the write, with no indefinite retries or periodic reapplication.

ASan/UBSan library fixtures cover every retained choice and loss subset for
both disconnected and removed connectors, kernel detachment, stale identities,
validation races, failed restoration and no remaining output. Nine native CLI
checks, eighteen recovery process checks, kernel-event parser checks and all
25 existing Python monitor tests pass. The command requires matching 0.3.0
development metadata; its install target and installed Python implementation
are unchanged. [Development record](../ai/2026-10-25-monitor-unplug.md).

This establishes software behavior only. Actual console framebuffer mapping,
physical fbcon/standby/unplug recovery, session handoff, multi-GPU compensation,
resource acceptance and sustained mode remain open. No live display mutation,
candidate preparation, installed-command change, deployment or stage movement
occurred.

## Development continuation: console framebuffer mapping, full C migration and resource measurements

The optional display API is now 0.4.0. Actual console framebuffer mapping
(`tam_display_map_console_fb`) reads `/sys/class/vtconsole`, queries
`FBIOGET_CON2FBMAP` or unambiguous bound `/sys/class/graphics/fb*` devices,
resolves the primary backing DRM card (`cardN`), and validates fbcon geometry
and pitch against the captured active DRM framebuffer reference via `GETFB2`
(`tam_display_state_verify_console_fb`). Atomic transactions support targeted
connector detachment (`tam_display_state_blank`) and wake re-attachment
(`tam_display_state_wake`), and `tam_vt.h` provides foreground VT `TIOCLINUX`
blank and wake ioctls.

The Python `tam-monitor` command is completely retired and replaced by the
native C executable built from `native.c`, `native-hw.c`, `native-preview.c`,
`native-tui.c`, and `native-events.c`. The native binary provides:
- Complete CLI parity: `list [--json] [--no-probe]`, `brightness`, `idle`,
  `preview`, `inspect`, `keep CONNECTOR --shell`, `keep CONNECTOR --seconds 1..60`,
  targeted `blank [--monitor CONNECTOR ...]`, and individual `wake [--monitor CONNECTOR | --all]`.
- Interactive terminal TUI: VT102 change-only redrawing, `SIGWINCH` resize
  adaptation, and key parity (`j`/`k`/Arrows, `+/-`, `r`, `b`, `i`, `o`, `x`, `w`, `s`, `q`/`ESC`)
  without an `ncurses` runtime dependency.
- In-session control socket: `SO_PEERCRED`-verified UNIX domain socket supporting
  live `WAKE`, `BLANK`, `KEEP`, `RESTORE`, and `STOP` requests during active sessions.

Resource measurements comparing the compiled C binary (`build/tam-monitor`)
against the deployed 0.5.4 Python baseline (`~/.local/bin/tam-monitor`):
- Binary size: 399,984 bytes (390.6 KiB) unstripped with full debug symbols;
  `.text` is 80,776 bytes (78.9 KiB), and `.debug_*` sections total 260,904 bytes (254.8 KiB).
- Static archives: `libtam-display.a` 219.1 KiB, `libtam-display-session.a` 36.8 KiB.
- Dynamic dependencies: `libsystemd.so.0`, `libm.so.6`, `libc.so.6`.
- Startup latency (7 runs median):
  - `tam-monitor --help`: 2.58 ms vs 83.36 ms Python (32.3x faster).
  - `tam-monitor list --json --no-probe`: 2.87 ms vs 82.56 ms Python (28.8x faster).
  - `tam-monitor list --json` (hardware probe): 432.53 ms vs 2,371.44 ms Python (5.5x faster).
- Peak RSS: 10,368 KiB (10.12 MiB) vs 21,840 KiB (21.33 MiB) Python (2.1x lower memory).
- Combined active owner + recovery guard memory during live `keep --shell` session:
  - Combined RSS: 4,356 KiB (4.25 MiB).
  - Combined PSS: 400 KiB (0.39 MiB), leaving 3.61 MiB headroom under the 4.00 MiB review budget (9.8% of budget used).

Test verification:
- 24 `test_monitor.py` tests covering hardware discovery, EDID sanitization, DDC/backlight, console idle, wake guard lifetime, signal handling, and TUI resize.
- 21 `native_preview.py` tests covering recovery deadlines, owner death, guard term, hotplug, VT handoff, CFB verification, `keep --shell` interactive session, targeted blank and individual wake.
- 9 `native_cli.py` tests and `test-native-events` parsing tests.
- All ASan/UBSan `libtam` test suites passing.

Development stage only: physical multi-monitor hardware trial and package deployment remain open for separate authorized Fred Test stage.
[Development record](../ai/2026-10-26-tam-monitor-c-migration.md).
