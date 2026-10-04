import QtQuick
import Quickshell
import "../services/clipboard" as Clipboard
import "../services/emojis" as Emojis
import "../services/imagepicker" as ImagePicker
import "../services/menu" as Menu
import "../services/notifications" as Notifications
import "../services/osd" as Osd
import "../services/reminders" as Reminders

// Session services the host owns. TAMLINUX_SERVICES names them,
// comma-separated; unknown names are ignored. Each one is vendored under
// ../services/. Notifications gets the shell injected for the compositor
// facade and the bar position; the menu gets the OSD for launch feedback.
Item {
  id: services

  property var shell: null
  readonly property var known: ["notifications", "osd", "clipboard", "emojis", "imagepicker", "reminders", "menu"]
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
    id: osdLoader
    active: services.enabled.indexOf("osd") !== -1
    sourceComponent: Component {
      Osd.Service {}
    }
    onLoaded: services.note("service-loaded osd")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed osd")
  }

  Loader {
    active: services.enabled.indexOf("clipboard") !== -1
    sourceComponent: Component {
      Clipboard.Service {}
    }
    onLoaded: services.note("service-loaded clipboard")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed clipboard")
  }

  Loader {
    active: services.enabled.indexOf("emojis") !== -1
    sourceComponent: Component {
      Emojis.Service {}
    }
    onLoaded: services.note("service-loaded emojis")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed emojis")
  }

  Loader {
    active: services.enabled.indexOf("imagepicker") !== -1
    sourceComponent: Component {
      ImagePicker.Service {}
    }
    onLoaded: services.note("service-loaded imagepicker")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed imagepicker")
  }

  Loader {
    active: services.enabled.indexOf("reminders") !== -1
    sourceComponent: Component {
      Reminders.Service {}
    }
    onLoaded: services.note("service-loaded reminders")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed reminders")
  }

  Loader {
    active: services.enabled.indexOf("menu") !== -1
    sourceComponent: Component {
      Menu.Service { osd: osdLoader.item }
    }
    onLoaded: services.note("service-loaded menu")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed menu")
  }

  Component.onCompleted: note("services " + (enabled.length > 0 ? enabled.join(",") : "none"))
}
