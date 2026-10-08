"""Read-only named Atlas inventory. No acquisition, preparation, ingestion or source writes.
--check reconstructs the same inventory and compares it without rewriting it.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,zipfile
import rasterio,fiona,shapely,pyproj,platform
from shapely.geometry import shape,box
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.path.insert(0,str(R/'scripts'))
from meridian_paths import resolve_storage_roots
D=resolve_storage_roots(repository_root=R,require_data=True).data
OUT=R/'docs/research/atlas-regional-expansion-inventory.json'
CORE=[2624000,1091000,2626000,1093000]
STATUS=['VERIFIED','DOCUMENTED BUT NOT INDEPENDENTLY VERIFIED','UNKNOWN','NOT APPLICABLE']
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def raster(p):
 with rasterio.open(p) as x:
  return dict(crs=str(x.crs),bounds=list(x.bounds),shape=list(x.shape),bands=x.count,dtypes=list(x.dtypes),resolution=list(x.res),transform=list(x.transform),nodata=x.nodata,tags=x.tags())
def build():
 spec=importlib.util.spec_from_file_location('storage_measure',R/'scripts/atlas/storage_requirements/measure.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);old=m.build()
 reads={}
 def record(rel):
  p=R/rel;reads[rel]=sha(p);return load(p)
 acquisition=record('docs/atlas/riffelhorn-support-acquisition.json');cop=record('docs/atlas/copernicus-common-acquisition.json');native=record('docs/atlas/semantic-comparison-sources.json')
 records=[]
 for key,assets in [('swiss-support',acquisition['assets']),('copernicus',cop['assets'])]:
  for a in assets:
   p=D/a['path'];actual=p.stat().st_size
   if actual!=a['bytes']:raise ValueError('source size drift '+a['path'])
   core=key=='swiss-support' and box(*a['bounds']).intersection(box(*CORE)).area>0
   hash_now=core or (key=='copernicus' and a['latitude']==45 and a['longitude']==7)
   row=dict(family=key,path=a['path'],bytes=actual,recordedSha256=a['sha256'],url=a['url'],availability='VERIFIED',identityVerification='VERIFIED' if hash_now else 'DOCUMENTED BUT NOT INDEPENDENTLY VERIFIED',currentFullHash=hash_now)
   if hash_now:
    row['currentSha256']=sha(p)
    if row['currentSha256']!=a['sha256']:raise ValueError('source hash drift '+a['path'])
   if core or key=='copernicus':row['header']=raster(p)
   if key=='swiss-support':row['support']=a['bounds'];row['officialItem']=a['officialItem'];row['officialProperties']=a['officialProperties']
   else:row['retentionReference']=a['acquiredAt']
   if key=='swiss-support' and not core:
    for k in ['url','officialItem','officialProperties']:row.pop(k,None)
    row['authoritativeRecord']='docs/atlas/riffelhorn-support-acquisition.json; exact path key'
   row['selectedCoreInput']=core;records.append(row)
 semantic_dir=D/'derived/atlas/semantic-comparison-v1'
 selected=['riffelhorn-worldcover.tif','riffelhorn-worldcover-window.json','geocover-bedrock.json','geocover-unconsolidated.json','glamos.zip','SGI_2016_glaciers-subset.json','SGI_2016_debriscover-subset.json']
 receipts={a['file']:a for a in native['files']};sem=[]
 for name in selected:
  p=semantic_dir/name;h=sha(p);prior=receipts.get(name)
  if prior and prior.get('sha256') and h!=prior['sha256']:raise ValueError('semantic drift '+name)
  row=dict(path='derived/atlas/semantic-comparison-v1/'+name,bytes=p.stat().st_size,sha256=h,availability='VERIFIED',byteIdentity='VERIFIED',upstreamByteIdentity='UNKNOWN')
  if prior:row['sourceReceipt']={k:prior[k] for k in ['url','retainedUtcFromFilesystem','parentHeadersCheckedUtc','completeParentHashKnown','subsetDefinition','operation'] if k in prior}
  if name.endswith('.tif'):row['header']=raster(p)
  if name.endswith('.json') and ('geocover' in name or 'SGI_' in name):
   x=load(p);fs=x.get('results',x.get('features'));row['records']=len(fs);row['identities']=[str(f.get('id',f.get('featureId'))) for f in fs];row['geometryBounds']=[list(shape(f['geometry']).bounds) for f in fs];row['geometryValid']=all(shape(f['geometry']).is_valid for f in fs)
   row['propertyKeys']=sorted(set(k for f in fs for k in f['properties']))
   if 'SGI_' in name:row['nativeCrs']=x['nativeCrs'];row['featureYears']=sorted(set(f['properties']['year_acq'] for f in fs));row['sgiIds']=sorted(set(f['properties']['sgi-id'] for f in fs))
  sem.append(row)
 # Independently reproduce the existing selection from retained original ZIP, in memory only.
 original=[]
 for layer in ['SGI_2016_glaciers','SGI_2016_debriscover']:
  saved=load(semantic_dir/(layer+'-subset.json'))['features'];byid={f['id']:f for f in saved};selected_original=[]
  with fiona.open('zip://'+str(semantic_dir/'glamos.zip'),layer=layer) as src:
   if src.crs.to_epsg()!=2056:raise ValueError('GLAMOS CRS')
   for f in src.filter(bbox=CORE):
    if shape(f['geometry']).intersection(box(*CORE)).area<=0:continue
    selected_original.append(f)
   identical=len(selected_original)==len(saved) and all(f['id'] in byid and dict(f['properties'])==byid[f['id']]['properties'] and shape(f['geometry']).equals_exact(shape(byid[f['id']]['geometry']),1e-8) for f in selected_original)
  if not identical:raise ValueError('GLAMOS subset not reproduced '+layer)
  original.append(dict(layer=layer,records=len(saved),nativeCrs='EPSG:2056',offlineSelectionIdentical=True,coordinateComparisonToleranceM=1e-8))
 with zipfile.ZipFile(semantic_dir/'glamos.zip') as z:
  archive=dict(entries=z.namelist(),readme=z.read('ReadMe.txt').decode('utf-8-sig',errors='replace'),prjHashes={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.endswith('.prj')})
 # Existing Welsh sources and water receipts are assessed by explicit paths/records only.
 welsh=record('src/atlas/terrain/metadata/tryfanProductRecord.json');wp=D/welsh['source']['path'];welsh_header=dict(path=welsh['source']['path'],bytes=wp.stat().st_size,header=raster(wp),priorSha256=welsh['source']['sha256'],currentFullHash=False)
 water=record('docs/atlas/water-check-sources.json');water_files=[]
 for a in water.get('files',[]):
  if 'file' not in a or 'bytes' not in a:continue
  p=D/'derived/atlas/water-check-v1'/a['file']
  water_files.append(dict(file=a['file'],available=p.is_file(),bytes=p.stat().st_size if p.is_file() else None,recordedBytes=a['bytes'],recordedSha256=a.get('sha256'),sourceUrl=a.get('url')))
 catalog=record('docs/atlas/riffelhorn-data-catalog.json');other=[]
 for a in catalog['assets']:
  p=D/catalog['external_root_relative']/a['path']
  if p.stat().st_size!=a['bytes']:raise ValueError('catalogue source size drift '+a['path'])
  row=dict(family=a['product'],path=str(p.relative_to(D)).replace(chr(92),'/'),bytes=a['bytes'],recordedSha256=a['sha256'],sourceItem=a['item_id'],sourceUrl=a['receipt']['url'],retainedAt=a['receipt']['download_utc'],previousOfficialChecksumMatch=a.get('authoritative_sha256_matches'),availability='VERIFIED',currentFullHash=False,identityVerification='DOCUMENTED BUT NOT INDEPENDENTLY VERIFIED',horizontalReference=a.get('horizontal_reference'),verticalReference=a.get('vertical_reference'),nativeResolution=a.get('native_observation_resolution_m'),priorHeaderReference='docs/atlas/riffelhorn-data-catalog.json; asset actual_file',sourceMethod=a.get('source_method'))
  if a['product']=='swisssurface3d-raster':row['currentHeader']=raster(p)
  other.append(row)
 dsm=wp.with_name('tryfan-004-dsm-1m.tif');welsh_dsm=dict(path=str(dsm.relative_to(D)).replace(chr(92),'/'),bytes=dsm.stat().st_size,header=raster(dsm),currentFullHash=False,identityVerification='DOCUMENTED BUT NOT INDEPENDENTLY VERIFIED',role='retained observed-surface preparation; not adopted as bare-earth terrain')
 return dict(schema='atlas-regional-expansion-inventory/v1',environment=dict(python=platform.python_version(),rasterio=rasterio.__version__,gdal=rasterio.__gdal_version__,fiona=fiona.__version__,shapely=shapely.__version__,pyproj=pyproj.__version__,proj=pyproj.proj_version_str),startingCheckpoint=load(H/'plan.json')['startingCheckpoint'],planSha256=sha(H/'plan.json'),statusVocabulary=STATUS,inspectionScope='Read-only named metadata/header/stat inventory; current hashes only selected compact inputs, four core Swiss TIFFs and one COG; no pixel preparation or new data',recordsReadSha256=reads,knownPreparationInventory=old['products'],priorArchiveAndWorking=old['reportedArchiveAndWorking'],sourceAvailability=records,semanticInputs=sem,glamosOriginalVerification=original,glamosArchive=archive,welshSource=welsh_header,waterReceiptAvailability=water_files,waterReceiptSummary={k:water[k] for k in ['retainedBytes','totalDirectoryBytes','rightsGate'] if k in water},additionalOriginalSources=other,additionalCatalogueStorage=catalog['storage'],welshDsm=welsh_dsm,selectedNativeInputsBytes=sum(r['bytes'] for r in records if r['selectedCoreInput'])+sum(s['bytes'] for s in sem),currentPayloadHashBytes=sum(r['bytes'] for r in records if r['currentFullHash'])+sum(s['bytes'] for s in sem),limitation='Stat/header checks do not prove all current payload hashes; recorded archive hashes and prior reproducibility are separately labelled. No website refresh implies retained data version or per-cell survey date.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();x=build();s=json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
 if args.check:
  if OUT.read_text(encoding='utf-8')!=s:raise SystemExit('Inventory changed')
 else:OUT.write_text(s,encoding='utf-8',newline='\n')
 print(json.dumps(dict(mode='check' if args.check else 'record',sourceFilesStatChecked=len(x['sourceAvailability']),preparedFilesStatChecked=sum(p['payloadFilesStatChecked'] for p in x['knownPreparationInventory']),currentPayloadHashBytes=x['currentPayloadHashBytes'],selectedNativeInputsBytes=x['selectedNativeInputsBytes'],glamosOfflineReproduction=x['glamosOriginalVerification'])))
