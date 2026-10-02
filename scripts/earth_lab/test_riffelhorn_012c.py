"""Independent analytical tests for the Lab's geometry and evidence screens."""
import unittest
import numpy as np
from riffelhorn_012c import triangle_closest, mesh_distances, fit_plane, normals, overlap_candidates, overlap_audit, LAS_DTYPE, rendered_normals, slice_points, project
from riffelhorn_012b import BOUNDS


class RetentionTests(unittest.TestCase):
    def test_triangle_plane_edges_vertices_and_upward_sign(self):
        t=np.array([[[0.,0,0],[2,0,0],[0,2,0]]])
        q=np.array([[.5,.5,3],[2,2,1],[-1,-1,0]])
        d,p,n=triangle_closest(q,t)
        np.testing.assert_allclose(d,[3,np.sqrt(3),np.sqrt(2)])
        np.testing.assert_allclose(p,[[.5,.5,0],[1,1,0],[0,0,0]])
        np.testing.assert_allclose(n,[[0,0,1]]*3)

    def test_adaptive_search_expands_and_is_not_vertical_difference(self):
        r,c=np.mgrid[:100,:100];grid=2500+2*(c*.5+.25)
        e,n=BOUNDS[0]+25,BOUNDS[3]-25
        d,p,normal,radius=mesh_distances(grid,np.array([[e,n,2560.]]))
        self.assertAlmostEqual(d[0],10/np.sqrt(5),places=8)
        self.assertGreater(radius[0],d[0]);self.assertGreater(radius[0],1)
        self.assertAlmostEqual(normal[0,2],1/np.sqrt(5))

    def test_pca_true_3d_plane_and_vertical_plane_without_sign_assumption(self):
        a,b=np.mgrid[-1:1:9j,-1:1:9j]
        for p,expected in ((np.column_stack([a.ravel(),b.ravel(),2*a.ravel()]),[-2,0,1]),
                           (np.column_stack([np.zeros(a.size),a.ravel(),b.ravel()]),[1,0,0])):
            n,rmse,planarity=fit_plane(p);expected=np.array(expected)/np.linalg.norm(expected)
            self.assertAlmostEqual(abs(n@expected),1);self.assertLess(rmse,1e-7);self.assertGreater(planarity,.15)

    def test_neighbourhood_uses_physical_3d_not_horizontal_radius(self):
        p=np.column_stack([np.linspace(-.2,.2,12),np.zeros(12),np.arange(12)*3])
        a=normals(p,p[:1],.5)
        self.assertEqual(a[0,5],1);self.assertTrue(np.isnan(a[0,0]))

    def test_multivalued_screen_is_not_a_heightfield_verdict(self):
        # A steep single-valued plane crosses a finite XY bin at many heights.
        x=np.array([.001,.002,.08,.081]);p=np.column_stack([x,np.zeros(4),100*x])
        self.assertEqual(len(overlap_candidates(p)),1)
        # Stacked surfaces also trigger: this screen deliberately cannot distinguish them.
        p[:,2]=[0,0,5,5];self.assertEqual(len(overlap_candidates(p)),1)
        p[:,2]=[0,.1,.2,.3];self.assertFalse(overlap_candidates(p))

    def test_slice_thickness_and_perspective_distance_are_explicit(self):
        p=np.array([[0,-.101,0],[0,-.1,0],[0,.1,0],[0,.101,0]])
        self.assertEqual(len(slice_points(p,1,0,.2)),2)
        points=np.array([[0,0,0],[1,0,0]],float);target=np.zeros(3)
        near,_=project(points,np.array([0.,-100,0]),target);far,_=project(points,np.array([0.,-200,0]),target)
        self.assertAlmostEqual(near[1,0]-near[0,0],2*(far[1,0]-far[0,0]))

    def test_coherent_sheet_screen_accepts_stacked_planes_not_steep_plane(self):
        x,y=np.mgrid[-1:1:21j,-1:1:21j];lower=np.column_stack([x.ravel(),y.ravel(),np.zeros(x.size)])
        upper=lower.copy();upper[:,2]=5;p=np.concatenate([lower,upper])
        records=np.zeros(len(p),LAS_DTYPE);records['class_flags']=2
        candidate={'indices':np.where(np.max(np.abs(p[:,:2]),axis=1)<.11)[0].tolist()}
        audit=overlap_audit(p,records,[candidate]);self.assertTrue(audit[0]['robust_two_sheet_support'])
        p[:,2]=100*p[:,0]
        self.assertFalse(overlap_audit(p,records,[candidate])[0]['robust_two_sheet_support'])

    def test_rendered_normals_retain_true_scale_and_native_diagonal(self):
        r,c=np.mgrid[:50,:50];grid=2500+2*c*.5-3*r*.5
        p=np.array([[BOUNDS[0]+10.1,BOUNDS[3]-10.2,2500]])
        expected=np.array([-2.,-3,1]);expected/=np.linalg.norm(expected)
        np.testing.assert_allclose(rendered_normals(grid,p),expected[None,:])


if __name__=='__main__':unittest.main()
