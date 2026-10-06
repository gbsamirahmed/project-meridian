"""Asset-free checks for inventory arithmetic; no runtime or retained payload writes."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import measure

class ArithmeticTests(unittest.TestCase):
    def test_groups_preserve_distinct_payload_roles(self):
        s=measure.summarize([{'path':'tiles/a','bytes':10},{'path':'tiles/b','bytes':30},{'path':'masks/a','bytes':2}])
        self.assertEqual(s['tiles']['bytes'],40);self.assertEqual(s['tiles']['objects'],2)
        self.assertEqual(s['tiles']['medianBytes'],20);self.assertEqual(s['masks']['bytes'],2)
    def test_invalid_inventory_cannot_double_count(self):
        with self.assertRaises(ValueError):measure.summarize([{'path':'tiles/a','bytes':10},{'path':'tiles/a','bytes':10}])
        with self.assertRaises(ValueError):measure.summarize([{'path':'tiles/a','bytes':-1}])
    def test_quantile_interpolates_finite_population(self):
        self.assertEqual(measure.quantile([40,10,30,20],.5),25)
        self.assertEqual(measure.quantile([40],.95),40)
        with self.assertRaises(ValueError):measure.quantile([],0)
        with self.assertRaises(ValueError):measure.quantile([1],1.1)
    def test_raw_grid_scaling_is_not_compressed_cost_estimate(self):
        self.assertEqual(measure.raw_grid_bytes(100,1,1,4),400)
        self.assertEqual(measure.raw_grid_bytes(100,.5,1,4),1600)
        self.assertEqual(measure.raw_grid_bytes(100,1,3,1),300)
        with self.assertRaises(ValueError):measure.raw_grid_bytes(100,0,1,4)
    def test_frozen_counts_distinguish_history_current_and_dependencies(self):
        d=json.loads(measure.OUT.read_text(encoding='utf-8'));q=d['qualifiedProof']
        self.assertEqual((q['claimRevisions'],q['currentResults'],q['recomputed']),(6,4,2))
        self.assertEqual((q['directInputUses'],q['derivedOnDerivedUses']),(6,3))
        self.assertEqual(sum(p['payloadFilesStatChecked'] for p in d['products']),16632)
    def test_unknown_receipt_bytes_remain_explicit(self):
        s=json.loads(measure.OUT.read_text(encoding='utf-8'))['semanticReceipts']
        self.assertEqual(len(s['mountainEntriesWithUnknownBytes']),3)
        self.assertEqual(s['worldcoverCropBytes'],9964)
        self.assertEqual(s['mountainSourceDocumentBytes'],24555804)

if __name__=='__main__':unittest.main()
