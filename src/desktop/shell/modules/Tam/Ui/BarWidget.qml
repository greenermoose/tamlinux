import QtQuick
import Tam.Commons

// Base item the clock bar widget extends. The host injects bar, moduleName,
// and settings; setting() reads one inline entry with a fallback.
Item {
  id: root

  property QtObject bar: null
  property string moduleName: ""
  property var settings: ({})

  readonly property bool vertical: bar ? bar.vertical : false
  readonly property int barSize: bar ? bar.barSize : Style.bar.sizeHorizontal

  // Run `method` on every live copy of this widget, one per screen. An IPC
  // target reaches only one copy, so that copy relays the call (Omarchy's
  // Ui/BarWidget does the same).
  function broadcast(method) {
    var items = bar && typeof bar.moduleWidgets === "function"
      ? bar.moduleWidgets(moduleName) : [root]
    for (var i = 0; i < items.length; i++) {
      if (items[i] && typeof items[i][method] === "function") items[i][method]()
    }
  }

  function setting(name, fallback) {
    var value = settings ? settings[name] : undefined
    return value === undefined || value === null ? fallback : value
  }
}
