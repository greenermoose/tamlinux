# Use `sudo` in kernel console VTs and `pkexec` elsewhere in `tam-deploy`

Updates `tam-deploy` privilege escalation so console activation and undo helpers
work cleanly in a kernel console virtual terminal (where `pkexec` / polkit agent
prompts cannot run) while keeping `/usr/bin/pkexec` for graphical desktop sessions
and non-console callers:

- **`_console_tty()` & `Deployment.bundle_privileged()` (`commands/tam-deploy/tam-deploy`):**
  Detects an interactive kernel console virtual terminal only when both `DISPLAY`
  and `WAYLAND_DISPLAY` are unset, `sys.stdin.isatty()` is true, and
  `os.ttyname(0)` matches `/dev/tty[1-9][0-9]*`. Only under that condition does
  `bundle_privileged()` invoke `/usr/bin/sudo /usr/bin/tam-bundle ...`; graphical
  sessions, PTYs, and non-interactive callers continue invoking `/usr/bin/pkexec
  /usr/bin/tam-bundle ...`.
- **`Deployment.console_helpers()` (`commands/tam-deploy/tam-deploy`):** Updates
  the helper guidance message to note `sudo` on a kernel console and `pkexec`
  otherwise.
- **Regression test (`commands/tam-deploy/tests/test_deploy.py`):** Adds
  `test_bundle_privileged_uses_sudo_only_on_kernel_console`, verifying
  `/usr/bin/sudo` for `/dev/tty1` without `DISPLAY`/`WAYLAND_DISPLAY` and
  `/usr/bin/pkexec` for `/dev/pts/0`, non-TTY stdin, `WAYLAND_DISPLAY`, and
  `DISPLAY`.

Verification: 130 `tam-deploy` unit tests passed (`python3 -B -m unittest
discover -s commands/tam-deploy/tests -v`); 18 real-engine
`bundle_integration.py` tests passed in mandatory PID namespace isolation.

- **Date:** 2026-11-14
- **CLI Tool:** Antigravity CLI (`agy`) `1.5.9`
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted implementation, documentation and tests.

## Guiding prompts

> I'm running in a kernel console virtual terminal. pkexec doesn't work there. That's why I have to do sudo. Should I start a graphical desktop? Or can you revise so that I can do everything from a kernel console.
>
> That needs to be put in context. AI agents that are asking for escalated privileges when I'm using them on the graphical desktop need to use pkexec with absolute paths. But when I'm running commands in a kernel console, I use sudo.
