# Visible text boot and explicit desktop startup

- **CLI Tool**: Codex CLI `0.164.0`.
- **Model**: `gpt-6.1-sol`.
- **Transcript**: Retained privately by the author.
- **Authorship**: Fred approved the plan and boundary; Codex developed the
  launcher, package-source removals, tests and documentation.

## Guiding prompts

> Anything that provides or forces a graphical login or shows graphics during the boot process should be removed from Tamlinux. That is wasteful extra stuff I do not need or want.

> When my machines boot, I want to see the normal text-only boot sequence so I can see exactly what they are loading and what is happening as soon as possible in the boot process.

Approval, excerpt:

> I approve. Proceed. You can close the review window. Ask if you have any further questions.

## Implementation and boundary

The reviewed [plan](../plans/console-first-startup.md) preserves the selected
minimal root-stock and bootstrap helper. Work begins after choosing Tamlinux
to boot; it does not redesign firmware or upstream media. Physical proof on
the first workstation precedes trying the second.

`tam-desktop` validates the foreground text VT and actual local login,
refreshes the session identity, rejects an existing graphical session and
enters the installed immutable generation. The internal UWSM launch disables
the system graphical-target wait. Greeter assets and chooser registration
were removed; the native command now enters `tam-desktop`. Historical SDDM
PAM recovery source remains unshipped.

Initial verification: 14 focused launcher, console-identity and native-entry
tests pass. Package and physical lifecycle verification are recorded as they
complete; this record does not assert physical text boot, desktop locking or
fleet acceptance. No Test/Run/Release or workstation boot mutation is implied.
