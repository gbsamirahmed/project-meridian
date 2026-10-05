import unittest
import numpy as np
import swissimage_baseline as s
import tempfile
from pathlib import Path
import rasterio
from rasterio.transform import from_origin
from analyze_swissimage_baseline import signal

class BaselineTests(unittest.TestCase):
    def test_rgb_roundtrip(self):
        a=np.arange(256,dtype='uint8');np.testing.assert_array_equal(s.encoded(s.linear(a)),a)
    def test_linear_parent_and_alpha(self):
        c=[np.zeros((4,4,4),dtype='float32') for _ in range(4)]
        c[0][0]=1;c[0][3]=1
        a=s.parent(c)
        np.testing.assert_array_equal(a[0,:2,:2],1)
        np.testing.assert_array_equal(a[3,:2,:2],1)
        self.assertEqual(float(a[3,2:,2:].max()),0)
        c[0][:,:,::2]=0
        a=s.parent(c);self.assertEqual(float(a[3,0,0]),.5)
        self.assertEqual(int(s.rgba(a)[0,0,0]),255)
        self.assertEqual(int(s.rgba(a)[0,0,3]),128)
    def test_black_is_not_nodata(self):
        a=np.zeros((4,2,2),dtype='float32');a[3]=1
        self.assertTrue(np.all(s.rgba(a)[:,:,3]==255))
    def test_tile_grid_seam(self):
        a=s.tile_transform(18,1,2);b=s.tile_transform(18,2,2)
        self.assertAlmostEqual(a.c+s.SIZE*a.a,b.c,places=8)
    def test_frozen_scope(self):
        self.assertEqual(len(s.TILES),4);self.assertEqual(s.BOUNDS,(2624000,1091000,2626000,1093000))
        self.assertEqual((s.MIN_Z,s.MAX_Z,s.SIZE),(12,18,512))
    def test_native_window_keeps_black_and_source_seams(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rows=[]
            for i,value in enumerate([0,128]):
                p=root/f'{i}.tif'
                with rasterio.open(p,'w',driver='GTiff',height=4,width=4,count=3,dtype='uint8',crs=2056,
                                   transform=from_origin(s.BOUNDS[0]+i*.4,s.BOUNDS[3],.1,.1)) as dst:
                    dst.write(np.full((3,4,4),value,dtype='uint8'))
                rows.append({'path':p.name})
            source=s.Sources(root,rows)
            try:
                a,_=source.window((s.BOUNDS[0],s.BOUNDS[3]-.4,s.BOUNDS[0]+.8,s.BOUNDS[3]))
                np.testing.assert_array_equal(a[3],1)
                np.testing.assert_array_equal(a[:3,:,:4],0)
                np.testing.assert_array_equal(s.encoded(a[:3,:,4:]),128)
            finally:source.close()
    def test_diagnostic_luminance_black_and_white(self):
        black=signal(np.zeros((4,4,3),dtype='uint8'));white=signal(np.full((4,4,3),255,dtype='uint8'))
        self.assertEqual(black['linearMean'],0);self.assertAlmostEqual(white['linearMean'],1)
        self.assertEqual(black['exactBlackFraction'],1)
    def test_png_and_field_determinism(self):
        with tempfile.TemporaryDirectory() as d:
            a=np.zeros((4,4,4),dtype='float32');a[:3]=.2;a[3]=1
            left,right=Path(d)/'a',Path(d)/'b';one=[];two=[]
            s.write_field(left,18,1,1,a,one);s.write_field(right,18,1,1,a,two)
            self.assertEqual(one,two)

if __name__=='__main__':unittest.main()
