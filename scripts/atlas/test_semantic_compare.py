"""Synthetic, asset-free research tests; run directly with research Python."""
import unittest
import numpy as np
from pyproj import Transformer, Geod
from shapely import points
from shapely.geometry import box, Polygon
from semantic_compare import patch_box, mosaic, nrw_mapping, point_pairs, vector_summary, checked_geometry, PLAN, PLAN_SHA, sha

class SemanticComparisonTests(unittest.TestCase):
    def test_plan_is_frozen_and_patches_inside(self):
        import json
        self.assertEqual(sha(PLAN),PLAN_SHA)
        for site in json.loads(PLAN.read_text())['sites'].values():
            for p in site['patches']:self.assertTrue(box(*site['bounds']).covers(patch_box(p)))
    def test_existing_benchmark_references(self):
        import ast,json
        from pathlib import Path
        plan=json.loads(PLAN.read_text())
        aoi=json.loads(Path('scripts/earth_lab/aois/tryfan-004.json').read_text())
        x,y=aoi['center']['easting'],aoi['center']['northing']
        self.assertEqual(plan['sites']['tryfan']['bounds'],[x-1500,y-1500,x+1500,y+1500])
        tree=ast.parse(Path('scripts/atlas/swissimage_baseline.py').read_text(encoding='utf-8-sig'))
        patches=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PATCHES' for t in n.targets))
        for p in plan['sites']['riffelhorn']['patches']:
            if p['id'] in patches:self.assertEqual(tuple(p['centre']+[p['side']]),patches[p['id']])
    def test_lv95_reference_and_roundtrip(self):
        tr=Transformer.from_crs(2056,4326,always_xy=True)
        lon,lat=tr.transform(2600000,1200000)
        self.assertAlmostEqual(lon,7.4386,places=3);self.assertAlmostEqual(lat,46.9511,places=3)
        back=Transformer.from_crs(4326,2056,always_xy=True)
        x,y=back.transform(lon,lat)
        self.assertAlmostEqual(x,2600000,places=2);self.assertAlmostEqual(y,1200000,places=2)
    def test_bng_control_and_roundtrip(self):
        tr=Transformer.from_crs(27700,4326,always_xy=True)
        lon,lat=tr.transform(266405,359387)
        self.assertTrue(-4.01<lon<-3.98);self.assertTrue(53.10<lat<53.13)
        x,y=Transformer.from_crs(4326,27700,always_xy=True).transform(lon,lat)
        self.assertAlmostEqual(x,266405,places=2);self.assertAlmostEqual(y,359387,places=2)
    def test_geodesic_cell_is_not_square_ten_metres(self):
        g=Geod(ellps='WGS84'); step=1/12000
        self.assertTrue(5<g.inv(-4,53,-4+step,53)[2]<6)
        self.assertTrue(9<g.inv(-4,53,-4,53+step)[2]<10)
    def test_mosaic_unknown_preserved_without_local_allocation(self):
        m=mosaic('Mosaic of:98% B.1.1,2% ?')
        self.assertEqual(sum(c['percent'] for c in m),100)
        self.assertEqual(m[1]['code'],'?')
        self.assertEqual(nrw_mapping('mosaic','Mosaic of:98% B.1.1,2% ?')['relation'],'PARTIAL OVERLAP')
    def test_not_accessed_is_not_absence(self):
        self.assertIsNone(nrw_mapping('NA','NA')['concept'])
        self.assertIn('Not accessed',nrw_mapping('NA','NA')['loss'])
    def test_overlap_and_hole_not_forced_exclusive(self):
        donut=Polygon([(0,0),(4,0),(4,4),(0,4)],holes=[[(1,1),(1,3),(3,3),(3,1)]])
        fs=[{'id':'a','properties':{'c':'a'},'geometry':donut},{'id':'b','properties':{'c':'b'},'geometry':box(2,0,4,4)}]
        d=vector_summary(fs,box(0,0,4,4),lambda p:p['c'])
        self.assertEqual(d['uncoveredAreaM2'],2)
        self.assertEqual(d['groupOverlapM2'],6)
    def test_native_claim_pairs_preserve_multiple_and_missing(self):
        fs=[{'properties':{'c':'cover'},'geometry':box(0,0,2,2)},{'properties':{'c':'substrate'},'geometry':box(0,0,1,1)}]
        d=point_pairs(np.array([60,70]),points([.5,3],[.5,3]),np.array([2.,2.]),fs,lambda p:p['c'])
        self.assertEqual(d['unmatchedCentreAreaM2'],2)
        self.assertEqual(d['nativePairsM2'],{'60 | cover':2,'60 | substrate':2})
    def test_invalid_geometry_rejected(self):
        with self.assertRaises(ValueError):checked_geometry({'type':'Polygon','coordinates':[[[0,0],[1,1],[0,1],[1,0],[0,0]]]},'bad')
    def test_depth_of_claim_not_erased(self):
        self.assertEqual(nrw_mapping('I.1.2.1','I.1.2.1')['concept'],'mineral exposure inventory')
        self.assertEqual(nrw_mapping('E.2.1','E.2.1')['relation'],'PARTIAL OVERLAP')
        self.assertEqual(nrw_mapping('C.2','C.2')['relation'],'PARTIAL OVERLAP')

if __name__=='__main__':unittest.main()
