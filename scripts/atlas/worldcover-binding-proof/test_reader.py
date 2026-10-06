"""Synthetic native affine boundaries and CRS roundtrip; retained production is not touched."""
import unittest
from affine import Affine
from pyproj import Transformer
from reader import cell_index
class Tests(unittest.TestCase):
 def test_half_open_edges(self):
  t=Affine(1,0,0,0,-1,2)
  self.assertEqual(cell_index(t,0,2,2,2),(0,0));self.assertEqual(cell_index(t,1,1,2,2),(1,1))
  self.assertIsNone(cell_index(t,2,1,2,2));self.assertIsNone(cell_index(t,1,0,2,2))
  self.assertIsNone(cell_index(t,-.01,1,2,2))
 def test_crs_roundtrip(self):
  a=Transformer.from_crs(27700,4326,always_xy=True);b=Transformer.from_crs(4326,27700,always_xy=True)
  x,y=b.transform(*a.transform(266405,359387));self.assertAlmostEqual(x,266405,places=2);self.assertAlmostEqual(y,359387,places=2)
if __name__=='__main__':unittest.main()
