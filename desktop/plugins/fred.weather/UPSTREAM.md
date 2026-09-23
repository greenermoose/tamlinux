# Upstream Provenance: `fred.weather`

`fred.weather` originated as an in-place clone replacement of the stock Omarchy weather plugin, enhanced with timeline architecture inspired by `daniellopez12/just-right-weather`, multi-monitor focus isolation, and an extended 10-day forecast.

## Field surveys

The Omarchy clone and Just Right Weather references below are the existing starting map. For a new requested survey, revisit those sources and search current forks and independent weather interfaces. Save dated findings in [upstream/](upstream/) and link each result here.

---

## 1. Upstream Omarchy Component

- **Package:** `omarchy`
- **Distro Release:** `4.0.4-1` (Arch Linux / Omarchy)
- **Source Directory:** `/usr/share/omarchy/shell/plugins/panels/weather/`
- **Date Cloned:** 2026-09-18
- **Upstream License:** MIT

### Upstream Inspection Diff Command

```bash
diff -u -r /usr/share/omarchy/shell/plugins/panels/weather ~/Code/tamlinux/weather-fred-tamlinux
```

### Upstream Copyright Notice

```
Copyright (c) 2024-2026 Omarchy Contributors

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

## 2. Inspiration & Architectural Credit: `just-right-weather`

The 48-hour timeline canvas curve, chronological sunrise/sunset event positioning, and combined Open-Meteo bundling were inspired by:

- **Project:** Just Right Weather
- **Author:** Daniel Lopez (`daniellopez12`)
- **Repository:** https://github.com/daniellopez12/just-right-weather
- **License:** MIT

`fred.weather` extends these concepts with:
- Multi-monitor focus isolation (independent typing across screens while expanded)
- Extended 10-day daily forecast
- Font Awesome Sun (`\uf185`) for crisp, non-ambiguous daylight rendering
- Bar hover tooltip displaying widget name, version, and daily forecast summary
- Centered version footer matching `fred.clock` and `fred.sysinfo`
- Hardened security baseline complying with marketplace issue #6509
