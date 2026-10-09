"""Novel whole-profile comparisons and owned-copy lifecycle checks, not fixture lookup."""
from pathlib import Path
import copy
import errno
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
from shared import SharedProjection
from reader import Reader, ReadError, projected
from store import Store
from verification import Snapshot
from shapely.geometry import Point

ROOT = Path(os.environ['ATLAS_SPIKE_PROJECTION'])
M = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
ID = M['projectionIdentity']; PINS = {v['alias']:k for k,v in M['pins'].items()}

class SharedBehaviour(unittest.TestCase):
    def test_single_verification_three_exact_views_and_safe_close(self):
        with patch('shared.Snapshot', wraps=Snapshot) as capture:
            owner = SharedProjection(ROOT, ID)
            views = [owner.pin(PINS[k]) for k in ['before','after','legacy']]
            self.assertEqual(capture.call_count, 1)
            self.assertTrue(all(v.snapshot is views[0].snapshot for v in views))
            self.assertEqual(len(views[0].snapshot.rasters), 6)
            with self.assertRaises(ReadError) as error: owner.close()
            self.assertEqual(error.exception.code, 'projection-busy')
            views[0].close(); views[0].close()
            self.assertEqual(views[0].outcome({})['code'], 'projection-closed')
            self.assertEqual(views[1].read({})['generation'], PINS['after'])
            for v in views[1:]: v.close()
            owner.close(); owner.close()
            with self.assertRaises(ReadError): owner.pin(PINS['after'])

    def test_invalid_pin_does_not_acquire_a_lease_or_switch_generation(self):
        with SharedProjection(ROOT, ID) as owner:
            for pin in [None, [], '0'*64]:
                with self.assertRaises(ReadError): owner.pin(pin)
            with owner.pin(PINS['legacy']) as view:
                self.assertIsNone(view.read({'identity':'glaciers:683'})['results'][0]['knowledgeRef'])
        with self.assertRaises(ReadError): SharedProjection(ROOT, '0'*64)

    def test_novel_profile_queries_match_complete_baseline_envelopes(self):
        # Coordinates generated from the entire declared core, not frozen requests.
        points = [[x,y] for x in [2624000,2624333.375,2624999.875,2625000,2625000.125,2625666.625,2626000]
                  for y in [1091000,1091456.125,1092000,1092456.875,1093000]]
        queries = [{'region':'riffelhorn','point':p,'crs':'EPSG:2056'} for p in points]
        for p in points[::7]:
            lonlat = projected(Point(p), 'EPSG:2056', 'EPSG:4326')
            queries.append({'region':'riffelhorn','point':[lonlat.x,lonlat.y],'crs':'OGC:CRS84'})
        for area in [[2624000,1091000,2626000,1093000], [2624999.875,1091999.875,2625000.125,1092000.125],
                     [2623999,1090999,2624000.125,1091000.125], [2625999.875,1092999.875,2626001,1093001]]:
            queries.append({'region':'riffelhorn','area':area,'crs':'EPSG:2056'})
        queries += [
            {'identity':'glaciers:683','region':'riffelhorn','families':['glaciers'],'time':{'role':'evidence-epoch','start':2014,'end':2016}},
            {'region':'riffelhorn','families':['dtm','dsm'],'time':{'role':'evidence-epoch','unknown':True}},
            {'region':'riffelhorn','knowledge':{'unknown':True}},
            {'region':'riffelhorn','identity':'novel-absent-source'},
            {'region':'riffelhorn','point':[2624333.375,1091456.125],'crs':'EPSG:2056','families':['dtm'],'evidenceClass':'source','time':{'role':'product-reference','start':2024,'end':2024}},
        ]
        comparisons = 0
        with SharedProjection(ROOT, ID) as owner:
            for pin in PINS.values():
                with owner.pin(pin) as view, Reader(ROOT,pin,ID) as reference:
                    for query in queries:
                        with self.subTest(pin=pin, query=query):
                            self.assertEqual(view.outcome(query), reference.outcome(query)); comparisons += 1
                    dtm = next(r['identity'] for r in view.records.values() if r['family']=='dtm')
                    for direction in ['inputs','dependents']:
                        for depth in ['direct','transitive']:
                            query={'relatedTo':{'identity':dtm,'direction':direction,'depth':depth}}
                            self.assertEqual(view.outcome(query),reference.outcome(query)); comparisons += 1
        print(json.dumps({'novelCompleteEnvelopeComparisons':comparisons}))

    def test_independently_justified_native_windows_seams_and_unknowns(self):
        with SharedProjection(ROOT, ID) as owner, owner.pin(PINS['after']) as view:
            q={'region':'riffelhorn','area':M['core'],'crs':'EPSG:2056','families':['dtm']}
            answer=view.read(q); self.assertEqual(len(answer['results']),4)
            for record in answer['results']:
                selection=answer['documents'][record['evidenceRef']]['detail']['selection']
                self.assertEqual(selection['window'], [0,0,2000,2000])
            q={'region':'riffelhorn','point':[2625000.125,1091567.125],'crs':'EPSG:2056','families':['dtm']}
            answer=view.read(q); doc=answer['documents'][answer['results'][0]['evidenceRef']]
            self.assertEqual((doc['detail']['selection']['row'],doc['detail']['selection']['column']), (865,0))
            self.assertEqual(doc['detail']['payload']['unit']['status'], 'unknown')
            answer=view.read({'region':'riffelhorn','point':[2626000,1091567.125],'crs':'EPSG:2056','families':['dtm']})
            self.assertEqual(answer['results'],[]); self.assertFalse(answer['gap']['physicalAbsenceInferred'])
            wrong=view.read({'identity':'glaciers:683','time':{'role':'product-reference','start':2015,'end':2015}})
            self.assertEqual(wrong['results'],[])

    def test_unsupported_requests_and_result_mutation_are_explicit(self):
        with SharedProjection(ROOT, ID) as owner, owner.pin(PINS['after']) as view:
            for q in [{'sql':'select all'}, {'time':{'role':'observation-time','unknown':True}},
                      {'region':'riffelhorn','point':[float('nan'),0],'crs':'EPSG:2056'}]:
                self.assertEqual(view.outcome(q)['code'],'query-invalid')
            q={'identity':'glaciers:683'}; wanted=view.read(q); altered=view.read(q)
            altered['members'].clear(); altered['documents'].clear()
            self.assertEqual(view.read(q),wanted)
            self.assertEqual(view.outcome({'relatedTo':{'identity':'novel-absent','direction':'inputs','depth':'direct'}})['code'],'relationship-missing')

    def test_post_open_replacement_and_deletion_preserve_all_pins(self):
        with tempfile.TemporaryDirectory(prefix='atlas-sharing-mutation-') as folder:
            target=Path(folder)/'copy'; shutil.copytree(ROOT,target)
            with SharedProjection(target, ID) as owner:
                views=[owner.pin(pin) for pin in PINS.values()]
                try:
                    q={'region':'riffelhorn','point':[2624333.375,1091456.125],'crs':'EPSG:2056'}
                    wanted=[v.read(q) for v in views]
                    member=target/next(iter(M['rasterFiles'].values()))
                    replacement=target/'replacement.tmp'; replacement.write_bytes(b'not a TIFF'); os.replace(replacement,member)
                    (target/'features.json').write_bytes(b'{}')
                    with self.assertRaises(ReadError): SharedProjection(target,ID)
                    shutil.rmtree(target)
                    for view,answer in zip(views,wanted): self.assertEqual(view.read(q),answer)
                finally:
                    for view in views: view.close()

    def test_missing_corrupt_incompatible_packages_rejected(self):
        with tempfile.TemporaryDirectory(prefix='atlas-sharing-invalid-') as folder:
            target=Path(folder)/'copy'; shutil.copytree(ROOT,target)
            (target/'manifest.json').write_bytes(b'{')
            with self.assertRaises(ReadError): SharedProjection(target,ID)
            (target/'manifest.json').write_text(json.dumps({**M,'schema':'future/v9'}),encoding='utf-8')
            with self.assertRaises(ReadError) as error: SharedProjection(target,ID)
            self.assertEqual(error.exception.code,'projection-incompatible')
            (target/'manifest.json').write_bytes((ROOT/'manifest.json').read_bytes())
            (target/'worldcover.json').unlink()
            with self.assertRaises(ReadError): SharedProjection(target,ID)

class SharedStore(unittest.TestCase):
    def test_ready_restart_failed_replacement_and_explicit_deletion(self):
        with tempfile.TemporaryDirectory(prefix='atlas-sharing-store-') as folder:
            store=Store.create(Path(folder)/'store'); store.install(ROOT,ID)
            with SharedProjection.from_store(store,ID) as owner:
                with owner.pin(PINS['before']) as before, owner.pin(PINS['after']) as after:
                    q={'identity':'glaciers:683'}; old=before.read(q); current=after.read(q)
                    self.assertNotEqual(old['results'][0]['knowledgeRef'],current['results'][0]['knowledgeRef'])
                    def fail(name):
                        if name.startswith('staging-write:'): raise OSError(errno.ENOSPC,'Injected write failure')
                    with self.assertRaises(ReadError): store.install(ROOT,ID,fail)
                    self.assertEqual(Store(store.root).selected(),ID)
                    with SharedProjection.from_store(Store(store.root)) as restarted, restarted.pin(PINS['before']) as view:
                        self.assertEqual(view.read(q),old)
                    store.delete(ID)
                    with self.assertRaises(ReadError): SharedProjection.from_store(Store(store.root))
                    self.assertEqual(before.read(q),old); self.assertEqual(after.read(q),current)

    def test_invalid_selection_receipt_and_member_never_use_old_owner(self):
        with tempfile.TemporaryDirectory(prefix='atlas-sharing-store-invalid-') as folder:
            store=Store.create(Path(folder)/'store'); store.install(ROOT,ID)
            with SharedProjection.from_store(store) as owner, owner.pin(PINS['after']) as view:
                expected=view.read({'identity':'glaciers:683'})
                (store.root/'selection.json').write_bytes(b'{')
                with self.assertRaises(ReadError): SharedProjection.from_store(store)
                with SharedProjection.from_store(store,ID) as explicit, explicit.pin(PINS['legacy']) as old:
                    self.assertEqual(old.generation,PINS['legacy'])
                (store.package(ID)/'worldcover.json').unlink()
                with self.assertRaises(ReadError): SharedProjection.from_store(store,ID)
                self.assertEqual(view.read({'identity':'glaciers:683'}),expected)

if __name__ == '__main__': unittest.main()
