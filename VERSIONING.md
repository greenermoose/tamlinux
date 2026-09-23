# Tamlinux versioning

Tamlinux uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The published number is the file [`VERSION`](VERSION) in this repository.
The workstation checkout [`config-fred-tamlinux`](https://github.com/greenermoose/config-fred-tamlinux)
keeps a matching `VERSION` so the running machine and this explainer agree.

## What the numbers mean

| Series | Meaning |
| :-- | :-- |
| **0.x** | Tamlinux is still based on [Omarchy](https://omarchy.com), plus Fred's patches and `fred.*` plugins. |
| **1.x** and later | The Omarchy dependency has been removed. Tamlinux still borrows ideas from Omarchy and keeps up with upstream Quickshell, Hyprland, Wayland, and Nix. |

**0.0.1** is the first workstation snapshot: this daily driver, working as
Tamlinux. An installer for a second computer (a fresh install) comes only
after 0.0.1 is solid on this machine.

Bump the product version when Fred decides Tamlinux itself changed, not on
every Home Manager switch. Write the new number in both `VERSION` files, log
it in [`CHANGELOG.md`](CHANGELOG.md), and keep the two files identical.

## What Tamlinux version is not

Plugin versions (`fred.workspaces`, `fred.clock`, and the rest), the
`tam-plugin` CLI, and the `ecosystem-fred-tamlinux` patch registry stay
independent artifacts. They have their own `VERSION` or `manifest.json`
numbers.

`config-fred-tamlinux` **1.5.1** is the last overlay-era composite. Those git
tags stay. They are no longer the product version. 0.0.1 is that overlay
frozen into Tamlinux.

## Tamlinux version vs Home Manager generation

These are two different counters. Do not set Tamlinux to `0.0.x` where `x` is
the Home Manager generation.

| | Tamlinux version | Home Manager generation |
| :-- | :-- | :-- |
| What it is | Declared product snapshot (portable, tagged, changelogged) | Local activation counter on one machine |
| Source of truth | `VERSION` files | `home-manager generations` / `~/.config/tamlinux/generation` |
| Advances when | Fred decides the product changed | Every successful `home-manager switch` |
| Portable? | Yes — the same number on a second computer | No — a fresh machine starts at 1 |

On a running workstation:

```bash
echo "$TAMLINUX_VERSION"                 # product version (0.0.1)
cat ~/.config/tamlinux/version           # same number
cat ~/.config/tamlinux/generation        # this machine's Home Manager generation
home-manager generations                 # full local rollback list
```

`$OMARCHY_CONFIG_VERSION` and `~/.config/omarchy/version` remain as 0.x
compatibility aliases of `$TAMLINUX_VERSION`. They are not a second product.
