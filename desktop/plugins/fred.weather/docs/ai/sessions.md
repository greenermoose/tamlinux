# AI Sessions & Prompt Log

This document records the exact prompts, tools, and models used during the development of `fred.weather`.

---

## Session 2026-09-18: Initial Implementation, Multi-Monitor Focus Isolation & 10-Day Forecast

- **Primary Tool:** Antigravity CLI (`agy 1.2.6`)
- **Model:** Gemini 3.8 Flash (High)
- **Role:** Full-stack QML/JS/Python engineering, security baseline compliance, and testing.

### Guiding Prompt
> "Create fred.weather as a clone replacement for the stock omarchy.weather widget. Follow the example for fred.clock in terms of making it part of the omarchy ecosystem and following all security requirements. Use https://github.com/daniellopez12/just-right-weather as an inspiration. Make sure to credit that plugin for ideas and link to that repo so people can see that plugin to compare. In fred.weather, we need to provide a daily, next 48 hours, and a ten day forecast. When you hover you should see the name and version # of the widget and the footer in the expanded view should include the name and version number. Like fred.sysinfo, you should be able to have the widget expanded in another monitor and still be able to type and use applications in other windows. That will allow you to see the full weather forecasts while you're writing emails or doing something else in another monitor. Also, I don't like the sun icon. It looks more like monitor brightness than a sun. Find another icon that looks more like a sun for sunny weather. And on hover, the daily forecast should appear."

### Key Technical Outputs
- Created `WeatherPanelWindow.qml` with single-monitor layershell surface and conditional keyboard focus.
- Implemented `HourlyForecast.qml` with 48h timeline canvas curve and solar markers.
- Implemented `DailyForecast.qml` with 10-day vertical outlook.
- Implemented `Model.js` with Font Awesome Sun (`\uf185`) and rich hover tooltip.
- Automated unit test coverage via `tests/model.test.cjs`.

---

## Session 2026-09-18: Hover Tooltip Layout Refinement & Version 1.0.1

- **Primary Tool:** Antigravity CLI (`agy 1.2.6`)
- **Model:** Gemini 3.8 Flash (High)
- **Role:** QML/JS tooltip engineering and test refinement.

### Guiding Prompts
> "For fred.weather on hover, move the version to the bottom, display it in a toned-down size and font color like the way the version is displayed in the clock expanded panel (provided as an example), and leave a space above the version line. Change the first line to Weather report for <Location>. Replace <Location> with the city and state or province (whatever the local country does to specify a city). For example, Brunswick, Maine. Bump the version number and push to GitHub when you have made these changes. Ask if you have any questions."
>
> "If changing font color or size is a problem for the hover, you can just use plain text but skip a line above the version. The version should be at the bottom of the tooltip and separated from the rest of the info displayed."

### Key Technical Outputs
- Added `formatLocationDisplay` in `Model.js` to combine city and state/province (e.g., `Brunswick, Maine`).
- Updated `buildBarHoverTooltip` in `Model.js` to begin with `Weather report for <Location>`, followed by conditions and forecast lines, a blank separator line, and `fred.weather v1.0.1` anchored at the bottom.
- Bound `reportLocation` in `Panel.qml` to `Model.formatLocationDisplay(configuredLocation, areaInfo, wttrLocation)`.
- Bumped version to `1.0.1` across `manifest.json`, `BarWidget.qml`, `Panel.qml`, `README.md`, and unit tests.

---

## Session 2026-09-18: Custom Hover Popup Styling, IPC Control & Version 1.0.2

- **Primary Tool:** Antigravity CLI (`agy 1.2.6`)
- **Model:** Gemini 3.8 Flash (High)
- **Role:** QML popup engineering, IPC architecture, visual asset capture, and release management.

### Guiding Prompts
> "Use the hp monitor for screen capture. Add a screen capture of the weather widget for the repo. Show bar, hover, and opened panel. Ask if you have questions."
>
> "Can't you programmatically control the plugin to display hover or panel? Do you have to fake moving a cursor over it?"
>
> "Keep going."

### Key Technical Outputs
- Implemented custom `PopupWindow` with `BorderSurface`, `Column`, and `Repeater` in `BarWidget.qml` to display styled hover lines with toned-down caption size and dimmed opacity (`0.45`) version footer separated by blank spacing, matching the design aesthetic of `fred.clock`.
- Factored `buildBarHoverLines` in `Model.js` to return pure content lines separate from the styled version footer.
- Added `showHover` and `hideHover` programmatic IPC entry points in `Panel.qml` and `WeatherStore.js` across both `fred.weather` and `omarchy.weather` namespaces.
- Enhanced monitor matching in `WeatherStore.js` to inspect monitor name, model, make, and descriptions across registered panels and Hyprland monitors.
- Captured high-resolution screenshots on the HP monitor (`HDMI-A-1`) showing the bar widget, active hover popup, and expanded focus-isolated weather panel, composited cleanly into `assets/screenshot.png` and `preview.png`.
- Bumped version to `1.0.2` across `manifest.json`, `BarWidget.qml`, `Panel.qml`, `Model.js`, `README.md`, and unit tests (`tests/model.test.cjs`).

---

## Session 2026-09-18: Multi-Monitor Broadcast, Retry Hardening & Resume Sync (Version 1.0.3)

- **Primary Tool:** Antigravity CLI (`agy 1.2.6`)
- **Model:** Gemini 3.8 Flash (High)
- **Role:** Bug diagnosis, multi-monitor broadcast architecture, retry error handling, and system resume integration.

### Guiding Prompts
> "Why is my MSI monitor still showing sun when my dell and hp are showing night time? It is after dark. Is there a failure to update certain monitors?"
>
> "Permanent fixes 1 and 3 sound good to me. Tell me more about fix #2. What does scheduleDailyForecastRetry() do and what calls and when?"
>
> "Great, let's do all 3 permanent fixes. Ready? Go!"

### Key Technical Outputs
- Diagnosed post-suspend timer freeze on non-hotplugging USB-C display (`DP-2`, MSI MP161) vs. recreated bars on hotplugging displays (`DP-1`, `HDMI-A-1`).
- Implemented `refreshAll(sourcePanel)`, `broadcastDailyForecast()`, and `broadcastReport()` in `WeatherStore.js` to synchronize weather state across all monitor panels immediately when any panel updates.
- Defined `scheduleDailyForecastRetry()` with exponential backoff (`dailyForecastRetryTimer`) in `Panel.qml` to handle early-wake network offline errors gracefully.
- Wired `omarchy-shell -q fred.weather refresh &` into `run_once()` in `msi-mp161-resume-workaround`.
- Added unit tests for `refreshAll` and payload broadcasting in `tests/model.test.cjs`.
- Bumped version to `1.0.3` across `manifest.json`, `BarWidget.qml`, and `Panel.qml`.

---

## Session 2026-09-18: Daily Forecast Local Timezone Alignment (Version 1.0.4)

- **Primary Tool:** Antigravity CLI (`agy 1.2.6`)
- **Model:** Gemini 3.8 Flash (High)
- **Role:** Root-cause analysis of timezone off-by-one bug, local/location date normalization, cache rollover defense, and unit test expansion.

### Guiding Prompts
> "Figure out why on Fri Sep 18 the ten day outlook thinks it's Saturday Sep 19. I'm guessing timezones are not being handled properly. Fidn the root cause and fix in fred.weather. Bump the version of fred.weather when you do and push to GitHub. Then let me test on this system before we make a release."

### Key Technical Outputs
- Identified root cause: `Panel.qml` calculated `todayString` via `new Date().toISOString().slice(0, 10)`. Because `.toISOString()` converts to zero-offset UTC time, any local time after 20:00 EDT (UTC-4) rolled over to the next day's UTC date (`2026-09-19`), causing the 10-day outlook to mark Saturday Sep 19 as "Today" and render Friday Sep 18 as a preceding day.
- Implemented `localDateString(date)` and `forecastTodayString(report, nowMs)` in `Model.js` to compute the calendar date in the target location's timezone using Open-Meteo's `utc_offset_seconds`, falling back safely to local machine time.
- Updated `openMeteoForecastDays()` to filter out dates strictly before `todayString`, preventing stale cached daily entries from appearing above "Today".
- Updated `openMeteoCurrentCondition()` to dynamically locate today's index in `daily.time` via `todayString`, ensuring current condition hi/lo and rain probability match the active day.
- Bound `todayString` in `Panel.qml` to `Model.forecastTodayString(dailyForecastReport, forecastClock)`.
- Added unit tests in `tests/model.test.cjs` covering negative and positive timezone offsets, late-evening rollover scenarios, cached data rollover across midnight, and dynamic today index resolution.
- Bumped version to `1.0.4` across `manifest.json`, `BarWidget.qml`, `Panel.qml`, and `Model.js`.



