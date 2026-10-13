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
         'tam-audio-input-set-default', 'tam-audio-output-set-default',
         'tam-audio-output-sink', 'tam-audio-sink-availability', 'tam-audio-tuning',
         'tam-hw-match', 'tam-restart-audio', 'tam-osd',
         'tam-audio-output-volume', 'tam-audio-output-switch',
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
                        'rm', 'cat', 'sleep', 'perl', 'basename', 'jq', 'date', 'cp',
                        'touch', 'cmp', 'install', 'sed', 'rmdir', 'id',
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
    else:
        response = json.loads(os.environ.get('TEST_AUDIO_RESPONSES', '{}')).get(' '.join(args))
        if response is not None: print(response)
        sys.exit(int(os.environ.get('TEST_AUDIO_STATUS', '0')))
elif name == 'systemctl':
    if args[1] in ('is-active', 'is-enabled'):
        print('inactive' if args[1] == 'is-active' else 'disabled')
        sys.exit(1)
elif name == 'pgrep': sys.exit(1)
elif name == 'match-machine': pass
elif name == 'ls' and args == ['/usr/lib/lv2/lsp-plugins.lv2/limiter_stereo.ttl']:
    sys.exit(int(os.environ.get('TEST_LV2_STATUS', '0')))
elif name == 'sleep': pass
elif name == 'setsid': os.execvp(args[0], args)
elif name == 'uwsm-app':
    assert args[0] == '--'
    os.execvp(args[1], args[1:])
'''
        for program in ('qs', 'timedatectl', 'busctl', 'setsid', 'uwsm-app',
                        'xdg-terminal-exec', 'codex', 'mise', 'wpctl', 'pactl', 'pgrep', 'match-machine'):
            path = self.bin / program
            path.write_text(source)
            path.chmod(0o755)
        self.recorder_source = source
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


    def audio_env(self, responses):
        return {'TEST_AUDIO_RESPONSES': json.dumps(responses)}

    def test_output_selection_moves_apps_but_preserves_dsp_and_easyeffects(self):
        sink = 'literal sink; $(touch NEVER)'
        streams = ('Sink Input #12\n\tapplication.name = "Browser"\n'
                   'Sink Input #13\n\tnode.name = "tamlinux_speaker_tuning_output"\n'
                   'Sink Input #14\n\tapplication.name = "EasyEffects"\n'
                   'Sink Input #15\n\tapplication.name = "Music"\n')
        result = self.run_command('tam-audio-output-set-default', '42', sink,
                                  **self.audio_env({'list sink-inputs': streams}))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('wpctl')[0]['args'], ['set-default', '42'])
        self.assertEqual([c['args'] for c in self.calls('pactl')],
                         [['set-default-sink', sink], ['list', 'sink-inputs'],
                          ['move-sink-input', '12', sink], ['move-sink-input', '15', sink]])
        self.assertFalse((self.home / 'NEVER').exists())

    def test_output_selection_missing_args_and_best_effort_failure(self):
        for args in ((), ('42',), ('', 'sink'), ('42', '')):
            self.assertNotEqual(self.run_command('tam-audio-output-set-default', *args).returncode, 0)
        self.assertFalse(self.log.exists())
        self.assertEqual(self.run_command('tam-audio-output-set-default', '42', 'sink',
                                         TEST_AUDIO_STATUS='1').returncode, 0)

    def test_output_resolver_keeps_selected_physical_output(self):
        result = self.run_command('tam-audio-output-sink',
                                  **self.audio_env({'get-default-sink': 'alsa_output.headphones'}))
        self.assertEqual(result.stdout, 'alsa_output.headphones\n')
        self.assertEqual(len(self.calls('pactl')), 1)

    def test_output_resolver_follows_tuning_and_easyeffects(self):
        for sink, property_line in [('tamlinux_speaker_tuning', 'node.name = "tamlinux_speaker_tuning_output"'),
                                    ('easyeffects_sink', 'application.name = "EasyEffects"')]:
            with self.subTest(sink=sink):
                response = {'list sink-inputs': 'Sink Input #1\n\tSink: 7\n\t' + property_line,
                            'list sinks short': '7\talsa_output.speakers\tother'}
                result = self.run_command('tam-audio-output-sink', sink, **self.audio_env(response))
                self.assertEqual(result.stdout, 'alsa_output.speakers\n')
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_output_resolver_idle_and_no_default_fallback(self):
        self.assertEqual(self.run_command('tam-audio-output-sink', 'idle_dsp').stdout, 'idle_dsp\n')
        self.assertEqual(self.run_command('tam-audio-output-sink', TEST_AUDIO_STATUS='1').stdout, '\n')

    def fixture_tuning(self):
        data = self.temp / 'audio-data'
        shutil.copytree(self.prefix / 'share/tamlinux/audio', data)
        shipped = data / 'tunings'
        shutil.rmtree(shipped)
        tuning = shipped / 'fixture'
        tuning.mkdir(parents=True)
        (tuning / 'tuning.conf').write_text(
            'description="Fixture speakers"\nmatch_command="' + str(self.bin / 'match-machine') +
            '"\nsink_pattern="^alsa_output.speakers$"\n')
        (tuning / 'filter-chain.conf').write_text('target.object = "@SPEAKER_SINK@"\n')
        for program in ('ls', 'sleep'):
            path = self.bin / program
            path.unlink()
            path.write_text(self.recorder_source)
            path.chmod(0o755)
        return data

    def tuning_env(self, data, extra=None):
        responses = {'list sinks short': '1\talsa_output.speakers\n2\ttamlinux_speaker_tuning',
                     'get-default-sink': 'alsa_output.headphones',
                     'list sink-inputs': 'Sink Input #3\n\tSink: 1\n\tnode.name = "tamlinux_speaker_tuning_output"'}
        responses.update(extra or {})
        return self.audio_env(responses) | {'TAMLINUX_AUDIO_DATA': str(data),
                                          'XDG_STATE_HOME': str(self.temp / 'state')}

    def test_availability_uses_tuning_but_keeps_unported_devices(self):
        data = self.fixture_tuning()
        sinks = ('Sink #1\n\tName: alsa_output.speakers\n'
                 'Sink #2\n\tName: alsa_output.headphones\n\tPorts:\n'
                 '\t\theadphone: Headphones (not available)\n\tActive Port: headphone\n'
                 'Sink #3\n\tName: bluetooth.speaker\n'
                 'Sink #4\n\tName: alsa_output.hdmi\n\tPorts:\n'
                 '\t\thdmi: HDMI (available)\n\tActive Port: hdmi\n')
        result = self.run_command('tam-audio-sink-availability', **self.tuning_env(data, {'list sinks': sinks}))
        self.assertEqual(result.stdout, 'alsa_output.speakers\t0\nalsa_output.headphones\t0\n'
                                       'bluetooth.speaker\t1\nalsa_output.hdmi\t1\n')
        self.assertFalse(self.calls('systemctl'))
        self.assertFalse(self.config.exists())

    def test_tuning_packaged_data_and_read_only_no_match(self):
        self.assertTrue((self.prefix / 'share/tamlinux/audio/LICENSE').is_file())
        self.assertIn('tamlinux_speaker_tuning',
                      (self.prefix / 'share/tamlinux/audio/tunings/dell-xps-2026/filter-chain.conf').read_text())
        data = self.temp / 'empty-data'
        (data / 'tunings').mkdir(parents=True)
        result = self.run_command('tam-audio-tuning', 'on', TAMLINUX_AUDIO_DATA=str(data))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No speaker tuning matches', result.stdout)
        self.assertFalse(self.log.exists())
        self.assertFalse(self.config.exists())

    def test_tuning_read_only_fronted_uses_owned_sink_name(self):
        data = self.fixture_tuning()
        result = self.run_command('tam-audio-tuning', 'fronted-sink', **self.tuning_env(data))
        self.assertEqual(result.stdout, 'alsa_output.speakers\n')
        self.assertFalse(self.calls('systemctl'))
        self.assertFalse(self.config.exists())

    def test_tuning_on_preserves_prior_files_and_uses_owned_service(self):
        data = self.fixture_tuning()
        prior = self.config / 'pipewire/tamlinux-speaker-tuning.conf'
        prior.parent.mkdir(parents=True)
        prior.write_text('prior user file')
        inherited = self.config / 'pipewire/omarchy-speaker-tuning.conf'
        inherited.write_text('untouched inherited file')
        result = self.run_command('tam-audio-tuning', 'on', **self.tuning_env(data))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Speakers now play through the tuning', result.stdout)
        backups = list((self.temp / 'state/tamlinux/audio-recovery').glob('tuning.*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / '0').read_text(), 'prior user file')
        self.assertTrue((backups[0] / '1.absent').exists())
        self.assertEqual(inherited.read_text(), 'untouched inherited file')
        fragment = self.config / 'pipewire/tamlinux-speaker-tuning.conf.d/90-tuning.conf'
        self.assertEqual(fragment.read_text(), 'target.object = "alsa_output.speakers"\n')
        unit = self.config / 'systemd/user/tamlinux-speaker-tuning.service'
        self.assertIn('/usr/bin/pipewire -c tamlinux-speaker-tuning.conf', unit.read_text())
        calls = [c['args'] for c in self.calls('systemctl')]
        self.assertIn(['--user', 'restart', 'tamlinux-speaker-tuning.service'], calls)
        self.assertFalse(any('omarchy' in ' '.join(c) for c in calls))

    def test_tuning_missing_lv2_or_backup_failure_cannot_write(self):
        data = self.fixture_tuning()
        result = self.run_command('tam-audio-tuning', 'on', TEST_LV2_STATUS='1', **self.tuning_env(data))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.config.exists())
        self.assertFalse(any(c['args'][1] not in ('is-active', 'is-enabled')
                             for c in self.calls('systemctl')))
        # A non-directory state root reliably reproduces failed recovery creation.
        blocker = self.temp / 'blocked-state'
        blocker.write_text('blocked')
        env = self.tuning_env(data) | {'XDG_STATE_HOME': str(blocker)}
        result = self.run_command('tam-audio-tuning', 'on', **env)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.config.exists())
        self.assertFalse(any(c['args'][1] not in ('is-active', 'is-enabled')
                             for c in self.calls('systemctl')))

    def test_tuning_failed_link_keeps_snapshot_and_removes_attempt(self):
        data = self.fixture_tuning()
        result = self.run_command('tam-audio-tuning', 'on',
                                  **self.tuning_env(data, {'list sink-inputs': ''}))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.config / 'systemd/user/tamlinux-speaker-tuning.service').exists())
        self.assertTrue(list((self.temp / 'state/tamlinux/audio-recovery').glob('tuning.*')))
        self.assertNotIn(['set-default-sink', 'tamlinux_speaker_tuning'],
                         [c['args'] for c in self.calls('pactl')])

    def test_tuning_off_preserves_snapshot_and_unrelated_filters(self):
        data = self.fixture_tuning()
        unit = self.config / 'systemd/user/tamlinux-speaker-tuning.service'
        unit.parent.mkdir(parents=True)
        unit.write_text('previous unit')
        unrelated = self.config / 'pipewire/filter-chain.conf.d/user.conf'
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text('user filter')
        result = self.run_command('tam-audio-tuning', 'off', **self.tuning_env(data,
                                  {'list sinks short': '1\talsa_output.speakers'}))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(unit.exists())
        backup = next((self.temp / 'state/tamlinux/audio-recovery').glob('tuning.*'))
        self.assertEqual((backup / '2').read_text(), 'previous unit')
        self.assertEqual(unrelated.read_text(), 'user filter')

    def test_osd_json_preserves_literal_message(self):
        message = 'quotes " and $(touch NEVER)\nnext line'
        result = self.run_command('tam-osd', '-i', 'volume-high', '-m', message, '-p', '42')
        self.assertEqual(result.returncode, 0, result.stderr)
        call = self.calls('qs')[-1]['args']
        self.assertEqual(call[6:8], ['osd', 'show'])
        payload = json.loads(call[8])
        self.assertEqual((payload['message'], payload['value'], payload['progressText']), (message, '42', '42%'))
        self.assertFalse((self.home / 'NEVER').exists())

    def test_volume_resolves_physical_sink_clamps_and_unmutes(self):
        responses = {'get-default-sink': 'alsa_output.headphones',
                     'get-sink-volume alsa_output.headphones': 'Volume: front-left: 65536 / 98% / 0.00 dB',
                     'get-sink-mute alsa_output.headphones': 'Mute: no'}
        result = self.run_command('tam-audio-output-volume', 'raise', **self.audio_env(responses))
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [c['args'] for c in self.calls('pactl')]
        self.assertIn(['set-sink-mute', 'alsa_output.headphones', '0'], calls)
        self.assertIn(['set-sink-volume', 'alsa_output.headphones', '100%'], calls)
        result = self.run_command('tam-audio-output-volume', '-200', **self.audio_env(responses))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(['set-sink-volume', 'alsa_output.headphones', '0%'],
                      [c['args'] for c in self.calls('pactl')])

    def test_volume_mute_debounce_uses_isolated_runtime_state(self):
        (self.temp / 'runtime').mkdir()
        (self.temp / 'runtime/tam-audio-output-volume-mute-toggle.last').write_text('999999999999999')
        result = self.run_command('tam-audio-output-volume', 'mute-toggle',
                                  **self.audio_env({'get-default-sink': 'alsa_output.headphones'}))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(c['args'][0] == 'set-sink-mute' for c in self.calls('pactl')))

    def test_output_switch_preserves_mute_and_skips_tuning_hardware(self):
        data = self.fixture_tuning()
        sinks = [{'index': 1, 'name': 'alsa_output.speakers', 'ports': []},
                 {'index': 2, 'name': 'tamlinux_speaker_tuning', 'ports': [], 'description': 'Speakers',
                  'volume': {'left': {'value_percent': '100%'}}},
                 {'index': 3, 'name': 'alsa_output.headphones', 'ports': [], 'description': 'Headphones',
                  'volume': {'left': {'value_percent': '30%'}}}]
        env = self.tuning_env(data, {'-f json list sinks': json.dumps(sinks),
              'get-default-sink': 'alsa_output.headphones',
              'get-sink-volume alsa_output.speakers': 'Volume: left: 100 / 80% / 0 dB',
              'get-sink-mute alsa_output.speakers': 'Mute: yes'})
        result = self.run_command('tam-audio-output-switch', **env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(['set-default-sink', 'tamlinux_speaker_tuning'],
                      [c['args'] for c in self.calls('pactl')])
        self.assertFalse(any(c['args'][0] == 'set-sink-mute' for c in self.calls('pactl')))
        payload = json.loads(self.calls('qs')[-1]['args'][8])
        self.assertEqual((payload['icon'], payload['message']), ('volume-muted', 'Speakers'))

    def test_audio_restart_healthy_only_uses_recorded_services(self):
        path = self.bin / 'sleep'
        path.unlink()
        path.write_text(self.recorder_source)
        path.chmod(0o755)
        result = self.run_command('tam-restart-audio')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('systemctl')[0]['args'], ['--user', 'restart',
                         'wireplumber.service', 'pipewire.service', 'pipewire-pulse.service'])
        self.assertFalse(self.config.exists())

    def test_usb_default_cleanup_backs_up_both_before_selective_edit(self):
        # Source installed function definitions only; do not inspect live /proc or reset hardware.
        definitions = (self.prefix / 'bin/tam-restart-audio').read_text().rsplit('\nrestart_audio_services || true', 1)[0]
        state = self.temp / 'state/wireplumber'
        state.mkdir(parents=True)
        nodes = 'default.configured.audio.sink=alsa_output.usb-test\n'
        nodes += 'default.configured.audio.sink.1=alsa_output.usb-other\nkeep=alsa_output.internal\n'
        routes = 'alsa_card.usb-test=route\nalsa_card.pci-test=keep\n'
        (state / 'default-nodes').write_text(nodes)
        (state / 'default-routes').write_text(routes)
        result = subprocess.run([shutil.which('bash'), '-c', definitions + '\nclear_usb_audio_defaults'],
                                env=self.env | {'XDG_STATE_HOME': str(self.temp / 'state')},
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((state / 'default-nodes').read_text(), 'keep=alsa_output.internal\n')
        self.assertEqual((state / 'default-routes').read_text(), 'alsa_card.pci-test=keep\n')
        self.assertEqual(next(state.glob('default-nodes.bak.*')).read_text(), nodes)
        self.assertEqual(next(state.glob('default-routes.bak.*')).read_text(), routes)
        # A backup error must preserve both originals and stop before either edit.
        (state / 'default-nodes').write_text(nodes)
        (state / 'default-routes').write_text(routes)
        cp = self.bin / 'cp'
        cp.unlink()
        cp.write_text(f'#!{sys.executable}\nimport sys\nsys.exit(1)\n'); cp.chmod(0o755)
        result = subprocess.run([shutil.which('bash'), '-c', definitions + '\nclear_usb_audio_defaults'],
                                env=self.env | {'XDG_STATE_HOME': str(self.temp / 'state')},
                                text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((state / 'default-nodes').read_text(), nodes)
        self.assertEqual((state / 'default-routes').read_text(), routes)


if __name__ == '__main__':
    unittest.main()
