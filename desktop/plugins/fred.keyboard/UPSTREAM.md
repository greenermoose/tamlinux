# Upstream Provenance

`ExplorerPanel.qml` is a clone of one stock Omarchy shell component, the
panel window a bar widget opens under its icon. Everything else in this
plugin was built from scratch (see `README.md`, "Prior art").

- **Upstream Project:** [Omarchy](https://omarchy.org/)
- **Upstream Version:** 4.0.4-1
- **Upstream Path:** `/usr/share/omarchy/shell/Ui/KeyboardPanel.qml`
- **Clone Date:** 2026-09-20
- **Upstream License:** MIT

## Why a clone

The stock panel places a transparent click-catcher on every other output so
that a click anywhere on any monitor dismisses it. This explorer is meant to
stay open while its owner works in an app on another monitor, so that block
is removed. There is no switch for it upstream; the component had to be
copied. The layer-shell namespace is renamed so the two are distinguishable
in `hyprctl layers`. Nothing else is changed.

## Upstream Diff Recipe

```bash
diff -u /usr/share/omarchy/shell/Ui/KeyboardPanel.qml \
        ~/.config/omarchy/plugins/fred.keyboard/ExplorerPanel.qml
```

Expected drift: the header comment, one `import qs.Ui`, the namespace, and
the removed `Variants` block. Anything else means upstream moved and the
clone should be refreshed.

## Upstream MIT License Notice

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
