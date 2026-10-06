"""Synthetic geometry / time tests; no correction and no imagery required."""
import unittest
import numpy as np
from affine import Affine
from assess import solar,normals,grid_basis,grid_sun,sampled_horizon
class Tests(unittest.TestCase):
 def test_spa_reference_coarse_agreement(self):
  # Published NREL SPA example: apparent zenith50.11162 az194.34024.
  # Different geometric/refraction/approximation model; tolerance .6deg is a test, not a global error bound.
  s=solar('2003-10-17T19:30:30Z',-105.1786,39.742476)
  self.assertLess(abs(s['azimuthTrueNorthDegrees']-194.34024),.6)
  self.assertLess(abs(90-s['geometricElevationDegrees']-50.11162),.6)
 def test_timezone_equivalence(self):
  a=solar('2023-09-07T10:00:00Z',7.76,45.98)
  b=solar('2023-09-07T12:00:00+02:00',7.76,45.98)
  self.assertEqual(a,b)
 def test_missing_timezone_rejected(self):
  with self.assertRaises(ValueError):solar('2023-09-07T10:00:00',7.7,46)
 def test_vector_unit_and_angles(self):
  s=solar('2023-09-07T10:00:00Z',7.7,46);v=s['unitENU']
  self.assertAlmostEqual(np.linalg.norm(v),1)
  self.assertGreater(v[2],0);self.assertGreater(v[0],0)
 def test_longitude_sign(self):
  a=solar('2023-03-21T08:00:00Z',30,0);b=solar('2023-03-21T08:00:00Z',-30,0)
  self.assertGreater(a['geometricElevationDegrees'],b['geometricElevationDegrees'])
 def test_leap_day(self):
  s=solar('2024-02-29T12:00:00Z',0,0);self.assertGreater(s['geometricElevationDegrees'],80)
 def test_flat_normal(self):
  n=normals(np.zeros((4,4)),.5);np.testing.assert_allclose(n,np.broadcast_to([0,0,1],n.shape))
 def test_row_north_sign(self):
  z=np.tile(np.arange(5.)[:,None],(1,5));n=normals(z,1)
  self.assertGreater(n[2,2,1],0);self.assertAlmostEqual(n[2,2,0],0)
 def test_grid_true_north(self):
  e,n=grid_basis(7.76,45.98);self.assertAlmostEqual(np.linalg.norm(e),1);self.assertAlmostEqual(np.linalg.norm(n),1)
  self.assertLess(abs(e@n),1e-5);self.assertGreater(n[1],0)
  s={'unitENU':[0,1,0]};np.testing.assert_allclose(grid_sun(s,e,n)[:2],n)
 def test_local_incidence_not_cast_shadow(self):
  z=np.zeros((25,25));z[:,15]=10
  ray=sampled_horizon(z,Affine(1,0,0,0,-1,25),[10.5,12.5],np.array([.9,0,.1]),10)
  self.assertTrue(ray['blockerWithinRadius']);self.assertGreater(np.dot([0,0,1],[.9,0,.1]),0)
 def test_no_blocker_does_not_certify_full_visibility(self):
  ray=sampled_horizon(np.zeros((25,25)),Affine(1,0,0,0,-1,25),[10.5,12.5],np.array([.9,0,.1]),10)
  self.assertFalse(ray['blockerWithinRadius']);self.assertIn('UNKNOWN',ray['stateOutsideRadius'])
 def test_insufficient_halo_rejected(self):
  with self.assertRaises(ValueError):sampled_horizon(np.zeros((25,25)),Affine(1,0,0,0,-1,25),[20.5,12.5],np.array([.9,0,.1]),10)
if __name__=='__main__':unittest.main()
