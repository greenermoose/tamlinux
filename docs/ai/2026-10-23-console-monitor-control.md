# Monitor control without a graphical desktop

- **CLI Tool**: Codex CLI (`codex`) `0.164.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted implementation directed by Fred.
- **Commit**: The commit introducing this record contains the implementation.
- **Guiding prompts**:
  > Explain why the monitors can be blanked and controlled from the graphical shell but not from the Linux text terminal shell. If necessary, create a TUI tam-* command that will allow monitors to be controlled just as well from a Linux terminal as from a graphical shell environment.

  > Looks good. I accept. Close the review window. Proceed.

Fred clarified that the target is a real Linux text console, including without
the desktop. He reviewed and accepted the local design before implementation.
The first scope provides console blank/wake/idle and supported hardware
brightness; independent output modesetting requires a later native DRM/KMS
backend and restoration proof. The interface explicitly reports those limits.

`tam-monitor` reads kernel connector metadata, uses existing DDC/backlight
helpers with deadlines and hardware readback, and validates console ownership,
foreground process group, active VT and text mode before console changes.
The guard alone performs forced blanking, retaining its controlling session
for the kernel ioctl while using a separate process group to survive terminal
interrupts. Caller death closes a private control socket and requests wake;
a fixed timeout also bounds a stalled/stopped caller. It refuses to poke a
different VT after a switch. Console idle writes use the kernel console
interface and verify the exported runtime interval where available.

Verification: 25 focused tests pass, including pseudo-terminal curses and
real subprocess recovery tests with substituted console/hardware operations.
The full commands development package builds with its checks. This is a
development build from an immutable local source snapshot, not a prepared
candidate or installed assembly. No stage, source pin, version, native package,
boot/login configuration or live monitor setting changed. Physical console
blank/wake, power saving and device ACL behavior still require packaged Test.
