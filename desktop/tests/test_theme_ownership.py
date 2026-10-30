"""Exercise owned writers with real templates and isolated XDG state."""
import importlib.util
import configparser
import json
import os
import re
import runpy
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / 'desktop/theme/engine.py'
ASSETS = ROOT / 'desktop/assets'


class ThemeHealth(unittest.TestCase):
    def test_ipc_health_rejects_the_shadowed_qml_palette(self):
        valid = runpy.run_path(str(ROOT / 'desktop/check-live'))['valid_theme_state']
        palette = {'foreground': '#a9b1d6', 'background': '#1a1b26',
                   'accent': '#7aa2f7', 'muted': '#414868'}
        self.assertTrue(valid(json.dumps(palette)))
        self.assertFalse(valid(json.dumps(dict.fromkeys(palette, 'undefined'))))
        for value in ('{}', '[]', 'null', 'broken JSON'):
            self.assertFalse(valid(value))


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
                self.assertTrue((self.current/'theme').is_dir())
                self.assertFalse((self.current/'theme').is_symlink())
                self.assertIn('"palette"', subprocess.check_output([str(ROOT/'commands/tam-theme-payload/tam-theme-payload')],env=self.env,text=True))
                self.assertNotIn('{{',(self.current/'theme/shell.toml').read_text())
        self.call('set','Tokyo Night')
        self.assertEqual(self.call('current').stdout,'Tokyo Night\n')

    def test_tamarack_variants_generate_and_switch_from_shared_tokens(self):
        for name, background, surface in (('tamarack-dark', '#0f1410', '#18201a'), ('tamarack-light', '#dfd8c7', '#d2c9b6'), ('tamarack-dark', '#0f1410', '#18201a')):
            self.call('set', name)
            output = subprocess.check_output([str(ROOT/'commands/tam-theme-payload/tam-theme-payload')], env=self.env, text=True)
            payload = json.loads(output)
            palette = payload['palette']
            self.assertEqual(payload['style']['fontFamily'], 'Atkinson Hyperlegible')
            self.assertEqual(palette['background'], background)
            self.assertEqual(payload['surfaces']['bar.background'], surface)
            self.assertEqual(payload['surfaces']['tooltip.background'], background)
            self.assertEqual(payload['surfaces']['image-picker.scrim'], background)
            self.assertEqual(payload['surfaces']['menu.selected-background'], surface)
            self.assertIn('active_border_color = \"' + ('#86b86a' if name.endswith('dark') else '#295326') + '\"', (self.current/'theme/hyprland.lua').read_text())
            self.assertEqual(palette['accentText'], background)
            self.assertIn(background[1:], (self.current/'theme/foot.ini').read_text())
            foot = configparser.ConfigParser()
            foot.read(self.current/'theme/foot.ini')
            self.assertEqual(foot['colors-dark']['background'], background[1:])
            self.assertEqual(foot['colors-light']['background'], background[1:])
            self.assertIn('theme[selected_fg]=\"' + background + '\"', (self.current/'theme/btop.theme').read_text())

    def test_tamarack_generated_surface_and_terminal_pairs_have_contrast(self):
        def luminance(color):
            channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
            return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))
        def check(foreground, background):
            low, high = sorted((luminance(foreground), luminance(background)))
            self.assertGreaterEqual((high + 0.05) / (low + 0.05), 4.5, (foreground, background))
        for variant in ('tamarack-dark', 'tamarack-light'):
            self.call('set', variant)
            theme = self.current/'theme'
            payload = json.loads(subprocess.check_output([str(ROOT/'commands/tam-theme-payload/tam-theme-payload')], env=self.env, text=True))
            surfaces = payload['surfaces']
            gtk4 = (theme/'gtk4.css').read_text()
            self.assertIn('--window-fg-color: ' + payload['palette']['foreground'] + ';', gtk4)
            self.assertIn('--window-bg-color: ' + payload['palette']['background'] + ';', gtk4)
            self.assertIn('--accent-bg-color: ' + payload['palette']['accent'] + ';', gtk4)
            self.assertIn('--accent-fg-color: ' + payload['palette']['accentText'] + ';', gtk4)
            check(payload['palette']['accentText'], payload['palette']['accent'])
            self.assertIn('--error-color: ' + payload['palette']['urgent'] + ';', gtk4)
            self.assertIn('--destructive-bg-color: ' + payload['palette']['urgent'] + ';', gtk4)
            self.assertIn('--destructive-fg-color: ' + payload['palette']['background'] + ';', gtk4)
            check(payload['palette']['urgent'], payload['palette']['background'])
            for section in ('bar', 'popups', 'tooltip', 'notifications', 'menu', 'polkit'):
                check(surfaces[section+'.text'], surfaces[section+'.background'])
            check(surfaces['menu.selected-text'], surfaces['menu.selected-background'])
            check(surfaces['polkit.text-error'], surfaces['polkit.background'])
            alacritty = tomllib.loads((theme/'alacritty.toml').read_text())['colors']
            check(alacritty['primary']['foreground'], alacritty['primary']['background'])
            check(alacritty['selection']['text'], alacritty['selection']['background'])
            for name in ('matches', 'focused_match'):
                check(alacritty['search'][name]['foreground'], alacritty['search'][name]['background'])
            foot = (theme/'foot.ini').read_text()
            btop = (theme/'btop.theme').read_text()
            colors = tomllib.loads((theme/'colors.toml').read_text())
            self.assertIn('selection-foreground='+colors['selection_foreground'][1:], foot)
            self.assertIn('selection-background='+colors['selection_background'][1:], foot)
            self.assertIn('theme[selected_fg]="'+colors['selection_foreground']+'"', btop)
            self.assertIn('theme[selected_bg]="'+colors['selection']+'"', btop)
            check(colors['selection_foreground'], colors['selection_background'])
            micro = (theme/'micro.micro').read_text()
            pairs = re.findall(r'^color-link \S+ "(?:bold )?(#[0-9a-fA-F]{6}),(#[0-9a-fA-F]{6})"$', micro, re.MULTILINE)
            self.assertEqual(len(pairs), 22, micro)
            self.assertRegex(micro, r'(?m)^color-link selection "' + colors['selection_foreground'] + r',#[0-9a-fA-F]{6}"$')
            for foreground, background in pairs:
                check(foreground, background)
            vscode = json.loads((theme/'vscode-theme.json').read_text())['colors']
            self.assertEqual(vscode['editor.selectionBackground'], colors['selection_background'])
            check(vscode['editor.selectionForeground'], vscode['editor.selectionBackground'])
            self.assertEqual(vscode['terminal.selectionBackground'], colors['selection_background'])
            check(vscode['terminal.selectionForeground'], vscode['terminal.selectionBackground'])
            check(vscode['button.secondaryForeground'], vscode['button.secondaryBackground'])
            for fg, backgrounds in (
                ('statusBar.foreground', ('statusBarItem.activeBackground', 'statusBarItem.compactHoverBackground')),
                ('statusBarItem.prominentForeground', ('statusBarItem.prominentBackground', 'statusBarItem.prominentHoverBackground')),
                ('statusBarItem.remoteForeground', ('statusBarItem.remoteBackground', 'statusBarItem.remoteHoverBackground')),
                ('statusBarItem.errorForeground', ('statusBarItem.errorBackground', 'statusBarItem.errorHoverBackground')),
                ('statusBarItem.warningForeground', ('statusBarItem.warningBackground', 'statusBarItem.warningHoverBackground')),
                ('commandCenter.activeForeground', ('commandCenter.activeBackground',)),
                ('extensionButton.foreground', ('extensionButton.background', 'extensionButton.hoverBackground')),
                ('extensionButton.prominentForeground', ('extensionButton.prominentBackground', 'extensionButton.prominentHoverBackground')),
            ):
                for bg in backgrounds:
                    check(vscode[fg], vscode[bg])

    def test_tamarack_respects_personal_shell_section(self):
        user = self.config/'tamlinux/themes/tamarack-dark'; user.mkdir(parents=True)
        (user/'shell.menu.toml').write_text('[menu]\nbackground = "#123456"\nbackground-alpha = 0.7\n')
        self.call('set', 'tamarack-dark')
        result = (self.current/'theme/shell.toml').read_text()
        self.assertIn('background = "#123456"', result)
        self.assertIn('background-alpha = 0.7', result)

    def test_tamarack_keeps_personal_gtk4_theme_output(self):
        user = self.config/'tamlinux/themes/tamarack-dark'; user.mkdir(parents=True)
        personal = ':root { --window-fg-color: #123456; }\n'
        (user/'gtk4.css').write_text(personal)
        self.call('set', 'tamarack-dark')
        self.assertEqual((self.current/'theme/gtk4.css').read_text(), personal)

    def test_tamarack_picker_previews_are_generated_from_palette(self):
        recorder = self.base / 'picker-arguments'
        self.stub('tam-menu-images', 'printf "%s\\n" "$@" > "'+str(recorder)+'"')
        self.call('set', 'tamarack-dark')
        self.call('switcher')
        args = recorder.read_text()
        self.assertIn('theme-picker', args)
        previews = list((self.base/'cache/tamlinux/theme-picker').glob('*/tamarack-*.png'))
        self.assertEqual(len(previews), 2)
        self.assertTrue(all(p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for p in previews))

    def test_fresh_initialize_generates_owned_state_without_application_adapters(self):
        self.stub('tam-theme-set-foot', 'exit 17')
        self.call('initialize', env={'TAMLINUX_THEME_OFFLINE': ''})
        self.assertEqual((self.current/'theme.name').read_text(), 'tamarack-dark\n')
        self.assertTrue((self.current/'background').is_symlink())
        self.assertFalse(self.config.exists())
        before = (self.current/'theme/colors.toml').read_bytes()
        self.call('initialize')
        self.assertEqual((self.current/'theme/colors.toml').read_bytes(), before)

    def test_initialize_preserves_existing_selected_name_and_dangling_theme_link(self):
        self.current.mkdir(parents=True)
        (self.current/'theme').symlink_to('user-generation-currently-unavailable')
        (self.current/'theme.name').write_text('personal selection')
        self.call('initialize')
        self.assertEqual(os.readlink(self.current/'theme'), 'user-generation-currently-unavailable')
        self.assertEqual((self.current/'theme.name').read_text(), 'personal selection')

    def test_atomic_exchange_retains_writes_to_open_old_files(self):
        spec = importlib.util.spec_from_file_location('theme_engine_test', ENGINE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.STATE = self.state/'tamlinux'
        active = self.current/'theme'; active.mkdir(parents=True)
        original = active/'personal.txt'; original.write_text('before')
        stage = self.base/'new-theme'; stage.mkdir()
        (stage/'personal.txt').write_text('new')
        with original.open('a') as writer:
            retained = module.publish_theme_directory(stage, active)
            writer.write(' after')
        self.assertEqual((active/'personal.txt').read_text(), 'new')
        self.assertEqual((retained/'personal.txt').read_text(), 'before after')

    def test_initialize_migrates_owned_theme_link_and_preserves_selection(self):
        legacy = self.state/'tamlinux/theme-generations/legacy'
        legacy.mkdir(parents=True)
        (legacy/'colors.toml').write_text('background = "#112233"\n')
        self.current.mkdir(parents=True)
        (self.current/'theme').symlink_to(legacy)
        (self.current/'theme.name').write_text('personal\n')
        self.call('initialize')
        self.assertFalse((self.current/'theme').is_symlink())
        self.assertEqual((self.current/'theme/colors.toml').read_bytes(), (legacy/'colors.toml').read_bytes())
        self.assertEqual((self.current/'theme.name').read_text(), 'personal\n')
        journals = list((self.state/'tamlinux/settings-recovery').glob('theme-directory-migration.*/manifest.json'))
        self.assertTrue(any(json.loads(p.read_text())['files'][0].get('symlink') == str(legacy) for p in journals))

    def test_switch_migrates_legacy_link_without_losing_background(self):
        legacy = self.state/'tamlinux/theme-generations/legacy'
        (legacy/'backgrounds').mkdir(parents=True)
        image = legacy/'backgrounds/personal.png'; image.write_bytes(b'personal artwork')
        self.current.mkdir(parents=True)
        (self.current/'theme').symlink_to(legacy)
        (self.current/'theme.name').write_text('personal\n')
        (self.current/'background').symlink_to(image)
        self.call('set', 'tamarack-dark')
        self.assertTrue((self.current/'theme').is_dir())
        self.assertFalse((self.current/'theme').is_symlink())
        self.assertEqual((self.current/'background').read_bytes(), b'personal artwork')
        self.assertEqual(image.read_bytes(), b'personal artwork')

    def test_active_directory_background_survives_switch_and_failure(self):
        self.call('set', 'tokyo-night')
        image = next((self.current/'theme/backgrounds').iterdir())
        original = image.read_bytes()
        background = self.current/'background'
        background.unlink(); background.symlink_to(image)
        self.stub('tam-theme-set-foot', 'exit 7')
        self.call('set', 'tamarack-dark', success=False, env={'TAMLINUX_THEME_OFFLINE': ''})
        self.assertEqual(background.read_bytes(), original)
        self.assertEqual((self.current/'theme.name').read_text(), 'tokyo-night\n')
        self.call('set', 'tamarack-dark')
        self.assertEqual(background.read_bytes(), original)
        self.assertFalse((self.current/'theme').is_symlink())
        journals = [json.loads(p.read_text()) for p in
                    (self.state/'tamlinux/settings-recovery').glob('theme.*/manifest.json')]
        retired = [Path(j['retiredTheme']) for j in journals if j.get('retiredTheme')]
        self.assertTrue(any((p/'backgrounds'/image.name).read_bytes() == original for p in retired
                            if (p/'backgrounds'/image.name).exists()))

    def test_invalid_input_cannot_mutate_selection(self):
        self.call('set','tokyo-night'); before=(self.current/'theme/colors.toml').read_bytes()
        for value in ('../escape','--foo','missing','a\nname'):
            self.call('set',value,success=False)
            self.assertEqual((self.current/'theme/colors.toml').read_bytes(),before)

    def test_invalid_or_failed_generation_preserves_working_theme(self):
        self.call('set','tokyo-night'); before=(self.current/'theme/colors.toml').read_bytes()
        user=self.config/'tamlinux/themes/broken'; user.mkdir(parents=True)
        (user/'colors.toml').write_text('background = "not a color"\n')
        self.call('set','broken',success=False)
        self.stub('tam-theme-set-templates','exit 7')
        self.call('set','nord',success=False)
        self.assertEqual((self.current/'theme/colors.toml').read_bytes(),before)

    def test_apply_failure_restores_links_names_and_application_bytes(self):
        self.call('set','tokyo-night'); before=(self.current/'theme/colors.toml').read_bytes()
        settings=self.config/'Code/User/settings.json'; settings.parent.mkdir(parents=True); settings.write_text('original settings')
        self.stub('tam-theme-set-foot', 'printf changed > "$XDG_CONFIG_HOME/Code/User/settings.json"; exit 7')
        self.call('set','nord',success=False,env={'TAMLINUX_THEME_OFFLINE':''})
        self.assertEqual(settings.read_text(),'original settings')
        self.assertEqual((self.current/'theme/colors.toml').read_bytes(),before)
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

    def test_refresh_retires_bundled_background_and_journals_original(self):
        self.call('set', 'tokyo-night')
        old_generation = (self.current/'theme').resolve()
        old = old_generation/'backgrounds/6-oma.jpg'
        old.write_bytes(b'retained original image')
        self.call('bg-set', old)
        self.call('refresh')
        self.assertNotEqual((self.current/'background').resolve(), old)
        self.assertTrue((self.current/'background').is_file())
        saved = list((self.state/'tamlinux/theme-generations').glob('background-*/6-oma.jpg'))
        self.assertTrue(any(p.read_bytes() == b'retained original image' for p in saved))
        journals = [json.loads(p.read_text()) for p in
                    (self.state/'tamlinux/settings-recovery').glob('theme.*/manifest.json')]
        self.assertTrue(any(any(f.get('symlink') == str(old) for f in j['files'])
                            for j in journals))

    def test_switch_preserves_dangling_personal_background_link(self):
        self.current.mkdir(parents=True)
        background = self.current/'background'
        background.symlink_to('/unavailable/personal.png')
        self.call('set', 'tamarack-dark')
        self.assertEqual(os.readlink(background), '/unavailable/personal.png')

    def test_switch_preserves_independent_personal_background(self):
        self.call('set', 'tokyo-night')
        personal = self.base/'personal.png'; personal.write_bytes(b'personal image')
        self.call('bg-set', personal)
        self.call('set', 'tamarack-dark')
        self.assertEqual((self.current/'background').resolve(), personal)
        self.assertEqual(personal.read_bytes(), b'personal image')

    def test_tamarack_background_follows_personal_palette_override(self):
        self.call('set', 'tamarack-dark')
        colors = (self.current/'theme/colors.toml').read_text().replace('#0f1410', '#142418')
        user = self.config/'tamlinux/themes/tamarack-dark'; user.mkdir(parents=True)
        (user/'colors.toml').write_text(colors)
        self.call('set', 'tamarack-dark')
        data = (self.current/'theme/backgrounds/tamarack.png').read_bytes()
        size = struct.unpack('!I', data[33:37])[0]
        self.assertEqual(zlib.decompress(data[41:41+size]), b'\x00\x14\x24\x18')
        self.assertEqual((user/'colors.toml').read_text(), colors)

    def test_tamarack_generates_small_solid_default_background(self):
        self.call('set', 'tamarack-dark')
        background = self.current/'background'
        self.assertTrue(background.is_file())
        self.assertTrue(background.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertLess(background.stat().st_size, 256)
        data = background.read_bytes()
        size = struct.unpack('!I', data[33:37])[0]
        self.assertEqual(zlib.decompress(data[41:41+size]), b'\x00\x0f\x14\x10')

    def test_refresh_preserves_same_named_personal_background(self):
        self.call('set', 'tokyo-night')
        personal = self.base/'6-oma.jpg'; personal.write_bytes(b'personal image')
        self.call('bg-set', personal)
        self.call('refresh')
        self.assertEqual((self.current/'background').resolve(), personal)

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
        self.assertEqual(self.call('current').stdout,'Tamarack Dark\n')

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
        for name in ('theme-install','theme-bg-install','branding-about','launch-about'):
            self.assertNotIn('omarchy-'+name,menu)
        self.assertNotIn('omarchy',(ASSETS/'fastfetch.json').read_text().lower())

if __name__=='__main__': unittest.main()
