# Packaged desktop helpers

`tam-shell` sends a bounded IPC call to the running Tamlinux shell. It resolves
the managed shell symlink to the same immutable path used by session startup;
`-q` makes an unavailable host/target/method a quiet best-effort result.
`TAMLINUX_SHELL_DIR` overrides the default XDG data path and
`TAMLINUX_SHELL_IPC_TIMEOUT` overrides the two-second IPC deadline.

The command package also delivers this direct desktop dependency chain:

| Command | Behavior | Dependencies |
| --- | --- | --- |
| `tam-shell` | IPC to an already running shell; does not launch it | Quickshell `qs`, coreutils, grep |
| `tam-menu-select` | Show options and return the chosen label | `tam-shell`, Perl (Encode/JSON::PP), coreutils |
| `tam-menu-timezone` | Select and apply a system timezone, then confirm | `tam-menu-select`, `tam-notification-send`, systemd timedated and host polkit |
| `tam-agent` | Read the default agent or launch/pick it | `tam-menu`, `tam-cmd-present`, `tam-launch-tui`, selected agent |
| `tam-default-agent` | Read/select a retained default, installing through Mise when needed | `tam-agent`, `tam-cmd-present`, presentation terminal, coreutils, grep, Mise |
| `tam-audio-input-set-default` | Select a microphone default and move existing capture streams | `wpctl`, `pactl`, awk; independent sound servers |
| `tam-cmd-present` | Test command availability on PATH | Bash |
| `tam-launch-tui` | Launch discrete command arguments in a terminal | coreutils, util-linux, UWSM `uwsm-app`, `xdg-terminal-exec`, selected terminal |

Nix delivery wraps these helpers with their own package's command directory and
declared runtime tools. Quickshell, UWSM, terminal integration and authorization
remain independent host prerequisites. The agent launcher uses the user's
`${XDG_CONFIG_HOME:-$HOME/.config}/tamlinux/defaults/agent`; it picks no agent
automatically. Agent-specific software and optional launch adapters must be
declared when those choices are enabled. The default-agent setter is now owned
and packaged. OpenClaw and Hermes support were retired on 2026-10-12; existing
selections are preserved on disk but cannot launch through `tam-agent`.

Each command has a Makefile check/install interface and an MIT license. Run
`make check` here for installed-command integration checks across the chain.
Python 3 and Perl are needed for those checks. Tests record IPC, terminal and
timedated boundaries; they do not launch agents, open windows, change the
system timezone or establish clean-host desktop acceptance. Every component
supports `make install PREFIX=/path/to/package` and `DESTDIR` staging.
