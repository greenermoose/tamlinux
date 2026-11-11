import QtQuick

// Replace only the Wayland window for an offscreen calendar interaction test.
Item {
  property Item anchorItem: null
  property QtObject bar: null
  property var owner: null
  property bool open: false
  property bool centerOnBar: false
  property Item focusTarget: null
  property int contentWidth: 560
  property int contentHeight: 800
  function fittedContentWidth(value) { return value }
  function fittedContentHeight(value) { return value }
}
