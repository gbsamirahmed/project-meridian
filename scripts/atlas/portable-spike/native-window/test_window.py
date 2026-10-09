"""Whole-domain differential checks, independent grid anchors and owned faults."""
from pathlib import Path
import copy
import errno
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
import pyproj
from rasterio.windows import Window
from window import WindowShared,WindowSnapshot,WindowStore,manifest_at,BASE,SOURCE,SOURCE_NAME,identity,ReadError
from shared import SharedProjection
from store import Store
from closure import derive,WINDOW

ORIGINAL=Path(os.environ['ATLAS_SPIKE_PROJECTION']);REDUCED=Path(os.environ['ATLAS_WINDOW_PROJECTION'])
M=json.loads((REDUCED/'manifest.json').read_text(encoding='utf-8'));ID=M['projectionIdentity']
PINS={v['alias']:k for k,v in M['pins'].items()}

def reseal(path,m):
    m.pop('projectionIdentity',None);m['projectionIdentity']=identity(m)
    (path/'manifest.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return m['projectionIdentity']

class WindowBehaviour(unittest.TestCase):
    def test_analytic_enclosure_and_original_absolute_grid(self):
        proof=derive();self.assertEqual(proof['sourceWindow'],WINDOW)
        n=M['window']['sourceNative'];a=n['transform']
        west=a[2]+WINDOW[0]*a[0];east=west+WINDOW[2]*a[0]
        self.assertLess(west,7.71);self.assertGreater(east,7.81)
        self.assertEqual(WINDOW[1:], [0,366,3600])
        self.assertEqual(n['shape'],[3600,3600]);self.assertEqual(M['sourceProjection']['projectionIdentity'],BASE)
        self.assertNotEqual(M['window']['storedMember'],SOURCE_NAME)

    def test_every_stored_pixel_matches_original_bits_and_other_members_identical(self):
        with SharedProjection(ORIGINAL,BASE) as source,WindowShared(REDUCED,ID) as owner:
            with source._snapshot.rasters[SOURCE_NAME].open(driver='GTiff') as src:
                expected=src.read(1,window=Window(*WINDOW)).tobytes()
            with owner._snapshot.rasters[SOURCE_NAME].open() as src:
                self.assertEqual(src.read(1,window=Window(*WINDOW)).tobytes(),expected)
                with self.assertRaises(ReadError):src.read(1,window=Window(WINDOW[0]-1,50,1,1))
            self.assertEqual(hashlib.sha256(expected).hexdigest(),M['window']['pixelSha256'])
        for name in M['sourceProjection']['files']:
            if name!=SOURCE_NAME:self.assertEqual((ORIGINAL/name).read_bytes(),(REDUCED/name).read_bytes())

    def test_novel_points_boundaries_crs_areas_and_combined_predicates(self):
        rng=random.Random(20261009)
        points=[[2624000+rng.random()*2000,1091000+rng.random()*2000] for _ in range(80)]
        points += [[x,y] for x in [2624000,2624999.999999,2625000,2625000.000001,2626000]
                   for y in [1091000,1091999.999999,1092000,1092000.000001,1093000]]
        queries=[{'region':'riffelhorn','point':p,'crs':'EPSG:2056'} for p in points]
        forward=pyproj.Transformer.from_crs('EPSG:2056','EPSG:4326',always_xy=True)
        for p in points[::13]:
            for crs in ['EPSG:4326','OGC:CRS84']:
                queries.append({'region':'riffelhorn','point':list(forward.transform(*p)),'crs':crs,'families':['dtm','dsm']})
        # Source-cell boundaries and representable neighbours, unrelated to fixture IDs.
        native=M['window']['sourceNative'];a=native['transform']
        for column,row in [(2701,51),(2733,72),(2762,83)]:
            lon=a[2]+column*a[0];lat=a[5]+row*a[4]
            for x in [math.nextafter(lon,-math.inf),lon,math.nextafter(lon,math.inf)]:
                queries.append({'region':'riffelhorn','point':[x,lat],'crs':'EPSG:4326','families':['dsm']})
        queries += [{'region':'riffelhorn','area':a,'crs':'EPSG:2056'} for a in [
            [2624000,1091000,2626000,1093000],[2623000,1090000,2627000,1094000],
            [2623999,1090999,2624000.01,1091000.01],[2625999.99,1092999.99,2626001,1093001],
            [2624999.75,1091999.75,2625000.25,1092000.25]]]
        queries += [{'region':'riffelhorn','area':[7.72,45.96,7.80,46.01],'crs':c} for c in ['EPSG:4326','OGC:CRS84']]
        queries += [
            {'identity':'dsm:'+SOURCE,'evidenceClass':'source','families':['dsm'],'time':{'role':'product-reference','start':2021,'end':2021}},
            {'region':'riffelhorn','families':['dsm'],'time':{'role':'evidence-epoch','unknown':True}},
            {'region':'riffelhorn','knowledge':{'unknown':True}},
            {'identity':'new-absent-identity'}, {'point':[2624500,1091500],'crs':'EPSG:2056','region':'riffelhorn','families':['dsm'],'time':{'role':'evidence-epoch','unknown':True}}]
        compared=0
        with SharedProjection(ORIGINAL,BASE) as reference,WindowShared(REDUCED,ID) as experiment:
            for pin in PINS.values():
                with reference.pin(pin) as old,experiment.pin(pin) as new:
                    for q in queries:self.assertEqual(new.outcome(q),old.outcome(q));compared+=1
                    if old.edges:
                        seed=old.records[next(e['from'] for e in old.edges if e['kind']=='consumes-qualified-source')]['identity']
                        for direction in ['inputs','dependents']:
                            q={'relatedTo':{'identity':seed,'direction':direction,'depth':'transitive'}}
                            self.assertEqual(new.outcome(q),old.outcome(q));compared+=1
        print(json.dumps({'novelCompleteEnvelopeComparisons':compared,'spatialQueries':len(queries)}))

    def test_independent_point_value_and_area_absolute_indices(self):
        n=M['window']['sourceNative'];a=n['transform']
        r,c=70,2740
        # Native cell centre is half a cell from each boundary, so round-trip noise
        # cannot justify changing its index. Confirm the full-source value directly.
        x=a[2]+(c+.5)*a[0];y=a[5]+(r+.5)*a[4]
        q={'region':'riffelhorn','point':[x,y],'crs':'EPSG:4326','families':['dsm']}
        with WindowShared(REDUCED,ID) as owner,owner.pin(PINS['after']) as view:
            answer=view.read(q);body=answer['documents'][answer['results'][0]['evidenceRef']]
            self.assertEqual((body['detail']['selection']['row'],body['detail']['selection']['column']),(r,c))
            with SharedProjection(ORIGINAL,BASE) as original,original._snapshot.rasters[SOURCE_NAME].open() as src:
                self.assertEqual(body['detail']['payload']['nativeValue'],float(src.read(1,window=Window(c,r,1,1))[0,0]))
            area=view.read({'region':'riffelhorn','area':[2623000,1090000,2627000,1094000],'crs':'EPSG:2056','families':['dsm']})
            selection=area['documents'][area['results'][0]['evidenceRef']]['detail']['selection']
            self.assertEqual(selection['window'],[2694,43,94,66])
            self.assertEqual(body['detail']['payload']['unit']['status'],'unknown')

    def test_bad_headers_offsets_schema_missing_and_tampered_payload(self):
        with tempfile.TemporaryDirectory(prefix='atlas-window-invalid-') as folder:
            target=Path(folder)/'copy';shutil.copytree(REDUCED,target)
            for change in ['offset','shape','stored','processing','schema']:
                m=copy.deepcopy(M)
                if change=='offset':m['window']['sourceWindow'][0]+=1
                elif change=='shape':m['window']['sourceNative']['shape']=[3600,366]
                elif change=='stored':m['window']['storedNative']['transform'][2]+=1/3600
                elif change=='processing':m['window']['processing']['resampling']='bilinear'
                else:m['schema']='future/v2'
                identifier=reseal(target,m)
                with self.assertRaises(ReadError):WindowSnapshot(target,identifier)
            (target/'manifest.json').write_bytes((REDUCED/'manifest.json').read_bytes())
            member=target/M['window']['storedMember'];raw=member.read_bytes();member.write_bytes(raw[:-1])
            with self.assertRaises(ReadError):WindowSnapshot(target,ID)
            member.unlink()
            with self.assertRaises(ReadError):WindowSnapshot(target,ID)

    def test_post_open_mutation_deletion_and_explicit_pin(self):
        with tempfile.TemporaryDirectory(prefix='atlas-window-mutation-') as folder:
            target=Path(folder)/'copy';shutil.copytree(REDUCED,target)
            with WindowShared(target,ID) as owner:
                views=[owner.pin(pin) for pin in PINS.values()]
                try:
                    q={'region':'riffelhorn','point':[2624567.625,1091876.375],'crs':'EPSG:2056'}
                    wanted=[v.read(q) for v in views]
                    replacement=target/'replacement.tmp';replacement.write_bytes(b'not a raster')
                    os.replace(replacement,target/M['window']['storedMember'])
                    with self.assertRaises(ReadError):WindowShared(target,ID)
                    shutil.rmtree(target)
                    for v,w in zip(views,wanted):self.assertEqual(v.read(q),w)
                    with self.assertRaises(ReadError):owner.pin('0'*64)
                finally:
                    for v in views:v.close()

    def test_old_reader_rejects_new_schema_and_no_scientific_fallback(self):
        with self.assertRaises(ReadError):SharedProjection(REDUCED,ID)
        with WindowShared(REDUCED,ID) as owner:
            with self.assertRaises(ReadError):owner.pin('0'*64)
            with owner.pin(PINS['legacy']) as view:self.assertIsNone(view.read({'identity':'glaciers:683'})['results'][0]['knowledgeRef'])

class WindowLifecycle(unittest.TestCase):
    def test_failed_replacement_last_ready_restart_and_successful_selection(self):
        with tempfile.TemporaryDirectory(prefix='atlas-window-store-') as folder:
            store=WindowStore.create(Path(folder)/'store');store.install(ORIGINAL,BASE)
            for stop in ['staging-write:','before-ready','after-ready']:
                def fail(name):
                    if name.startswith(stop):raise OSError(errno.ENOSPC,'Injected owned write failure')
                with self.assertRaises(ReadError):store.install(REDUCED,ID,fail)
                self.assertEqual(WindowStore(store.root).selected(),BASE)
                with WindowShared.from_store(WindowStore(store.root),BASE) as old,old.pin(PINS['before']) as view:
                    self.assertEqual(view.generation,PINS['before'])
                for stage in list((store.root/'staging').iterdir()):store.discard_stage(stage.name)
            store.install(REDUCED,ID)
            with WindowStore(store.root).open(PINS['after']) as view:self.assertEqual(view.generation,PINS['after'])
            with WindowStore(store.root).open(PINS['before'],BASE) as old:self.assertEqual(old.generation,PINS['before'])
            code="from window import WindowStore; import sys; s=WindowStore(sys.argv[1]);\nwith s.open(sys.argv[2]) as r:print(r.generation)"
            child=subprocess.run([sys.executable,'-B','-c',code,str(store.root),PINS['legacy']],cwd=Path(__file__).parent,text=True,capture_output=True)
            self.assertEqual(child.returncode,0,child.stderr);self.assertEqual(child.stdout.strip(),PINS['legacy'])
            store.delete(ID)
            with self.assertRaises(ReadError):store.open(PINS['after'])
            with store.open(PINS['after'],BASE) as old:self.assertEqual(old.generation,PINS['after'])

if __name__=='__main__':unittest.main()
