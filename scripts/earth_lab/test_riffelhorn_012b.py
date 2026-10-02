"""Analytical registration/scale checks, independent of Swiss payloads or Unreal."""
import unittest
import numpy as np

from riffelhorn_012b import BOUNDS, mesh_arrays, nearest_spacing, sample_grid, triangle_distance


class RiffelhornTests(unittest.TestCase):
    def test_cell_centre_bilinear_sampling_recovers_plane(self):
        r,c=np.mgrid[:8,:8]
        grid=2500+2*(c*.5+.25)+3*(r*.5+.25)
        x=np.array([BOUNDS[0]+.25,BOUNDS[0]+1,BOUNDS[0]+2.25])
        y=np.array([BOUNDS[3]-.25,BOUNDS[3]-1.5,BOUNDS[3]-2.25])
        expected=2500+2*(x-BOUNDS[0])+3*(BOUNDS[3]-y)
        np.testing.assert_allclose(sample_grid(grid,x,y),expected)
        self.assertTrue(np.isnan(sample_grid(grid,np.array([BOUNDS[0]]),np.array([BOUNDS[3]]))).all())

    def test_true_scale_axes_winding_and_native_uv(self):
        r,c=np.mgrid[:502,:502];grid=(2500+c*.1+r*.2).astype(np.float32)
        p,n,uv,indices=mesh_arrays(grid,0,0)
        np.testing.assert_allclose(p[0],[.25,0,.25])
        np.testing.assert_allclose(p[500],[250.25,50,.25])
        self.assertEqual(len(indices)//3,500000)
        self.assertGreater(np.cross(p[indices[1]]-p[indices[0]],p[indices[2]]-p[indices[0]])[1],0)
        np.testing.assert_allclose(n[100],[-.2,1,-.4]/np.linalg.norm([-.2,1,-.4]),atol=.001)
        # First mesh centre corresponds to distributed image pixel index 2, after 5-pixel apron.
        np.testing.assert_allclose(uv[0]*2510-.5,[7,7],atol=1e-6)

    def test_seam_heights_and_normals_identical(self):
        r,c=np.mgrid[:502,:1002];grid=(2500+np.sin(c/40)+np.cos(r/30)).astype(np.float32)
        left,right=mesh_arrays(grid,0,0),mesh_arrays(grid,0,500)
        for index in (0,1):
            np.testing.assert_array_equal(left[index].reshape(501,501,3)[:,-1],right[index].reshape(501,501,3)[:,0])

    def test_exact_nearest_spacing_includes_height_and_duplicates(self):
        x,y=np.mgrid[:21,:21]
        p=np.column_stack((x.ravel(),y.ravel(),np.zeros(x.size)))
        result=nearest_spacing(p,queries=50)
        self.assertEqual(result['query_count'],50)
        self.assertEqual(result['horizontal_m']['median_m'],1)
        self.assertEqual(result['three_dimensional_m']['median_m'],1)
        duplicated=np.repeat(p,2,axis=0)
        result=nearest_spacing(duplicated,queries=50)
        self.assertEqual(result['three_dimensional_m']['max_m'],0)

    def test_nearest_mesh_distance_is_geometric_not_vertical_residual(self):
        r,c=np.mgrid[:40,:40]
        grid=2500+(c*.5+.25)*2
        e,n=BOUNDS[0]+10,BOUNDS[3]-10
        # Plane z=2500+2x: +1 m vertical displacement has 1/sqrt(5) normal distance.
        p=np.array([[e,n,2521],[e,n,2520]])
        np.testing.assert_allclose(triangle_distance(grid,p),[1/np.sqrt(5),0],atol=1e-9)


if __name__=='__main__':unittest.main()
