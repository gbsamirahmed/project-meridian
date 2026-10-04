"""Synthetic hierarchy contracts; no service or external terrain dependency."""
import unittest
import tempfile,threading
from pathlib import Path
from PIL import Image
import numpy as np
import terrain_hierarchy as h
import riffelhorn_terrain as rt

class HierarchyTests(unittest.TestCase):
    def test_exact_contributors_masks_fallback_and_missing_context(self):
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);obj=h.Hierarchy.__new__(h.Hierarchy)
            obj.data=root;obj.out=root/'output';obj.gate=14;obj.lock=threading.RLock();obj.config={'identity':'synthetic'}
            obj.common_files={};obj.swiss_files={}
            for prefix,table,z,x,y,height in [(h.cp.PRODUCT,obj.common_files,13,0,0,1000),(h.sp.PRODUCT,obj.swiss_files,13,0,0,1100),(h.sp.PRODUCT,obj.swiss_files,14,0,0,1200)]:
                key=f'tiles/{z}/{x}/{y}.png';p=root/prefix/key;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(rt.encode(np.full((256,256),height)))
                table[key]={'sha256':rt.digest(p),'path':key}
            body,row=obj.tile('H1',14,0,0)
            self.assertEqual(body,(root/h.sp.PRODUCT/'tiles/14/0/0.png').read_bytes())
            self.assertEqual(row['heightReference'],'LN02');self.assertEqual(row['contributor'],1)
            self.assertTrue(np.all(np.asarray(Image.open(obj.out/row['maskPath']))==1))
            body,row=obj.tile('H1',13,0,0)
            self.assertEqual(body,(root/h.cp.PRODUCT/'tiles/13/0/0.png').read_bytes())
            self.assertEqual(row['heightReference'],'EGM2008')
            body,row=obj.tile('H1',14,1,0)
            np.testing.assert_array_equal(rt.decode(body),1000);self.assertEqual(row['contributor'],0)
            self.assertEqual(obj.inventory()['maskLabels']['1'],'swissALTI3D LN02')
            with self.assertRaises(FileNotFoundError):obj.tile('H1',14,2,0)
            with self.assertRaises(FileNotFoundError):obj.tile('H1',7,0,0)
            # A changed mask is an error, not an anonymous cached DEM.
            Image.fromarray(np.ones((256,256),dtype='uint8')).save(obj.out/row['maskPath'])
            with self.assertRaises(ValueError):obj.inventory()

    def test_scale_does_not_create_support(self):
        for z in range(8,19):
            self.assertEqual(h.select('H0',z,False,14),0)
            self.assertEqual(h.select('H1',z,False,14),0)
            self.assertEqual(h.select('common',z,True,14),0)
        self.assertEqual(h.select('H0',12,True,14),1)
        self.assertEqual(h.select('H1',13,True,14),0)
        self.assertEqual(h.select('H1',14,True,14),1)
        with self.assertRaises(ValueError):h.select('blend',18,True,14)

    def test_cell_registration_plane_and_join(self):
        y,x=np.mgrid[-1:257,-1:257]
        a=1000+2*x+3*y
        b=h.overzoom(a,14,0,0)
        expected=1000+2*((np.arange(256)+.5)/2-.5)+3*((np.arange(256)[:,None]+.5)/2-.5)
        np.testing.assert_allclose(b,expected)
        c=h.overzoom(a,14,1,0)
        np.testing.assert_allclose(c[:,0]-b[:,-1],1)
        # Compare the same plane represented in the adjacent z13 parent.
        d=h.overzoom(a+512,14,2,0)
        np.testing.assert_allclose(d[:,0]-c[:,-1],1)

    def test_no_extra_information_or_vertical_correction(self):
        a=np.full((258,258),2987.125)
        for z in range(14,19):
            b=h.overzoom(a,z,0,0)
            np.testing.assert_array_equal(b,a[:256,:256])
        y,x=np.mgrid[:258,:258];a=2000+np.sin(x/8)*100+np.cos(y/7)*50
        b=h.overzoom(a,18,23,17)
        self.assertGreaterEqual(b.min(),a.min());self.assertLessEqual(b.max(),a.max())
        encoded=rt.encode(b)
        self.assertEqual(encoded,rt.encode(b))
        self.assertLessEqual(np.max(np.abs(rt.decode(encoded)-b)),1/512)

if __name__=='__main__':unittest.main()
