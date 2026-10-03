"""Synthetic only; no official estate, browser, downloads or service."""
import unittest
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds
from rasterio.windows import Window
from pyproj import Transformer
import riffelhorn_support as sp
import riffelhorn_terrain as rt

class SupportTests(unittest.TestCase):
    def test_protected_interior_and_collars_are_distinct(self):
        centre=sp.CENTRE;b=sp.BOUNDS;r=sp.RADIUS
        collar=min(centre[0]-b[0],b[2]-centre[0],centre[1]-b[1],b[3]-centre[1])-r
        self.assertEqual(collar,3500);self.assertGreater(collar,2500)
        self.assertLess(np.hypot(1000,1000),r)
        self.assertEqual((b[2]-b[0],b[3]-b[1]),(10000,10000))

    def test_full_tile_support_is_not_centre_only_coverage(self):
        inv=Transformer.from_crs(3857,2056,always_xy=True)
        self.assertTrue(sp.tile_supported(12,2136,1457,inv))
        self.assertFalse(sp.tile_supported(11,1068,728,inv))
        self.assertFalse(sp.tile_supported(12,2135,1457,inv))

    def test_global_aligned_window_delivery_is_deterministic_across_tile_join(self):
        forward=Transformer.from_crs(2056,3857,always_xy=True,allow_ballpark=False);forward.transform(*sp.CENTRE)
        a=np.arange(128*128,dtype='float32').reshape(128,128)*.01+2000
        with MemoryFile()as mem:
            with mem.open(driver='GTiff',width=128,height=128,count=1,dtype='float32',crs='EPSG:2056',nodata=-9999,transform=from_bounds(2623000,1090000,2627000,1094000,128,128))as ds:
                ds.write(a,1)
                vrt,(x0,_,y0,_)=sp.warped(ds,18,forward)
                with vrt:
                    x=(136723-x0)*256;y=(93282-y0)*256
                    joint=vrt.read(1,window=Window(x,y,512,256))
                    left=vrt.read(1,window=Window(x,y,256,256));right=vrt.read(1,window=Window(x+256,y,256,256))
                    np.testing.assert_array_equal(joint,np.hstack([left,right]))
                    body=rt.encode(left);self.assertEqual(body,rt.encode(left))
                    self.assertLessEqual(float(np.max(np.abs(rt.decode(body)-left))),1/512)

    def test_nodata_is_never_encoded_as_an_authoritative_surface(self):
        with self.assertRaises(ValueError):rt.encode(np.full((256,256),np.nan))
        self.assertEqual(rt.decode(rt.encode(np.zeros((256,256)))).max(),0)

if __name__=='__main__':unittest.main()
