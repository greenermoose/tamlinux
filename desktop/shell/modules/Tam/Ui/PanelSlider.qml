import QtQuick
import Tam.Commons

Item {
  id: root

  property QtObject bar: null
  property real value: 0
  property real minimum: 0
  property real maximum: 1
  property real step: 0.05
  property bool integer: false
  property bool dragging: false
  property int tickCount: 0
  property color trackColor: bar ? Style.selectedFillFor(bar.foreground, Color.accent) : "#333333"
  property color fillColor: bar ? bar.foreground : Color.foreground
  property color knobColor: bar ? bar.foreground : Color.foreground

  signal moved(real value)
  signal released(real value)
  signal rightClicked()

  implicitHeight: Math.max(Style.spacing.controlHeight, knobSize)
  readonly property real trackHeight: Math.max(4, Math.round(Style.spacing.controlHeight * 0.11))
  readonly property real knobSize: Math.max(14, Math.round(Style.spacing.controlHeight * 0.38))

  function snap(raw) {
    var span = maximum - minimum
    if (!isFinite(span) || span <= 0) return minimum
    var clamped = Math.max(minimum, Math.min(maximum, raw))
    var increment = step > 0 ? step : span
    var steps = Math.round((clamped - minimum) / increment)
    var next = minimum + steps * increment
    if (integer) next = Math.round(next)
    return Math.max(minimum, Math.min(maximum, next))
  }

  function valueFromX(x) {
    var span = Math.max(1, width - knobSize)
    var ratio = Math.max(0, Math.min(1, (x - knobSize / 2) / span))
    return snap(minimum + ratio * (maximum - minimum))
  }

  Rectangle {
    anchors.verticalCenter: parent.verticalCenter
    x: root.knobSize / 2
    width: Math.max(0, parent.width - root.knobSize)
    height: root.trackHeight
    radius: height / 2
    color: root.trackColor

    Rectangle {
      width: Math.max(0, (parent.width * (root.value - root.minimum)) / Math.max(0.001, root.maximum - root.minimum))
      height: parent.height
      radius: parent.radius
      color: root.fillColor
    }
  }

  Rectangle {
    width: root.knobSize
    height: root.knobSize
    radius: width / 2
    anchors.verticalCenter: parent.verticalCenter
    x: {
      var span = Math.max(1, root.width - root.knobSize)
      var ratio = (root.value - root.minimum) / Math.max(0.001, root.maximum - root.minimum)
      return Math.max(0, Math.min(span, ratio * span))
    }
    color: root.knobColor
  }

  MouseArea {
    anchors.fill: parent
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton | Qt.RightButton
    onPressed: function(mouse) {
      if (mouse.button === Qt.RightButton) {
        root.rightClicked()
        return
      }
      root.dragging = true
      root.value = root.valueFromX(mouse.x)
      root.moved(root.value)
    }
    onPositionChanged: function(mouse) {
      if (!root.dragging) return
      root.value = root.valueFromX(mouse.x)
      root.moved(root.value)
    }
    onReleased: function(mouse) {
      if (!root.dragging) return
      root.dragging = false
      root.value = root.valueFromX(mouse.x)
      root.released(root.value)
    }
  }
}
