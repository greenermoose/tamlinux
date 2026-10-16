"""Only the shell owns panel IPC; exercise its actual JavaScript routes."""
import json
from pathlib import Path
import re
import subprocess
import unittest
from test_launch_environment import block_end

DESKTOP = Path(__file__).resolve().parents[1]


class PanelRouterTests(unittest.TestCase):
    def test_replicated_components_register_no_ipc_targets(self):
        paths = list((DESKTOP / "plugins").rglob("*.qml"))
        paths += list((DESKTOP / "shell/panels").rglob("*.qml"))
        paths += list((DESKTOP / "shell/bar").rglob("*.qml"))
        paths += [DESKTOP / "shell/modules/Tam/Ui/Panel.qml", DESKTOP / "shell/host/PanelHost.qml"]
        for path in paths:
            self.assertNotRegex(path.read_text(), r"\bIpcHandler\s*\{", str(path))

    def test_call_reaches_focused_widget_and_respects_existing_panel_selection(self):
        source = (DESKTOP / "shell/shell.qml").read_text()
        start = source.index("  function callPanel(")
        opening = source.index("{", start)
        function = source[start:block_end(source, opening) + 1]
        script = '''
const events = [];
const first = { refresh() { events.push("first"); } };
const focused = { refresh() { events.push("focused"); } };
const panel = { open() { events.push("panel"); } };
let chosen = null;
const liveWidgets = [ {id:"fred.workspaces",key:"A#0",widget:first},
 {id:"fred.workspaces",key:"B#0",widget:focused}, {id:"fred.workspaces",key:"C#0",widget:first} ];
const moduleWidgets = () => [first,focused,first];
const focusedScreenName = () => "B";
const knownRoute = () => true;
const findPanelWidget = () => chosen;
const overlay = () => null;
const evidence = () => {};
''' + function + '''
const replies = [callPanel("fred.workspaces", "refresh")];
chosen = panel;
replies.push(callPanel("fred.clock", "open"));
replies.push(callPanel("fred.clock", "missing"));
replies.push(callPanel("fred.clock", "__proto__"));
console.log(JSON.stringify({events,replies}));
'''
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10, check=True)
        self.assertEqual(json.loads(result.stdout), {"events": ["focused", "panel"],
                                                    "replies": ["ok", "ok", "unknown", "unknown"]})
