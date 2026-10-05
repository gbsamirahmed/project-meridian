"""Synthetic support topology/count tests. No external estate dependency."""
import unittest
import numpy as np
from support_extent import connected,obstruction_path,tile_extent,tiles,estimate
from seam_corridor import feasibility

class SupportExtentTests(unittest.TestCase):
    def test_diagonal_polygons_are_not_connected(self):
        mask=np.eye(4,dtype=bool);seeds=np.zeros((4,4),bool);seeds[0,0]=True
        self.assertEqual(connected(mask,seeds).sum(),1)

    def test_multiple_seed_components_are_retained(self):
        mask=np.zeros((7,7),bool);mask[1,1:4]=True;mask[5,3:6]=True
        seeds=np.zeros_like(mask);seeds[1,1]=True;seeds[5,5]=True
        self.assertEqual(connected(mask,seeds).sum(),6)

    def test_obstruction_path_is_in_exclusion_and_adjacent(self):
        mask=np.zeros((7,7),bool);mask[:,3]=True
        seeds=np.zeros_like(mask);seeds[2,3]=True
        targets=np.zeros_like(mask);targets[6]=True
        path=obstruction_path(mask,seeds,targets)
        self.assertTrue(mask[path[:,0],path[:,1]].all())
        self.assertTrue((abs(np.diff(path,axis=0)).sum(axis=1)==1).all())
        self.assertEqual(len(path),5)

    def test_unknown_coverage_barrier_is_not_a_bypass(self):
        mask=np.ones((11,11),bool);mask[4:7,4:7]=False;mask[5:,5]=False
        self.assertFalse(feasibility(mask,np.zeros(mask.shape),(5,5))[0])
        mask[9,5]=True
        self.assertTrue(feasibility(mask,np.zeros(mask.shape),(5,5))[0])

    def test_rounding_keeps_existing_tiles_and_margin(self):
        box=tile_extent([2614500,1084550,2639800,1099950],536)
        self.assertEqual(box,[2613000,1084000,2641000,1101000])
        self.assertTrue(tiles([2620000,1087000,2630000,1097000])<=tiles(box))

    def test_counts_reuse_and_separate_area_estimates(self):
        row=estimate([2614000,1082000,2640000,1100000])
        self.assertEqual((row['tiles'],row['reuse'],row['new']),(468,100,368))
        self.assertEqual(row['sourceBytesAreaEstimate'],round(1667166026*4.68))
        self.assertEqual(row['deliveryBytesAreaEstimate'],round(930914852*4.68))
        self.assertTrue(row['notGenerated'])

    def test_non_tile_aligned_extent_rejected(self):
        with self.assertRaises(ValueError):tiles([2620001,1087000,2630000,1097000])

    def test_disconnected_target_does_not_create_witness(self):
        mask=np.eye(4,dtype=bool);seed=np.zeros_like(mask);seed[0,0]=True
        target=np.zeros_like(mask);target[3,3]=True
        self.assertIsNone(obstruction_path(mask,seed,target))

if __name__=='__main__':unittest.main()
