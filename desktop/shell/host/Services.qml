import QtQuick
import Quickshell
import "../services/notifications" as Notifications

// Session services the host owns. TAMLINUX_SERVICES names them,
// comma-separated; unknown names are ignored. Each one is vendored under
// ../services/ and gets the shell injected for the compositor facade and the
// bar position.
Item {
  id: services

  property var shell: null
  readonly property var known: ["notifications"]
  readonly property var enabled: {
    var wanted = String(Quickshell.env("TAMLINUX_SERVICES") || "").split(",")
    var picked = []
    for (var i = 0; i < wanted.length; i++) {
      var name = wanted[i].trim()
      if (known.indexOf(name) !== -1 && picked.indexOf(name) === -1) picked.push(name)
    }
    return picked
  }

  function note(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  // Static imports, not URLs: Quickshell only scans files it reaches by import.
  Loader {
    active: services.enabled.indexOf("notifications") !== -1
    sourceComponent: Component {
      Notifications.Service { shell: services.shell }
    }
    onLoaded: services.note("service-loaded notifications")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed notifications")
  }

  Component.onCompleted: note("services " + (enabled.length > 0 ? enabled.join(",") : "none"))
}
