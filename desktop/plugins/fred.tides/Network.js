var responseLimits = {
  tides: 256 * 1024,
  geocode: 64 * 1024,
  location: 2048
}

var closedEnv = ["LANG=C", "LC_ALL=C", "PATH=/usr/bin:/bin"]

function curlCommand(url, timeoutSeconds, maxBytes) {
  // -q: ignore curlrc to prevent config file injections or overrides
  // -f: fail silently on server errors (HTTP 4xx/5xx)
  // -sS: silent mode but show error message if it fails
  // --max-time: enforce hard process deadline
  // --max-filesize: hard network transfer limit
  return ["curl", "-q", "-fsS", "--max-time", String(timeoutSeconds),
    "--connect-timeout", "5", "--max-filesize", String(maxBytes), url]
}

function responseText(text, arg2, arg3, arg4) {
  var maxBytes = typeof arg4 === "number" ? arg4 : (typeof arg2 === "number" ? arg2 : 1024 * 1024)
  var hasExitInfo = typeof arg2 === "number" && typeof arg3 === "number" && typeof arg4 === "number"
  if (hasExitInfo && (arg2 !== 0 || arg3 !== 0))
    throw new Error("Request failed with exit code " + arg2)

  var raw = String(text || "").trim()
  if (!raw) throw new Error("Empty response")
  if (raw.length > maxBytes) throw new Error("Response exceeds " + maxBytes + " bytes")

  var bytes = 0
  for (var i = 0; i < raw.length; i++) {
    var code = raw.charCodeAt(i)
    if (code < 0x80) bytes++
    else if (code < 0x800) bytes += 2
    else if (code >= 0xd800 && code <= 0xdbff
        && i + 1 < raw.length && raw.charCodeAt(i + 1) >= 0xdc00
        && raw.charCodeAt(i + 1) <= 0xdfff) {
      bytes += 4
      i++
    } else bytes += 3
    if (bytes > maxBytes) throw new Error("Response exceeds " + maxBytes + " bytes")
  }

  return raw
}

if (typeof module !== "undefined") {
  module.exports = {
    responseLimits: responseLimits,
    closedEnv: closedEnv,
    curlCommand: curlCommand,
    responseText: responseText
  }
}
