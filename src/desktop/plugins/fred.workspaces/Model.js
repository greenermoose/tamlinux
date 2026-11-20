// Pure decisions for the workspaces widget, Qt-free so they can be unit tested
// under node (tests/test_model.py).

// Every bar runs this widget, and each one sees an output-set change. Only one
// of them may run `tam-desktop-mode reconcile`: concurrent runs interleaved
// their batches and moved the wrong workspace (2026-10-19 VT-switch
// incident). The owner is the first, by name, of the outputs present both
// before and after the change: its bar was already running and saw the
// change, so every established bar agrees. A bar built for a returning output
// never qualifies through that output. If no output survived the change, the
// first current output owns it.
function reconcileOwner(previousNames, currentNames, barName) {
  var name = String(barName || "")
  if (name === "" || !Array.isArray(currentNames)) return false
  var previous = Array.isArray(previousNames) ? previousNames : []
  var current = currentNames.filter(function(n) { return typeof n === "string" && n !== "" })
  var stable = current.filter(function(n) { return previous.indexOf(n) !== -1 })
  var pool = (stable.length > 0 ? stable : current).slice().sort()
  return pool.length > 0 && pool[0] === name
}

if (typeof module !== "undefined") {
  module.exports = {
    reconcileOwner: reconcileOwner
  }
}
