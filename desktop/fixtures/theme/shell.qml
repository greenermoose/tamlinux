// A headless check of real QML bindings, including successive theme changes.
import QtQuick
import Quickshell
import Tam.Commons
import Tam.Commons as Commons

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
        check(String(Commons.Color.background) === "#14181c", "startup palette")
        check(String(Commons.Color.polkit.text) === "#d7dde2", "visible prompt defaults")
        check(Commons.Color.applyPayload(payload({"menu.background": "#123456",
          "polkit.text-error": "#abcdef", "image-picker.scrim": "#800f1410"})), "first palette")
        check(String(Commons.Color.menu.background) === "#123456", "surface override")
        check(String(Commons.Color.polkit.textError) === "#abcdef", "error override")
        check(Commons.Color.imagePicker.scrim.a > 0.49 && Commons.Color.imagePicker.scrim.a < 0.51, "Qt ARGB alpha")
        check(String(Commons.Color.notifications.text) === "#e4e6d8", "notification binding")
        check(Commons.Color.applyPayload(payload({})), "second palette")
        check(String(Commons.Color.menu.background) === "#0f1410", "old surface reset")
        check(String(Commons.Color.polkit.textError) === "#e07a5f", "old error reset")
        check(String(Commons.Color.imagePicker.selectedBorder) === "#86b86a", "picker binding")
        var invalid = payload({})
        invalid.palette.accent = "invalid"
        check(!Commons.Color.applyPayload(invalid), "reject invalid palette")
        check(String(Commons.Color.accent) === "#86b86a", "rejection preserves palette")
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
