# Upstream Provenance

This plugin began life as a clone of the stock Omarchy display panel widget (`omarchy.monitor`).

## Field surveys

The Omarchy clone provenance and license notice below remain the code-ancestry record. For a requested display-panel survey, start with that source and its forks, then compare independent display tools. Save dated findings in [upstream/](upstream/) and link each result here.

- **Upstream Project:** [Omarchy](https://omarchy.org/)
- **Upstream Version:** 4.0.4-1
- **Upstream Path:** `/usr/share/omarchy/shell/plugins/panels/monitor/`
- **Clone Date:** 2026-09-18
- **Upstream License:** MIT

`MonitorPanelWindow.qml` in v1.1.0 is adapted from Omarchy's
`/usr/share/omarchy/shell/Ui/KeyboardPanel.qml`. It retains the owner-output
layer-shell surface, focus prime, popout coordination, animation, local
outside-click dismissal, and bar click forwarding, while intentionally
omitting upstream's `Variants` block of transparent dismissal windows on
other outputs. The adapted component remains covered by the upstream MIT
notice below and the plugin's GPL-3.0-or-later distribution terms.

## Upstream Diff Recipe

To compare this plugin's files against the upstream Omarchy distribution:

```bash
diff -u -r /usr/share/omarchy/shell/plugins/panels/monitor ~/Code/tamlinux/monitor-fred-tamlinux
```

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
