"""Effective boot-provider resume hooks; no suspend or boot mutation."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2]/'commands/tam-hibernation-available/tam-hibernation-available'

class ResumeConfiguration(unittest.TestCase):
    def test_effective_hooks_and_explicit_override(self):
        # Exercise the actual function independently of host swap capacity.
        source = SCRIPT.read_text()
        function = source[source.index('resume_configured() {'):source.index('\nif (( SWAPSIZE > HIBERNATION_IMAGE_SIZE )) && resume_configured;')]
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); conf = base/'mkinitcpio.conf'; directory = base/'conf.d'; directory.mkdir()
            cmdline = base/'cmdline'
            env = dict(os.environ, TAM_KERNEL_CMDLINE=str(cmdline), TAM_MKINITCPIO_CONF=str(conf), TAM_MKINITCPIO_CONF_DIR=str(directory))
            env.pop('TAM_RESUME_CONF', None)
            for label, boot, main, dropins, expected in [
                ('resume hook', 'root=x resume=UUID=x', 'HOOKS=(base resume)', {}, True),
                ('systemd hook', 'resume=UUID=x', 'HOOKS=(base systemd)', {}, True),
                ('no device', 'root=x', 'HOOKS=(systemd)', {}, False),
                ('empty device', 'resume=', 'HOOKS=(resume)', {}, False),
                ('no hook', 'resume=x', 'HOOKS=(base udev)', {}, False),
                ('dropin removes hook', 'resume=x', 'HOOKS=(systemd)', {'a.conf':'HOOKS=(base)'}, False),
                ('last dropin wins', 'resume=x', 'HOOKS=(base)', {'a.conf':'HOOKS=(base)', 'z.conf':'HOOKS=(resume)'}, True),
                ('word boundaries', 'noresume=x', 'HOOKS=(systemd)', {}, False),
                ('hook boundaries', 'resume=x', 'HOOKS=(notresume)', {}, False),
            ]:
                with self.subTest(label=label):
                    for p in directory.iterdir(): p.unlink()
                    conf.write_text(main); cmdline.write_text(boot)
                    for name, content in dropins.items(): (directory/name).write_text(content)
                    result = subprocess.run(['bash', '-c', function+'\nresume_configured'], env=env, capture_output=True)
                    self.assertEqual(result.returncode == 0, expected, result.stderr)
            marker = base/'explicit'; marker.touch()
            for path, expected in [(marker, True), (base/'absent', False)]:
                result = subprocess.run(['bash', '-c', function+'\nresume_configured'], env=env|{'TAM_RESUME_CONF':str(path)}, capture_output=True)
                self.assertEqual(result.returncode == 0, expected)
