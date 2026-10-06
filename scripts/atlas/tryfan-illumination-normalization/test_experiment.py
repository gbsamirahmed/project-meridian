"""Focused safeguards for a frozen experiment stopped at its eligibility gate."""
import unittest
from unittest.mock import patch
import numpy as np
from rasterio.transform import from_origin
import experiment as e

class ProtocolTests(unittest.TestCase):
    def test_nodata_offset_and_negative_values(self):
        a=e.decode(np.array([0,900,1000,2000],dtype=np.uint16))
        self.assertTrue(np.isnan(a[0]));np.testing.assert_allclose(a[1:],[-.01,0,.1],atol=1e-15)
    def test_mean_terrain_conserves_constant(self):
        np.testing.assert_array_equal(e.aggregate(np.ones((3000,3000))*7),np.ones((300,300))*7)
    def test_wrong_terrain_shape_rejected(self):
        with self.assertRaises(ValueError):e.aggregate(np.zeros((300,300)))
    def test_north_up_folds_are_fixed(self):
        f=e.fold_grid();self.assertEqual(np.bincount(f.ravel()).tolist(),[2500]*4)
        self.assertEqual([int(f[r,c]) for r,c in [(0,0),(0,99),(99,0),(99,99)]],[0,1,2,3])
    def population(self):
        f=e.fold_grid();mu=np.tile(np.linspace(.3,1,100),(100,1));scl=np.where(np.indices((100,100))[1]%2,4,5)
        return mu,np.ones((100,100),bool),scl,f
    def test_admissible_population_passes(self):
        self.assertTrue(e.gate(*self.population())['passed'])
    def test_insufficient_one_fold_rejects_whole_design(self):
        mu,mask,scl,f=self.population();remove=(scl==5)&(f==3);mask[remove]=False
        cells=np.argwhere(remove)[:12];mask[cells[:,0],cells[:,1]]=True
        gate=e.gate(mu,mask,scl,f)
        self.assertFalse(gate['passed']);self.assertIn('SCL5 SE heldout 12<20',gate['failures'])
    def test_exact_twenty_threshold(self):
        mu,mask,scl,f=self.population();remove=(scl==5)&(f==3);mask[remove]=False
        cells=np.argwhere(remove)[:20];mask[cells[:,0],cells[:,1]]=True
        self.assertTrue(e.gate(mu,mask,scl,f)['passed'])
    def test_training_excludes_heldout_illumination(self):
        mu,mask,scl,f=self.population();mu[:]=.6;mu[f==0]=np.tile(np.linspace(.3,1,50),(50,1)).ravel()
        gate=e.gate(mu,mask,scl,f)
        row=[r for r in gate['folds'] if r['SCL']==4 and r['heldout']=='NW'][0]
        self.assertAlmostEqual(row['trainingMuP95MinusP05'],0);self.assertFalse(gate['passed'])
    def test_flat_normal_and_true_north(self):
        ns=e.old.normals(np.zeros((3,3)),10);np.testing.assert_array_equal(ns,np.tile([0,0,1],(3,3,1)))
        self.assertAlmostEqual(e.sun(0,60,(np.array([1,0]),np.array([0,1])))[2],np.sin(np.pi/3))
    def test_north_rising_terrain_normal_sign(self):
        ns=e.old.normals(np.repeat(np.array([[20],[10],[0]]),3,axis=1),10)
        self.assertLess(ns[1,1,1],0)
    def test_flat_ray_support_and_no_blocker(self):
        points=np.tile([1500.5,1500.5],(10000,1));z=np.zeros((3000,3000));sg=np.array([.5,0,np.sqrt(.75)])
        blocked,support,_=e.rays(z,from_origin(0,3000,1,1),points,sg)
        self.assertTrue(support.all());self.assertFalse(blocked.any())
    def test_ray_outside_halo_excludes_support(self):
        points=np.tile([2500.5,1500.5],(10000,1));z=np.zeros((3000,3000));sg=np.array([.5,0,np.sqrt(.75)])
        _,support,_=e.rays(z,from_origin(0,3000,1,1),points,sg)
        self.assertFalse(support.any())
    def test_ray_detects_heightfield_blocker(self):
        points=np.tile([1500.5,1500.5],(10000,1));z=np.zeros((3000,3000));z[:,1510:1520]=100
        blocked,support,_=e.rays(z,from_origin(0,3000,1,1),points,np.array([.5,0,np.sqrt(.75)]))
        self.assertTrue(blocked.all() and support.all())
    def test_texture_omits_fold_boundaries_and_excluded_cells(self):
        rgb=np.ones((100,100,3));rgb[:,50:]=2;mask=np.ones((100,100),bool);scl=np.ones((100,100),int)*4
        stats=e.texture(rgb,mask,scl,e.fold_grid());self.assertEqual(stats['4']['edges'],19600)
        self.assertEqual(stats['4']['perBandNormalizedGradientP05P50P95']['B04'],[0,0,0]);self.assertEqual(stats['5']['edges'],0)
    def test_failed_gate_no_models_or_publication(self):
        b={'gate':{'passed':False,'failures':['SCL5 SE heldout 12<20']}}
        with patch.object(e,'baseline',return_value=(b,None)),patch.object(e,'sha',return_value='test'),patch.object(e,'write'):
            _,r,_=e.run()
        self.assertEqual(r['fittedModels'],0);self.assertEqual(r['correctedCells'],0);self.assertFalse(r['correctedRepresentationPublished'])
    def test_no_silent_future_correction_on_changed_evidence(self):
        with patch.object(e,'baseline',return_value=({'gate':{'passed':True}},None)):
            with self.assertRaises(RuntimeError):e.run()

if __name__=='__main__':unittest.main()
