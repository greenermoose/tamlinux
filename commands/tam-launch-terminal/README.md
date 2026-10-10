# Terminal and editor launch chain

These product commands are installed by `commands/<name>/Makefile` into
`$PREFIX/bin/<name>`. Delivery resolves sibling helpers from the same command
output and supplies their implementation tools. UWSM, xdg-terminal-exec,
Hyprland and consumer-selected terminal/editor applications are host providers.

| Interface | Caller and behavior | Owned mutable interface |
| --- | --- | --- |
| `tam-launch-terminal [command...]` | Bar terminal actions and session keybindings; opens the focused terminal's directory | `tam-cmd-terminal-cwd`; Kitty remote socket `$XDG_RUNTIME_DIR/tamlinux-kitty-<pid>` |
| `tam-launch-editor [--inline] [paths...]` | Config editor and session editor actions; terminal editors use `tam-launch-tui`, graphical editors use UWSM | `${XDG_STATE_HOME:-$HOME/.local/state}/tamlinux/defaults/editor`; absent/unavailable selection uses baseline `nvim` |
| `tam-launch-config-editor <path>` | Menu config actions; low-urgency notice and selected editor open the same path | Same editor state; notification failure does not prevent editing |
| `tam-launch-floating-terminal-with-presentation <command> [args...]` | Menu maintenance actions; Tamlinux wordmark and completion pause | `${XDG_STATE_HOME:-$HOME/.local/state}/tamlinux/current/theme/gum_env.lua` |
| `tam-default-editor [selection]` | Menu checked expressions and editor selection | Same editor state as the launcher |
| `tam-default-terminal [selection]` | Menu checked expressions and terminal selection | `${XDG_CONFIG_HOME:-$HOME/.config}/xdg-terminals.list`; standard terminal desktop-entry IDs |

The presentation launcher retains the menu's single-argument shell-expression
interface. With multiple arguments it executes a command vector, preserving
spaces, quotes and option-like data. It returns the command's status and skips
the completion pause for status 130. `tam-show-done` exits when there is no
controlling terminal. `tam-show-logo` retains the current text wordmark.

The directory helper uses Kitty remote control when its owned socket exists;
otherwise it inspects the focused terminal's shell child. Invalid/missing window,
shell or directory returns `$HOME`. Kitty and its `kitten` tool are optional
selected-application facilities. Later packaged Kitty defaults must create the
matching owned socket. No inherited socket/theme fallback is consulted.

Editor state already uses the owned location, so no conversion is required
for this transfer. The theme path and Kitty producer cutover still require the
theme/defaults migration manifest before Test. Existing terminal preferences
remain at their standard XDG path; selection creates a missing config directory.
Rollback uses the retained old command output and preserved original settings;
this component test does not implement the overall upgrade/rollback transaction.

Run `make -C commands/tam-launch-terminal check` for the installed-chain tests.
They isolate home/XDG/PATH, create local socket fixtures and record terminal/IPC
boundaries. Delivery also runs the real wrapped output with a minimal host PATH.
Physical terminal rendering and fresh graphical login remain installation tests.
