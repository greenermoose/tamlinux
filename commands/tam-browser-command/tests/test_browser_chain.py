"""Installed browser/focus chains with isolated XDG state and recorded IPC."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

COMMANDS = Path(__file__).resolve().parents[2]
NAMES = ('tam-browser-command', 'tam-default-browser', 'tam-launch-browser',
         'tam-launch-webapp', 'tam-hyprland-focus-app', 'tam-launch-or-focus',
         'tam-launch-or-focus-webapp', 'tam-launch-or-focus-tui', 'tam-launch-tui',
         'tam-notification-send')


class BrowserChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.stage.cleanup)
        cls.prefix = Path(cls.stage.name)
        for name in NAMES:
            subprocess.run(['make', 'install', f'PREFIX={cls.prefix}'],
                           cwd=COMMANDS / name, check=True, capture_output=True)

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.bin = self.root / 'host-bin'
        self.bin.mkdir()
        self.log = self.root / 'calls.jsonl'
        self.home = self.root / 'home'
        self.home.mkdir()
        self.data = self.root / 'data'
        self.env = {'HOME': str(self.home), 'PATH': f'{self.prefix}/bin:{self.bin}',
                    'XDG_DATA_HOME': str(self.data), 'XDG_DATA_DIRS': str(self.root / 'system-data'),
                    'XDG_CONFIG_HOME': str(self.root / 'config'), 'TEST_LOG': str(self.log),
                    'TEST_DEFAULT': 'chromium.desktop', 'BROWSER': 'must-be-unset', 'LANG': 'C'}
        for name in ('python3', 'bash', 'env', 'jq', 'grep', 'date', 'basename', 'head'):
            (self.bin / name).symlink_to(shutil.which(name))
        self.recorder = f'#!{sys.executable}\n' + '''
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['TEST_LOG'], 'a') as out:
    out.write(json.dumps({'name': name, 'args': args, 'browser': os.environ.get('BROWSER')}) + '\\n')
if name == 'xdg-settings':
    if os.environ.get('TEST_XDG_FAIL'): sys.exit(1)
    if args[0] == 'get': print(os.environ.get('TEST_DEFAULT', 'chromium.desktop'))
elif name == 'xdg-mime': print('chromium.desktop')
elif name == 'systemd-run':
    if os.environ.get('TEST_RUN_FAIL'): sys.exit(1)
    i = args.index('uwsm-app')
    os.execvp(args[i], args[i:])
elif name in ('setsid', 'uwsm-app'):
    if name == 'uwsm-app': args = args[1:]
    os.execvp(args[0], args)
elif name == 'hyprctl':
    if args[:2] == ['clients', '-j']: print(os.environ.get('TEST_CLIENTS', '[]'))
    elif os.environ.get('TEST_LUA_FAIL') and args[1].startswith('hl.'): sys.exit(1)
elif '--help' in args and os.environ.get('TEST_FIREFOX'): print('MOZ_LOG')
'''
        for name in ('xdg-settings', 'xdg-mime', 'systemd-run', 'uwsm-app',
                     'setsid', 'hyprctl', 'busctl', 'xdg-terminal-exec', 'chromium', 'firefox'):
            self.stub(self.bin / name)
        self.desktop('chromium.desktop', 'chromium --profile-directory="Default Profile" %U')

    def stub(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.recorder)
        path.chmod(0o755)

    def desktop(self, name, command, root=None, extra=''):
        path = (root or self.data) / 'applications' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('[Desktop Entry]\nType=Application\nName=Browser Name\n'
                        f'Exec={command}\n{extra}')
        return path

    def run_command(self, name, *args, **env):
        return subprocess.run([str(self.prefix / 'bin' / name), *args],
                              cwd=self.home, env=self.env | env, text=True,
                              capture_output=True, timeout=10)

    def calls(self, name):
        if not self.log.exists(): return []
        return [value for line in self.log.read_text().splitlines()
                if (value := json.loads(line))['name'] == name]

    def test_xdg_precedence_and_static_arguments(self):
        self.desktop('chromium.desktop', 'wrong', self.root / 'system-data')
        result = self.run_command('tam-browser-command', 'chromium.desktop')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ['chromium', '--profile-directory=Default Profile'])
        self.assertFalse(self.log.exists())

    def test_quoted_executable_and_literal_shell_characters(self):
        self.desktop('custom.desktop', '"/opt/Browser With Spaces" "literal $(touch NEVER)" %U')
        result = self.run_command('tam-browser-command', 'custom.desktop')
        self.assertEqual(json.loads(result.stdout), ['/opt/Browser With Spaces', 'literal $(touch NEVER)'])
        self.assertFalse((self.home / 'NEVER').exists())

    def test_field_codes_expand_as_argv_without_recursive_expansion(self):
        path = self.desktop('custom.desktop', 'chromium %i %c %k "100%%" %U', extra='Icon=browser-icon\n')
        result = self.run_command('tam-browser-command', 'custom.desktop')
        self.assertEqual(json.loads(result.stdout), ['chromium', '--icon', 'browser-icon',
                                                  'Browser Name', str(path), '100%'])

    def test_invalid_hidden_missing_and_path_entries_fail_before_launch(self):
        self.desktop('bad.desktop', 'chromium %Z')
        self.desktop('hidden.desktop', 'chromium', extra='Hidden=true\n')
        self.desktop('quote.desktop', '"chromium')
        for name in ('bad.desktop', 'hidden.desktop', 'quote.desktop', 'absent.desktop', '../chromium.desktop'):
            with self.subTest(name=name):
                result = self.run_command('tam-browser-command', name)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
        self.assertFalse(self.log.exists())

    def test_xdg_data_dirs_provider_and_empty_home(self):
        self.desktop('firefox.desktop', 'firefox %u', self.root / 'system-data')
        result = self.run_command('tam-browser-command', 'firefox.desktop')
        self.assertEqual(json.loads(result.stdout), ['firefox'])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_profile_provider_fallback(self):
        self.desktop('profile.desktop', 'chromium', self.home / '.nix-profile/share')
        result = self.run_command('tam-browser-command', 'profile.desktop')
        self.assertEqual(json.loads(result.stdout), ['chromium'])

    def test_default_get_and_set_clear_browser_environment(self):
        self.assertEqual(self.run_command('tam-default-browser').stdout, 'chromium\n')
        result = self.run_command('tam-default-browser', 'firefox')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('xdg-settings')[-1]['args'], ['set', 'default-web-browser', 'firefox.desktop'])
        self.assertTrue(all(value['browser'] is None for value in self.calls('xdg-settings')))

    def test_rejected_selection_and_failed_handler_do_not_notify(self):
        self.assertNotEqual(self.run_command('tam-default-browser', 'unknown').returncode, 0)
        self.assertNotEqual(self.run_command('tam-default-browser', 'firefox', TEST_XDG_FAIL='1').returncode, 0)
        self.assertEqual(self.calls('busctl'), [])

    def test_browser_private_preserves_urls_and_literal_arguments(self):
        literal = 'https://example.org/?q=--private $(touch NEVER)'
        result = self.run_command('tam-launch-browser', '--private', literal, 'second URL')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('chromium')[-1]['args'], ['--profile-directory=Default Profile',
                                                          '--incognito', literal, 'second URL'])
        self.assertFalse((self.home / 'NEVER').exists())

    def test_firefox_private_and_https_handler_fallback(self):
        self.desktop('firefox.desktop', 'firefox %U')
        result = self.run_command('tam-launch-browser', '--private', TEST_DEFAULT='firefox.desktop', TEST_FIREFOX='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('firefox')[-1]['args'], ['--private-window'])
        result = self.run_command('tam-launch-browser', TEST_DEFAULT='')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls('xdg-mime')), 1)

    def test_browser_failure_does_not_focus(self):
        result = self.run_command('tam-launch-browser', 'https://example.org', TEST_RUN_FAIL='1', HYPRLAND_INSTANCE_SIGNATURE='fixture')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls('hyprctl'), [])

    def test_webapp_chromium_fallback_and_argument_boundaries(self):
        literal = 'https://example.org/?x=$(touch NEVER)&q=a b'
        result = self.run_command('tam-launch-webapp', literal, '--name=App With Spaces', TEST_DEFAULT='firefox.desktop')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('chromium')[-1]['args'], ['--profile-directory=Default Profile',
                                                          '--app=' + literal, '--name=App With Spaces'])
        self.assertFalse((self.home / 'NEVER').exists())
        self.assertNotEqual(self.run_command('tam-launch-webapp').returncode, 0)

    def test_focus_owned_agent_title_and_legacy_dispatch_fallback(self):
        clients = json.dumps([{'class': 'foot', 'initialClass': 'org.tamlinux.agent',
                               'initialTitle': 'codex', 'address': '0x123'}])
        result = self.run_command('tam-hyprland-focus-app', 'codex', TEST_CLIENTS=clients, TEST_LUA_FAIL='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('hyprctl')[-1]['args'], ['dispatch', 'focuswindow', 'address:0x123'])

    def test_old_agent_class_does_not_act_as_runtime_alias(self):
        clients = json.dumps([{'class': 'foot', 'initialClass': 'org.omarchy.agent',
                               'initialTitle': 'codex', 'address': '0x123'}])
        self.assertNotEqual(self.run_command('tam-hyprland-focus-app', 'codex', TEST_CLIENTS=clients).returncode, 0)

    def test_focus_webapp_keeps_literal_url_and_focus_skips_launch(self):
        literal = 'https://example.org/?q=$(touch NEVER)&x=a b'
        result = self.run_command('tam-launch-or-focus-webapp', 'Example', literal)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('chromium')[-1]['args'][-1], '--app=' + literal)
        self.assertFalse((self.home / 'NEVER').exists())
        count = len(self.calls('chromium'))
        clients = json.dumps([{'class': 'Example', 'title': 'Example', 'address': '0x456'}])
        result = self.run_command('tam-launch-or-focus-webapp', 'Example', literal, TEST_CLIENTS=clients)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls('chromium')), count)

    def test_focus_tui_preserves_argv_and_rejects_empty_request(self):
        literal = 'literal $(touch NEVER) with spaces'
        result = self.run_command('tam-launch-or-focus-tui', 'micro', literal)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('xdg-terminal-exec')[-1]['args'], ['--app-id=org.tamlinux.micro', '-e', 'micro', literal])
        self.assertFalse((self.home / 'NEVER').exists())
        self.assertNotEqual(self.run_command('tam-launch-or-focus-tui').returncode, 0)


if __name__ == '__main__':
    unittest.main()
