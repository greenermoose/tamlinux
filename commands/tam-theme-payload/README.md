# tam-theme-payload

Print a bounded, validated JSON palette, surface-role and style payload for
`tamlinux`'s shell. This is a non-resident adapter: it reads data, prints JSON
and exits. It performs no downloads, executes no theme code and writes no files.

The selected theme is under
`${XDG_STATE_HOME:-$HOME/.local/state}/tamlinux/current/theme`. It reads
`colors.toml` and `shell.toml`, then merges the user's
`${XDG_CONFIG_HOME:-$HOME/.config}/tamlinux/shell.toml` and finally
`${XDG_STATE_HOME:-$HOME/.local/state}/tamlinux/shell.toml` settings.
`--theme-dir`, `--override` and `--state` select explicit input paths.
Missing or malformed files use the existing defaults for their affected data.

Requires Python 3.11 or later. Run `make check`; install with
`make install PREFIX=/path/to/package`. The product command package discovers
this directory through its Makefile. This source transfer does not deploy the
command or move an existing user's selected theme; the 0.4.3 theme/assets
package and state migration must be ready before the candidate is activated.

GNU GPL v3 or later; see the repository LICENSE.
