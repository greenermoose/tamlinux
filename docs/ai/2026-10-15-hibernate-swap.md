## Session: 2026-10-15 — Drain zram swap before hibernating (0.4.3 Develop)

- **CLI Tool**: Claude Code (`claude`) `2.1.300`
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Commits**: `9db54be` (hook), `b70dfde` (preflight telemetry)
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > I asked agy to investigate why the system did not hibernate last night. It is writing up its findings and saving them in the [redacted: private repository] repo. Ponder the evidence and see if you can figure out the root cause or put in place more extensive logging that can help us collect more evidence that will help pinpoint it and lead to a permanent fix. As soon as agy is done I'll have it release any claims on work that might be impeding you.

  > 1 yes as long as you're sure clearing these will not have a deleterious effect on the work I'm attempting to get done today, primary getting Tamlinux 0.4.3 ready for testing with my account during my daily driving of the system
  > 2 Let's keep large scratch files out of RAM. This seems like a mitigation rather than a real fix. Why can't we handle large scratch files at the moment of hibernation and defer dealing with them until then? If I'm understanding your proposed mitigation, we will proactively keep scratch files out of RAM, slowing down our daily work all day long. Correct me if this is not the case.

  > Yes, build the hook

  > Do the small follow up to the packaged copy in tamlinux if you can. If you cannot, leave a note for codex to handle it.

- **Key Decisions & Implementation Notes**:
  - The failed hibernation stopped in image preallocation ("Image allocation
    is N pages short"), not in the later page check. The kernel copies the
    saved pages within RAM, so the image is capped at about half of memory.
    About 10 GiB of tmpfs files had been swapped into zram, and zram
    outranks disk swap, so reclaim could only recompress pages and never
    move them out of RAM.
  - Keeping scratch files on disk was only a mitigation: it covers files,
    not program memory that swaps into zram. Fred asked for the work to
    happen at hibernation time instead. The fix is a systemd sleep hook,
    because hooks are the only per-leg point in suspend-then-hibernate
    (`SYSTEMD_SLEEP_ACTION` names the leg) and run while user sessions are
    frozen.
  - `tamlinux-hibernate-swap` turns zram swap off before the hibernate leg
    and back on, at its previous priority with discard, on post or before a
    fallback suspend. It ships as a native default because Tamlinux's own
    zram configuration (whole-RAM size, priority 100) is what creates the
    exposure.
  - Safety bounds: skip when disk swap would end above 80% used, since
    systemd-oomd's swap kill acts at 90%. The drain is limited to 60 s, inside
    systemd's 90 s hook limit, and an interrupted kernel swapoff keeps zram on
    with whatever it still holds. A lock and state file keep a second copy
    from draining twice. The hook never touches disk swap or the resume
    device.
  - Fred then asked for the extended hibernate preflight telemetry in the
    packaged `suspend-unless-stay-awake`. It now also records the
    minimum-image inputs from `/proc/meminfo`, zram `mm_stat`, tmpfs usage
    and the largest `/tmp` entries.
  - Not yet measured: how long a multi-GiB drain takes on real hardware.
    The first natural hibernations after installation provide that number
    through the hook's journal lines (tag `tamlinux-hibernate-swap`).
- **Verification**:
  - 14 new tests drive the hook with fake `swapoff`/`swapon`/`logger`
    against a synthetic `/proc/swaps`. They cover the drain and restore,
    plain hibernate and hybrid sleep, the untouched suspend leg, the fallback
    suspend, the disk-capacity skip, no disk swap, no zram, empty zram, an
    interrupted drain, a second copy, and negative priorities.
  - The native-defaults suite (origins digest and mode, vendor paths,
    Tamlinux names) and the full desktop suite (572 tests) pass.
  - The `suspend-unless-stay-awake` check and the 22 display/power helper
    tests pass, and a live `--capture-only` run printed all sections.
  - No hibernation has run with the hook yet.
