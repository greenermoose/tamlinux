// Ported from omarchy 4.0.4 shell/plugins/bar/indicators/Dnd.qml
// (MIT, Copyright (c) David Heinemeier Hansson; see ../../services/LICENSE-omarchy).
// Changes: owned module, id, and command names.

import QtQuick
import Tam.Commons
import Tam.Ui

BarIndicator {
  id: root

  readonly property var notificationService: bar?.shell?.firstPartyServiceFor("tamlinux.notifications")
  readonly property bool dnd: notificationService ? notificationService.doNotDisturb : false

  active: dnd
  activeText: "󰂛"
  inactiveText: "󰂛"
  activeTooltipText: "Allow Notifications"
  inactiveTooltipText: "Silence Notifications"

  onPressed: function() {
    if (root.notificationService) {
      root.notificationService.setDoNotDisturb(!root.notificationService.doNotDisturb)
    }
  }
}
