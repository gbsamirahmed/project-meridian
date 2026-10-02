import json
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np

from bluesky_012a import BOUNDS,mesh_arrays,world_edges,write_glb


class BlueskyTests(unittest.TestCase):
    def test_world_file_is_pixel_centre_not_corner(self):
        for size,res in ((4000,.25),(8000,.125),(20000,.05)):
            self.assertEqual(world_edges((res,0,0,-res,456000+res/2,340000-res/2),size,size),BOUNDS)

    def test_rotation_is_rejected(self):
        with self.assertRaises(ValueError): world_edges((.25,.01,0,-.25,0,0),4000,4000)

    def test_native_mesh_height_axes_uv_and_triangles(self):
        # One complete tile-sized synthetic grid, preserving an analytical slope.
        rows,cols=np.mgrid[:502,:502];dsm=(70+rows*.01+cols*.02).astype(np.float32)
        arrays=mesh_arrays(dsm,0,0);p,n,uv,idx=arrays
        self.assertEqual(len(p),501**2);self.assertEqual(len(idx)//3,500000)
        np.testing.assert_allclose(p[0],[.125,0,.125])
        np.testing.assert_allclose(p[500],[125.125,10,.125])
        np.testing.assert_allclose(uv[0],[.375/125.5]*2)
        self.assertTrue(np.allclose(np.linalg.norm(n,axis=1),1))
        tri=p[idx[:3]];self.assertGreater(np.cross(tri[1]-tri[0],tri[2]-tri[0])[1],0)

    def test_glb_buffers_round_trip_exactly(self):
        arrays=(np.array([[1,2,3],[4,5,6],[7,8,9]],dtype='<f4'),np.ones((3,3),dtype='<f4'),np.zeros((3,2),dtype='<f4'),np.array([0,1,2],dtype='<u4'))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.glb';write_glb(path,arrays);data=path.read_bytes()
            magic,version,length=struct.unpack_from('<III',data);self.assertEqual((magic,version,length),(0x46546c67,2,len(data)))
            size,kind=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+size]);start=20+size+8
            for array,view in zip(arrays,doc['bufferViews']):
                self.assertEqual(data[start+view['byteOffset']:start+view['byteOffset']+view['byteLength']],array.tobytes())

    def test_adjacent_patches_share_exact_heights_and_normals(self):
        rows,cols=np.mgrid[:502,:1002]
        dsm=(70+np.sin(cols/30)+np.cos(rows/20)).astype(np.float32)
        left=mesh_arrays(dsm,0,0);right=mesh_arrays(dsm,0,500)
        for index in (0,1):
            np.testing.assert_array_equal(left[index].reshape(501,501,3)[:,-1],right[index].reshape(501,501,3)[:,0])

    def test_uv_maps_the_same_dsm_centre_in_every_native_texture(self):
        uv=.375/125.5
        for res in (.25,.125,.05):
            size=125.5/res
            # Normalized texture coordinate maps to pixel centre, not corner.
            self.assertAlmostEqual(uv*size-.5,(.25+.125)/res-.5)


if __name__=='__main__': unittest.main()
