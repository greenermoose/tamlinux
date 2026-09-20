import QtQuick
import qs.Commons

// A list of binds as "chord   what it does" rows, laid out in two columns
// filled top to bottom (column-major, so reading order is natural), inside
// a bounded, wheel-scrollable area with a scroll indicator when it overflows.
// Used by the search results and the orphan-bind list.
//
// rows: [{ chord, does, muted }]. `muted` draws the chord in the muted colour
// (an orphan: findable, not pressable here).
Item {
  id: root

  property var rows: []
  property int columns: 2
  property real maxHeight: Style.space(240)
  property real rowGap: Style.spacing.xs

  // True when there is more than fits: the caller can say "scroll" in its
  // caption, and the indicator at the right edge shows where you are.
  readonly property bool overflowing: flick.contentHeight > flick.height + 1

  readonly property color muted: Qt.rgba(Color.foreground.r, Color.foreground.g,
                                         Color.foreground.b, 0.55)

  visible: rows.length > 0
  implicitHeight: visible ? flick.height : 0

  // Split rows column-major: the first ceil(n/columns) go left, and so on.
  readonly property var slices: {
    var n = root.rows.length, per = Math.ceil(n / Math.max(1, root.columns)), out = []
    for (var c = 0; c < root.columns; c++) out.push(root.rows.slice(c * per, (c + 1) * per))
    return out
  }

  Flickable {
    id: flick
    width: parent.width
    height: Math.min(columnsRow.implicitHeight, root.maxHeight)
    contentHeight: columnsRow.implicitHeight
    contentWidth: width
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    Row {
      id: columnsRow
      width: flick.width - (root.overflowing ? indicator.width + Style.spacing.sm : 0)
      spacing: Style.spacing.rowPaddingX

      Repeater {
        model: root.slices

        Column {
          id: col
          required property var modelData
          width: (columnsRow.width - columnsRow.spacing * (root.columns - 1)) / root.columns
          spacing: 0

          // The widest chord in this column sets its chord column.
          readonly property real chordColumn: {
            var w = 0
            for (var i = 0; i < meter.count; i++) {
              var it = meter.itemAt(i)
              if (it) w = Math.max(w, it.implicitWidth)
            }
            return Math.min(w + Style.spacing.md, width * 0.6)
          }

          Repeater {
            id: meter
            model: col.modelData
            Text {
              required property var modelData
              visible: false
              text: modelData.chord
              font.family: Style.font.family
              font.pixelSize: Style.font.caption
            }
          }

          Repeater {
            model: col.modelData

            Item {
              required property var modelData
              width: col.width
              height: doesText.implicitHeight + root.rowGap

              Text {
                id: chordText
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                width: col.chordColumn
                elide: Text.ElideRight
                text: modelData.chord
                font.family: Style.font.family
                font.pixelSize: Style.font.caption
                color: modelData.muted ? root.muted : Color.accent
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
                color: Color.foreground
              }
            }
          }
        }
      }
    }
  }

  // Scroll indicator: a track at the right edge with a thumb sized and
  // placed from the Flickable's visible area. Present only when there is
  // somewhere to scroll to.
  Rectangle {
    id: indicator
    visible: root.overflowing
    anchors.right: parent.right
    anchors.top: flick.top
    width: Math.max(3, Style.space(4))
    height: flick.height
    radius: width / 2
    color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.10)

    Rectangle {
      width: parent.width
      radius: width / 2
      color: Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.7)
      height: Math.max(Style.space(16), parent.height * flick.visibleArea.heightRatio)
      y: (parent.height - height) * (flick.visibleArea.yPosition /
                                     Math.max(0.0001, 1 - flick.visibleArea.heightRatio))
    }
  }
}
