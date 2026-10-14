"""Capture workflow regressions with recorded tools; no graphical session/device.

The selected helpers execute, including their real Linux PID/start-tick lifecycle.
Only external capture/IPC tools are fixtures. Geometry redesign is out of scope.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

COMMANDS = Path(__file__).resolve().parents[2]
STUB = r'''
import json, os, pathlib, signal, sys, time
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as out:
    out.write(json.dumps([name, args]) + '\n')
if name == 'hyprctl':
    if args[0] == 'monitors': print(os.environ['MONITORS'])
    elif args[0] == 'clients': print(os.environ.get('CLIENTS', '[]'))
    elif args[0] == 'getoption': print('{"int":2}')
    elif args[0] == 'cursorpos': print('20, 20')
elif name == 'slurp':
    sys.stdin.read()
    for _ in range(100):
        if pathlib.Path(os.environ['TEST_FREEZE_PID']).exists(): break
        time.sleep(.01)
    print(os.environ.get('SELECTION', '20,30 640x480'))
elif name == 'hyprpicker':
    pathlib.Path(os.environ['TEST_FREEZE_PID']).write_text(str(os.getpid()))
    while True: time.sleep(.05)
elif name == 'grim':
    if os.environ.get('GRIM_FAIL'): sys.exit(5)
    if args[-1] == '-': sys.stdout.write('image bytes')
    else: pathlib.Path(args[-1]).write_text('image bytes')
elif name in ('tesseract', 'zbarimg'):
    sys.stdin.read()
    if os.environ.get('DECODER_FAIL'): sys.exit(4)
    print(os.environ.get('DECODED', 'fixture decoded text'))
elif name == 'wl-copy':
    if os.environ.get('COPY_FAIL'): sys.exit(3)
    pathlib.Path(os.environ['CLIPBOARD']).write_text(sys.stdin.read())
elif name == 'gpu-screen-recorder':
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    pathlib.Path(os.environ['RECORDER_PID']).write_text(str(os.getpid()))
    if os.environ.get('RECORDER_FAIL'): sys.exit(8)
    if not os.environ.get('RECORDER_STALL'):
        pathlib.Path(args[args.index('-o')+1]).write_text('recorded video')
    while True: time.sleep(.05)
elif name == 'ffprobe':
    if 'a' in args: print('audio')
elif name == 'ffmpeg':
    pathlib.Path(args[args.index('-loglevel')-1]).write_text('processed video')
elif name == 'mpv':
    if args and args[0].startswith('av:'):
        if os.environ.get('WEBCAM_FAIL'): sys.exit(8)
        while True: time.sleep(.05)
elif name == 'v4l2-ctl':
    if '--list-devices' in args:
        print(os.environ.get('DEVICES', ''))
    elif '--info' in args:
        print('Device Caps :\n    Video Capture')
elif name == 'pkill': sys.exit(1)
elif name == 'pgrep': sys.exit(1)
elif name == 'tam-notification-send' and os.environ.get('NOTIFY_FAIL'): sys.exit(1)
'''


class Capture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        names = ('hyprctl', 'slurp', 'hyprpicker', 'grim', 'tesseract', 'zbarimg',
                 'wl-copy', 'gpu-screen-recorder', 'ffmpeg', 'ffprobe', 'mpv',
                 'v4l2-ctl', 'pkill', 'pgrep', 'tam-notification-send', 'tam-shell',
                 'tam-menu-select', 'tensaku')
        for name in names:
            path = self.bin / name
            path.write_text('#!' + sys.executable + '\n' + STUB)
            path.chmod(0o755)
        for path in COMMANDS.glob('tam-capture-*/tam-capture-*'):
            if path.is_file(): (self.bin / path.name).symlink_to(path)
        monitor = dict(name='DP-fixture', focused=True, x=-1280, y=0,
                       width=2560, height=1440, scale=2, transform=0,
                       activeWorkspace={'id': 1})
        self.env = os.environ | {
            'TAMLINUX_GPU_SCREEN_RECORDER': str(self.bin / 'gpu-screen-recorder'),
            'HOME': str(self.root / 'home'), 'XDG_CONFIG_HOME': str(self.root / 'config'),
            'XDG_RUNTIME_DIR': str(self.root / 'runtime'),
            'XDG_STATE_HOME': str(self.root / 'state'),
            'XDG_CACHE_HOME': str(self.root / 'cache'),
            'PATH': str(self.bin) + ':' + os.environ.get('PATH', os.defpath),
            'CALLS': str(self.root / 'calls'), 'CLIPBOARD': str(self.root / 'clipboard'),
            'TEST_FREEZE_PID': str(self.root / 'freeze-pid'),
            'RECORDER_PID': str(self.root / 'recorder-pid'),
            'MONITORS': json.dumps([monitor]),
            'TAMLINUX_SCREENSHOT_DIR': str(self.root / 'Pictures'),
            'TAMLINUX_SCREENRECORD_DIR': str(self.root / 'Videos'),
            'DBUS_SESSION_BUS_ADDRESS': 'unix:path=' + str(self.root / 'no-bus'),
            'WAYLAND_DISPLAY': 'wayland-capture-fixture',
        }
        (self.root / 'runtime').mkdir()
        (self.root / 'Videos').mkdir()
        self.addCleanup(self.kill_children)

    def kill_children(self):
        for name in ('freeze-pid', 'recorder-pid'):
            path = self.root / name
            if path.exists():
                try: os.kill(int(path.read_text()), signal.SIGTERM)
                except ProcessLookupError: pass

    def run_helper(self, name, *args, extra=None, ok=True, timeout=15):
        result = subprocess.run([str(self.bin / ('tam-capture-' + name)), *args],
                                env=self.env | (extra or {}), cwd=self.root,
                                capture_output=True, text=True, timeout=timeout)
        if ok: self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def calls(self, name):
        path = self.root / 'calls'
        return [args for tool, args in map(json.loads, path.read_text().splitlines()) if tool == name] if path.exists() else []

    def assert_dead(self, filename):
        pid = int((self.root / filename).read_text())
        for _ in range(30):
            try:
                state = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()[0]
                if state == 'Z': return
            except (FileNotFoundError, ProcessLookupError): return
            time.sleep(.01)
        self.fail(f'child {pid} survived cleanup')

    def test_fullscreen_and_monitor_match(self):
        self.assertEqual(self.run_helper('region', 'fullscreen').stdout, '-1280,0 1280x720\n')
        self.assertEqual(self.run_helper('region', 'fullscreen', '--match-monitor').stdout, 'monitor:DP-fixture\n')

    def test_cancel_keep_freeze_does_not_leak(self):
        self.assertNotEqual(self.run_helper('region', 'region', '--keep-freeze', extra={'SELECTION': ''}, ok=False).returncode, 0)
        self.assert_dead('freeze-pid')

    def test_screenshot_save_and_copy(self):
        saved = Path(self.run_helper('screenshot', 'region', 'save').stdout.strip())
        self.assertEqual(saved.read_text(), 'image bytes')
        self.assert_dead('freeze-pid')
        self.run_helper('screenshot', 'fullscreen', 'copy')
        self.assertEqual((self.root / 'clipboard').read_text(), 'image bytes')
        self.assertEqual(self.calls('hyprctl')[-1], ['eval', 'hl.config({ cursor = { no_hardware_cursors = 2 } })'])

    def test_screenshot_collision_and_notification_failure(self):
        one = self.run_helper('screenshot', 'fullscreen', extra={'NOTIFY_FAIL': '1'}).stdout.strip()
        two = self.run_helper('screenshot', 'fullscreen', extra={'NOTIFY_FAIL': '1'}).stdout.strip()
        self.assertNotEqual(one, two)
        self.assertEqual(self.calls('tam-notification-send')[-1][-2:], ['tam-capture-edit', two])

    def test_screenshot_invalid_processing(self):
        self.assertNotEqual(self.run_helper('screenshot', 'region', 'invalid', ok=False).returncode, 0)
        self.assertFalse(self.calls('hyprctl'))

    def test_capture_failures_do_not_copy_or_claim_success(self):
        for name, args in [('screenshot', ('fullscreen', 'copy')), ('text', ()), ('qr', ())]:
            with self.subTest(name=name):
                result = self.run_helper(name, *args, extra={'GRIM_FAIL': '1'}, ok=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / 'clipboard').exists())
        self.assertFalse(self.calls('tam-notification-send')[-1][0] == 'QR code copied to clipboard')

    def test_ocr_literal_text_and_language(self):
        text = 'literal $(touch NEVER); text'
        self.run_helper('text', extra={'DECODED': text, 'TAMLINUX_OCR_LANGS': 'eng+fra', 'NOTIFY_FAIL': '1'})
        self.assertEqual((self.root / 'clipboard').read_text(), text)
        self.assertIn('eng+fra', self.calls('tesseract')[-1])
        self.assertFalse((self.root / 'NEVER').exists())
        self.assert_dead('freeze-pid')

    def test_qr_sensitive_and_no_secret_in_output(self):
        secret = 'otpauth://fixture-secret'
        result = self.run_helper('qr', extra={'DECODED': secret})
        self.assertNotIn(secret, result.stdout + result.stderr + (self.root / 'calls').read_text())
        self.assertEqual(self.calls('wl-copy')[-1], ['--sensitive'])
        self.assertIn('-Sdisable', self.calls('zbarimg')[-1])
        self.assertIn('-Sqrcode.enable', self.calls('zbarimg')[-1])
        self.assertEqual((self.root / 'clipboard').read_text(), secret)
        self.assert_dead('freeze-pid')

    def test_decoder_failure(self):
        for name in ('text', 'qr'):
            self.assertNotEqual(self.run_helper(name, extra={'DECODER_FAIL': '1'}, ok=False).returncode, 0)
        self.assertFalse((self.root / 'clipboard').exists())

    def test_clipboard_failure(self):
        for name in ('text', 'qr'):
            self.assertNotEqual(self.run_helper(name, extra={'COPY_FAIL': '1'}, ok=False).returncode, 0)
        self.assertFalse(self.calls('tam-notification-send'))

    def test_edit_literal_filename(self):
        path = self.root / 'image $(touch NEVER).png'
        path.touch()
        self.run_helper('edit', str(path))
        argv = self.calls('tensaku')[-1]
        self.assertEqual(argv[:4], ['--filename', str(path), '--output-filename', str(path)])
        self.assertFalse((self.root / 'NEVER').exists())

    def test_webcam_unavailable(self):
        self.assertEqual(self.run_helper('webcam-list').stdout, '')
        self.assertNotEqual(self.run_helper('screenrecording-with-webcam', ok=False).returncode, 0)
        self.assertFalse(self.calls('gpu-screen-recorder'))

    def test_requested_webcam_failure_prevents_recording(self):
        self.assertNotEqual(self.run_helper('screenrecording-with-webcam',
                            extra={'DEVICES': 'Fixture camera:\n    /dev/video0', 'WEBCAM_FAIL': '1'},
                            ok=False).returncode, 0)
        self.assertFalse(self.calls('gpu-screen-recorder'))
        self.assertFalse((self.root / 'runtime/tamlinux-capture/webcam').exists())

    def test_record_start_status_stop_without_videos_directory(self):
        self.assertNotEqual(self.run_helper('screenrecording', '--status', ok=False).returncode, 0)
        self.run_helper('screenrecording', '--fullscreen', '--with-desktop-audio', '--with-microphone-audio')
        self.run_helper('screenrecording', '--status')
        argv = self.calls('gpu-screen-recorder')[-1]
        self.assertEqual(argv[argv.index('-a')+1], 'default_output|default_input')
        result = self.run_helper('screenrecording', '--stop-recording', extra={'TAMLINUX_SCREENRECORD_DIR': str(self.root / 'missing')})
        self.assertTrue(Path(result.stdout.strip()).is_file())
        self.assertNotEqual(self.run_helper('screenrecording', '--status', ok=False).returncode, 0)
        self.assert_dead('recorder-pid')
        self.assertFalse((self.root / 'runtime/tamlinux-capture/filename').exists())

    def test_record_failed_start(self):
        self.assertNotEqual(self.run_helper('screenrecording', '--fullscreen', extra={'RECORDER_FAIL': '1'}, ok=False).returncode, 0)
        self.assertFalse(list((self.root / 'Videos').iterdir()))
        self.assertFalse((self.root / 'runtime/tamlinux-capture/recorder').exists())

    def test_record_stalled_start_is_bounded(self):
        self.assertNotEqual(self.run_helper('screenrecording', '--fullscreen', extra={'RECORDER_STALL': '1'}, ok=False).returncode, 0)
        self.assert_dead('recorder-pid')
        self.assertFalse(list((self.root / 'Videos').iterdir()))

    def test_recycled_pid_is_not_signalled(self):
        directory = self.root / 'runtime/tamlinux-capture'
        directory.mkdir(mode=0o700)
        (directory / 'recorder').write_text(f'{os.getpid()} 0\n')
        self.assertNotEqual(self.run_helper('screenrecording', '--status', ok=False).returncode, 0)
        self.assertNotEqual(self.run_helper('screenrecording', '--stop-recording', ok=False).returncode, 0)
        self.assertFalse(self.calls('gpu-screen-recorder'))

    def test_record_invalid_options(self):
        for option in ('--unknown', '--webcam-size=huge'):
            self.assertNotEqual(self.run_helper('screenrecording', option, ok=False).returncode, 0)
        self.assertFalse(self.calls('gpu-screen-recorder'))

    def test_recorder_provider_must_be_an_absolute_executable(self):
        for selected in ('gpu-screen-recorder', str(self.root/'missing-provider')):
            result=self.run_helper('screenrecording','--fullscreen',
                extra={'TAMLINUX_GPU_SCREEN_RECORDER':selected},ok=False)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('selected absolute native recorder',result.stderr)
        self.assertFalse(self.calls('gpu-screen-recorder'))

    def test_region_recording_target_preserves_logical_coordinates(self):
        self.run_helper('screenrecording')
        argv = self.calls('gpu-screen-recorder')[-1]
        self.assertEqual(argv[:2], ['-w', '640x480+20+30'])
        self.run_helper('screenrecording', '--stop-recording')

    def test_runtime_symlink_rejected(self):
        directory = self.root / 'runtime/tamlinux-capture'
        destination = self.root / 'other'
        destination.mkdir()
        directory.symlink_to(destination, target_is_directory=True)
        for name in ('region', 'screenrecording'):
            self.assertNotEqual(self.run_helper(name, extra={}, ok=False).returncode, 0)
        self.assertFalse(list(destination.iterdir()))

    def test_webcam_resize_reads_shared_region(self):
        directory = self.root / 'runtime/tamlinux-capture'
        directory.mkdir(mode=0o700)
        (directory / 'region').write_text('640x480+20+30')
        monitors = json.loads(self.env['MONITORS'])
        monitors[0]['id'] = 0
        clients = [dict(title='WebcamOverlay', address='0x123', size=[320, 360], monitor=0)]
        self.run_helper('webcam-resize', 'medium', extra={'CLIENTS': json.dumps(clients), 'MONITORS': json.dumps(monitors)})
        dispatch = [args for args in self.calls('hyprctl') if args[0] == 'dispatch']
        self.assertIn('x = 107, y = 120', dispatch[0][1])
        self.assertIn('x = 513, y = 350', dispatch[1][1])


if __name__ == '__main__': unittest.main()
