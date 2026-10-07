"""Accounting and decision safeguards; never fits or modifies a domain product."""
import unittest,copy
import assess as A
class Acceptance(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=A.read(A.ROOT/A.MANIFEST);cls.p=A.read(A.ROOT/A.GATES);cls.old=A.git_bytes('docs/research/atlas-research-state.md').decode('utf-8')
 def changed(self,change):
  m=copy.deepcopy(self.m);change(m)
  with self.assertRaises(ValueError):A.check_structure(m,self.p,self.old)
 def test_complete_evidence(self):self.assertTrue(A.check_structure(self.m,self.p,self.old))
 def test_missing_capability(self):self.changed(lambda m:m['coverage'].pop(0))
 def test_wrong_capability_name(self):self.changed(lambda m:m['coverage'][0].update(capability='unrelated field'))
 def test_duplicate_capability(self):self.changed(lambda m:m['coverage'].append(copy.deepcopy(m['coverage'][0])))
 def test_field_is_not_proof(self):self.changed(lambda m:m['coverage'][0].update(proofs=['META']))
 def test_unknown_proof(self):self.changed(lambda m:m['coverage'][0].update(proofs=['FAKE']))
 def test_historical_status_preserved(self):self.changed(lambda m:m['threads'][0].update(historicalStatus='CLOSED'))
 def test_missing_thread(self):self.changed(lambda m:m['threads'].pop())
 def test_parked_remains_parked(self):self.changed(lambda m:next(t for t in m['threads'] if t['id']=='A13').update(pilotClass='CLOSED'))
 def test_admission_not_build(self):self.changed(lambda m:m.update(nextTaskStarted=True))
 def test_frozen_gates(self):self.changed(lambda m:m.update(gatesSha256='0'*64))
 def test_failure_overrides_other_passes(self):
  g=copy.deepcopy(self.m['gates']);g[1]['status']='FAIL';self.assertEqual(A.decision(g,[],[]),'A - NOT READY')
 def test_specific_prerequisite(self):self.assertEqual(A.decision(self.m['gates'],['one prerequisite'],[]),'B - CONDITIONALLY READY')
 def test_conditional_gate(self):
  g=copy.deepcopy(self.m['gates']);g[0]['status']='CONDITIONAL PASS';self.assertEqual(A.decision(g,[],[]),'B - CONDITIONALLY READY')
 def test_blocker_overrides_pass(self):self.assertEqual(A.decision(self.m['gates'],[],['fundamental contradiction']),'A - NOT READY')
 def test_missing_gate_not_vote(self):
  with self.assertRaises(ValueError):A.decision(self.m['gates'][:-1],[],[])
 def test_wrong_footprint(self):self.changed(lambda m:m['pilot'].update(bounds=[0,0,1,1]))
if __name__=='__main__':unittest.main()
