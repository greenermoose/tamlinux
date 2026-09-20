import QtQuick
import qs.Ui
import qs.Commons

// Reverse lookup: type part of a command, see the chords that run it. The
// matching keys are marked on the board by the owner (via `results`).
//
// Focus rules. While the field has focus, keystrokes are text and the live
// board does not record them; Escape hands focus back to the capture area
// (clearing the query first if there is one). Capture mode and search are
// modes, not neighbours: switching capture on takes focus from the field,
// and while capture is on the field cannot be clicked, since every click in
// the panel is recorded instead.
Item {
  id: root

  property string query: ""
  property var results: []        // from Bindings.searchBinds
  property int total: 0

  // Where focus goes when the field is left.
  property Item focusHome: null

  readonly property color muted: Qt.rgba(Color.foreground.r, Color.foreground.g,
                                         Color.foreground.b, 0.55)

  implicitHeight: column.implicitHeight

  function leave() {
    if (root.focusHome) root.focusHome.forceActiveFocus()
  }

  function clear() {
    field.text = ""
  }

  Column {
    id: column
    width: parent.width
    spacing: Style.spacing.xs

    TextField {
      id: field
      width: parent.width
      placeholderText: "Find a command: volume, workspace, screenshot..."
      onTextChanged: root.query = text
      Keys.onEscapePressed: function (event) {
        if (field.text !== "") field.text = ""
        else root.leave()
        event.accepted = true
      }
    }

    Text {
      visible: root.query !== "" && root.results.length === 0
      width: parent.width
      text: "No bind matches."
      font.family: Style.font.family
      font.pixelSize: Style.font.caption
      color: root.muted
    }

    BindList {
      id: list
      width: parent.width
      maxHeight: Style.space(220)
      rows: {
        var out = []
        for (var i = 0; i < root.results.length; i++)
          out.push({ chord: root.results[i].label, does: root.results[i].does,
                     muted: !root.results[i].placed })
        return out
      }
    }

    Text {
      visible: root.results.length > 0
      width: parent.width
      text: root.results.length + " match" + (root.results.length === 1 ? "" : "es") +
            (root.results.length >= 60 ? " (first 60)" : "") +
            " - marked on the board." +
            (list.overflowing ? " Scroll the list with the mouse wheel." : "") +
            " Esc clears."
      font.family: Style.font.family
      font.pixelSize: Style.font.caption
      color: root.muted
    }
  }
}
