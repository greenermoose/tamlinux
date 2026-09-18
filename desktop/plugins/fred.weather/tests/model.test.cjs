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

test("buildBarHoverTooltip generates multi-line summary with name and version", () => {
  const payload = sampleOpenMeteoPayload();
  const cond = Model.openMeteoCurrentCondition(payload);
  const days = Model.openMeteoForecastDays(payload, "2030-01-10", 10);
  const tooltip = Model.buildBarHoverTooltip("1.0.0", cond, days, true, "New York, NY");
  assert.ok(tooltip.includes("fred.weather v1.0.0"));
  assert.ok(tooltip.includes("New York, NY"));
  assert.ok(tooltip.includes("Clear Sky · 72°F"));
  assert.ok(tooltip.includes("Wind: 7 mph NW"));
  assert.ok(tooltip.includes("Tomorrow:"));
});

test("Network curlCommand enforces deadlines, security flags and max bytes", () => {
  const cmd = Network.curlCommand("https://api.open-meteo.com/test", 5, 128 * 1024);
  assert.deepEqual(cmd, [
    "curl", "-q", "-fsS", "--max-time", "5", "--connect-timeout", "5",
    "--max-filesize", String(128 * 1024), "https://api.open-meteo.com/test"
  ]);
});
