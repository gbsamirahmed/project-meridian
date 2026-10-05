import unittest
import numpy as np
from terrain_scale import components, energy, lift, stats


class ScaleTests(unittest.TestCase):
    def test_identity_and_no_mutation(self):
        s=np.array([0.,20.,100.]); c=np.array([5.,8.,40.])
        original=s.copy(); q=components(s,c,np.array([0.,10.,80.]),np.array([4.,7.,39.]))
        np.testing.assert_allclose(q['raw'],q['broad']+q['detailDifference'])
        np.testing.assert_array_equal(s,original)

    def test_common_detail_not_assumed_zero(self):
        q=components(np.array([5.]),np.array([7.]),np.array([4.]),np.array([3.]))
        self.assertEqual(q['commonDetail'][0],4)
        self.assertEqual(q['detailDifference'][0],-3)

    def test_cross_term_not_error_fraction(self):
        b=np.array([1.,2.,3.]);r=np.array([-1.,-2.,-3.])
        v=energy(b+r,b,r)
        self.assertAlmostEqual(v['closure'],0)
        self.assertEqual(v['rawMeanSquare'],0)
        self.assertLess(v['twiceCrossMoment'],0)

    def test_plane_lift_cell_registration(self):
        yy,xx=np.indices((6,6));coarse=2*(xx+.5)+3*(yy+.5)
        a=lift(coarse,(8,8),(2,2),(0,0),2)
        y,x=np.indices(a.shape)
        np.testing.assert_allclose(a,2*(x+2+.5)/2+3*(y+2+.5)/2)

    def test_no_partial_interpolation(self):
        a=np.ones((4,4));a[1,1]=np.nan
        b=lift(a,(6,6),(0,0),(0,0),2)
        self.assertTrue(np.isnan(b[2,2]))
        self.assertTrue(np.isnan(b[0,0]))
        self.assertEqual(b[5,5],1)

    def test_independent_statistics(self):
        q=stats(np.array([-2.,0.,2.,np.nan]))
        self.assertEqual(q['count'],3)
        self.assertEqual(q['median'],0)
        self.assertAlmostEqual(q['rms'],np.sqrt(8/3))
        self.assertAlmostEqual(q['nmad'],2*1.4826)


if __name__=='__main__':
    unittest.main()
