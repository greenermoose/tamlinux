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

  // Room the list may take. The owner computes it from what else is in the
  // panel, so the expanded list never pushes the panel past its card.
  property real maxListHeight: Style.space(260)

  // Height of everything here except the list: the header row and, when
  // expanded, a line reserved for the scroll hint whether or not it shows
  // (reading `list.overflowing` here would loop back through the list's
  // own height). Lets the owner size `maxListHeight`.
  readonly property real fixedHeight: headerRow.height + column.spacing +
                                      (expanded ? scrollHint.implicitHeight + column.spacing : 0)

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
      id: headerRow
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

    BindList {
      id: list
      visible: root.expanded
      width: parent.width
      maxHeight: Math.max(Style.space(60), root.maxListHeight)
      rows: {
        var out = []
        for (var i = 0; i < root.rows.length; i++)
          out.push({ chord: root.rows[i].chord, does: root.rows[i].does, muted: false })
        return out
      }
    }

    Text {
      id: scrollHint
      visible: root.expanded && list.overflowing
      width: parent.width
      text: "Scroll the list with the mouse wheel."
      font.family: Style.font.family
      font.pixelSize: Style.font.caption
      color: root.muted
    }
  }
}
