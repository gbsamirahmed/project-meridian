"""Primitive comparisons run before any reader substitution; no altered expectations."""
import json
import math
import os
from pathlib import Path
import sys
import unittest
from native import NativeGeos, GeometryError
from shapely.geometry import Point, Polygon, MultiPolygon, box, mapping, shape
from shapely import GEOSException
import numpy as np

class Primitive(unittest.TestCase):
    def test_boundaries_holes_multipart_and_serialisation(self):
        outer=[(0,0),(4,0),(4,4),(0,4),(0,0)];hole=[(1,1),(3,1),(3,3),(1,3),(1,1)]
        source=MultiPolygon([Polygon(outer,[hole]),box(6,0,7,1)])
        points=[((.5,.5),True),((0,2),True),((1,2),True),((2,2),False),((6.5,.5),True),((5,5),False)]
        with NativeGeos() as ctx:
            g=ctx.from_json(mapping(source))
            self.assertEqual(g.wkb,source.wkb);self.assertEqual(g.__geo_interface__,mapping(source))
            self.assertEqual(g.bounds,source.bounds);self.assertEqual(g.area,source.area)
            for xy,expected in points:
                with ctx.temporary_point(*xy) as p:
                    self.assertEqual(g.covers(p),expected);self.assertEqual(g.covers(p),source.covers(Point(xy)))
                    self.assertEqual(p.wkb,Point(xy).wkb)
            xs=np.array([[0,1,2],[6.5,5,.5]]);ys=np.array([[2,2,2],[.5,5,.5]])
            self.assertEqual(ctx.covers_points(g,xs,ys).tolist(),[[True,True,False],[True,False,True]])
            # Allocation failure must release the prepared handle, not yield empty evidence.
            from unittest.mock import patch
            destroy=ctx.lib.GEOSPreparedGeom_destroy_r
            with patch.object(np,'empty',side_effect=MemoryError('injected centre allocation')), patch.object(ctx.lib,'GEOSPreparedGeom_destroy_r',wraps=destroy) as released:
                with self.assertRaises(MemoryError):ctx.covers_points(g,xs,ys)
                self.assertEqual(released.call_count,1)
        print(json.dumps({'boundaryPointCases':6,'centreMaskCases':6}))

    def test_intersection_order_and_positive_area(self):
        a=box(0,0,4,4);multi=MultiPolygon([a,box(6,0,7,1)])
        cases=[(a,box(3,0,5,4)),(a,box(4,0,5,4)),(a,box(4,4,5,5)),
               (a,box(math.nextafter(4,-math.inf),0,5,4)),(a,box(5,5,6,6)),
               (multi,box(3,0,6.5,4)),(box(2624000,1091000,2626000,1093000),box(2623999,1090999,2624000.01,1091000.01))]
        with NativeGeos() as ctx:
            for first,second in cases:
                with ctx.arena():
                    result=ctx.from_wkb(first.wkb).intersection(ctx.from_wkb(second.wkb));expected=first.intersection(second)
                    self.assertEqual(result.area,expected.area);self.assertEqual(result.is_empty,expected.is_empty)
                    self.assertEqual(result.geom_type,expected.geom_type);self.assertEqual(result.wkb,expected.wkb)
                    self.assertEqual(result.__geo_interface__,mapping(expected))
            self.assertEqual(len(ctx.owned),0)
        self.assertEqual(cases[1][0].intersection(cases[1][1]).area,0)
        self.assertEqual(cases[2][0].intersection(cases[2][1]).area,0)
        self.assertGreater(cases[3][0].intersection(cases[3][1]).area,0)
        print(json.dumps({'exactOverlayCases':len(cases)}))

    def test_empty_invalid_and_malformed_are_not_false_evidence(self):
        invalid=Polygon([(0,0),(2,2),(0,2),(2,0),(0,0)])
        with NativeGeos() as ctx:
            g=ctx.from_wkb(invalid.wkb)
            self.assertFalse(g.is_valid);self.assertTrue(ctx.notices)
            with self.assertRaises(GEOSException): invalid.intersection(box(0,0,1,1))
            with self.assertRaises(GeometryError):g.intersection(ctx.box(0,0,1,1))
            self.assertTrue(ctx.errors)
            empty=ctx.polygon();self.assertTrue(empty.is_empty);self.assertEqual(empty.area,0);self.assertTrue(empty.is_valid)
            self.assertEqual(empty.wkb,Polygon().wkb);self.assertEqual(empty.__geo_interface__,mapping(Polygon()))
            self.assertTrue(all(math.isnan(v) for v in empty.bounds))
            for raw in [b'',b'invalid',Point().wkb[:6]]:
                with self.assertRaises(GeometryError):ctx.from_wkb(raw)
            for data in [{}, {'type':'Polygon','coordinates':[[[0,0],[1,1]]]}, {'type':'Point','coordinates':[1,2,3]}]:
                with self.assertRaises(GeometryError):ctx.from_json(data)
            with self.assertRaises(GeometryError):ctx.point(math.inf,0)
            with self.assertRaises(GeometryError):ctx.polygon([(0,0),(1,1)])
            self.assertTrue(ctx.point(0,0).is_valid)
            self.assertLessEqual(len(ctx.notices),16)

    def test_ownership_release_cross_context_and_closed_handles(self):
        one,two=NativeGeos(),NativeGeos()
        try:
            seed=one.point(1,2);other=two.point(1,2)
            with self.assertRaises(GeometryError):seed.covers(other)
            seed.close();seed.close()
            with self.assertRaises(GeometryError):_ = seed.area
            for _ in range(1000):
                with one.arena():
                    g=one.from_wkb(Point(1,2).wkb);one.box(0,0,3,3).covers(g)
            self.assertEqual(one.owned,{})
            with self.assertRaisesRegex(RuntimeError,'injected'):
                with one.arena():
                    stale=one.point(1,2);raise RuntimeError('injected')
            with self.assertRaises(GeometryError):_ = stale.x
            replacement=one.point(3,4)
            with self.assertRaises(GeometryError):_ = stale.x
            one.close();one.close()
            with self.assertRaises(GeometryError):_ = replacement.x
            with self.assertRaises(GeometryError):one.point(0,0)
            other.close();self.assertEqual(two.owned,{})
        finally:one.close();two.close()
        print(json.dumps({'creationReleaseCycles':1000}))

    def test_protected_xyz_and_borrowed_component_interchange(self):
        source=MultiPolygon([Polygon([(0,0,5),(4,0,6),(4,4,7),(0,4,8),(0,0,5)], [[(1,1,9),(1,2,9),(2,2,9),(1,1,9)]])])
        with NativeGeos() as ctx:
            g=ctx.from_wkb(source.wkb)
            self.assertEqual(g.wkb,source.wkb);self.assertEqual(g.__geo_interface__,mapping(source))
            self.assertTrue(g.covers(ctx.point(.5,.5)))
            self.assertEqual(len(ctx.owned),1)

    def test_context_initialisation_without_shapely_runtime_import(self):
        # The separate resources driver verifies sys.modules; this check records exact engine identity.
        with NativeGeos() as ctx:self.assertEqual(ctx.identity['version'],'3.13.1-CAPI-1.19.2')

@unittest.skipUnless(os.environ.get('ATLAS_WINDOW_PROJECTION'),'Explicit retained projection required.')
class RetainedFeatures(unittest.TestCase):
    def test_all_native_xy_xyz_feature_interchange(self):
        data=json.loads((Path(os.environ['ATLAS_WINDOW_PROJECTION'])/'features.json').read_text(encoding='utf-8'))
        with NativeGeos() as ctx:
            for entry in data['features']:
                source=shape(entry['native']['geometry'])
                with ctx.arena():
                    g=ctx.from_wkb(source.wkb)
                    self.assertEqual(g.wkb,source.wkb);self.assertEqual(g.__geo_interface__,mapping(source))
                    self.assertEqual(g.bounds,source.bounds);self.assertEqual(g.area,source.area)
                    self.assertEqual(g.is_valid,source.is_valid)
            self.assertEqual(ctx.owned,{})
        print(json.dumps({'exactRetainedFeatureInterchanges':len(data['features'])}))

@unittest.skipUnless(os.environ.get('ATLAS_WINDOW_PROJECTION'),'Explicit retained projection required.')
class QueryIntegration(unittest.TestCase):
    def test_novel_complete_envelopes_and_blocked_shapely_pyproj_dispatch(self):
        from adapter import NativeSession
        from window import WindowShared
        from conformance import first_difference
        import reader,shapely,pyproj,random
        from unittest.mock import patch
        from contextlib import ExitStack
        root=Path(os.environ['ATLAS_WINDOW_PROJECTION']);m=json.loads((root/'manifest.json').read_text())
        rng=random.Random(20261011)
        points=[[2624000+rng.random()*2000,1091000+rng.random()*2000] for _ in range(24)]
        points += [[x,y] for x in [2624000,2625000,2626000] for y in [1091000,1092000,1093000]]
        queries=[{'region':'riffelhorn','point':p,'crs':'EPSG:2056'} for p in points]
        forward=pyproj.Transformer.from_crs(2056,4326,always_xy=True)
        for xy in points[::8]:
            for crs in ['EPSG:4326','OGC:CRS84']:queries.append({'region':'riffelhorn','point':list(forward.transform(*xy)),'crs':crs})
        queries += [{'region':'riffelhorn','area':a,'crs':'EPSG:2056'} for a in [[2623000,1090000,2627000,1094000],[2623999,1091001,2624001,1091002],[2624999.75,1091999.75,2625000.25,1092000.25]]]
        queries += [{'region':'riffelhorn','point':[2624500,1091500],'crs':'EPSG:2056','families':['dsm'],'time':{'role':'evidence-epoch','unknown':True}},
                    {'identity':'another-absent-identity'}, {'region':'riffelhorn','area':[2624000,1091000,2625000,1092000],'crs':'EPSG:2056','evidenceClass':'derived','spatialSupport':'consumed'},
                    {'region':'riffelhorn','area':[2623000,1090000,2624000,1091000],'crs':'EPSG:2056'},
                    {'region':'riffelhorn','point':[0,0],'crs':'EPSG:3857'}]
        count=0
        with WindowShared(root,m['projectionIdentity']) as old,NativeSession(root,m['projectionIdentity']) as new:
            for pin in m['pins']:
                with old.pin(pin) as reference,new.pin(pin) as native:
                    for query in queries:
                        expected=reference.outcome(query)
                        with ExitStack() as guards:
                            for name in ['intersection','covers','area','points','polygons','get_exterior_ring','get_interior_ring','get_geometry','get_coordinates','to_wkb','get_type_id','is_empty','is_valid','bounds']:
                                if hasattr(shapely.lib,name):guards.enter_context(patch.object(shapely.lib,name,side_effect=AssertionError('Shapely query dispatch: '+name)))
                            guards.enter_context(patch.object(pyproj.Transformer,'from_crs',side_effect=AssertionError('pyproj query dispatch')))
                            actual=native.outcome(query)
                        difference=first_difference(expected,actual);self.assertIsNone(difference,difference);count+=1
                    self.assertEqual(len(new.geometry.owned),38)
        print(json.dumps({'novelNativeGeometryEnvelopes':count,'queriesPerPin':len(queries)}))

    def test_scoped_failure_restoration_busy_close_and_generation(self):
        from adapter import NativeSession
        import reader
        from window import ReadError
        root=Path(os.environ['ATLAS_WINDOW_PROJECTION']);m=json.loads((root/'manifest.json').read_text())
        before={k:getattr(reader,k) for k in ['Point','Polygon','box','mapping','projected','shapely']}
        with NativeSession(root,m['projectionIdentity']) as session:
            with self.assertRaisesRegex(RuntimeError,'injected'):
                with session.query_scope(),session.geometry.arena():session.geometry.point(0,0);raise RuntimeError('injected')
            for k,v in before.items():self.assertIs(getattr(reader,k),v)
            self.assertEqual(len(session.geometry.owned),38)
            with self.assertRaises(ReadError):session.pin('0'*64)
            view=session.pin(next(iter(m['pins'])))
            with self.assertRaises(ReadError):session.close()
            self.assertEqual(view.read({'identity':'glaciers:683'})['generation'],view.generation)
            view.close()
        for k,v in before.items():self.assertIs(getattr(reader,k),v)
        with self.assertRaises(ReadError):session.__enter__()

if __name__=='__main__':unittest.main()
