.pragma library

// One ingress and work queue per shell engine, shared by every bar instance.
// Publication never waits for the compositor worker. There is only one
// publisher, so asynchronous process startup cannot reorder accepted clicks.
var clients = []
var pendingSwitch = null
var publishing = null
var working = null
var pending = []
var serial = 0

function register(client) {
  if (clients.indexOf(client) < 0) clients.push(client)
  pump()
}

function unregister(client) {
  clients = clients.filter(function(c) { return c !== client })
  if (publishing && publishing.client === client) {
    if (!pendingSwitch) pendingSwitch = publishing.request
    publishing = null
  }
  if (working && working.client === client) {
    pending.unshift(working.request)
    working = null
  }
  pump()
}

function submit(client, args, windows) {
  var request = { args: args.slice(), serial: ++serial, tries: 0 }
  if (windows && args[0] === "switch" && args[2] !== "follow-timer") {
    request.origin = client.desktopIngressOrigin()
    pendingSwitch = request // Latest click replaces only unaccepted clicks.
    // A delayed focus observation may not follow an explicit bar request.
    pending = pending.filter(function(r) { return r.args[2] !== "follow-timer" })
  } else {
    // Coalesce repair per output, DPMS per output, and follow observations.
    var key = args[0] === "dpms-on" || args[0] === "dpms-off" ? "dpms" : args[0]
    var target = args[0] === "realign" || key === "dpms" ? args[1] : ""
    request.key = key + ":" + target
    pending = pending.filter(function(r) { return r.key !== request.key })
    if (pending.length >= 64) {
      client.queueRejected(args)
      return false
    }
    pending.push(request)
  }
  pump()
  return true
}

function pump() {
  if (!clients.length) return
  var client = clients[0]
  if (!publishing && pendingSwitch) {
    var request = pendingSwitch
    pendingSwitch = null
    publishing = { client: client, request: request }
    client.startPublication(["accept-switch", request.args[1], request.origin])
  }
  // Drain ingress first. Older workers already running are generation gated.
  if (!working && !publishing && !pendingSwitch && pending.length) {
    var next = pending.shift()
    working = { client: client, request: next }
    client.startQueuedAction(next.args)
  }
}

function published(client, ok) {
  if (!publishing || publishing.client !== client) return
  var request = publishing.request
  publishing = null
  if (ok) {
    pending = pending.filter(function(r) { return r.args[0] !== "apply-intent" })
    pending.unshift({ args: ["apply-intent"], serial: request.serial, tries: 0 })
  } else if (++request.tries < 3 && !pendingSwitch) {
    pendingSwitch = request
  } else {
    client.queueRejected(request.args)
  }
  pump()
}

function finished(client, busy, incomplete) {
  if (!working || working.client !== client) return
  var request = working.request
  working = null
  // Retry only the retained latest intent, never republish an older click.
  if ((busy || (incomplete && request.args[0] === "apply-intent")) && ++request.tries < 3) pending.push(request)
  else if (busy || incomplete) client.queueRejected(request.args)
  pump()
}
