"""Installed helper chains with recorded host IPC/terminal/timezone boundaries."""

import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = ROOT.parent
PRODUCT = COMMANDS.parent
NAMES = ['tam-shell', 'tam-menu-select', 'tam-menu-timezone', 'tam-agent',
         'tam-default-agent', 'tam-launch-floating-terminal-with-presentation',
         'tam-audio-input-set-default',
         'tam-cmd-present', 'tam-launch-tui', 'tam-notification-send',
         'tam-qmlcache-purge', 'tam-restart-shell']


class DesktopHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.staging = tempfile.TemporaryDirectory(prefix='tam-desktop-install-')
        cls.addClassCleanup(cls.staging.cleanup)
        cls.prefix = Path(cls.staging.name) / 'usr'
        for name in NAMES:
            subprocess.run(['make', 'install', f'PREFIX={cls.prefix}'],
                           cwd=COMMANDS / name, capture_output=True, check=True)
        shutil.copy2(PRODUCT / 'desktop/menu/tam-menu', cls.prefix / 'bin/tam-menu')

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tam-desktop-test-')
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.bin = self.temp / 'bin'
        self.bin.mkdir()
        self.log = self.temp / 'calls.jsonl'
        self.home = self.temp / 'home'
        self.home.mkdir()
        self.config = self.temp / 'config'
        self.real_shell = self.temp / 'immutable-shell'
        self.real_shell.mkdir()
        (self.real_shell / 'shell.qml').touch()
        managed_shell = self.temp / 'share/tamlinux/shell'
        managed_shell.parent.mkdir(parents=True)
        managed_shell.symlink_to(self.real_shell, target_is_directory=True)
        self.env = {
            'HOME': str(self.home), 'XDG_CONFIG_HOME': str(self.config),
            'XDG_DATA_HOME': str(self.temp / 'share'),
            'XDG_RUNTIME_DIR': str(self.temp / 'runtime'),
            'XDG_CACHE_HOME': str(self.temp / 'cache'),
            'TMPDIR': str(self.temp), 'WAYLAND_DISPLAY': 'wayland-test',
            'PATH': f'{self.prefix}/bin:{self.bin}', 'TEST_LOG': str(self.log),
        }
        for program in ('readlink', 'ls', 'grep', 'head', 'timeout', 'mktemp',
                        'rm', 'cat', 'sleep', 'perl', 'basename', 'jq',
                        'find', 'sha1sum', 'cut', 'dirname', 'mkdir', 'mv', 'awk'):
            target = shutil.which(program)
            if not target:
                raise RuntimeError(f'Helper tests require {program}')
            (self.bin / program).symlink_to(target)
        # Every effectful boundary is recorded; none invokes a desktop,
        # authorization service or coding agent from the user's session.
        source = f'#!{sys.executable}\n' + '''
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['TEST_LOG'], 'a') as out:
    out.write(json.dumps({'name': name, 'args': args, 'cwd': os.getcwd(),
                          'display': os.environ.get('WAYLAND_DISPLAY')}) + '\\n')
if name == 'qs':
    status = int(os.environ.get('TEST_QS_STATUS', '0'))
    if status: sys.exit(status)
    if args[6:8] == ['menu', 'open']:
        payload = json.loads(args[8])
        if not os.environ.get('TEST_MENU_CANCEL'):
            pathlib.Path(payload['selectionFile']).write_text(
                os.environ.get('TEST_MENU_SELECTION', 'UTC'))
        pathlib.Path(payload['doneFile']).touch()
    else:
        print(os.environ.get('TEST_QS_OUTPUT', 'pong'))
elif name == 'timedatectl':
    if args == ['list-timezones']: print('UTC\\nAmerica/New_York')
    else: sys.exit(int(os.environ.get('TEST_TIMEZONE_STATUS', '0')))
elif name == 'busctl': print('u 42')
elif name == 'mise':
    key = 'TEST_MISE_WHERE_STATUS' if args[0] == 'where' else 'TEST_MISE_USE_STATUS'
    sys.exit(int(os.environ.get(key, '0')))
elif name == 'wpctl': sys.exit(int(os.environ.get('TEST_AUDIO_STATUS', '0')))
elif name == 'pactl':
    if args == ['list', 'short', 'source-outputs']:
        print(os.environ.get('TEST_SOURCE_OUTPUTS', ''))
    else: sys.exit(int(os.environ.get('TEST_AUDIO_STATUS', '0')))
elif name == 'setsid': os.execvp(args[0], args)
elif name == 'uwsm-app':
    assert args[0] == '--'
    os.execvp(args[1], args[1:])
'''
        for program in ('qs', 'timedatectl', 'busctl', 'setsid', 'uwsm-app',
                        'xdg-terminal-exec', 'codex', 'mise', 'wpctl', 'pactl'):
            path = self.bin / program
            path.write_text(source)
            path.chmod(0o755)
        path = self.bin / 'systemctl'
        path.write_text(source)
        path.chmod(0o755)

    def run_command(self, name, *args, input=None, **environment):
        return subprocess.run([str(self.prefix / 'bin' / name), *args],
                              cwd=self.home, env=self.env | environment,
                              input=input, capture_output=True, text=True, timeout=10)

    def calls(self, name):
        if not self.log.exists():
            return []
        return [call for line in self.log.read_text().splitlines()
                if (call := json.loads(line))['name'] == name]

    def choose_agent(self, value):
        path = self.config / 'tamlinux/defaults/agent'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n')

    def test_ipc_uses_resolved_package_path_and_discrete_arguments(self):
        args = ['notifications', 'show', '--data', 'space and \"quotes\"', 'line\nbreak']
        result = self.run_command('tam-shell', *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'pong\n')
        call = self.calls('qs')[0]
        self.assertEqual(call['args'], ['ipc', '-n', '-p', str(self.real_shell),
                                       'call', '--', *args])

    def test_ipc_missing_host_fails_and_quiet_mode_succeeds(self):
        result = self.run_command('tam-shell', 'menu', 'ping',
                                  TAMLINUX_SHELL_DIR=str(self.temp / 'missing'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('config not found', result.stderr)
        result = self.run_command('tam-shell', '-q', 'menu', 'ping',
                                  TAMLINUX_SHELL_DIR=str(self.temp / 'missing'))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        self.assertFalse(self.calls('qs'))

    def test_ipc_reports_target_method_and_connection_failures(self):
        for output in ('Target not found.', 'Function not found.',
                       'Not ready to accept queries yet'):
            with self.subTest(output=output):
                result = self.run_command('tam-shell', 'menu', 'ping', TEST_QS_OUTPUT=output)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr)
                result = self.run_command('tam-shell', '-q', 'menu', 'ping', TEST_QS_OUTPUT=output)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        result = self.run_command('tam-shell', 'menu', 'ping', TEST_QS_STATUS='4')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('not running', result.stderr)

    def test_ipc_timeout_reports_unresponsive_host(self):
        self.stub_sleeping_qs()
        result = self.run_command('tam-shell', 'menu', 'ping', TAMLINUX_SHELL_IPC_TIMEOUT='0.05s')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('not responding', result.stderr)

    def stub_sleeping_qs(self):
        (self.bin / 'qs').write_text(f'#!{sys.executable}\nimport time\ntime.sleep(5)\n')

    def test_selection_preserves_unicode_options_and_cleans_result_files(self):
        options = ['󰢌\tA label\tDetails', 'Quotes " and spaces', '東京']
        result = self.run_command('tam-menu-select', 'Choose "one"', *options,
                                  '--', '--width', '520', '--maxheight', '480',
                                  TEST_MENU_SELECTION='東京')
        self.assertEqual((result.returncode, result.stdout), (0, '東京'), result.stderr)
        payload = json.loads(self.calls('qs')[0]['args'][8])
        self.assertEqual(payload['options'], options)
        self.assertEqual(payload['prompt'], 'Choose "one"')
        self.assertEqual((payload['width'], payload['maxHeight']), (520, 480))
        self.assertFalse(Path(payload['selectionFile']).exists())
        self.assertFalse(Path(payload['doneFile']).exists())

    def test_selection_cancel_does_not_change_timezone(self):
        result = self.run_command('tam-menu-timezone', TEST_MENU_CANCEL='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([c['args'] for c in self.calls('timedatectl')], [['list-timezones']])
        self.assertFalse(self.calls('busctl'))

    def test_timezone_chain_reads_choices_applies_selection_and_confirms(self):
        result = self.run_command('tam-menu-timezone', TEST_MENU_SELECTION='America/New_York')
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(self.calls('qs')[0]['args'][8])
        self.assertEqual(payload['options'], ['UTC', 'America/New_York'])
        self.assertEqual([c['args'] for c in self.calls('timedatectl')],
                         [['list-timezones'], ['set-timezone', 'America/New_York']])
        bus = self.calls('busctl')[0]['args']
        self.assertEqual(bus[8], 'tamlinux-action')
        self.assertEqual(bus[11], 'Timezone is now set to America/New_York')

    def test_timezone_failure_does_not_send_success_toast(self):
        result = self.run_command('tam-menu-timezone', TEST_TIMEZONE_STATUS='6')
        self.assertEqual(result.returncode, 6)
        self.assertFalse(self.calls('busctl'))

    def test_no_agent_is_selected_on_a_clean_host(self):
        result = self.run_command('tam-agent', '--current')
        self.assertEqual((result.returncode, result.stdout), (0, ''))
        result = self.run_command('tam-agent', '--pick')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('qs')[0]['args'][6:], ['menu', 'summon', 'setup.default.agent'])
        self.assertFalse(self.calls('xdg-terminal-exec'))

    def test_agent_launch_preserves_prompt_arguments_and_work_directory(self):
        self.choose_agent('codex')
        work = self.home / 'Work'
        work.mkdir()
        prompt = '--help; $(touch NEVER)\nnext line'
        result = self.run_command('tam-agent', '--prompt', prompt)
        self.assertEqual(result.returncode, 0, result.stderr)
        terminal = self.calls('xdg-terminal-exec')[0]
        self.assertEqual(terminal['args'], ['--app-id=org.tamlinux.agent', '-e',
                                           'codex', '--approve-for-me', '--', prompt])
        self.assertEqual(terminal['cwd'], str(work))
        self.assertFalse(self.calls('codex'))
        self.assertFalse((work / 'NEVER').exists())

    def test_unavailable_or_unsupported_agent_does_not_launch(self):
        for choice in ('not-installed', 'qs'):
            with self.subTest(choice=choice):
                self.choose_agent(choice)
                result = self.run_command('tam-agent')
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.calls('xdg-terminal-exec'))

    def test_command_presence_checks_all_requested_programs(self):
        self.assertEqual(self.run_command('tam-cmd-present', 'codex', 'qs').returncode, 0)
        self.assertNotEqual(self.run_command('tam-cmd-present', 'qs', 'absent').returncode, 0)

    def test_retired_openclaw_selection_never_launches_even_when_installed(self):
        for name in ('openclaw', 'tam-launch-openclaw'):
            shutil.copy2(self.bin / 'codex', self.bin / name)
        self.choose_agent('openclaw')
        selection = self.config / 'tamlinux/defaults/agent'
        for flags in ((), ('--inline', '--prompt', 'preserve this prompt')):
            with self.subTest(flags=flags):
                result = self.run_command('tam-agent', *flags)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Unsupported default agent: openclaw', result.stderr)
                self.assertFalse(self.log.exists(), 'retired agent must not launch any process')
                self.assertEqual(selection.read_text(), 'openclaw\n')

    def test_agent_default_reader_uses_same_xdg_state_and_preserves_unset(self):
        self.assertEqual(self.run_command('tam-default-agent').stdout, '')
        self.assertFalse((self.config / 'tamlinux/defaults/agent').exists())
        self.choose_agent('codex')
        self.assertEqual(self.run_command('tam-default-agent').stdout, 'codex\n')
        self.assertEqual(self.run_command('tam-agent', '--current').stdout, 'codex\n')
        fallback = self.home / '.config/tamlinux/defaults/agent'
        fallback.parent.mkdir(parents=True)
        fallback.write_text('pi\n')
        self.assertEqual(self.run_command('tam-default-agent', XDG_CONFIG_HOME='').stdout, 'pi\n')

    def test_user_installed_agent_aliases_select_canonical_values_without_mise(self):
        directory = self.home / '.local/bin'
        directory.mkdir(parents=True)
        for alias, canonical in [('claude-code', 'claude'), ('open-code', 'opencode'),
                                 ('github-copilot', 'copilot'), ('gemini-cli', 'gemini'),
                                 ('oh-my-pi', 'omp'), ('muse-code', 'muse'), ('cursor', 'cursor-agent')]:
            with self.subTest(alias=alias):
                shutil.copy2(self.bin / 'codex', self.bin / canonical)
                (directory / canonical).symlink_to(self.bin / canonical)
                result = self.run_command('tam-default-agent', alias)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.run_command('tam-agent', '--current').stdout, canonical + '\n')
                self.assertEqual(self.run_command('tam-default-agent', '--installed', alias).returncode, 0)
        self.assertFalse(self.calls('mise'))

    def test_missing_agent_installation_is_presented_as_discrete_argv(self):
        result = self.run_command('tam-default-agent', 'codex', TEST_MISE_WHERE_STATUS='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        terminal = self.calls('xdg-terminal-exec')[0]['args']
        self.assertEqual(terminal[-4:], ['argv', 'tam-default-agent', '--install', 'codex'])
        self.assertFalse((self.config / 'tamlinux/defaults/agent').exists())
        self.assertEqual(self.calls('mise')[0]['args'], ['where', 'codex'])

    def test_failed_install_does_not_change_existing_selection(self):
        self.choose_agent('pi')
        result = self.run_command('tam-default-agent', '--install', 'codex', TEST_MISE_USE_STATUS='2')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('default agent is unchanged', result.stderr)
        self.assertEqual(self.run_command('tam-default-agent').stdout, 'pi\n')
        self.assertEqual(self.calls('mise')[0]['args'], ['use', '-g', 'codex'])
        self.assertFalse(self.calls('codex'))
        self.assertFalse(self.calls('xdg-terminal-exec'))

    def test_successful_install_commits_state_then_launches_inline(self):
        self.choose_agent('pi')
        result = self.run_command('tam-default-agent', '--install', 'codex')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_command('tam-default-agent').stdout, 'codex\n')
        self.assertEqual(self.calls('codex')[0]['args'], ['--approve-for-me'])
        self.assertFalse(self.calls('xdg-terminal-exec'))
        self.assertEqual(list((self.config / 'tamlinux/defaults').iterdir()),
                         [self.config / 'tamlinux/defaults/agent'])

    def test_retired_agents_reject_installed_or_unbuilt_stubs_without_effects(self):
        for name in ('openclaw', 'hermes'):
            with self.subTest(agent=name):
                stub = self.bin / name
                stub.write_text('#!/bin/bash\nmise use -g pipx:hermes-agent\n')
                stub.chmod(0o755)
                self.choose_agent(name)
                for args in ((name,), ('--installed', name), ('--install', name)):
                    result = self.run_command('tam-default-agent', *args)
                    self.assertNotEqual(result.returncode, 0)
                result = self.run_command('tam-agent', '--inline', '--prompt', 'a; $(literal)')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.run_command('tam-default-agent').stdout, name + '\n')
                self.assertFalse(self.log.exists(), 'retired stub must never execute or install')

    def test_invalid_default_agent_requests_fail_without_writes_or_installation(self):
        for args in (('--install',), ('--installed',), ('unknown',), ('codex', 'extra'),
                     ('--installed', 'codex', 'extra')):
            with self.subTest(args=args):
                self.assertNotEqual(self.run_command('tam-default-agent', *args).returncode, 0)
        self.assertFalse(self.log.exists())
        self.assertFalse((self.config / 'tamlinux/defaults/agent').exists())

    def test_audio_input_selection_moves_existing_streams_with_literal_arguments(self):
        source = 'alsa_input.literal; $(touch NEVER)'
        result = self.run_command('tam-audio-input-set-default', '42', source,
                                  TEST_SOURCE_OUTPUTS='17\tclient\n29\tother client')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('wpctl')[0]['args'], ['set-default', '42'])
        self.assertEqual([call['args'] for call in self.calls('pactl')],
                         [['set-default-source', source], ['list', 'short', 'source-outputs'],
                          ['move-source-output', '17', source], ['move-source-output', '29', source]])
        self.assertFalse((self.home / 'NEVER').exists())
        self.assertFalse(self.config.exists())

    def test_audio_input_selection_retains_best_effort_behavior_on_provider_failure(self):
        result = self.run_command('tam-audio-input-set-default', '42', 'microphone',
                                  TEST_AUDIO_STATUS='1', TEST_SOURCE_OUTPUTS='17\tclient')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls('pactl')), 3)
        self.assertFalse(self.config.exists())

    def test_audio_input_selection_rejects_missing_arguments_without_calls(self):
        for args in ((), ('42',), ('', 'microphone'), ('42', '')):
            self.assertNotEqual(self.run_command('tam-audio-input-set-default', *args).returncode, 0)
        self.assertFalse(self.log.exists())

    def test_cache_purge_removes_only_selected_plugin_code_entries(self):
        plugins = self.temp / 'plugins'
        plugins.mkdir()
        immutable = self.temp / 'immutable-plugin'
        immutable.mkdir()
        for name in ('Main.qml', 'file with spaces.js', 'module.mjs', 'README.md'):
            (immutable / name).write_text('fixture')
        (plugins / 'fred.demo').symlink_to(immutable, target_is_directory=True)
        cache = self.temp / 'cache/quickshell/qmlcache'
        cache.mkdir(parents=True)
        code_entries = []
        for source in (plugins / 'fred.demo').iterdir():
            stem = hashlib.sha1(str(source).encode()).hexdigest()
            for suffix in ('.qmlc', '.jsc'):
                entry = cache / (stem + suffix)
                entry.write_text('compiled fixture')
                if source.suffix != '.md':
                    code_entries.append(entry)
        unrelated = cache / 'unrelated.qmlc'
        unrelated.write_text('another app')
        result = self.run_command('tam-qmlcache-purge', '-q', str(plugins))
        self.assertEqual((result.returncode, result.stdout), (0, ''), result.stderr)
        self.assertTrue(unrelated.exists())
        self.assertFalse(any(entry.exists() for entry in code_entries))
        self.assertEqual(len(list(cache.iterdir())), 3)  # Unrelated and two non-code entries.
        self.assertTrue((immutable / 'Main.qml').exists())

    def test_shell_restart_uses_try_restart_without_starting_an_inactive_unit(self):
        result = self.run_command('tam-restart-shell')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('systemctl')[0]['args'],
                         ['--user', 'try-restart', 'tamlinux-shell.service'])


if __name__ == '__main__':
    unittest.main()
