"""Public proof-interface tests; all destructive cases own isolated fixtures."""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from core import Store,STATE,fixture,prepare,update,verdict,encode,sha

class Proof(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=STATE,prefix='test-');self.s=Store(Path(self.tmp.name)/'store')
        self.p=fixture(self.s,4,1);self.anchor,_=prepare(self.s,self.p);self.q=update(self.s,self.p)
    def tearDown(self):self.tmp.cleanup()
    def both(self,p=None,expected=True,anchor=None,rule='v1'):
        p=p or self.q;a=verdict(self.s,p,'full',rule=rule);b=verdict(self.s,p,'incremental',anchor or self.anchor,rule)
        self.assertEqual(a['accepted'],expected,a);self.assertEqual(b['accepted'],expected,b);return a,b
    def alter(self,slot,fn):
        v=copy.deepcopy(self.s.get(self.q['members'][slot]));fn(v);self.q['members'][slot]=self.s.put(v)
    def test_baseline_and_reuse(self):
        a,b=self.both(self.p);self.assertEqual(b['counter']['localReused'],12);self.assertEqual(b['counter']['rowsChecked'],0);self.assertEqual(b['counter']['componentIntegrity'],12)
    def test_local_changed_chain(self):
        a,b=self.both();self.assertEqual(b['counter']['localChecks'],2);self.assertEqual(b['counter']['crossChecks'],1);self.assertEqual(b['counter']['crossReused'],3)
    def test_scattered(self):self.both(update(self.s,self.p,'four-scattered'))
    def test_fanout(self):
        p=fixture(self.s,4,4);anchor,_=prepare(self.s,p);q=update(self.s,p);a,b=self.both(q,anchor=anchor);self.assertEqual(b['counter']['localChecks'],5)
    def test_hash_corruption(self):
        h=self.q['members']['semantic:0'];(self.s.objects/(h+'.json')).write_bytes(b'changed');self.both(expected=False)
    def test_missing_component(self):
        (self.s.objects/(self.q['members']['semantic:0']+'.json')).unlink();self.both(expected=False)
    def test_schema(self):self.alter('semantic:0',lambda v:v.update(schema='wrong'));self.both(expected=False)
    def test_duplicate_key(self):self.alter('semantic:0',lambda v:v['records'][1].update(key=v['records'][0]['key']));self.both(expected=False)
    def test_scope(self):self.alter('derived:0',lambda v:v['records'][0].update(inputUse=[9,1]));self.both(expected=False)
    def test_missing_dependency(self):self.alter('derived:0',lambda v:v.update(dependencies=[]));self.both(expected=False)
    def test_broken_reference(self):self.alter('derived:0',lambda v:v['dependencies'][0].update(slot='terrain:999'));self.both(expected=False)
    def test_dependency_identity(self):self.alter('derived:0',lambda v:v['dependencies'][0].update(identity='0'*64));self.both(expected=False)
    def test_cross_support(self):self.alter('derived:0',lambda v:v['dependencies'][0].update(use=[64,128]));self.both(expected=False)
    def test_incomplete(self):self.q['members'].pop('semantic:0');self.both(expected=False)
    def test_incompatible_membership(self):self.q['members']['semantic:0']=self.q['members']['terrain:0'];self.both(expected=False)
    def test_rule_invalidation(self):
        a,b=self.both(rule='v2');self.assertEqual(b['counter']['localReused'],0);self.assertEqual(b['counter']['localChecks'],12)
    def test_unknown_rule(self):self.both(expected=False,rule='unknown')
    def test_changed_method_context(self):self.q['context']['method']='other-method';self.both(expected=False)
    def test_reference_context(self):self.q['context']['reference']='different-context';self.both(expected=False)
    def test_stale_is_historical(self):
        q=update(self.s,self.p,refresh=False);self.both(q,False);q['context']['requireFresh']=False;self.both(q,True)
    def test_invalid_receipt_falls_back(self):
        t=self.s.get(self.anchor);(self.s.objects/(t['receipts']['semantic:0']+'.json')).write_bytes(b'forged valid')
        a,b=self.both();self.assertGreater(b['counter']['fallbacks'],0)
    def test_forged_receipt_cannot_hide_invalid_component(self):
        t=self.s.get(self.anchor);h=t['receipts']['semantic:0'];(self.s.objects/(h+'.json')).write_bytes(b'{"outcome":"valid"}')
        self.alter('derived:0',lambda v:v.update(dependencies=[]));self.both(expected=False)
    def test_missing_trust_index_falls_back(self):
        t=self.s.get(self.anchor);(self.s.objects/(t['reverse']['terrain:0']+'.json')).unlink();a,b=self.both();self.assertGreater(b['counter']['fallbacks'],0)
    def test_corrupt_reverse_cannot_hide_stale(self):
        t=self.s.get(self.anchor);(self.s.objects/(t['reverse']['terrain:0']+'.json')).write_bytes(encode({'sources':[]}));self.both(update(self.s,self.p,refresh=False),False)
    def test_unknown_anchor_revalidates(self):self.both(anchor='0'*64)
    def test_candidate_cannot_designate_trust(self):
        self.q['validationAnchor']=self.anchor;self.both(expected=False)
    def test_changed_native_qualifier(self):
        v=copy.deepcopy(self.s.get(self.q['qualifier']));v['retained']['terrain']['rightsProvenance']=[];self.q['qualifier']=self.s.put(v);self.both(expected=False)
    def test_historical_method_policy(self):
        self.q['context'].update(method='changed-policy',requireFresh=False);self.both(expected=True)
    def test_invalid_identity_before_file_access(self):
        self.q['members']['semantic:0']='z'*64;a,b=self.both(expected=False)
        self.assertEqual(a['counter']['componentIntegrity'],0);self.assertEqual(b['counter']['componentIntegrity'],0)
    def test_serialized_order_counters(self):
        h=self.q['members']['semantic:0'];(self.s.objects/(h+'.json')).write_bytes(b'corrupt')
        for mode in ['full','incremental']:
            a=verdict(self.s,self.q,mode,self.anchor);b=verdict(self.s,json.loads(encode(self.q)),mode,self.anchor)
            self.assertEqual(a['accepted'],b['accepted']);self.assertEqual(a['counter'],b['counter'])
    def test_fresh_process_invalid_trust_counters(self):
        t=self.s.get(self.anchor);(self.s.objects/(t['reverse']['terrain:0']+'.json')).unlink();h=self.s.put(self.q)
        expected=verdict(self.s,self.q,'incremental',self.anchor)
        for seed in ['1','2','3']:
            q=subprocess.run([sys.executable,str(Path(__file__).with_name('worker.py')),'--store',str(self.s.path),'--publication',h,'--anchor',self.anchor,'--candidate'],capture_output=True,text=True,env={**os.environ,'PYTHONHASHSEED':seed})
            self.assertEqual(q.returncode,0,q.stderr);actual=json.loads(q.stdout);self.assertEqual(actual['counter'],expected['counter']);self.assertEqual(actual['accepted'],expected['accepted'])
    def test_determinism(self):
        a=verdict(self.s,self.q,'incremental',self.anchor);b=verdict(self.s,self.q,'incremental',self.anchor);self.assertEqual(a['counter'],b['counter']);self.assertEqual(a['publication'],b['publication'])
    def test_publication_and_pins(self):
        old=self.s.publish_checked(self.p);self.s.reset();_,pinned=self.s.resolve();new=self.s.publish_checked(self.q,'incremental',self.anchor)
        self.assertNotEqual(old,new);self.assertEqual(self.s.resolve()[0],new);self.assertEqual(self.s.resolve(old)[1],pinned);self.both(pinned)
    def test_rejection_never_advances(self):
        old=self.s.publish_checked(self.p);self.q['members'].pop('derived:0')
        with self.assertRaises(ValueError):self.s.publish_checked(self.q,'incremental',self.anchor)
        self.assertEqual(self.s.root()['generation'],old)
    def test_abrupt_interruption_and_restart(self):
        old=self.s.publish_checked(self.p);h=self.s.put(self.q)
        for point in ['after-validation','before-switch']:
            r=subprocess.run([sys.executable,str(Path(__file__).with_name('worker.py')),'--store',str(self.s.path),'--publication',h,'--anchor',self.anchor,'--publish','--fail',point],capture_output=True)
            self.assertEqual(r.returncode,79,r.stderr);fresh=Store(self.s.path);self.assertEqual(fresh.resolve()[0],old)
            with self.assertRaises(AssertionError):fresh.resolve(h)
        self.s.publish_checked(self.q,'incremental',self.anchor)
    def test_fresh_process(self):
        self.s.publish_checked(self.p)
        q=subprocess.run([sys.executable,str(Path(__file__).with_name('worker.py')),'--store',str(self.s.path),'--anchor',self.anchor],capture_output=True,text=True)
        self.assertEqual(q.returncode,0,q.stderr);v=json.loads(q.stdout);self.assertTrue(v['accepted']);self.assertEqual(v['counter']['localReused'],12)

if __name__=='__main__':unittest.main()
