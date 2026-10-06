// Check the palette service with a stub adapter in an isolated environment.
import QtQuick
import Quickshell
import Tam.Commons
import "../../shell/services/theme" as Theme

ShellRoot {
  property int stage: 0
  property int ticks: 0
  property int completedReads: 0
  property string mode: Quickshell.env("TAMLINUX_THEME_CHECK_MODE") || "success"
  property string failure: ""
  Theme.Service { id: theme }

  Connections {
    target: theme
    function onBusyChanged() {
      if (theme.busy) return
      completedReads += 1
      if (completedReads === 2 && (mode === "failed-output" || mode === "malformed" || mode === "timeout")) {
        if (String(Color.background) !== "#0f1410" || Style.font.body !== Math.round(24 * Style.uiScale))
          failure = "failed reader changed the active theme"
      }
    }
  }

  function check(ok, message) {
    if (!ok) throw new Error(message)
  }

  Timer {
    interval: 25
    running: true
    repeat: true
    onTriggered: {
      try {
        ticks += 1
        if (failure) throw new Error(failure)
        if (ticks > 300) throw new Error("service timeout")
        if (stage === 0 && String(Color.background) === "#0f1410") {
          check(String(Color.menu.background) === "#123456", "startup surface")
          check(Style.font.body === Math.round(24 * Style.uiScale), "startup type scale")
          stage = 1
          theme.reloadTheme()
          theme.reloadTheme()
          theme.reloadTheme()
        } else if (stage === 1 && completedReads === 3) {
          check(String(Color.background) === "#102030", "recovery palette")
          check(String(Color.menu.background) === "#102030", "removed surface resets")
          check(Style.font.body === Math.round(12 * Style.uiScale), "removed style resets")
          console.log("TAMLINUX_THEME_SERVICE_PROOF PASS")
          Qt.quit()
        }
      } catch (error) {
        console.error("TAMLINUX_THEME_SERVICE_PROOF FAIL " + error)
        Qt.quit()
      }
    }
  }
}
