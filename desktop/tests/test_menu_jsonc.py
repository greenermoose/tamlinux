"""Exercise the actual menu parser, bounded reader, and reactive QML source."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import io
import tarfile
import time
import socket as sockets
import tempfile
import unittest

DESKTOP = Path(__file__).resolve().parents[1]
MENU = DESKTOP / "shell/services/menu"
spec = importlib.util.spec_from_file_location("menu_reader", MENU / "read-menu.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class ParserTests(unittest.TestCase):
    def evaluate(self, code):
        result = subprocess.run(["node", "-e", "const assert=require('assert'); const M=require(process.argv[1]);" + code,
                                 str(MENU / "MenuModel.js")], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_quoted_actions_and_jsonc_comments(self):
        action = 'printf "%s" "a,} // literal /* text */,] \\\" end"'
        source = '// heading\n' + json.dumps({"run": {"action": action, "aliases": ["test"]}})
        source = source[:-1] + ', /* trailing */ } // end'
        self.evaluate("const rows=M.parseMenuJsonc(" + json.dumps(source) + ");assert.equal(rows[0].action," + json.dumps(action) + ");")

    def test_malformed_documents_and_fields_rejected(self):
        sources = ['', '[]', 'null', '{,}', '{"x":{,}}', '{"x":{}} /* unfinished',
                   '{"x":{"label":1}}', '{"x":{"aliases":[1]}}', '{"x":{"action":"a","target":"root"}}',
                   '{"__proto__":{"action":"a"}}', '{"x":{"unknown":"a"}}',
                   '{"items":[]}', '{"x":{"label":"a"} "y":{}}', '{"x":{"label":1/* c */2}}']
        for source in sources:
            with self.subTest(source=source):
                self.evaluate("assert.throws(()=>M.parseMenuJsonc(" + json.dumps(source) + "));")

    def test_size_depth_count_alias_and_field_bounds(self):
        self.evaluate("""
assert.throws(()=>M.parseMenuJsonc(' '.repeat(262145)));
assert.throws(()=>M.stripJsonc('['.repeat(33)+']'.repeat(33)));
const rows={}; for(let i=0;i<2049;i++) rows['r'+i]={};
assert.throws(()=>M.parseMenuJsonc(JSON.stringify(rows)));
assert.throws(()=>M.parseMenuJsonc(JSON.stringify({x:{aliases:Array(33).fill('a')}})));
assert.throws(()=>M.parseMenuJsonc(JSON.stringify({x:{action:'a'.repeat(16385)}})));
assert.equal(M.parseMenuJsonc('{}').length,0);
""")

    def test_invalid_merged_routes_rejected(self):
        self.evaluate("""
for (const rows of [{x:{parent:'missing'}}, {x:{target:'missing'}},
                    {x:{parent:'y'},y:{parent:'x'}}, {x:{target:'x'}}])
  assert.throws(()=>M.mergeMenuSources(M.parseMenuJsonc(JSON.stringify(rows)),[]));
const defaults=M.parseMenuJsonc('{"x":{"label":"X","aliases":["old"]},"x.run":{"action":"echo ok"}}');
const model=M.mergeMenuSources(defaults,[]);
assert.equal(M.resolveRoute(model.items,model.itemOrder,'old'),'x');
assert.equal(M.matchesQuery(model.items['x.run'], 'run', true),true);
""")

    def test_product_defaults_are_valid(self):
        self.evaluate("const fs=require('fs'); const rows=M.parseMenuJsonc(fs.readFileSync(" +
                      json.dumps(str(DESKTOP / "menu/default.jsonc")) + ", 'utf8')); const model=M.mergeMenuSources(rows,[]); assert(model.items.root); assert(model.items['system.shutdown']);")


class ReaderTests(unittest.TestCase):
    def test_regular_file_symlink_and_byte_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "menu"
            path.write_text('{"unicode":"é"}')
            link = Path(directory) / "link"
            link.symlink_to(path)
            self.assertEqual(reader.read_menu(link), path.read_text())
            path.write_bytes(b" " * reader.LIMIT)
            self.assertEqual(len(reader.read_menu(path)), reader.LIMIT)
            path.write_bytes(b" " * (reader.LIMIT + 1))
            with self.assertRaises(ValueError): reader.read_menu(path)

    def test_invalid_utf8_and_nonregular_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "menu"
            path.write_bytes(b"\xff")
            with self.assertRaises(ValueError): reader.read_menu(path)
            fifo = Path(directory) / "fifo"
            os.mkfifo(fifo)
            with self.assertRaises(ValueError): reader.read_menu(fifo)
            with self.assertRaises(ValueError): reader.read_menu(directory)


class QmlSourceTests(unittest.TestCase):
    def test_service_retains_last_valid_merged_menu_and_recovers(self):
        with tempfile.TemporaryDirectory(prefix="tm-") as directory:
            root = Path(directory)
            # Freeze unrelated shell dependencies at the committed revision;
            # only the owned menu candidate is overlaid into this isolated proof.
            archive = subprocess.check_output(["git", "archive", "HEAD", "desktop/shell"], cwd=DESKTOP.parent)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
                tree.extractall(root, filter="data")
            shell = root / "desktop/shell"
            shutil.copytree(MENU, shell / "services/menu", dirs_exist_ok=True)
            defaults = root / "default.jsonc"
            defaults.write_text('{"tools":{"label":"Tools"},"tools.run":{"action":"echo safe"}}')
            extension = root / "extension.jsonc"
            extension.write_text('{"quicklaunch":{"label":"Quick Launch","aliases":["quick"]},"quicklaunch.reboot":{"action":"tam-system-reboot"}}')
            fixture = r'''
import QtQuick
import Quickshell
import Quickshell.Io
import "services/menu" as Menu
ShellRoot {
  id: root
  property int stage: 0
  property string recorded: ""
  function check(ok, message) { if (!ok) { console.error("MENU_FAILED "+message); Qt.exit(1) } }
  Menu.Service {
    id: service
    defaultMenuPath: __DEFAULT__
    userMenuPath: __EXTENSION__
    function runAction(command) { root.recorded = command }
  }
  FileView { id: writer; path: service.userMenuPath; preload: false }
  Timer {
    interval: 150; repeat: true; running: true
    onTriggered: {
      if (!service.rowsLoaded) return
      var status = JSON.parse(service.modelStatus())
      if (root.stage === 0) {
        root.check(status.rows === 5 && service.resolveRoute("quick") === "quicklaunch", "initial routes");
        service.openRoute("quicklaunch.reboot");
        root.check(root.recorded === "tam-system-reboot", "safe power dispatch");
        writer.setText('{"bad":{"parent":"missing"}}'); root.stage = 1;
      } else if (root.stage === 1 && status.error) {
        root.check(status.rows === 5 && service.items["quicklaunch.reboot"].action === "tam-system-reboot", "merged retention");
        writer.setText('{"quicklaunch":{"label":"Quick Launch","aliases":["quick"]},"quicklaunch.reboot":{"action":"echo changed"}}'); root.stage = 2;
      } else if (root.stage === 2 && !status.error && service.items["quicklaunch.reboot"].action === "echo changed") {
        writer.setText('{"quicklaunch":'); root.stage = 3;
      } else if (root.stage === 3 && status.error) {
        root.check(status.rows === 5 && service.items["quicklaunch.reboot"].action === "echo changed", "parse retention");
        console.log("MENU_MODEL_OK"); Qt.quit();
      }
    }
  }
  Timer { interval: 7000; running: true; onTriggered: { console.error("MENU_FAILED timeout stage "+root.stage); Qt.exit(1) } }
}
'''.replace('__DEFAULT__', json.dumps(str(defaults))).replace('__EXTENSION__', json.dumps(str(extension)))
            (shell / "proof-menu.qml").write_text(fixture)
            runtime = root / "r"
            runtime.mkdir(mode=0o700)
            # Detect sandbox socket restrictions before launching wlroots;
            # its failed-start cleanup can abort and raise a crash notification.
            probe = runtime / "probe.sock"
            try:
                with sockets.socket(sockets.AF_UNIX) as sock:
                    sock.bind(str(probe))
            except PermissionError:
                self.skipTest("headless Wayland socket unavailable; run outside the sandbox")
            probe.unlink()
            env = {"PATH": "/usr/bin", "HOME": directory, "XDG_CONFIG_HOME": directory,
                   "XDG_CACHE_HOME": directory, "XDG_RUNTIME_DIR": directory,
                   "QML_IMPORT_PATH": str(shell / "modules"), "QT_QPA_PLATFORM": "offscreen", "QSG_RENDER_LOOP": "basic"}
            env["XDG_RUNTIME_DIR"] = str(runtime)
            config = root / "sway.conf"
            config.write_text('output HEADLESS-1 resolution 1280x720\n')
            with (root / "sway.log").open('w') as sway_log:
                sway = subprocess.Popen(["/usr/bin/sway", "-c", str(config)],
                                        env=dict(env, WLR_BACKENDS="headless", WLR_LIBINPUT_NO_DEVICES="1", WLR_RENDERER="pixman"),
                                        stdout=sway_log, stderr=subprocess.STDOUT)
                try:
                    deadline = time.monotonic() + 5
                    socket = None
                    while time.monotonic() < deadline and sway.poll() is None:
                        socket = next((p for p in runtime.glob("wayland-*") if not p.name.endswith('.lock')), None)
                        if socket: break
                        time.sleep(0.05)
                    self.assertIsNotNone(socket, (root / "sway.log").read_text())
                    env.update(WAYLAND_DISPLAY=socket.name, QT_QPA_PLATFORM="wayland")
                    result = subprocess.run(["/usr/bin/quickshell", "--no-color", "-p", str(shell / "proof-menu.qml")],
                                            env=env, capture_output=True, text=True, timeout=10)
                finally:
                    sway.terminate()
                    sway.wait(timeout=5)
        log = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, log)
        self.assertIn("MENU_MODEL_OK", log)
        self.assertNotIn("MENU_FAILED", log)

    def test_reactive_last_valid_source_and_missing_optional(self):
        with tempfile.TemporaryDirectory(prefix="tam-menu-") as directory:
            root = Path(directory)
            for name in ("MenuSource.qml", "MenuModel.js", "read-menu.py"):
                shutil.copyfile(MENU / name, root / name)
            path = root / "data.jsonc"
            path.write_text('{"x":{"label":"First"}}')
            qml = r'''
import QtQuick
import Quickshell
import Quickshell.Io
ShellRoot {
  id: root
  property int stage: 0
  function check(ok, message) { if (!ok) { console.error("MENU_FAILED "+message); Qt.exit(1) } }
  MenuSource { id: source; path: __PATH__ }
  MenuSource { id: optional; path: __MISSING__; optional: true }
  FileView { id: writer; path: source.path; preload: false }
  Timer {
    interval: 150; repeat: true; running: true
    onTriggered: {
      if (!source.ready || !optional.ready) return
      if (root.stage === 0) {
        root.check(source.items[0].label === "First", "initial");
        root.check(optional.valid && optional.items.length === 0, "missing optional");
        writer.setText('{"x":'); root.stage = 1;
      } else if (root.stage === 1 && source.error) {
        root.check(source.items[0].label === "First", "malformed retention");
        writer.setText(" ".repeat(262145)); root.stage = 2;
      } else if (root.stage === 2 && source.error.indexOf("read failed") >= 0) {
        root.check(source.items[0].label === "First", "oversized retention");
        writer.setText('{"x":{"label":"Second"}}'); root.stage = 3;
      } else if (root.stage === 3 && !source.error && source.items[0].label === "Second") {
        source.path = __MISSING__; root.stage = 4;
      } else if (root.stage === 4 && source.error) {
        root.check(source.items[0].label === "Second", "read failure retention");
        console.log("MENU_SOURCE_OK"); Qt.quit();
      }
    }
  }
  Timer { interval: 7000; running: true; onTriggered: { console.error("MENU_FAILED timeout stage "+root.stage); Qt.exit(1) } }
}
'''.replace('__PATH__', json.dumps(str(path))).replace('__MISSING__', json.dumps(str(root / "missing.jsonc")))
            (root / "shell.qml").write_text(qml)
            env = {"PATH": "/usr/bin", "HOME": directory, "XDG_CONFIG_HOME": directory,
                   "XDG_CACHE_HOME": directory, "XDG_RUNTIME_DIR": directory,
                   "QT_QPA_PLATFORM": "offscreen", "QSG_RENDER_LOOP": "basic"}
            result = subprocess.run(["/usr/bin/quickshell", "--no-color", "-p", str(root)],
                                    env=env, capture_output=True, text=True, timeout=10)
        log = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, log)
        self.assertIn("MENU_SOURCE_OK", log)
        self.assertNotIn("MENU_FAILED", log)


if __name__ == "__main__":
    unittest.main()
