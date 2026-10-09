"""Non-fixture CRS, geometry and complete-envelope checks; no scientific repair."""
from pathlib import Path
import json
import math
import os
import random
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'native-window'))
from window import WindowShared
from native_proj import NativeProj, BindingError, comparison_binding, PIPELINE
from conformance import first_difference
import pyproj
import reader
from shapely import GEOSException
from shapely.geometry import Point, Polygon, MultiPolygon, box


class Operations(unittest.TestCase):
    def test_bidirectional_arrays_axes_and_checked_operation(self):
        rng = random.Random(20261010)
        xs = [2624000, 2626000, 2625000]+[2624000+rng.random()*2000 for _ in range(128)]
        ys = [1091000, 1093000, 1092000]+[1091000+rng.random()*2000 for _ in range(128)]
        with NativeProj() as binding:
            geographic = binding.xy(xs, ys, 'EPSG:2056', 'EPSG:4326')
            ref = pyproj.Transformer.from_crs(2056,4326,always_xy=True)
            self.assertEqual(geographic, tuple(tuple(a) for a in ref.transform(xs,ys)))
            self.assertEqual(binding.operation('EPSG:2056','EPSG:4326')[1], PIPELINE)
            for source in ['EPSG:4326', 'OGC:CRS84']:
                actual = binding.xy(*geographic, source, 'EPSG:2056')
                reverse = pyproj.Transformer.from_crs(4326,2056,always_xy=True)
                self.assertEqual(actual, tuple(tuple(a) for a in reverse.transform(*geographic)))
                self.assertEqual(binding.operation(source,'EPSG:2056')[1], reverse.definition)
            self.assertEqual(binding.xy(*geographic,'OGC:CRS84','EPSG:4326'), geographic)
            self.assertFalse(binding.lib.proj_context_is_network_enabled(binding.ctx))
        print(json.dumps({'exactCoordinatePairsCompared':len(xs)*4}))

    def test_failure_and_ownership(self):
        binding = NativeProj()
        try:
            for xs,ys,s,t in [([1],[],'EPSG:2056','EPSG:4326'),([math.inf],[0],'EPSG:2056','EPSG:4326'),
                               ([0],[0],'EPSG:3857','EPSG:2056'),([7],[100],'EPSG:4326','EPSG:2056')]:
                with self.assertRaises(BindingError): binding.xy(xs,ys,s,t)
            with self.assertRaises(BindingError): binding.projected(Point(7,46,10),'EPSG:4326','EPSG:2056')
        finally: binding.close()
        binding.close()
        with self.assertRaises(BindingError): binding.xy([0],[0],'EPSG:2056','EPSG:4326')

    def test_callback_restoration(self):
        original = reader.projected
        with NativeProj() as binding:
            with self.assertRaisesRegex(RuntimeError, 'injected'):
                with comparison_binding(binding): raise RuntimeError('injected')
            self.assertIs(reader.projected, original)

    def test_reference_geometry_semantics_adversarial(self):
        # These diagnose the retained GEOS behaviour; no alternative kernel is asserted.
        outer = [(0,0),(4,0),(4,4),(0,4),(0,0)]
        hole = [(1,1),(3,1),(3,3),(1,3),(1,1)]
        g = Polygon(outer,[hole]); multi = MultiPolygon([g,box(6,0,7,1)])
        self.assertTrue(g.covers(Point(0,2)))
        self.assertFalse(g.contains(Point(0,2)))
        self.assertFalse(g.covers(Point(2,2)))
        self.assertTrue(g.covers(Point(1,2)))
        self.assertTrue(multi.covers(Point(6.5,.5)))
        self.assertEqual(g.intersection(box(4,0,5,4)).area,0)
        self.assertGreater(g.intersection(box(math.nextafter(4,-math.inf),0,5,4)).area,0)
        invalid = Polygon([(0,0),(2,2),(0,2),(2,0),(0,0)])
        self.assertFalse(invalid.is_valid)
        with self.assertRaises(GEOSException): invalid.intersection(box(0,0,1,1))
        self.assertTrue(g.intersection(box(5,5,6,6)).is_empty)


@unittest.skipUnless(os.environ.get('ATLAS_WINDOW_PROJECTION'), 'Explicit retained window projection required.')
class CompleteEnvelopes(unittest.TestCase):
    def test_novel_queries_exact_all_pins_and_no_pyproj_query_dispatch(self):
        root=Path(os.environ['ATLAS_WINDOW_PROJECTION']); manifest=json.loads((root/'manifest.json').read_text())
        rng=random.Random(20261010)
        points=[[2624000+rng.random()*2000,1091000+rng.random()*2000] for _ in range(30)]
        points += [[x,y] for x in [2624000,2625000,2626000] for y in [1091000,1092000,1093000]]
        queries=[{'region':'riffelhorn','point':p,'crs':'EPSG:2056'} for p in points]
        forward=pyproj.Transformer.from_crs(2056,4326,always_xy=True)
        for point in points[::7]:
            for crs in ['EPSG:4326','OGC:CRS84']:
                queries.append({'region':'riffelhorn','point':list(forward.transform(*point)),'crs':crs})
        a=manifest['window']['sourceNative']['transform']
        for col,row in [(2701,51),(2733,72),(2762,83)]:
            x,y=a[2]+col*a[0],a[5]+row*a[4]
            for lon in [math.nextafter(x,-math.inf),x,math.nextafter(x,math.inf)]:
                queries.append({'region':'riffelhorn','point':[lon,y],'crs':'EPSG:4326','families':['dsm']})
        for area in [[2623000,1090000,2627000,1094000],[2623999,1090999,2624000.01,1091000.01],
                     [2625999.99,1092999.99,2626001,1093001],[2625000,1091000,2625000.000001,1093000]]:
            queries.append({'region':'riffelhorn','area':area,'crs':'EPSG:2056'})
        for crs in ['EPSG:4326','OGC:CRS84']:
            queries.append({'region':'riffelhorn','area':[7.72,45.96,7.80,46.01],'crs':crs})
        queries += [{'identity':'glaciers:683','evidenceClass':'source','time':{'role':'evidence-epoch','start':2015,'end':2015}},
                    {'families':['dsm'],'time':{'role':'evidence-epoch','unknown':True}},
                    {'knowledge':{'unknown':True}}, {'identity':'novel-absent-id'},
                    {'region':'riffelhorn','point':[1,1],'crs':'EPSG:3857'}, {'sql':'unsupported'}]
        count=0
        with WindowShared(root,manifest['projectionIdentity']) as owner, NativeProj() as binding:
            for pin in manifest['pins']:
                with owner.pin(pin) as view:
                    selected=list(queries)
                    if view.edges:
                        seed=view.records[next(e['from'] for e in view.edges if e['kind']=='consumes-qualified-source')]['identity']
                        selected += [{'relatedTo':{'identity':seed,'direction':d,'depth':'transitive'}} for d in ['inputs','dependents']]
                    for query in selected:
                        expected=view.outcome(query)
                        with comparison_binding(binding), patch('pyproj.Transformer.from_crs', side_effect=AssertionError('Authoritative binding dispatched during query')):
                            actual=view.outcome(query)
                        self.assertIsNone(first_difference(expected,actual),first_difference(expected,actual));count+=1
            # Independently calculated original DSM cell centre, not frozen coordinates.
            q={'region':'riffelhorn','point':[a[2]+2740.5*a[0],a[5]+70.5*a[4]],'crs':'EPSG:4326','families':['dsm']}
            with owner.pin(next(k for k,v in manifest['pins'].items() if v['alias']=='after')) as view, comparison_binding(binding):
                answer=view.read(q);doc=answer['documents'][answer['results'][0]['evidenceRef']]
                self.assertEqual((doc['detail']['selection']['row'],doc['detail']['selection']['column']),(70,2740))
                self.assertEqual(doc['detail']['payload']['unit']['status'],'unknown')
        print(json.dumps({'novelCompleteEnvelopeComparisons':count,'queriesWithoutLineage':len(queries)}))

if __name__ == '__main__': unittest.main()
