"""Calendar argument and detached journal launcher behavior without session access."""
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT/'desktop/plugins/fred.clock/Model.js'
BIN = Path(os.environ.get('TAM_JOURNAL_LAUNCHER_TEST_BIN', ROOT/'commands/tam-launch-journal/build/tam-launch-journal'))


class JournalIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # check-all runs desktop tests before per-command make checks. Build
        # this one launcher when testing a fresh checkout, using the normal
        # LIBTAM_PREFIX/pkg-config dependency contract.
        if 'TAM_JOURNAL_LAUNCHER_TEST_BIN' not in os.environ and not BIN.is_file():
            args=['make','-C',str(ROOT/'commands/tam-launch-journal'),'all']
            for key in ('LIBTAM_PREFIX','LIBTAM_LIBS'):
                if key in os.environ: args.append(key+'='+os.environ[key])
            result=subprocess.run(args,capture_output=True,text=True,timeout=60)
            if result.returncode:
                raise RuntimeError('Cannot build journal launcher (libtam 0.6 required):\n'+result.stdout+result.stderr)

    def test_actual_calendar_buttons_route_selected_date_offscreen(self):
        with tempfile.TemporaryDirectory(prefix='journal-qml-') as temp:
            root=Path(temp); modules=root/'modules/Tam'; modules.mkdir(parents=True)
            source=ROOT/'desktop/shell/modules/Tam'
            for directory in source.iterdir():
                if directory.name!='Ui': (modules/directory.name).symlink_to(directory)
            ui=modules/'Ui'; ui.mkdir()
            for path in (source/'Ui').iterdir():
                if path.name!='KeyboardPanel.qml': (ui/path.name).symlink_to(path)
            shutil.copyfile(ROOT/'desktop/fixtures/journal/KeyboardPanel.qml',ui/'KeyboardPanel.qml')
            (root/'plugin').symlink_to(ROOT/'desktop/plugins/fred.clock')
            (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import "plugin" as Plugin
ShellRoot {
  property var calls: []
  QtObject { id: host; function openJournal(day, quick) { calls.push([day,quick]) } }
  Plugin.Panel { id: calendar; hostWidget: host }
  function visit(item) {
    if ((item.text === "Quick note for this date" || item.text === "Open journal for this date") && typeof item.clicked === "function") item.clicked()
    var children=item.children || []
    for(var i=0;i<children.length;i++) visit(children[i])
  }
  Timer { interval: 100; running: true; onTriggered: {
    calendar.selectedDateKey="2026-11-03"
    visit(calendar)
    console.log("JOURNAL_UI " + JSON.stringify(calls))
    Qt.quit()
  } }
}
''')
            runtime=root/'runtime';runtime.mkdir(mode=0o700)
            env={k:v for k,v in os.environ.items() if not k.startswith(('QT_','QML_','GDK_')) and k not in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS')}
            env.update(QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',QML_IMPORT_PATH=str(root/'modules'),XDG_RUNTIME_DIR=str(runtime),TAMLINUX_CLOCK_OFFLINE='1',HOME=str(root))
            try:
                result=subprocess.run(['quickshell','-p',str(root)],env=env,capture_output=True,text=True,timeout=10)
            except subprocess.TimeoutExpired as error:
                self.fail(((error.stdout or b'')+(error.stderr or b'')).decode(errors='replace')[-4500:])
            output=result.stdout+result.stderr
            marker=next((line.split('JOURNAL_UI ',1)[1] for line in output.splitlines() if 'JOURNAL_UI ' in line),None)
            self.assertIsNotNone(marker,output[-3500:])
            self.assertEqual(json.loads(marker),[['2026-11-03',True],['2026-11-03',False]])

    def test_calendar_selected_date_is_typed_and_validated(self):
        script = '''const assert=require('assert'); const m=require(process.argv[1]);
assert.deepStrictEqual(m.journalArgs('2026-11-03',true),['add','--date','2026-11-03']);
assert.deepStrictEqual(m.journalArgs('2024-02-29',false),['--date','2024-02-29']);
for (const day of ['2026-02-29','2026-13-01','0000-01-01','2026-11-11; touch x','../x'])
 assert.deepStrictEqual(m.journalArgs(day,true),[]);
'''
        subprocess.run(['node','-e',script,str(MODEL)],check=True,timeout=10)

    def test_launcher_preserves_argv_and_editor_lifetime(self):
        with tempfile.TemporaryDirectory(prefix='journal-launch-') as temp:
            root=Path(temp); bindir=root/'commands with spaces'; bindir.mkdir()
            journal=bindir/'tam-journal'; journal.write_text('#!/bin/sh\nexit 0\n');journal.chmod(0o755)
            launcher=bindir/'tam-launch-tui'
            launcher.write_text('''#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
Path(os.environ['CAPTURE']).write_text(json.dumps({'args':sys.argv[1:],'pid':os.getpid(),'session':os.getsid(0)}))
time.sleep(20)
''');launcher.chmod(0o755)
            record=root/'record'
            env={'PATH':'/usr/bin','HOME':str(root),'TAMLINUX_BIN':str(bindir),'CAPTURE':str(record)}
            start=time.monotonic()
            result=subprocess.run([str(BIN),'add','--date','2026-11-03'],env=env,capture_output=True,text=True,timeout=4)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertLess(time.monotonic()-start,4)
            end=time.monotonic()+4
            while not record.exists() and time.monotonic()<end:time.sleep(.01)
            self.assertTrue(record.exists())
            data=json.loads(record.read_text())
            try:
                self.assertEqual(data['args'],['--app-id=org.tamlinux.journal',str(journal),'add','--date','2026-11-03'])
                self.assertEqual(data['pid'],data['session'])
                os.kill(data['pid'],0)
            finally:os.kill(data['pid'],signal.SIGTERM)

    def test_missing_dependency_and_malicious_arguments_fail(self):
        with tempfile.TemporaryDirectory() as home:
            env={'HOME':home,'PATH':'/usr/bin','TAMLINUX_BIN':home}
            result=subprocess.run([str(BIN),'add'],env=env,capture_output=True,text=True,timeout=3)
            self.assertEqual(result.returncode,1)
            for args in [('add','--date','2026-11-11;echo x'),('unknown',),('add','add')]:
                result=subprocess.run([str(BIN),*args],env=env,capture_output=True,text=True,timeout=3)
                self.assertEqual(result.returncode,2)

    def test_existing_bar_slots_and_controls_are_preserved(self):
        layout=json.loads((ROOT/'desktop/shell/bar/default-layout.json').read_text())
        self.assertEqual(layout['centerAnchor'],'fred.clock')
        self.assertEqual([x['id'] for x in layout['layout']['center']],['tamlinux.indicators','fred.tamversion','fred.clock','tamlinux.keyboard-layout','fred.weather','fred.tides'])
        self.assertFalse(any('journal' in x['id'] for entries in layout['layout'].values() for x in entries))
        bindings=(ROOT/'desktop/session/hypr/tamlinux/bindings/utilities.lua').read_text()
        for chord,label in [('META + N','Dismiss last notification'),('META + CTRL + J','Toggle nightlight'),('META + SHIFT + J','Quick note')]:
            self.assertIn('"'+chord+'", "'+label+'"',bindings)


if __name__ == '__main__':unittest.main()
