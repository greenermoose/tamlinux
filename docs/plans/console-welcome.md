# Tamlinux console welcome

Status: accepted for development; no login changes made. The banner generator
and native vendor issue fragment are in development for 0.5.6. Binding native
package installation, update and rollback to the assembly is not yet complete.

The text console should welcome people to Tamlinux, identify the cultivar and
rootstock, and remain useful when recovering the graphical session. The
accepted symbol is a simple text tamarack:

```text
       /\
      /\/\
     ///\\\       Welcome to Tamlinux!
       ||

     Cultivar:  Blue Sparkler 0.5.5
     Rootstock: Arch Linux (rolling)
     Kernel:    7.2.11-arch1-1.1
     Console:   tty2

hostname login:
```

The values shown are an example, not fixed product defaults. Keep the host's
normal login prompt, and use plain ASCII so the message works on a basic Linux
console. Rootstock identity comes from the host OS; the console name comes
from the login service. Show the running kernel release separately from the
rootstock distribution and its version or rolling-release designation, and
include the OS version where one exists. Do not label the kernel as the OS
version.

## Identity and delivery

The banner is displayed before a user is known, while the current cultivar
and version describe a per-user installation. Do not read an arbitrary user's
home or imply that every user has the same cultivar. Propose an explicitly
configured machine-level selection that identifies the selected Tamlinux
assembly, updated and rolled back with that assembly. If no trustworthy
selection exists, show a generic Tamlinux welcome and omit the cultivar
version. Resolve the exact source and ownership as part of implementation;
do not introduce a second manually maintained version authority.

Investigate the host's existing getty and issue-file precedence before choosing
the integration. Deliver the product banner through a recorded
`tamlinux-packages` assembly, with host-specific configuration administered
separately. Preserve the host OS identity, user overrides, and console login.
Avoid a background service or network dependency for display.

## Acceptance

- Confirm the selected assembly's identity is displayed accurately, updates
  and rollback follow the selected assembly, and missing identity has a safe
  fallback. Test a multi-user or differing-selection case.
- Check the rendered text, host identity, running kernel release, terminal
  name and login prompt in a controlled environment. Confirm plain ASCII and
  narrow-console readability.
- Before any actual login change, record the previous Home Manager generation
  and a Snapper snapshot; obtain approval for the concrete privileged step.
  Test and Run of an exact assembly require their respective stage words.
- Fred verifies a physical console login and recovery after the candidate is
  installed; automated rendering does not establish that the console works.
