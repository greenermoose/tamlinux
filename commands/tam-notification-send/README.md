# tam-notification-send

Send a Tamlinux desktop notification through the standard session D-Bus
notification service. Requires Bash, `busctl` (systemd) and `jq`.

The default application identity is `tamlinux-action`. The shell uses
`tamlinux-glyph` for a custom glyph and `tamlinux-exec-argv` for click actions.
The sender and shell receiver must be delivered together. The packaged reminder
writer uses the same identity and glyph hint. No inherited wire-name fallback
is provided.

`--exec` takes a program and separate arguments at the end of the command;
arguments remain data, including spaces, newlines and shell metacharacters.
Headlines and descriptions are typed D-Bus strings, not parsed as sender options
after their positions have been selected. Other options retain their current
meaning: urgency, icon/image, expiration, replacement ID and printed ID.

Run `make check` (Python 3, Node.js and `jq` required for tests). It exercises
the installed sender against a recording D-Bus boundary and passes its actual
payload through the shell's notification model, including persistence and
restored click actions. These checks do not start the desktop or prove visual
acceptance. Install using `make install PREFIX=/path/to/package`; `DESTDIR` is
supported. Nix delivery supplies the runtime programs through a wrapper.

MIT; see LICENSE. Historical source attribution is retained in the executable.
