"""Synthetic tests only; no external estate/server/network required."""
import tempfile
import unittest
from unittest.mock import patch
import json
from pathlib import Path
import numpy as np
import riffelhorn_terrain as terrain
from riffelhorn_terrain import AwsCache, SIZE, encode, decode, pixel_xy, tile_bounds, stable_id


class ProductTests(unittest.TestCase):
    def test_encoding_error_and_invalid_nodata(self):
        h=np.linspace(-20,3100,SIZE*SIZE).reshape(SIZE,SIZE)
        body=encode(h)
        self.assertEqual(body,encode(h))
        self.assertLessEqual(float(np.max(np.abs(decode(body)-h))),1/512+1e-9)
        for value in [np.nan,np.inf,32768,-32769]:
            with self.assertRaises(ValueError):encode(np.full((SIZE,SIZE),value))
        self.assertAlmostEqual(float(decode(encode(np.full((SIZE,SIZE),123.25)))[0,0]),123.25)

    def test_xyz_pixel_centres_and_adjacent_tile_continuity(self):
        for z in [5,15,18]:
            b=tile_bounds(z,10,11);span=b[2]-b[0]
            x,y=pixel_xy(b[0]+span/512,b[3]-span/512,z)
            self.assertAlmostEqual(float(x),10*SIZE,places=6)
            self.assertAlmostEqual(float(y),11*SIZE,places=6)
            self.assertEqual(b[2],tile_bounds(z,11,11)[0])

    def test_cross_parent_interpolation_and_no_new_height_information(self):
        class Synthetic(AwsCache):
            def tile(self,z,x,y):
                # A known plane in global pixel coordinates, crossing tile edges.
                return (x*SIZE+np.arange(SIZE)[None,:])*.001+(y*SIZE+np.arange(SIZE)[:,None])*.002
        with tempfile.TemporaryDirectory() as root:
            cache=Synthetic(Path(root))
            values=cache.sample_pixels(15,np.array([255.5,256.5]),np.array([255.5,256.5]))
            np.testing.assert_allclose(values,np.array([255.5,256.5])*.003)
            high=cache.at_tile(18,100,100)
            xx=(100*SIZE+np.arange(SIZE)[None,:]+.5)/8-.5
            yy=(100*SIZE+np.arange(SIZE)[:,None]+.5)/8-.5
            np.testing.assert_allclose(high,xx*.001+yy*.002)

    def test_identity_is_stable_and_sensitive_to_provenance(self):
        self.assertEqual(stable_id({'a':1,'b':2}),stable_id({'b':2,'a':1}))
        self.assertNotEqual(stable_id({'vertical':'LN02'}),stable_id({'vertical':'unknown'}))

    def test_verifier_rejects_provenance_drift_without_external_data(self):
        with tempfile.TemporaryDirectory() as root:
            data=Path(root);out=data/terrain.PRODUCT;out.mkdir(parents=True)
            manifest={'processing':{'scriptSha256':terrain.repository_text_digest(terrain.__file__)},
                'source':{'inputs':[{'sha256':'original'}],'catalogSha256':'frozen'},
                'files':[],'awsInputs':{},'storageBytes':0}
            manifest['identity']=stable_id(manifest)
            (out/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            with patch.object(terrain,'inspect_sources',return_value=(None,None,[{'sha256':'original'}],'frozen')):
                self.assertEqual(terrain.verify(data)['identity'],manifest['identity'])
            for inputs,catalog in [([{'sha256':'changed'}],'frozen'),([{'sha256':'original'}],'changed')]:
                with patch.object(terrain,'inspect_sources',return_value=(None,None,inputs,catalog)):
                    with self.assertRaisesRegex(ValueError,'Frozen source provenance changed'):
                        terrain.verify(data)

    def test_repository_text_hash_survives_git_line_endings(self):
        with tempfile.TemporaryDirectory() as root:
            lf=Path(root)/'lf';crlf=Path(root)/'crlf'
            lf.write_bytes(b'one\ntwo\n');crlf.write_bytes(b'one\r\ntwo\r\n')
            self.assertEqual(terrain.repository_text_digest(lf),terrain.repository_text_digest(crlf))
            self.assertNotEqual(terrain.digest(lf),terrain.digest(crlf))


if __name__=='__main__':unittest.main()
