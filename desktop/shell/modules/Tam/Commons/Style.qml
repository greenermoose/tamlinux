pragma Singleton
import QtQuick
import Quickshell

// Spacing and type scale. TAMLINUX_UI_SCALE multiplies the 12px root.
// Token formulas match shell/host/ui_contract.py. This does not read a theme.
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

  readonly property int normalBorderWidth: 1

  function controlFill(focused, hot, foreground, accent) {
    if (focused) return Util.alpha(accent || foreground || Color.accent, 0.22)
    if (hot) return hoverFillFor(foreground, accent)
    return Util.alpha(foreground || Color.foreground, 0.08)
  }

  readonly property QtObject spacing: QtObject {
    readonly property int hairline: root.space(1)
    readonly property int xs: root.space(3)
    readonly property int sm: root.space(4)
    readonly property int md: root.space(6)
    readonly property int lg: root.space(8)
    readonly property int xl: root.space(10)
    readonly property int controlGap: root.space(8)
    readonly property int controlPaddingX: root.space(10)
    readonly property int controlPaddingY: root.space(6)
    readonly property int controlHeight: root.space(28)
    readonly property int popupRowHeight: root.space(28)
    readonly property int popupPadding: root.space(14)
    readonly property int rowPaddingX: root.space(12)
  }

  readonly property QtObject font: QtObject {
    readonly property string family: root.fontFamily
    readonly property int baseSize: root.fontBaseSize
    readonly property int caption: root.fontPx(0.833)
    readonly property int bodySmall: root.fontPx(0.917)
    readonly property int body: root.fontPx(1.0)
    readonly property int subtitle: root.fontPx(13 / 12)
    readonly property int title: root.fontPx(1.167)
    readonly property int icon: root.fontPx(1.167)
    readonly property int display: root.fontPx(2)
    readonly property int displayLarge: root.fontPx(28 / 12)
  }

  readonly property QtObject bar: QtObject {
    readonly property int sizeHorizontal: Math.max(1, Math.round(26 * root.uiScale))
    readonly property int iconSlot: Math.max(1, Math.round(27 * root.uiScale))
    readonly property int iconCanvas: Math.max(1, Math.round(16 * root.uiScale))
    readonly property int iconFont: Math.max(1, Math.round(13 * root.uiScale))
    readonly property int statusSlot: Math.max(1, Math.round(21 * root.uiScale))
  }
}
