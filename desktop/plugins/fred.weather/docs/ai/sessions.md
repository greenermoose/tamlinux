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

