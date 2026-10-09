// Device detection parsing, against this machine's real /proc data shape.
//   node tests/device.test.js

var D = require("./load.js").loadQmlJs("Device.js")
var fs = require("fs")

var failures = []
function check(n, c, d) { if (!c) failures.push(n + (d ? ": " + d : "")) }

var SAMPLE = [
  'I: Bus=0019 Vendor=0000 Product=0001 Version=0000',
  'N: Name="Power Button"',
  'H: Handlers=kbd event0 ',
  'B: KEY=10000000000000 0',
  '',
  'I: Bus=0011 Vendor=0001 Product=0002 Version=ab41',
  'N: Name="AT Raw Set 2 keyboard"',
  'H: Handlers=sysrq kbd leds event2 ',
  'B: KEY=402000000 3803078f800d001 feffffdfffefffff fffffffffffffffe',
  '',
  'I: Bus=0003 Vendor=17ef Product=608c Version=0111',
  'N: Name="LiteOn Lenovo Calliope USB Keyboard"',
  'H: Handlers=sysrq kbd leds event5 ',
  'B: KEY=1000000000007 ff9f207ac14057ff febeffdfffefffff fffffffffffffffe',
  '',
  'I: Bus=0003 Vendor=17ef Product=608c Version=0111',
  'N: Name="LiteOn Lenovo Calliope USB Keyboard Consumer Control"',
  'H: Handlers=kbd event7 js0 ',
  'B: KEY=3f000305af80000 0 0 0',
  ''
].join('\n')

var devs = D.parseProcDevices(SAMPLE)
check("parsed some devices", devs.length >= 3, String(devs.length))

var names = devs.map(function (d) { return d.name })
check("found the Calliope", names.indexOf("LiteOn Lenovo Calliope USB Keyboard") >= 0, names.join("|"))

var cal = devs.filter(function (d) { return d.name.indexOf("Calliope USB Keyboard") >= 0 && d.name.indexOf("Consumer") < 0 })[0]
check("Calliope vendor", cal && cal.vendor === "17ef", cal && cal.vendor)
check("Calliope product", cal && cal.product === "608c", cal && cal.product)
check("Calliope bus is USB", cal && cal.busLabel === "USB", cal && cal.busLabel)


// Regression: 64-bit KEY= words must not lose bits to float imprecision.
check("counts a full 64-bit word", D.countKeyBits("ffffffffffffffff") === 64,
      String(D.countKeyBits("ffffffffffffffff")))
check("counts across words", D.countKeyBits("ffffffffffffffff ffffffffffffffff") === 128,
      String(D.countKeyBits("ffffffffffffffff ffffffffffffffff")))
check("Calliope count matches the kernel header decode", cal && cal.keyCount === 163,
      cal && String(cal.keyCount))

// Noise filtering
check("virtual keyboard is noise", D.isNoiseName("hl-virtual-keyboard-fcitx5"))
check("AT stub is noise", D.isNoiseName("AT Raw Set 2 keyboard"))
check("power button is noise", D.isNoiseName("Power Button"))
check("Consumer Control is noise", D.isNoiseName("LiteOn Lenovo Calliope USB Keyboard Consumer Control"))
check("real keyboard is not noise", !D.isNoiseName("LiteOn Lenovo Calliope USB Keyboard"))

// Primary selection must land on the main board, not its sibling nodes.
var primary = D.primaryKeyboard(devs)
check("primary is the Calliope main node",
      primary && primary.name === "LiteOn Lenovo Calliope USB Keyboard",
      primary && primary.name)

check("no devices -> null", D.primaryKeyboard([]) === null)
check("garbage does not throw", D.parseProcDevices(null).length === 0)

// Keymap extraction prefers the main keyboard.
var HY = JSON.stringify({ keyboards: [
  { name: "at-raw-set-2-keyboard", main: false, active_keymap: "English (US)" },
  { name: "hl-virtual-keyboard-fcitx5", main: true, active_keymap: "English (US)" }
]})
check("keymap read", D.activeKeymap(HY) === "English (US)", D.activeKeymap(HY))
check("bad json -> empty", D.activeKeymap("{{{") === "")

// Summary line
var s = D.summary(primary, "English (US)")
check("summary names the board", s.indexOf("Lenovo Calliope") >= 0, s)
check("summary has keymap", s.indexOf("English (US)") >= 0, s)
check("summary has bus", s.indexOf("USB") >= 0, s)
check("no keyboard -> honest message", D.summary(null, "x").indexOf("No keyboard") >= 0)

// Against the live machine, if present.
if (fs.existsSync("/proc/bus/input/devices")) {
  var live = D.parseProcDevices(fs.readFileSync("/proc/bus/input/devices", "utf8"))
  var lp = D.primaryKeyboard(live)
  check("live: found a keyboard", !!lp, "none")
  if (lp) console.log("   live primary: " + D.summary(lp, "") + "  (" + lp.keyCount + " keys declared)")
}

// LED paths are derived from the device's own handlers, not guessed.
var calDev = { name: "x", handlers: "sysrq kbd leds event5" }
var lp = D.ledPaths(calDev)
check("led path derived from event index",
      lp && lp.caps === "/sys/class/leds/input5::capslock/brightness", lp && lp.caps)
check("num led path", lp && lp.num === "/sys/class/leds/input5::numlock/brightness", lp && lp.num)
check("index parsed", D.inputIndexFor(calDev) === 5, String(D.inputIndexFor(calDev)))
check("no leds handler -> null", D.ledPaths({ handlers: "kbd event7" }) === null)
check("no device -> null", D.ledPaths(null) === null)
check("led on parsing", D.ledOn("1") === true && D.ledOn("0") === false && D.ledOn("") === false)
check("led brightness >1 counts as on", D.ledOn("255") === true)

// Against the live machine: the derived path must actually exist.
if (fs.existsSync("/proc/bus/input/devices")) {
  var lp2 = D.ledPaths(D.primaryKeyboard(D.parseProcDevices(
    fs.readFileSync("/proc/bus/input/devices", "utf8"))))
  if (lp2) {
    check("live: caps led path exists", fs.existsSync(lp2.caps), lp2.caps)
    check("live: num led path exists", fs.existsSync(lp2.num), lp2.num)
    if (fs.existsSync(lp2.caps))
      console.log("   live LEDs: caps=" + (D.ledOn(fs.readFileSync(lp2.caps,"utf8")) ? "on" : "off") +
                  " num=" + (D.ledOn(fs.readFileSync(lp2.num,"utf8")) ? "on" : "off"))
  }
}

if (failures.length) {
  console.error("FAIL (" + failures.length + ")")
  failures.forEach(function (f) { console.error("  - " + f) })
  process.exit(1)
}
console.log("ok - device detection")
