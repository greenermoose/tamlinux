import QtQuick
import Quickshell
import "../services/notifications" as Notifications
import "../services/osd" as Osd

// Session services the host owns. TAMLINUX_SERVICES names them,
// comma-separated; unknown names are ignored. Each one is vendored under
// ../services/. Notifications gets the shell injected for the compositor
// facade and the bar position.
Item {
  id: services

  property var shell: null
  readonly property var known: ["notifications", "osd"]
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

  Loader {
    active: services.enabled.indexOf("osd") !== -1
    sourceComponent: Component {
      Osd.Service {}
    }
    onLoaded: services.note("service-loaded osd")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed osd")
  }

  Component.onCompleted: note("services " + (enabled.length > 0 ? enabled.join(",") : "none"))
}
