import QtQuick
import Quickshell
import "../services/background" as Background
import "../services/battery" as Battery
import "../services/clipboard" as Clipboard
import "../services/emojis" as Emojis
import "../services/idle" as Idle
import "../services/imagepicker" as ImagePicker
import "../services/keybindings" as Keybindings
import "../services/media" as Media
import "../services/menu" as Menu
import "../services/nightlight" as Nightlight
import "../services/notifications" as Notifications
import "../services/osd" as Osd
import "../services/polkit" as Polkit
import "../services/reminders" as Reminders
import "../services/theme" as Theme

// Session services the host owns. TAMLINUX_SERVICES names them,
// comma-separated; unknown names are ignored. Implementations live in
// ../services/. Notifications gets the shell injected for the compositor
// facade and the bar position, and the keybinding viewer gets it for the
// facade's bindings; the panel host (PanelHost.qml, the ported panels)
// gets the shell, the OSD, and the media service; the menu gets the OSD for launch feedback,
// the media service gets it for each media-key action, and the background
// gets the menu for its desktop double-clicks. Polkit, idle, and battery
// need nothing. Only one polkit agent per session registers, so polkit stays
// out of TAMLINUX_SERVICES while another agent holds the session.
// The bar's indicators reach notifications, night light, and idle through
// firstPartyServiceFor (shell.qml), which reads the items below; the shell's
// panel routes reach the OSD and the panel host's overlays the same way.
Item {
  id: services

  property var shell: null
  readonly property var known: ["notifications", "osd", "clipboard", "emojis", "imagepicker", "reminders", "menu", "background", "polkit", "media", "idle", "nightlight", "battery", "theme", "keybindings", "panels"]
  readonly property var enabled: {
    var wanted = String(Quickshell.env("TAMLINUX_SERVICES") || "").split(",")
    var picked = []
    for (var i = 0; i < wanted.length; i++) {
      var name = wanted[i].trim()
      if (known.indexOf(name) !== -1 && picked.indexOf(name) === -1) picked.push(name)
    }
    return picked
  }

  readonly property var notifications: notificationsLoader.item
  readonly property var media: mediaLoader.item
  readonly property var idle: idleLoader.item
  readonly property var nightlight: nightlightLoader.item
  readonly property var osd: osdLoader.item
  readonly property var panels: panelsLoader.item

  function note(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  // Static imports, not URLs: Quickshell only scans files it reaches by import.
  Loader {
    active: services.enabled.indexOf("theme") !== -1
    sourceComponent: Component { Theme.Service {} }
    onLoaded: services.note("service-loaded theme")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed theme")
  }

  Loader {
    id: notificationsLoader
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
    id: menuLoader
    active: services.enabled.indexOf("menu") !== -1
    sourceComponent: Component {
      Menu.Service { osd: osdLoader.item }
    }
    onLoaded: services.note("service-loaded menu")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed menu")
  }

  Loader {
    active: services.enabled.indexOf("background") !== -1
    sourceComponent: Component {
      Background.Service { menu: menuLoader.item }
    }
    onLoaded: services.note("service-loaded background")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed background")
  }

  Loader {
    active: services.enabled.indexOf("polkit") !== -1
    sourceComponent: Component {
      Polkit.Service {}
    }
    onLoaded: services.note("service-loaded polkit")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed polkit")
  }

  Loader {
    id: mediaLoader
    active: services.enabled.indexOf("media") !== -1
    sourceComponent: Component {
      Media.Service { osd: osdLoader.item }
    }
    onLoaded: services.note("service-loaded media")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed media")
  }

  Loader {
    id: idleLoader
    active: services.enabled.indexOf("idle") !== -1
    sourceComponent: Component {
      Idle.Service {}
    }
    onLoaded: services.note("service-loaded idle")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed idle")
  }

  Loader {
    id: nightlightLoader
    active: services.enabled.indexOf("nightlight") !== -1
    sourceComponent: Component {
      Nightlight.Service {}
    }
    onLoaded: services.note("service-loaded nightlight")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed nightlight")
  }

  Loader {
    active: services.enabled.indexOf("battery") !== -1
    sourceComponent: Component {
      Battery.Service {}
    }
    onLoaded: services.note("service-loaded battery")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed battery")
  }

  Loader {
    active: services.enabled.indexOf("keybindings") !== -1
    sourceComponent: Component {
      Keybindings.Service { shell: services.shell }
    }
    onLoaded: services.note("service-loaded keybindings")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed keybindings")
  }

  Loader {
    id: panelsLoader
    active: services.enabled.indexOf("panels") !== -1
    sourceComponent: Component {
      PanelHost { shell: services.shell; osd: osdLoader.item; media: mediaLoader.item }
    }
    onLoaded: services.note("service-loaded panels")
    onStatusChanged: if (status === Loader.Error) services.note("service-failed panels")
  }

  Component.onCompleted: note("services " + (enabled.length > 0 ? enabled.join(",") : "none"))
}
