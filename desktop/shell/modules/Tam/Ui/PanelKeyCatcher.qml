import QtQuick

// Key dispatcher for the calendar popup. Escape closes, arrows move, and
// other single characters are forwarded as text.
Item {
  id: root

  property bool blocked: false

  signal moveRequested(int dx, int dy)
  signal activateRequested()
  signal closeRequested()
  signal returnRequested()
  signal tabRequested(int direction)
  signal textKey(string text)

  focus: true
  Keys.priority: Keys.BeforeItem
  Keys.onPressed: function(event) {
    if (root.blocked) return
    if (event.key === Qt.Key_Escape) {
      closeRequested()
      event.accepted = true
      return
    }
    if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
      tabRequested((event.modifiers & Qt.ShiftModifier) || event.key === Qt.Key_Backtab ? -1 : 1)
      event.accepted = true
      return
    }
    if (event.key === Qt.Key_Down) { moveRequested(0, 1); event.accepted = true; return }
    if (event.key === Qt.Key_Up) { moveRequested(0, -1); event.accepted = true; return }
    if (event.key === Qt.Key_Right) { moveRequested(1, 0); event.accepted = true; return }
    if (event.key === Qt.Key_Left) { moveRequested(-1, 0); event.accepted = true; return }
    if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
      returnRequested()
      activateRequested()
      event.accepted = true
      return
    }
    if (event.key === Qt.Key_Space) {
      activateRequested()
      event.accepted = true
      return
    }
    if (event.text && event.text.length === 1 && event.key !== Qt.Key_Escape) {
      textKey(event.text)
      event.accepted = true
    }
  }
}
