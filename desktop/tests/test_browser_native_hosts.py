"""Exercise real frame handling and side-effect boundaries."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]/'browser'
spec = importlib.util.spec_from_file_location('native_host', ROOT/'native_host.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def frame(value):
    data = json.dumps(value).encode()
    return struct.pack('<I', len(data))+data


class NativeHosts(unittest.TestCase):
    def test_extension_keys_match_only_allowed_origins_and_owned_names(self):
        for directory,action,name in [('copy-url','copy','copy_url'),('yt-dlp','download','ytdlp')]:
            manifest=json.loads((ROOT/'extensions'/directory/'manifest.json').read_text())
            digest=hashlib.sha256(base64.b64decode(manifest['key'])).hexdigest()[:32]
            identity=''.join(chr(ord('a')+int(x,16)) for x in digest)
            self.assertEqual(m.ORIGINS[action],f'chrome-extension://{identity}/')
            self.assertIn('nativeMessaging',manifest['permissions'])
            worker=(ROOT/'extensions'/directory/manifest['background']['service_worker']).read_text()
            self.assertIn(f'org.tamlinux.{name}',worker)
            self.assertNotIn('com.omarchy',worker)

    def test_valid_frame_is_read_without_shell_interpretation(self):
        with tempfile.TemporaryFile() as stream:
            stream.write(frame({'url':'https://example.org/a?x=$(id)&q=\"'}));stream.seek(0)
            self.assertEqual(m.request(stream),'https://example.org/a?x=$(id)&q=\"')

    def test_truncated_oversized_and_invalid_frames_do_not_call_tools(self):
        for data in [b'',b'\x05\0\0\0{}',struct.pack('<I',m.MAX_MESSAGE+1),
                     frame({'url':'bad\ncommand'}),frame({'url':12}),frame({'url':'a','extra':True})]:
            result=subprocess.run([sys.executable,'-I',str(ROOT/'native_host.py'),'copy',m.ORIGINS['copy']],
                                  input=data,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            payload=result.stdout[4:];self.assertEqual(struct.unpack('<I',result.stdout[:4])[0],len(payload))
            self.assertEqual(json.loads(payload),{'copied':False})

    def test_wrong_origin_is_refused_before_reading_stdin(self):
        result=subprocess.run([sys.executable,'-I',str(ROOT/'native_host.py'),'download',m.ORIGINS['copy']],
                              input=frame({'url':'https://example.org'}),capture_output=True,timeout=5)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(result.stdout,b'')

    def test_copy_passes_url_as_stdin_and_stdout_stays_private(self):
        with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as call:
            self.assertEqual(m.handle('copy','a;$(id)'),{'copied':True})
        self.assertEqual(call.call_args_list[0].args[0],['wl-copy','--type','text/plain'])
        self.assertEqual(call.call_args_list[0].kwargs['input'],b'a;$(id)')

    def test_download_rejects_non_web_urls_and_credentials_before_spawn(self):
        with patch.object(m.subprocess,'Popen') as spawn:
            for url in ['file:///etc/passwd','--exec=id','https://user:secret@example.org','http:///empty']:
                with self.assertRaises(ValueError):m.handle('download',url)
            spawn.assert_not_called()

    def test_download_detaches_with_one_url_argument_and_no_browser_pipe(self):
        with patch.object(m.subprocess,'Popen') as spawn:
            self.assertEqual(m.handle('download','https://example.org/video'),{'accepted':True})
        self.assertEqual(spawn.call_args.args[0][-2:],['--download','https://example.org/video'])
        self.assertTrue(spawn.call_args.kwargs['start_new_session'])
        self.assertEqual(spawn.call_args.kwargs['stdout'],subprocess.DEVNULL)
