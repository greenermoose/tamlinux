"""Real migration failure, resume and recovery cases in independent XDG roots."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('migration',ROOT/'desktop/migration/engine.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Migration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.roots={kind:self.base/kind for kind in ('config','data','state')}
        self.journal=self.roots['state']/'tamlinux/migration/proof'

    def write(self,root,relative,data):
        p=self.roots[root]/relative;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data);return p

    def seed(self):
        mode=self.write('state','tamlinux/desktop-mode',b'omarchy\n')
        app=self.write('data','applications/Example.desktop',b'[Desktop Entry]\nName=Example\nExec=omarchy-launch-webapp "https://example.org"\n')
        source=self.write('config','hypr/input.lua',b'hl.config({ input = { kb_layout = "de" } })\n')
        return mode,app,source

    def test_fresh_state_plan_and_apply_do_not_invent_legacy_files(self):
        plan=m.prepare(self.roots,self.journal)
        self.assertEqual(plan['rows'],[]);self.assertEqual(m.apply(self.journal,self.roots)['status'],'applied')

    def test_in_place_conversion_preserves_original_bytes_and_machine_values(self):
        mode,app,source=self.seed();prior_app=app.read_bytes();prior_input=source.read_bytes()
        plan=m.prepare(self.roots,self.journal);self.assertEqual(len(plan['rows']),3)
        m.apply(self.journal,self.roots)
        self.assertEqual(mode.read_bytes(),b'tamlinux\n')
        self.assertIn(b'Exec=tam-launch-webapp',app.read_bytes())
        self.assertEqual(source.read_bytes(),prior_input)
        self.assertEqual((self.roots['config']/'tamlinux/hypr/input.lua').read_bytes(),prior_input)
        m.rollback(self.journal,self.roots)
        self.assertEqual(mode.read_bytes(),b'omarchy\n');self.assertEqual(app.read_bytes(),prior_app)
        self.assertFalse((self.roots['config']/'tamlinux/hypr/input.lua').exists())

    def test_existing_conflicting_destination_blocks_entire_batch_before_write(self):
        mode,app,source=self.seed()
        target=self.write('config','tamlinux/hypr/input.lua',b'personal override')
        plan=m.prepare(self.roots,self.journal);self.assertEqual(plan['status'],'blocked')
        with self.assertRaises(ValueError):m.apply(self.journal,self.roots)
        self.assertEqual(mode.read_bytes(),b'omarchy\n');self.assertEqual(target.read_bytes(),b'personal override')

    def test_interruption_after_one_write_is_idempotently_resumed(self):
        self.seed();m.prepare(self.roots,self.journal)
        self.assertEqual(m.apply(self.journal,self.roots,stop_after=1)['status'],'applying')
        self.assertEqual(m.apply(self.journal,self.roots)['status'],'applied')
        self.assertEqual(m.apply(self.journal,self.roots)['status'],'applied')
        self.assertEqual(list(self.base.rglob('.tamlinux-migrate-*')),[])

    def test_interruption_between_file_publication_and_journal_commit_is_resumed(self):
        self.seed();doc=m.prepare(self.roots,self.journal)
        row=doc['rows'][0];row['status']='writing';doc['status']='applying'
        m.save(self.journal/'journal.json',doc);m.atomic(Path(row['target']),row['after'])
        self.assertEqual(m.apply(self.journal,self.roots)['status'],'applied')

    def test_changed_source_or_destination_after_plan_is_never_overwritten(self):
        mode,app,source=self.seed();m.prepare(self.roots,self.journal)
        source.write_bytes(b'later personal input')
        with self.assertRaises(ValueError):m.apply(self.journal,self.roots)
        self.assertEqual(mode.read_bytes(),b'omarchy\n')
        self.assertEqual(source.read_bytes(),b'later personal input')

    def test_rollback_archives_post_migration_writes_and_is_retryable(self):
        mode,app,source=self.seed();m.prepare(self.roots,self.journal);m.apply(self.journal,self.roots)
        mode.write_bytes(b'windows\n');mode.chmod(0o640)
        app.unlink();app.symlink_to('later-personal-launcher')
        doc=m.rollback(self.journal,self.roots)
        self.assertEqual(doc['status'],'rolled-back')
        archives=[json.loads(p.read_text()) for p in (self.journal/'new-writes').rglob('*.json')]
        self.assertTrue(any(x['state'].get('link')=='later-personal-launcher' for x in archives))
        self.assertTrue(any(x['state'].get('bytes')==base64.b64encode(b'windows\n').decode() and x['state']['mode']==0o640 for x in archives))
        before=list((self.journal/'new-writes').rglob('*.json'))
        m.rollback(self.journal,self.roots)
        self.assertEqual(before,list((self.journal/'new-writes').rglob('*.json')))
        with self.assertRaises(ValueError):m.apply(self.journal,self.roots)

    def test_linked_original_is_preserved_for_explicit_review(self):
        target=self.roots['state']/'tamlinux/desktop-mode';target.parent.mkdir(parents=True)
        target.symlink_to('unavailable-legacy-selection')
        doc=m.prepare(self.roots,self.journal)
        self.assertEqual(doc['status'],'blocked')
        self.assertEqual(os.readlink(target),'unavailable-legacy-selection')

    def test_unknown_legacy_helper_is_a_conflict_not_an_unresolved_runtime_alias(self):
        self.write('config','hypr/bindings.lua',b'hl.exec("omarchy-unknown-tool")\n')
        self.assertEqual(m.prepare(self.roots,self.journal)['status'],'blocked')

    def test_unlisted_destination_in_edited_journal_is_refused(self):
        self.seed();doc=m.prepare(self.roots,self.journal)
        outside=self.write('data','personal.txt',b'keep')
        doc['rows'][0]['target']=str(outside);m.save(self.journal/'journal.json',doc)
        with self.assertRaises(ValueError):m.apply(self.journal,self.roots)
        self.assertEqual(outside.read_bytes(),b'keep')

    def test_redirected_parent_is_refused_without_outside_modification(self):
        mode,app,source=self.seed();outside=self.base/'outside';outside.mkdir()
        (self.roots['config']/'tamlinux').symlink_to(outside)
        with self.assertRaises(ValueError):m.prepare(self.roots,self.journal)
        self.assertEqual(list(outside.iterdir()),[])
