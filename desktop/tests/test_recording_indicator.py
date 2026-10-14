"""Actual QML clicks must launch typed recording actions with exact argv."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SHELL = Path(__file__).resolve().parents[1]/'shell'


class RecordingIndicator(unittest.TestCase):
    def test_idle_click_opens_recording_menu_and_active_click_stops_owned_recorder(self):
        provider=os.environ.get('TAMLINUX_TEST_QUICKSHELL') or shutil.which('quickshell')
        if not provider:
            self.skipTest('Quickshell unavailable for actual QML signal verification')
        with tempfile.TemporaryDirectory(prefix='tamlinux-recording-indicator-') as temporary:
            root=Path(temporary);binary=root/'bin';binary.mkdir();log=root/'argv.jsonl'
            for name in ['tam-menu','tam-capture-screenrecording']:
                helper=binary/name
                helper.write_text('#!/usr/bin/python3\nimport json,sys\n'
                    +f'with open({str(log)!r},"a") as f:f.write(json.dumps(sys.argv)+"\\n")\n'
                    +'sys.exit(1 if sys.argv[1:]==["--status"] else 0)\n')
                helper.chmod(0o700)
            qml='''import QtQuick
import Quickshell
import HOST as Host
import INDICATORS as Indicators
Item {
  Host.BarApi { id: api }
  Indicators.ScreenRecording { id: recording; bar: api }
  Timer { interval: 100; running: true; repeat: false
    onTriggered: { recording.recording = false; recording.pressed(Qt.LeftButton) } }
  Timer { interval: 500; running: true; repeat: false
    onTriggered: { recording.recording = true; recording.pressed(Qt.LeftButton) } }
  Timer { interval: 1000; running: true; repeat: false
    onTriggered: { api.screenRecording("invalid"); Qt.quit() } }
}
'''.replace('HOST',json.dumps((SHELL/'host').as_uri())).replace('INDICATORS',json.dumps((SHELL/'bar/indicators').as_uri()))
            (root/'shell.qml').write_text(qml)
            runtime=root/'runtime';runtime.mkdir(mode=0o700)
            env={'HOME':str(root),'PATH':str(binary)+':/usr/bin:/bin',
                 'XDG_RUNTIME_DIR':str(runtime),'XDG_CONFIG_HOME':str(root/'config'),
                 'XDG_STATE_HOME':str(root/'state'),'XDG_CACHE_HOME':str(root/'cache'),
                 'QT_QPA_PLATFORM':'offscreen','QT_QUICK_BACKEND':'software',
                 'QML_IMPORT_PATH':str(SHELL/'modules'),'TAMLINUX_HOST_ACTIONS':'1',
                 'TAMLINUX_BIN':str(binary),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/nonexistent'}
            result=subprocess.run([provider,'--no-color','-p',str(root/'shell.qml')],env=env,
                                  capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(log.exists(),result.stdout+result.stderr)
            calls=[json.loads(line) for line in log.read_text().splitlines()]
            actions=[call for call in calls if call[1:]!=['--status']]
            self.assertEqual(actions,[[str(binary/'tam-menu'),'toggle','trigger.capture.screenrecord'],
                                     [str(binary/'tam-capture-screenrecording'),'--stop-recording']])
