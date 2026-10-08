"""Focused equivalence and packing-boundary tests; all state is external."""
import copy,unittest,uuid
from model import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.s=Store(STATE/'tests'/uuid.uuid4().hex);self.p=B.fixture(self.s,4,1);self.r=M.profile()
 def cmp(self,p=None,r=None,kind=None,expected=True):
  p=p or self.p;r=r or self.r
  f=execute(self.s,p,r);self.assertEqual(f['accepted'],expected)
  for mode in ['individual','packed','shared']:
   d=execute(self.s,self.p,self.r,mode,k=2);a=d['anchor']
   if kind=='missing':
    t=self.s.get(a);h=t['receipts']['terrain:0'] if mode=='individual' else t['directory']['terrain:0'];(self.s.objects/(h+'.json')).unlink()
   if kind=='mismatch':
    t=copy.deepcopy(self.s.get(a))
    if mode=='individual':t['receipts']['terrain:0']=t['receipts']['semantic:0']
    else:t['directory']['terrain:0']=t['directory']['semantic:0']
    a=self.s.put(t)
   if kind=='unknown':a='0'*64
   i=execute(self.s,p,r,mode,a,2);self.assertEqual(i['accepted'],expected,(mode,i['error']))
   if kind:self.assertGreater(i['validation']['fallbacks'],0)
  return f
 def test_unchanged(self):self.cmp()
 def test_local(self):self.cmp(M.update(self.s,self.p,'local',1,1))
 def test_scattered(self):self.cmp(M.update(self.s,self.p,'scattered',1,1))
 def test_broad(self):self.cmp(M.update(self.s,self.p,'all',1,1))
 def test_local_rule(self):r=M.profile();r['local']['terrain']=2;self.cmp(r=r)
 def test_cross_rule(self):r=M.profile();r['cross']=2;self.cmp(r=r)
 def test_publication_rule(self):r=M.profile();r['publication']=2;self.cmp(r=r)
 def test_context(self):p=copy.deepcopy(self.p);p['context']['requireFresh']=False;self.cmp(p)
 def test_stale_historical(self):p=B.update(self.s,self.p,refresh=False);p['context']['requireFresh']=False;self.cmp(p)
 def test_stale_current(self):self.cmp(B.update(self.s,self.p,refresh=False),expected=False)
 def test_membership(self):p=copy.deepcopy(self.p);p['members'].pop('terrain:0');self.cmp(p,expected=False)
 def test_dependency(self):
  p=copy.deepcopy(self.p);c=copy.deepcopy(self.s.get(p['members']['derived:0']));c['dependencies'][0]['slot']='terrain:99';p['members']['derived:0']=self.s.put(c);self.cmp(p,expected=False)
 def test_component_hash(self):
  anchors={m:execute(self.s,self.p,self.r,m)['anchor'] for m in ['individual','packed','shared']};(self.s.objects/(self.p['members']['terrain:0']+'.json')).write_bytes(b'bad');self.assertFalse(execute(self.s,self.p,self.r)['accepted'])
  for m,a in anchors.items():self.assertFalse(execute(self.s,self.p,self.r,m,a)['accepted'])
 def test_component_missing(self):
  anchors={m:execute(self.s,self.p,self.r,m)['anchor'] for m in ['individual','packed','shared']};(self.s.objects/(self.p['members']['terrain:0']+'.json')).unlink();self.assertFalse(execute(self.s,self.p,self.r)['accepted'])
  for m,a in anchors.items():self.assertFalse(execute(self.s,self.p,self.r,m,a)['accepted'])
 def test_component_metadata(self):
  p=copy.deepcopy(self.p);v=copy.deepcopy(self.s.get(p['members']['semantic:0']));v['records'][0]['support']=[99,100];p['members']['semantic:0']=self.s.put(v);self.cmp(p,expected=False)
 def test_missing_pack(self):self.cmp(kind='missing')
 def test_directory_mismatch(self):self.cmp(kind='mismatch')
 def test_unknown_anchor(self):self.cmp(kind='unknown')
 def test_bad_rule(self):r=M.profile();r['cross']='bad';self.cmp(r=r,expected=False)
 def test_candidate_trust(self):p=copy.deepcopy(self.p);p['anchor']='0'*64;self.cmp(p,expected=False)
 def test_identity_floor(self):
  for m in ['packed','shared']:
   a=execute(self.s,self.p,self.r,m)['anchor'];d=execute(self.s,self.p,self.r,m,a);self.assertEqual(d['validation']['componentIntegrity'],12);self.assertEqual(d['validation']['membershipChecks'],12);self.assertEqual(d['validation']['rowsChecked'],0)
 def test_group_directory(self):
  a=execute(self.s,self.p,self.r,'packed',k=2);d=execute(self.s,self.p,self.r,'shared',k=2);self.assertEqual(len(self.s.get(a['anchor'])['directory']),12);self.assertEqual(len(self.s.get(d['anchor'])['directory']),6)
 def test_pack_reuse(self):
  a=execute(self.s,self.p,self.r,'shared',k=2)['anchor'];d=execute(self.s,self.p,self.r,'shared',a,2);self.assertEqual(d['maintenance']['packsCreated'],0);self.assertEqual(d['maintenance']['packsReused'],6)
 def test_partial_rewrite(self):
  a=execute(self.s,self.p,self.r,'shared',k=2)['anchor'];p=M.update(self.s,self.p,'local',1,1);d=execute(self.s,p,self.r,'shared',a,2);self.assertEqual(d['maintenance']['packsCreated'],2);self.assertEqual(d['maintenance']['packEntriesWritten'],4)
 def test_entry_digest(self):
  a=execute(self.s,self.p,self.r,'shared',k=2)['anchor'];t=copy.deepcopy(self.s.get(a));v=copy.deepcopy(self.s.get(t['directory']['terrain:0']));v['entries']['terrain:0']['receiptIdentity']='0'*64;t['directory']['terrain:0']=self.s.put(v);a=self.s.put(t);d=execute(self.s,self.p,self.r,'shared',a,2);self.assertTrue(d['accepted']);self.assertGreater(d['validation']['fallbacks'],0)
 def test_bad_pack_bytes(self):
  a=execute(self.s,self.p,self.r,'shared',k=2)['anchor'];h=self.s.get(a)['directory']['terrain:0'];(self.s.objects/(h+'.json')).write_bytes(b'bad');d=execute(self.s,self.p,self.r,'shared',a,2);self.assertTrue(d['accepted']);self.assertGreater(d['validation']['fallbacks'],0);self.assertIsNone(d['anchor']);self.assertTrue(d['evidenceError']);self.assertRaises(ValueError,commit,self.s,self.p,d,'shared')
 def test_interruption(self):
  d=execute(self.s,self.p,self.r,'shared');old=M.commit(self.s,self.p,d)['publication'];before=(self.s.path/'current.json').read_bytes();p=M.update(self.s,self.p,'local',1,1);i=execute(self.s,p,self.r,'shared',d['anchor']);c=M.commit(self.s,p,i,True);self.assertEqual(before,(self.s.path/'current.json').read_bytes());self.assertRaises(AssertionError,self.s.resolve,c['publication']);self.s.reset();self.assertEqual(self.s.resolve(old)[0],old);self.assertEqual(self.s.c['ancestry'],0)
 def test_rejected_root(self):
  d=execute(self.s,self.p,self.r,'shared');M.commit(self.s,self.p,d);before=(self.s.path/'current.json').read_bytes();p=copy.deepcopy(self.p);p['members'].pop('semantic:0');i=execute(self.s,p,self.r,'shared',d['anchor']);self.assertRaises(ValueError,M.commit,self.s,p,i);self.assertEqual(before,(self.s.path/'current.json').read_bytes())
 def test_history_immutable(self):
  d=execute(self.s,self.p,self.r,'shared');h=M.commit(self.s,self.p,d)['publication'];b=(self.s.objects/(d['anchor']+'.json')).read_bytes();p=M.update(self.s,self.p,'local',1,1);i=execute(self.s,p,self.r,'shared',d['anchor']);M.commit(self.s,p,i);self.assertEqual(b,(self.s.objects/(d['anchor']+'.json')).read_bytes());self.s.reset();self.assertEqual(self.s.resolve(h)[0],h);self.assertEqual(self.s.c['membershipReads'],33)
 def test_directory_write_interruption(self):
  d=execute(self.s,self.p,self.r,'shared',k=2);old=commit(self.s,self.p,d,'shared')['publication'];before=(self.s.path/'current.json').read_bytes();p=M.update(self.s,self.p,'local',1,1);put=self.s.put
  def interrupted(v):
   if v['schema']=='packed-validation-root/v1':raise OSError('injected directory-write interruption')
   return put(v)
  self.s.put=interrupted
  self.assertRaises(OSError,execute,self.s,p,self.r,'shared',d['anchor'],2);self.assertEqual(before,(self.s.path/'current.json').read_bytes());self.assertRaises(AssertionError,self.s.resolve,sha(encode(p)));self.s.put=put;retry=execute(self.s,p,self.r,'shared',d['anchor'],2);commit(self.s,p,retry,'shared');self.s.reset();self.assertEqual(self.s.resolve(old)[0],old)
 def test_corrupt_pack_invalid_science(self):
  a=execute(self.s,self.p,self.r,'shared',k=2)['anchor'];h=self.s.get(a)['directory']['terrain:0'];(self.s.objects/(h+'.json')).write_bytes(b'bad');p=copy.deepcopy(self.p);p['members'].pop('semantic:0');d=execute(self.s,p,self.r,'shared',a,2);self.assertFalse(d['accepted']);self.assertIsNone(d['anchor'])
 def test_canonical(self):
  a=execute(self.s,self.p,self.r,'shared');p=copy.deepcopy(self.p);p['members']=dict(reversed(list(p['members'].items())));d=execute(self.s,p,self.r,'shared',a['anchor']);self.assertEqual(a['anchor'],d['anchor'])
if __name__=='__main__':unittest.main()
