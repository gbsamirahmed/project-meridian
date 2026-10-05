"""Synthetic geometry/parser checks require no external metadata or image pixels."""
import tempfile, unittest
from pathlib import Path
import numpy as np
import riffelhorn_observation_support as m

class ObservationSupportTests(unittest.TestCase):
    def test_flat_and_unit_normals(self):
        n,s=m.normals(np.zeros((5,5)),.5)
        np.testing.assert_allclose(n,np.broadcast_to([0,0,1],n.shape));np.testing.assert_allclose(s,1)
    def test_row_axis_aspect(self):
        # Height rises northward: downslope/normal points south.
        h=-np.indices((5,5))[0].astype(float)
        n,s=m.normals(h,1)
        np.testing.assert_allclose(n,np.broadcast_to([0,-1,1]/np.sqrt(2),n.shape))
        angle,factor=m.incidence(n,[0,0,1]);np.testing.assert_allclose(angle,45);np.testing.assert_allclose(factor,np.sqrt(2))
    def test_frontal_and_backface(self):
        n=np.array([1.,0,1])/np.sqrt(2)
        a,f=m.incidence(n,n);self.assertAlmostEqual(float(a),0,places=6);self.assertAlmostEqual(float(f),1)
        a,f=m.incidence(n,-n);self.assertAlmostEqual(float(a),180,places=6);self.assertTrue(np.isinf(f))
        with self.assertRaises(ValueError):m.incidence(n,[0,0,0])
    def test_polygon_not_bbox(self):
        self.assertEqual(m.covered([[[0,0],[2,0],[0,2],[0,0]]],[[.2,.2],[1.8,1.8]]).tolist(),[True,False])
        with self.assertRaises(ValueError):m.covered([[],[]],[[0,0]])
        with self.assertRaises(ValueError):m.covered([[[0,0],[1,float('nan')],[1,1],[0,0]]],[[0,0]])
    def test_bad_catalogue_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.csv';p.write_text('easting;northing\n1;2\n')
            with self.assertRaises(ValueError):m.read_frames(p)
    def test_frozen_targets(self):
        self.assertEqual(m.TARGETS['steep'],(2624805,1092330,60))
        self.assertEqual(m.TARGETS['summit'],(2624810,1092252,150))
        self.assertEqual(m.TARGETS['dark-context'],(2624740,1092318,150))
    def test_image_endpoint_rejected_without_network(self):
        import json
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'docs/atlas').mkdir(parents=True)
            (root/'docs/atlas/riffelhorn-observation-support.json').write_text(json.dumps({'frozenGate':{},'metadataReceipts':[{'file':'frame.tif','url':'https://data.geo.admin.ch/frame.tif'}]}))
            with patch('urllib.request.urlopen') as request:
                with self.assertRaises(ValueError):m.fetch_metadata(root,root/'metadata')
                request.assert_not_called()
    def test_coordinate_roundtrip(self):
        from pyproj import Transformer
        a=Transformer.from_crs(2056,4326,always_xy=True);b=Transformer.from_crs(4326,2056,always_xy=True)
        q=b.transform(*a.transform(2624805,1092330));np.testing.assert_allclose(q,[2624805,1092330],atol=.01,rtol=0)

if __name__=='__main__':unittest.main()
