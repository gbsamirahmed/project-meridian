"""Asset-free physical geometry tests; never accesses public services or research assets."""
import unittest,json,tempfile,hashlib
from pathlib import Path
import numpy as np
from pyproj import Transformer
from matplotlib.path import Path as Polygon
import swiss_multiview_benchmark as m

class GeometryTests(unittest.TestCase):
    def test_flat_and_tilted_normals(self):
        y,x=np.indices((9,9));n,s=m.normals(x*2.,2)
        np.testing.assert_allclose(n[4,4],[-2**-.5,0,2**-.5]);self.assertAlmostEqual(s[4,4],2**.5)
        n,s=m.normals(-y*2.,2);self.assertLess(n[4,4,1],0) # rises north: uphill normal points south
        np.testing.assert_allclose(np.linalg.norm(n,axis=-1),1)
    def test_front_nadir_and_backface(self):
        n=np.array([np.sin(np.radians(70)),0,np.cos(np.radians(70))])
        mu,inc=m.incidence_vectors(n,[0,0,1]);self.assertAlmostEqual(float(inc),70)
        mu,inc=m.incidence_vectors(n,n);self.assertAlmostEqual(float(inc),0,places=6)
        mu,inc=m.incidence_vectors(n,-n);self.assertLess(float(mu),0)
        with self.assertRaises(ValueError):m.incidence_vectors(n,[0,0,0])
        with self.assertRaises(ValueError):m.incidence_vectors([0,0,2],[0,0,1])
    def test_material_gate_geometry(self):
        n=np.array([np.sin(np.radians(70)),0,np.cos(np.radians(70))])
        v=np.array([np.sin(np.radians(30)),0,np.cos(np.radians(30))])
        mu,inc=m.incidence_vectors(n,v);self.assertAlmostEqual(float(inc),40)
        self.assertLess(1/float(mu),2);self.assertGreater(1/n[2],2)
    def test_rotation_handedness_order_and_inverse(self):
        R=m.rotation(.2,-.4,.7);np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-14);self.assertAlmostEqual(np.linalg.det(R),1)
        np.testing.assert_allclose(m.rotation(0,0,np.pi/2)@[1,0,0],[0,1,0],atol=1e-14)
        self.assertFalse(np.allclose(R,m.rotation(0,0,.7)@m.rotation(0,-.4,0)@m.rotation(.2,0,0)))
    def test_camera_plane_and_extent(self):
        uv=m.camera_plane([[1,2,0]],[0,0,10],np.eye(3),10)
        np.testing.assert_allclose(uv,[[1,2]])
        with self.assertRaises(ValueError):m.camera_plane([[0,0,11]],[0,0,10],np.eye(3))
        with self.assertRaises(ValueError):m.camera_plane([[0,0,0]],[0,0,10],np.zeros((3,3)))
    def test_tangent_sampling_nadir_plane(self):
        major,minor=m.tangent_sampling(np.array([[0,0,0.]]),np.array([[0,0,1.]]),np.array([0,0,1000.]),np.eye(3))
        self.assertAlmostEqual(float(major[0]),1000*.00376/107)
        self.assertAlmostEqual(float(minor[0]),float(major[0]))
    def test_footprint_not_envelope(self):
        triangle=Polygon([[0,0],[10,0],[0,10],[0,0]])
        self.assertTrue(triangle.contains_point([2,2]));self.assertFalse(triangle.contains_point([9,9]))
    def test_crs_roundtrip(self):
        f=Transformer.from_crs(2056,4326,always_xy=True);b=Transformer.from_crs(4326,2056,always_xy=True)
        x,y=b.transform(*f.transform(2713830,1206710));self.assertAlmostEqual(x,2713830,places=2);self.assertAlmostEqual(y,1206710,places=2)
    def test_los_clear_and_obstructed(self):
        profile=[{'dist':d,'alts':{'DTM2':0}} for d in (0,5,10,20)]
        self.assertEqual(m.los_clearance(profile,20,0),10)
        profile[2]['alts']['DTM2']=30;self.assertEqual(m.los_clearance(profile,20,0),-20)
    def test_gori_units_and_missing_fields(self):
        fields={'x0':2713830,'y0':1206710,'z0':3800,'omega':0,'phi':0,'kappa':1.2,'focal':107,'ppx':0,'ppy':0,'ux':265.957447,'vy':-265.957447,'lines':13440,'samples':31520}
        text='\n'.join(f'{k}={v};' for k,v in fields.items())+'\nLHN95 EPSG:2056'
        self.assertEqual(m.parse_gori(text)['focal'],107)
        with self.assertRaises(ValueError):m.parse_gori(text.replace('LHN95','LN02'))
        with self.assertRaises(ValueError):m.parse_gori(text.replace('focal=107;',''))
    def test_hash_verification(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'input').write_bytes(b'abc');(p/'input-manifest.json').write_text(json.dumps({'files':[{'file':'input','sha256':hashlib.sha256(b'abc').hexdigest()}]}))
            m.verify_inputs(p);(p/'input').write_bytes(b'abd')
            with self.assertRaises(ValueError):m.verify_inputs(p)
    def test_invalid_terrain_and_angles(self):
        with self.assertRaises(ValueError):m.normals(np.zeros((3,3)),0)
        with self.assertRaises(ValueError):m.rotation(float('nan'),0,0)

if __name__=='__main__':unittest.main()
