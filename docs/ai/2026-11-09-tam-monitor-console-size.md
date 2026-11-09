# Session: 2026-11-09 — tam-monitor semver, console-size and console fit during keep (0.1.0 to 0.3.0)

- **CLI Tool**: `claude` `2.1.321`
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Authorship**: AI-assisted, directed by Fred.
- **Commits**: `dffe90a` (0.1.0), `46f0734` (0.2.0), `9b92f8d` (0.3.0). These
  carry a `Co-Authored-By: Claude Opus 5.5` trailer but no `AI-Tool` or
  `AI-Model` trailer; this record supplies them and the commits are not
  amended.
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > I am running a VT kernel console. Three monitors are mirroring this. The MSI and hp look fine. but the Dell display is not full screen. The display is shrunken, starting in the top left corner. There are big blank gaps on the right side and below the part of the screen that is working. Why is this happening? I'm not sure why the active area of the display on this monitor is not using all pixels. This same monitor works fine in the graphical shell. In that graphics mode, all pixels are used and the display looks normal, not shrunken to the top left. Please investigate, research, and advise.

  > I have turned off the other monitors now. Is there a command I can issue through tam-monitor to make the Dell show full screen? Those other monitors are blank so I don't care about them.

  > Give tam-monitor a semver. Then update it so that it can change console sizes. I never want to use python to do things like this. Note that rather than writing python scripts I want to fix my tam-* commands to be fully functional.

  > Make keep fit the console automatically

- **Key Decisions & Implementation Notes**:
  - Cause: with mirrored outputs, DRM fbdev emulation allocates one
    framebuffer for the largest monitor (2560x1440) but fbcon draws only in
    the area every lit monitor can show (1920x1080). Each monitor scans out
    from the top-left at its native mode, so the larger one shows the
    console in a corner.
  - 0.1.0: `version.h` (`TAM_MONITOR_VERSION`) and `--version`/`-v`,
    following `tam-hardware`. The command versions independently of the
    product.
  - 0.2.0: `tam-monitor console-size` in a new `native-console.c`. It reports
    the console area, the framebuffer allocated at boot, the VT text grid
    and each lit monitor's current CRTC mode (sysfs preferred mode when the
    card cannot be opened), and sets the area with `FBIOPUT_VSCREENINFO` and
    `FB_ACTIVATE_ALL`: `CONNECTOR`, `WIDTHxHEIGHT` or `--all`. It never
    exceeds the allocated framebuffer (the DRM fbdev limit), changes no
    display mode, and prints the exact `sudo` line when `/dev/fbN` is not
    writable. A first answer was a one-off Python script; Fred rejected
    that, and the feature went into the command instead.
  - 0.3.0: the recovery owner of `keep` and targeted `blank` sessions fits
    the console to the lit monitors after the selection and after each
    successful in-session request, and puts the original area back before
    KMS restore (and before `RESTORE`/`STOP`), so other monitors never
    relight with a cropped console. Best effort: without access it says so
    on stderr and the session is unchanged. `preview` never fits.
    `console-size` and the session share one set helper.
  - Writing `/dev/fbN` without root needs the host to tag fb devices
    `uaccess`; that rule is host configuration, outside this repository.
- **Verification**:
  - `make -C commands/tam-monitor check`: 73 tests pass (16 CLI fixture,
    31 recovery-guard fixture, 26 process tests), including oversize and
    malformed sizes, missing access, sysfs fallback, fit-then-restore order,
    keeping the smaller monitor, targeted blank and preview.
  - Fred's trial on a real VT with the 0.3.0 development build: `keep DP-1
    --shell` showed the console full screen on the 2560x1440 monitor; on
    exit the two 1080p monitors returned with the console at 1080p, not
    cropped.
