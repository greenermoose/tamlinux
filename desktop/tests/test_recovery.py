"""Exercise settings checkpoints with real files, links and process failures."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('recovery', ROOT/'desktop/migration/recovery.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class Recovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.roots = {kind: self.base/kind for kind in ('home', 'config', 'data', 'state')}
        for path in self.roots.values():
            path.mkdir()
        self.journal = self.roots['state']/'tamlinux/migration/before-test'

    def write(self, kind, name, data=b'original', mode=0o600):
        path = self.roots[kind]/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(mode)
        return path

    def fixture(self):
        layout = self.write('config', 'tamlinux/hypr/monitors.lua', b'left center right\n', 0o640)
        self.write('config', 'omarchy/shell.json.bak.20261001', b'old bar')
        self.write('config', 'foot/foot.ini', b'[main]\nfont=personal\n')
        self.write('data', 'applications/mimeapps.list', b'old browser')
        self.write('home', '.pi/agent/settings.json', b'{"theme":"personal"}')
        link = self.roots['config']/'helix/themes/tamlinux.toml'
        link.parent.mkdir(parents=True)
        link.symlink_to('/unavailable/original-theme')
        self.write('state', 'tamlinux/current/theme.name', b'original-theme\n')
        self.write('state', 'tamlinux/theme-generations/original/colors.toml', b'background="black"\n')
        return layout, link

    def test_restore_preserves_layout_old_backups_link_identity_and_later_writes(self):
        layout, link = self.fixture()
        self.write('config', 'personal-unrelated', b'leave me')
        before = r.preserve(self.roots, self.journal)
        self.assertEqual(before['status'], 'preserved')
        layout.write_bytes(b'new physical layout')
        layout.chmod(0o600)
        link.unlink()
        link.symlink_to('/different/new-theme')
        new = self.write('config', 'tamlinux/new-settings.json', b'new settings')
        self.write('config', 'omarchy/shell.json.bak.20261001', b'later backup change')
        result = r.restore(self.roots, self.journal)
        self.assertEqual(result['status'], 'restored')
        self.assertEqual(layout.read_bytes(), b'left center right\n')
        self.assertEqual(layout.stat().st_mode & 0o777, 0o640)
        self.assertEqual(os.readlink(link), '/unavailable/original-theme')
        self.assertFalse(new.exists())
        archives = [json.loads(p.read_text()) for p in (self.journal/'new-writes').glob('*.json')]
        files = archives[0]['files']
        self.assertEqual((self.journal/'blobs'/files[str(layout)]['blob']).read_bytes(), b'new physical layout')
        self.assertEqual(files[str(link)]['link'], '/different/new-theme')
        self.assertIn(str(new), files)
        self.assertEqual((self.roots['config']/'personal-unrelated').read_bytes(), b'leave me')

    def audio_fixture(self):
        import copy
        state = {'unit': r.AUDIO_UNIT, 'active': 'active', 'enabled': 'enabled',
                 'defaults': {'sink': 'speakers', 'source': 'microphone'}, 'devices': {
                 'sink': {'speakers': {'mute': False, 'volume': {'front-left': 32768, 'front-right': 16384}}},
                 'source': {'microphone': {'mute': True, 'volume': {'mono': 8192}}}}}
        original = copy.deepcopy(state)
        def call(tools, provider, *args, **kwargs):
            if provider == 'systemctl':
                if args[1] == 'is-enabled': return state['enabled']
                if args[1] == 'stop': state['active'] = 'inactive'
                if args[1] == 'start': state['active'] = 'active'
                return
            operation, name, *values = args
            if operation.startswith('set-default-'):
                state['defaults'][operation.removeprefix('set-default-')] = name
            elif operation.endswith('-volume'):
                kind = operation.removeprefix('set-').removesuffix('-volume')
                channels = state['devices'][kind][name]['volume']
                state['devices'][kind][name]['volume'] = dict(zip(channels, map(int, values)))
            else:
                kind = operation.removeprefix('set-').removesuffix('-mute')
                state['devices'][kind][name]['mute'] = values == ['1']
        def read(tools):
            if tools is None: raise ValueError('Missing audio clients')
            return copy.deepcopy(state)
        return state, original, call, read

    def test_tuning_files_links_audio_and_later_values_restore_with_retry(self):
        state, original, call, read = self.audio_fixture()
        unit = self.write('config','systemd/user/'+r.AUDIO_UNIT,b'original unit',0o640)
        link=self.roots['config']/('systemd/user/graphical-session.target.wants/'+r.AUDIO_UNIT)
        link.parent.mkdir(parents=True);link.symlink_to('../'+r.AUDIO_UNIT)
        host=self.write('config','pipewire/tamlinux-speaker-tuning.conf',b'original host')
        stale=self.write('config','wireplumber/wireplumber.conf.d/90-tamlinux-speaker-tuning.conf',b'prior config')
        tools={'systemctl':'/bin/systemctl','pactl':'/bin/pactl'}
        with patch.object(r,'audio_read',side_effect=read), patch.object(r,'audio_call',side_effect=call):
            saved=r.preserve(self.roots,self.journal,audio=tools)
            self.assertEqual(saved['audio'],original)
            host.write_bytes(b'later tuning');unit.write_bytes(b'later unit');stale.unlink()
            state['devices']['sink']['speakers']['volume']['front-left']=50000
            state['devices']['source']['microphone']['mute']=False
            later=json.loads(json.dumps(state))
            with self.assertRaises(ValueError): r.restore(self.roots,self.journal)
            self.assertEqual(host.read_bytes(),b'later tuning')
            self.assertEqual(r.restore(self.roots,self.journal,audio=tools,stop_after=1)['status'],'restoring')
            # A completed original may have different service state after the partial stop.
            result=r.restore(self.roots,self.journal,audio=tools)
            self.assertEqual(result['status'],'restored');self.assertEqual(state,original)
        self.assertEqual(host.read_bytes(),b'original host');self.assertEqual(unit.read_bytes(),b'original unit')
        self.assertEqual(unit.stat().st_mode&0o777,0o640);self.assertEqual(stale.read_bytes(),b'prior config')
        self.assertEqual(link.readlink(),Path('../'+r.AUDIO_UNIT))
        records=[json.loads(p.read_text()) for p in (self.journal/'new-writes').glob('*.json')]
        self.assertTrue(any(doc['audio']==later for doc in records))
        self.assertTrue(any(p.read_bytes()==b'later tuning' for p in (self.journal/'blobs').iterdir()))

    def test_audio_restore_checks_device_names_and_channels_before_volume_mutation(self):
        state,original,call,read=self.audio_fixture();state['active']='inactive'
        # Channel enumeration changes; restoration still sends values in current order.
        state['devices']['sink']['speakers']['volume']={'front-right':9000,'front-left':50000}
        def provider(tools,name,*args,**kwargs):
            if name=='systemctl' and args[1]=='is-enabled':return 'enabled'
            return call(tools,name,*args,**kwargs)
        with patch.object(r,'audio_read',side_effect=read),patch.object(r,'audio_call',side_effect=provider):
            r.audio_restore({},original)
            self.assertEqual(state,original)
            state['devices']['sink']['different']=state['devices']['sink'].pop('speakers')
            with self.assertRaisesRegex(ValueError,'unavailable'):r.audio_restore({},original)
        r.audio_validate(original)
        original['devices']['sink']['speakers']['volume']['front-left']=2147483648
        with self.assertRaises(ValueError):r.audio_validate(original)

    def test_edited_audio_unit_inventory_cannot_control_an_unlisted_service(self):
        state,original,call,read=self.audio_fixture()
        with patch.object(r,'audio_read',side_effect=read):r.preserve(self.roots,self.journal,audio={'systemctl':'/bin/systemctl','pactl':'/bin/pactl'})
        doc=json.loads((self.journal/'checkpoint.json').read_text());doc['audio']['unit']='arbitrary.service'
        r.save(self.journal/'checkpoint.json',doc)
        with patch.object(r,'audio_call') as provider:
            with self.assertRaises(ValueError):r.restore(self.roots,self.journal,audio={})
            provider.assert_not_called()

    def test_native_missing_tuning_unit_requires_confirmed_not_found(self):
        with patch.object(r, 'audio_call', side_effect=['', 'not-found']):
            self.assertEqual(r.audio_enablement({}), 'not-found')
        with patch.object(r, 'audio_call', side_effect=['', 'loaded']):
            self.assertEqual(r.audio_enablement({}), '')
        with patch.object(r, 'audio_call', side_effect=['', ValueError('refused bus')]):
            with self.assertRaises(ValueError): r.audio_enablement({})

    def test_persistent_routes_require_quiescence_and_archive_retry_writes(self):
        route = self.write('state', 'wireplumber/default-routes', b'original routes', 0o640)
        outside = self.write('config', 'tamlinux/current.json', b'leave other settings')
        quiet = subprocess.CompletedProcess([], 0, 'ActiveState=inactive\nSubState=dead\n', '')
        active = subprocess.CompletedProcess([], 0, 'ActiveState=active\nSubState=running\n', '')
        with patch.object(r.subprocess, 'run', return_value=active):
            with self.assertRaisesRegex(ValueError, 'Stop WirePlumber'):
                r.preserve(self.roots, self.journal, audio_state='/bin/systemctl')
        self.assertFalse(self.journal.exists())
        with patch.object(r.subprocess, 'run', return_value=quiet):
            saved = r.preserve(self.roots, self.journal, audio_state='/bin/systemctl')
        self.assertEqual(saved['selection'], 'audio-state')
        route.write_bytes(b'later routes'); route.chmod(0o600)
        with patch.object(r.subprocess, 'run', return_value=active):
            with self.assertRaisesRegex(ValueError, 'Stop WirePlumber'):
                r.restore(self.roots, self.journal, audio_state='/bin/systemctl')
        self.assertEqual(route.read_bytes(), b'later routes')
        with patch.object(r.subprocess, 'run', return_value=quiet):
            self.assertEqual(r.restore(self.roots, self.journal, stop_after=1, audio_state='/bin/systemctl')['status'], 'restoring')
            route.write_bytes(b'write after interruption')
            self.assertEqual(r.restore(self.roots, self.journal, audio_state='/bin/systemctl')['status'], 'restored')
            self.assertEqual(r.restore(self.roots, self.journal, audio_state='/bin/systemctl')['status'], 'restored')
        self.assertEqual(route.read_bytes(), b'original routes')
        self.assertEqual(route.stat().st_mode & 0o777, 0o640)
        self.assertEqual(outside.read_bytes(), b'leave other settings')
        blobs = [p.read_bytes() for p in (self.journal/'blobs').iterdir()]
        self.assertIn(b'later routes', blobs)
        self.assertIn(b'write after interruption', blobs)
        with self.assertRaises(ValueError): r.load(self.journal, self.roots)

    def test_persistent_absence_and_scope_cannot_be_expanded(self):
        quiet = subprocess.CompletedProcess([], 0, 'ActiveState=inactive\nSubState=dead\n', '')
        with patch.object(r.subprocess, 'run', return_value=quiet):
            r.preserve(self.roots, self.journal, audio_state='/bin/systemctl')
            added = self.write('state', 'wireplumber/stream-properties', b'later stream selection')
            r.restore(self.roots, self.journal, audio_state='/bin/systemctl')
            self.assertFalse(added.exists())
            self.assertFalse(added.parent.exists())
            doc = json.loads((self.journal/'checkpoint.json').read_text())
            doc['entries'].append({'path': str(self.roots['config']), 'exclude': []})
            r.save(self.journal/'checkpoint.json', doc)
            with self.assertRaises(ValueError):
                r.restore(self.roots, self.journal, audio_state='/bin/systemctl')

    def test_custom_application_and_vault_roots_restore_without_touching_other_data(self):
        locations={**self.roots,'claude':self.base/'custom-claude','t3code':self.base/'custom-t3',
                   'obsidianVault0':self.base/'vault'}
        files=[]
        for root,name,data in [('claude','settings.json',b'old Claude settings'),
                               ('claude','themes/tamlinux.json',b'old Claude theme'),
                               ('t3code','userdata/themes/tamlinux.json',b'old T3 theme'),
                               ('obsidianVault0','.obsidian/themes/Tamlinux/theme.css',b'old vault theme')]:
            path=locations[root]/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data);path.chmod(0o640);files.append((path,data))
        notes=locations['obsidianVault0']/'notes.md';notes.write_bytes(b'personal notes')
        registry=self.write('config','obsidian/obsidian.json',b'{"vaults":{"original":{}}}')
        r.preserve(locations,self.journal)
        for path,_ in files:path.write_bytes(b'later application writes');path.chmod(0o600)
        registry.write_bytes(b'{"vaults":{"later":{}}}')
        added=locations['obsidianVault0']/'.obsidian/themes/Tamlinux/new.css';added.write_bytes(b'later generated file')
        notes.write_bytes(b'later personal notes')
        self.assertEqual(r.restore(locations,self.journal,stop_after=2)['status'],'restoring')
        self.assertEqual(r.restore(locations,self.journal)['status'],'restored')
        for path,data in files:
            self.assertEqual(path.read_bytes(),data);self.assertEqual(path.stat().st_mode&0o777,0o640)
        self.assertEqual(registry.read_bytes(),b'{"vaults":{"original":{}}}')
        self.assertFalse(added.exists());self.assertEqual(notes.read_bytes(),b'later personal notes')
        self.assertTrue(any(p.read_bytes()==b'later application writes' for p in (self.journal/'blobs').iterdir()))
        self.assertTrue(any(p.read_bytes()==b'later generated file' for p in (self.journal/'blobs').iterdir()))

    def test_custom_roots_must_match_and_cannot_expand_journal_destinations(self):
        locations={**self.roots,'claude':self.base/'custom-claude'}
        file=locations['claude']/'settings.json';file.parent.mkdir();file.write_bytes(b'original')
        r.preserve(locations,self.journal);file.write_bytes(b'keep later')
        with self.assertRaises(ValueError):r.restore(self.roots,self.journal)
        doc=json.loads((self.journal/'checkpoint.json').read_text())
        doc['entries'].append({'path':str(self.base/'unrelated'),'exclude':[]})
        r.save(self.journal/'checkpoint.json',doc)
        with self.assertRaises(ValueError):r.restore(locations,self.journal)
        self.assertEqual(file.read_bytes(),b'keep later')

    def test_standard_application_roots_do_not_overlap_the_home_manifest(self):
        file=self.write('home','.claude/settings.json',b'original')
        locations={**self.roots,'claude':self.roots['home']/'.claude','t3code':self.roots['home']/'.t3'}
        r.preserve(locations,self.journal);file.write_bytes(b'later')
        r.restore(locations,self.journal)
        self.assertEqual(file.read_bytes(),b'original')

    def test_custom_root_link_to_uncovered_mutable_settings_blocks_completion(self):
        root=self.base/'custom-claude';root.mkdir();outside=self.base/'outside';outside.write_bytes(b'keep')
        (root/'settings.json').symlink_to(outside)
        locations={**self.roots,'claude':root}
        with self.assertRaises(ValueError):r.preserve(locations,self.journal)
        with self.assertRaises(ValueError):r.load(self.journal,locations)
        self.assertEqual(outside.read_bytes(),b'keep')

    def test_cli_binds_custom_roots_and_vaults_to_original_and_later_writes(self):
        vault=self.base/'vault';theme=vault/'.obsidian/themes/Tamlinux/theme.css'
        theme.parent.mkdir(parents=True);theme.write_bytes(b'old theme')
        claude=self.base/'custom-claude';claude.mkdir();settings=claude/'settings.json';settings.write_bytes(b'old settings')
        env={**os.environ,'HOME':str(self.roots['home'])}
        env.update({'XDG_'+key.upper()+'_HOME':str(self.roots[key]) for key in ('config','state','data')})
        env['CLAUDE_CONFIG_DIR']=str(claude);env.pop('T3CODE_HOME',None)
        def call(action,*args):
            return subprocess.run([shutil.which('python3'),'-B',str(ROOT/'desktop/migration/engine.py'),action,str(self.journal),*args],
                                  env=env,capture_output=True,text=True)
        self.assertEqual(call('preserve','--obsidian-vault',str(vault)).returncode,0)
        settings.write_bytes(b'later settings');theme.write_bytes(b'later theme')
        # Restore from the explicit captured root even after the runtime override changes.
        env['CLAUDE_CONFIG_DIR']=str(self.base/'different-claude')
        self.assertNotEqual(call('restore','--obsidian-vault',str(vault)).returncode,0)
        result=call('restore','--claude-root',str(claude),'--obsidian-vault',str(vault))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(settings.read_bytes(),b'old settings');self.assertEqual(theme.read_bytes(),b'old theme')
        self.assertTrue(any(p.read_bytes()==b'later theme' for p in (self.journal/'blobs').iterdir()))

    def test_new_tree_deleted_tree_and_file_directory_replacements_restore(self):
        file = self.write('config', 'tamlinux/file', b'file before')
        child = self.write('config', 'foot/nested/config', b'child before')
        r.preserve(self.roots, self.journal)
        file.unlink()
        file.mkdir()
        (file/'new').write_bytes(b'new directory contents')
        shutil.rmtree(child.parent)
        self.write('config', 'kitty/new/deep/config', b'new application')
        r.restore(self.roots, self.journal)
        self.assertEqual(file.read_bytes(), b'file before')
        self.assertEqual(child.read_bytes(), b'child before')
        self.assertFalse((self.roots['config']/'kitty').exists())

    def test_interrupted_restore_can_resume_after_deletion_or_publication(self):
        layout, _ = self.fixture()
        r.preserve(self.roots, self.journal)
        layout.write_bytes(b'later edit')
        self.assertEqual(r.restore(self.roots, self.journal, stop_after=1)['status'], 'restoring')
        self.assertEqual(r.restore(self.roots, self.journal)['status'], 'restored')
        self.assertEqual(layout.read_bytes(), b'left center right\n')
        self.assertTrue(any(b'later edit' == p.read_bytes() for p in (self.journal/'blobs').iterdir()))

    def test_retry_keeps_new_writes_and_excluded_settings_journals(self):
        self.fixture()
        old = self.write('state', 'tamlinux/settings-recovery/prior/manifest.json', b'old recovery')
        r.preserve(self.roots, self.journal)
        new = self.write('state', 'tamlinux/settings-recovery/new/manifest.json', b'later recovery')
        r.restore(self.roots, self.journal)
        r.restore(self.roots, self.journal)
        self.assertEqual(old.read_bytes(), b'old recovery')
        self.assertEqual(new.read_bytes(), b'later recovery')
        self.assertEqual(r.load(self.journal, self.roots)['status'], 'restored')

    def test_bad_original_blob_blocks_all_restoration_before_settings_change(self):
        layout, _ = self.fixture()
        doc = r.preserve(self.roots, self.journal)
        layout.write_bytes(b'keep later value')
        blob = self.journal/'blobs'/doc['files'][str(layout)]['blob']
        blob.write_bytes(b'substituted recovery bytes')
        with self.assertRaises(ValueError):
            r.restore(self.roots, self.journal)
        self.assertEqual(layout.read_bytes(), b'keep later value')

    def test_concurrent_later_writer_is_not_overwritten_after_archive(self):
        layout,_=self.fixture()
        r.preserve(self.roots,self.journal)
        layout.write_bytes(b'first later edit')
        save=r.save
        def concurrent(path,doc):
            save(path,doc)
            if path==self.journal/'checkpoint.json' and doc.get('status')=='restoring':
                layout.write_bytes(b'concurrent latest edit')
        with patch.object(r,'save',side_effect=concurrent):
            with self.assertRaises(ValueError):r.restore(self.roots,self.journal)
        self.assertEqual(layout.read_bytes(),b'concurrent latest edit')
        r.restore(self.roots,self.journal)
        self.assertEqual(layout.read_bytes(),b'left center right\n')
        self.assertTrue(any(p.read_bytes()==b'concurrent latest edit' for p in (self.journal/'blobs').iterdir()))

    def test_edited_journal_cannot_write_unlisted_file_or_traverse_saved_link(self):
        layout, _ = self.fixture()
        doc = r.preserve(self.roots, self.journal)
        outside = self.write('config', 'not-selected', b'keep outside')
        doc['files'][str(outside)] = doc['files'][str(layout)]
        r.save(self.journal/'checkpoint.json', doc)
        with self.assertRaises(ValueError):
            r.restore(self.roots, self.journal)
        self.assertEqual(outside.read_bytes(), b'keep outside')

    def test_live_symlink_replacement_is_archived_and_never_followed(self):
        layout, _ = self.fixture()
        r.preserve(self.roots, self.journal)
        shutil.rmtree(self.roots['config']/'tamlinux')
        outside = self.base/'outside'
        outside.mkdir()
        (outside/'personal').write_bytes(b'do not follow')
        (self.roots['config']/'tamlinux').symlink_to(outside)
        r.restore(self.roots, self.journal)
        self.assertEqual(layout.read_bytes(), b'left center right\n')
        self.assertEqual((outside/'personal').read_bytes(), b'do not follow')

    def test_live_linked_config_source_bytes_and_link_survive_restoration(self):
        source=self.base/'consumer-config';(source/'hypr').mkdir(parents=True)
        monitors=source/'hypr/monitors.lua';monitors.write_bytes(b'original live layout')
        link=self.roots['config']/'hypr';link.symlink_to(source/'hypr')
        locations={**self.roots,'settingsSource':source}
        r.preserve(locations,self.journal)
        monitors.write_bytes(b'later live source layout')
        r.restore(locations,self.journal)
        self.assertEqual(os.readlink(link),str(source/'hypr'))
        self.assertEqual(monitors.read_bytes(),b'original live layout')
        self.assertTrue(any(p.read_bytes()==b'later live source layout' for p in (self.journal/'blobs').iterdir()))
        with self.assertRaises(ValueError):r.load(self.journal,self.roots)

    def test_uncovered_mutable_config_link_blocks_checkpoint_completion(self):
        source=self.base/'outside-source';source.mkdir();(source/'monitors.lua').write_bytes(b'keep')
        (self.roots['config']/'hypr').symlink_to(source)
        with self.assertRaises(ValueError):r.preserve(self.roots,self.journal)
        with self.assertRaises(ValueError):r.load(self.journal,self.roots)
        self.assertEqual((source/'monitors.lua').read_bytes(),b'keep')

    def test_selected_scope_with_excluded_journals_refuses_file_replacement(self):
        self.fixture()
        r.preserve(self.roots, self.journal)
        # Replacing an ancestor of the journal is a conflict, never a reason
        # to remove the saved original or trust an unrelated recovery folder.
        state_root = self.roots['state']/'tamlinux'
        state_root.rename(self.roots['state']/'moved')
        state_root.write_bytes(b'conflicting later state')
        with self.assertRaises((ValueError, OSError)):
            r.restore(self.roots, self.journal)
        self.assertEqual(state_root.read_bytes(), b'conflicting later state')

    def test_fifo_is_a_conflict_and_checkpoint_cannot_be_restored_incomplete(self):
        self.fixture()
        os.mkfifo(self.roots['config']/'tamlinux/live-fifo')
        with self.assertRaises(ValueError):
            r.preserve(self.roots, self.journal)
        with self.assertRaises(ValueError):
            r.load(self.journal, self.roots)

    def test_special_permissions_refuse_incomplete_backup_and_later_restore(self):
        layout, _ = self.fixture()
        layout.chmod(0o2600)
        with self.assertRaises(ValueError):
            r.preserve(self.roots, self.journal)
        with self.assertRaises(ValueError):
            r.load(self.journal, self.roots)
        self.assertEqual(layout.stat().st_mode & 0o7777, 0o2600)
        layout.chmod(0o600)
        complete = self.journal.with_name('complete')
        r.preserve(self.roots, complete)
        layout.write_bytes(b'keep later special file')
        layout.chmod(0o2600)
        with self.assertRaises(ValueError):
            r.restore(self.roots, complete)
        self.assertEqual(layout.read_bytes(), b'keep later special file')
        self.assertEqual(r.load(complete, self.roots)['status'], 'preserved')

    def test_symlinked_recovery_directory_is_refused(self):
        self.fixture()
        r.preserve(self.roots, self.journal)
        original = self.journal.with_name('actual')
        self.journal.rename(original)
        self.journal.symlink_to(original)
        with self.assertRaises(ValueError):
            r.load(self.journal, self.roots)

    def test_cli_roundtrip_in_separate_home_preserves_existing_machine_layout(self):
        layout, _ = self.fixture()
        env = {**os.environ, 'HOME':str(self.roots['home']),
               **{'XDG_'+k.upper()+'_HOME':str(self.roots[k]) for k in ('config','data','state')}}
        engine = ROOT/'desktop/migration/engine.py'
        def call(action):
            return subprocess.run(['/usr/bin/python3', str(engine), action, str(self.journal)],
                                  env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(call('preserve').returncode, 0)
        layout.write_bytes(b'preview changes')
        result = call('restore')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'restored')
        self.assertEqual(layout.read_bytes(), b'left center right\n')

    def test_actual_dconf_user_values_and_absent_defaults_restore(self):
        dconf = shutil.which('dconf')
        dbus = shutil.which('dbus-run-session')
        if not dconf or not dbus:
            self.skipTest('Actual dconf and isolated D-Bus session unavailable')
        script = self.base/'gtk-proof.py'
        script.write_text('''import importlib.util,json,subprocess,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('r',sys.argv[1]);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
roots={k:Path(v) for k,v in json.loads(sys.argv[2]).items()};journal=Path(sys.argv[3]);dconf=sys.argv[4]
theme='/org/gnome/desktop/interface/gtk-theme';scheme='/org/gnome/desktop/interface/color-scheme'
subprocess.run([dconf,'write',theme,"'Original'"],check=True)
before=r.preserve(roots,journal,dconf);assert before['gtk'][scheme] is None
subprocess.run([dconf,'write',theme,"'Later'"],check=True)
subprocess.run([dconf,'write',scheme,"'prefer-dark'"],check=True)
r.restore(roots,journal,dconf)
assert r.gtk_read(dconf,list(before['gtk']))==before['gtk']
later=[json.loads(p.read_text()) for p in (journal/'new-writes').glob('*.json')]
assert later[0]['gtk'][theme]=="'Later'"
''')
        env = {**os.environ, 'HOME':str(self.roots['home']),
               'XDG_CONFIG_HOME':str(self.roots['config'])}
        env.pop('DCONF_PROFILE', None)
        result = subprocess.run([dbus, '--', '/usr/bin/python3', str(script), str(ROOT/'desktop/migration/recovery.py'),
            json.dumps({k:str(v) for k,v in self.roots.items()}), str(self.journal), dconf],
            env=env, capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr)
