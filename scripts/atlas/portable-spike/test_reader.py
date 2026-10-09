"""Novel behaviour and failure checks; no frozen requests or expected answers read."""
from pathlib import Path
import copy
import hashlib
import json
import os
import tempfile
import unittest
from reader import Reader, ReadError, identity

ROOT=Path(os.environ['ATLAS_SPIKE_PROJECTION'])
MANIFEST=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
PINS={v['alias']:k for k,v in MANIFEST['pins'].items()}

class Behaviour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader=Reader(ROOT,PINS['after'],MANIFEST['projectionIdentity'])

    def test_novel_affine_point_and_conjunction(self):
        q={'region':'riffelhorn','point':[2624123.875,1091567.125],'crs':'EPSG:2056','families':['dtm'],'evidenceClass':'source','time':{'role':'product-reference','start':2024,'end':2024}}
        a=self.reader.read(q); self.assertEqual(len(a['results']),1)
        doc=a['documents'][a['results'][0]['evidenceRef']]
        # Exact 0.5 m affine: SW tile origin (2624000,1092000), floor, not nearest.
        self.assertEqual(doc['detail']['selection']['column'],247)
        self.assertEqual(doc['detail']['selection']['row'],865)
        self.assertEqual(a['generation'],PINS['after'])
        q['time']={'role':'evidence-epoch','start':2024,'end':2024}
        self.assertEqual(self.reader.read(q)['results'],[])

    def test_novel_east_seam_offsets(self):
        base={'region':'riffelhorn','families':['dtm'],'crs':'EPSG:2056'}
        west=self.reader.read({**base,'point':[2624999.875,1091456.125]}); east=self.reader.read({**base,'point':[2625000.125,1091456.125]})
        self.assertEqual(len(west['results']),1); self.assertEqual(len(east['results']),1)
        self.assertNotEqual(west['results'][0]['identity'],east['results'][0]['identity'])
        for answer,col in [(west,1999),(east,0)]:
            self.assertEqual(answer['documents'][answer['results'][0]['evidenceRef']]['detail']['selection']['column'],col)

    def test_novel_vector_temporal_identity_conjunction(self):
        q={'identity':'glaciers:683','region':'riffelhorn','families':['glaciers'],'representation':'vector','time':{'role':'evidence-epoch','start':2014,'end':2016}}
        self.assertEqual([r['identity'] for r in self.reader.read(q)['results']],['glaciers:683'])
        q['time']['role']='product-reference'
        self.assertEqual(self.reader.read(q)['results'],[])

    def test_slope_inputs_and_transitive_source_dependents(self):
        slope=next(r for r in self.reader.records.values() if r['family']=='terrain-slope')
        result=self.reader.read({'relatedTo':{'identity':slope['identity'],'direction':'inputs','depth':'direct'}})
        self.assertEqual(len(result['results']),1); self.assertEqual(result['results'][0]['family'],'dtm')
        source=result['results'][0]['identity']
        direct=self.reader.read({'relatedTo':{'identity':source,'direction':'dependents','depth':'direct'}})
        transitive=self.reader.read({'relatedTo':{'identity':source,'direction':'dependents','depth':'transitive'}})
        self.assertTrue(all(r['family']=='terrain-slope' for r in direct['results']))
        self.assertEqual(len(transitive['results']),2*len(direct['results']))
        self.assertEqual({r['family'] for r in transitive['results']},{'terrain-slope','planar-area-ratio'})

    def test_pins_are_explicit_and_historical(self):
        before=Reader(ROOT,PINS['before']); legacy=Reader(ROOT,PINS['legacy'])
        self.assertNotEqual(before.base['members'],self.reader.base['members'])
        self.assertEqual(legacy.read({'identity':'glaciers:683'})['results'][0]['knowledgeRef'],None)
        self.assertRaises(ReadError,Reader,ROOT,'0'*64)
        self.assertRaises(ReadError,Reader,ROOT,PINS['after'],'0'*64)

    def test_malformed_unknown_and_unsupported(self):
        for q in [{'point':[True,1],'region':'riffelhorn','crs':'EPSG:2056'}, {'area':[2,2,1,1],'region':'riffelhorn','crs':'EPSG:2056'}, {'terrainFusion':True}, {'knowledge':{'unknown':False}}]:
            self.assertEqual(self.reader.outcome(q)['code'],'query-invalid')
        a=self.reader.read({'identity':'a-novel-missing-evidence'})
        self.assertFalse(a['gap']['physicalAbsenceInferred'])
        self.assertEqual(self.reader.outcome({'relatedTo':{'identity':'a-novel-missing-evidence','direction':'inputs','depth':'transitive'}})['code'],'relationship-missing')
        self.assertEqual(self.reader.outcome({'region':'tryfan','point':[2624123.875,1091567.125],'crs':'EPSG:2056'})['code'],'profile-unsupported')

    def test_returned_answer_cannot_change_pinned_state(self):
        first=self.reader.read({'identity':'glaciers:683'})
        expected=copy.deepcopy(first)
        first['members'].clear()
        first['results'][0]['identity']='invented'
        first['documents'][first['results'][0]['evidenceRef']].clear()
        self.assertEqual(self.reader.read({'identity':'glaciers:683'}),expected)

    def test_canonical_numeric_keys_and_unicode(self):
        self.assertEqual(identity({'20':1,'100':2}),hashlib.sha256(b'{\n  "20": 1,\n  "100": 2\n}\n').hexdigest())
        self.assertEqual(identity({'text':'é — unknown'}),hashlib.sha256('{\n  "text": "é — unknown"\n}\n'.encode()).hexdigest())

    def altered(self,change,code):
        # Owned temporary directory: copy small metadata; hard-link immutable raster bytes.
        with tempfile.TemporaryDirectory(prefix='atlas-projection-test-') as folder:
            target=Path(folder)
            for p in ROOT.iterdir():
                if p.suffix=='.tif': os.link(p,target/p.name)
                else: (target/p.name).write_bytes(p.read_bytes())
            change(target)
            with self.assertRaises(ReadError) as caught: Reader(target,PINS['after'])
            self.assertEqual(caught.exception.code,code)

    def test_corrupt_member(self):
        self.altered(lambda d:(d/'features.json').write_bytes(b'{}'),'projection-integrity')

    def test_missing_member(self):
        self.altered(lambda d:(d/'worldcover.json').unlink(),'projection-unavailable')

    def mutate_manifest(self,d,field,value,reseal=False):
        m=copy.deepcopy(MANIFEST); m[field]=value
        if reseal: m['projectionIdentity']=identity({k:v for k,v in m.items() if k!='projectionIdentity'})
        (d/'manifest.json').write_text(json.dumps(m,ensure_ascii=False),encoding='utf-8')

    def test_incompatible_schema(self):
        self.altered(lambda d:self.mutate_manifest(d,'schema','future/v9'),'projection-incompatible')

    def test_manifest_tampering(self):
        self.altered(lambda d:self.mutate_manifest(d,'core',[0,0,1,1]),'projection-integrity')

    def test_resealed_missing_required_closure(self):
        files={k:v for k,v in MANIFEST['files'].items() if k!='features.json'}
        self.altered(lambda d:self.mutate_manifest(d,'files',files,True),'projection-integrity')

    def test_missing_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ReadError) as caught: Reader(Path(folder)/'missing',PINS['after'])
            self.assertEqual(caught.exception.code,'projection-unavailable')

if __name__=='__main__': unittest.main()
