"""Opt-in theme recovery proof using a private D-Bus and dconf profile."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT/'desktop/theme/engine.py'
ADAPTER = ROOT/'commands/tam-theme-set-gnome/tam-theme-set-gnome'


def worker():
    spec = importlib.util.spec_from_file_location('theme_engine_proof', ENGINE)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    prefix = '/org/gnome/desktop/interface/'
    before = {prefix+'color-scheme': None, prefix+'gtk-theme': "'Personal'", prefix+'icon-theme': None}
    subprocess.run(['dconf', 'write', prefix+'gtk-theme', "'Personal'"], check=True)
    assert (Path(os.environ['XDG_CONFIG_HOME'])/'dconf/tamlinux_proof').is_file()
    assert engine.gtk_read(shutil.which('dconf')) == before
    settings = Path(os.environ['XDG_CONFIG_HOME'])/'sample.conf'
    settings.write_text('original\n')
    try:
        with engine.transaction('real-dconf-proof', [settings], shutil.which('dconf')) as journal:
            subprocess.run([str(ADAPTER)], check=True)
            observed = engine.gtk_read(shutil.which('dconf'))
            assert observed[prefix+'color-scheme'] == "'prefer-dark'"
            assert observed[prefix+'gtk-theme'] == "'Adwaita-dark'"
            assert observed[prefix+'icon-theme'] == "'Yaru-blue'"
            settings.write_text('later edit\n')
            raise ValueError('injected later failure')
    except ValueError as error:
        assert str(error) == 'injected later failure', error
    assert engine.gtk_read(shutil.which('dconf')) == before
    assert settings.read_text() == 'original\n'
    record = json.loads((journal.directory/'manifest.json').read_text())
    assert record['status'] == 'restored-after-failure'
    assert record['gtkBefore'] == before
    assert record['gtkAfterFailure'] == observed
    assert (journal.directory/record['files'][0]['afterFailure']['saved']).read_text() == 'later edit\n'
    print('isolated dconf and file recovery passed')


@unittest.skipUnless(os.environ.get('TAMLINUX_DCONF_PROOF') == '1', 'opt-in private D-Bus proof')
class ThemeDconfIntegration(unittest.TestCase):
    def test_actual_gnome_adapter_and_dconf_restore(self):
        for command in ('dbus-run-session', 'dconf', 'gsettings'):
            if not shutil.which(command):
                self.skipTest(command+' is unavailable')
        with tempfile.TemporaryDirectory(prefix='tamlinux-dconf-proof-') as directory:
            root = Path(directory)
            for name in ('home', 'config', 'state', 'cache', 'data', 'run', 'bin'):
                (root/name).mkdir(mode=0o700)
            profile = root/'dconf-profile'
            profile.write_text('user-db:tamlinux_proof\n')
            resolver = root/'bin/tam-theme-color'
            resolver.write_text('#!/bin/sh\nprintf "dark\\n"\n')
            resolver.chmod(0o755)
            env = dict(os.environ, HOME=str(root/'home'), XDG_CONFIG_HOME=str(root/'config'),
                       XDG_STATE_HOME=str(root/'state'), XDG_RUNTIME_DIR=str(root/'run'),
                       XDG_CACHE_HOME=str(root/'cache'), XDG_DATA_HOME=str(root/'data'),
                       DCONF_PROFILE=str(profile), GSETTINGS_BACKEND='dconf',
                       PATH=str(root/'bin')+':'+os.defpath)
            for key in ('DBUS_SESSION_BUS_ADDRESS', 'DBUS_STARTER_ADDRESS', 'DBUS_STARTER_BUS_TYPE',
                        'GSETTINGS_SCHEMA_DIR', 'GIO_EXTRA_MODULES', 'PYTHONOPTIMIZE'):
                env.pop(key, None)
            result = subprocess.run(['dbus-run-session', '--', sys.executable, str(Path(__file__).resolve()), '--worker'],
                                    env=env, text=True, capture_output=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('isolated dconf and file recovery passed', result.stdout)


if __name__ == '__main__':
    if sys.argv[1:] == ['--worker']:
        worker()
    else:
        unittest.main()
