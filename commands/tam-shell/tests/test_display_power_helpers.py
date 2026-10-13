"""Staged display/power chains; all devices, IPC, processes and sleep are fixtures."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import test_desktop_helpers as installed

NAMES = '''tam-brightness-display tam-brightness-display-ddc tam-brightness-display-apple
 tam-brightness-keyboard tam-brightness-keyboard-mute tam-hw-display
 tam-hyprland-monitor-focused tam-hyprland-monitor-focused-apple tam-system-lock
 tam-system-sleep-lock tam-system-wake suspend-unless-stay-awake
 tam-launch-screensaver tam-toggle-screensaver tam-screensaver
 tam-hyprland-monitor-clamshell tam-hyprland-monitor-laptop tam-hyprland-monitor-internal
 tam-hyprland-monitor-internal-mirror tam-hyprland-monitor-external-active
 tam-hw-clamshell tam-toggle tam-toggle-enabled tam-hyprland-toggle
 tam-hyprland-toggle-enabled tam-hyprland-toggle-disabled tam-hw-laptop-closed
 tam-hw-external-monitors tam-toggle-idle tam-settings-preserve'''.split()
MONITORS = [dict(name='eDP-1',focused=True,disabled=False,dpmsStatus=True,scale=2,make='Fixture',model='LCD'),
            dict(name='DP-2',focused=False,disabled=False,dpmsStatus=True,scale=1,make='Fixture',model='LCD')]

class DisplayPower(unittest.TestCase):
    run_command = installed.DesktopHelpers.run_command
    calls = installed.DesktopHelpers.calls

    @classmethod
    def setUpClass(cls):
        installed.DesktopHelpers.setUpClass.__func__(cls)
        for name in NAMES:
            subprocess.run(['make','install',f'PREFIX={cls.prefix}'],cwd=installed.COMMANDS/name,capture_output=True,check=True)

    def setUp(self):
        installed.DesktopHelpers.setUp(self)
        runtime = self.temp/'runtime'; runtime.mkdir()
        self.env['XDG_STATE_HOME']=str(self.temp/'state')
        self.env['HYPRLAND_INSTANCE_SIGNATURE']='fixture'
        self.env['TEST_MONITORS']=json.dumps(MONITORS)
        for name in ('python3','flock','free','swapon','zramctl'):
            (self.bin/name).symlink_to(shutil.which(name))
        self.backlight=self.temp/'backlight'; self.backlight.mkdir(); (self.backlight/'intel_backlight').mkdir()
        self.leds=self.temp/'leds'; self.leds.mkdir(); (self.leds/'fixture::kbd_backlight').mkdir()
        self.env['TAMLINUX_BACKLIGHT_PATH']=str(self.backlight)
        self.env['TAMLINUX_LEDS_PATH']=str(self.leds)
        self.env['TAMLINUX_LID_PATH']=str(self.temp/'lid')
        self.env['TAMLINUX_DRM_PATH']=str(self.temp/'drm')
        self.env['TAMLINUX_HYPRLOCK_PAM']=str(self.temp/'no-pam')
        source=f'#!{sys.executable}\n'+'''
import json,os,pathlib,sys
name=pathlib.Path(sys.argv[0]).name; args=sys.argv[1:]
with open(os.environ['TEST_LOG'],'a') as out: out.write(json.dumps({'name':name,'args':args})+'\\n')
if name=='hyprctl':
    if args[0]=='monitors': print(os.environ['TEST_MONITORS'])
    elif args[0]=='activewindow': print('{"class":"fixture"}')
    else: sys.exit(int(os.environ.get('TEST_HYPR_STATUS','0')))
elif name=='brightnessctl':
    if args[-1]=='max': print(os.environ.get('TEST_MAX','100'))
    elif args[-1]=='get': print('40')
    elif args[-1]=='-m': print('fixture,backlight,40,'+os.environ.get('TEST_BRIGHTNESS','40')+'%,100')
    else: sys.exit(int(os.environ.get('TEST_BRIGHTNESS_STATUS','0')))
elif name=='ddcutil':
    if 'detect' in args: print('I2C bus: /dev/i2c-7\\nDRM connector: card0-DP-2')
    elif 'getvcp' in args: print('VCP 10 C 40 100')
    else: sys.exit(int(os.environ.get('TEST_DDC_STATUS','0')))
elif name=='pidof': sys.exit(0 if os.environ.get('TEST_LOCKED') else 1)
elif name=='pgrep': sys.exit(0 if os.environ.get('TEST_EFFECT_RUNNING') and '-t' in args else 1)
elif name=='pidwait': sys.exit(1)
elif name=='pkill': pass
elif name=='setsid': pass
elif name=='busctl': print('t 5000000')
elif name=='systemctl': pass
elif name=='logger': sys.stdin.read()
elif name=='socat': print('openwindow>>42,0,org.tamlinux.screensaver,fixture')
elif name=='xdg-terminal-exec': print('foot.desktop')
elif name=='ttfx': sys.exit(0)
'''
        for name in ('hyprctl','brightnessctl','ddcutil','pidof','pgrep','pidwait','pkill','setsid','hyprlock','busctl','systemctl','logger','socat','xdg-terminal-exec','ttfx'):
            path=self.bin/name
            if path.exists() or path.is_symlink(): path.unlink()
            path.write_text(source); path.chmod(0o755)

    def block_recovery(self):
        path=self.temp/'state/tamlinux/settings-recovery'; path.parent.mkdir(parents=True,exist_ok=True); path.write_text('blocked')

    def pam(self):
        path=self.temp/'pam'; path.touch(); self.env['TAMLINUX_HYPRLOCK_PAM']=str(path)

    def test_internal_low_brightness_step_and_failed_set(self):
        result=self.run_command('tam-brightness-display','--no-osd','+5%',TEST_BRIGHTNESS='3')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn(['-d','intel_backlight','set','4%'],[c['args'] for c in self.calls('brightnessctl')])
        self.assertNotEqual(self.run_command('tam-brightness-display','100%',TEST_BRIGHTNESS_STATUS='1').returncode,0)
        self.assertFalse(self.calls('qs'))

    def test_display_dpms_skip_lit_and_propagate_dispatch_failure(self):
        self.assertEqual(self.run_command('tam-brightness-display','on').returncode,0)
        self.assertFalse([c for c in self.calls('hyprctl') if c['args'][0]=='dispatch'])
        self.assertNotEqual(self.run_command('tam-brightness-display','off',TEST_HYPR_STATUS='1').returncode,0)
        self.assertFalse(self.calls('brightnessctl'))

    def test_ddc_cache_and_failed_write_invalidation(self):
        self.assertEqual(self.run_command('tam-brightness-display-ddc','DP-2').stdout,'40\n')
        self.assertEqual(self.run_command('tam-brightness-display-ddc','DP-2','+5%').stdout,'45\n')
        self.assertIn(['--bus','7','--skip-ddc-checks','--noverify','setvcp','10','45'],[c['args'] for c in self.calls('ddcutil')])
        self.assertNotEqual(self.run_command('tam-brightness-display-ddc','DP-2','100%',TEST_DDC_STATUS='1').returncode,0)
        self.assertFalse((self.temp/'runtime/tam-brightness-display-ddc/DP-2.bus').exists())

    def test_backlight_selector_excludes_touchbar_and_prefers_gmux(self):
        (self.backlight/'appletb_backlight').mkdir(); (self.backlight/'gmux_backlight').mkdir()
        self.assertEqual(self.run_command('tam-hw-display').stdout,'gmux_backlight\n')

    def test_keyboard_zero_range_and_write_failure(self):
        for flags in ({'TEST_MAX':'0'},{'TEST_BRIGHTNESS_STATUS':'1'}):
            self.assertNotEqual(self.run_command('tam-brightness-keyboard','--no-osd','up',**flags).returncode,0)
        self.assertNotEqual(self.run_command('tam-brightness-keyboard','off',TEST_BRIGHTNESS_STATUS='1').returncode,0)
        self.assertEqual(self.run_command('tam-brightness-keyboard','--no-osd','cycle').returncode,0)
        self.assertFalse(self.calls('qs'))

    def test_suspend_uses_shared_marker_and_explicit_override(self):
        self.assertEqual(self.run_command('tam-toggle-idle','stay-awake').returncode,0)
        self.assertEqual(self.run_command('suspend-unless-stay-awake').returncode,0)
        self.assertFalse(self.calls('systemctl'))
        self.assertEqual(self.run_command('tam-toggle-idle','allow-idle').returncode,0)
        self.assertEqual(self.run_command('suspend-unless-stay-awake').returncode,0)
        self.assertEqual(self.calls('systemctl')[-1]['args'],['suspend-then-hibernate'])
        explicit=self.temp/'explicit'; explicit.touch()
        before=len(self.calls('systemctl'))
        self.run_command('suspend-unless-stay-awake',TAMLINUX_STAY_AWAKE_FILE=str(explicit))
        self.assertEqual(len(self.calls('systemctl')),before)

    def test_invalid_stay_awake_override_matches_shell_fallback(self):
        self.run_command('tam-toggle-idle','stay-awake',TAMLINUX_STAY_AWAKE_FILE='relative')
        self.run_command('suspend-unless-stay-awake',TAMLINUX_STAY_AWAKE_FILE='relative')
        self.assertFalse(self.calls('systemctl'))
        self.assertTrue((self.temp/'state/tamlinux/stay-awake').exists())
        self.assertFalse((self.home/'relative').exists())

    def test_lock_missing_pam_stops_before_locker_or_cleanup(self):
        self.assertNotEqual(self.run_command('tam-system-lock').returncode,0)
        self.assertFalse(self.calls('setsid')); self.assertFalse(self.calls('pkill'))

    def test_lock_selects_packaged_default_and_user_config(self):
        self.pam(); self.assertEqual(self.run_command('tam-system-lock').returncode,0)
        self.assertTrue(self.calls('setsid')[0]['args'][-1].endswith('/share/tamlinux/lock/hyprlock.conf'))
        config=self.config/'hypr/hyprlock.conf'; config.parent.mkdir(parents=True); config.write_text('user')
        self.run_command('tam-system-lock')
        self.assertEqual(self.calls('setsid')[-1]['args'][-1],str(config))

    def test_sleep_lock_missing_pam_and_deadline_failure(self):
        self.assertNotEqual(self.run_command('tam-system-sleep-lock','50').returncode,0)
        self.assertFalse(self.calls('setsid'))
        self.pam(); result=self.run_command('tam-system-sleep-lock','100')
        self.assertNotEqual(result.returncode,0); self.assertIn('did not start',result.stderr)
        self.assertTrue(self.calls('setsid')); self.assertFalse(self.calls('systemctl'))

    def test_sleep_lock_running_process_is_only_recorded_observation(self):
        self.pam(); result=self.run_command('tam-system-sleep-lock','500',TEST_LOCKED='1')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(self.calls('setsid')); self.assertFalse(self.calls('systemctl'))

    def test_screensaver_toggle_preserves_and_reader_honors_xdg(self):
        self.assertEqual(self.run_command('tam-toggle-screensaver').returncode,0)
        self.assertTrue((self.temp/'state/tamlinux/toggles/screensaver-off').exists())
        self.assertNotEqual(self.run_command('tam-launch-screensaver').returncode,0)
        self.assertFalse(self.calls('hyprctl'))
        self.assertTrue(list((self.temp/'state/tamlinux/settings-recovery').glob('toggles.*/manifest.json')))

    def test_screensaver_launcher_uses_assets_and_same_output_sibling(self):
        # One monitor/event avoids waiting for another fictitious window.
        result=self.run_command('tam-launch-screensaver','force',TEST_MONITORS=json.dumps(MONITORS[:1]))
        self.assertEqual(result.returncode,0,result.stderr)
        dispatches=[c['args'][1] for c in self.calls('hyprctl') if c['args'][0]=='dispatch']
        self.assertTrue(any('/share/tamlinux/screensaver/foot.ini' in d and '/bin/tam-screensaver' in d for d in dispatches))

    def test_toggle_backup_failure_leaves_marker(self):
        marker=self.temp/'state/tamlinux/toggles/screensaver-off'; marker.parent.mkdir(parents=True); marker.write_text('original')
        self.block_recovery()
        self.assertNotEqual(self.run_command('tam-toggle-screensaver').returncode,0)
        self.assertEqual(marker.read_text(),'original'); self.assertFalse(self.calls('qs'))

    def test_monitor_backup_failure_prevents_disable_and_reload(self):
        self.block_recovery()
        self.assertNotEqual(self.run_command('tam-hyprland-monitor-internal','off').returncode,0)
        self.assertFalse((self.temp/'state/tamlinux/toggles/hypr/internal-monitor-disable.lua').exists())
        self.assertFalse([c for c in self.calls('hyprctl') if c['args'][0]=='reload'])

    def test_unsafe_monitor_and_flag_names_rejected(self):
        monitors=[dict(MONITORS[0],name='eDP-1"; unsafe') ,MONITORS[1]]
        self.assertNotEqual(self.run_command('tam-hyprland-monitor-internal','off',TEST_MONITORS=json.dumps(monitors)).returncode,0)
        self.assertNotEqual(self.run_command('tam-toggle','../escape').returncode,0)
        self.assertFalse((self.temp/'state/tamlinux/escape').exists())

    def test_wake_reconciles_clamshell_after_dpms_without_sleep(self):
        result=self.run_command('tam-system-wake')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(self.calls('brightnessctl')); self.assertFalse(self.calls('systemctl'))
        self.assertFalse([c for c in self.calls('hyprctl') if c['args'][0]=='reload'])

    def test_invalid_apple_brightness_stops_before_native_authorization(self):
        result=self.run_command('tam-brightness-display-apple','$(unsafe)')
        self.assertEqual(result.returncode,2)
        body=(installed.COMMANDS/'tam-brightness-display-apple/tam-brightness-display-apple').read_text()
        self.assertNotIn('sudo ',body)
        self.assertIn('/usr/bin/pkexec /usr/bin/asdcontrol',body)

    def test_screensaver_effect_uses_packaged_text_and_restores_cursor(self):
        result=self.run_command('tam-screensaver',input='x',TEST_EFFECT_RUNNING='1')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(self.calls('ttfx'))
        self.assertTrue(self.calls('ttfx')[0]['args'][1].endswith('/share/tamlinux/screensaver/screensaver.txt'))
        self.assertTrue(any('invisible = false' in ' '.join(c['args']) for c in self.calls('hyprctl')))

    def test_clamshell_preserves_scale_and_flag_then_reopens(self):
        lid=self.temp/'lid/LID0/state'; lid.parent.mkdir(parents=True); lid.write_text('state: closed')
        drm=self.temp/'drm/card0-DP-2/status'; drm.parent.mkdir(parents=True); drm.write_text('connected')
        result=self.run_command('tam-hyprland-monitor-clamshell')
        self.assertEqual(result.returncode,0,result.stderr)
        flag=self.temp/'state/tamlinux/toggles/hypr/internal-monitor-clamshell.lua'
        self.assertIn('disabled = true',flag.read_text())
        self.assertEqual((flag.parent/'internal-monitor-scale').read_text(),'2\n')
        lid.write_text('state: open')
        self.assertEqual(self.run_command('tam-hyprland-monitor-clamshell').returncode,0)
        self.assertFalse(flag.exists())
        self.assertEqual(len(list((self.temp/'state/tamlinux/settings-recovery').glob('monitor.*/manifest.json'))),3)

    def test_clamshell_blocked_snapshot_does_not_replace_old_flag(self):
        lid=self.temp/'lid/LID0/state'; lid.parent.mkdir(parents=True); lid.write_text('state: closed')
        drm=self.temp/'drm/card0-DP-2/status'; drm.parent.mkdir(parents=True); drm.write_text('connected')
        flag=self.temp/'state/tamlinux/toggles/hypr/internal-monitor-clamshell.lua'
        flag.parent.mkdir(parents=True); flag.write_text('original')
        self.block_recovery()
        self.assertNotEqual(self.run_command('tam-hyprland-monitor-clamshell').returncode,0)
        self.assertEqual(flag.read_text(),'original')
        self.assertFalse([c for c in self.calls('hyprctl') if c['args'][0]=='reload'])

    def test_apple_denial_and_failed_retry_in_disposable_instrumented_body(self):
        # Fixed native paths and HID predicates are substituted only in a copy.
        # No authorization service or real hardware is called by this test.
        original=(installed.COMMANDS/'tam-brightness-display-apple/tam-brightness-display-apple').read_text()
        device=self.temp/'hiddev0'; device.touch()
        body=original.replace('/usr/bin/asdcontrol',str(self.bin/'asdcontrol')).replace('/usr/bin/pkexec',str(self.bin/'pkexec'))
        body=body.replace('/dev/usb/hiddev* /dev/hiddev*',str(device)).replace('/dev/hiddev*',str(self.temp)+'/hiddev*').replace('/dev/usb/hiddev*',str(self.temp)+'/hiddev*').replace('-c $cached','-f $cached').replace('-c $device','-f $device')
        body=body.replace("awk -F: '/^\\/dev\\/(usb\\/)?hiddev/{ print $1; exit }'", "awk -F: '{ print $1; exit }'")
        script=self.temp/'apple'; script.write_text(body); script.chmod(0o755)
        driver=self.bin/'asdcontrol'; driver.write_text('#!/bin/bash\nexit 1\n'); driver.chmod(0o755)
        auth=self.bin/'pkexec'; auth.write_text(f'#!{sys.executable}\nimport os,sys\nif os.environ.get("TEST_DENIED"): sys.exit(126)\nif "--detect" in sys.argv: print({str(device)!r}+": Apple")\nelif "--" in sys.argv: sys.exit(1)\nelse: print("BRIGHTNESS=30000")\n'); auth.chmod(0o755)
        denied=subprocess.run([str(script)],env=self.env|{'TEST_DENIED':'1'},capture_output=True,text=True,timeout=5)
        self.assertNotEqual(denied.returncode,0)
        retry=subprocess.run([str(script),'--no-osd','50%'],env=self.env,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(retry.returncode,0)
        read=subprocess.run([str(script)],env=self.env,capture_output=True,text=True,timeout=5)
        self.assertEqual(read.returncode,0,read.stderr); self.assertEqual(read.stdout,'50\n')

if __name__=='__main__': unittest.main()
