"""Synthetic checks; no retained terrain or network required."""
import unittest
import numpy as np
from copernicus_common import mean_parent
from tryfan_product import geometry
import riffelhorn_terrain as rt

class PreparationTests(unittest.TestCase):
    def test_affine_parent_conserves_mean(self):
        y,x=np.mgrid[:16,:16];a=(100+2*x+3*y).astype('float32');b=mean_parent(a)
        np.testing.assert_array_equal(b,102.5+4*np.mgrid[:8,:8][1]+6*np.mgrid[:8,:8][0]);self.assertEqual(float(a.mean()),float(b.mean()))
    def test_hole_does_not_become_valid_parent_or_zero(self):
        a=np.zeros((8,8),dtype='float32');a[0,0]=np.nan;b=mean_parent(a)
        self.assertTrue(np.isnan(b[0,0]));self.assertEqual(b[1,1],0);self.assertTrue(np.isnan(mean_parent(b)[0,0]))
    def test_support_union_retains_absent_tile_gap(self):
        g=geometry(14,[(8009,5328),(8010,5328),(8012,5328)])
        self.assertEqual(len(g['geometry']['coordinates']),2);self.assertEqual(g['geometry']['coordinates'][0][0][0][0],8009/2**14*360-180)
        self.assertIsNone(geometry(14,[]))
    def test_encoding_bounded_deterministic(self):
        a=np.linspace(0,1000,256*256,dtype='float32').reshape(256,256);body=rt.encode(a)
        self.assertEqual(body,rt.encode(a));self.assertLessEqual(np.max(abs(rt.decode(body)-a)),1/512)
        with self.assertRaises(ValueError):rt.encode(a*np.nan)

if __name__=='__main__':unittest.main()
