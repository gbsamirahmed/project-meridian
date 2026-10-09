"""Owned-copy hardening and process-interruption tests; never modify retained inputs."""
from pathlib import Path
import copy
import errno
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from reader import Reader, ReadError, identity
from store import Store
import store as store_module
from verification import json_value

ROOT = Path(os.environ['ATLAS_SPIKE_PROJECTION'])
MANIFEST = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
ID = MANIFEST['projectionIdentity']
PINS = {v['alias']:k for k,v in MANIFEST['pins'].items()}
DRIVERS = Path(__file__).parent.resolve()

def write_manifest(root, m):
    m['projectionIdentity'] = identity({k:v for k,v in m.items() if k != 'projectionIdentity'})
    (root/'manifest.json').write_text(json.dumps(m,ensure_ascii=False),encoding='utf-8')
    return m['projectionIdentity']

def reseal_member(root, name, change):
    value = json.loads((root/name).read_text(encoding='utf-8')); change(value)
    raw = json.dumps(value,ensure_ascii=False).encode('utf-8'); (root/name).write_bytes(raw)
    m = copy.deepcopy(MANIFEST); m['files'][name] = {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    return write_manifest(root,m)

class Hardening(unittest.TestCase):
    def altered(self, change):
        with tempfile.TemporaryDirectory(prefix='atlas-hardening-') as folder:
            p = Path(folder)/'copy'; shutil.copytree(ROOT,p)
            change(p)
            with self.assertRaises(ReadError): Reader(p,PINS['after'])

    def test_strict_json_numbers_keys_depth_encoding(self):
        for raw in [b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":1e999}',b'{"x":9007199254740992}',b'{"x":"\\ud800"}',b'['*65+b'0'+b']'*65,b'\xff']:
            with self.subTest(raw=raw[:40]):
                with self.assertRaises((ReadError,ValueError)): json_value(raw)
        self.assertEqual(json_value(b'{"x":-0.0,"20":1,"100":2}'),{'x':0,'20':1,'100':2})

    def test_truncated_duplicate_and_nonobject_manifest(self):
        for raw in [b'{',b'[]',b'{"schema":1,"schema":2}']:
            with self.subTest(raw=raw): self.altered(lambda p:(p/'manifest.json').write_bytes(raw))

    def test_oversized_manifest_rejected_before_parse(self):
        self.altered(lambda p:(p/'manifest.json').write_bytes(b' '*65537))

    def test_invalid_declared_size_and_count(self):
        for size in [-1,True,170*1024*1024]:
            def change(p):
                m = copy.deepcopy(MANIFEST); m['files']['features.json']['bytes'] = size; write_manifest(p,m)
            with self.subTest(size=size): self.altered(change)

    def test_unexpected_file_and_directory_member(self):
        self.altered(lambda p:(p/'extra.json').write_bytes(b'{}'))
        self.altered(lambda p:[(p/('extra-'+str(i))).write_bytes(b'{}') for i in range(18)])
        self.altered(lambda p:((p/'worldcover.json').unlink(),(p/'worldcover.json').mkdir()))

    def test_unsafe_member_and_incompatible_profile(self):
        for field, value in [('profile','future/v9'),('rasterFiles',{'x':'../outside.tif'}),('pins',{'bad':[]})]:
            with self.subTest(field=field): self.altered(lambda p:write_manifest(p,{**copy.deepcopy(MANIFEST),field:value}))

    def test_all_pins_verified_not_only_requested_pin(self):
        self.altered(lambda p:(p/(PINS['before']+'.json')).write_bytes(b'{}'))

    def test_missing_qualified_document(self):
        def change(d): d['answer']['documents'].pop(d['answer']['results'][0]['rightsRef'])
        self.altered(lambda p:reseal_member(p,PINS['after']+'.json',change))

    def test_changed_membership_and_knowledge(self):
        for change in [lambda d:d['answer']['results'][0].update(componentIdentity='0'*64),lambda d:d['knowledge']['riffelhorn'].update(acceptedAt='2000-01-01T00:00:00.000Z')]:
            self.altered(lambda p:reseal_member(p,PINS['after']+'.json',change))

    def test_missing_native_record_even_with_reduced_declared_count(self):
        def change(p):
            name = PINS['after']+'.json'
            reseal_member(p,name,lambda d:d['answer']['results'].pop(0))
            m=json.loads((p/'manifest.json').read_text(encoding='utf-8')); m['pins'][PINS['after']]['records']-=1; write_manifest(p,m)
        self.altered(change)

    def test_selector_tampering_and_missing_selector(self):
        for change in [lambda d:d['selectors'][0]['cells'][0].__setitem__(0,0),lambda d:d['selectors'].pop()]:
            self.altered(lambda p:reseal_member(p,PINS['after']+'.json',change))

    def test_edge_mismatch_and_missing_dependency(self):
        for change in [lambda d:d['answer']['relationships'][0].update(toRevision='0'*64),lambda d:d['answer']['relationships'].pop()]:
            self.altered(lambda p:reseal_member(p,PINS['after']+'.json',change))

    def test_cycle_rejected_even_when_edges_resealed(self):
        def change(d):
            e=d['answer']['relationships'][0]; e['to']=e['from']; e['toRevision']=e['fromRevision']; e['identity']=identity({k:v for k,v in e.items() if k!='identity'})
        self.altered(lambda p:reseal_member(p,PINS['after']+'.json',change))

    def test_native_geometry_binding_and_duplicate_feature(self):
        self.altered(lambda p:reseal_member(p,'features.json',lambda d:d['features'].__setitem__(0,d['features'][1])))

    def test_native_raster_header_and_identity_binding(self):
        def change(d): next(r for r in d['answer']['results'] if r['representation']=='raster')['support']['shape'][0]+=1
        self.altered(lambda p:reseal_member(p,PINS['after']+'.json',change))

    def test_post_open_snapshots_survive_raster_metadata_replace_and_delete(self):
        with tempfile.TemporaryDirectory(prefix='atlas-snapshot-') as folder:
            p=Path(folder)/'copy'; shutil.copytree(ROOT,p)
            q={'region':'riffelhorn','point':[2624123.875,1091567.125],'crs':'EPSG:2056','families':['dtm']}
            with Reader(p,PINS['after']) as first, Reader(p,PINS['before']) as second:
                expected=first.read(q); historical=second.read(q)
                raster=next(r for r in expected['results'] if r['family']=='dtm')['identity']
                member=p/MANIFEST['rasterFiles'][raster]
                # Atomic path replacement while two readers exist; no retained hard link.
                replacement=p/'replacement.tmp'; replacement.write_bytes(b'not a TIFF'); os.replace(replacement,member)
                (p/'features.json').write_bytes(b'{}'); (p/'worldcover.json').unlink()
                self.assertEqual(first.read(q),expected); self.assertEqual(second.read(q),historical)
                with self.assertRaises(ReadError): Reader(p,PINS['after'])
                shutil.rmtree(p)
                self.assertEqual(first.read(q),expected)
            self.assertEqual(first.outcome(q)['code'],'projection-closed')

class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='atlas-store-'); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.store=Store.create(self.root/'store')
        self.store.install(ROOT,ID)
        self.candidate=self.root/'candidate'; shutil.copytree(ROOT,self.candidate)
        m=copy.deepcopy(MANIFEST); m['coverage']+=' Administrative packaging fault-test variant; scientific records unchanged.'
        self.new_id=write_manifest(self.candidate,m)

    def assert_old_ready(self):
        self.assertEqual(Store(self.store.root).selected(),ID)
        with Store(self.store.root).open(PINS['after']) as reader: self.assertEqual(reader.generation,PINS['after'])

    def test_stage_write_failure_preserves_selection(self):
        def hook(name):
            if name.startswith('staging-write:') and name.endswith('.tif'): raise OSError(errno.ENOSPC,'Injected disk full')
        with self.assertRaises(ReadError) as e:self.store.install(self.candidate,self.new_id,hook)
        self.assertEqual(e.exception.code,'store-write'); self.assert_old_ready()
        self.assertFalse((self.store.root/'ready'/(self.new_id+'.json')).exists())
        stages=list((self.store.root/'staging').iterdir()); self.assertEqual(len(stages),1)
        self.store.discard_stage(stages[0].name); self.assertEqual(list((self.store.root/'staging').iterdir()),[])

    def test_process_interruptions_around_ready_and_selection_commits(self):
        for boundary in ['staged-member:manifest.json','before-ready','after-ready','before-select','after-select']:
            with self.subTest(boundary=boundary):
                # Reset only explicitly owned candidate state between serial fault trials.
                if (self.store.root/'packages'/self.new_id).exists(): self.store.delete(self.new_id)
                self.store.select(ID)
                for p in list((self.store.root/'staging').iterdir()): self.store.discard_stage(p.name)
                code="import sys,os; sys.path.insert(0,sys.argv[1]); from store import Store; Store(sys.argv[2]).install(sys.argv[3],sys.argv[4],lambda n: os._exit(73) if n==sys.argv[5] else None)"
                result=subprocess.run([sys.executable,'-B','-c',code,str(DRIVERS),str(self.store.root),str(self.candidate),self.new_id,boundary],capture_output=True)
                self.assertEqual(result.returncode,73,result.stderr.decode())
                restarted=Store(self.store.root)
                self.assertEqual(restarted.selected(),self.new_id if boundary=='after-select' else ID)
                ready=(restarted.root/'ready'/(self.new_id+'.json')).exists()
                self.assertEqual(ready,boundary in ['after-ready','before-select','after-select'])
                with restarted.open(PINS['after']) as reader:self.assertEqual(reader.generation,PINS['after'])
                with restarted.open(PINS['before'],ID):pass

    def test_corrupt_candidate_never_ready(self):
        for name in ['manifest.json','features.json',MANIFEST['rasterFiles'][next(iter(MANIFEST['rasterFiles']))]]:
            original=(self.candidate/name).read_bytes(); (self.candidate/name).write_bytes(b'{')
            with self.assertRaises(ReadError):self.store.install(self.candidate,self.new_id)
            self.assert_old_ready(); self.assertFalse((self.store.root/'ready'/(self.new_id+'.json')).exists())
            (self.candidate/name).write_bytes(original)
            for p in list((self.store.root/'staging').iterdir()): self.store.discard_stage(p.name)

    def test_mutation_before_readiness_is_rejected(self):
        def hook(name):
            if name=='before-final-verify': (self.store.package(self.new_id)/'features.json').write_bytes(b'{}')
        with self.assertRaises(ReadError):self.store.install(self.candidate,self.new_id,hook)
        self.assert_old_ready(); self.assertFalse((self.store.root/'ready'/(self.new_id+'.json')).exists())

    def test_record_write_failures_preserve_previous_selection(self):
        for record_name in [self.new_id+'.json','selection.json']:
            def hook(name):
                if name == 'record-written:'+record_name: raise OSError(errno.ENOSPC,'Injected record write failure')
            with self.subTest(record=record_name):
                with self.assertRaises(ReadError): self.store.install(self.candidate,self.new_id,hook)
                self.assert_old_ready()
                self.assertEqual(list(self.store.root.glob('.record-*')),[])
                self.assertEqual(list((self.store.root/'ready').glob('.record-*')),[])

    def test_interrupted_delete_leaves_no_silent_selection(self):
        def hook(name):
            if name == 'delete-selection-cleared': raise RuntimeError('Injected interrupted deletion')
        with self.assertRaises(RuntimeError): self.store.delete(ID,hook)
        with self.assertRaises(ReadError): Store(self.store.root).open(PINS['after'])
        # Still-ready orphan is recoverable only through explicit selection.
        self.store.select(ID); self.assert_old_ready()

    def test_incompatible_candidate_preserves_last_ready(self):
        m=json.loads((self.candidate/'manifest.json').read_text(encoding='utf-8')); m['profile']='future/v9'; new=write_manifest(self.candidate,m)
        with self.assertRaises(ReadError):self.store.install(self.candidate,new)
        self.assert_old_ready()

    def test_restart_bad_or_incomplete_selection_never_falls_back(self):
        for raw in [b'{',b'{}',b'{"schema":"future"}',json.dumps({'schema':'atlas-projection-selection-spike/v1','projectionIdentity':'0'*64}).encode()]:
            (self.store.root/'selection.json').write_bytes(raw)
            with self.assertRaises(ReadError):Store(self.store.root).open(PINS['after'])
        (self.store.root/'selection.json').unlink()
        with self.assertRaises(ReadError):self.store.open(PINS['after'])
        self.store.select(ID); self.assert_old_ready()

    def test_generation_mismatch_no_fallback(self):
        with self.assertRaises(ReadError) as e:self.store.open('0'*64)
        self.assertEqual(e.exception.code,'projection-generation'); self.assert_old_ready()

    def test_tampered_ready_and_member_fail_after_restart(self):
        receipt=self.store.root/'ready'/(ID+'.json'); original=receipt.read_bytes(); receipt.write_bytes(b'{}')
        with self.assertRaises(ReadError):Store(self.store.root).open(PINS['after'])
        receipt.write_bytes(original)
        (self.store.package(ID)/'worldcover.json').unlink()
        with self.assertRaises(ReadError):Store(self.store.root).open(PINS['after'])

    def test_delete_selected_and_obsolete_with_open_reader(self):
        with self.store.open(PINS['after']) as old:
            expected=old.read({'identity':'glaciers:683'})
            self.store.install(self.candidate,self.new_id)
            self.store.delete(ID); self.assertEqual(self.store.selected(),self.new_id)
            self.assertEqual(old.read({'identity':'glaciers:683'}),expected)
            self.store.delete(self.new_id)
            with self.assertRaises(ReadError):Store(self.store.root).open(PINS['after'])
            self.assertEqual(old.read({'identity':'glaciers:683'}),expected)

    def test_idempotent_install_and_failed_conflicting_identity(self):
        self.store.install(ROOT,ID); self.assert_old_ready()
        with self.assertRaises(ReadError):self.store.install(self.candidate,ID)
        self.assert_old_ready()

    def test_store_budget_rejection_preserves_ready(self):
        previous=store_module.MAX_STORE
        try:
            store_module.MAX_STORE=1
            with self.assertRaises(ReadError) as e:self.store.install(self.candidate,self.new_id)
            self.assertEqual(e.exception.code,'store-budget'); self.assert_old_ready()
        finally: store_module.MAX_STORE=previous

    def test_owned_path_and_selection_guards(self):
        with self.assertRaises(ReadError):Store.create(ROOT)
        for bad in ['../outside','candidate-../outside','candidate-..\\outside','not-owned']:
            with self.assertRaises(ReadError):self.store.discard_stage(bad)
        with self.assertRaises(ReadError):self.store.delete('../outside')

if __name__=='__main__':unittest.main()
