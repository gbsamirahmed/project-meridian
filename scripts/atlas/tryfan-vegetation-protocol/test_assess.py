"""Focused mask/support semantics; no fitted correction tests or hidden fitting."""
import ast,unittest
from pathlib import Path
import numpy as np
from shapely.geometry import box
import assess as a
class Safeguards(unittest.TestCase):
 def test_components_not_diagonal_independence(self):
  self.assertEqual(a.components(np.eye(3,dtype=bool)),[1,1,1])
 def test_connected_group(self):
  self.assertEqual(a.components(np.ones((2,3),bool)),[6])
 def test_empty_components(self):self.assertEqual(a.components(np.zeros((4,4),bool)),[])
 def test_point_boundary_guard(self):
  pts=np.tile([50.,50.],(10000,1));pts[0]=[1,50];pts[1]=[-1,50];pts[2]=[20,50]
  guard,d=a.guarded_support(box(0,0,100,100),pts,20)
  self.assertFalse(guard.ravel()[0]);self.assertFalse(guard.ravel()[1]);self.assertTrue(guard.ravel()[2]);self.assertEqual(d.ravel()[1],0)
 def test_guard_does_not_erode_artificial_core(self):
  pts=np.tile([5.,5.],(10000,1));guard,_=a.guarded_support(box(-100,-100,1000,1000),pts,20);self.assertTrue(guard.all())
 def test_holes_are_excluded(self):
  g=box(0,0,100,100).difference(box(40,40,60,60));pts=np.tile([50.,50.],(10000,1));guard,_=a.guarded_support(g,pts,20);self.assertFalse(guard.any())
 def test_train_excludes_entire_heldout(self):
  f=a.previous.fold_grid()
  for i in range(4):self.assertFalse((a.train_region(i)&(f==i)).any())
 def test_train_guard_not_just_other_quadrants(self):
  for i in range(4):self.assertLess(a.train_region(i).sum(),7500)
 def test_guard_is_symmetric(self):
  t=a.train_region(0);self.assertTrue(np.array_equal(t[:,::-1],a.train_region(1)));self.assertTrue(np.array_equal(t[::-1,:],a.train_region(2)))
 def test_constant_incidence_rejected_despite_many_cells(self):
  plan=a.read(a.HERE/'assessment-plan.json');g=a.support_gate(np.ones((100,100),bool),np.full((100,100),.7),np.ones((100,100,3)),plan)
  self.assertFalse(g['passed']);self.assertIn('NW: trainMuSpread',g['failures'])
 def test_empty_support_rejected_without_fake_value(self):
  p=a.read(a.HERE/'assessment-plan.json');g=a.support_gate(np.zeros((100,100),bool),np.ones((100,100)),np.ones((100,100,3)),p)
  self.assertFalse(g['passed']);self.assertIsNone(g['folds'][0]['testMuP05P50P95'])
 def test_small_cluster_is_not_enough_blocks(self):
  m=np.zeros((100,100),bool);m[:10,:10]=True;p=a.read(a.HERE/'assessment-plan.json');g=a.support_gate(m,np.tile(np.linspace(.3,1,100),(100,1)),np.ones((100,100,3)),p)
  self.assertFalse(g['passed']);self.assertIn('NW: testOccupied100mBlocks',g['failures'])
 def test_undefined_pearson_remains_unknown(self):
  self.assertIsNone(a.pearson(np.ones(20),np.arange(20)));self.assertIsNone(a.pearson(np.array([1]),np.array([2])))
 def test_spectral_empty_is_unknown_not_zero(self):
  s=a.spectral(np.ones((100,100,3)),np.zeros((100,100),bool));self.assertIsNone(s['RoverG']);self.assertEqual(s['adjacentEligibleEdges'],0)
 def test_logical_mask_hash_stable_and_sensitive(self):
  m=np.zeros((100,100),bool);h=a.mask_hash(m);self.assertEqual(h,a.mask_hash(m.copy()));m[0,0]=True;self.assertNotEqual(h,a.mask_hash(m))
 def test_no_correction_or_parameter_fit_path(self):
  tree=ast.parse(Path(a.__file__).read_text(encoding='utf-8'));names=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Call):
    if isinstance(n.func,ast.Name):names.append(n.func.id)
    elif isinstance(n.func,ast.Attribute):names.append(n.func.attr)
  self.assertFalse(set(names)&{'polyfit','lstsq','linregress','curve_fit','minimize','fit','baseline'})
  self.assertEqual(names.count('run'),1)
if __name__=='__main__':unittest.main()
