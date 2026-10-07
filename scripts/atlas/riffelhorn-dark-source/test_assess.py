"""Focused checks for support, quantization and descriptive spatial diagnostics."""
import unittest, tempfile
from pathlib import Path
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
import assess as A
class Tests(unittest.TestCase):
 def test_intensity_black_white(self):
  self.assertTrue(np.allclose(A.intensity(np.array([[0,0,0],[255,255,255]],dtype='uint8')),[0,255]))
 def test_encoded_proxy_not_gamma_decoded(self):
  self.assertAlmostEqual(A.intensity(np.array([[128,128,128]]))[0],128)
 def test_half_open_bins(self):
  self.assertEqual(A.binmask(np.array([0,5,10]),0,5).tolist(),[True,False,False])
 def test_constant_undefined(self):
  ac,c,g=A.spatial(np.ones((2,10,10)));self.assertTrue(np.isnan(ac).all() and np.isnan(c).all());self.assertTrue((g==0).all());self.assertIsNone(A.corr([1,1],[2,2]))
 def test_exact_partition_required(self):
  with self.assertRaises(ValueError):A.blocks(np.zeros((11,10)),5)
  with self.assertRaises(ValueError):A.aggregate(np.zeros((1,10,10)),3)
 def test_mean_preservation(self):
  a=np.arange(2500).reshape(1,50,50);self.assertAlmostEqual(A.aggregate(a,10).mean(),a.mean())
 def test_shuffle_histogram(self):
  a=np.arange(200).reshape(2,10,10);b=A.shuffled(a,123);self.assertTrue(np.array_equal(np.sort(a.reshape(2,-1)),np.sort(b.reshape(2,-1))));self.assertTrue(np.array_equal(b,A.shuffled(a,123)))
 def test_ramp_coherence(self):
  a=np.repeat(np.tile(np.arange(10),(10,1))[None],5,axis=0);ac,c,g=A.spatial(a);sa,sc,_=A.spatial(A.shuffled(a,123));self.assertTrue((c==1).all());self.assertGreater(ac.mean(),.9);self.assertLess(sa.mean(),.2);self.assertLess(sc.mean(),.6)
 def test_noise_comparator_not_signal_score(self):
  a=np.random.default_rng(4).normal(size=(500,10,10));ac,c,g=A.spatial(a);self.assertLess(abs(np.nanmedian(ac)),.05);self.assertGreater(np.nanmedian(c),0) # gradient tensor finite-sample bias is real
 def test_JPEG_phase_uses_source_offset(self):
  y=np.tile(np.arange(16),(16,1));a=A.phase_audit(y,0,0)['dark']['columns'];b=A.phase_audit(y,0,1)['dark']['columns'];self.assertEqual(a[0]['pairs'],16);self.assertEqual(b[1]['pairs'],16)
 def test_valid_black_is_not_nodata(self):
  with MemoryFile() as mem:
   with mem.open(driver='GTiff',height=10,width=10,count=3,dtype='uint8',crs=2056,transform=from_origin(0,1,.1,.1)) as ds:
    ds.write(np.zeros((3,10,10),dtype='uint8'));rgb,r,c=A.patch(ds,[.5,.5,1]);self.assertTrue((rgb==0).all())
 def test_missing_support_rejected(self):
  with MemoryFile() as mem:
   with mem.open(driver='GTiff',height=10,width=10,count=3,dtype='uint8',nodata=0,crs=2056,transform=from_origin(0,1,.1,.1)) as ds:
    ds.write(np.zeros((3,10,10),dtype='uint8'))
    with self.assertRaises(ValueError):A.patch(ds,[.5,.5,1])
 def test_figures_independent_of_serialization_order(self):
  images={k:np.tile(np.arange(100,dtype='uint8')[None,:,None],(100,1,3)) for k in A.PLAN['patches']}
  empty={'blocks':0};valid={'blocks':1,'contrastRMS_DN':{'0.1':[1,2,3],'1.0':[1,2,3]},'adjacency05m':[.1,.2,.3],'shuffleAdjacency05m':[-.1,0,.1]}
  st={f'{lo}-{hi}':valid if lo==10 else empty for lo,hi in zip(A.BINS[:-1],A.BINS[1:])}
  stats={k:{'blockStrata':st} for k in images};old=A.OUT
  try:
   with tempfile.TemporaryDirectory() as d:
    A.OUT=Path(d);A.figures(images,stats);first={p.name:p.read_bytes() for p in A.OUT.iterdir()}
    A.figures(dict(reversed(list(images.items()))),dict(reversed(list(stats.items()))));self.assertEqual(first,{p.name:p.read_bytes() for p in A.OUT.iterdir()})
  finally:A.OUT=old
if __name__=='__main__':unittest.main()
