import QtQuick
import Tam.Ui
import Tam.Commons
import Tam.Commons as Commons
import "KeyboardModel.js" as KM
import "."

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
  implicitHeight: placedRows.reduce(function (height, row) {
    return height + (row.height + row.gapAfter) * view.unit
  }, 0)

  function isDown(code) {
    return code !== null && code !== undefined && !!view.pressed[code]
  }

  Column {
    spacing: 0

    Repeater {
      model: view.placedRows

      Item {
        id: rowItem
        required property var modelData
        readonly property real rowHeight: modelData.height
        width: view.boardUnits * view.unit
        height: (modelData.height + modelData.gapAfter) * view.unit

        Repeater {
          model: modelData.placed

          // A key spanning down from the row above is drawn by the row that
          // declared it, so the continued copy renders nothing.
          Loader {
            required property var modelData
            active: !modelData.continued
            x: modelData.x * view.unit
            y: (modelData.cell.y || 0) * view.unit
            width: modelData.w * view.unit
            height: (modelData.cell.h || rowItem.rowHeight) * view.unit

            // Loader owns the loaded item's size. Keep an intermediate Item
            // so it cannot stretch the keycap across the gutter.
            sourceComponent: Item {
              Rectangle {
                id: keycap
                readonly property var cell: modelData.cell
                readonly property bool isLed: !!cell.led
                readonly property bool ledLit: isLed && !!view.ledState[cell.led]
                readonly property bool isDead: !cell.led &&
                                              (cell.code === null || cell.code === undefined)
                readonly property var codes: KM.cellCodes(cell)
                readonly property bool down: codes.some(function (code) { return view.isDown(code) })
                readonly property bool bound: !isDead && !isLed &&
                                              codes.some(function (code) { return !!view.bindings[code] })
                readonly property bool marked: !isDead && !isLed &&
                                               codes.some(function (code) { return !!view.marked[code] })

                x: view.gutter / 2
                y: view.gutter / 2
                width: parent.width - view.gutter
                height: parent.height - view.gutter
                radius: isLed ? height / 2 : Math.max(2, Style.space(3))

                color: down ? Commons.Color.accent
                            : isLed ? (ledLit
                                       ? Commons.Color.accent
                                       : Qt.rgba(Commons.Color.foreground.r, Commons.Color.foreground.g,
                                                 Commons.Color.foreground.b, 0.08))
                            : marked ? Qt.rgba(Commons.Color.accent.r, Commons.Color.accent.g,
                                               Commons.Color.accent.b, 0.38)
                            : bound ? Qt.rgba(Commons.Color.accent.r, Commons.Color.accent.g,
                                              Commons.Color.accent.b, 0.16)
                            : Qt.rgba(Commons.Color.foreground.r, Commons.Color.foreground.g,
                                      Commons.Color.foreground.b, 0.06)

                border.width: marked ? 2 : 1
                border.color: (down || ledLit || marked)
                  ? Commons.Color.accent
                  : Qt.rgba(Commons.Color.foreground.r, Commons.Color.foreground.g, Commons.Color.foreground.b,
                            isDead ? 0.12 : 0.22)

                Column {
                  anchors.centerIn: parent
                  width: parent.width - 4
                  spacing: 0
                  readonly property color labelColor: (keycap.down || keycap.ledLit)
                    ? Commons.Color.background
                    : keycap.isDead ? Qt.rgba(Commons.Color.foreground.r, Commons.Color.foreground.g,
                                       Commons.Color.foreground.b, 0.40)
                             : Commons.Color.foreground
                  Text {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    fontSizeMode: Text.HorizontalFit
                    minimumPixelSize: 7
                    text: keycap.cell.label !== undefined ? keycap.cell.label : keycap.cell.id
                    font.family: Style.font.family
                    font.pixelSize: Math.max(8, Math.min(view.unit * 0.30, keycap.height * 0.52))
                    color: parent.labelColor
                  }
                  Text {
                    visible: text !== ""
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    fontSizeMode: Text.HorizontalFit
                    minimumPixelSize: 6
                    text: keycap.cell.secondaryLabel || ""
                    font.family: Style.font.family
                    font.pixelSize: Math.max(6, view.unit * 0.18)
                    color: parent.labelColor
                    opacity: 0.75
                  }
                }

                // Hover shows the key's code and every bind on it. Hover only:
                // no buttons accepted, so clicks fall through to whatever owns
                // them (the capture surface, when the mode is on).
                MouseArea {
                  id: hover
                  anchors.fill: parent
                  hoverEnabled: !keycap.isLed
                  acceptedButtons: Qt.NoButton
                }

                PanelToolTip {
                  visible: hover.containsMouse && text !== ""
                  text: view.tooltipFor(keycap.cell)
                }

                // A key the OS never sees (firmware-local, e.g. Fn) is marked so
                // its permanent inertness reads as intentional, not broken.
                Text {
                  visible: keycap.isDead && !keycap.isLed
                  anchors.top: parent.top
                  anchors.right: parent.right
                  anchors.margins: 1
                  text: "○"
                  font.pixelSize: Math.max(6, view.unit * 0.18)
                  color: Qt.rgba(Commons.Color.foreground.r, Commons.Color.foreground.g,
                                 Commons.Color.foreground.b, 0.45)
                }
              }
            }
          }
        }
      }
    }
  }
}
