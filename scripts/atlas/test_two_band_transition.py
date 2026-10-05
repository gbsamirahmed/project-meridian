import unittest
import numpy as np
import tempfile
import threading
from pathlib import Path
from two_band_transition import compose,weights,weight_derivative,Transition,rt
from finish_two_band import spill_depth


class TwoBandTests(unittest.TestCase):
    def test_frozen_endpoints_and_monotonic(self):
        r=np.linspace(0,5000,10001);b,d=weights(r)
        self.assertTrue(np.all(np.diff(b)<=1e-12));self.assertTrue(np.all(np.diff(d)<=1e-12))
        np.testing.assert_array_equal(b[r<=1500],1);np.testing.assert_array_equal(d[r<=3000],1)
        np.testing.assert_array_equal(b[r>=4000],0);np.testing.assert_array_equal(d[r>=4000],0)

    def test_pure_endpoints_unchanged_and_inputs_immutable(self):
        r=np.array([0.,1500.,3000.,3500.,4000.,5000.]);s=np.arange(6.)+50;c=np.arange(6.)+10
        original=s.copy();t,b,d,label=compose(s,c,s-3,c-1,r)
        np.testing.assert_array_equal(t[:2],s[:2]);np.testing.assert_array_equal(t[-2:],c[-2:])
        np.testing.assert_array_equal(label,[1,1,2,3,0,0]);np.testing.assert_array_equal(s,original)
        np.testing.assert_array_equal(d[:3],1)

    def test_exact_operator_retains_common_residual(self):
        r=np.array([3500.]);s=np.array([70.]);c=np.array([20.]);sb=np.array([50.]);cb=np.array([15.])
        t,b,d,_=compose(s,c,sb,cb,r)
        np.testing.assert_allclose(t,cb+b*(sb-cb)+d*(s-sb)+(1-d)*(c-cb))
        np.testing.assert_allclose(t,d*s+(1-d)*c+(b-d)*(sb-cb))

    def test_absent_support_never_padded(self):
        with self.assertRaises(ValueError):compose(np.array([np.nan]),np.array([1.]),np.array([2.]),np.array([3.]),np.array([2000.]))
        t,*_=compose(np.array([np.nan]),np.array([1.]),np.array([np.nan]),np.array([np.nan]),np.array([4500.]))
        self.assertEqual(t[0],1)

    def test_derivative_matches_finite_difference(self):
        r=np.array([1700.,2500.,3500.]);eps=.01
        b1,_=weights(r+eps);b0,_=weights(r-eps)
        np.testing.assert_allclose((b1-b0)/(2*eps),weight_derivative(r,1500,2500),atol=1e-10)
        self.assertEqual(weight_derivative(np.array([1500.]),1500,2500)[0],0)

    def test_identical_surfaces_remain_identical(self):
        r=np.arange(0,5001,25.);s=100+r*.05
        t,*_=compose(s,s,s-2,s-2,r)
        np.testing.assert_allclose(t,s,atol=1e-12)

    def test_encoded_product_and_masks_rebuild_without_external_assets(self):
        def fixture(path):
            t=Transition.__new__(Transition);t.out=Path(path);t.lock=threading.RLock()
            t.config={'identity':'synthetic-fixture'}
            t.retained={'glacier250Mask':np.zeros((400,400),bool)}
            radius=np.broadcast_to(np.linspace(0,5000,256),(256,256)).copy()
            shape=radius.shape;s=np.full(shape,100.);c=np.full(shape,200.)
            t.coordinates=lambda z,x,y:(2625000+radius,np.full(shape,1092000.),radius,radius,radius)
            t.values=lambda z,x,y:compose(s,c,s-3,c-1,radius)
            return t,radius
        with tempfile.TemporaryDirectory() as root:
            t,r=fixture(Path(root)/'first');u,_=fixture(Path(root)/'second')
            body,row=t.tile('transition',14,1,1);again,other=u.tile('transition',14,1,1)
            self.assertEqual(body,again);self.assertEqual(row,other)
            values=rt.decode(body)
            np.testing.assert_array_equal(values[r<=1500],100)
            np.testing.assert_array_equal(values[r>=4000],200)
            with np.load(t.out/row['maskPath']) as a:
                np.testing.assert_array_equal(a['detailWeight'][r<=3000],1)
                np.testing.assert_array_equal(a['detailWeight'][r>=4000],0)
                np.testing.assert_array_equal(a['labels'][r<=1500],1)
                np.testing.assert_array_equal(a['labels'][r>=4000],0)

    def test_pit_check_has_fixed_outlets_not_a_terrain_correction(self):
        a=np.full((5,5),10.);a[2,2]=7.;old=a.copy()
        depth=spill_depth(a)
        self.assertEqual(depth[2,2],3)
        np.testing.assert_array_equal(a,old)
        plane=np.broadcast_to(np.arange(5.),(5,5)).copy()
        np.testing.assert_array_equal(spill_depth(plane),0)


if __name__=='__main__':unittest.main()
