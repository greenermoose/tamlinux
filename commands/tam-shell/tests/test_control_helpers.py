"""Retained controls: staged install, private state and recorded native effects."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

import test_desktop_helpers as installed

NAMES = '''tam-settings-preserve tam-network-status tam-network-band
tam-network-password tam-network-qr tam-network-speedtest tam-dns tam-restart-wifi
tam-bluetooth-power tam-bluetooth-device tam-restart-bluetooth tam-powerprofiles-list
tam-powerprofiles-set tam-battery-status tam-system-stats tam-toggle-idle
tam-toggle-nightlight tam-restart-hyprsunset tam-display-text-size tam-weather-location'''.split()
UUID = '11111111-2222-3333-4444-555555555555'


class Controls(unittest.TestCase):
    run_command = installed.DesktopHelpers.run_command
    calls = installed.DesktopHelpers.calls

    @classmethod
    def setUpClass(cls):
        installed.DesktopHelpers.setUpClass.__func__(cls)
        for name in NAMES:
            subprocess.run(['make', 'install', f'PREFIX={cls.prefix}'],
                           cwd=installed.COMMANDS / name, capture_output=True, check=True)

    def setUp(self):
        installed.DesktopHelpers.setUp(self)
        self.env['XDG_STATE_HOME'] = str(self.temp / 'state')
        for name in ('python3', 'sort', 'tr', 'tac', 'stat', 'xargs', 'tee'):
            (self.bin / name).symlink_to(shutil.which(name))
        source = self.recorder_source + '''
elif name == 'nmcli':
    key = ' '.join(args)
    response = json.loads(os.environ.get('TEST_NM_RESPONSES', '{}')).get(key, '')
    print(response, end='\\n' if response else '')
    if args[:2] == ['connection', 'up'] and os.environ.get('TEST_REASSOC_FAIL'): sys.exit(1)
    if os.environ.get('TEST_NM_FAIL') and args == ['-t', '-f', 'UUID,TYPE', 'connection', 'show']: sys.exit(1)
elif name == 'iw': print(os.environ.get('TEST_IW_LINK', 'SSID: Fixture\\nfreq: 5180'))
elif name == 'ip': print(os.environ.get('TEST_ROUTE', ''))
elif name == 'qrencode':
    pathlib.Path(os.environ['TEST_QR_PAYLOAD']).write_text(sys.stdin.read())
    print('  ##  \\n##  ##')
elif name == 'powerprofilesctl':
    if os.environ.get('TEST_POWER_UNAVAILABLE'): sys.exit(1)
    if args == ['list']: print('  performance:\\n* balanced:\\n  power-saver:')
    elif args == ['get']: print('balanced')
    else: sys.exit(int(os.environ.get('TEST_POWER_SET_STATUS', '0')))
elif name == 'gsettings':
    state = pathlib.Path(os.environ['TEST_GTK_STATE'])
    if args[0] == 'get': print("'Sans 11'" if args[2] == 'font-name' else (state.read_text() if state.exists() else '1.0'))
    else:
        status = int(os.environ.get('TEST_GTK_STATUS', '0'))
        if not status and not os.environ.get('TEST_GTK_LOST_WRITE'):
            state.write_text(args[3] if args[0] == 'set' else '1.0')
        sys.exit(status)
elif name == 'dconf': print(os.environ.get('TEST_DCONF_VALUE', ''))
elif name == 'pkill': pass
elif name == 'rfkill': sys.exit(int(os.environ.get('TEST_RFKILL_STATUS', '0')))
elif name == 'bluetoothctl':
    if args == ['list']: print('Controller AA:BB:CC:DD:EE:FF Fixture')
    elif args[0] == 'show': print('Powered: yes')
elif name == 'hyprctl': print(os.environ.get('TEST_TEMPERATURE', '4000'))
elif name == 'upower':
    if args == ['-e']: print('/org/freedesktop/UPower/devices/battery_BAT0')
    else: print('native-path: BAT0\\npercentage: 80%\\nenergy-full: 50 Wh\\nenergy-rate: 0.1 W\\nstate: pending-charge')
elif name == 'curl':
    print(os.environ.get('TEST_CURL_OUTPUT', 'Fixture City, Country'))
elif name == 'systemctl':
    if args[0] == 'is-active': print('active')
elif name == 'cp':
    if os.environ.get('TEST_COPY_FAIL'): sys.exit(1)
    os.execv(os.environ['TEST_REAL_CP'], [os.environ['TEST_REAL_CP'], *args])
'''
        # systemctl was already a recorder; replace it with this expanded one.
        for name in ('nmcli', 'iw', 'ip', 'qrencode', 'powerprofilesctl', 'gsettings',
                     'dconf', 'pkill', 'rfkill', 'bluetoothctl', 'hyprctl', 'upower',
                     'curl', 'systemctl', 'cp'):
            path = self.bin / name
            if path.is_symlink(): path.unlink()
            path.write_text(source)
            path.chmod(0o755)
        self.env['TEST_REAL_CP'] = shutil.which('cp')
        self.env['TEST_QR_PAYLOAD'] = str(self.temp / 'qr-payload')
        self.env['TEST_GTK_STATE'] = str(self.temp / 'gtk-factor')

    def snapshots(self, kind):
        return list((self.temp / 'state/tamlinux/settings-recovery').glob(kind + '.*/manifest.json'))

    def block_recovery(self):
        path = self.temp / 'state/tamlinux/settings-recovery'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('blocked')

    def test_preserve_records_absence_symlink_bytes_and_private_permissions(self):
        target = self.temp / 'target'
        target.write_text('original')
        link = self.temp / 'link'
        link.symlink_to(target)
        result = self.run_command('tam-settings-preserve', 'fixture', '--file', str(link),
                                  '--file', str(self.temp / 'absent'), '--value', 'setting', 'a b')
        self.assertEqual(result.returncode, 0, result.stderr)
        snapshot = Path(result.stdout.strip())
        manifest = json.loads((snapshot / 'manifest.json').read_text())
        self.assertEqual(manifest['files'][0]['symlink'], str(target))
        self.assertEqual((snapshot / '0').read_text(), 'original')
        self.assertFalse(manifest['files'][1]['present'])
        self.assertEqual(manifest['observations']['setting'], 'a b')
        self.assertEqual(snapshot.stat().st_mode & 0o777, 0o700)

    def test_preserve_unreadable_target_fails_without_completed_manifest(self):
        link = self.temp / 'broken'
        link.symlink_to(self.temp / 'absent')
        result = self.run_command('tam-settings-preserve', 'fixture', '--file', str(link))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(result.stdout)
        self.assertFalse(self.snapshots('fixture'))

    def test_idle_and_weather_writes_preserve_previous_states(self):
        result = self.run_command('tam-toggle-idle', 'stay-awake')
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.temp / 'state/tamlinux/stay-awake'
        self.assertTrue(path.exists())
        self.assertFalse(json.loads(self.snapshots('idle')[0].read_text())['files'][0]['present'])
        self.assertEqual(self.run_command('tam-toggle-idle', 'allow-idle').returncode, 0)
        self.assertFalse(path.exists())
        name = 'City; literal "name"'
        result = self.run_command('tam-weather-location', '--set', name, '34.1,-118.5')
        self.assertEqual(result.returncode, 0, result.stderr)
        location = self.temp / 'state/tamlinux/settings/weather.json'
        self.assertEqual(json.loads(location.read_text())['name'], name)
        self.assertEqual(self.run_command('tam-weather-location').stdout, name + '\n')
        self.assertFalse(self.calls('curl'))
        self.assertEqual(self.run_command('tam-weather-location', '--clear').returncode, 0)
        self.assertFalse(location.exists())
        self.assertEqual(len(self.snapshots('weather')), 2)

    def test_settings_backup_failure_prevents_idle_and_weather_changes(self):
        self.block_recovery()
        for name, args in [('tam-toggle-idle', ['stay-awake']),
                           ('tam-weather-location', ['--set', 'City'])]:
            self.assertNotEqual(self.run_command(name, *args).returncode, 0)
        self.assertFalse((self.temp / 'state/tamlinux/stay-awake').exists())
        self.assertFalse((self.temp / 'state/tamlinux/settings/weather.json').exists())

    def test_weather_rejects_invalid_coordinates_before_mutation(self):
        result = self.run_command('tam-weather-location', '--set', 'City', '91,0')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.snapshots('weather'))

    def test_power_profiles_list_state_and_restore_saved_source(self):
        result = self.run_command('tam-powerprofiles-list', '--active-state')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'power-saver\t0\nbalanced\t1\nperformance\t0\n')
        result = self.run_command('tam-powerprofiles-set', 'battery', 'power-saver')
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.temp / 'state/tamlinux/powerprofiles/battery'
        self.assertEqual(path.read_text(), 'power-saver\n')
        self.assertEqual(self.run_command('tam-powerprofiles-set', 'battery').returncode, 0)
        self.assertEqual(self.calls('powerprofilesctl')[-1]['args'], ['set', 'power-saver'])
        self.assertEqual(len(self.snapshots('powerprofiles')), 1)

    def test_power_unavailable_and_backup_failure_do_not_set_or_save(self):
        result = self.run_command('tam-powerprofiles-set', 'ac', 'performance', TEST_POWER_UNAVAILABLE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unavailable', result.stderr)
        self.block_recovery()
        result = self.run_command('tam-powerprofiles-set', 'ac', 'performance')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse([c for c in self.calls('powerprofilesctl') if c['args'][0] == 'set'])
        self.assertFalse((self.temp / 'state/tamlinux/powerprofiles/ac').exists())

    def test_power_failed_set_leaves_previous_preference(self):
        path = self.temp / 'state/tamlinux/powerprofiles/ac'
        path.parent.mkdir(parents=True)
        path.write_text('balanced\n')
        result = self.run_command('tam-powerprofiles-set', 'ac', 'performance', TEST_POWER_SET_STATUS='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_text(), 'balanced\n')
        self.assertEqual(len(self.snapshots('powerprofiles')), 1)

    def terminals(self):
        files = {'alacritty/alacritty.toml': '[font]\nsize = 9\n',
                 'kitty/kitty.conf': 'font_family Fixture\nfont_size 9.0\n',
                 'ghostty/config': 'font-family = Fixture\nfont-size = 9\n',
                 'foot/foot.ini': '[main]\nfont=Fixture:size=9\n'}
        for name, content in files.items():
            path = self.config / name
            path.parent.mkdir(parents=True)
            path.write_text(content)
        return files

    def test_text_size_paired_xdg_writes_snapshot_and_reset(self):
        self.terminals()
        state = self.temp / 'state/tamlinux/shell.toml'
        state.parent.mkdir(parents=True)
        state.write_text('[other]\nvalue = 1\n[font]\nfamily = "Fixture"\n')
        result = self.run_command('tam-display-text-size', '16')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('base-size = 16', state.read_text())
        self.assertIn('value = 1', state.read_text())
        self.assertIn('font_size 12.0', (self.config / 'kitty/kitty.conf').read_text())
        self.assertIn('size = 12', (self.config / 'alacritty/alacritty.toml').read_text())
        self.assertIn('font-size = 12', (self.config / 'ghostty/config').read_text())
        self.assertIn(':size=12', (self.config / 'foot/foot.ini').read_text())
        manifest = json.loads(self.snapshots('text-size')[0].read_text())
        self.assertEqual(len(manifest['files']), 5)
        self.assertEqual(manifest['observations'], {'gtk-factor': '1.0', 'gtk-user-value': ''})
        self.assertIn(['set', 'org.gnome.desktop.interface', 'text-scaling-factor', '1.3636'],
                      [c['args'] for c in self.calls('gsettings')])
        result = self.run_command('tam-display-text-size', 'reset')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('base-size', state.read_text())
        self.assertIn('font_size 9.0', (self.config / 'kitty/kitty.conf').read_text())
        self.assertEqual(len(self.snapshots('text-size')), 2)

    def test_text_backup_failure_leaves_every_file_and_gtk_unmodified(self):
        files = self.terminals()
        self.block_recovery()
        result = self.run_command('tam-display-text-size', '16')
        self.assertNotEqual(result.returncode, 0)
        for name, content in files.items(): self.assertEqual((self.config / name).read_text(), content)
        self.assertFalse([c for c in self.calls('gsettings') if c['args'][0] != 'get'])
        self.assertFalse(self.calls('qs'))

    def test_text_gtk_failed_or_lost_commit_preserves_every_file(self):
        files = self.terminals()
        for env in ({'TEST_GTK_STATUS': '1'}, {'TEST_GTK_LOST_WRITE': '1'}):
            result = self.run_command('tam-display-text-size', '16', **env)
            self.assertNotEqual(result.returncode, 0)
            for name, content in files.items():
                self.assertEqual((self.config / name).read_text(), content)
        self.assertFalse(self.calls('qs'))

    def band_env(self):
        return {'TEST_NM_RESPONSES': json.dumps({
            '-e no -g DEVICE,TYPE,STATE device status': 'wlan0:wifi:connected',
            '-e no -g GENERAL.CONNECTION device show wlan0': 'Fixture',
            '-e no -g 802-11-wireless.band connection show Fixture': '',
            '-e no -g FREQ,SSID dev wifi list ifname wlan0 --rescan no': '2412 MHz:Fixture\n5180 MHz:Fixture'})}

    def test_band_available_pin_and_failed_reassociation_restores_previous(self):
        result = self.run_command('tam-network-band', **self.band_env())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('available\t2.4 5', result.stdout)
        result = self.run_command('tam-network-band', '2.4', TEST_REASSOC_FAIL='1', **self.band_env())
        self.assertNotEqual(result.returncode, 0)
        mutations = [c['args'] for c in self.calls('nmcli') if c['args'][:2] == ['connection', 'modify']]
        self.assertEqual(mutations, [['connection', 'modify', 'Fixture', '802-11-wireless.band', 'bg'],
                                     ['connection', 'modify', 'Fixture', '802-11-wireless.band', '']])
        self.assertEqual(len(self.snapshots('network-band')), 1)

    def test_band_absent_target_and_preservation_failure_never_modify(self):
        self.assertNotEqual(self.run_command('tam-network-band', '6', **self.band_env()).returncode, 0)
        self.block_recovery()
        self.assertNotEqual(self.run_command('tam-network-band', '5', **self.band_env()).returncode, 0)
        self.assertFalse([c for c in self.calls('nmcli') if c['args'][:2] == ['connection', 'modify']])

    def test_wifi_qr_escapes_secrets_and_rejects_enterprise(self):
        responses = {'--get-values GENERAL.CON-UUID device show wlan0': UUID,
                     '--show-secrets --escape no --get-values 802-11-wireless.ssid,802-11-wireless-security.key-mgmt,802-11-wireless-security.psk,802-11-wireless.hidden,802-11-wireless-security.wep-key0 connection show uuid ' + UUID:
                     'Fixture:City\nwpa-psk\np;ass\\word\nyes\n'}
        result = self.run_command('tam-network-qr', '--meta', 'wlan0', TEST_NM_RESPONSES=json.dumps(responses))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'meta\twlan0\tWPA\tFixture:City\n010\n101\n')
        self.assertEqual((self.temp / 'qr-payload').read_text(), 'WIFI:T:WPA;S:Fixture\\:City;P:p\\;ass\\\\word;H:true;;')
        key = list(responses)[1]
        responses[key] = 'Fixture\nwpa-eap\n\nno\n'
        self.assertNotEqual(self.run_command('tam-network-qr', 'wlan0', TEST_NM_RESPONSES=json.dumps(responses)).returncode, 0)
        self.assertEqual(len(self.calls('qrencode')), 1)

    def test_wifi_password_uses_uuid_literal_interface(self):
        responses = {'--get-values GENERAL.CON-UUID device show wlan0': UUID,
                     '--show-secrets --escape no --get-values 802-11-wireless-security.key-mgmt,802-11-wireless-security.psk,802-11-wireless-security.wep-key0 connection show uuid ' + UUID: 'wpa-psk\nsecret\n'}
        result = self.run_command('tam-network-password', 'wlan0', TEST_NM_RESPONSES=json.dumps(responses))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'secret\n')

    def test_bluetooth_validation_power_and_failed_unblock(self):
        self.assertNotEqual(self.run_command('tam-bluetooth-device', 'pair', 'literal; bad').returncode, 0)
        self.assertFalse(self.calls('bluetoothctl'))
        self.assertEqual(self.run_command('tam-bluetooth-power', 'off').returncode, 0)
        self.assertEqual(self.calls('rfkill')[0]['args'], ['block', 'bluetooth'])
        self.assertNotEqual(self.run_command('tam-bluetooth-power', 'on', TEST_RFKILL_STATUS='1').returncode, 0)
        self.assertFalse(self.calls('bluetoothctl'))

    def test_battery_holding_uses_xdg_independent_kernel_fixture(self):
        supplies = self.temp / 'supplies'
        for folder, files in {'BAT0': {'charge_control_end_threshold': '80', 'power_now': '100000'},
                              'AC': {'type': 'Mains', 'online': '1'}}.items():
            for name, content in files.items():
                path = supplies / folder / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
        result = self.run_command('tam-battery-status', '--shell', TAMLINUX_POWER_SUPPLY_PATH=str(supplies))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('state\tholding', result.stdout)
        self.assertIn('threshold\t80%', result.stdout)

    def test_nightlight_status_and_invalid_speedtest_do_not_network(self):
        result = self.run_command('tam-toggle-nightlight', '--status')
        self.assertEqual(json.loads(result.stdout), {'enabled': True, 'temperature': 4000})
        self.assertEqual(self.run_command('tam-network-speedtest', 'invalid').returncode, 2)
        self.assertFalse(self.calls('curl'))

    def dns_fixture(self):
        # Only this disposable body maps fixed root paths/authorization to a
        # recorded environment. The shipped command has no root path override.
        source = (self.prefix / 'bin/tam-dns').read_text()
        self.dns_dir = self.temp / 'dns'
        self.dns_dir.mkdir()
        self.dns_nm = self.dns_dir / 'nm.conf'
        self.dns_resolved = self.dns_dir / 'resolved.conf'
        self.dns_resolved.write_text('[Resolve]\nDNS=192.0.2.1\n# original\n')
        source = source.replace('RECOVERY_DIR=/var/lib/tamlinux/network-recovery',
                                'RECOVERY_DIR=' + str(self.dns_dir / 'recovery'))
        source = source.replace('NM_DNS_CONF=/etc/NetworkManager/conf.d/20-tamlinux-dns.conf',
                                'NM_DNS_CONF=' + str(self.dns_nm))
        source = source.replace('RESOLVED_CONF=/etc/systemd/resolved.conf', 'RESOLVED_CONF=' + str(self.dns_resolved))
        source = source.replace('export PATH=/usr/bin:/bin', 'export PATH=' + self.env['PATH'])
        source = source.replace('require_root "$provider"', ': # recorded root authorization boundary')
        path = self.temp / 'dns-body'
        path.write_text(source)
        path.chmod(0o755)
        self.dns_script = path
        self.dns_responses = {'-t -f UUID,TYPE connection show': UUID + ':802-11-wireless\n' +
                             '66666666-7777-8888-9999-aaaaaaaaaaaa:vpn'}
        for field, value in {'ipv4.dns': '192.0.2.53', 'ipv6.dns': '',
                             'ipv4.ignore-auto-dns': 'no', 'ipv6.ignore-auto-dns': 'no'}.items():
            self.dns_responses['-e no -g ' + field + ' connection show uuid ' + UUID] = value

    def run_dns_body(self, provider, **env):
        return subprocess.run([str(self.dns_script), provider], env=self.env | {
            'TEST_NM_RESPONSES': json.dumps(self.dns_responses)} | env,
            capture_output=True, text=True, timeout=10)

    def test_dns_paired_files_profiles_preserved_before_fixed_writes(self):
        self.dns_fixture()
        result = self.run_dns_body('Google')
        self.assertEqual(result.returncode, 0, result.stderr)
        snapshot, = (self.dns_dir / 'recovery').glob('dns.*')
        self.assertTrue((snapshot / '0.absent').exists())
        self.assertEqual((snapshot / '1.content').read_text(), '[Resolve]\nDNS=192.0.2.1\n# original\n')
        self.assertEqual((snapshot / UUID / 'ipv4.dns').read_text(), '192.0.2.53\n')
        self.assertIn('servers=8.8.8.8', self.dns_nm.read_text())
        self.assertIn('DNS=8.8.8.8#dns.google', self.dns_resolved.read_text())
        self.assertEqual(len([c for c in self.calls('nmcli') if c['args'][:2] == ['connection', 'modify']]), 1)

    def test_dns_backup_or_profile_query_failure_stops_every_mutation(self):
        self.dns_fixture()
        before = self.dns_resolved.read_text()
        for env in ({'TEST_COPY_FAIL': '1'}, {'TEST_NM_FAIL': '1'}):
            result = self.run_dns_body('Google', **env)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.dns_resolved.read_text(), before)
            self.assertFalse(self.dns_nm.exists())
        self.assertFalse([c for c in self.calls('nmcli') if c['args'][:2] == ['connection', 'modify']])

    def test_dns_source_mutation_refuses_untrusted_copy(self):
        # No authorization recorder is substituted in this installed-copy test.
        if os.geteuid() == 0: self.skipTest('root cannot test unprivileged authorization')
        result = self.run_command('tam-dns', 'Google')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('only the Nix-store copy', result.stderr)
        self.assertFalse(self.calls('nmcli'))


if __name__ == '__main__':
    unittest.main()
