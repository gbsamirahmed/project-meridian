"""Real-source oracle, boundary, qualification and isolated failure tests."""
from pathlib import Path
import copy,json,shutil,subprocess,sys,tempfile,unittest
import query as Q
class RetrievalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.s=Q.Session();cls.matrix=Q.P.load(Q.H/'matrix.json');cls.tmp=Path(tempfile.mkdtemp(prefix='riffelhorn-retrieval-'))
 def answer(self,q,mode='selective'):return self.s.query(q,mode)['answer']
 def test_all_matrix_full_envelope_equivalence(self):
  for c in self.matrix['cases']:
   expected=self.answer(c['query'],'scan')
   for mode in ['grouped','selective']:self.assertEqual(expected,self.answer(c['query'],mode),c['id']+mode)
 def test_brute_native_feature_geometries(self):
  for f in self.s.features:
   point=Q.shape(f['native']['geometry']).intersection(Q.CORE).representative_point();q={'point':[point.x,point.y],'representation':'vector'}
   expected=sorted(a['identity'] for a in self.s.features if Q.shape(a['native']['geometry']).covers(point));self.assertEqual(expected,[a['identity'] for a in self.answer(q)['results']])
 def test_point_samples_direct_gdal(self):
  results=self.answer({'point':[2624500,1091500],'representation':'raster'})['results']
  for a in results:
   binding=a['detail']['binding'];point=Q.project(Q.Point(2624500,1091500),'EPSG:2056',binding['native']['crs'])
   with Q.rasterio.open(self.s.data/binding['input']['path']) as src:
    row,col=src.index(point.x,point.y);v=src.read(1,window=Q.Window(col,row,1,1))[0,0]
   payload=a['detail']['payload'];self.assertEqual(row,payload['selection']['row']);self.assertEqual(col,payload['selection']['column']);self.assertEqual(float(v),payload.get('nativeValue',payload.get('nativeCode')))
 def test_core_edge_and_seam(self):
  self.assertEqual(len(self.answer({'point':[2625000,1092000],'families':['dtm']})['results']),1)
  self.assertEqual(self.answer({'point':[2626000,1092000],'families':['dtm']})['results'],[])
  self.assertEqual(self.answer({'point':[2624500,1091000],'families':['dtm']})['results'],[])
 def test_vector_boundary_included(self):
  c=next(c for c in self.matrix['cases'] if c['id']=='feature-boundary');ids=[r['identity'] for r in self.answer(c['query'])['results']];self.assertIn(self.s.features[0]['identity'],ids)
 def test_area_positive_intersection(self):
  q={'area':[2624975,1091975,2625025,1092025],'representation':'vector'};geom=Q.box(*q['area']);expected=sorted(f['identity'] for f in self.s.features if Q.shape(f['native']['geometry']).intersection(geom).area>0)
  self.assertEqual(expected,[r['identity'] for r in self.answer(q)['results']])
 def test_spatial_false_positives_filtered(self):
  q=next(c['query'] for c in self.matrix['cases'] if c['id']=='point-all');out=self.s.query(q);self.assertGreater(out['metrics']['spatialFalsePositiveCandidates'],0);self.assertEqual(self.answer(q,'scan'),out['answer'])
 def test_source_scoped_exact_feature(self):
  q={'feature':'geocover-bedrock:179373'};out=self.s.query(q);self.assertEqual(out['metrics']['recordsConsidered'],1);self.assertEqual(out['answer']['results'][0]['detail']['nativeIdentity'],179373)
 def test_missing_feature_is_not_physical_absence(self):self.assertEqual(self.answer({'feature':'glaciers:absent'})['gap']['reason'],'no-matching-retained-evidence')
 def test_raster_support_is_not_feature(self):self.assertFalse(self.answer({'feature':self.s.rasters[0]['id']})['results'])
 def test_real_parent_associations(self):
  result=self.answer({'feature':'glaciers:683','associated':True})['results'];self.assertEqual(len(result),7);self.assertEqual(sum(bool(r['detail']['associations']) for r in result),6)
 def test_time_known_native_epochs(self):
  for year,n in [(2015,1),(2016,6),(2021,1),(2026,0)]:self.assertEqual(len(self.answer({'time':{'role':'evidence-epoch','start':year,'end':year}})['results']),n)
 def test_unknown_time_is_not_universal(self):
  rs=self.answer({'time':{'role':'evidence-epoch','unknown':True}})['results'];self.assertEqual(len(rs),36);self.assertTrue(all(r['temporal']['evidence-epoch']['status']=='unknown' for r in rs))
 def test_release_distinct_from_observation(self):
  rs=self.answer({'time':{'role':'product-reference','start':2020,'end':2020}})['results'];self.assertEqual(len(rs),7);self.assertTrue(all(r['temporal']['evidence-epoch']['year'] in [2015,2016] for r in rs))
 def test_geo_ages_not_observation_dates(self):self.assertFalse(self.answer({'families':['geocover-bedrock'],'time':{'role':'evidence-epoch','start':2015,'end':2016}})['results'])
 def test_height_qualifications_and_unit_unknown(self):
  rs=self.answer({'point':[2624500,1091500],'families':['dtm','dsm']})['results'];self.assertEqual(len(rs),2);self.assertTrue(any('LN02' in r['qualification']['vertical'] for r in rs));self.assertTrue(any('EGM2008' in r['qualification']['vertical'] for r in rs));self.assertTrue(all(r['detail']['payload']['unit']['status']=='unknown' for r in rs))
 def test_native_worldcover_counts(self):
  r=self.answer({'area':Q.P.CORE,'families':['worldcover']})['results'][0];p=r['detail']['payload'];self.assertEqual(sum(p['counts'].values()),p['selectedCellCentres']);self.assertLess(p['selectedCellCentres'],218*312);self.assertTrue(r['detail']['definitions']);self.assertTrue(r['detail']['mappingQualifications'])
 def test_full_qualification_provenance_preserved(self):
  r=self.answer({'feature':'geocover-bedrock:179373'})['results'][0];f=next(f for f in self.s.features if f['identity']==r['identity']);self.assertEqual(r['detail']['nativeFields'],f['native']['properties']);self.assertTrue(all(x['rights']['references'] and x['rights']['attribution'] for x in r['detail']['resources']));self.assertEqual(r['detail']['nativeClaim'],next(c for c in self.s.collections[f['family']]['claims'] if c['id']==f['identity']))
 def test_outside_support_explicit(self):self.assertEqual(self.answer({'point':[0,0]})['gap']['reason'],'outside-support')
 def test_invalid_spatial_support(self):
  for q in [{'area':[2,3,1,4]},{'point':[float('nan'),1]},{'point':[1]}]:
   with self.assertRaises(ValueError):self.answer(q)
 def test_unsupported_crs(self):
  with self.assertRaisesRegex(ValueError,'CRS'):self.answer({'point':[1,2],'crs':'EPSG:9999'})
 def test_unsupported_temporal_precision(self):
  with self.assertRaisesRegex(ValueError,'calendar-year'):self.answer({'time':{'role':'evidence-epoch','start':'2016-01-01','end':'2016-12-31'}})
 def test_malformed_query(self):
  for q in [[],{'invented':'field'},{'associated':True},{'families':['invented']}]:
   with self.assertRaises(ValueError):self.answer(q)
 def test_duplicate_conflicting_identity(self):
  fs=copy.deepcopy(self.s.features);fs.append(fs[0])
  with self.assertRaisesRegex(ValueError,'duplicate'):Q.validate_records(fs,self.s.rasters,self.s.bundle)
 def test_missing_provenance(self):
  b=copy.deepcopy(self.s.bundle);b['collections'][1]['claims'][0]['record']={}
  with self.assertRaisesRegex(ValueError,'provenance'):Q.validate_records(self.s.features,self.s.rasters,b)
 def test_unknown_native_crs(self):
  fs=copy.deepcopy(self.s.features);fs[0]['nativeCrs']='unknown'
  with self.assertRaisesRegex(ValueError,'CRS'):Q.validate_records(fs,self.s.rasters,self.s.bundle)
 def test_prepared_missing_corrupt_malformed(self):
  for kind in ['missing','corrupt','malformed']:
   root=self.tmp/kind;root.mkdir();shutil.copy(self.s.root/'manifest.json',root/'manifest.json')
   if kind=='corrupt':(root/'input-manifest.json').write_bytes(b'corrupt')
   if kind=='malformed':(root/'manifest.json').write_bytes(b'[]')
   with self.assertRaises(ValueError):Q.Session(root=root)
 def test_missing_native_payload_explicit(self):
  old=self.s.data;self.s.data=self.tmp/'unavailable'
  try:
   with self.assertRaisesRegex(ValueError,'unavailable'):self.answer({'point':[2624500,1091500],'families':['worldcover']})
  finally:self.s.data=old
 def test_isolated_nodata_contract(self):
  from unittest.mock import patch
  binding=next(r for r in self.s.rasters if r['family']=='worldcover')
  class Source:
   crs=binding['native']['crs'];shape=binding['native']['shape'];transform=Q.rasterio.Affine(*binding['native']['transform'][:6]);nodata=0
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,*args,**kwargs):return Q.np.zeros((1,1),dtype='uint8')
  with patch.object(Q.rasterio,'open',return_value=Source()):
   p=self.answer({'point':[2624500,1091500],'families':['worldcover']})['results'][0]['detail']['payload'];self.assertEqual(p['kind'],'gap');self.assertEqual(p['reason'],'no-observation');self.assertFalse(p['physicalAbsenceInferred'])
 def test_conflicting_temporal_predicates(self):
  with self.assertRaisesRegex(ValueError,'unknown time'):self.answer({'time':{'role':'evidence-epoch','unknown':True,'start':2015}})
 def test_fresh_process_same_hashes(self):
  q=subprocess.run([sys.executable,str(Q.H/'query.py'),'--matrix'],cwd=Q.R,capture_output=True,text=True,encoding='utf-8');self.assertEqual(q.returncode,0,q.stderr);x=json.loads(q.stdout);self.assertEqual(x['answers'],{c['id']:Q.P.digest(Q.P.canonical(self.answer(c['query']))) for c in self.matrix['cases']})
if __name__=='__main__':unittest.main()
