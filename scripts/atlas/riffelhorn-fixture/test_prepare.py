"""Preparation boundary tests using exact public inputs and isolated negative state."""
from pathlib import Path
import copy,json,shutil,subprocess,sys,tempfile,time,unittest
import prepare as p
DATA=p.resolve_storage_roots(repository_root=p.R,require_data=True).data
SPEC=p.load(p.SPEC);INV=p.load(p.R/'docs/research/atlas-regional-expansion-inventory.json')
class PreparationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.outputs=p.build(DATA);cls.scratch=Path(tempfile.mkdtemp(prefix='riffelhorn-proof-'))
  cls.a=p.prepare(DATA,cls.scratch/'first');cls.root=Path(cls.a['preparedRoot'])
 def test_exact_frozen_inputs(self):
  self.assertEqual(len(self.outputs['input-manifest.json']['inputs']),12);self.assertEqual(sum(x['bytes'] for x in SPEC['inputs']),120347916)
 def test_dtm_native_support(self):
  rs=self.outputs['raster-bindings.json']['rasters'][:4]
  self.assertEqual([x['native']['shape'] for x in rs],[[2000,2000]]*4);self.assertTrue(all(x['native']['resolution']==[.5,.5] and x['native']['nodata']==-9999 for x in rs))
 def test_independent_dsm(self):
  r=self.outputs['raster-bindings.json']['rasters'][4];self.assertEqual(r['native']['tags']['AREA_OR_POINT'],'Point');self.assertIn('EGM2008',self.outputs['qualification.json']['families']['dsm']['vertical']);self.assertEqual(r['verticalTransformation'],'none')
 def test_native_worldcover_window(self):
  r=self.outputs['raster-bindings.json']['rasters'][5];self.assertEqual(r['window']['window'],[20979,24142,312,218]);self.assertEqual(sum(r['nativeCodeCounts'].values()),218*312);self.assertEqual(r['parentByteIdentity']['status'],'unknown')
 def test_full_native_features_preserved(self):
  fs=self.outputs['features.json']['features'];self.assertEqual(len(fs),38)
  for family,i in [('geocover-bedrock',7),('geocover-unconsolidated',8),('glaciers',10),('debris',11)]:
   src=p.load(DATA/SPEC['inputs'][i]['path']);self.assertEqual([f['native'] for f in fs if f['family']==family],src.get('results',src.get('features')))
 def test_glamos_original_reproduced(self):self.assertEqual(self.outputs['qualification.json']['glamosSelection']['counts'],{'glaciers':1,'debris':6})
 def test_feature_parent_and_time(self):
  bundle=self.outputs['semantic-evidence.json'];debris=next(c for c in bundle['collections'] if c['id'].startswith('debris:'))
  self.assertEqual(debris['context']['time'][0]['extent']['value'],'2016');self.assertTrue(all(c['associations'][0]['id']=='683' for c in debris['claims']))
 def test_rights_and_native_unknowns(self):
  self.assertTrue(all(r['rights']['attribution'] for r in self.outputs['raster-bindings.json']['rasters']));q=self.outputs['qualification.json'];self.assertEqual(len(q['optionalReferences']),2);self.assertIn('unknown',q['families']['geocover']['vertical'])
 def test_core_eligibility_only(self):
  q=self.outputs['qualification.json'];self.assertEqual(len(q['eligibility']['geometry']['coordinates'][0]),129);self.assertEqual(q['coordinateOperation']['verticalOperation'],'none');self.assertFalse(q['integration']['registered'])
 def test_empty_state_byte_reproduction(self):
  b=p.prepare(DATA,self.scratch/'second');self.assertEqual(b['revision'],self.a['revision'])
  for name in [*p.FILES,'manifest.json']:self.assertEqual((self.root/name).read_bytes(),(Path(b['preparedRoot'])/name).read_bytes())
 def test_immutable_retry(self):
  prior={n:p.sha(self.root/n) for n in [*p.FILES,'manifest.json']};a=p.prepare(DATA,self.scratch/'first');self.assertTrue(a['retry']);self.assertEqual(prior,{n:p.sha(self.root/n) for n in prior})
 def test_fresh_process_load(self):
  q=subprocess.run([sys.executable,str(p.H/'prepare.py'),'verify','--output',str(self.root)],cwd=p.R,capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);self.assertEqual(json.loads(q.stdout)['revision'],self.a['revision'])
 def test_missing_input(self):
  with self.assertRaisesRegex(ValueError,'missing required input'):p.build(self.scratch/'empty-data')
 def test_wrong_input_size(self):
  root=self.scratch/'wrong-size';a=SPEC['inputs'][0];f=root/a['path'];f.parent.mkdir(parents=True);f.write_bytes(b'invalid')
  with self.assertRaisesRegex(ValueError,'size mismatch'):p.build(root)
 def test_altered_input_bytes(self):
  root=self.scratch/'wrong-hash';a=SPEC['inputs'][0];f=root/a['path'];f.parent.mkdir(parents=True)
  with f.open('wb') as s:s.truncate(a['bytes'])
  with self.assertRaisesRegex(ValueError,'hash mismatch'):p.build(root)
 def test_unsupported_crs(self):
  h=self.outputs['raster-bindings.json']['rasters'][0]['native'];bad={**h,'crs':'EPSG:4326'}
  with self.assertRaisesRegex(ValueError,'unsupported CRS'):p.check_header(bad,h)
 def test_native_field_mismatch(self):
  b=next(x for x in INV['semanticInputs'] if x['path'].endswith('geocover-bedrock.json'));x=p.load(DATA/b['path']);x['results'][0]['properties']['invented']=1
  with self.assertRaisesRegex(ValueError,'native field'):p.check_features(x,'geocover-bedrock',b)
 def test_native_selection_mismatch(self):
  b=next(x for x in INV['semanticInputs'] if x['path'].endswith('geocover-bedrock.json'));x=p.load(DATA/b['path']);x['results'].pop()
  with self.assertRaisesRegex(ValueError,'selection count'):p.check_features(x,'geocover-bedrock',b)
 def test_glamos_original_mismatch(self):
  subsets={k:[copy.deepcopy(f['native']) for f in self.outputs['features.json']['features'] if f['family']==k] for k in ['glaciers','debris']};subsets['glaciers'][0]['properties']['year_acq']=2016
  with self.assertRaisesRegex(ValueError,'original geometry/field'):p.reproduce_glamos(DATA,SPEC,subsets)
 def test_semantic_reference_mismatch(self):
  x=copy.deepcopy(self.outputs['semantic-evidence.json']);x['collections'][0]['claims'][0]['native']['property']['id']='nonexistent';f=self.scratch/'invalid-semantic.json';f.write_bytes(p.canonical(x))
  with self.assertRaisesRegex(ValueError,'unresolved definition'):p.semantic_check(f)
 def interrupted(self,point):
  root=self.scratch/point
  with self.assertRaisesRegex(RuntimeError,'interruption'):p.prepare(DATA,root,point)
  self.assertEqual(len(list(root.iterdir())),1);stage=next(root.iterdir());self.assertFalse((stage/'manifest.json').exists())
  with self.assertRaisesRegex(ValueError,'incomplete preparation'):p.verify(stage,DATA)
  self.assertTrue(p.verify(self.root,DATA)['status']=='COMPLETE')
 def test_early_interruption(self):self.interrupted('early')
 def test_pre_completion_interruption(self):self.interrupted('pre-completion')
 def test_output_corruption_rejected(self):
  root=self.scratch/'bad-output';shutil.copytree(self.root,root);(root/'features.json').write_bytes(b'corrupt')
  with self.assertRaisesRegex(ValueError,'identity mismatch'):p.verify(root,DATA)
 def test_missing_output_rejected(self):
  root=self.scratch/'missing-output';root.mkdir();shutil.copy(self.root/'manifest.json',root/'manifest.json')
  with self.assertRaisesRegex(ValueError,'missing prepared artifact'):p.verify(root,DATA)
 def test_malformed_manifest(self):
  root=self.scratch/'bad-manifest';root.mkdir();(root/'manifest.json').write_bytes(b'[]')
  with self.assertRaisesRegex(ValueError,'malformed'):p.verify(root,DATA)
 def test_path_escape(self):
  with self.assertRaisesRegex(ValueError,'outside root'):p.safe(self.scratch,'../escape')
 def test_accepted_data_destination_forbidden(self):
  with self.assertRaisesRegex(ValueError,'outside isolated'):
   p.prepare(DATA,DATA/'experiments/atlas/tryfan-regional-pilot-v1')
 def test_resealed_qualification_mismatch(self):
  root=self.scratch/'resealed';shutil.copytree(self.root,root)
  x=p.load(root/'qualification.json');x['families']['dtm']['vertical']='invented datum';(root/'qualification.json').write_bytes(p.canonical(x))
  m=p.load(root/'manifest.json')
  for a in m['artifacts']:
   if a['path']=='qualification.json':a['sha256']=p.sha(root/a['path']);a['bytes']=(root/a['path']).stat().st_size
  m['revision']=p.digest(p.canonical({k:v for k,v in m.items() if k not in ['status','revision']}));(root/'manifest.json').write_bytes(p.canonical(m))
  with self.assertRaisesRegex(ValueError,'qualification identity mismatch'):p.verify(root,DATA)
 def test_interrupted_child_process(self):
  dest=self.scratch/'process-interruption';q=subprocess.run([sys.executable,str(p.H/'prepare.py'),'prepare','--output',str(dest),'--interrupt','pre-completion'],cwd=p.R,capture_output=True,text=True)
  self.assertNotEqual(q.returncode,0);self.assertFalse(any(dest.rglob('manifest.json')));self.assertEqual(p.verify(self.root,DATA)['revision'],self.a['revision'])
 def test_not_world_publication(self):self.assertFalse(any(self.outputs['qualification.json']['integration'][k] for k in ['registered','queryImplemented','derivationsComputed','published','consumerServing']))
if __name__=='__main__':unittest.main()
