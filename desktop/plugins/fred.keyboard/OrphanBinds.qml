import QtQuick
import qs.Commons

// Binds whose key is not on the attached keyboard: a one-line header that
// expands into "chord - what it does" rows. Fred's config carries binds
// inherited from a laptop (XF86 media and brightness keys, a touchpad
// toggle) that a desktop board can never send; F13-F24 are the same story.
// They are shown so nobody wonders why a documented shortcut does nothing,
// and shown out of the way because that is a once-in-a-while question.
Item {
  id: root

  // [{ chord, does }], sorted by the caller.
  property var rows: []
  property int total: 0
  property bool expanded: false
  signal toggled()

  readonly property real dim: 0.55
  readonly property color muted: Qt.rgba(Color.foreground.r, Color.foreground.g,
                                         Color.foreground.b, dim)

  visible: rows.length > 0
  implicitHeight: visible ? column.implicitHeight : 0

  Column {
    id: column
    width: parent.width
    spacing: Style.spacing.xs

    // Header row: chevron + summary. Clickable when capture mode is off
    // (with it on, the capture surface above records the click instead).
    Item {
      width: parent.width
      height: headerText.implicitHeight + Style.spacing.xs * 2

      Row {
        anchors.verticalCenter: parent.verticalCenter
        spacing: Style.spacing.sm

        Text {
          text: root.expanded ? "▾" : "▸"
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          color: root.muted
        }

        Text {
          id: headerText
          text: root.rows.length + " of " + root.total + " binds use keys this keyboard " +
                "does not have" + (root.expanded ? ":" : "")
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          color: root.muted
        }
      }

      MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.toggled()
      }
    }

    // The list. Two columns so chords line up; the widest chord sets the
    // column. Scrolls if the panel cannot fit it.
    Flickable {
      visible: root.expanded
      width: parent.width
      height: Math.min(list.implicitHeight, Style.space(220))
      contentHeight: list.implicitHeight
      clip: true
      boundsBehavior: Flickable.StopAtBounds

      Column {
        id: list
        width: parent.width
        spacing: 0

        readonly property real chordColumn: {
          var w = 0
          for (var i = 0; i < chordMeter.count; i++) {
            var it = chordMeter.itemAt(i)
            if (it) w = Math.max(w, it.implicitWidth)
          }
          return Math.min(w + Style.spacing.md, parent.width * 0.5)
        }

        Repeater {
          id: chordMeter
          model: root.rows
          // Measured, never shown: the widest chord.
          Text {
            required property var modelData
            visible: false
            text: modelData.chord
            font.family: Style.font.family
            font.pixelSize: Style.font.caption
          }
        }

        Repeater {
          model: root.rows

          Item {
            required property var modelData
            width: list.width
            height: doesText.implicitHeight + Style.spacing.xs

            Text {
              id: chordText
              anchors.left: parent.left
              anchors.leftMargin: Style.spacing.md
              anchors.verticalCenter: parent.verticalCenter
              width: list.chordColumn
              elide: Text.ElideRight
              text: modelData.chord
              font.family: Style.font.family
              font.pixelSize: Style.font.caption
              color: Color.foreground
            }

            Text {
              id: doesText
              anchors.left: chordText.right
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              elide: Text.ElideRight
              text: modelData.does
              font.family: Style.font.family
              font.pixelSize: Style.font.caption
              color: root.muted
            }
          }
        }
      }
    }
  }
}
