# tam-monitor C implementation: review and correction handoff

Status: findings reproduced against the revisions below; corrections not implemented.
Date: 2026-10-27.
Scope: architecture, validation, recovery, CLI/TUI behavior and test coverage.
Next action: independently verify each finding, add regression coverage, then correct the confirmed defects.

## Assessment and evidence boundary

Keep the independent recovery owner and the division between command, display
library and session adapter. They are useful foundations. The implementation is
not ready for acceptance: ordinary commands, supervisor requests and fallback
paths enforce different validation and recovery rules.

There are eight findings. R1, R2 and R3 deserve attention before a physical trial.
R3 has a narrower conclusion than the initial conversational review: the fixture
proves that an error returned after a simulated apply does not trigger immediate
recovery. It does **not** prove that an actual failed DRM atomic ioctl partially
changed hardware. Verify the library contract and classify errors before choosing
that correction.

| Repository | Reviewed revision | Role |
| --- | --- | --- |
| `tamlinux` | `c8648c3381296dd5fd994b1bf3d7fd215d992697` | C command migration |
| `libtam` | `2218bb59acaf6781073a66257f49f0dc3759f18c` | Display/session API 0.4.0 |
| `tamlinux-packages` | `e7ad5848afde012fd555e181122007165edbf686` | Recipe inspection only |

Validation completed in the review:

- `make check` in `commands/tam-monitor`: 9 native CLI tests, 21 recovery tests,
  24 hardware/console/process tests, and the C event-parser test program passed.
- `make test-display test-session` in `libtam`: discovery/routing, owned
  restoration, VT ownership and session test programs passed with
  AddressSanitizer and UndefinedBehaviorSanitizer.
- Additional isolated reproductions described below exercised real processes,
  sockets, pipes, timers and PTYs. VT, DRM and brightness writes were mocked.

No physical display, live VT, package or deployment was changed. Passing fixtures
do not establish visible text rendering, physical standby, actual GPU recovery
or a working package. Those remain separate acceptance work under the
[existing console-monitor plan](../plans/console-monitor-control.md).

## Reproduce safely

The companion [reproduction script](2026-10-27-tam-monitor-reproduce.py) emits JSON
observations for R1–R8. It is a diagnostic harness, not permanent regression
coverage. Exit zero means the harness ran, not that the product passed. Compare
the output with each finding's acceptance criteria.

1. Read the workspace instructions and acquire the necessary path claims. Use the
   existing checkout. Record its current revision and changes; do not reset
   someone else's work to the reviewed revision. Immutable source links below
   preserve the baseline if the checkout has advanced.
2. Have a C compiler, Python 3, `pkg-config`, and libtam display/session development
   files at API 0.4.0 or later available. Use the same library for the command
   build and extra fixture link. If using the development prefix, set
   `PKG_CONFIG_PATH` to its `lib/pkgconfig` directory. Do not change the active
   desktop or install packages merely to run these fixtures.
3. From the `tamlinux` root, run:

   ```sh
   make -C commands/tam-monitor check
   python3 -B docs/reviews/2026-10-27-tam-monitor-reproduce.py
   ```

   Run one case with, for example:

   ```sh
   python3 -B docs/reviews/2026-10-27-tam-monitor-reproduce.py --case R4
   ```

4. If changing the library contract, run `make test-display test-session` from
   the `libtam` checkout as well.

The script requires the two fixture executables built by `make check`; it never
substitutes the real command for either fixture. R3/R6 compile a temporary copy
of the existing link-time fixture against unchanged product objects. The extra
fixture injects failure only into blank, and supplies two synthetic monitors for
the TUI. Tracked source is untouched and temporary files are removed. Adapt the
harness explicitly if the fixture API changes; its observations are not proof
that an unrecognized future implementation passed.

The original sandbox blocked the UNIX socket handshake and LeakSanitizer's
process inspection. Successful socket and sanitizer checks ran with host access
while retaining hardware mocks. An environment error is not a product finding;
obtain the required test permissions instead of weakening the checks.

## Findings

### R1 — Framebuffer discovery failure permits unverified mutation

Priority: high.
Evidence: fixture-reproduced branch bypass; physical consequence not exercised.

**Location:** [resolve_target_card, lines 535–570][r1-code] and the worker's
conditional `verify_cfb` check. A mapping error becomes success if the caller
supplies an explicit card or card-prefixed connector. `verify_cfb` stays false.

**Reproduce:** run R1. It sets `TAM_MONITOR_FIXTURE_MAP_FAIL=1` and invokes the
preview fixture as `keep DP-1 --card 1 --seconds 1 --json`. The baseline returns
`ok:true`, with `acquire`, `capture`, `apply`, `keep:DP-1`, `restore`, `free`,
`release`, and no `verify_cfb`. Also cover a card-prefixed target and targeted blank.

**Basis:** a chosen DRM card is not proof that its framebuffer backs the active
text console. The accepted plan requires identifying that framebuffer and
preserving retained text rendering. The kernel describes fbcon as running on a
framebuffer device and permits console-to-framebuffer mapping.
[Project requirement](../plans/console-monitor-control.md#prove-the-kernel-path-before-building-the-ui),
[Linux framebuffer-console documentation](https://docs.kernel.org/fb/fbcon.html).

**Correction:** ordinary keep/targeted blank should refuse mapping or geometry
verification failure. A card argument may constrain a verified mapping, not waive
it. If bounded experimental preview intentionally has a weaker contract, preserve
that explicitly and separately from normal console control.

**Acceptance:** mapping failure, card mismatch and GETFB2 mismatch produce no
apply; successful verification still permits the transaction. Cover explicit
cards and card-prefixed connectors.

### R2 — Supervisor requests discard or fail to validate GPU identity

Priority: high.
Evidence: explicit-card mismatch reproduced; related prefix/TUI paths identified in source.

**Location:** [run_supervised_session, lines 586–616][r2-code]. The active-session
path sends `KEEP <connector>` before card resolution and omits the explicit card.
The TUI also sends bare connector names. The library's [matcher][matcher] accepts
a card-prefixed query by stripping its card number, without verifying that number
against the topology's DRM device.

**Reproduce:** run R2. Start the fixture's card 1 supervisor with
`keep DP-1 --shell`; invoke `keep HDMI-A-1 --card 63 --json` while it listens.
The baseline reports success and records `keep:HDMI-A-1` in the card 1 worker.

**Impact:** a command naming another GPU can affect the current GPU instead.
The source establishes lost identity; the fixture does not simulate physical
multi-GPU behavior. Also inspect every connector in a multi-target blank request:
normal session setup currently resolves only its first connector.

**Correction:** preserve card identity in requests and validate every explicit
card and connector prefix against the supervisor's owned card. Make the TUI
preserve its selection's card. Reject mismatches before any state change; do not
use prefix stripping or the first batch target as full validation.

**Acceptance:** reject wrong explicit cards, wrong prefixes, mixed-card blank
batches and TUI selections on another GPU, with no apply. Valid bare/qualified
names on the owned card must retain their behavior.

### R3 — Interactive apply errors lack recovery classification and immediate recovery

Priority: high for verification; correction depends on the established error contract.
Evidence: injected post-apply error; actual failed-ioctl hardware effects not established.

**Location:** [handle_client_request, lines 218–244][r3-code]. Keep/blank/wake
errors return to the client while the worker continues. Only STOP sets
`stop_session`. Initial apply errors instead reach recovery. The library marks
state changed before a potentially uncertain write and explicitly treats an
interrupted write as requiring recovery. [Library implementation][uncertain-write].

**Reproduce:** run R3. Its temporary fixture changes only blank's failure flag,
allowing the initial keep to succeed. Start `keep DP-1 --shell`, wake HDMI-A-1,
then request a blank that records apply and returns injected I/O failure. The
client exits 1. At 200 ms after the error, the owner is alive with no restoration
after that request. Restoration happens when the finite fixture shell exits;
the outer session exits 0. The original reproduction without the preliminary
wake showed the same missing recovery branch.

**Qualification:** Linux atomic KMS requires failing validation to leave hardware
unchanged. Do not interpret this synthetic sequence as proof that an ordinary
rejected atomic transaction partially applied. Nor should an invalid connector
necessarily terminate a healthy session. The finding is missing classification
and handling for the library's declared uncertain-write/recovery contract.
[Linux atomic modesetting documentation](https://docs.kernel.org/gpu/drm-kms.html#atomic-mode-setting).

**Correction:** establish whether each library failure means (a) no mutation and
valid prior state, (b) state requires revalidation/restoration, or (c) ownership
lost and restoration forbidden. Expose enough information to the supervisor
instead of guessing from generic errors. For (b), stop new mutations, restore
through normal access checks, release if necessary, and preserve the failure in
the outer result. For (c), release without stale replay. Harmless validation
errors may leave the session running. An explicit library recovery-needed state
or result is an option, not a prescribed ABI change.

**Acceptance:** distinguish invalid requests from errors injected at real library
commit boundaries. Include EINTR/uncertain apply, failed restore and revocation.
Successful later cleanup must not hide a fatal session error. Preserve useful
interaction after harmless validation failure. Do not mark this fixed solely
from the high-level mock.

### R4 — A silent client blocks the recovery event loop

Priority: medium.
Evidence: real local sockets, mocked display transaction.

**Location:** [client acceptance, lines 197–215][r4-code]. `accept4()` sets only
`SOCK_CLOEXEC`; the handler performs blocking recv with a two-second timeout
inside the recovery process.

**Reproduce:** run R4. Start fixture `keep DP-1 --seconds 1 --json`, connect a
SOCK_SEQPACKET client to its temporary `vt2.sock`, and send nothing. Completion
took approximately 2.01 seconds despite the independent one-second timer. The
measurement includes startup and exit; exact timing varies.

**Authority:** Linux accepted sockets do not inherit O_NONBLOCK. Socket receive
timeouts bound socket I/O, not the application's independent recovery deadline.
[accept(2)](https://man7.org/linux/man-pages/man2/accept.2.html),
[socket(7), SO_RCVTIMEO](https://man7.org/linux/man-pages/man7/socket.7.html).

**Correction:** use nonblocking accepted sockets and integrate bounded client
read/write state with timer, signal, owner-death, session and hotplug events.
Bound client count/message size and prioritize recovery. Setting nonblocking but
immediately closing on EAGAIN races legitimate clients; wait for readiness with
the other events. Another blocking timeout does not solve the architectural issue.

**Acceptance:** silent/slow clients cannot materially postpone deadline, VT
handoff, termination or owner-death recovery. Allow modest scheduling variance
rather than asserting exact millisecond timing.

### R5 — Helper timeout stops being enforced after output pipes close

Priority: medium.
Evidence: real helper runner with a harmless fake brightness helper.

**Location:** [helper completion, lines 203–214][r5-code]. After both output streams
reach EOF, `waitpid(pid, ..., 0)` has no deadline.

**Reproduce:** run R5. The fake brightness helper executes `exec 1>&- 2>&-` and
`sleep 1.2`. With a 100 ms fixture timeout, readback took approximately 1.20
seconds and reported an invalid response rather than timeout. The finite sleep
avoids leaving a hung child; a child that never exits has no bound on this path.

**Authority:** waitpid without WNOHANG can block waiting for child state; pipe
closure does not establish exit.
[waitpid(2)](https://man7.org/linux/man-pages/man2/waitpid.2.html).

**Correction:** retain one monotonic deadline across capture and child exit.
Observe completion after EOF using nonblocking wait and bounded event waits, or
a suitable process-notification descriptor. On expiry, terminate the helper
process group and reap it; preserve descendant cleanup. Handle wait errors
explicitly and avoid a busy loop when both stream descriptors close.

**Acceptance:** a child closing both streams before sleeping times out promptly;
normal EOF/exit succeeds. Retain coverage of one closed stream, inherited
descendant pipes, signals, output bounds and descendant termination.

### R6 — TUI x does not implement a state-based blank/wake toggle

Priority: medium.
Evidence: real TUI in a PTY against mocked operations; library semantics checked in source.

**Location:** [KEY_TOGGLE_ONE, lines 349–367][r6-code]. It requests blank first
and wake only if blank fails. The [library][blank-code] combines requested and
already-detached outputs rather than treating repeat blank as a state query.

**Reproduce:** run R6. Keep HDMI-A-1, leaving DP-1 detached. The PTY TUI selects
DP-1 and receives `xxq`. The baseline records two `blank:DP-1` operations and no
wake. Since DP-1 starts detached, expected behavior is wake then blank. The
[command documentation][command-readme] promises an x toggle.

**Correction:** implement a supervisor-side toggle using current detached state,
or obtain authoritative state without introducing a query/write race.
`tam_display_state_is_detached()` already exists. A blank failure is not evidence
of prior blanking: it can represent invalid input, lost ownership or I/O failure.

**Acceptance:** consecutive x presses alternate starting both awake and detached.
Cover failures and changes by another client. Preserve brightness and non-console
TUI behavior.

### R7 — Narrowing brightness input permits out-of-range hardware writes

Priority: medium.
Evidence: reviewed 64-bit GCC build; brightness writes mocked.

**Location:** [brightness parsing, lines 224–231][r7-code]. A valid long is cast
to int before the callee's 1–100 check.

**Reproduce:** run R7. `4294967297` and `-4294967295` both exited zero, printed 1,
and invoked the fake helper with `DP-1 1%`. These exact values depend on the
reviewed long/int widths. No actual brightness changed.

**Authority:** GCC documents reduction modulo the destination width for an
unrepresentable signed-integer conversion. This is not a claim of undefined
signed arithmetic overflow.
[GCC integer conversions](https://gcc.gnu.org/onlinedocs/gcc/Integers-implementation.html).

**Correction:** check the parsed long against 1 and 100 before casting, or reuse
a bounded parser. Retain the callee's check. Reject invalid input before discovery,
probing or helper invocation.

**Acceptance:** zero, negative, >100, wrapping values, LONG_MAX, overflow text,
empty input and trailing junk cause no helper calls. Valid endpoints work. Define
leading-sign/whitespace handling consistently with documented syntax.

### R8 — Listener creation failure is reported as successful readiness

Priority: medium.
Evidence: overlong temporary UNIX socket pathname.

**Location:** [worker, lines 355–357][r8-code]. A negative listener result is
ignored and readiness stage 2 is sent with a success error structure. Display
application already happened.

**Reproduce:** run R8. Use an owned mode-0700 runtime directory whose socket path
exceeds sun_path capacity but passes the earlier directory-length check. No socket
is created, yet the baseline starts the fixture shell and returns `ok:true`.
A shell-start marker distinguishes actual shell launch from successful refusal.

**Authority:** Linux documents a 108-byte sockaddr_un.sun_path array. This
implementation's pathname copy also needs space for its terminating NUL.
[unix(7), address format](https://man7.org/linux/man-pages/man7/unix.7.html).

**Correction:** require a listener for sessions promising interactive control.
Prepare it before mutation/readiness where possible, preserving any existing
owner's socket. Otherwise recover an already-applied transaction before release.
Return a useful path/bind/listen error; never announce readiness or start a shell
without the promised channel.

**Acceptance:** path-length, directory, bind and listen failures produce nonzero
results, no shell launch and no unrecovered change. Normal listeners work.
Failure cleanup must not unlink another owner's socket.

## Packaging observation — no package build performed

The inspected [commands derivation][package-commands] lacks libtam display/session
and libsystemd development dependencies and a pkg-config tool declaration. Its
check/install phases invoke a Makefile that now needs them. The inspected
[libtam derivation][package-libtam] uses default targets; display/session are
optional targets in [libtam's Makefile][libtam-makefile]. Local tests used available
development libraries, which are not evidence of Nix build inputs. This is an
integration gap for the migration, not a claim that the deployed package is broken.

Before assembling it, explicitly build/install display/session archives, headers
and metadata; declare their dependencies; give the commands derivation matching
library/pkg-config inputs. Verify a clean package build and installed executable.
Do not depend on a developer HOME fallback or mint a candidate merely to file or
correct this review.

## Suggested implementation order and completion evidence

1. Reproduce against the exact commits or explain source drift. Convert R7/R5
   into focused regression tests and fix parser/helper lifetime independently.
2. Establish one target-validation contract for initial and interactive operations
   (R1/R2). Keep immutable baseline and current selection state distinct.
3. Define the command/library error and recovery contract (R3); make listener
   setup and client handling obey it (R8/R4).
4. Implement the TUI toggle from authoritative supervisor state (R6).
5. After behavioral coverage, consider separating control protocol, supervised
   session and console blanking from the 1,122-line native-preview.c. Avoid mixing
   a large structural rewrite into the first fixes unless necessary.
6. Run command and relevant library sanitizer tests, exercising actual library
   boundaries rather than only success mocks. Correct packaging separately and
   record exact source/dependency revisions for any built candidate.

For every finding, record disposition: reproduced, corrected (commit and regression
test), not reproduced with explanation, or deferred with reason. Recommendations
are review guidance to verify. Preserve valid behavior: owned foreground VT and
session checks, independent owner-death recovery, deadline/hotplug handling,
refusal of stale replay after revocation, visible errors and usable TUI/shell
cleanup. Physical trials follow the existing package/stage authorization rules;
this report grants no live display or stage-move permission.

## Authorship and sources

Prepared with Codex CLI 0.164.0 and detected model `gpt-6-astra`.
See the [AI session record](../ai/2026-10-27-tam-monitor-review.md).
External references were consulted on 2026-10-27. They support platform semantics;
pinned source links and reproductions support implementation claims. Correction
recommendations are engineering judgment. Line numbers refer to these revisions.

[r1-code]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/native-preview.c#L535-L570
[r2-code]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/native-preview.c#L586-L616
[r3-code]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/native-preview.c#L218-L244
[r4-code]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/native-preview.c#L197-L215
[r5-code]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/native-hw.c#L203-L214
[r6-code]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/native-tui.c#L349-L367
[r7-code]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/native.c#L224-L231
[r8-code]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/native-preview.c#L355-L357
[matcher]: https://github.com/greenermoose/libtam/blob/2218bb59acaf6781073a66257f49f0dc3759f18c/src/tam_display_plan.c#L11-L20
[uncertain-write]: https://github.com/greenermoose/libtam/blob/2218bb59acaf6781073a66257f49f0dc3759f18c/src/tam_display_atomic.c#L257-L267
[blank-code]: https://github.com/greenermoose/libtam/blob/2218bb59acaf6781073a66257f49f0dc3759f18c/src/tam_display_atomic.c#L437-L495
[command-readme]: https://github.com/greenermoose/tamlinux/blob/c8648c3381296dd5fd994b1bf3d7fd215d992697/commands/tam-monitor/README.md#interactive-tui
[package-commands]: https://github.com/greenermoose/tamlinux-packages/blob/e7ad5848afde012fd555e181122007165edbf686/nix/packages/default.nix#L492-L533
[package-libtam]: https://github.com/greenermoose/tamlinux-packages/blob/e7ad5848afde012fd555e181122007165edbf686/nix/packages/default.nix#L3-L12
[libtam-makefile]: https://github.com/greenermoose/libtam/blob/2218bb59acaf6781073a66257f49f0dc3759f18c/Makefile

## Development correction status (2026-10-27)

The review remains the baseline; these corrections are development work and
are not evidence of physical acceptance.

- R1: ordinary keep/blank now require fbcon mapping; fixture tests cover
  explicit cards, qualified targets and mapping failure.
- R2: supervisor and initial blank requests validate qualified targets against
  the owned card; the TUI transmits its card-qualified identity.
- R3: library API 0.4.1 exposes uncertain commit state and refuses subsequent
  mutation; the supervisor ends the session and attempts authorized recovery.
  Instrumented ioctl fixtures exercise both an applied EINTR and an atomic
  rejection preserving the prior state. An actual rejected atomic ioctl has
  not been shown to partially apply. Revocation must still forbid stale replay.
- R4: accepted clients are nonblocking and polled with recovery events; a
  silent-client deadline regression passes.
- R5: helper completion retains the deadline after pipe EOF; a real child
  closing both pipes then sleeping times out.
- R6: the supervisor toggles its current detached state; the original PTY
  reproduction now records wake then blank.
- R7: brightness is range-checked before narrowing or hardware discovery.
- R8: a listener is required before mutation; a pre-existing socket is
  preserved, and overlong paths fail without starting the shell.

Further adversarial and final package checks remain required before proposing
the exact candidate; fixture behavior is not physical display proof.
