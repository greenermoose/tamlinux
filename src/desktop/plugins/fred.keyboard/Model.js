.pragma library

// Shared helpers. Kept separate from the layout data (layouts/*.json) and the
// layout logic (KeyboardModel.js, LayoutResolver.js).

// Build a closed environment: only the named keys are copied from the shell's
// environment, plus any explicit extras. Nothing else is inherited.
function pickEnv(keys, extra, lookup) {
  var env = {}
  if (extra) {
    for (var k in extra) {
      if (Object.prototype.hasOwnProperty.call(extra, k) &&
          extra[k] !== undefined && extra[k] !== null && extra[k] !== "") {
        env[k] = String(extra[k])
      }
    }
  }
  if (keys && typeof lookup === "function") {
    for (var i = 0; i < keys.length; i++) {
      var val = lookup(keys[i])
      if (val !== undefined && val !== null && val !== "") env[keys[i]] = String(val)
    }
  }
  return env
}

// Absolute path to a file shipped beside this plugin.
function helperPath(name) {
  if (typeof Qt === "undefined" || !Qt.resolvedUrl) return name
  var url = String(Qt.resolvedUrl(name))
  if (url.indexOf("file://") === 0) url = url.substring(7)
  return decodeURIComponent(url)
}
