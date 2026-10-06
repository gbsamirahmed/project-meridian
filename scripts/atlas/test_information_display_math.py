"""Asset-free synthetic geometry and sampling checks."""
import math,unittest
import numpy as np
from information_display_math import *
class Tests(unittest.TestCase):
    def test_css_device_and_canvas_clamp(self):
        self.assertEqual(applied_ratio([1440,900],[2880,1800]),[2,2])
        np.testing.assert_allclose(applied_ratio([1440,900],[4096,2560]),[128/45,128/45])
        self.assertAlmostEqual(metres_per_pixel(60,12),metres_per_pixel(0,12)/2)
    def test_flat_plane(self):
        j=np.array([[2,0],[0,-2],[0,0.]])
        f=footprint(j,[2,2]);np.testing.assert_allclose(f['surfacePrincipalMetresPerCssPixel'],[2,2]);np.testing.assert_allclose(f['surfacePrincipalMetresPerFramebufferPixel'],[1,1]);np.testing.assert_allclose(f['normalENU'],[0,0,1])
    def test_slope_normal_and_anisotropy(self):
        j=np.array([[1,0],[0,-1],[math.sqrt(3),0.]])
        f=footprint(j);self.assertAlmostEqual(f['slopeDegrees'],60);np.testing.assert_allclose(f['mapToSurfacePrincipalStretch'],[2,1]);self.assertAlmostEqual(f['downslopeAspectDegrees'],270);np.testing.assert_allclose(f['normalENU'],[-math.sqrt(3)/2,0,.5])
    def test_sample_projection_reciprocity(self):
        j=np.array([[2,1],[0,-4],[3,5.]])
        a=sample_projection(j,1,[2,3]);b=a['framebufferPixelsPerSamplePrincipal'];c=a['samplesPerFramebufferPixelPrincipal'];np.testing.assert_allclose(b,[1/c[1],1/c[0]])
    def test_facing_away_cross_slope_not_equivalent(self):
        # Orthographic oblique screen derivative on planes: screen y=-N cos(pitch)+H sin(pitch).
        p=math.radians(55);g=math.tan(math.radians(30));sizes=[]
        for grad in [(0,g),(0,-g),(g,0)]:
            screen=np.array([[1,0],[grad[0]*math.sin(p),-math.cos(p)+grad[1]*math.sin(p)]])
            a=np.linalg.inv(screen);j=np.vstack([a,np.array(grad)@a]);sizes.append(footprint(j)['surfacePrincipalMetresPerCssPixel'][0])
        self.assertGreater(max(sizes)/min(sizes),3)
    def test_finite_difference_and_exaggeration(self):
        deg=180/(math.pi*R);o=[0,0,100]
        st={'step':2,'east':{'xyz':[2*deg,0,104]},'west':{'xyz':[-2*deg,0,96]},'north':{'xyz':[0,2*deg,100]},'south':{'xyz':[0,-2*deg,100]}}
        np.testing.assert_allclose(jacobian(o,st,2),[[1,0],[0,-1],[1,0]])
    def test_wavelength_is_bound_not_legibility(self):
        j=np.array([[1,0],[0,-4],[0,0.]])
        a=wavelength_projection(j,16,[2,2]);self.assertEqual(a['projectedCssPixelRange'],[4,16]);self.assertEqual(a['projectedFramebufferPixelRange'],[8,32])
    def test_missing_and_singular_are_not_fabricated(self):
        with self.assertRaises(ValueError):footprint(np.zeros((3,2)))
        with self.assertRaises(ValueError):sample_projection(np.ones((3,2)),0)
        with self.assertRaises(ValueError):enu([0,0,None],[0,0,0])
        self.assertIsNone(containing_tile([],[-3.999,53.115]))
    def test_tile_coverage_not_finer_unrelated_tile(self):
        p=[0,0];self.assertEqual(containing_tile([{'z':2,'x':2,'y':2},{'z':5,'x':1,'y':1}],p)['z'],2)
    def test_surface_sampling_oriented_grid(self):
        f=footprint(np.array([[1,0],[0,-1],[math.sqrt(3),0.]]))
        self.assertAlmostEqual(.25*f['mapToSurfacePrincipalStretch'][0],.5)
        self.assertAlmostEqual(.25*f['mapToSurfacePrincipalStretch'][1],.25)
if __name__=='__main__':unittest.main()
