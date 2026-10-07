"""Display bounds/colour/source support safeguards; no production dependencies."""
import unittest,tempfile
from pathlib import Path
import numpy as np
import experiment as E
class Tests(unittest.TestCase):
 def test_black_and_white(self):
  a=np.array([[0,0,0],[255,255,255]],dtype='uint8')
  for amp in [4,8]:self.assertTrue(np.array_equal(E.transfer(a,amp)[0],a))
 def test_anchors_and_monotonic(self):
  i=np.linspace(0,255,100001)
  for amp in [4,8]:
   t=E.curve(i,amp);self.assertTrue((np.diff(t)>=0).all());self.assertTrue(np.array_equal(t[i<=5],i[i<=5]));self.assertTrue(np.array_equal(t[i>=80],i[i>=80]))
 def test_gain_cap_gamut_and_order(self):
  rgb=np.random.default_rng(10).integers(0,256,(10000,3),dtype='uint8')
  for amp in [4,8]:
   out,raw,g=E.transfer(rgb,amp);self.assertTrue((g<=1.5).all());self.assertLessEqual(raw.max(),255+1e-12)
   for j,k in [(0,1),(0,2),(1,2)]:self.assertFalse((((rgb[:,j].astype(float)-rgb[:,k])*(out[:,j].astype(float)-out[:,k]))<0).any())
 def test_raw_colour_ratio(self):
  a=np.array([[5,10,20],[15,12,23]],dtype='uint8');out,raw,g=E.transfer(a,8);self.assertTrue(np.allclose(raw/raw.sum(axis=1)[:,None],a/a.sum(axis=1)[:,None]))
 def test_neutral_and_quantization(self):
  grey=np.repeat(np.arange(256,dtype='uint8')[:,None],3,axis=1)
  for amp in [4,8]:
   out,_,_=E.transfer(grey,amp);self.assertTrue((out[:,0]==out[:,1]).all());self.assertLessEqual(np.diff(out[:,0].astype(int)).max(),2)
 def test_source_unchanged(self):
  a=np.array([[[4,8,12],[140,155,190]]],dtype='uint8');before=a.copy();E.transfer(a,8);self.assertTrue(np.array_equal(a,before))
 def test_constant_field_no_halo(self):
  a=np.full((12,12,3),15,dtype='uint8');out,_,_=E.transfer(a,8);self.assertEqual(len(np.unique(out.reshape(-1,3),axis=0)),1)
 def test_point_independence(self):
  a=np.array([[12,15,21],[130,145,160]],dtype='uint8');out,_,_=E.transfer(a,4);self.assertTrue(np.array_equal(out[0],E.transfer(a[:1],4)[0][0]))
 def test_no_chroma_confidence_from_hue(self):
  h,s=E.hsv(np.array([[10,10,10],[10,0,0],[0,10,0],[0,0,10]]));self.assertEqual(h.tolist(),[0,0,120,240]);self.assertEqual(s.tolist(),[0,1,1,1])
 def test_identity_amplitude(self):
  a=np.random.default_rng(2).integers(0,256,(30,3),dtype='uint8');self.assertTrue(np.array_equal(E.transfer(a,0)[0],a))
 def test_deterministic(self):
  a=np.random.default_rng(3).integers(0,256,(20,20,3),dtype='uint8');self.assertTrue(np.array_equal(E.transfer(a,8)[0],E.transfer(a,8)[0]))
 def test_predeclared_two_candidates(self):
  self.assertEqual(E.PLAN['candidateOrder'],['toe4','toe8']);self.assertEqual([c['amplitudeDN'] for c in E.PLAN['candidates'].values()],[4,8])
 def test_matched_figures_write_bounded_files(self):
  images={k:np.full((100,100,3),15,dtype='uint8') for k in E.PLAN['patches']};old=E.OUT
  try:
   with tempfile.TemporaryDirectory() as d:
    E.OUT=Path(d);E.figures(images,{});first={p.name:p.read_bytes() for p in E.OUT.iterdir()}
    E.figures(dict(reversed(list(images.items()))),{});self.assertEqual(first,{p.name:p.read_bytes() for p in E.OUT.iterdir()});self.assertEqual(len(first),3)
  finally:E.OUT=old
if __name__=='__main__':unittest.main()
