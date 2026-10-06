// A headless check of real QML bindings, including successive theme changes.
import QtQuick
import Quickshell
import Tam.Commons

ShellRoot {
  function check(ok, message) {
    if (!ok) throw new Error(message)
  }

  function payload(surfaces) {
    return {palette: {foreground: "#e4e6d8", background: "#0f1410",
      accent: "#86b86a", accentText: "#e4e6d8", urgent: "#e07a5f",
      muted: "#9aa391"}, surfaces: surfaces, style: {}}
  }

  Timer {
    interval: 1
    running: true
    onTriggered: {
      try {
        check(Color.applyPayload(payload({"menu.background": "#123456",
          "polkit.text-error": "#abcdef", "image-picker.scrim": "#800f1410"})), "first palette")
        check(String(Color.menu.background) === "#123456", "surface override")
        check(String(Color.polkit.textError) === "#abcdef", "error override")
        check(Color.imagePicker.scrim.a > 0.49 && Color.imagePicker.scrim.a < 0.51, "Qt ARGB alpha")
        check(String(Color.notifications.text) === "#e4e6d8", "notification binding")
        check(Color.applyPayload(payload({})), "second palette")
        check(String(Color.menu.background) === "#0f1410", "old surface reset")
        check(String(Color.polkit.textError) === "#e07a5f", "old error reset")
        check(String(Color.imagePicker.selectedBorder) === "#86b86a", "picker binding")
        var invalid = payload({})
        invalid.palette.accent = "invalid"
        check(!Color.applyPayload(invalid), "reject invalid palette")
        check(String(Color.accent) === "#86b86a", "rejection preserves palette")
        Style.applyThemeStyle({fontBaseSize: 24, spacingScale: 1})
        check(Style.font.body === Math.round(24 * Style.uiScale), "type scale")
        check(Style.spacing.controlHeight === Math.round(56 * Style.uiScale), "controls grow with type")
        check(Style.bar.sizeHorizontal === Math.round(52 * Style.uiScale), "bar grows with type")
        Style.applyThemeStyle({fontBaseSize: 2, spacingScale: 100})
        check(Style.font.body === Math.round(12 * Style.uiScale) &&
          Style.spacing.controlHeight === Math.round(28 * Style.uiScale), "invalid style resets")
        Style.applyThemeStyle({})
        check(Style.font.family === "monospace", "fontconfig source")
        console.log("TAMLINUX_THEME_PROOF PASS")
      } catch (error) {
        console.error("TAMLINUX_THEME_PROOF FAIL " + error)
      }
      Qt.quit()
    }
  }
}
