# start

First text-login workstation activities menu (D215 / D224).

From **0.2.0** onward, `start` is a **pure C** program linked only against
`libtam` (and libc). It is **not** a Python script and must not regain a
Python runtime dependency. It works on systems without a Python interpreter.

The interactive TUI (pager) is separate from the menu catalog it displays.
Edit the catalog in [`menu.json`](menu.json); do not hard-code activities in C
except for id-specific launch helpers (Frotz story prompt, pMARS warriors).

## Build

Requires an installed `libtam` (pkg-config `libtam`, or `LIBTAM_PREFIX`).

```bash
make
make check
make install PREFIX=$HOME/.local/dev
```

## Install layout

| Path | Content |
| :--- | :--- |
| `$PREFIX/bin/start` | Binary |
| `$PREFIX/share/start/menu.json` | Activity catalog |
| `$PREFIX/share/start/VERSION` | Command semver |
| `$PREFIX/share/licenses/start/LICENSE` | GPL-3.0-or-later |

Optional overrides: `START_MENU` points at an alternate catalog file;
`START_VERSION` overrides the version string (checked before VERSION files).

## Usage

```text
start              # interactive menu (TTY required)
start --list       # letter, id, command, installed, description
start --check      # per-item install marks and N/M summary
start --version|-V
start --help|-h
```

Opening the menu never starts graphics; the desktop launches only when the
user selects that activity. Quit with Esc (Backspace and Delete also quit).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
