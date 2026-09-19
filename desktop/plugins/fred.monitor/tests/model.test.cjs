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

test("formatFacts produces formatted facts row", () => {
  const parsed = Model.parseState(sampleStateJson);
  const factsDP2 = Model.formatFacts(parsed.displays[0]);
  assert.ok(factsDP2.includes("1920×1080 @ 60.00 Hz"));
  assert.ok(factsDP2.includes("scale 1.5 → 1280×720 logical"));
  assert.ok(factsDP2.includes("transform 0"));
  assert.ok(factsDP2.includes("DPMS on"));
  assert.ok(factsDP2.includes("VRR off"));
  assert.ok(factsDP2.includes("workspace 1"));
  assert.ok(factsDP2.includes('13.4"×7.5" (15.3" diag)'));
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
