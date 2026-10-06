"""Focused numerical and scope safeguards, no scientific-accuracy claim."""
import unittest,math,json
from pathlib import Path
import assess as a
import numpy as np
class Safeguards(unittest.TestCase):
 def test_registered_signal(self):
  x=np.random.default_rng(7).normal(size=(90,90));r=a.search(x,x,20,40,10,.5);self.assertEqual(r['best']['eastMetres'],0);self.assertEqual(r['best']['northMetres'],0);self.assertAlmostEqual(r['best']['score'],1)
 def test_east_north_offset(self):
  x=np.random.default_rng(7).normal(size=(90,90));y=np.roll(x,(-2,4),(0,1));r=a.search(y,x,20,40,10,.5);self.assertEqual(r['best']['eastMetres'],2);self.assertEqual(r['best']['northMetres'],1)
 def test_south_west_offset(self):
  x=np.random.default_rng(9).normal(size=(90,90));y=np.roll(x,(4,-2),(0,1));r=a.search(y,x,20,40,10,.5);self.assertEqual(r['best']['eastMetres'],-1);self.assertEqual(r['best']['northMetres'],-2)
 def test_fixed_support(self):
  x=np.random.default_rng(9).normal(size=(90,90));r=a.search(x,x,20,40,10,.5);self.assertEqual(len(r['surface']),441)
 def test_no_subpixel_precision(self):
  x=np.random.default_rng(9).normal(size=(90,90));r=a.search(x,x,20,40,10,.5);self.assertTrue(all((v['eastMetres']/.5).is_integer() and (v['northMetres']/.5).is_integer() for v in r['surface']))
 def test_flat_unidentifiable(self):
  r=a.search(np.ones((90,90)),np.ones((90,90)),20,40,10,.5);self.assertIsNone(r['best']);self.assertTrue(r['ambiguous'])
 def test_missing_scope_rejected(self):
  with self.assertRaises(ValueError):a.search(np.ones((40,40)),np.ones((40,40)),5,30,10,.5)
 def test_invalid_values_rejected(self):
  x=np.ones((90,90));x[20,20]=np.nan
  with self.assertRaises(ValueError):a.search(x,x,20,40,10,.5)
 def test_brightness_not_geometry(self):
  x=np.random.default_rng(8).normal(size=(90,90));self.assertAlmostEqual(a.pearson(x,3*x+20),1);self.assertAlmostEqual(a.pearson(x,-x),-1)
 def test_smoothing_constant(self):self.assertTrue(np.allclose(a.gaussian_filter(np.ones((40,40)),2),1))
 def test_smoothing_linear_interior(self):
  x=np.tile(np.arange(50),(50,1));self.assertTrue(np.allclose(a.gaussian_filter(x,2)[10:-10,10:-10],x[10:-10,10:-10]))
 def test_stencil_halo(self):self.assertGreaterEqual(a.PLAN['haloMetres'],a.PLAN['searchHalfWidthMetres']+4*a.PLAN['smoothingSigmaCells']*.5+1)
 def test_coupling_nadir_zero(self):self.assertEqual(a.coupling(5,0),0)
 def test_coupling_linear_height(self):self.assertAlmostEqual(a.coupling(5,20),5*a.coupling(1,20))
 def test_coupling_not_observed_pose(self):self.assertAlmostEqual(a.coupling(1,30),1/math.sqrt(3))
 def test_inherited_patch_population(self):self.assertEqual(a.PLAN['patches'],{k:list(v) for k,v in a.BASE.PATCHES.items()})
 def test_declared_no_correction(self):self.assertTrue(a.PLAN['noCorrection']);self.assertTrue(a.PLAN['noSubpixelFit']);self.assertIn('not measured registration',a.PLAN['controls'])
 def test_no_new_dependencies(self):self.assertNotIn('scipy',Path(a.__file__).read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
