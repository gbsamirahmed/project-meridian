"""Synthetic preparation tests; no external data or network dependency."""
import unittest
import numpy as np
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
import copernicus_common as cp
import riffelhorn_terrain as rt

class CommonTests(unittest.TestCase):
    def test_parent_plane_and_mean(self):
        y,x=np.mgrid[:16,:16];a=(100+x*2+y*3).astype('float32')
        b=cp.mean_parent(a)
        np.testing.assert_array_equal(b,102.5+np.mgrid[:8,:8][1]*4+np.mgrid[:8,:8][0]*6)
        self.assertEqual(float(b.mean()),float(a.mean()))

    def test_no_false_support_from_holes_or_zero(self):
        a=np.zeros((8,8),dtype='float32');a[1,1]=np.nan
        b=cp.mean_parent(a);self.assertTrue(np.isnan(b[0,0]));self.assertEqual(b[1,1],0)
        self.assertTrue(np.isnan(cp.mean_parent(b)[0,0]))
        with self.assertRaises(ValueError):rt.encode(np.full((256,256),np.nan))

    def test_extrema_smooth_without_overshoot(self):
        a=np.zeros((16,16),dtype='float32');a[3,3]=100;a[9,9]=-100
        b=cp.mean_parent(a);self.assertEqual(b.max(),25);self.assertEqual(b.min(),-25)
        self.assertEqual(b.mean(),a.mean())

    def test_encoding_independent_of_parent_aggregation(self):
        rng=np.random.default_rng(11);a=rng.uniform(-10,4500,(512,512)).astype('float32')
        parent=cp.mean_parent(a);body=rt.encode(parent)
        self.assertEqual(body,rt.encode(parent));self.assertLessEqual(np.abs(rt.decode(body)-parent).max(),1/512)

    def test_default_gdal_horizontal_axis_mapping_retains_support(self):
        a=np.full((100,100),2500,dtype='float32');out=np.full((256,256),np.nan,dtype='float32')
        from rasterio.warp import transform_bounds
        bounds=transform_bounds(4326,3857,7,45,8,46)
        reproject(a,out,src_transform=from_bounds(7,45,8,46,100,100),src_crs=4326,dst_transform=from_bounds(*bounds,256,256),dst_crs=3857,resampling=Resampling.bilinear,dst_nodata=np.nan)
        self.assertTrue(np.all(np.isfinite(out)));np.testing.assert_array_equal(out,2500)

    def test_full_descendants_and_local_support(self):
        self.assertEqual(sum(cp.extent(z)[2]*cp.extent(z)[3]for z in range(8,14)),2730)
        self.assertEqual(cp.extent(13),(4256,2880,32,64))
        with self.assertRaises(ValueError):cp.mean_parent(np.ones((3,4)))

if __name__=='__main__':unittest.main()
