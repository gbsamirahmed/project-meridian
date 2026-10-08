import unittest,uuid,copy,json,subprocess,sys
from pathlib import Path
from model import Store,STATE,PLAN,records,build,query,expected,audit,encode,sha,templates
class Tests(unittest.TestCase):
 def fixture(self,family='terrain',n=128,strategy='moderate'):
  s=Store(STATE/('test-'+str(uuid.uuid4())));rows=records(family,n);q=s.put({'schema':'granularity-qualifier/v1','family':family,'test':'labelled fixture'});p=build(s,rows,strategy,q,family);g,_=s.publish(p);return s,rows,p,g
 def test_frozen_hypotheses(self):self.assertEqual(len(PLAN['hypotheses']),5);self.assertEqual(PLAN['populations'],[128,512,2048])
 def test_exact_selection_all_families_organisations(self):
  for f in PLAN['families']:
   for strategy in PLAN['strategies']:
    s,rows,p,g=self.fixture(f,strategy=strategy)
    for kind in ['narrow','area','broad','feature']:
     s.reset();a=query(s,g,kind);self.assertEqual(a['records'],expected(rows,f,kind));self.assertEqual(s.c['membershipReads'],33);self.assertEqual(s.c['ancestry'],0)
 def test_record_identity_location_independent(self):
  a=Store(STATE/('test-'+str(uuid.uuid4())));b=Store(STATE/('test-'+str(uuid.uuid4())));v={'schema':'test/v1','source':'same'};self.assertEqual(a.put(v),b.put(v))
 def test_canonical_determinism(self):self.assertEqual(encode({'b':2,'a':1}),encode({'a':1,'b':2}))
 def test_native_template_not_rewritten(self):
  t=templates();self.assertEqual(t['worldcover']['templates'][0]['binding']['assignment'][:11],'Native code');self.assertIn('revision',t['derived']['templates'][0]['claim'])
 def test_selected_corruption(self):
  s,_,p,g=self.fixture();file=s.objects/(p['members'][1]['id']+'.json');file.write_bytes(file.read_bytes()+b' ');s.reset();self.assertRaises(AssertionError,query,s,g,'narrow')
 def test_missing_selected(self):
  s,_,p,g=self.fixture();(s.objects/(p['members'][1]['id']+'.json')).unlink();s.reset();self.assertRaises(FileNotFoundError,query,s,g,'narrow')
 def test_unknown_generation(self):s,_,_,_=self.fixture();s.reset();self.assertRaises(AssertionError,s.resolve,'0'*64)
 def test_unpublished_complete_candidate(self):
  s,rows,p,g=self.fixture();before=(s.path/'current.json').read_bytes();new={**p,'ordinal':2,'predecessor':g};h,_=s.publish(new,fail=True);s.reset();self.assertRaises(AssertionError,s.resolve,h);self.assertEqual((s.path/'current.json').read_bytes(),before);self.assertEqual(s.resolve()[0],g)
 def test_history_direct_after_switch(self):
  s,rows,p,g=self.fixture();new={**p,'ordinal':2,'predecessor':g};h,_=s.publish(new);s.reset();self.assertEqual(query(s,g,'narrow')['records'],query(s,h,'narrow')['records']);self.assertEqual(s.root()['generation'],h)
 def test_false_bounding_descriptor_rejected_before_switch(self):
  s,rows,p,g=self.fixture();before=s.root();p=copy.deepcopy(p);p['members'][0]['bounds']=[9000,9001];p.update(predecessor=g,ordinal=2);self.assertRaises(AssertionError,s.publish,p);self.assertEqual(s.root(),before)
 def test_internal_selective_path_verified(self):
  s,rows,p,g=self.fixture(n=2048,strategy='selective');s.reset();a=query(s,g,'narrow');self.assertEqual(len(a['records']),1);self.assertLess(s.c['recordsInspected'],2048);self.assertGreater(s.c['pages'],0)
 def test_between_requests_cache_not_trusted(self):
  s,_,p,g=self.fixture();s.reset();query(s,g,'narrow');f=s.objects/(p['members'][1]['id']+'.json');f.write_bytes(f.read_bytes()+b' ');s.reset();self.assertRaises(AssertionError,query,s,g,'narrow')
 def test_source_methods_and_actual_scope_preserved(self):
  t=templates()['derived']['templates'];self.assertIn('method',t[0]['receipt']);self.assertIn('spatial',t[0]['receipt']['inputs'][0]);self.assertIn('methodRevision',t[0]['receipt'])
 def test_dependency_pair(self):
  r=records('derived',128);self.assertEqual(r[65]['upstream'],64);self.assertNotEqual(r[64]['inputUse'],r[64]['support']);self.assertEqual(len(expected(r,'derived','narrow')),2)
 def test_component_replacement_not_recompute(self):
  s,rows,p,g=self.fixture(strategy='fine');changed=copy.deepcopy(rows);changed[64]['syntheticApplicabilityRevision']=1;s.reset();new=build(s,changed,'fine',p['qualifier'],'terrain');self.assertEqual(s.c['newObjects'],1);self.assertEqual(len(set(m['id'] for m in p['members'])&set(m['id'] for m in new['members'])),127)
 def test_independent_reader(self):
  s,rows,p,g=self.fixture();r=json.loads(subprocess.check_output([sys.executable,str(Path(__file__).parent/'run.py'),'--worker',str(s.path),g,'narrow'],text=True,encoding='utf-8'));self.assertEqual(r['samples'][0]['required'],1)
if __name__=='__main__':unittest.main()
