"""Fresh application consumers, custom XDG roots and preserved user choices."""
import importlib.util
from pathlib import Path
import os
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('session_defaults', ROOT / 'desktop/session/initialize.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Defaults(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {'HOME': str(self.root / 'home'), 'XDG_CONFIG_HOME': str(self.root / 'config'),
                    'XDG_STATE_HOME': str(self.root / 'state')}

    def initialize(self):
        return module.initialize(ROOT / 'desktop/assets', self.env)

    def test_empty_configuration_pairs_custom_state_theme_editor_and_kitty_socket(self):
        self.assertEqual(len(self.initialize()), 10)
        config = self.root / 'config'
        self.assertIn(str(self.root / 'state/tamlinux/current/theme/alacritty.toml'),
                      (config / 'alacritty/alacritty.toml').read_text())
        self.assertIn('tamlinux-kitty-{kitty_pid}', (config / 'kitty/kitty.conf').read_text())
        self.assertEqual((config / 'helix/config.toml').read_text(), 'theme = "tamlinux"\n')
        self.assertEqual(os.readlink(config / 'helix/themes/tamlinux.toml'),
                         str(self.root / 'state/tamlinux/current/theme/helix.toml'))
        self.assertEqual((self.root / 'state/tamlinux/defaults/editor').read_text(), 'helix\n')
        self.assertEqual(self.initialize(), [])

    def test_existing_user_bytes_modes_and_dangling_links_are_preserved(self):
        target = self.root / 'config/alacritty/alacritty.toml'
        target.parent.mkdir(parents=True)
        target.write_bytes(b'personal terminal\n'); target.chmod(0o640)
        editor = self.root / 'state/tamlinux/defaults/editor'
        editor.parent.mkdir(parents=True); editor.symlink_to('unavailable-choice')
        self.initialize()
        self.assertEqual(target.read_bytes(), b'personal terminal\n')
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
        self.assertEqual(os.readlink(editor), 'unavailable-choice')

    def test_redirected_destination_parent_is_refused_without_outside_write(self):
        config = self.root / 'config'; outside = self.root / 'other'
        config.mkdir(); outside.mkdir(); (config / 'alacritty').symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink parent'):
            self.initialize()
        self.assertEqual(list(outside.iterdir()), [])

    def test_relative_xdg_is_refused_before_any_publication(self):
        self.env['XDG_STATE_HOME'] = 'relative'
        with self.assertRaises(ValueError): self.initialize()
        self.assertFalse((self.root / 'config').exists())
