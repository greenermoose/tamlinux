# Upstream Provenance: `fred.tides`

`fred.tides` originated as an Omarchy shell bar plugin inspired by and adapting concepts from `Woogy7/omarchy-tides`, enhanced with multi-monitor focus isolation, security-hardened execution, glanceable bar hover telemetry, configurable units, and a modular provider architecture (Open-Meteo Marine in v1.0; NOAA and harmonic calculations in v1.1).

---

## 1. Upstream Inspiration & Component

- **Project:** Tides for Omarchy (`omarchy-tides`)
- **Author:** Woogy7 (`Woogy7`)
- **Repository:** https://github.com/Woogy7/omarchy-tides
- **Marketplace ID:** `io.github.woogy7.tides`
- **Upstream License:** MIT
- **Date Adapted:** 2026-09-18

### Upstream Inspiration Diff Command

```bash
diff -u -r ~/Code/omarchy-fred-tides <(git clone https://github.com/Woogy7/omarchy-tides /tmp/upstream-tides && echo /tmp/upstream-tides)
```

### Upstream Copyright Notice

```
MIT License

Copyright (c) 2026 Woogy7

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 2. Additional Inspiration: `linecast`

The daylight-shaded curve gradients and terminal-grade aesthetic simplicity were inspired by:

- **Project:** Linecast (`linecast tides`)
- **Author:** ashuttl (`ashuttl`)
- **Repository:** https://github.com/ashuttl/linecast
- **License:** MIT

---

## 3. Fred Suite Extensions in `fred.tides`

`fred.tides` refactors and extends the original design to adhere to Fred's suite conventions:
- **Multi-Monitor Focus Isolation:** Implements `TidesPanelWindow.qml` and `TidesStore.js` with `WlrKeyboardFocus.OnDemand` strictly scoped to the panel's monitor, eliminating modal lockout on secondary monitors.
- **Glanceable Bar Tooltip:** Provides hover telemetry showing widget name, version (`fred.tides v1.0.0`), current water level, trend (rising/falling), and exact countdown to the next high or low tide.
- **Security Baseline:** Sanitized execution environment (`LANG=C`, `PATH=/usr/bin:/bin`), hard curl timeouts (5s connect, 10s max), response size caps, and descriptor-relative atomic cache writes to `~/.cache/fred.tides/cache.json`.
- **Modular Provider Architecture:** Structured for Open-Meteo Marine API in v1.0 with abstraction stubs for NOAA CO-OPS and local mathematical harmonic calculations in v1.1.
- **Unit Configuration:** Seamless toggle between Metric (`m`) and Imperial (`ft`) heights.
- **Suite Consistency:** Centered version footer, GPL-3.0-or-later licensing, and dual-artifact workflow.
