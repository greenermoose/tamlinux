// Ported from omarchy 4.0.4 shell/plugins/menu/BarWidget.qml
// (MIT, Copyright (c) David Heinemeier Hansson; see ../../services/LICENSE-omarchy).
// Changes: owned module id; the clicks call the bar's typed actions
// (openMenu, openTerminal) instead of bar.run command strings. The glyph is
// the owned icon font preserves the retained glyph; new artwork follows later.

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
    fontFamily: "Tamlinux Icons"
    horizontalMargin: 7.5
    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.openTerminal("")
      else root.bar.openMenu("")
    }
  }
}
