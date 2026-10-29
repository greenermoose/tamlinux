// Pure helpers for the polkit service: fingerprint detection and the
// authorization label.
//
// Ported from omarchy 4.0.4 shell/plugins/polkit/PolkitModel.js (MIT,
// Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Adds
// compositor-neutral prompt placement on a visible output.

function promptScreen(screens, outputs, focusedName) {
  screens = screens || []
  outputs = outputs || []
  var focused = null
  var firstLit = null
  for (var i = 0; i < screens.length; i++) {
    var screen = screens[i]
    if (!screen) continue
    var output = null
    for (var j = 0; j < outputs.length; j++) {
      if (outputs[j] && outputs[j].name === screen.name) {
        output = outputs[j]
        break
      }
    }
    var lit = output && output.dpmsOn !== false
    if (screen.name === focusedName) {
      focused = screen
      if (lit) return screen
    }
    if (lit && !firstLit) firstLit = screen
  }
  // If every output is dark, the service wakes the selected output. A shell
  // without a compositor snapshot still has a usable screen fallback.
  return firstLit || focused || screens[0] || null
}

function promptLooksFingerprint(text) {
  var s = String(text || "").toLowerCase()
  return s.indexOf("finger") !== -1 || s.indexOf("fprint") !== -1 || s.indexOf("swipe") !== -1
}

function fingerprintConfiguredFromPamConfig(raw) {
  // Fingerprint is available whenever pam_fprintd appears anywhere in the auth
  // stack — it need not be the first module. A clamshell gate (pam_exec) may
  // legitimately precede it to skip fingerprint while the lid is closed.
  var lines = String(raw || "").split("\n")
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i].replace(/^\s+|\s+$/g, "")
    if (!line || line.charAt(0) === "#") continue
    if (!line.match(/^auth\s+/)) continue
    if (line.indexOf("pam_fprintd.so") !== -1) return true
  }
  return false
}

function authorizationLabel(message) {
  var text = String(message || "")
  var match = text.match(/^Authentication is (?:needed|required) to run [`']([^`']+)[`'] as /i)
  return match ? "Authorize running '" + match[1] + "'" : text
}

if (typeof module !== "undefined") {
  module.exports = {
    promptScreen: promptScreen,
    promptLooksFingerprint: promptLooksFingerprint,
    fingerprintConfiguredFromPamConfig: fingerprintConfiguredFromPamConfig,
    authorizationLabel: authorizationLabel
  }
}
