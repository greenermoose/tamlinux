"""An active registered trial routes IPC; stale records use the package."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'tam-shell'

class LiveRouting(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.state=self.root/'state/tamlinux/development';self.state.mkdir(parents=True)
        self.packaged=self.root/'data/tamlinux/shell';self.packaged.mkdir(parents=True);(self.packaged/'shell.qml').touch()
        self.live=self.state/'builds/shell'/('a'*64)/'source/desktop/shell'
        self.live.mkdir(parents=True);(self.live/'shell.qml').touch()
        self.args=self.root/'ipc-args'
        ipc=self.root/'qs';ipc.write_text('#!'+shutil.which('sh')+'\nprintf "%s\\n" "$@" > "$IPC_ARGS"\necho pong\n');ipc.chmod(0o755)
        self.env=dict(os.environ,HOME=str(self.root),XDG_STATE_HOME=str(self.root/'state'),
                      XDG_DATA_HOME=str(self.root/'data'),TAMLINUX_QUICKSHELL_IPC=str(ipc),
                      WAYLAND_DISPLAY='fixture',IPC_ARGS=str(self.args))
        self.env.pop('TAMLINUX_SHELL_DIR',None)
        fields=Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()
        self.record={'schema':1,'shell':str(self.live),'pid':os.getpid(),'processId':fields[19],
                     'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}

    def invoke(self):
        result=subprocess.run([str(SCRIPT),'reminders','ping'],env=self.env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        return self.args.read_text().splitlines()

    def test_registered_live_trial_and_explicit_selection(self):
        (self.state/'live.json').write_text(json.dumps(self.record))
        self.assertIn(str(self.live),self.invoke())
        self.env['TAMLINUX_SHELL_DIR']=str(self.packaged)
        self.assertIn(str(self.packaged),self.invoke())

    def test_stale_process_other_boot_and_escape_use_packaged_endpoint(self):
        for change in ({'processId':'0'},{'boot':'other-boot'},{'shell':str(self.root)}):
            (self.state/'live.json').write_text(json.dumps(dict(self.record,**change)))
            self.assertIn(str(self.packaged),self.invoke())

    def test_malformed_record_uses_packaged_endpoint(self):
        (self.state/'live.json').write_text('broken')
        self.assertIn(str(self.packaged),self.invoke())
