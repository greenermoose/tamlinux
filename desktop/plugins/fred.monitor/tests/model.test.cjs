const assert = require("node:assert/strict");
const test = require("node:test");
const Model = require("../Model.js");

const sampleStateJson = JSON.stringify({
  focusedMonitor: "DP-1",
  displays: [
    {
      id: 2,
      name: "DP-2",
      description: "Microstep MSI MP161 PB7H033700102",
      make: "Microstep",
      model: "MSI MP161",
      serial: "PB7H033700102",
      enabled: true,
      focused: false,
      width: 1920,
      height: 1080,
      physicalWidth: 340,
      physicalHeight: 190,
      sizeInches: '13.4"×7.5" (15.3" diag)',
      refreshRate: 60.0,
      availableRates: [60.0, 59.94, 50.0],
      x: 0,
      y: 720,
      scale: 1.5,
      logicalWidth: 1280,
      logicalHeight: 720,
      transform: 0,
      dpmsStatus: true,
      vrr: false,
      workspace: "1",
      brightness: 95,
      brightnessAvailable: true
    },
    {
      id: 1,
      name: "DP-1",
      description: "Dell Inc. DELL S2725DSM 4VLM1D4",
      make: "Dell Inc.",
      model: "DELL S2725DSM",
      serial: "4VLM1D4",
      enabled: true,
      focused: true,
      width: 2560,
      height: 1440,
      physicalWidth: 600,
      physicalHeight: 340,
      sizeInches: '23.6"×13.4" (27.2" diag)',
      refreshRate: 59.951,
      availableRates: [143.97, 120.0, 59.95],
      x: 1280,
      y: 0,
      scale: 1.0,
      logicalWidth: 2560,
      logicalHeight: 1440,
      transform: 0,
      dpmsStatus: true,
      vrr: false,
      workspace: "2",
      brightness: 75,
      brightnessAvailable: true
    },
    {
      id: 0,
      name: "HDMI-A-1",
      description: "Hewlett Packard HP 22cwa 6CM7480T0C",
      make: "Hewlett Packard",
      model: "HP 22cwa",
      serial: "6CM7480T0C",
      enabled: true,
      focused: false,
      width: 1920,
      height: 1080,
      physicalWidth: 480,
      physicalHeight: 270,
      sizeInches: '18.9"×10.6" (21.7" diag)',
      refreshRate: 60.0,
      availableRates: [60.0, 59.94, 50.0],
      x: 3840,
      y: 360,
      scale: 1.0,
      logicalWidth: 1920,
      logicalHeight: 1080,
      transform: 0,
      dpmsStatus: true,
      vrr: false,
      workspace: "3",
      brightness: 0,
      brightnessAvailable: false
    }
  ]
});

test("parseState parses new JSON document correctly", () => {
  const parsed = Model.parseState(sampleStateJson);
  assert.equal(parsed.focusedMonitor, "DP-1");
  assert.equal(parsed.displays.length, 3);
  assert.equal(parsed.enabledDisplayCount, 3);
  assert.equal(parsed.displays[0].name, "DP-2");
  assert.equal(parsed.displays[0].brightness, 95);
  assert.equal(parsed.displays[0].brightnessAvailable, true);
  assert.equal(parsed.displays[2].brightnessAvailable, false);
});

test("formatFacts omits settings repeated by card controls", () => {
  const parsed = Model.parseState(sampleStateJson);
  const factsDP2 = Model.formatFacts(parsed.displays[0]);
  assert.ok(!factsDP2.includes("1920×1080"));
  assert.ok(!factsDP2.includes("60.00 Hz"));
  assert.ok(!factsDP2.includes("scale"));
  assert.ok(!factsDP2.includes("15.3″"));
  assert.ok(!factsDP2.includes("DPMS"));
  assert.ok(factsDP2.includes("VRR off"));
  assert.ok(factsDP2.includes("workspace 1"));
});

test("cardIdentity puts physical inches before the monitor model", () => {
  const parsed = Model.parseState(sampleStateJson);
  assert.equal(Model.cardIdentity(parsed.displays[0]), "15.3″ MSI MP161");
  assert.equal(Model.cardIdentity(parsed.displays[1]), "27.2″ DELL S2725DSM");
});

test("positionLabel assigns Left, Center, Right accurately based on x coordinates", () => {
  const parsed = Model.parseState(sampleStateJson);
  assert.equal(Model.positionLabel("DP-2", parsed.displays), "Left");
  assert.equal(Model.positionLabel("DP-1", parsed.displays), "Center");
  assert.equal(Model.positionLabel("HDMI-A-1", parsed.displays), "Right");
});

test("availableScales and matchingScaleIndex work for various resolutions", () => {
  const presets = ["1", "1.25", "1.5", "1.6", "2", "3", "4"];
  const scales1080 = Model.availableScales(presets, 1920, 1080);
  assert.ok(scales1080.length > 0);
  const match1 = Model.matchingScaleIndex(scales1080, 1.5, 1920, 1080);
  assert.ok(match1 >= 0);
  const match2 = Model.matchingScaleIndex(scales1080, 1.0, 1920, 1080);
  assert.ok(match2 >= 0);
});

test("brightness clamping and names", () => {
  assert.equal(Model.clampBrightness(-10), 1);
  assert.equal(Model.clampBrightness(110), 100);
  assert.equal(Model.clampBrightness(75), 75);
  assert.equal(Model.brightnessName(100), "Sun blast");
  assert.equal(Model.brightnessName(80), "Solar flare");
  assert.equal(Model.brightnessName(70), "Golden hour");
  assert.equal(Model.brightnessName(50), "Even day");
  assert.equal(Model.brightnessName(35), "Soft glow");
  assert.equal(Model.brightnessName(25), "Lamp light");
  assert.equal(Model.brightnessName(15), "Candlelit");
  assert.equal(Model.brightnessName(5), "Night owl");
});

test("monitorCountLabel uses readable singular and plural headings", () => {
  assert.equal(Model.monitorCountLabel(0), "No Monitors");
  assert.equal(Model.monitorCountLabel(1), "One Monitor");
  assert.equal(Model.monitorCountLabel(2), "Two Monitors");
  assert.equal(Model.monitorCountLabel(3), "Three Monitors");
  assert.equal(Model.monitorCountLabel(4), "4 Monitors");
});

test("formatHover describes the bar instance monitor", () => {
  const parsed = Model.parseState(sampleStateJson);
  const text = Model.formatHover(parsed.displays[1], parsed.displays, "1.2.0");
  assert.equal(text.split("\n")[0], "Center Monitor");
  assert.ok(text.includes("DP-1 · Dell Inc. DELL S2725DSM · 27.2″"));
  assert.ok(text.includes("2560 × 1440 · 59.95 Hz · 1×"));
  assert.ok(text.endsWith("\n\nfred.monitor v1.2.0"));
});

test("sortDisplays and alignDisplays use physical order and logical geometry", () => {
  const parsed = Model.parseState(sampleStateJson);
  const sorted = Model.sortDisplays([parsed.displays[2], parsed.displays[0], parsed.displays[1]]);
  assert.deepEqual(sorted.map(d => d.name), ["DP-2", "DP-1", "HDMI-A-1"]);

  const bottom = Model.alignDisplays(sorted, "bottom");
  assert.deepEqual(bottom.map(d => [d.name, d.x, d.y]), [
    ["DP-2", 0, 720],
    ["DP-1", 1280, 0],
    ["HDMI-A-1", 3840, 360]
  ]);
});

test("moveDisplay swaps columns before recalculating geometry", () => {
  const parsed = Model.parseState(sampleStateJson);
  const moved = Model.moveDisplay(parsed.displays, "DP-1", -1, "bottom");
  assert.deepEqual(Model.sortDisplays(moved).map(d => d.name), ["DP-1", "DP-2", "HDMI-A-1"]);
  assert.equal(moved.find(d => d.name === "DP-1").x, 0);
  assert.equal(moved.find(d => d.name === "DP-2").x, 2560);
});
