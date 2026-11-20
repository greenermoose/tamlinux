// Split the final plugin version line from plain-text hover content.
// A version can be the entire hover when the widget has no other status.
function parse(raw) {
  var text = String(raw || "")
  if (!text) return { body: "", footer: "" }
  var lines = text.replace(/\s+$/, "").split(/\r?\n/)
  var footer = lines[lines.length - 1].trim()
  if (!/^fred\.[a-z0-9_.-]+\s+v\S+.*$/i.test(footer))
    return { body: text, footer: "" }
  return {
    body: lines.slice(0, -1).join("\n").replace(/\s+$/, ""),
    footer: footer
  }
}

if (typeof module !== "undefined") module.exports = { parse: parse }
