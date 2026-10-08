"""Public experiment entry points; fixed predicates, receipt trust and retention tests."""
import copy,json,unittest,uuid,subprocess,sys
from model import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.s=Store(STATE/'tests'/uuid.uuid4().hex);self.p=B.fixture(self.s,4,1);self.r=profile();self.first=execute(self.s,self.p,self.r,maintain=True);self.a=self.first['anchor']
 def compare(self,p=None,r=None,anchor=None,expected=True):
  p=p or self.p;r=r or self.r;a=anchor or self.a
  f=execute(self.s,p,r);i=execute(self.s,p,r,'incremental',a,True)
  self.assertEqual((f['accepted'],i['accepted']),(expected,expected));return f,i
 def test_initial_creation(self):self.assertEqual(self.first['maintenance']['receiptsCreated'],12)
 def test_unchanged_shares(self):
  f,i=self.compare();self.assertEqual(i['validation']['rowsChecked'],0);self.assertEqual(i['maintenance']['receiptsShared'],12)
 def test_local_recompute(self):
  f,i=self.compare(update(self.s,self.p,'local',1,1));self.assertEqual(i['validation']['rowsChecked'],128);self.assertEqual(i['validation']['crossChecks'],1)
 def test_targeted_rule(self):
  r=profile();r['local']['terrain']=2;f,i=self.compare(r=r);self.assertEqual(i['validation']['rowsChecked'],256);self.assertEqual(i['validation']['localReused'],8)
 def test_cross_rule(self):
  r=profile();r['cross']=2;f,i=self.compare(r=r);self.assertEqual(i['validation']['rowsChecked'],0);self.assertEqual(i['validation']['crossChecks'],4)
 def test_publication_rule(self):
  r=profile();r['publication']=2;f,i=self.compare(r=r);self.assertEqual(i['validation']['publicationChecks'],1);self.assertEqual(i['validation']['rowsChecked'],0)
 def test_context_change(self):
  p=copy.deepcopy(self.p);p['context']['requireFresh']=False;f,i=self.compare(p);self.assertEqual(i['validation']['crossChecks'],4)
 def test_historical_policy(self):
  p=B.update(self.s,self.p,refresh=False);p['context']['requireFresh']=False;self.compare(p)
 def test_stale_current(self):self.compare(B.update(self.s,self.p,refresh=False),expected=False)
 def test_incomplete(self):
  p=copy.deepcopy(self.p);p['members'].pop('semantic:0');self.compare(p,expected=False)
 def test_broken_reference(self):
  p=copy.deepcopy(self.p);c=copy.deepcopy(self.s.get(p['members']['derived:0']));c['dependencies'][0]['slot']='terrain:99';p['members']['derived:0']=self.s.put(c);self.compare(p,expected=False)
 def test_bad_hash(self):
  (self.s.objects/(self.p['members']['terrain:0']+'.json')).write_bytes(b'broken');self.compare(expected=False)
 def test_missing_component(self):
  (self.s.objects/(self.p['members']['semantic:0']+'.json')).unlink();self.compare(expected=False)
 def test_bad_metadata(self):
  p=copy.deepcopy(self.p);c=copy.deepcopy(self.s.get(p['members']['semantic:0']));c['records'][0]['support']=[99,100];p['members']['semantic:0']=self.s.put(c);self.compare(p,expected=False)
 def test_mismatched_receipt(self):
  t=copy.deepcopy(self.s.get(self.a));t['receipts']['terrain:0']=t['receipts']['semantic:0'];a=self.s.put(t);f,i=self.compare(anchor=a);self.assertGreater(i['validation']['fallbacks'],0)
 def test_missing_receipt(self):
  t=self.s.get(self.a);(self.s.objects/(t['receipts']['terrain:0']+'.json')).unlink();f,i=self.compare();self.assertGreater(i['validation']['fallbacks'],0)
 def test_unknown_anchor(self):
  f,i=self.compare(anchor='0'*64);self.assertGreater(i['validation']['fallbacks'],0)
 def test_issuer_context_immutable(self):
  b=(self.s.objects/(self.a+'.json')).read_bytes();self.compare(update(self.s,self.p,'local',1,1));self.assertEqual(b,(self.s.objects/(self.a+'.json')).read_bytes())
 def test_reverse_carry_forward(self):
  p=update(self.s,self.p,'local',1,1);f,i=self.compare(p);t=self.s.get(i['anchor']);self.assertEqual(self.s.get(t['reverse']['terrain:1'])['sources'],['derived:1'])
 def test_selective_issuer(self):
  f,i=self.compare(update(self.s,self.p,'local',1,1));self.assertEqual(i['maintenance']['receiptsCreated'],2);self.assertEqual(i['maintenance']['outgoingChanged'],2);self.assertEqual(i['maintenance']['reverseChanged'],1)
 def test_rule_identity_bound(self):self.assertNotEqual(rid('local:terrain',1),rid('local:terrain',2))
 def test_no_candidate_anchor(self):
  p=copy.deepcopy(self.p);p['anchor']=self.a;self.compare(p,expected=False)
 def test_integrity_floor(self):
  f,i=self.compare();self.assertEqual(i['validation']['componentIntegrity'],12);self.assertEqual(i['validation']['membershipChecks'],12)
 def test_invalid_rule(self):
  r=profile();r['cross']='bad';self.compare(r=r,expected=False)
 def test_interrupted_root(self):
  publish(self.s,self.p,self.r);before=(self.s.path/'current.json').read_bytes();p=update(self.s,self.p,'local',1,1);d,c=publish(self.s,p,self.r,self.a,True);self.assertEqual(before,(self.s.path/'current.json').read_bytes());self.assertRaises(AssertionError,self.s.resolve,c['publication'])
 def test_rejected_root(self):
  publish(self.s,self.p,self.r);before=(self.s.path/'current.json').read_bytes();p=copy.deepcopy(self.p);p['members'].pop('terrain:0');self.assertRaises(ValueError,publish,self.s,p,self.r,self.a);self.assertEqual(before,(self.s.path/'current.json').read_bytes())
 def test_historical_resolution(self):
  d,c=publish(self.s,self.p,self.r);old=c['publication'];p=update(self.s,self.p,'local',1,1);publish(self.s,p,self.r,d['anchor']);self.s.reset();h,q=self.s.resolve(old);self.assertEqual(h,old);self.assertEqual(self.s.c['ancestry'],0);self.assertEqual(self.s.c['membershipReads'],33)
 def test_fresh_process(self):
  publish(self.s,self.p,self.r);h=sha(encode(self.p));out=subprocess.check_output([sys.executable,str(HERE/'worker.py'),'--store',str(self.s.path),'--publication',h,'--anchor',self.a,'--rules',json.dumps(self.r)],text=True,encoding='utf-8');v=json.loads(out);self.assertTrue(v['accepted']);self.assertEqual(v['validation']['rowsChecked'],0)
 def test_canonical_order(self):
  p=copy.deepcopy(self.p);p['members']=dict(reversed(list(p['members'].items())));f,i=self.compare(p);self.assertEqual(i['anchor'],self.a)
 def test_low_reuse_no_false_savings(self):
  f,i=self.compare(update(self.s,self.p,'all',1,1));self.assertEqual(i['validation']['localChecks'],8);self.assertEqual(i['validation']['localReused'],4)
if __name__=='__main__':unittest.main()
