"""Real source snapshots, overrides and rollback without touching the desktop."""
from importlib.machinery import SourceFileLoader
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_loader('dev',SourceFileLoader('dev',str(Path(__file__).parents[1]/'tam-dev')))
dev=importlib.util.module_from_spec(spec);spec.loader.exec_module(dev)

class Development(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.repo=self.root/'workspace/tamlinux'
        command=self.repo/'commands/tam-demo';command.mkdir(parents=True)
        (command/'tam-demo').write_text('#!'+shutil.which('sh')+'\necho original\n');(command/'tam-demo').chmod(0o755)
        (command/'Makefile').write_text('install:\n\tinstall -Dm755 tam-demo $(PREFIX)/bin/tam-demo\ncheck:\n\t./tam-demo\n')
        subprocess.run(['git','init','-q',str(self.repo)],check=True)
        self.git('config','user.name','Fixture');self.git('config','user.email','fixture@example.invalid')
        self.git('add','--','commands');self.git('commit','-qm','Initial')
        self.env=patch.dict(os.environ,{'HOME':str(self.root/'home'),'XDG_STATE_HOME':str(self.root/'state')})
        self.env.start();self.addCleanup(self.env.stop)

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],text=True).strip()

    def test_dirty_trial_is_explicit_cached_and_reversible(self):
        source=self.repo/'commands/tam-demo/tam-demo';source.write_text('#!'+shutil.which('sh')+'\necho changed\n')
        record=dev.build(self.repo.parent,'command:tam-demo')
        self.assertTrue(record['dirty'])
        self.assertEqual(subprocess.check_output([str(Path(record['prefix'])/'bin/tam-demo')],text=True),'changed\n')
        dev.check(record)
        with patch.object(dev,'run',wraps=dev.run) as invoked:
            self.assertEqual(dev.build(self.repo.parent,'command:tam-demo'),record)
            dev.check(record)
            self.assertFalse(any(call.args[0]=='make' for call in invoked.call_args_list))
        dev.trial(record)
        target=Path.home()/'.local/dev/bin/tam-demo'
        self.assertTrue(target.is_symlink())
        dev.stop('command:tam-demo');self.assertFalse(target.exists())
        self.assertEqual(self.git('log','--format=%s'), 'Initial')

    def test_command_checks_keep_sibling_dependencies_and_development_headers(self):
        sibling=self.repo/'commands/tam-sibling';sibling.mkdir();(sibling/'value').write_text('dependency')
        record=dev.build(self.repo.parent,'command:tam-demo')
        self.assertEqual((Path(record['source'])/'commands/tam-sibling/value').read_text(),'dependency')
        headers=Path.home()/'.local/dev/include';headers.mkdir(parents=True)
        header=headers/'libtam.h';header.write_text('first interface')
        before=dev.toolchain_key('tam');header.write_text('changed interface')
        self.assertNotEqual(before,dev.toolchain_key('tam'))

    def test_later_override_is_preserved(self):
        record=dev.build(self.repo.parent,'command:tam-demo');dev.trial(record)
        target=Path.home()/'.local/dev/bin/tam-demo';target.unlink();target.write_text('later work')
        with self.assertRaisesRegex(dev.DevError,'changed since trial'):
            dev.stop('command:tam-demo')
        self.assertEqual(target.read_text(),'later work')

    def test_preexisting_links_and_regular_files_are_restored(self):
        target=Path.home()/'.local/dev/bin/tam-demo';target.parent.mkdir(parents=True)
        target.symlink_to('/old/development-command')
        record=dev.build(self.repo.parent,'command:tam-demo');dev.trial(record);dev.stop('command:tam-demo')
        self.assertEqual(os.readlink(target),'/old/development-command')
        target.unlink();target.write_text('keep')
        dev.trial(record);self.assertTrue(target.is_symlink())
        dev.stop('command:tam-demo');self.assertEqual(target.read_text(),'keep')

    def test_source_escape_and_unknown_selector_refused(self):
        outside=self.root/'outside';outside.write_text('outside')
        (self.repo/'commands/tam-demo/escape').symlink_to(outside)
        with self.assertRaises(dev.DevError):dev.build(self.repo.parent,'command:tam-demo')
        with self.assertRaises(dev.DevError):dev.select(self.repo.parent,'command:../../etc')

    def test_live_launch_failure_restores_packaged_service(self):
        record={'component':'shell','makeDirectory':None,'source':str(self.root),'files':{}}
        endpoint=Path.home()/'.local/share/tamlinux/shell';endpoint.parent.mkdir(parents=True)
        endpoint.symlink_to('/packaged/shell')
        ipc=Path.home()/'.local/bin/tam-shell';ipc.parent.mkdir(parents=True);ipc.write_text('# fixture')
        with patch.object(dev,'gui',return_value=(['missing'],{})), patch.object(dev,'run',return_value='Development live routing: v1') as run, \
             patch.object(dev.subprocess,'Popen',side_effect=OSError('launch failed')):
            with self.assertRaises(OSError):dev.trial(record,True)
        self.assertEqual(run.call_args_list[-1].args,('systemctl','--user','start','tamlinux-shell.service'))
        self.assertEqual(os.readlink(endpoint),'/packaged/shell')

    def test_previews_do_not_inherit_live_settings_paths(self):
        source=self.root/'preview-source';source.mkdir()
        record={'component':'app:keybindings','source':str(source),'sourceKey':'dev-identity'}
        with patch.dict(os.environ,{'TAMLINUX_BAR_LAYOUT':'/live/layout','TAMLINUX_SERVICES':'polkit,clipboard'}), \
             patch.object(dev,'quickshell',return_value=('/selected/quickshell',{})):
            command,env=dev.gui(record,False)
        self.assertNotIn('TAMLINUX_BAR_LAYOUT',env)
        self.assertNotIn('TAMLINUX_SERVICES',env)
        self.assertNotEqual(env['HOME'],os.environ['HOME'])
        self.assertEqual(command[0],'/selected/quickshell')

    def test_exited_supervisor_is_not_mistaken_for_running_trial(self):
        import sys,time
        process=subprocess.Popen([sys.executable,'-c','pass'])
        self.addCleanup(process.wait)
        for _ in range(100):
            fields=Path(f'/proc/{process.pid}/stat').read_text().split(') ',1)[1].split()
            if fields[0]=='Z':break
            time.sleep(.01)
        self.assertIsNone(dev.process_id(process.pid))
