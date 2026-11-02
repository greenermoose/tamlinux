"""Render real keyboard keycaps without connecting to the desktop or reading input."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

DESKTOP = Path(__file__).resolve().parents[1]
PLUGIN = DESKTOP / "plugins/fred.keyboard"
_loader = importlib.machinery.SourceFileLoader("keyboard_widget_proof", str(DESKTOP / "widget-proof"))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
proof = importlib.util.module_from_spec(_spec)
_loader.exec_module(proof)
QUICKSHELL = proof.find_quickshell(None)
MARKER = "KEYBOARD_RENDER "

QML = '''import QtQuick
import Quickshell
import Quickshell.Io
import "plugin" as Plugin
import "plugin/Bindings.js" as Bindings

ShellRoot {
  FileView {
    path: LAYOUT_PATH
    onLoaded: board.layout = JSON.parse(text())
  }
  Window {
    visible: true
    width: 1000
    height: 300
    Plugin.KeyboardView {
      id: board
      unit: Math.min(38, 1000 / Math.max(1, boardUnits))
    }
  }
  Timer {
    interval: 100
    running: true
    onTriggered: {
      var keys = []
      function collect(item) {
        if (item.cell !== undefined) keys.push(item)
        for (var i = 0; i < item.children.length; i++) collect(item.children[i])
      }
      collect(board)
      var k = keys.filter(function(item) { return item.cell.code === 37 })[0]
      if (!k) { console.log("KEYBOARD_RENDER " + JSON.stringify({error: "K key missing"})); Qt.quit(); return }
      var idle = String(k.color)
      var report = {
        rows: board.placedRows.length, width: board.width, height: board.height,
        keycaps: keys.filter(function(item) { return !item.isLed }).length,
        sized: keys.every(function(item) { return item.width > 0 && item.height > 0 }),
        gutters: keys.every(function(item) {
          return Math.abs(item.width - (item.parent.width - board.gutter)) < 0.01 &&
                 Math.abs(item.height - (item.parent.height - board.gutter)) < 0.01
        }),
        initiallyUp: !k.down
      }
      var code = Bindings.evdevFromNative(45) // K: evdev 37 + XKB offset 8
      var pressed = {}; pressed[code] = true; board.pressed = pressed
      Qt.callLater(function() {
        report.pressed = k.down && String(k.color) !== idle
        report.onlyK = keys.filter(function(item) { return item.down }).length === 1
        board.pressed = ({})
        Qt.callLater(function() {
          report.released = !k.down && String(k.color) === idle
          if (board.layout.id !== "hp-15-f233wm-us") {
            console.log("KEYBOARD_RENDER " + JSON.stringify(report)); Qt.quit(); return
          }
          function cap(id) { return keys.filter(function(item) { return item.cell.id === id })[0] }
          var up = cap("UP"), down = cap("DOWN"), f6 = cap("F6")
          var upPos = up.mapToItem(board, 0, 0), downPos = down.mapToItem(board, 0, 0)
          report.splitArrows = Math.abs(upPos.x - downPos.x) < 0.01 &&
            upPos.y + up.height < downPos.y && up.height < cap("LEFT").height
          report.shortFunctionRow = f6.height < cap("A").height
          board.pressed = ({103: true})
          Qt.callLater(function() {
            report.onlyUp = up.down && !down.down && keys.filter(function(item) { return item.down }).length === 1
            board.pressed = ({108: true})
            Qt.callLater(function() {
              report.onlyDown = down.down && !up.down && keys.filter(function(item) { return item.down }).length === 1
              board.pressed = ({113: true})
              Qt.callLater(function() {
                report.mediaAlias = f6.down && keys.filter(function(item) { return item.down }).length === 1
                board.pressed = ({})
                Qt.callLater(function() {
                  report.mediaReleased = !f6.down
                  console.log("KEYBOARD_RENDER " + JSON.stringify(report)); Qt.quit()
                })
              })
            })
          })
        })
      })
    }
  }
}
'''


@unittest.skipUnless(QUICKSHELL and Path(QUICKSHELL).exists(), "no Quickshell available")
class KeyboardRender(unittest.TestCase):
    def render(self, filename):
        with tempfile.TemporaryDirectory(prefix="keyboard-render-") as temp:
            root = Path(temp)
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            (root / "plugin").symlink_to(PLUGIN, target_is_directory=True)
            qml = QML.replace("LAYOUT_PATH", json.dumps(str(PLUGIN / "layouts" / filename)))
            (root / "shell.qml").write_text(qml)
            result = subprocess.run(
                [QUICKSHELL, "-p", str(root / "shell.qml")],
                env=proof.environment(runtime, []), capture_output=True, text=True, timeout=15,
            )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertEqual(proof.problems(output), [], output)
        for line in output.splitlines():
            if MARKER in line:
                return json.loads(line.split(MARKER, 1)[1])
        self.fail(output)

    def test_bundled_boards_render_and_highlight_only_the_pressed_key(self):
        registry = json.loads((PLUGIN / "layouts/index.json").read_text())
        files = [registry["standIn"]] + [entry["file"] for entry in registry["layouts"]]
        for filename in files:
            with self.subTest(layout=filename):
                layout = json.loads((PLUGIN / "layouts" / filename).read_text())
                expected = sum(not cell.get("led") for row in layout["rows"] for cell in row)
                report = self.render(filename)
                self.assertNotIn("error", report, report)
                self.assertEqual(report["keycaps"], expected, report)
                self.assertEqual(report["rows"], 6, report)
                self.assertGreater(report["width"], 0, report)
                self.assertLessEqual(report["width"], 1000, report)
                self.assertGreater(report["height"], 0, report)
                for flag in ("sized", "gutters", "initiallyUp", "pressed", "onlyK", "released"):
                    self.assertTrue(report[flag], (flag, report))
                if layout["id"] == "hp-15-f233wm-us":
                    for flag in ("splitArrows", "shortFunctionRow", "onlyUp", "onlyDown", "mediaAlias", "mediaReleased"):
                        self.assertTrue(report[flag], (flag, report))


if __name__ == "__main__":
    unittest.main()
