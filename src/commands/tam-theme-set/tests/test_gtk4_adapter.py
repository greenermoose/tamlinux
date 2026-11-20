"""Preserving GTK 4 integration in disposable homes and state directories."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('gtk4_adapter_engine', ROOT / 'desktop/theme/engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
media_supported = engine.gtk4_media_supported


class Gtk4Adapter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'; self.home.mkdir()
        self.config = self.root / 'config'
        self.state = self.root / 'state/tamlinux'
        self.current = self.state / 'current'; self.current.mkdir(parents=True)
        self.bin = self.root / 'bin'; self.bin.mkdir()
        for command in ('tam-theme-set-templates', 'tam-theme-color', 'tam-theme-colors-from-alacritty'):
            (self.bin / command).symlink_to(ROOT / 'commands' / command / command)
        for command in (*('tam-theme-set-' + name for name in engine.ADAPTERS),
                        *('tam-restart-' + name for name in ('terminal', 'hyprctl', 'btop', 'opencode', 'helix')),
                        'tam-hook'):
            self.stub(command, 'exit 0')
        env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.config),
                   XDG_STATE_HOME=str(self.root / 'state'), XDG_CACHE_HOME=str(self.root / 'cache'),
                   TAMLINUX_ASSETS_DIR=str(ROOT / 'desktop/assets'), TAMLINUX_THEME_OFFLINE='',
                   DBUS_SESSION_BUS_ADDRESS='', PATH=str(self.bin) + ':' + os.environ['PATH'])
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, env, clear=True))
        for name, value in (('HOME', self.home), ('CONFIG', self.config), ('STATE', self.state),
                            ('CURRENT', self.current), ('CACHE', self.root / 'cache/tamlinux'),
                            ('ASSETS', ROOT / 'desktop/assets')):
            self.stack.enter_context(patch.object(engine, name, value))
        self.stack.enter_context(patch.object(engine, 'gtk4_media_supported', return_value=True))
        self.stack.enter_context(patch.object(engine, 'sync_shell'))

    def stub(self, command, body):
        path = self.bin / command
        path.write_text('#!' + shutil.which('bash') + '\n' + body + '\n')
        path.chmod(0o755)

    @property
    def css(self):
        return self.config / 'gtk-4.0/gtk.css'

    def test_both_variants_share_one_adaptive_file_and_switch_away_preserves_user_control(self):
        with contextlib.redirect_stderr(io.StringIO()) as messages:
            engine.set_theme('tamarack-dark')
        self.assertTrue(self.css.is_symlink())
        self.assertEqual(os.readlink(self.css), str(self.current / 'theme/gtk4-adaptive.css'))
        dark = self.css.read_text()
        dark_css = (self.current / 'theme/gtk4.css').read_text()
        self.assertIn('@media (prefers-color-scheme: dark)', dark)
        self.assertIn('@media (prefers-color-scheme: light)', dark)
        self.assertIn('#e4e6d8', dark)
        self.assertIn('#18231b', dark)
        self.assertIn('restart already-open applications', messages.getvalue())
        with contextlib.redirect_stderr(io.StringIO()) as messages:
            engine.set_theme('tamarack-light')
        light_css = (self.current / 'theme/gtk4.css').read_text()
        self.assertEqual(self.css.read_text(), dark)
        self.assertEqual(dark, f'@media (prefers-color-scheme: dark) {{\n{dark_css}\n}}\n'
                               f'@media (prefers-color-scheme: light) {{\n{light_css}\n}}\n')
        self.assertNotIn('restart already-open applications', messages.getvalue())
        with contextlib.redirect_stderr(io.StringIO()) as messages:
            engine.set_theme('tokyo-night')
        self.assertFalse(os.path.lexists(self.css))
        self.assertIn('restart already-open applications', messages.getvalue())

    def test_existing_personal_css_file_is_never_replaced(self):
        self.css.parent.mkdir(parents=True)
        self.css.write_text('/* personal */\n')
        with contextlib.redirect_stderr(io.StringIO()) as messages:
            engine.set_theme('tamarack-dark')
        self.assertFalse(self.css.is_symlink())
        self.assertEqual(self.css.read_text(), '/* personal */\n')
        self.assertIn('preserving existing personal stylesheet', messages.getvalue())

    def test_personal_dangling_symlink_is_never_replaced(self):
        self.css.parent.mkdir(parents=True)
        self.css.symlink_to('personal.css')
        with contextlib.redirect_stderr(io.StringIO()):
            engine.set_theme('tamarack-dark')
        self.assertEqual(os.readlink(self.css), 'personal.css')

    def test_failed_later_adapter_restores_absence_and_previous_theme(self):
        engine.set_theme('tokyo-night')
        self.stub('tam-theme-set-browser', 'exit 7')
        with self.assertRaises(subprocess.CalledProcessError):
            engine.set_theme('tamarack-dark')
        self.assertFalse(os.path.lexists(self.css))
        self.assertEqual((self.current / 'theme.name').read_text(), 'tokyo-night\n')

    def test_failed_switch_restores_owned_link_and_previous_palette(self):
        with contextlib.redirect_stderr(io.StringIO()):
            engine.set_theme('tamarack-dark')
        original = self.css.read_bytes()
        self.stub('tam-theme-set-browser', 'exit 7')
        with self.assertRaises(subprocess.CalledProcessError):
            engine.set_theme('tamarack-light')
        self.assertTrue(self.css.is_symlink())
        self.assertEqual(self.css.read_bytes(), original)
        self.assertEqual((self.current / 'theme.name').read_text(), 'tamarack-dark\n')

    def test_variant_color_override_is_in_pair_in_either_direction(self):
        user = self.config / 'tamlinux/themes/tamarack-dark'
        user.mkdir(parents=True)
        (user / 'colors.toml').write_text(engine.tamarack_colors('dark').replace('#e4e6d8', '#f0f1ea'))
        with contextlib.redirect_stderr(io.StringIO()):
            engine.set_theme('tamarack-light')
        pair = self.css.read_text()
        self.assertIn('#f0f1ea', pair)
        with contextlib.redirect_stderr(io.StringIO()):
            engine.set_theme('tamarack-dark')
        self.assertEqual(self.css.read_text(), pair)

    def test_personal_template_is_preserved_and_not_nested(self):
        template = self.config / 'tamlinux/themed/gtk4.css.tpl'
        template.parent.mkdir(parents=True)
        template.write_text('/* personal */\n')
        engine.set_theme('tamarack-dark')
        self.assertFalse(os.path.lexists(self.css))
        self.assertEqual((self.current / 'theme/gtk4.css').read_text(), '/* personal */\n')

    def test_personal_variant_css_disables_only_our_link(self):
        with contextlib.redirect_stderr(io.StringIO()):
            engine.set_theme('tamarack-dark')
        personal = self.config / 'tamlinux/themes/tamarack-light/gtk4.css'
        personal.parent.mkdir(parents=True)
        personal.write_text('/* personal variant */\n')
        with contextlib.redirect_stderr(io.StringIO()) as messages:
            engine.set_theme('tamarack-light')
        self.assertFalse(os.path.lexists(self.css))
        self.assertEqual(personal.read_text(), '/* personal variant */\n')
        self.assertEqual((self.current / 'theme/gtk4.css').read_text(), '/* personal variant */\n')
        self.assertIn('restart already-open applications', messages.getvalue())

    def test_unsupported_gtk_does_not_install_managed_css(self):
        with patch.object(engine, 'gtk4_media_supported', return_value=False):
            with contextlib.redirect_stderr(io.StringIO()) as messages:
                engine.set_theme('tamarack-dark')
        self.assertFalse(os.path.lexists(self.css))
        self.assertIn('GTK 4.20 or newer', messages.getvalue())

    def test_missing_library_lookup_is_treated_as_unsupported(self):
        with patch.object(engine.ctypes.util, 'find_library', side_effect=OSError('unavailable')):
            self.assertFalse(media_supported())

    def test_unavailable_alternate_palette_does_not_block_theme_switch(self):
        with patch.object(engine, 'prepare_gtk4_pair', side_effect=OSError('unavailable')):
            with contextlib.redirect_stderr(io.StringIO()) as messages:
                engine.set_theme('tamarack-dark')
        self.assertEqual((self.current / 'theme.name').read_text(), 'tamarack-dark\n')
        self.assertFalse(os.path.lexists(self.css))
        self.assertIn('adaptive palette unavailable', messages.getvalue())

    def test_offline_theme_change_preserves_the_managed_css_target(self):
        with contextlib.redirect_stderr(io.StringIO()):
            engine.set_theme('tamarack-dark')
        before = self.css.read_bytes()
        with patch.dict(os.environ, {'TAMLINUX_THEME_OFFLINE': '1'}):
            engine.set_theme('tokyo-night')
        self.assertTrue(self.css.is_symlink())
        self.assertEqual(self.css.read_bytes(), before)
