pragma Singleton
import QtQuick
import Quickshell

// Spacing and type scale for the clock proof. TAMLINUX_UI_SCALE multiplies
// the 12px root; it does not read compositor options.
QtObject {
  id: root

  readonly property real uiScale: {
    var n = Number(Quickshell.env("TAMLINUX_UI_SCALE") || "1")
    if (!isFinite(n) || n <= 0 || n > 3) return 1
    return n
  }

  property int cornerRadius: 8
  property int gapsOut: 8
  property int fontBaseSize: Math.max(1, Math.round(12 * uiScale))
  property real spacingScale: uiScale
  property string fontFamily: "monospace"

  function spaceReal(px) {
    var n = Number(px)
    if (!isFinite(n) || n <= 0) return 0
    return n * spacingScale
  }

  function space(px) {
    var n = spaceReal(px)
    if (n <= 0) return 0
    return Math.max(1, Math.round(n))
  }

  function fontPx(mult) {
    return Math.max(1, Math.round(fontBaseSize * mult))
  }

  function hoverStateColor(foreground, accent) {
    return foreground || Color.foreground
  }

  function selectedStateColor(foreground, accent) {
    return accent || Color.accent
  }

  function normalStateColor(foreground, accent) {
    return foreground || Color.foreground
  }

  function hoverFillFor(foreground, accent) {
    return Util.alpha(hoverStateColor(foreground, accent), 0.12)
  }

  function selectedFillFor(foreground, accent) {
    return Util.alpha(selectedStateColor(foreground, accent), 0.22)
  }

  function normalBorderFor(foreground, accent) {
    return Util.alpha(normalStateColor(foreground, accent), 0.4)
  }

  readonly property QtObject spacing: QtObject {
    readonly property int hairline: root.space(1)
    readonly property int controlPaddingX: root.space(10)
    readonly property int controlPaddingY: root.space(6)
    readonly property int popupPadding: root.space(14)
    readonly property int sm: root.space(4)
  }

  readonly property QtObject font: QtObject {
    readonly property string family: root.fontFamily
    readonly property int caption: root.fontPx(0.833)
    readonly property int bodySmall: root.fontPx(0.917)
    readonly property int body: root.fontPx(1.0)
    readonly property int title: root.fontPx(1.167)
    readonly property int icon: root.fontPx(1.167)
  }

  readonly property QtObject bar: QtObject {
    readonly property int sizeHorizontal: Math.max(1, Math.round(26 * root.uiScale))
    readonly property int iconSlot: Math.max(1, Math.round(27 * root.uiScale))
  }
}
