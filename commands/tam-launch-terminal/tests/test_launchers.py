"""Installed terminal/editor chains; record host effects with isolated state."""

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest

COMMANDS = Path(__file__).resolve().parents[2]
NAMES = ['tam-launch-terminal', 'tam-cmd-terminal-cwd', 'tam-launch-editor',
         'tam-launch-config-editor', 'tam-launch-floating-terminal-with-presentation',
         'tam-show-logo', 'tam-show-done', 'tam-default-editor', 'tam-default-terminal',
         'tam-cmd-present', 'tam-launch-tui', 'tam-notification-send']


class InstalledLaunchers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage = tempfile.TemporaryDirectory(prefix='tam-launch-install-')
        cls.addClassCleanup(cls.stage.cleanup)
        cls.prefix = Path(cls.stage.name) / 'usr'
        for name in NAMES:
            subprocess.run(['make', 'install', f'PREFIX={cls.prefix}'],
                           cwd=COMMANDS / name, capture_output=True, check=True)

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tam-launch-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.home = self.root / 'home'
        self.home.mkdir()
        self.config = self.root / 'config'
        self.state = self.root / 'state'
        self.runtime = self.root / 'runtime'
        self.runtime.mkdir()
        self.work = self.root / 'work with spaces'
        self.work.mkdir()
        self.log = self.root / 'calls.jsonl'
        self.env = {'HOME': str(self.home), 'XDG_CONFIG_HOME': str(self.config),
                    'XDG_STATE_HOME': str(self.state), 'XDG_RUNTIME_DIR': str(self.runtime),
                    'PATH': f'{self.prefix}/bin:{self.bin}', 'TEST_LOG': str(self.log),
                    'TEST_CWD': str(self.work), 'LANG': 'C', 'TERM': 'dumb'}
        for name in ('bash', 'awk', 'grep', 'tail', 'readlink', 'mkdir', 'dirname',
                     'cat', 'basename', 'jq'):
            program = shutil.which(name)
            if not program:
                raise RuntimeError(f'Tests require {name}')
            (self.bin / name).symlink_to(program)
        source = f'#!{sys.executable}\n' + '''
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['TEST_LOG'], 'a') as out:
    out.write(json.dumps({'name': name, 'args': args, 'cwd': os.getcwd(),
                          'gum': os.environ.get('GUM_INPUT_PROMPT_FOREGROUND')}) + '\\n')
if name in ('setsid', 'uwsm-app'):
    if name == 'uwsm-app':
        assert args[0] == '--'
        args = args[1:]
    os.execvp(args[0], args)
elif name == 'xdg-terminal-exec':
    if args == ['--print-id']:
        print(os.environ.get('TEST_TERMINAL', 'foot.desktop:session'))
    elif os.environ.get('TEST_EXEC_PRESENTATION'):
        i = args.index('-e')
        os.execvp(args[i+1], args[i+1:])
elif name == 'hyprctl':
    print(os.environ.get('TEST_WINDOW', 'pid: 42'))
elif name == 'kitten':
    print(json.dumps([{'tabs': [{'windows': [{'cwd': os.environ['TEST_CWD']}]}]}]))
elif name == 'busctl':
    sys.exit(int(os.environ.get('TEST_BUS_STATUS', '0')))
else:
    sys.exit(int(os.environ.get('TEST_COMMAND_STATUS', '0')))
'''
        for name in ('setsid', 'uwsm-app', 'xdg-terminal-exec', 'hyprctl', 'kitten',
                     'pgrep', 'busctl', 'clear', 'nvim', 'vim', 'code', 'capture-args'):
            path = self.bin / name
            path.write_text(source)
            path.chmod(0o755)

    def run_command(self, name, *args, **env):
        return subprocess.run([str(self.prefix / 'bin' / name), *args], cwd=self.home,
                              env=self.env | env, text=True, capture_output=True, timeout=10)

    def calls(self, name):
        if not self.log.exists():
            return []
        return [c for line in self.log.read_text().splitlines()
                if (c := json.loads(line))['name'] == name]

    def choose_editor(self, value):
        path = self.state / 'tamlinux/defaults/editor'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n')
        return path

    def kitty_socket(self, name='tamlinux-kitty-42'):
        sock = socket.socket(socket.AF_UNIX)
        self.addCleanup(sock.close)
        sock.bind(str(self.runtime / name))

    def test_fresh_defaults_read_without_creating_state(self):
        self.assertEqual(self.run_command('tam-default-editor').stdout, 'nvim\n')
        self.assertEqual(self.run_command('tam-default-terminal').stdout, 'foot\n')
        self.assertFalse(self.state.exists())
        self.assertFalse(self.config.exists())

    def test_editor_selector_and_launcher_share_owned_state(self):
        result = self.run_command('tam-default-editor', 'code')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_command('tam-default-editor').stdout, 'code\n')
        self.assertEqual(self.run_command('tam-launch-editor', 'file with spaces').returncode, 0)
        self.assertEqual(self.calls('code')[0]['args'], ['file with spaces'])
        self.assertFalse((self.home / '.local').exists())

    def test_unsupported_editor_preserves_selection(self):
        path = self.choose_editor('vim')
        self.assertNotEqual(self.run_command('tam-default-editor', 'invalid').returncode, 0)
        self.assertEqual(path.read_text(), 'vim\n')
        self.assertFalse(self.calls('busctl'))

    def test_all_editor_choices_round_trip(self):
        for choice, value in [('code', 'code'), ('cursor', 'cursor'), ('zed', 'zeditor'),
                              ('zeditor', 'zeditor'), ('sublime_text', 'sublime_text'),
                              ('helix', 'helix'), ('vim', 'vim'), ('emacs', 'emacs'),
                              ('nvim', 'nvim')]:
            with self.subTest(choice=choice):
                self.assertEqual(self.run_command('tam-default-editor', choice).returncode, 0)
                self.assertEqual(self.run_command('tam-default-editor').stdout, value + '\n')

    def test_terminal_selector_creates_xdg_config_and_retains_choices(self):
        for choice, desktop in [('alacritty', 'Alacritty.desktop'), ('foot', 'foot.desktop'),
                                ('ghostty', 'com.mitchellh.ghostty.desktop'), ('kitty', 'kitty.desktop')]:
            with self.subTest(choice=choice):
                result = self.run_command('tam-default-terminal', choice)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((self.config / 'xdg-terminals.list').read_text().endswith(desktop + '\n'))
                self.assertEqual(self.run_command('tam-default-terminal', TEST_TERMINAL=desktop).stdout,
                                 choice + '\n')
        before = (self.config / 'xdg-terminals.list').read_bytes()
        self.assertNotEqual(self.run_command('tam-default-terminal', 'invalid').returncode, 0)
        self.assertEqual((self.config / 'xdg-terminals.list').read_bytes(), before)
        self.assertFalse((self.home / '.config').exists())

    def test_terminal_launcher_reads_owned_kitty_directory_and_preserves_argv(self):
        self.kitty_socket()
        values = ['program', 'space and "quotes"', '--flag', '$(touch NEVER)']
        result = self.run_command('tam-launch-terminal', *values)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('xdg-terminal-exec')[0]['args'],
                         ['--dir=' + str(self.work), *values])
        self.assertEqual(self.calls('kitten')[0]['args'],
                         ['@', '--to', 'unix:' + str(self.runtime / 'tamlinux-kitty-42'),
                          'ls', '--match', 'state:focused'])
        self.assertFalse((self.home / 'NEVER').exists())

    def test_directory_falls_back_without_shell_or_valid_window_pid(self):
        for window in ('', 'pid: 42', 'pid: invalid'):
            with self.subTest(window=window):
                result = self.run_command('tam-cmd-terminal-cwd', TEST_WINDOW=window)
                self.assertEqual((result.returncode, result.stdout), (0, str(self.home) + '\n'))
        self.assertTrue(all(c['args'] == ['-P', '42'] for c in self.calls('pgrep')))

    def test_directory_rejects_nonexistent_kitty_cwd(self):
        self.kitty_socket()
        result = self.run_command('tam-cmd-terminal-cwd', TEST_CWD=str(self.root / 'missing'))
        self.assertEqual(result.stdout, str(self.home) + '\n')

    def test_old_kitty_socket_is_not_a_runtime_fallback(self):
        self.kitty_socket('omarchy-kitty-42')
        result = self.run_command('tam-cmd-terminal-cwd')
        self.assertEqual(result.stdout, str(self.home) + '\n')
        self.assertFalse(self.calls('kitten'))

    def test_terminal_editor_routes_to_tui_with_discrete_arguments(self):
        self.choose_editor('vim')
        result = self.run_command('tam-launch-editor', 'a b', '--', '$(touch NEVER)')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('xdg-terminal-exec')[0]['args'],
                         ['--app-id=org.tamlinux.vim', '-e', 'vim', 'a b', '--', '$(touch NEVER)'])
        self.assertFalse(self.calls('vim'))

    def test_inline_editor_runs_in_current_terminal(self):
        self.choose_editor('vim')
        result = self.run_command('tam-launch-editor', '--inline', 'a b')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('vim')[0]['args'], ['a b'])
        self.assertFalse(self.calls('xdg-terminal-exec'))

    def test_missing_selected_editor_uses_baseline_neovim_fallback(self):
        self.choose_editor('uninstalled')
        result = self.run_command('tam-launch-editor', '--inline', 'file')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('nvim')[0]['args'], ['file'])

    def test_config_editor_notifies_and_opens_same_path(self):
        self.choose_editor('code')
        path = str(self.config / 'file with "quotes".lua')
        result = self.run_command('tam-launch-config-editor', path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('code')[0]['args'], [path])
        bus = self.calls('busctl')[0]['args']
        self.assertIn('tamlinux-action', bus)
        self.assertIn('Editing config file', bus)
        self.assertIn(path, bus)

    def test_config_editor_missing_path_does_not_launch(self):
        self.assertNotEqual(self.run_command('tam-launch-config-editor').returncode, 0)
        self.assertFalse(self.calls('code'))
        self.assertFalse(self.calls('busctl'))

    def test_config_editing_still_launches_when_notifications_unavailable(self):
        self.choose_editor('code')
        result = self.run_command('tam-launch-config-editor', 'file', TEST_BUS_STATUS='6')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('code')[0]['args'], ['file'])

    def test_presentation_argv_and_owned_theme_are_preserved(self):
        theme = self.state / 'tamlinux/current/theme/gum_env.lua'
        theme.parent.mkdir(parents=True)
        theme.write_text('hl.env("GUM_INPUT_PROMPT_FOREGROUND", "#aabbcc")\n')
        values = ['capture-args', 'space and "quotes"', '--option', '$(touch NEVER)']
        result = self.run_command('tam-launch-floating-terminal-with-presentation', *values,
                                  TEST_EXEC_PRESENTATION='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('capture-args')[0]['args'], values[1:])
        self.assertEqual(self.calls('capture-args')[0]['gum'], '#aabbcc')
        self.assertFalse((self.home / 'NEVER').exists())
        self.assertIn('tam', result.stdout)

    def test_presentation_keeps_single_expression_menu_contract(self):
        result = self.run_command('tam-launch-floating-terminal-with-presentation',
                                  'capture-args "a b"; capture-args second', TEST_EXEC_PRESENTATION='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([c['args'] for c in self.calls('capture-args')], [['a b'], ['second']])

    def test_presentation_retains_failure_status(self):
        result = self.run_command('tam-launch-floating-terminal-with-presentation',
                                  'capture-args', 'argument', TEST_EXEC_PRESENTATION='1',
                                  TEST_COMMAND_STATUS='7')
        self.assertEqual(result.returncode, 7, result.stderr)

    def test_presentation_requires_command_and_done_is_noninteractive_without_tty(self):
        result = self.run_command('tam-launch-floating-terminal-with-presentation')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.calls('xdg-terminal-exec'))
        result = self.run_command('tam-show-done')
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
