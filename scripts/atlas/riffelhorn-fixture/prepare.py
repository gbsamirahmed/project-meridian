"""Offline preparation of the frozen native Riffelhorn metadata fixture.
No acquisition, resampling, physical derivation, registration or publication.
"""
from pathlib import Path
import argparse,hashlib,json,platform,subprocess,sys,time,uuid
from collections import Counter
import fiona,pyproj,rasterio,shapely
from shapely.geometry import shape,box
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.path.insert(0,str(R/'scripts'))
from meridian_paths import resolve_storage_roots
SPEC=R/'docs/research/atlas-regional-expansion-fixture.json'
PLAN=H/'plan.json';CORE=[2624000,1091000,2626000,1093000]
METHOD='atlas-riffelhorn-native-preparation/v1'
FILES=['input-manifest.json','raster-bindings.json','features.json','semantic-evidence.json','qualification.json']

def canonical(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
def digest(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();require(p.is_relative_to(root.resolve()),'path outside root');return p
def tools():return dict(python=platform.python_version(),rasterio=rasterio.__version__,gdal=rasterio.__gdal_version__,fiona=fiona.__version__,shapely=shapely.__version__,pyproj=pyproj.__version__,proj=pyproj.proj_version_str)
def header(p):
 with rasterio.open(p) as x:
  return dict(crs=str(x.crs),bounds=list(x.bounds),shape=list(x.shape),bands=x.count,dtypes=list(x.dtypes),resolution=list(x.res),transform=list(x.transform),nodata=x.nodata,tags=x.tags())
def check_header(actual,expected):require(actual==expected,'unsupported CRS or mismatched native raster header')
def check_features(x,family,baseline):
 fs=x.get('results',x.get('features'));require(isinstance(fs,list),'malformed native feature collection')
 require(len(fs)==baseline['records'],'native feature selection count mismatch')
 require([str(f['id']) for f in fs]==baseline['identities'],'native feature IDs mismatch')
 require(sorted(set(k for f in fs for k in f['properties']))==baseline['propertyKeys'],'native field selection mismatch')
 require(len(set(str(f['id']) for f in fs))==len(fs),'duplicate native feature ID')
 for f in fs:
  g=shape(f['geometry']);require(g.is_valid and not g.is_empty,'invalid native geometry; repair forbidden')
  require(g.intersection(box(*CORE)).area>0,'feature lacks positive-area core applicability')
  require(all(v is None or isinstance(v,(str,int,float,bool)) for v in f['properties'].values()),'non-scalar native fields')
  if family.startswith('geocover'):
   require(f['id']==f['featureId'],'GeoCover source ID mismatch')
   suffix='bedrock' if family.endswith('bedrock') else 'unconsolidated'
   require(f['layerBodId']=='ch.swisstopo.geologie-swissgeocover2d_'+suffix,'wrong native GeoCover layer')
  else:require(x['nativeCrs']=='EPSG:2056' and f['properties']['sgi-id']=='B56-07','GLAMOS native CRS/parent mismatch')
 return fs

def reproduce_glamos(data,spec,subsets):
 zip_path=data/spec['inputs'][9]['path']
 for family,layer in [('glaciers','SGI_2016_glaciers'),('debris','SGI_2016_debriscover')]:
  saved={f['id']:f for f in subsets[family]};selected=[]
  with fiona.open('zip://'+str(zip_path),layer=layer) as src:
   require(src.crs.to_epsg()==2056,'unsupported GLAMOS CRS')
   for f in src.filter(bbox=CORE):
    if shape(f['geometry']).intersection(box(*CORE)).area>0:selected.append(f)
  require(len(selected)==len(saved),'GLAMOS original selection mismatch')
  for f in selected:
   require(f['id'] in saved and dict(f['properties'])==saved[f['id']]['properties'] and shape(f['geometry']).equals_exact(shape(saved[f['id']]['geometry']),1e-8),'GLAMOS original geometry/field mismatch')
 return {'method':'native2056 bbox prefilter then positive-area intersection; retain full geometry','comparisonToleranceM':1e-8,'counts':{'glaciers':1,'debris':6},'geometryClipping':False,'geometryRepair':False}

def qualify(spec,environment):
 # Densify boundary only. This creates no new height or physical observation.
 ring=[];x0,y0,x1,y1=CORE
 for a,b in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
  for n in range(32):ring.append([a[0]+(b[0]-a[0])*n/32,a[1]+(b[1]-a[1])*n/32])
 ring.append(ring[0]);tr=pyproj.Transformer.from_crs(2056,4326,always_xy=True)
 transformed=[list(tr.transform(*p)) for p in ring]
 return dict(schema='atlas-riffelhorn-qualification/v1',core={'crs':'EPSG:2056','bounds':CORE,'areaKm2':4},eligibility={'kind':'geojson','geometry':{'type':'Polygon','coordinates':[transformed]}},coordinateOperation={'from':'EPSG:2056','to':'OGC:CRS84','always_xy':True,'segmentsPerEdge':32,'description':tr.description,'reportedAccuracyM':tr.accuracy,'proj':environment['proj'],'verticalOperation':'none','meaning':'2D transformed core applicability only; not full-feature support or raster envelope'},families={
 'dtm':{'meaning':'swissALTI3D bare-earth DTM; sampling is not accuracy','vertical':'LN02 / EPSG:5728 documented provider provenance; not embedded compound CRS','time':'2024 product; mixed2021/2022 lidar and2023 imagery; per-cell dates unknown'},
 'dsm':{'meaning':'Independent Copernicus DSM including surface objects and possible infill','vertical':'EGM2008 / EPSG:3855 documented provider provenance','time':'2010-2015 observations plus infill;2021 distribution, exact subrelease/per-cell dates unknown'},
 'worldcover':{'meaning':'2021 v200 native categorical classification; not cell truth, fraction or confidence','time':'nominal2021 epoch; exact pixel observation dates unknown'},
 'geocover':{'meaning':'Interpreted substrate/deposit mapping, not current visible exposure or complete absence','vertical':'Third ordinate retained unchanged; meaning unknown','time':'retained API snapshot; release identity and survey epochs unknown; geological ages are not observation dates'},
 'glamos':{'meaning':'Dated inventory membership, not current glacier truth or exposed-ice fraction','time':'glacier feature2015, debris2016; SGI2016r2020 product release'}},rightsBoundary=spec['rightsBoundary'],rightsReferences=spec['rightsReferences'],optionalReferences=spec['optionalReferencePreparations'],unknowns=spec['nonBlockingUnknowns'],excludedClaims=spec['excludedClaims'],supportRules={'nativeFeature':'full native geometry retained, may extend outside core','applicability':'positive-area core intersection is selection, not clipping or complete coverage','worldcover':'native rectangular crop envelope is larger than transformed core','outsideCore':'outside-support, not evidence of physical absence','missing':'unknown/not-covered/unsupported must remain distinct; no extrapolation'},integration={'prepared':True,'registered':False,'queryImplemented':False,'derivationsComputed':False,'published':False,'consumerServing':False},software=environment)

def expected_source(path,family,inventory):
 if family=='worldcover':
  receipt=next(a for a in inventory['semanticInputs'] if a['path']==path)
  return {'organisation':'ESA WorldCover consortium','dataset':'ESA WorldCover2021v200','retainedExtractIdentity':receipt['sha256'],'upstreamByteIdentity':{'status':'unknown','reason':'complete parent hash not established'},'upstreamRecord':receipt.get('sourceReceipt',{}),'preparation':'existing native-grid window; no resampling','sourceRecord':'docs/atlas/semantic-comparison-sources.json'}
 item=next(a for a in inventory['sourceAvailability'] if a['path']==path)
 return {'organisation':'swisstopo' if family=='dtm' else 'Copernicus DEM provider','dataset':'swissALTI3D2024 DTM' if family=='dtm' else 'Copernicus GLO30-F DSM distribution2021','retainedArtifactIdentity':item['recordedSha256'],'upstreamByteIdentity':'not established by current hash alone','sourceRecord':'docs/atlas/riffelhorn-support-acquisition.json' if family=='dtm' else 'docs/atlas/copernicus-common-acquisition.json','upstreamUrl':item['url'],'productRecord':item.get('officialItem',item.get('retentionReference')),'properties':item.get('officialProperties',{})}
def raster_rights(family):
 spec=load(SPEC)
 if family=='dtm':licence='swisstopo OGD source-credit terms';credit='© swisstopo; Meridian native support bindings, no elevation transformation.'
 elif family=='dsm':
  rights=load(R/'docs/atlas/copernicus-common-metadata.json')['source']['rights']
  return {**rights,'references':[*rights['references'],'docs/atlas/copernicus-common-metadata.json'],'preparationNotice':'Native support bindings only; unchanged DEM bytes; local proof, no legal delivery notice or source redistribution.'}
 else:licence='CC-BY-4.0';credit=load(R/'docs/atlas/semantic-comparison-sources.json')['requiredCredits']['WorldCover']
 return {'licence':{'status':'known','value':licence},'attribution':[credit],'references':spec['rightsReferences'],'limitations':spec['rightsBoundary']}

def build(data):
 spec=load(SPEC);plan=load(PLAN);require(sha(SPEC)==plan['specificationSha256'],'frozen specification changed')
 inventory=load(R/'docs/research/atlas-regional-expansion-inventory.json');env=tools()
 require(env==plan['toolchain'],'unqualified toolchain change; review reproducibility boundary')
 require(spec['supports'][0]['bounds']==CORE and len(spec['inputs'])==12,'wrong frozen target')
 for a in spec['inputs']:
  p=safe(data,a['path']);require(p.is_file(),'missing required input '+a['path'])
  require(p.stat().st_size==a['bytes'],'input size mismatch '+a['path']);require(sha(p)==a['sha256'],'input hash mismatch '+a['path'])
 inputs=[{**a,'artifactIdentity':'sha256:'+a['sha256'],'upstreamAuthenticity':'not established by content hash','locatorRoot':'configured public meridian-data'} for a in spec['inputs']]
 rasters=[];expected={a['path']:a['header'] for a in inventory['sourceAvailability'] if 'header' in a}
 expected.update({a['path']:a['header'] for a in inventory['semanticInputs'] if 'header' in a})
 for i in [0,1,2,3,4,5]:
  a=inputs[i];h=header(safe(data,a['path']));check_header(h,expected[a['path']])
  family='dtm' if i<4 else 'dsm' if i==4 else 'worldcover'
  rasters.append({'id':family+':'+a['sha256'],'family':family,'input':a,'native':h,'sampling':'none; existing grid retained','verticalTransformation':'none','coreApplicability':{'crs':'EPSG:2056','bounds':CORE},'identityMeaning':'retained artifact bytes; not measurement truth','sourceRecord':expected_source(a['path'],family,inventory),'rights':raster_rights(family)})
 require(shapely.union_all([box(*x['native']['bounds']) for x in rasters[:4]]).equals(box(*CORE)) and sum(box(*x['native']['bounds']).area for x in rasters[:4])==4e6,'DTM support gap/overlap')
 window=load(safe(data,inputs[6]['path']));require(window['sourceCrs']=='EPSG:4326' and window['window']==[20979,24142,312,218] and window['windowTransform']==rasters[5]['native']['transform'],'native WorldCover window mismatch')
 with rasterio.open(safe(data,inputs[5]['path'])) as src:
  counts={str(int(k)):int(v) for k,v in sorted(Counter(src.read(1).ravel().tolist()).items())}
 require(set(map(int,counts))<={0,10,20,30,40,50,60,70,80,90,95,100},'unsupported WorldCover class')
 rasters[5]['window']=window;rasters[5]['nativeCodeCounts']=counts;rasters[5]['parentByteIdentity']={'status':'unknown','reason':'full source tile not retained/hashed by this proof'}
 features=[];subsets={};baseline={Path(a['path']).name:a for a in inventory['semanticInputs'] if 'records' in a}
 for i,family in [(7,'geocover-bedrock'),(8,'geocover-unconsolidated'),(10,'glaciers'),(11,'debris')]:
  a=inputs[i];x=load(safe(data,a['path']));fs=check_features(x,family,baseline[Path(a['path']).name]);subsets[family]=fs
  for f in fs:
   identity=family+':'+str(f['id'])
   features.append({'identity':identity,'revision':a['sha256'],'family':family,'nativeCrs':'EPSG:2056','retainedInput':a['artifactIdentity'],'native':f,'supportMeaning':'full native geometry; selected by positive-area intersection; no clipping','coreApplicability':CORE,'parentGlacier':('glaciers:683' if family=='debris' else None),'verticalMeaning':'unknown; third ordinate preserved, never interpreted' if family.startswith('geocover') else '2D inventory outline'})
 original=reproduce_glamos(data,spec,subsets)
 q=qualify(spec,env);q['glamosSelection']=original
 return {'input-manifest.json':{'schema':'atlas-riffelhorn-inputs/v1','specificationSha256':sha(SPEC),'inputs':inputs,'originalsUnchanged':True},'raster-bindings.json':{'schema':'atlas-riffelhorn-native-rasters/v1','rasters':rasters},'features.json':{'schema':'atlas-riffelhorn-native-features/v1','features':features},'qualification.json':q,'semantic-evidence.json':semantic(inputs,rasters,features,q)}

def semantic(inputs,rasters,features,q):
 known=lambda x:{'status':'known','value':x}
 unknown=lambda x:{'status':'unknown','reason':x}
 ref=lambda x:{'id':x,'revision':'1'}
 credits=load(R/'docs/atlas/semantic-comparison-sources.json')['requiredCredits']
 resources=[];definitions=[];collections=[];mappings=[];products={}
 families=[('worldcover',5,'ESA WorldCover2021v200','CC-BY-4.0','WorldCover'),('geocover-bedrock',7,'swissGEOCOVER2D retained bedrock snapshot','swisstopo OGD source-credit terms','GeoCover'),('geocover-unconsolidated',8,'swissGEOCOVER2D retained unconsolidated snapshot','swisstopo OGD source-credit terms','GeoCover'),('glaciers',10,'GLAMOS SGI2016r2020 glaciers','CC-BY-4.0','GLAMOS'),('debris',11,'GLAMOS SGI2016r2020 debris','CC-BY-4.0','GLAMOS')]
 for family,i,name,licence,credit in families:
  src={'kind':'source','id':family+':provider-product','revision':unknown('exact snapshot release unknown') if family.startswith('geocover') else known('2021v200' if family=='worldcover' else 'SGI2016r2020')}
  prod={'kind':'product','id':family+':retained-preparation','revision':known(inputs[i]['sha256'])};products[family]=prod
  rights={'licence':known(licence),'references':['docs/atlas/semantic-comparison-sources.json',*q['rightsReferences']],'attribution':[credits[credit]],'limitations':q['rightsBoundary']}
  for entity,parents in [(src,[]),(prod,[src])]:
   resources.append({'ref':entity,'domain':'semantics','name':name,'definition':{'href':'docs/research/atlas-regional-expansion-fixture.json','selector':family},'rights':rights,'inputs':parents})
  kind='category' if family=='worldcover' else 'descriptor' if family.startswith('geocover') else 'membership'
  meaning=q['families']['worldcover' if family=='worldcover' else 'geocover' if family.startswith('geocover') else 'glamos']['meaning']
  definitions.append({**ref(family+':native-property'),'kind':'property','label':name,'meaning':meaning,'vocabulary':{'id':name,'version':src['revision']},'reference':{'href':'docs/atlas/source-native-semantic-comparison.md'},'valueKinds':[kind]})
 for family,i,name,licence,credit in families:
  prop=ref(family+':native-property');claims=[]
  support={'geometry':{'kind':'asset','asset':{'href':'fixture-relative:features.json','selector':family+' full native geometries'},'crs':known({'name':'CH1903+ / LV95','identifier':'EPSG:2056'}),'interpretation':'Full preserved native geometry; core selection/applicability separately declared'},'meaning':'Native feature support, not core clipped geometry','grain':unknown('not a sampling grid')}
  if family=='worldcover':
   support={'geometry':{'kind':'native-rectangle','crs':{'name':'WGS84 lon/lat','identifier':'EPSG:4326'},'bounds':rasters[5]['native']['bounds'],'axisOrder':'xy'},'meaning':'Retained native crop envelope; codes apply to selected cells, not entire rectangle','grain':known('native 1/12000 degree grid; source nominal10m is not accuracy')}
  t={'kind':'unknown','reason':'GeoCover survey epoch unknown; geological age fields are not observation times'} if family.startswith('geocover') else {'kind':'epoch','value':'2021' if family=='worldcover' else '2015' if family=='glaciers' else '2016','precision':'year','basis':'source nominal classification epoch' if family=='worldcover' else 'native year_acq field'}
  context={'support':support,'time':[{'role':'nominal-epoch' if family=='worldcover' else 'survey','extent':t}], 'evidence':{'modes':['classification' if family=='worldcover' else 'interpreted-mapping' if family.startswith('geocover') else 'survey-inventory'],'description':'Source-native retained evidence, with preparation lineage; no new physical inference','inputs':[{'kind':'resource','ref':products[family],'role':'retained native evidence'}],'completeness':'unknown','limitations':q['families']['worldcover' if family=='worldcover' else 'geocover' if family.startswith('geocover') else 'glamos']['meaning'],'processing':[{'method':METHOD,'revision':known('1'),'software':q['software'],'parameters':{'resampling':False,'geometryClipping':False,'verticalTransformation':False}}]}}
  if family=='worldcover':
   codes={0:'No observation/nodata',10:'Tree cover',20:'Shrubland',30:'Grassland',40:'Cropland',50:'Built-up',60:'Bare / sparse vegetation',70:'Snow and ice',80:'Permanent water bodies',90:'Herbaceous wetland',95:'Mangroves',100:'Moss and lichen'}
   for code,label in codes.items():
    term=ref('worldcover:code:'+str(code))
    if code:
     definitions.append({**term,'kind':'value','label':label,'meaning':'Source-native WorldCover2021v200 nomenclature: '+label+'; limitations per source PUM, not physical truth','vocabulary':{'id':'ESA WorldCover nomenclature','version':known('2021v200 PUM2.0')},'reference':{'href':'docs/atlas/source-native-semantic-comparison.md'}})
    result={'kind':'assertion','value':{'kind':'category','term':term}} if code else {'kind':'gap','reason':'no-observation','explanation':'Native code0/nodata; does not prove physical absence'}
    claim={**ref('worldcover:binding:'+str(code)),'native':{'property':prop,'fields':{'code':code},**({'term':term} if code else {})},'result':result,'record':{'href':'public-data-relative:'+inputs[i]['path'],'sha256':inputs[i]['sha256'],'selector':'native code '+str(code)}}
    claims.append(claim)
  else:
   for f in [f for f in features if f['family']==family]:
    feature={'namespace':products[family],'id':str(f['native']['id']),'kind':'inventory-object'}
    claim={**ref(f['identity']),'native':{'property':prop,'fields':f['native']['properties']},'feature':feature,'result':{'kind':'assertion','value':{'kind':'descriptor','text':f['native']['properties']['label']} if family.startswith('geocover') else {'kind':'membership','feature':feature}},'context':{'support':{**support,'geometry':{**support['geometry'],'asset':{'href':'fixture-relative:features.json','selector':f['identity']+' full native geometry'}}}},'record':{'href':'public-data-relative:'+inputs[i]['path'],'sha256':inputs[i]['sha256'],'selector':str(f['native']['id'])}}
    if family=='debris':claim['associations']=[{'namespace':products['glaciers'],'id':'683','kind':'inventory-object'}]
    claims.append(claim)
  collection={**ref(family+':prepared-collection'),'product':products[family],'representation':'raster' if family=='worldcover' else 'vector','context':context,'claims':claims}
  if family=='worldcover':collection['binding']={'asset':{'href':'public-data-relative:'+inputs[i]['path'],'sha256':inputs[i]['sha256']},'assignment':'Native code dictionary binding; later retrieval selects cells within exact native support. No claim of homogeneous crop cover.','codes':[{'code':c['native']['fields']['code'],'claim':ref(c['id'])} for c in claims]}
  collections.append(collection)
 # Explicitly reject tempting scientific conflations without mapping native values away.
 for family,target,label in [('geocover-bedrock','visible-exposure','Current exposed mineral surface'),('worldcover','glacier-object','Dated glacier inventory object')]:
  definitions.append({**ref('fixture:'+target),'kind':'property','label':label,'meaning':'Rejected candidate interpretation only; this preparation supplies no such physical inference','vocabulary':{'id':'Meridian preparation qualification examples','version':known('1')},'reference':{'href':'docs/research/atlas-regional-expansion-fixture.json'},'valueKinds':['descriptor']})
  m={**ref('rejected:'+family),'from':ref(family+':native-property'),'target':ref('fixture:'+target),'relationship':'unmappable','method':{'method':'preserve source-native meaning'},'loss':['Native substrate/classification does not establish current exposed material or dated glacier object identity'],'qualification':'Do not convert source meaning into this unsupported physical claim'};mappings.append(m)
 return {'contract':'atlas-semantic-evidence/v1','resources':resources,'definitions':definitions,'mappings':mappings,'collections':collections}

def semantic_check(path):
 q=subprocess.run(['node',str(H/'verify_semantic.mjs'),str(path)],cwd=R,capture_output=True,text=True,encoding='utf-8')
 require(q.returncode==0,'frozen semantic contract rejected: '+q.stdout+q.stderr)

def describe(outputs):return [{'path':name,'bytes':len(canonical(outputs[name])),'sha256':digest(canonical(outputs[name]))} for name in FILES]
def identity(outputs):return {'schema':'atlas-riffelhorn-preparation-complete/v1','method':METHOD,'planSha256':sha(PLAN),'specificationSha256':sha(SPEC),'artifacts':describe(outputs)}
def verify(root,data):
 require((root/'manifest.json').is_file(),'incomplete preparation: completion manifest missing')
 m=load(root/'manifest.json');require(isinstance(m,dict) and m.get('schema')=='atlas-riffelhorn-preparation-complete/v1','malformed/unsupported completion manifest')
 require(m.get('status')=='COMPLETE' and m.get('method')==METHOD,'not a complete supported preparation')
 require(isinstance(m.get('artifacts'),list) and [a['path'] for a in m['artifacts']]==FILES,'missing/unknown/unsafe artifact membership')
 for a in m['artifacts']:
  p=safe(root,a['path']);require(p.is_file(),'missing prepared artifact')
  require(p.stat().st_size==a['bytes'] and sha(p)==a['sha256'],'prepared artifact identity mismatch')
 outputs=build(data);expected=identity(outputs)
 require({k:m.get(k) for k in expected}==expected,'preparation/source/qualification identity mismatch')
 require(m['revision']==digest(canonical(expected)),'preparation revision mismatch')
 semantic_check(root/'semantic-evidence.json')
 return m

def prepare(data,destination,interrupt=None):
 start=time.perf_counter();outputs=build(data);built=time.perf_counter();dest=destination.resolve()
 require(not dest.is_relative_to(R),'prepared payloads must stay outside code repository')
 if dest.is_relative_to(data):
  require(dest.is_relative_to(data/'derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1'),'preparation destination outside isolated Riffelhorn proof subtree')
 stage=dest/('staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
 # No completion marker is present until every artifact and contract has passed.
 for n,name in enumerate(FILES):
  (stage/name).write_bytes(canonical(outputs[name]))
  if interrupt=='early' and n==0:raise RuntimeError('injected early staging interruption: '+str(stage))
 semantic_check(stage/'semantic-evidence.json')
 if interrupt=='pre-completion':raise RuntimeError('injected pre-completion interruption: '+str(stage))
 body=identity(outputs);revision=digest(canonical(body));m={**body,'status':'COMPLETE','revision':revision}
 (stage/'manifest.json').write_bytes(canonical(m));verified=time.perf_counter();verify(stage,data)
 target=dest/revision;retry=target.exists()
 if retry:
  old=verify(target,data);require(old==m,'immutable preparation retry collision')
  # Keep isolated completed staging as evidence of retry; never overwrite/delete old state.
 else:stage.rename(target)
 end=time.perf_counter()
 return {'revision':revision,'preparedRoot':str(target),'artifactCount':len(FILES)+1,'inputArtifactCount':12,'inputHashBytesPerBuild':sum(a['bytes'] for a in load(SPEC)['inputs']),'outputBytes':sum(a['bytes'] for a in m['artifacts'])+len(canonical(m)),'timingSeconds':{'build':built-start,'encodingAndSemanticValidation':verified-built,'freshVerificationAndFinalize':end-verified,'total':end-start},'byteAccounting':'Input hash bytes exact per build; verification repeats build. GDAL/Fiona header/archive reads are not reliably counted physical I/O. Outputs exact UTF8 bytes; no raster payload copying.','retry':retry}

def main():
 a=argparse.ArgumentParser();a.add_argument('operation',choices=['prepare','verify']);a.add_argument('--data-root',type=Path);a.add_argument('--output',type=Path,required=True);a.add_argument('--interrupt',choices=['early','pre-completion']);args=a.parse_args()
 data=(args.data_root or resolve_storage_roots(repository_root=R,require_data=True).data).resolve()
 if args.operation=='prepare':result=prepare(data,args.output,args.interrupt)
 else:
  start=time.perf_counter();m=verify(args.output,data);result={'revision':m['revision'],'artifactCount':len(m['artifacts'])+1,'verificationSeconds':time.perf_counter()-start,'complete':True,'registered':False,'published':False}
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8')
 try:main()
 except (ValueError,KeyError,TypeError,FileNotFoundError,RuntimeError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
