import QtQuick
import Tam.Commons
import Tam.Ui

// Constructs the shared controls the other plugins bind. It is not a fred.*
// plugin, it has no panel of its own, and it does not register an IPC target.
BarWidget {
  id: root

  moduleName: "tamlinux.ui"
  property string hostKey: ""

  implicitWidth: 8
  implicitHeight: 8

  function note(line) {
    console.log("TAMLINUX_EVIDENCE " + line)
  }

  function sameColor(left, right) {
    var a = Qt.color(String(left))
    var b = Qt.color(String(right))
    return Math.round(a.r * 255) === Math.round(b.r * 255)
      && Math.round(a.g * 255) === Math.round(b.g * 255)
      && Math.round(a.b * 255) === Math.round(b.b * 255)
  }

  function wheelPair(accumulator, delta) {
    var result = Util.wheelSteps(accumulator, delta)
    return Math.round(result.steps) + "," + Math.round(result.remainder)
  }

  function bindHost() {
    var flatSpec = Border.flat("#8eb6c9", 2)
    var surface = Border.surfaceSpec("popups", "border", "#3c4a54", 1)
    var focus = Border.controlSpec("focus", "#d7dde2", "#8eb6c9")
    var normal = Border.controlSpec("normal", "#d7dde2", "#8eb6c9")
    note("ui-border flat-top=" + Border.top(flatSpec)
      + " surface-top=" + Border.top(surface)
      + " control-top=" + Border.top(focus)
      + " focus-accent=" + (sameColor(focus.color, "#8eb6c9") ? "true" : "false")
      + " normal-foreground=" + (sameColor(normal.color, "#d7dde2") ? "true" : "false")
      + " overlay=" + (Border.needsOverlay(focus) ? "true" : "false"))
    note("ui-wheel " + wheelPair(0, 120) + " " + wheelPair(0, 60) + " " + wheelPair(60, 60) + " " + wheelPair(100, -20))
    var fill = Style.controlFill(false, true, Color.foreground, Color.accent)
    note("ui-tokens display=" + Style.font.display
      + " large=" + Style.font.displayLarge
      + " subtitle=" + Style.font.subtitle
      + " base=" + Style.font.baseSize
      + " control=" + Style.spacing.controlHeight
      + " slot=" + Style.bar.statusSlot
      + " accent=" + (Color.accentText ? "set" : "missing")
      + " fill=" + (fill ? "set" : "missing"))
    note("ui-built Border")
    note("ui-built BarIconButton")
    note("ui-built BorderSurface")
    note("ui-built CursorSurface")
    note("ui-built Dropdown")
    note("ui-built PanelHero")
    note("ui-built PanelSectionHeader")
    note("ui-built PanelSlider")
    note("ui-built ToggleSwitch")
    note("ui-built Button")
    note("ui-built host=" + hostKey)
  }

  Item {
    visible: false
    width: 1
    height: 1

    BarIconButton {
      bar: root.bar
      text: "A"
      active: true
      tooltipText: "ui"
    }

    BorderSurface {
      width: 4
      height: 4
      borderSpec: Border.flat("#8eb6c9", 1)
    }

    CursorSurface {
      width: 4
      height: 4
      outline: true
      hasCursor: true

      PanelSlider {
        anchors.fill: parent
        bar: root.bar
        minimum: 0
        maximum: 1
        step: 0.5
        value: 0.5
      }
    }

    Dropdown {
      value: "center"
      showLabel: false
      options: [
        { value: "top", label: "Top" },
        { value: "center", label: "Center" }
      ]
    }

    PanelHero {
      title: "UI"
      meta: "proof"
      foreground: Color.foreground
      iconComponent: Component {
        Text { text: "A"; color: Color.foreground }
      }
    }

    PanelSectionHeader {
      text: "SECTION"
      foreground: Color.foreground
    }

    ToggleSwitch {
      checked: true
      interactive: false
    }

    Button {
      text: "Apply"
      iconText: "A"
      bordered: true
      active: true
      iconSpinning: false
    }
  }
}
