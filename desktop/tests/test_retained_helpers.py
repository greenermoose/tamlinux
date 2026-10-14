"""Exercise real retained helpers at recorded IPC and isolated state boundaries."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASH = shutil.which('bash')


class RetainedHelpers(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.bin = self.home / 'bin'
        self.bin.mkdir()
        self.log = self.home / 'calls.jsonl'
        self.env = {'HOME': str(self.home), 'XDG_STATE_HOME': str(self.home / 'state'),
                    'XDG_CONFIG_HOME': str(self.home / 'config'), 'PATH': str(self.bin),
                    'CALL_LOG': str(self.log), 'ACTIVE': json.dumps({'address': '0xa',
                        'pinned': False, 'size': [900, 600], 'class': 'test/app', 'workspace': {'id': 1}})}
        for name in ['jq', 'mkdir', 'mktemp', 'mv', 'rm', 'dirname', 'readlink', 'python3', 'awk', 'cat']:
            executable = shutil.which(name)
            if not executable:
                self.skipTest(name + ' unavailable')
            (self.bin / name).symlink_to(executable)
        for name in ['hyprctl', 'wpctl', 'tam-osd', 'tam-shell', 'tam-brightness-keyboard-mute',
                     'tam-notification-send', 'tam-hw-touchpad']:
            target = self.bin / name
            target.write_text('#!' + shutil.which('python3') + '\n' + r'''
import json,os,sys
name=sys.argv[0].split('/')[-1]
with open(os.environ['CALL_LOG'],'a') as f:f.write(json.dumps([name,*sys.argv[1:]])+'\n')
if name=='wpctl':sys.exit(7)
if name=='tam-hw-touchpad':print('touchpad');sys.exit(0)
if name=='hyprctl':
 if sys.argv[1]=='activewindow':print(os.environ['ACTIVE'])
 elif sys.argv[1]=='activeworkspace':print('{"id": 1, "tiledLayout": "dwindle"}')
 elif sys.argv[1]=='monitors':print(os.environ.get('MONITORS','[]'))
 elif sys.argv[1] in ('dispatch','eval'):sys.exit(int(os.environ.get('IPC_EXIT','0')))
'''.lstrip())
            target.chmod(0o755)
        (self.bin / 'tam-settings-preserve').symlink_to(ROOT / 'commands/tam-settings-preserve/tam-settings-preserve')

    def run_helper(self, name, *arguments):
        return subprocess.run([BASH, str(ROOT / 'commands' / name / name), *arguments],
                              env=self.env, text=True, capture_output=True, timeout=5)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def preservation_failure(self):
        path = self.bin / 'tam-settings-preserve'
        path.unlink()
        path.write_text('#!' + BASH + '\nexit 19\n')
        path.chmod(0o755)

    def test_failed_microphone_mutation_sends_no_success_osd_or_led_change(self):
        result = self.run_helper('tam-audio-input-mute')
        self.assertEqual(result.returncode, 7)
        self.assertEqual(self.calls(), [['wpctl', 'set-mute', '@DEFAULT_AUDIO_SOURCE@', 'toggle']])

    def test_malformed_window_geometry_is_rejected_before_native_ipc(self):
        for arguments in [('1); os.execute("bad")',), ('0',), ('100', '100', 'x', '4')]:
            with self.subTest(arguments=arguments):
                self.assertEqual(self.run_helper('tam-hyprland-window-pop', *arguments).returncode, 2)
                self.assertEqual(self.calls(), [])

    def test_invalid_native_window_identity_cannot_become_a_lua_expression(self):
        self.env['ACTIVE'] = json.dumps({'address': 'x"}); evil() --', 'pinned': False})
        self.assertNotEqual(self.run_helper('tam-hyprland-window-transparency-toggle').returncode, 0)
        self.assertEqual(self.calls(), [['hyprctl', 'activewindow', '-j']])

    def test_workspace_layout_preserves_previous_bytes_before_atomic_replacement(self):
        target = self.home / 'state/tamlinux/workspace-layouts/1.lua'
        target.parent.mkdir(parents=True)
        target.write_text('personal prior layout\n')
        result = self.run_helper('tam-hyprland-workspace-layout-toggle')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('layout = "scrolling"', target.read_text())
        snapshots = list((self.home / 'state/tamlinux/settings-recovery').glob('workspace-layout.*'))
        self.assertEqual(len(snapshots), 1)
        self.assertEqual((snapshots[0] / '0').read_text(), 'personal prior layout\n')
        self.assertEqual(list(target.parent.glob('.layout.*')), [])

    def test_preservation_failure_prevents_layout_write_and_dispatch(self):
        target = self.home / 'state/tamlinux/workspace-layouts/1.lua'
        target.parent.mkdir(parents=True)
        target.write_text('original')
        self.preservation_failure()
        self.assertNotEqual(self.run_helper('tam-hyprland-workspace-layout-toggle').returncode, 0)
        self.assertEqual(target.read_text(), 'original')
        self.assertTrue(all(call[1]=='activeworkspace' for call in self.calls()))

    def test_preservation_failure_prevents_input_state_and_device_mutation(self):
        self.preservation_failure()
        self.assertNotEqual(self.run_helper('tam-toggle-input-device','touchpad','off').returncode, 0)
        self.assertEqual(self.calls(), [['tam-hw-touchpad']])
        self.assertFalse((self.home / 'state/tamlinux/toggles/hypr/touchpad-disabled-name').exists())

    def test_modeless_monitor_distinguishes_missing_modes_and_unanswered_query(self):
        for data, expected in [('[]',1), ('[{"width":0,"height":0}]',0), ('malformed',2)]:
            with self.subTest(data=data):
                self.env['MONITORS']=data
                self.assertEqual(self.run_helper('tam-hyprland-monitor-modeless').returncode, expected)

    def test_scaling_rejects_zero_or_untrusted_native_dimensions_before_dispatch(self):
        for width in [0, '1); evil()', 100000]:
            self.env['MONITORS']=json.dumps([{'focused':True,'name':'DP-1','width':width,
                'height':1080,'refreshRate':60,'scale':1}])
            result=self.run_helper('tam-hyprland-monitor-scaling','1.25')
            self.assertNotEqual(result.returncode,0)
            self.assertTrue(all(call[1]=='monitors' for call in self.calls()))
            self.assertFalse((self.home/'config/tamlinux/hypr/monitors.lua').exists())

    def test_notification_deadline_input_is_rejected_before_bus_or_ipc(self):
        for value in ['-1', '301', '1+evil', '10000000000']:
            self.assertEqual(self.run_helper('tam-notification-wait',value).returncode,2)
        self.assertEqual(self.calls(),[])

    def test_launcher_remove_rejects_parent_traversal_before_any_file_change(self):
        target=self.home/'private.desktop';target.write_text('personal document')
        result=self.run_helper('tam-remove-launcher-entry','../../private','Private')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(target.read_text(),'personal document')


if __name__ == '__main__':
    unittest.main()
