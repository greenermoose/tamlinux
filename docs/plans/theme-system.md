# Theme system, fonts and identity

**Status — 2026-10-07:** design direction chosen; implementation planned for
stage 0.5, after settings/menu ownership (0.4) and before native package/system
ownership and final Omarchy removal (0.6). Hyprland remains the daily compositor.
The Sway adapter is later integration, not a theme-system prerequisite.

## Purpose and design

Give the shell and supported applications a consistent, accessible Tamlinux
appearance with one maintained source. The chosen Tamarack direction uses a
dark green palette with green/gold accents, a required light variant, Atkinson
Hyperlegible UI text and Mono Nerd terminal/glyph roles. Use solid surfaces,
small borders/gaps and a small radius; avoid blur, shadows, transparency and
decorative animation. Confirm actual font families, licenses and package
availability during implementation.

One versioned, machine-readable token schema defines colors, font roles,
sizes, spacing, borders and motion. Packaged defaults, validated user overrides
and generated app output have distinct ownership. Shared QML consumes generated
values from that schema. App adapters may interpret supported tokens, but do
not maintain independent hand-copied palettes. Validate token ranges and required
WCAG contrast pairs in both variants before applying.

Theme/font/background preferences and generated state use Tamlinux XDG paths.
Import relevant old choices once when destinations are absent; preserve existing
preferences, custom assets and licenses. Replace the inherited current-theme
directory and indirect application imports together with all readers/writers.
An independently owned background link may be used by the background service.

## Steps

| Step | Deliverable | Evidence |
| --- | --- | --- |
| **0.5.0** | Token schema, dark/light variants, validation and consumer inventory | Contrast checks, invalid-input rejection, consistent shell preview. |
| **0.5.1** | Deterministic generator, coherent apply/rollback and theme/background migration | Supported apps and every retained theme/background action work; persistence, idempotence and partial-failure recovery. |
| **0.5.2** | Independently packaged fonts, glyphs and selection/install behavior | Readable roles and glyph coverage at supported scales; no legacy-font dependence. |
| **0.5.3** | Mark/wordmark, menu/bar, login, About and screensaver identity | Actual surfaces and fallbacks verified; inherited branding/version aliases retired. |

Generate supported shell, Hyprland, terminal, btop, Neovim, GTK/Qt and Chromium
output only after proving each adapter's format and reload behavior. Inventory
installed consumers and indirect imports before declaring the cutover complete.
Retain font selection and custom theme/wallpaper import functions with a
validated data format and explicit conversion handling for unsupported formats.
Never drop a working function simply to eliminate a dependency.

## Apply and recovery contract

Generate into staging with a manifest of output files, hashes, owners and reload
requirements. Validate before active writes; apply one coherent selection and
retain the prior working output/data set. Test interrupted writes, invalid input,
partial reloads and restoration. Do not overwrite unrelated app configuration;
define how user changes to generated files are reconciled. Unchanged input
does not cause unnecessary writes or restarts. No background theme poller.

Privileged login/boot output belongs to installed system owners, separate from
ordinary user theme writes. Boot assets are integrated with the boot project
and its recovery checks before final removal at 0.6. Theme acceptance cannot
claim a pending boot change was applied. Host OS metadata remains accurate.

Test actual apps, new terminal windows where needed, shell restart and login,
dark/light and font changes and return, custom assets, missing glyph fallback
and current display scales. Preserve mutable settings, app files and package
artifacts as well as deployment generations. Resource/energy claims need a
reproducible measured workload and stated uncertainty. Public page styling
follows acceptance and the publication workflow.

See [desktop decoupling](desktop-decoupling.md) and
[versioning](../../VERSIONING.md) for stage gates. This document delivers a
plan; it does not install fonts, apply a theme or advance the product version.
