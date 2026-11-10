# Native product installation for bundle recipes

- **CLI Tool:** Codex CLI 0.167.0
- **Model:** `gpt-6.1-sol`
- **Transcript:** Retained privately by the author.
- **Commits:** The commit adding this record and subsequent fixes naming it.
- **Authorship:** Codex implemented the approved native installation path.

## Guiding prompt

> Pick up where claude left off and work on tam-bundle. The goal is to finish tam-bundle and start using it on [redacted: host].

## Changes and verification

A top-level Makefile builds the six native C commands and installs every
command through its existing Makefile. The shared data installer supplies
the shell, plugins, owned assets and icon font, session entry points, menus,
native helper descriptors and user service units beneath the same prefix.
Units use stable prefix paths. Building enables and starts no services,
and writes no home configuration or system integration.

Third-party programs and fonts belong to native packages. There are no
Nix wrappers in this tree; version notes come from the bundle recipe.

`make`, staging `make install` and the three `make check-install` tests pass.
The tests compare two full data installations byte for byte, exercise an
installed menu away from the checkout, and check the prefix boundary and
generated units. The full staged product also seals successfully with
tam-bundle. These are build checks; native login and desktop cutover remain
separate integration steps.

The native adapter also gains login-shell and user-manager environment
templates. They append the product prefix during bring-up, retaining the
old delivery's precedence until an explicit cutover transaction. This does
not by itself enable a new shell service or change a running session.
