const assert = require("node:assert/strict");
const test = require("node:test");
const Model = require("../Model.js");
const Network = require("../Network.js");

function sampleOpenMeteoPayload() {
  const start = Date.parse("2030-01-10T00:00:00Z");
  const time = Array.from({ length: 96 }, (_, i) =>
    new Date(start + i * 3600000).toISOString().slice(0, 16));
  const dates = [
    "2030-01-10", "2030-01-11", "2030-01-12", "2030-01-13", "2030-01-14",
    "2030-01-15", "2030-01-16", "2030-01-17", "2030-01-18", "2030-01-19"
  ];
  return {
    utc_offset_seconds: -18000,
    current: {
      temperature_2m: 22.0,
      apparent_temperature: 21.5,
      relative_humidity_2m: 55,
      wind_speed_10m: 12.0,
      wind_direction_10m: 315,
      weather_code: 0, // Clear
      is_day: 1
    },
    hourly: {
      time,
      temperature_2m: time.map((_, i) => 15 + (i % 10)),
      precipitation_probability: time.map(() => 20),
      precipitation: time.map(() => 0.5),
      weather_code: time.map(() => 0),
      is_day: time.map((_, i) => (i % 24 >= 6 && i % 24 < 18 ? 1 : 0))
    },
    daily: {
      time: dates,
      sunrise: dates.map(d => d + "T06:30"),
      sunset: dates.map(d => d + "T18:15"),
      temperature_2m_max: [24, 25, 23, 22, 21, 20, 22, 23, 24, 25],
      temperature_2m_min: [14, 15, 13, 12, 11, 10, 12, 13, 14, 15],
      weather_code: [0, 1, 2, 3, 45, 51, 61, 71, 80, 95],
      precipitation_probability_max: [10, 20, 30, 40, 50, 60, 70, 80, 90, 95],
      precipitation_sum: [0.0, 0.5, 1.2, 0.0, 0.0, 2.0, 5.5, 1.0, 12.0, 25.0]
    }
  };
}

test("sun icon maps to Font Awesome sun (U+F185) for clear day", () => {
  const iconDay = Model.iconForOpenMeteoCode(0, false);
  assert.equal(iconDay, "\uf185"); // Font Awesome sun

  const iconNight = Model.iconForOpenMeteoCode(0, true);
  assert.equal(iconNight, "\ue32b"); // Night moon
});

test("openMeteoCurrentCondition extracts wind, temp, hi/lo and cardinal direction", () => {
  const payload = sampleOpenMeteoPayload();
  const cond = Model.openMeteoCurrentCondition(payload);
  assert.equal(cond.temp_C, "22");
  assert.equal(cond.temp_F, "72");
  assert.equal(cond.windDirectionCardinal, "NW");
  assert.equal(cond.description, "Clear Sky");
  assert.equal(cond.todayMaxC, "24");
  assert.equal(cond.todayMinC, "14");
});

test("openMeteoForecastDays parses 10 daily forecasts", () => {
  const payload = sampleOpenMeteoPayload();
  const days = Model.openMeteoForecastDays(payload, "2030-01-10", 10);
  assert.equal(days.length, 10);
  assert.equal(days[0].date, "2030-01-10");
  assert.equal(days[0].dayLabel, "Today");
  assert.equal(days[0].description, "Clear Sky");
  assert.equal(days[0].precipitationProbability, 10);
  assert.equal(days[9].date, "2030-01-19");
  assert.equal(days[9].description, "Thunderstorm");
});

test("hourlyForecast includes 48 entries and chronological sunrise/sunset", () => {
  const payload = sampleOpenMeteoPayload();
  const nowMs = Date.parse("2030-01-10T12:00:00Z");
  const entries = Model.hourlyForecast(payload, nowMs, 48);
  const hours = entries.filter(e => e.kind === "hour");
  assert.equal(hours.length, 48);
  const solar = entries.filter(e => e.kind === "sunrise" || e.kind === "sunset");
  assert.ok(solar.length >= 2);
  assert.ok(entries.every((e, idx) => idx === 0 || entries[idx - 1].time <= e.time));
});

test("formatLocationDisplay resolves city and state/province accurately", () => {
  // Configured city without region gets region from areaInfo
  assert.equal(
    Model.formatLocationDisplay("Brunswick", { areaName: [{ value: "Brunswick" }], region: [{ value: "Maine" }] }, "Brunswick"),
    "Brunswick, Maine"
  );

  // Configured city already containing state/province keeps exact specification
  assert.equal(
    Model.formatLocationDisplay("Brunswick, Maine", { areaName: [{ value: "Brunswick" }], region: [{ value: "Maine" }] }, "Brunswick"),
    "Brunswick, Maine"
  );

  // ZIP code search format with state abbreviation gets stripped zip
  assert.equal(
    Model.formatLocationDisplay("Brunswick, ME 04011", null, "Brunswick"),
    "Brunswick, ME"
  );

  // Empty configured location falls back to areaInfo city + region
  assert.equal(
    Model.formatLocationDisplay("", { areaName: [{ value: "Toronto" }], region: [{ value: "Ontario" }] }, "Toronto"),
    "Toronto, Ontario"
  );

  // City-state where region equals city name does not repeat
  assert.equal(
    Model.formatLocationDisplay("Singapore", { areaName: [{ value: "Singapore" }], region: [{ value: "Singapore" }] }, "Singapore"),
    "Singapore"
  );
});

test("buildBarHoverLines generates array of summary lines without version line", () => {
  const payload = sampleOpenMeteoPayload();
  const cond = Model.openMeteoCurrentCondition(payload);
  const days = Model.openMeteoForecastDays(payload, "2030-01-10", 10);
  const lines = Model.buildBarHoverLines(cond, days, true, "Brunswick, Maine");
  assert.equal(lines[0], "Weather report for Brunswick, Maine");
  assert.equal(lines[1], "Clear Sky · 72°F (H: 75° / L: 57°)");
  assert.equal(lines[2], "Feels like: 71°F · Humidity: 55% · Wind: 7 mph NW");
  assert.equal(lines[3], "Precipitation chance today: 10%");
  assert.ok(lines[4].startsWith("Tomorrow:"));
  assert.equal(lines.length, 5);
});

test("buildBarHoverTooltip generates multi-line summary with location header and version at bottom", () => {
  const payload = sampleOpenMeteoPayload();
  const cond = Model.openMeteoCurrentCondition(payload);
  const days = Model.openMeteoForecastDays(payload, "2030-01-10", 10);
  const tooltip = Model.buildBarHoverTooltip("1.0.2", cond, days, true, "Brunswick, Maine");
  assert.ok(tooltip.startsWith("Weather report for Brunswick, Maine\n"));
  assert.ok(tooltip.endsWith("\n\nfred.weather v1.0.2"));
  assert.ok(tooltip.includes("Clear Sky · 72°F"));
  assert.ok(tooltip.includes("Wind: 7 mph NW"));
  assert.ok(tooltip.includes("Tomorrow:"));

  // Verify empty condition fallback still produces header and version separated by blank line
  const emptyTooltip = Model.buildBarHoverTooltip("1.0.2", null, [], true, "Brunswick, Maine");
  assert.equal(emptyTooltip, "Weather report for Brunswick, Maine\n\nfred.weather v1.0.2");
});

test("Network curlCommand enforces deadlines, security flags and max bytes", () => {
  const cmd = Network.curlCommand("https://api.open-meteo.com/test", 5, 128 * 1024);
  assert.deepEqual(cmd, [
    "curl", "-q", "-fsS", "--max-time", "5", "--connect-timeout", "5",
    "--max-filesize", String(128 * 1024), "https://api.open-meteo.com/test"
  ]);
});

test("Network responseText validates byte bounds, exit codes, and utf-8 counting", () => {
  assert.equal(Network.responseText("  hello world  ", 100), "hello world");
  assert.equal(Network.responseText("{\"temp\":20}", 0, 0, 1024), "{\"temp\":20}");

  assert.throws(() => Network.responseText("", 100), /Empty response/);
  assert.throws(() => Network.responseText("  \n\t  ", 100), /Empty response/);
  assert.throws(() => Network.responseText("abcde", 3), /Response exceeds 3 bytes/);
  assert.throws(() => Network.responseText("hello", 1, 0, 100), /Request failed with exit code 1/);

  // Multibyte UTF-8: '€' is 3 bytes, '😀' is 4 bytes
  assert.equal(Network.responseText("€", 3), "€");
  assert.throws(() => Network.responseText("€", 2), /Response exceeds 2 bytes/);
  assert.equal(Network.responseText("😀", 4), "😀");
  assert.throws(() => Network.responseText("😀", 3), /Response exceeds 3 bytes/);
});

test("WeatherStore registers panels and resolves monitors by name and make/model", () => {
  const fs = require("node:fs");
  const path = require("node:path");
  const vm = require("node:vm");

  const code = fs.readFileSync(path.join(__dirname, "../WeatherStore.js"), "utf8")
    .replace(/^\.pragma library\s*/m, "");
  const mod = { exports: {} };
  vm.runInNewContext(code, { module: mod, exports: mod.exports, console });
  const WeatherStore = mod.exports;

  const panelHP = { id: "hp-panel", opened: false, open: () => { panelHP.opened = true; } };
  const panelDell = { id: "dell-panel", opened: false, open: () => { panelDell.opened = true; } };
  const panelMSI = { id: "msi-panel", opened: false, open: () => { panelMSI.opened = true; } };

  WeatherStore.register("HDMI-A-1", panelHP);
  assert.equal(WeatherStore.getPanel("HDMI-A-1"), panelHP);
  WeatherStore.register("DP-1", panelDell);
  WeatherStore.register("DP-2", panelMSI);

  const hyprlandMonitors = [
    { name: "HDMI-A-1", description: "Hewlett Packard HP 22cwa", model: "HP 22cwa" },
    { name: "DP-1", description: "Dell Inc. DELL S2725DSM", model: "DELL S2725DSM" },
    { name: "DP-2", description: "Microstep MSI MP161", model: "MSI MP161" }
  ];

  // Direct monitor name match
  assert.equal(WeatherStore.resolveTargetPanel("HDMI-A-1", "DP-1", hyprlandMonitors), panelHP);
  assert.equal(WeatherStore.resolveTargetPanel("dp-2", "DP-1", hyprlandMonitors), panelMSI);

  // Hyprland description / model match (e.g. "hp", "dell", "msi")
  assert.equal(WeatherStore.resolveTargetPanel("hp", "DP-1", hyprlandMonitors), panelHP);
  assert.equal(WeatherStore.resolveTargetPanel("dell", "HDMI-A-1", hyprlandMonitors), panelDell);
  assert.equal(WeatherStore.resolveTargetPanel("msi", "DP-1", hyprlandMonitors), panelMSI);

  // Fallback to focused monitor
  assert.equal(WeatherStore.resolveTargetPanel("", "DP-1", hyprlandMonitors), panelDell);

  // Clean unregister
  WeatherStore.unregister("HDMI-A-1", panelHP);
  assert.equal(WeatherStore.getPanel("HDMI-A-1"), null);
  WeatherStore.unregister("DP-1", panelDell);
  WeatherStore.unregister("DP-2", panelMSI);
});

test("WeatherStore multi-monitor refreshAll and payload broadcast", () => {
  const fs = require("node:fs");
  const path = require("node:path");
  const vm = require("node:vm");

  const code = fs.readFileSync(path.join(__dirname, "../WeatherStore.js"), "utf8")
    .replace(/^\.pragma library\s*/m, "");
  const mod = { exports: {} };
  vm.runInNewContext(code, { module: mod, exports: mod.exports, console });
  const WeatherStore = mod.exports;

  let refreshedDell = 0;
  let refreshedMSI = 0;
  let receivedForecast = null;
  let receivedReport = null;

  const pDell = {
    refresh: () => { refreshedDell++; },
    applyDailyForecast: (payload) => { receivedForecast = payload; },
    applyReport: (payload) => { receivedReport = payload; }
  };
  const pMSI = {
    refresh: () => { refreshedMSI++; }
  };

  WeatherStore.register("DP-1", pDell);
  WeatherStore.register("DP-2", pMSI);

  // Test refreshAll
  const count = WeatherStore.refreshAll();
  assert.equal(count, 2);
  assert.equal(refreshedDell, 1);
  assert.equal(refreshedMSI, 1);

  // Test broadcastDailyForecast
  const forecastCount = WeatherStore.broadcastDailyForecast("DP-2", { test: 123 }, Date.now(), "Brunswick");
  assert.equal(forecastCount, 1);
  assert.deepEqual(receivedForecast, { test: 123 });

  // Test broadcastReport
  const reportCount = WeatherStore.broadcastReport("DP-2", { report: 456 }, Date.now(), "Brunswick");
  assert.equal(reportCount, 1);
  assert.deepEqual(receivedReport, { report: 456 });

  WeatherStore.unregister("DP-1", pDell);
  WeatherStore.unregister("DP-2", pMSI);
});

test("forecastTodayString handles negative and positive timezone offsets accurately", () => {
  // 2026-09-18 at 22:40 EDT is 2026-09-19 at 02:40 UTC
  const lateEveningUtcMs = Date.parse("2026-09-19T02:40:00Z");

  // In America/New_York (EDT, UTC-4 = -14400s), local date is still 2026-09-18
  const reportEdt = { utc_offset_seconds: -14400 };
  assert.equal(Model.forecastTodayString(reportEdt, lateEveningUtcMs), "2026-09-18");

  // In Asia/Tokyo (JST, UTC+9 = +32400s), local date is 2026-09-19 (11:40 AM)
  const reportJst = { utc_offset_seconds: 32400 };
  assert.equal(Model.forecastTodayString(reportJst, lateEveningUtcMs), "2026-09-19");

  // Fallback to local machine date when report is null or lacks offset
  const localDate = Model.forecastTodayString(null, lateEveningUtcMs);
  assert.match(localDate, /^\d{4}-\d{2}-\d{2}$/);
});

test("openMeteoForecastDays aligns Today label with local timezone date rather than UTC", () => {
  const payload = sampleOpenMeteoPayload();
  // Payload has utc_offset_seconds: -18000 (-5h EST)
  // At 2030-01-11 02:30:00Z (UTC is Jan 11), in EST (-5h) it is 2030-01-10 21:30:00 (Jan 10)
  const eveningUtcMs = Date.parse("2030-01-11T02:30:00Z");
  const localToday = Model.forecastTodayString(payload, eveningUtcMs);
  assert.equal(localToday, "2030-01-10");

  const days = Model.openMeteoForecastDays(payload, localToday, 10);
  assert.equal(days[0].date, "2030-01-10");
  assert.equal(days[0].isToday, true);
  assert.equal(days[0].dayLabel, "Today");
  assert.equal(days[1].date, "2030-01-11");
  assert.equal(days[1].isToday, false);
  assert.equal(days[1].dayLabel, "Fri Jan 11");
});

test("openMeteoForecastDays skips past days when reading cached data across midnight", () => {
  const payload = sampleOpenMeteoPayload();
  // If cache starts at 2030-01-10, but current local date has rolled over to 2030-01-11
  const days = Model.openMeteoForecastDays(payload, "2030-01-11", 10);
  assert.equal(days[0].date, "2030-01-11");
  assert.equal(days[0].isToday, true);
  assert.equal(days[0].dayLabel, "Today");
  assert.equal(days[1].date, "2030-01-12");
  assert.equal(days[1].isToday, false);
  assert.equal(days[1].dayLabel, "Sat Jan 12");
});

test("openMeteoCurrentCondition indexes into daily arrays matching todayString", () => {
  const payload = sampleOpenMeteoPayload();
  // Index 0 (Jan 10) has max 24, min 14, precip 10
  const cond0 = Model.openMeteoCurrentCondition(payload, "2030-01-10");
  assert.equal(cond0.todayMaxC, "24");
  assert.equal(cond0.todayMinC, "14");
  assert.equal(cond0.todayPrecipProbability, 10);

  // Index 1 (Jan 11) has max 25, min 15, precip 20
  const cond1 = Model.openMeteoCurrentCondition(payload, "2030-01-11");
  assert.equal(cond1.todayMaxC, "25");
  assert.equal(cond1.todayMinC, "15");
  assert.equal(cond1.todayPrecipProbability, 20);
});




