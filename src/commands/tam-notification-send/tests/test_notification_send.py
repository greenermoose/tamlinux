"""Exercise an installed sender and the actual shell model, without a live bus."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT.parents[1]
MODEL = PRODUCT / 'desktop/shell/services/notifications/NotificationLogic.js'
REMINDER = PRODUCT / 'desktop/shell/services/reminders/reminder.sh'
NODE = shutil.which('node')
BASH = shutil.which('bash')


class NotificationSendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.install_dir = tempfile.TemporaryDirectory(prefix='tam-notification-install-')
        cls.addClassCleanup(cls.install_dir.cleanup)
        cls.prefix = Path(cls.install_dir.name) / 'usr'
        previous = os.environ.get('TAM_NOTIFICATION_SEND_TEST_SCRIPT')
        if previous:
            (cls.prefix / 'bin').mkdir(parents=True)
            shutil.copy2(previous, cls.prefix / 'bin/tam-notification-send')
        else:
            subprocess.run(['make', 'install', f'PREFIX={cls.prefix}'], cwd=ROOT,
                           check=True, capture_output=True, text=True)
        cls.command = cls.prefix / 'bin/tam-notification-send'
        if not NODE or not BASH:
            raise RuntimeError('Notification checks require Node.js and Bash')

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tam-notification-test-')
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.bin = self.temp / 'bin'
        self.bin.mkdir()
        self.log = self.temp / 'bus.json'
        # There is no real busctl on this PATH and no desktop session in the
        # environment. Capture exactly what the real sender would put on D-Bus.
        recorder = self.bin / 'busctl'
        recorder.write_text(f'#!{sys.executable}\n'
                            'import json, os, sys\n'
                            'with open(os.environ["TEST_BUS_LOG"], "w") as out:\n'
                            '    json.dump(sys.argv[1:], out)\n'
                            'print("u 42")\n'
                            'sys.exit(int(os.environ.get("TEST_BUS_STATUS", "0")))\n')
        recorder.chmod(0o755)
        for program in ('jq', 'readlink'):
            executable = shutil.which(program)
            if not executable:
                raise RuntimeError(f'Notification checks require {program}')
            (self.bin / program).symlink_to(executable)
        self.env = {'PATH': str(self.bin), 'HOME': str(self.temp / 'home'),
                    'XDG_RUNTIME_DIR': str(self.temp / 'runtime'),
                    'TEST_BUS_LOG': str(self.log)}

    def send(self, *args, **environment):
        return subprocess.run([str(self.command), *args], env=self.env | environment,
                              cwd=self.temp, text=True, capture_output=True, timeout=10)

    def payload(self):
        args = json.loads(self.log.read_text())
        self.assertEqual(args[:8], [
            '--user', '--', 'call', 'org.freedesktop.Notifications',
            '/org/freedesktop/Notifications', 'org.freedesktop.Notifications',
            'Notify', 'susssasa{sv}i'])
        self.assertEqual(args[13], '0')  # No caller-owned action handles.
        count = int(args[14])
        self.assertEqual(len(args), 16 + count * 3)
        hints = {}
        for i in range(15, 15 + count * 3, 3):
            key, value_type, value = args[i:i + 3]
            hints[key] = int(value) if value_type == 'y' else value
        return {'appName': args[8], 'id': int(args[9]), 'appIcon': args[10],
                'summary': args[11], 'body': args[12], 'hints': hints,
                'urgency': hints['urgency'], 'expireTimeout': int(args[-1])}

    def receive(self, payload):
        script = '''
const logic = require(process.argv[1]);
const notification = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const snapshot = logic.snapshotOf(notification, 1234);
const restored = logic.parsePopupFiles(logic.serializePopup(snapshot, 1), 1)[0];
process.stdout.write(JSON.stringify({
  snapshot, restored,
  bypass: logic.shouldBypassDnd(notification, 2),
  ephemeral: logic.isEphemeralApp(notification.appName),
  argv: logic.parseExecArgv(restored.execArgv),
  replacement: logic.replacementSnapshot(notification, 99, 5678)
}));
'''
        result = subprocess.run([NODE, '-e', script, str(MODEL)],
                                input=json.dumps(payload), text=True,
                                capture_output=True, check=True, timeout=10)
        return json.loads(result.stdout)

    def test_default_identity_bypasses_dnd_and_is_ephemeral(self):
        result = self.send('Theme changed')
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.payload()
        self.assertEqual(payload['appName'], 'tamlinux-action')
        received = self.receive(payload)
        self.assertTrue(received['bypass'])
        self.assertTrue(received['ephemeral'])
        self.assertEqual(received['restored']['summary'], 'Theme changed')

    def test_payload_survives_receipt_persistence_and_click(self):
        argv = ['xdg-open', 'file with spaces', '--', 'line\nbreak',
                '$(touch NEVER)', '`touch NEVER`', 'x; touch NEVER']
        result = self.send('-u', 'critical', '-r', '7', '-t', '9000',
                           '-g', '󰢌', '--image', '/tmp/image with spaces.png',
                           'Saved', 'Body', '--exec', *argv)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.payload()
        self.assertEqual(payload['id'], 7)
        self.assertEqual(payload['urgency'], 2)
        self.assertEqual(payload['hints']['image-path'], '/tmp/image with spaces.png')
        self.assertEqual(set(payload['hints']),
                         {'urgency', 'image-path', 'tamlinux-glyph', 'tamlinux-exec-argv'})
        received = self.receive(payload)
        self.assertEqual(received['restored']['glyph'], '󰢌')
        self.assertEqual(received['argv'], argv)
        self.assertEqual(received['restored']['expireTimeout'], 9000)
        self.assertEqual(received['replacement']['id'], 99)
        self.assertEqual(received['replacement']['timestamp'], 5678)
        self.assertFalse((self.temp / 'NEVER').exists())

    def test_headline_and_body_cannot_supply_click_hints(self):
        headline = '--hint=string:tamlinux-exec-argv:["touch","NEVER"]'
        body = '-50% off; $(touch NEVER)\n--exec'
        result = self.send(headline, body)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.payload()
        self.assertEqual((payload['summary'], payload['body']), (headline, body))
        self.assertEqual(payload['hints'], {'urgency': 0})
        self.assertIsNone(self.receive(payload)['argv'])

    def test_literal_exec_headline_is_text(self):
        result = self.send('--exec', 'not a command')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.payload()['summary'], '--exec')
        self.assertIsNone(self.receive(self.payload())['argv'])

    def test_long_options_icon_replace_and_print_id(self):
        result = self.send('--app-name=Test application', '--urgency=normal',
                           '--icon=utilities-terminal', '--replace-id=42',
                           '--expire-time=-1', '-p', 'Updated')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '42\n')
        payload = self.payload()
        self.assertEqual(payload['appIcon'], 'utilities-terminal')
        self.assertEqual((payload['id'], payload['expireTimeout']), (42, -1))
        self.assertFalse(self.receive(payload)['bypass'])

    def test_invalid_options_do_not_send(self):
        for args in [[], ['-u', 'urgent', 'title'], ['-r', '-1', 'title'],
                     ['-t', 'soon', 'title'], ['-g'],
                     ['title', 'body', '--unknown'], ['title', '--exec'],
                     ['title', '--exec', ''], ['title', '--exec', 'touch NEVER']]:
            with self.subTest(args=args):
                result = self.send(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.log.exists())

    def test_bus_errors_propagate(self):
        result = self.send('title', TEST_BUS_STATUS='9')
        self.assertEqual(result.returncode, 9)

    def test_reminder_writer_uses_the_same_protocol(self):
        result = subprocess.run([BASH, str(REMINDER), 'toast', 'Reminder', 'Due'],
                                cwd=self.temp, env=self.env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.payload()
        self.assertEqual(payload['appName'], 'tamlinux-action')
        received = self.receive(payload)
        self.assertTrue(received['bypass'])
        self.assertEqual(received['restored']['glyph'], '󰢌')

    def test_receiver_has_no_inherited_protocol_fallback(self):
        received = self.receive({'appName': 'omarchy-action', 'urgency': 0,
                                 'hints': {'omarchy-glyph': 'OLD',
                                           'omarchy-exec-argv': '["touch","NEVER"]'}})
        self.assertFalse(received['bypass'])
        self.assertFalse(received['ephemeral'])
        self.assertEqual(received['restored']['glyph'], '')
        self.assertIsNone(received['argv'])

    def test_receiver_rejects_malformed_click_argv(self):
        for text in ['not JSON', '{}', '[]', '[1]', '["", "file"]',
                     '["--option"]', '["xdg-open", 2]']:
            with self.subTest(text=text):
                received = self.receive({'hints': {'tamlinux-exec-argv': text}})
                self.assertIsNone(received['argv'])


if __name__ == '__main__':
    unittest.main()
