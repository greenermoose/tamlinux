// Isolated headless proof: records actions and synthetic input, never live apps.
import QtQuick
import QtTest
import Quickshell
import Quickshell.Io
import Tam.Commons
import "services/menu" as Menu
import "host" as Host

ShellRoot {
  id: proof
  property int stage: 0
  property string recorded: ""
  property int gapActions: 0
  property int widgetActions: 0
  property bool screenshotReady: !Quickshell.env("START_MENU_SCREENSHOT")
  readonly property var primaryScreen: Quickshell.screens.find(function(screen) { return screen.name === "HEADLESS-1" })
  property var barLayout: null
  property string barPosition: "top"
  property bool barHidden: false
  property bool barTransparent: false
  property string clockEntry: ""
  property string fixtureEntry: ""
  property string compositorEntry: ""
  property string uiEntry: ""
  property var extraEntries: []
  property var compositor: QtObject {
    id: facade
    property var point: ({x: 40, y: 60})
    signal pointerPositionReady(int token, var point)
    function requestPointerPosition(token) {
      Qt.callLater(function() { facade.pointerPositionReady(token, facade.point) })
      return true
    }
  }
  function evidence(message) {}
  function attachHost(key, surface) {}
  function unregisterHost(key) {}
  function detachHost(key) {}
  function check(ok, message) {
    if (!ok) { console.error("START_FAILED " + message); Qt.exit(1) }
  }
  Menu.Service {
    id: menu
    shell: proof
    defaultMenuPath: __DEFAULT__
    userMenuPath: __EXTENSION__
    function runAction(command) { proof.recorded = command }
  }
  Host.BarWindow {
    id: bar
    shell: proof
    hostKey: "HEADLESS-1#0"
    screenRef: proof.primaryScreen
    Item {
      id: occupied
      x: 100; y: 0; width: 80; height: bar.height
      property string moduleName: "test.occupied"
      MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        onClicked: proof.widgetActions++
      }
    }
  }
  Host.HyprlandAdapter { id: adapterProbe }
  TestCase { id: input; parent: menu.menuWindow.contentItem; name: "StartInput"; when: false }
  Process {
    id: capture
    command: ["grim", "-o", "HEADLESS-1", Quickshell.env("START_MENU_SCREENSHOT")]
    onExited: function(code) { proof.check(code === 0, "isolated screenshot"); proof.screenshotReady = true }
  }
  Connections {
    target: bar.surface
    function onActivePopoutChanged() {}
  }
  Timer {
    interval: 120; repeat: true; running: true
    onTriggered: {
      if (!menu.rowsLoaded) return
      if (proof.stage === 0) {
        proof.check(adapterProbe.pointerResult(0, '{"x":-12.5,"y":3}').x === -12.5, "adapter pointer parse")
        proof.check(adapterProbe.pointerResult(1, '{"x":2,"y":3}') === null, "adapter failed query")
        proof.check(adapterProbe.pointerResult(0, '{"x":1e999,"y":3}') === null, "adapter rejects nonfinite point")
        proof.check(adapterProbe.pointerResult(0, '{"x":"2","y":3}') === null, "adapter rejects string coordinate")
        bar.surface.registerWidget(occupied)
        proof.check(bar.surface.occupiedAt(100, 5), "widget left edge occupied")
        proof.check(!bar.surface.occupiedAt(180, 5), "gap outside widget")
        occupied.visible = false
        proof.check(!bar.surface.occupiedAt(110, 5), "hidden widget releases gap")
        occupied.visible = true
        input.mouseClick(bar.contentItem, 110, 5, Qt.RightButton)
        proof.check(proof.widgetActions === 1, "widget right click preserved")
        input.mouseClick(bar.contentItem, 20, 5, Qt.RightButton)
        input.mouseClick(bar.contentItem, 20, 5, Qt.LeftButton)
        input.mouseClick(bar.contentItem, 20, 5, Qt.RightButton, Qt.MetaModifier)
        menu.startAt({output: proof.primaryScreen.name, x: 30, y: bar.height, edge: "top"})
        proof.stage = 1
      } else if (proof.stage === 1) {
        if (!proof.screenshotReady) { if (!capture.running) capture.running = true; return }
        proof.check(menu.startView && menu.visibleModel.count === 15, "both groups exposed")
        proof.check(menu.visibleModel.get(0).section === "Quick Launch", "launch heading")
        proof.check(menu.visibleModel.get(11).section === "Settings", "settings heading")
        proof.check(menu.cardHeight < 650 && menu.visibleRowsHeight > 400, "compact default fits 720")
        proof.check(menu.menuWindow.effectiveCardTop === bar.height, "bar anchored below bar")
        menu.setFilter("no such menu entry")
        proof.check(menu.visibleModel.count === 0 && menu.visibleRowsHeight >= menu.emptyRowHeight, "empty search has room for its message")
        menu.setFilter("palette")
        proof.check(menu.visibleModel.count === 1 && menu.visibleModel.get(0).itemId === "style.theme", "settings search")
        menu.setFilter("App 10")
        proof.check(menu.visibleModel.count === 1, "launch search")
        menu.activateIndex(0, false)
        proof.check(proof.recorded === "echo app10", "exact action dispatch")
        menu.startAt({output: proof.primaryScreen.name, x: 1270, y: 710})
        proof.stage = 2
      } else if (proof.stage === 2) {
        proof.check(menu.menuWindow.startPlacement.x + menu.cardWidth <= 1272, "right edge clamp")
        proof.check(menu.menuWindow.effectiveCardTop + menu.cardHeight <= 712, "bottom edge clamp")
        input.keyClick(Qt.Key_Down)
        proof.check(menu.selectedIndex === 1, "native down key")
        input.keyClick(Qt.Key_Up)
        proof.check(menu.selectedIndex === 0, "native up key")
        menu.select(-1)
        proof.check(menu.selectedIndex === 14, "keyboard wraps across headings")
        var top = menu.menuWindow.effectiveCardTop
        menu.activateIndex(14, false)
        proof.check(menu.activeMenu === "style.bar.position", "settings drilldown")
        proof.check(menu.menuWindow.effectiveCardTop === top, "stable navigation position")
        menu.goBack()
        proof.check(menu.startView, "back returns to combined view")
        Style.applyThemeStyle({fontBaseSize:20})
        proof.stage = 3
      } else if (proof.stage === 3) {
        proof.check(menu.baseRowHeight >= 40, "large text increases row targets")
        proof.check(menu.visibleRowsHeight < 15 * menu.baseRowHeight, "large text scrolls")
        menu.select(1)
        menu.startAt({output:proof.primaryScreen.name,x:30,y:43,edge:"top"})
        proof.check(menu.menuWindow.effectiveCardTop >= 43 && menu.menuWindow.effectiveCardTop + menu.cardHeight <= 720 - Style.gapsOut, "large menu stays below top bar")
        menu.startAt({output:proof.primaryScreen.name,x:30,y:677,edge:"bottom"})
        proof.check(menu.menuWindow.effectiveCardTop + menu.cardHeight <= 677, "large menu stays above bottom bar")
        menu.cancel()
        var generation = menu.startGeneration
        menu.finishPointer(0, '{"x":10,"y":10}', generation - 1)
        proof.check(!menu.opened, "stale pointer response cannot reopen")
        var second = Quickshell.screens.find(function(screen) { return screen.name === "HEADLESS-2" })
        proof.check(second && second.x < 0 && second.width === 1280, "scaled negative-origin output")
        menu.startPending = true
        menu.finishPointer(0, JSON.stringify({x:second.x + 40, y:second.y + 60}), menu.startGeneration)
        proof.check(menu.startScreen === second && menu.startAnchor.x === 40 && menu.startAnchor.y === 60, "pointer output and local coordinates")
        menu.cancel()
        Style.applyThemeStyle({fontBaseSize:12})
        menu.openExistingMenu("root")
        proof.check(!menu.startView, "root route remains usable")
        menu.cancel()
        menu.open(JSON.stringify({mode:"input",prompt:"Example"}))
        proof.check(!menu.startSession && menu.dmenuActive, "input resets Start placement and density")
        menu.cancel()
        proof.check(menu.providers["text-sizes"].actionFor("21") === "", "size upper bound")
        proof.check(menu.providers["text-sizes"].actionFor("12; bad") === "", "size rejects shell text")
        menu.startAt({output:proof.primaryScreen.name,x:30,y:26})
        menu.setActiveMenu("style.text-size", true, false)
        proof.stage = 4
      } else if (proof.stage === 4) {
        if (menu.visibleModel.count !== 13) return
        proof.check(menu.visibleModel.get(0).label === "9 px", "size enumeration minimum")
        proof.check(menu.visibleModel.get(11).label === "20 px", "size enumeration maximum")
        proof.check(menu.visibleModel.get(12).label === "Reset to default (12 px)", "reset option")
        menu.mergeProviderRows("16 px\t16\t16", "style.text-size", "text-sizes")
        proof.check(menu.visibleModel.get(0).icon === "✓", "current size marker")
        menu.activateIndex(0, false)
        proof.check(proof.recorded.indexOf("tam-display-text-size '16'") === 0, "size dispatch")
        facade.point = {x: -1240, y: 60}
        menu.openRoute("start")
        proof.stage = 5
      } else if (proof.stage === 5) {
        if (!menu.opened || menu.startPending) return
        proof.check(menu.startScreen.name === "HEADLESS-2" && menu.startAnchor.x === 40, "global route through compositor facade")
        menu.toggle("start")
        proof.check(!menu.opened, "global toggle dismisses once")
        console.log("START_MENU_OK")
        Qt.quit()
      }
    }
  }
  Timer { interval: 10000; running: true; onTriggered: { console.error("START_FAILED timeout stage " + proof.stage); Qt.exit(1) } }
}
