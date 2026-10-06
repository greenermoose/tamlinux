// Ported from omarchy 4.0.4 shell/plugins/menu/BarWidget.qml
// (MIT, Copyright (c) David Heinemeier Hansson; see ../../services/LICENSE-omarchy).
// Changes: owned module id; the clicks call the bar's typed actions
// (openMenu, openTerminal) instead of bar.run command strings. The glyph is
// still Omarchy's logo font until the Tamlinux look (plan 18 step 0.5).

import QtQuick
import Tam.Ui

BarWidget {
  id: root
  moduleName: "tamlinux.menu"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: ""
    fontFamily: "omarchy"
    horizontalMargin: 7.5
    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.openTerminal("")
      else root.bar.openMenu("")
    }
  }
}
