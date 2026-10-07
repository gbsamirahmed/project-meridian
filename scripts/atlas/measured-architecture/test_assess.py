import unittest,json,subprocess,sys
from pathlib import Path
from assess import R,build,encode,pointer,digest,OUT
class AssessmentTests(unittest.TestCase):
 def setUp(self):self.e=build();self.rows={r['id']:r for r in self.e['metrics']}
 def test_deterministic_receipt(self):self.assertEqual(encode(self.e),OUT.read_text(encoding='utf-8'));self.assertEqual(encode(build()),encode(self.e))
 def test_fresh_process(self):self.assertEqual(subprocess.run([sys.executable,str(Path(__file__).with_name('assess.py')),'--check'],cwd=R,capture_output=True).returncode,0)
 def test_measured_trace(self):
  for row in self.rows.values():
   if row['classification']=='MEASURED':self.assertIsNotNone(pointer(json.loads((R/row['evidence']['file']).read_text()),row['evidence']['pointer']))
 def test_sources_pinned(self):
  for p,h in self.e['sources'].items():self.assertEqual(digest(R/p),h)
 def test_read_amplification_scope(self):
  v=self.rows['requested-read-amplification']['value'];self.assertEqual(v['requestedBytes'],31823590);self.assertEqual(v['responseBytes'],32836);self.assertAlmostEqual(v['ratio'],31823590/32836);self.assertIn('not disk',self.rows['requested-read-amplification']['qualification'])
 def test_scoped_not_global(self):
  self.assertEqual(self.rows['active-recompute-share']['value'],.5)
  for u in ['U1','U2']:self.assertEqual(len(self.rows[u+'-recomputed']['value']),2);self.assertEqual(len(self.rows[u+'-reused']['value']),2);self.assertEqual(self.rows[u+'-publication']['value']['changedArtifacts'],0)
 def test_failure_receipts(self):
  for u in ['U1','U2']:
   fs=self.rows[u+'-interruptions']['value'];self.assertEqual(len(fs),4);self.assertTrue(all(f['exitCode']==91 and f['current']==f['freshService'] for f in fs))
 def test_inventory_history(self):self.assertEqual(self.e['baselineCounts'],dict(artifacts=310,families=5,representations=8));self.assertEqual(self.rows['retained-generation-bytes']['value'],5658085)
 def test_no_measurement_precision_invention(self):self.assertEqual({r['classification'] for r in self.rows.values()},{'MEASURED','DERIVED FROM MEASUREMENTS','ESTIMATED','UNKNOWN'});self.assertIn('Illustrative',self.rows['resolution-sensitivity']['qualification'])
 def test_decision_categories_and_one_next(self):
  d=json.loads((R/'docs/research/atlas-measured-architecture-decisions.json').read_text());self.assertEqual({r['classification'] for r in d['records']},{'DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT'});self.assertEqual(d['nextExperiment']['status'],'NOT BEGUN');self.assertEqual(len({r['id'] for r in d['records']}),len(d['records']));self.assertNotIn('S7',d['nextTask'])
if __name__=='__main__':unittest.main()
