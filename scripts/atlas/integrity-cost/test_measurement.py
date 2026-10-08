"""Tests protect attribution, equivalence and frozen guarantees, not timing speedups."""
import unittest,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
class AssessmentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.p=json.loads((H/'plan.json').read_text());cls.x=json.loads((R/'docs/research/atlas-integrity-cost-results.json').read_text())
 def test_frozen_criteria_and_authoritative_code(self):
  self.assertEqual(hashlib.sha256((H/'plan.json').read_bytes()).hexdigest(),'48f3cc4b0c3ae8cf2da7d5494ef4352b5d1f045bbca165b820b6ea8c6baaafce')
  for p,h in self.p['authoritativeHashes'].items():self.assertEqual(hashlib.sha256((R/p).read_bytes()).hexdigest(),h,p)
 def test_plain_meter_exact_outcomes(self):
  self.assertEqual(len(self.x['node']),14)
  for c in self.x['node']:self.assertEqual([x['value'] for x in c['observations']['plain']['samples']],[x['value'] for x in c['observations']['meter']['samples']],c['id'])
 def test_exclusive_times_do_not_double_count(self):
  for c in self.x['node']:
   for s in c['observations']['meter']['samples']:
    self.assertLessEqual(sum(v['exclusiveMs'] for v in s['ops'].values()),s['milliseconds']+.001)
    for v in s['ops'].values():self.assertGreaterEqual(v['exclusiveMs'],-.001);self.assertLessEqual(v['exclusiveMs'],v['inclusiveMs']+.001)
 def test_payload_population_and_byte_controls(self):
  for c in self.x['node']:
   if c['action']=='payload':
    for s in c['observations']['meter']['samples']:
     self.assertEqual(s['value'],{'artifacts':c['artifacts'],'bytes':c['payloadBytes']});self.assertEqual(s['reads']['payload']['bytes'],c['payloadBytes']);self.assertEqual(s['ops']['statSync']['calls'],2*c['artifacts']);self.assertEqual(s['hashes']['buffer']['calls'],c['artifacts'])
 def test_complete_full_metadata_floor(self):
  for c in self.x['metadata']['meter']['rows']:
   if c['kind']=='population':
    for s in c['samples']:
     self.assertEqual(s['counter']['componentIntegrity'],3*c['case']['n']);self.assertEqual(s['counter']['membershipChecks'],3*c['case']['n']);self.assertEqual(s['counter']['crossChecks'],c['case']['n']*c['case']['fanout']);self.assertEqual(s['counter']['rowsChecked'],3*c['case']['n']*64)
 def test_unchanged_and_localized_recheck_current_bytes(self):
  for c in self.x['metadata']['meter']['rows']:
   if c['kind']=='sequence':
    for rep in c['repeats']:
     for row in rep['rows']:
      self.assertEqual(row['validation']['counter']['componentIntegrity'],192);self.assertEqual(row['commit']['counter']['componentIntegrity'],192);self.assertTrue(row['commit']['committed'])
 def test_history_has_no_ancestry(self):
  for c in self.x['node']:
   if c['action']=='history':
    for s in c['observations']['meter']['samples']:self.assertEqual(s['files']['membership']['calls'],33);self.assertEqual(s['files']['components']['calls'],5);self.assertEqual(s['files']['publications']['calls'],1)
  for c in self.x['metadata']['meter']['rows']:
   if c['kind']=='sequence':
    for r in c['repeats']:self.assertEqual(r['current']['ancestry'],0);self.assertEqual(r['historical']['ancestry'],0)
 def test_failures_preserve_root_and_reject(self):
  self.assertEqual(len(self.x['failures']),9)
  self.assertTrue(all(f['rootPreserved'] and f['code'] for f in self.x['failures']))
  for mode in ['plain','meter']:self.assertTrue(all(not f['accepted'] and f['rootPreserved'] for f in self.x['metadata'][mode]['failures']))
if __name__=='__main__':unittest.main()
