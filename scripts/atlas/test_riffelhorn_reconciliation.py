"""Synthetic offline checks; no external products, browser or network needed."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import riffelhorn_reconciliation as r


class ReconciliationTests(unittest.TestCase):
    def test_filter_constant_and_impulse(self):
        np.testing.assert_allclose(r.gaussian(np.full((32,32),12.),4),12.,atol=1e-12)
        a=np.zeros((32,32));a[16,16]=1
        b=r.gaussian(a,4)
        self.assertEqual(np.unravel_index(np.argmax(b),b.shape),(16,16))
        self.assertAlmostEqual(b.sum(),1.,places=12)
        self.assertAlmostEqual(b[15,16],b[17,16],places=12)

    def test_distance_weights_outside_and_interior(self):
        e=np.array([2623900,2624000,2624125,2624500]);n=np.full(4,1092000)
        np.testing.assert_allclose(r.weights(r.distance(e,n),250),[0,0,.5,1])
        G=np.array([100.,110.,120.,130.]);S=G+50
        C=G+r.weights(r.distance(e,n),250)*(S-G)
        np.testing.assert_array_equal(C[:2],G[:2]);self.assertEqual(C[-1],S[-1])

    def test_adaptive_width_is_not_forced_inside_support(self):
        d=np.full((32,32),100.)
        width=r.adaptive_width(d,np.ones_like(d))
        np.testing.assert_allclose(width,100/np.tan(np.deg2rad(3)),atol=1e-10)
        self.assertGreater(float(width.min()),1000)

    def test_native_grid_registration_and_bilinear(self):
        a=np.arange(16).reshape(4,4).astype(float)
        self.assertEqual(float(r.bilinear(a,2624001,1092999)),0)
        self.assertAlmostEqual(float(r.bilinear(a,2624002,1092998)),2.5)

    def test_missing_frozen_cache_never_downloads(self):
        with tempfile.TemporaryDirectory() as root,patch.object(r.rt,'urlopen',side_effect=AssertionError('network called')):
            with self.assertRaises(FileNotFoundError):r.FrozenAws(Path(root)).tile(15,1,1)

    def test_robust_translation_known_plane(self):
        x,y=np.meshgrid(np.linspace(-1,1,20),np.linspace(-2,2,20))
        c,res=r.fit_translation(4*x-2*y+3,x,y)
        np.testing.assert_allclose(c,[4,-2,3],atol=1e-10)
        self.assertLess(res['rms'],1e-10)

    def test_manifest_identity_and_output_drift(self):
        with tempfile.TemporaryDirectory() as root:
            data=Path(root);out=data/'experiments/atlas'/r.VERSION;out.mkdir(parents=True)
            (out/'test.txt').write_text('original')
            m={'scriptSha256CanonicalLf':r.rt.repository_text_digest(r.__file__),
                'parentProductIdentity':'parent','awsInputs':{},'outputs':{'test.txt':{'sha256':r.rt.digest(out/'test.txt')}}}
            m['identity']=r.rt.stable_id(m)
            (out/'manifest.json').write_text(json.dumps(m))
            with patch.object(r.rt,'verify',return_value={'identity':'parent'}):
                self.assertEqual(r.verify_analysis(data)['identity'],m['identity'])
                (out/'test.txt').write_text('changed')
                with self.assertRaisesRegex(ValueError,'output changed'):r.verify_analysis(data)


if __name__=='__main__':unittest.main()
