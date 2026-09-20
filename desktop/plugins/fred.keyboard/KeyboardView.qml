import QtQuick
import qs.Ui
import qs.Commons
import "KeyboardModel.js" as KM

// Draws a resolved keyboard layout as schematic keycaps.
//
// Schematic means flat rectangles sized in keycap units - not a trace of key
// profiles or the board's chassis. It does not mean approximate: which keys
// exist and where they sit comes from the resolved layout, so a non-standard
// board is drawn as it actually is.
Item {
  id: view

  // The layout object from layouts/*.json.
  property var layout: null

  // evdev codes currently held down, as an object used as a set.
  property var pressed: ({})

  // evdev code -> short description of what it is bound to, or "" if unbound.
  property var bindings: ({})

  // evdev codes to mark as search results: drawn with the accent outline.
  property var marked: ({})

  // cell -> hover text, provided by the owner (Bindings.keyTooltip).
  property var tooltipFor: function (cell) { return "" }

  // Real indicator state from sysfs, keyed by the cell's `led` name:
  // { capslock: bool, numlock: bool }
  property var ledState: ({})

  // Size of one keycap unit in pixels.
  property real unit: Style.space(34)
  property real gutter: Math.max(2, Style.space(3))

  readonly property var placedRows: layout ? KM.place(layout) : []
  readonly property real boardUnits: {
    var w = 0
    for (var i = 0; i < placedRows.length; i++) w = Math.max(w, placedRows[i].width)
    return w
  }

  implicitWidth: boardUnits * unit
  implicitHeight: placedRows.length * unit

  function isDown(code) {
    return code !== null && code !== undefined && !!view.pressed[code]
  }

  Column {
    spacing: 0

    Repeater {
      model: view.placedRows

      Item {
        required property var modelData
        width: view.boardUnits * view.unit
        height: view.unit

        Repeater {
          model: modelData.placed

          // A key spanning down from the row above is drawn by the row that
          // declared it, so the continued copy renders nothing.
          Loader {
            required property var modelData
            active: !modelData.continued
            x: modelData.x * view.unit
            y: 0
            width: modelData.w * view.unit
            height: (modelData.cell.h || 1) * view.unit

            sourceComponent: Rectangle {
              readonly property var cell: modelData.cell
              readonly property bool isLed: !!cell.led
              readonly property bool ledLit: isLed && !!view.ledState[cell.led]
              readonly property bool isDead: !cell.led &&
                                            (cell.code === null || cell.code === undefined)
              readonly property bool down: view.isDown(cell.code)
              readonly property bool bound: !isDead && !isLed &&
                                            !!view.bindings[cell.code]
              readonly property bool marked: !isDead && !isLed &&
                                             !!view.marked[cell.code]

              x: view.gutter / 2
              y: view.gutter / 2
              width: parent.width - view.gutter
              height: parent.height - view.gutter
              radius: isLed ? height / 2 : Math.max(2, Style.space(3))

              color: down ? Color.accent
                          : isLed ? (ledLit
                                     ? Color.accent
                                     : Qt.rgba(Color.foreground.r, Color.foreground.g,
                                               Color.foreground.b, 0.08))
                          : marked ? Qt.rgba(Color.accent.r, Color.accent.g,
                                             Color.accent.b, 0.38)
                          : bound ? Qt.rgba(Color.accent.r, Color.accent.g,
                                            Color.accent.b, 0.16)
                          : Qt.rgba(Color.foreground.r, Color.foreground.g,
                                    Color.foreground.b, 0.06)

              border.width: marked ? 2 : 1
              border.color: (down || ledLit || marked)
                ? Color.accent
                : Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b,
                          isDead ? 0.12 : 0.22)

              Text {
                anchors.centerIn: parent
                width: parent.width - 4
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                text: cell.label !== undefined ? cell.label : cell.id
                font.family: Style.font.family
                font.pixelSize: Math.max(8, view.unit * 0.30)
                color: (down || ledLit)
                  ? Color.background
                  : isDead ? Qt.rgba(Color.foreground.r, Color.foreground.g,
                                     Color.foreground.b, 0.40)
                           : Color.foreground
              }

              // Hover shows the key's code and every bind on it. Hover only:
              // no buttons accepted, so clicks fall through to whatever owns
              // them (the capture surface, when the mode is on).
              MouseArea {
                id: hover
                anchors.fill: parent
                hoverEnabled: !isLed
                acceptedButtons: Qt.NoButton
              }

              PanelToolTip {
                visible: hover.containsMouse && text !== ""
                text: view.tooltipFor(cell)
              }

              // A key the OS never sees (firmware-local, e.g. Fn) is marked so
              // its permanent inertness reads as intentional, not broken.
              Text {
                visible: isDead && !isLed
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.margins: 1
                text: "○"
                font.pixelSize: Math.max(6, view.unit * 0.18)
                color: Qt.rgba(Color.foreground.r, Color.foreground.g,
                               Color.foreground.b, 0.45)
              }
            }
          }
        }
      }
    }
  }
}
