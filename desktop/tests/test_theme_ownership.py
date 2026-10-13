"""Exercise owned writers with real templates and isolated XDG state."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / 'desktop/theme/engine.py'
ASSETS = ROOT / 'desktop/assets'

class ThemeOwnership(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / 'bin'; self.bin.mkdir()
        self.config = self.base / 'config'; self.state = self.base / 'state'
        self.env = dict(os.environ, HOME=str(self.base / 'home'), XDG_CONFIG_HOME=str(self.config),
                        XDG_STATE_HOME=str(self.state), XDG_CACHE_HOME=str(self.base/'cache'),
                        TAMLINUX_ASSETS_DIR=str(ASSETS), TAMLINUX_THEME_ENGINE=str(ENGINE),
                        TAMLINUX_THEME_OFFLINE='1', PATH=str(self.bin)+':'+os.environ['PATH'])
        for name in ('tam-theme-set-templates', 'tam-theme-color', 'tam-theme-colors-from-alacritty'):
            (self.bin / name).symlink_to(ROOT/'commands'/name/name)
        self.stub('tam-shell', 'exit 0')
        self.stub('tam-launch-about', 'exit 0')
        self.stub('tam-launch-screensaver', 'exit 0')
        self.stub('tam-launch-editor', 'exit 0')
        self.stub('tam-restart-terminal', 'exit 0')
        self.stub('tam-restart-shell', 'exit 0')
        self.stub('tam-hook', 'exit 0')

    def stub(self, name, code):
        p=self.bin/name
        if p.is_symlink(): p.unlink()
        p.write_text('#!'+shutil.which('bash')+'\n'+code+'\n'); p.chmod(0o755)

    def call(self, action, *args, success=True, env=None):
        result=subprocess.run(['python3', str(ENGINE), action, *map(str,args)], env=self.env | (env or {}), text=True, capture_output=True, timeout=30)
        if success: self.assertEqual(result.returncode,0,result.stderr)
        else: self.assertNotEqual(result.returncode,0,result.stdout)
        return result

    @property
    def current(self): return self.state/'tamlinux/current'

    def test_all_bundled_themes_generate_without_inherited_tools(self):
        for theme in sorted((ASSETS/'themes').iterdir()):
            with self.subTest(theme=theme.name):
                self.call('set',theme.name)
                self.assertEqual((self.current/'theme.name').read_text().strip(),theme.name)
                self.assertTrue((self.current/'theme').is_symlink())
                self.assertIn('"palette"', subprocess.check_output([str(ROOT/'commands/tam-theme-payload/tam-theme-payload')],env=self.env,text=True))
                self.assertNotIn('{{',(self.current/'theme/shell.toml').read_text())
        self.call('set','Tokyo Night')
        self.assertEqual(self.call('current').stdout,'Tokyo Night\n')

    def test_invalid_input_cannot_mutate_selection(self):
        self.call('set','tokyo-night'); before=os.readlink(self.current/'theme')
        for value in ('../escape','--foo','missing','a\nname'):
            self.call('set',value,success=False)
            self.assertEqual(os.readlink(self.current/'theme'),before)

    def test_invalid_or_failed_generation_preserves_working_theme(self):
        self.call('set','tokyo-night'); before=os.readlink(self.current/'theme')
        user=self.config/'tamlinux/themes/broken'; user.mkdir(parents=True)
        (user/'colors.toml').write_text('background = "not a color"\n')
        self.call('set','broken',success=False)
        self.stub('tam-theme-set-templates','exit 7')
        self.call('set','nord',success=False)
        self.assertEqual(os.readlink(self.current/'theme'),before)

    def test_apply_failure_restores_links_names_and_application_bytes(self):
        self.call('set','tokyo-night'); before=os.readlink(self.current/'theme')
        settings=self.config/'Code/User/settings.json'; settings.parent.mkdir(parents=True); settings.write_text('original settings')
        self.stub('tam-theme-set-foot', 'printf changed > "$XDG_CONFIG_HOME/Code/User/settings.json"; exit 7')
        self.call('set','nord',success=False,env={'TAMLINUX_THEME_OFFLINE':''})
        self.assertEqual(settings.read_text(),'original settings')
        self.assertEqual(os.readlink(self.current/'theme'),before)
        self.assertEqual((self.current/'theme.name').read_text(),'tokyo-night\n')
        journals=list((self.state/'tamlinux/settings-recovery').glob('theme.*/manifest.json'))
        self.assertTrue(any(json.loads(p.read_text())['status']=='restored-after-failure' for p in journals))

    def test_local_palette_overlays_and_shell_section_templates(self):
        user=self.config/'tamlinux/themes/tokyo-night'; user.mkdir(parents=True)
        (user/'shell.bar.toml').write_text('[bar]\nbackground = "#123456"\n')
        self.call('set','tokyo-night')
        self.assertIn('#123456',(self.current/'theme/shell.toml').read_text())

    def test_repo_theme_cannot_publish_executable_configs_or_external_links(self):
        user=self.config/'tamlinux/themes/extra'; (user/'.git').mkdir(parents=True)
        shutil.copyfile(ASSETS/'themes/tokyo-night/colors.toml',user/'colors.toml')
        for file in ('hyprland.lua','neovim.lua','alacritty.toml','kitty.conf','vscode.json'):
            (user/file).write_text('run arbitrary code')
        (user/'escape.txt').symlink_to('/etc/passwd')
        self.call('set','extra')
        self.assertNotEqual((self.current/'theme/hyprland.lua').read_text(),'run arbitrary code')
        self.assertNotEqual((self.current/'theme/kitty.conf').read_text(),'run arbitrary code')
        self.assertFalse((self.current/'theme/escape.txt').exists())
        self.assertFalse((self.current/'theme/vscode.json').exists())

    def test_background_set_next_refresh_and_failed_set(self):
        self.call('set','tokyo-night')
        image=self.base/'image with spaces.png'; image.write_bytes(b'image')
        self.call('bg-set',image); self.assertEqual((self.current/'background').resolve(),image)
        self.call('refresh'); self.assertEqual((self.current/'background').resolve(),image)
        self.call('bg-set',self.base/'missing.png',success=False)
        self.assertEqual((self.current/'background').resolve(),image)
        self.call('bg-next'); self.assertNotEqual((self.current/'background').resolve(),image)

    def test_remove_preserves_user_tree_and_returns_to_baseline(self):
        user=self.config/'tamlinux/themes/extra'; user.mkdir(parents=True)
        shutil.copyfile(ASSETS/'themes/nord/colors.toml',user/'colors.toml')
        self.call('set','extra'); self.call('remove','extra')
        self.assertFalse(user.exists())
        self.assertEqual((self.current/'theme.name').read_text(),'tokyo-night\n')
        journals=list((self.state/'tamlinux/settings-recovery').glob('theme-remove.*/0/colors.toml'))
        self.assertEqual(journals[0].read_bytes(),(ASSETS/'themes/nord/colors.toml').read_bytes())
        self.call('remove','../other',success=False)

    def test_install_rejects_options_transport_helpers_and_existing_themes(self):
        for url in ('--upload-pack=bad','ext::bad','file:///tmp/theme','https://omarchy.org/themes/whatever',''):
            if not url: continue
            self.call('install',url,success=False)
        user=self.config/'tamlinux/themes/extra'; user.mkdir(parents=True)
        (user/'original').write_text('saved')
        self.call('install','https://example.invalid/extra-theme.git',success=False)
        self.assertEqual((user/'original').read_text(),'saved')

    def test_font_writer_preserves_xml_terminal_quoting_and_symlink_source(self):
        family='Font & "Quote" \\ Name'
        self.stub('fc-list', "printf '%s\\n' 'Font & \"Quote\" \\ Name'")
        original=self.base/'original.toml'; original.write_text('[font.normal]\nfamily = "Before"\n')
        alacritty=self.config/'alacritty/alacritty.toml'; alacritty.parent.mkdir(parents=True); alacritty.symlink_to(original)
        fontconf=self.config/'fontconfig/fonts.conf'; fontconf.parent.mkdir(parents=True); fontconf.write_text('<fontconfig><!--user settings--><dir>/extra/fonts</dir></fontconfig>')
        self.call('font-set',family)
        self.assertEqual(original.read_text(),'[font.normal]\nfamily = "Before"\n')
        import tomllib
        self.assertEqual(tomllib.loads(alacritty.read_text())['font']['normal']['family'],family)
        import xml.etree.ElementTree as ET
        xml=ET.parse(self.config/'fontconfig/conf.d/99-tamlinux-monospace.conf')
        self.assertEqual(xml.find('.//edit/string').text,family)
        self.assertIn('<!--user settings-->',fontconf.read_text())
        self.assertIn('<dir>/extra/fonts</dir>',fontconf.read_text())
        self.call('font-set','missing',success=False)
        journals=list((self.state/'tamlinux/settings-recovery').glob('font.*/manifest.json'))
        self.assertTrue(any('symlink' in x for x in json.loads(journals[0].read_text())['files']))

    def test_branding_reset_edit_cancel_and_failed_conversion(self):
        dest=self.config/'tamlinux/branding/about.txt'; dest.parent.mkdir(parents=True); dest.write_text('user logo')
        self.stub('tam-transcode-ascii','exit 7')
        self.call('branding-about','image','bad.png',success=False)
        self.assertEqual(dest.read_text(),'user logo')
        self.stub('tam-file-select','exit 0')
        self.call('branding-about','image'); self.assertEqual(dest.read_text(),'user logo')
        self.call('branding-about','reset'); self.assertEqual(dest.read_text(),'TAMLINUX\n')
        self.call('branding-screensaver','text')
        self.assertEqual((dest.parent/'screensaver.txt').read_text(),'TAMLINUX\n')

    def test_font_changes_inline_alacritty_families_and_can_change_again(self):
        self.stub('fc-list', "printf '%s\\n' 'Selected Font' 'Other Font'")
        terminal=self.config/'alacritty/alacritty.toml'; terminal.parent.mkdir(parents=True)
        terminal.write_text('[font]\nnormal = { family = "Before" }\nbold = { family = "Before" }\n')
        self.call('font-set','Selected Font')
        self.call('font-set','Other Font')
        import tomllib
        data=tomllib.loads(terminal.read_text())
        self.assertEqual(data['font']['normal']['family'],'Other Font')
        self.assertEqual(data['font']['bold']['family'],'Other Font')

    def test_malformed_fontconfig_restores_terminal_writes(self):
        self.stub('fc-list', "printf 'Selected Font\\n'")
        terminal=self.config/'alacritty/alacritty.toml'; terminal.parent.mkdir(parents=True)
        terminal.write_text('[font.normal]\nfamily = "Before"\n')
        fontconf=self.config/'fontconfig/fonts.conf'; fontconf.parent.mkdir(parents=True)
        fontconf.write_text('broken XML')
        self.call('font-set','Selected Font',success=False)
        self.assertEqual(terminal.read_text(),'[font.normal]\nfamily = "Before"\n')
        self.assertEqual(fontconf.read_text(),'broken XML')
        self.assertFalse((fontconf.parent/'conf.d/99-tamlinux-monospace.conf').exists())

    def test_picker_preload_keeps_its_images_and_does_not_lock_readers(self):
        self.stub('tam-menu-images', 'test -d "${@: -1}"; printf "%s" "${@: -1}"')
        result=self.call('switcher','--preload')
        previews=Path(result.stdout)
        self.assertTrue(previews.is_dir())
        self.assertTrue(all(p.exists() for p in previews.iterdir()))
        self.assertEqual(self.call('current').stdout,'Tokyo Night\n')

    def test_font_package_install_refuses_inherited_or_failed_resolution(self):
        command=ROOT/'commands/tam-pkg-add/tam-pkg-add'
        for output in ('omarchy some-font', 'extra omarchy-settings', 'extra linux-omarchy'):
            self.stub('pacman', 'if [[ $1 == -Q ]]; then exit 1; fi; printf "%s\\n" '+__import__('shlex').quote(output))
            self.stub('pkexec', 'touch "'+str(self.base/'privileged')+'"; exit 99')
            result=subprocess.run([str(command),'ttf-example'],env=self.env,text=True,capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((self.base/'privileged').exists())
        self.stub('pacman','exit 7')
        result=subprocess.run([str(command),'ttf-example'],env=self.env,text=True,capture_output=True,timeout=5)
        self.assertEqual(result.returncode,7)
        self.assertFalse((self.base/'privileged').exists())

    def test_asset_default_menu_has_owned_names_and_fonts(self):
        menu=(ROOT/'desktop/menu/default.jsonc').read_text()
        self.assertIn('"iconFont":"Tamlinux Icons"',menu)
        for name in ('theme-install','theme-bg-install','branding-about','branding-screensaver','launch-about'):
            self.assertNotIn('omarchy-'+name,menu)
        self.assertNotIn('omarchy',(ASSETS/'fastfetch.json').read_text().lower())

if __name__=='__main__': unittest.main()
