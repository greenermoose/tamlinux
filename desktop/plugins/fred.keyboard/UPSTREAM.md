# Upstream Provenance

Two kinds of debt are recorded here: one file cloned from Omarchy itself
(section 1), and the earlier Omarchy plugins whose ideas shaped this one
without any of their code being used (section 2). Credit where due, both
ways.

## Field surveys

The cloned Omarchy component and the prior-art table below are the existing starting map. For a new requested survey, revisit those sources and search current forks and independent keyboard or binding tools. Save dated findings in [upstream/](upstream/) and link each result here.

## 1. Cloned code: `ExplorerPanel.qml`

`ExplorerPanel.qml` is a clone of one stock Omarchy shell component, the
panel window a bar widget opens under its icon. Everything else in this
plugin was built from scratch.

- **Upstream Project:** [Omarchy](https://omarchy.org/)
- **Upstream Version:** 4.0.4-1
- **Upstream Path:** `/usr/share/omarchy/shell/Ui/KeyboardPanel.qml`
- **Clone Date:** 2026-09-20
- **Upstream License:** MIT

### Why a clone

The stock panel places a transparent click-catcher on every other output so
that a click anywhere on any monitor dismisses it. This explorer is meant to
stay open while its owner works in an app on another monitor, so that block
is removed. There is no switch for it upstream; the component had to be
copied. The layer-shell namespace is renamed so the two are distinguishable
in `hyprctl layers`. Nothing else is changed.

### Upstream Diff Recipe

```bash
diff -u /usr/share/omarchy/shell/Ui/KeyboardPanel.qml \
        ~/.config/omarchy/plugins/fred.keyboard/ExplorerPanel.qml
```

Expected drift: the header comment, one `import qs.Ui`, the namespace, and
the removed `Variants` block. Anything else means upstream moved and the
clone should be refreshed.

### Upstream MIT License Notice

```text
MIT License

Copyright (c) Omarchy Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 2. Prior art that shaped the design (no code copied)

Found during the research round of 2026-09-19 by searching the Omarchy plugin
ecosystem by concept rather than by name. All are MIT licensed. Fred's
decision was to build rather than fork, so nothing below is vendored; each
entry says what it contributed. If any of their code is ever copied, that
file gets its own section above and the MIT notice applies.

| Plugin | What it does | What it gave this plugin |
| :-- | :-- | :-- |
| [`dai199/omarchy-visual-keybindings`](https://github.com/dai199/omarchy-visual-keybindings) | Explore and create bindings on an interactive keyboard | The closest sibling. Its independent use of Quickshell's `ShortcutInhibitor` corroborated the capture-mode mechanism; its Hyprland-submap fallback was considered and not adopted (documented in the plan). Its keycode table mixing evdev and X11 spaces is the hazard `Bindings.js` exists to avoid. |
| [`neilerua973/omarchy-keybindings-editor`](https://github.com/neilerua973/omarchy-keybindings-editor) | On-screen keyboard editor for binds | A cleanly modular file layout worth imitating; its own note that the arrow cluster and media row are "stacked as their own rows (a simplification vs. a physical keyboard)" is the fidelity problem the field-observed layout library answers. Its `KeyCapture.js` returning null for arrows, punctuation and media keys is why this plugin covers the full key set. |
| [`felixzsh/omarchy-key-visualizer`](https://github.com/felixzsh/omarchy-key-visualizer) | Shows keys as you type, for screencasts | Presentation ideas for the live board. |
| [`seth-wood/keyarchy`](https://github.com/seth-wood/keyarchy) | Scores which binds you actually use | The observation that unused shortcuts are worth surfacing; adjacent, not implemented here. |
| [`fze-fze/omarchy-shortcut-sheet`](https://github.com/fze-fze/omarchy-shortcut-sheet) | Tap Super for a live shortcut sheet | The reverse-lookup user experience: from a command to its keys. |
| [`YonatanBaum/omarchy-app-shortcuts`](https://github.com/YonatanBaum/omarchy-app-shortcuts) | Per-application cheat sheet | A per-application scope this plugin deliberately does not cover. |
| [`balazsorban44/omarchy-keyboard-minimap`](https://github.com/balazsorban44/omarchy-keyboard-minimap) | Keyboard minimap with global capture | The `/dev/input` approach that this plugin rejects by design: it is a system-wide keylogger, and the panel-scoped alternative here exists in contrast to it. |
| [`balazsorban44/omarchy-keybinding-coach`](https://github.com/balazsorban44/omarchy-keybinding-coach) | One binding at a time in the bar | The teaching angle: a bind is something to learn, not only to look up. |

Two things none of them do, and this plugin does because of that gap: report
the keyboard hardware's identity, and flag binds whose keys the attached
board cannot send.

The research itself was done by an Antigravity CLI session (`agy 1.2.7`,
Gemini 3.8 Flash High) and a Claude Code session (`claude 2.1.278`, Claude
Opus 5) under Fred's direction; see `AI_PROVENANCE.md`.
