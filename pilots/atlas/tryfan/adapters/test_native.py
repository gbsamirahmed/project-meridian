"""Labelled digital/geometry fixtures, never fabricated Tryfan observations."""
import unittest, tempfile, hashlib, json
from pathlib import Path
import rasterio
import numpy as np
from affine import Affine
from shapely.geometry import Polygon, mapping, box
from native import cell_index,members,Reader,NativeError
def grids():
    receipt=Path(__file__).resolve().parents[4]/'docs/atlas/semantic-comparison-sources.json'
    transform=next(f for f in json.loads(receipt.read_text())['files'] if f['file']=='tryfan-worldcover.tif')['subsetDefinition']['windowTransform']
    return [(Affine(1,0,0,0,-1,2),2,2),(Affine(*transform[:6]),554,334)]
class NativeAddressing(unittest.TestCase):
    def test_northwest_included(self):
        for t,w,h in grids():self.assertEqual(cell_index(t,*(t*(0,0)),w,h),(0,0))
    def test_east_south_excluded(self):
        for t,w,h in grids():
            for c,r in [(w,0),(0,h),(-.1,1),(1,-.1)]:self.assertIsNone(cell_index(t,*(t*(c,r)),w,h))
    def test_adjacent_cell_halfopen(self):
        for t,w,h in grids():
            for c,r in [(1,1),(w-1,h-1)]:self.assertEqual(cell_index(t,*(t*(c,r)),w,h),(r,c))
    def test_polygon_boundary_hole_and_multiplicity(self):
        g=Polygon([(0,0),(5,0),(5,5),(0,5)],holes=[[(1,1),(2,1),(2,2),(1,2)]])
        fs=[({'properties':{'objectid':1}},g),({'properties':{'objectid':2}},box(0,0,3,3))]
        self.assertEqual(len(members(fs,.5,.5)),2)
        self.assertTrue(members(fs,0,0)[0]['onBoundary'])
        self.assertEqual([v['id'] for v in members(fs,1.5,1.5)],['2'])
        self.assertTrue(members(fs,1,1)[0]['onBoundary'])
    def test_no_membership_not_absence(self):
        self.assertEqual(members([({'properties':{'objectid':1}},box(0,0,1,1))],2,2),[])
    def test_bbox_not_exact_intersection(self):
        g=Polygon([(0,0),(5,0),(0,5)])
        self.assertEqual(members([({'properties':{'objectid':1}},g)],4,4),[])
    def test_support_exact_intersection(self):
        f=({'properties':{'objectid':1}},box(0,0,5,5))
        self.assertEqual(members([f],0,0,[4,4,6,6])[0]['intersectionM2'],1)
    def test_corrupt_native_code_explicit_failure(self):
        # Synthetic proper-shaped raster, separately hashed; no retained file modification.
        with tempfile.TemporaryDirectory(prefix='meridian-s2-native-') as d:
            p=Path(d)/'fixture.tif';t=Affine(1/12000,0,-4,0,-1/12000,53)
            with rasterio.open(p,'w',driver='GTiff',width=554,height=334,count=1,dtype='uint8',crs='EPSG:4326',transform=t,nodata=0) as ds:
                ds.write(np.full((334,554),255,dtype='uint8'),1)
            record={'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            with self.assertRaises(NativeError) as caught:
                Reader({'core':[264900,357800,267900,360800],'gridTransform':list(t),'artifacts':{'worldcover':record}})
            self.assertEqual(caught.exception.code,'corrupt-native-code')
    def test_invalid_native_geometry_no_silent_repair(self):
        with tempfile.TemporaryDirectory(prefix='meridian-s2-native-') as d:
            p=Path(d)/'fixture.json'
            import json
            p.write_text(json.dumps({'crs':{'properties':{'name':'urn:ogc:def:crs:EPSG::27700'}},'features':[{'properties':{'objectid':1},'geometry':mapping(Polygon([(0,0),(2,2),(0,2),(2,0)]))}]}))
            record={'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            with self.assertRaises(NativeError) as caught:Reader({'core':[0,0,3,3],'artifacts':{'nrw':record}})
            self.assertEqual(caught.exception.code,'invalid-native-geometry')
if __name__=='__main__':unittest.main()
