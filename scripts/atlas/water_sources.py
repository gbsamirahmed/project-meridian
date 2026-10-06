"""Frozen upper-Exe water evidence acquisition, never an Atlas runtime dependency.
Only native semantic data/metadata windows; no imagery, classification or modelling.
"""
import argparse, datetime, hashlib, json, math, ssl, urllib.parse, urllib.request
from pathlib import Path
import certifi, rasterio
from rasterio.windows import Window, from_bounds
from rasterio.warp import transform_bounds
PLAN = Path('docs/atlas/water-check-plan.json')
PLAN_HASH = '04a9deefbf7ae763268ff9d0974624239c5f02b12ec688fd36927f26a94f2415'
TLS = ssl.create_default_context(cafile=certifi.where())
BASE = 'https://environment.data.gov.uk/spatialdata/'
COLLECTIONS = {
 'wfd': ('simplified-wfd-transitional-and-coastal-water-bodies-cycle-3-classification-2019','Simplified_WFD_Transitional_and_Coastal_Water_Bodies_Cycle_3_Classification_2019'),
 'phi': ('priority-habitat-inventory-england','Priority_Habitat_Inventory_England'),
 'flood': ('flood-map-for-planning-flood-zones','Flood_Zones_2_3_Rivers_and_Sea'),
 'rfo': ('recorded-flood-outlines','Recorded_Flood_Outlines')}
DOCS = {
 'rfo-catalogue.html':'https://www.data.gov.uk/dataset/16e32c53-35a6-4d54-a111-ca09031eaaaf/recorded-flood-outlines1',
 'rfo-description.pdf':'https://environment.data.gov.uk/file-management-open/data-sets/ed73f2e8-a3c2-44db-952d-6e359c7c3987/files/Guidance_Recorded_Flood_Outline_v6_2.pdf',
 'grazing-marsh-definition.pdf':'https://data.jncc.gov.uk/data/82b0af67-d19a-4a89-b987-9dba73be1272/UKBAP-BAPHabitats-07-CoastFloodGrazingMarsh.pdf',
 'wfd-catalogue.html':'https://www.data.gov.uk/dataset/52fa8958-ea30-46fc-8ecb-f31ea8f89aa6/water-framework-directive-wfd-transitional-and-coastal-water-bodies-cycle-3-classification-20191',
 'phi-catalogue.html':'https://www.data.gov.uk/dataset/4b6ddab7-6c0f-4407-946e-d6499f19fcde/priority-habitats-inventory-england',
 'flood-catalogue.html':'https://www.data.gov.uk/dataset/104434b0-5263-4c90-9b1e-e43b1d57c750/flood-map-for-planning-flood-zones1',
 'phi-attributes.pdf':'https://environment.data.gov.uk/api/file/download?fileDataSetId=d30e3fa2-5ca6-4851-b19d-1429ad9d84e0&fileName=Priority_Habitats_Inventory_Attribute_Metadata.pdf',
 'phi-spatial.pdf':'https://environment.data.gov.uk/api/file/download?fileDataSetId=d30e3fa2-5ca6-4851-b19d-1429ad9d84e0&fileName=Priority_Habitats_Inventory_Spatial_Metadata.pdf',
 'phi-lineage.xlsx':'https://environment.data.gov.uk/api/file/download?fileDataSetId=d30e3fa2-5ca6-4851-b19d-1429ad9d84e0&fileName=PHI%20V3%20Datasets.xlsx',
 'flood-description.pdf':'https://environment.data.gov.uk/api/file/download?fileDataSetId=455d2eb3-3065-4d20-871b-c4d5dee23f67&fileName=Flood%20Zones%20Product%20Description.pdf',
 'jrc-guide.pdf':'https://storage.googleapis.com/water-world/downloads_ancillary/DataUsersGuidev2024_v.5.pdf',
 'jrc-access.html':'https://global-surface-water.appspot.com/download',
 'ogl3.html':'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'}
JRC = 'https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/'
RASTERS = {'occurrence': 'download2024/Aggregated/VER1-5/occurrence/occurrence_10W_60N_v1_5_2024.tif'}
for m in ['03','09']: RASTERS['monthly-2024-'+m]=f'MonthlyHistory/2024/2024_{m}/monthlyhistory_10W_60N_v1_5_2024_{m}.tif'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def fetch(root,name,url,receipts,licence,optional=False):
 p=root/name
 if not p.exists():
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Meridian bounded water semantics research'}),timeout=30,context=TLS) as r:
    b=r.read(12000001)
    if len(b)>12000000:raise ValueError('Bounded response budget exceeded: '+name)
    headers={k:r.headers.get(k) for k in ['ETag','Last-Modified','Content-Type']}
   p.write_bytes(b)
   save(root/(name+'.receipt.json'),{'retrievedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'headers':headers})
  except Exception as e:
   if not optional:raise
   receipts.append({'file':name,'url':url,'status':'Not retained: '+str(e)});return None
 receipt=json.loads((root/(name+'.receipt.json')).read_text())
 receipts.append({'file':name,'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'licence':licence,**receipt})
 return p

def acquire(root):
 if sha(PLAN)!=PLAN_HASH:raise ValueError('Frozen plan changed')
 plan=json.loads(PLAN.read_text());root.mkdir(parents=True,exist_ok=True);rs=[]
 frozen=Path('docs/atlas/water-check-sources.json')
 if frozen.exists():
  for f in json.loads(frozen.read_text())['files']:
   if f.get('sha256') and (root/f['file']).exists() and sha(root/f['file'])!=f['sha256']:raise ValueError('Source changed '+f['file'])
 for k,(slug,col) in COLLECTIONS.items():
  base=BASE+slug+'/ogc/features/v1/collections/'+col
  fetch(root,k+'-collection.json',base+'?f=json',rs,'OGL3; PHI contributor CC-BY4 notice retained' if k=='phi' else 'OGL3, EA/OS credit as applicable')
  fetch(root,k+'-schema.json',base+'/queryables?f=json',rs,'OGL3')
  params={'f':'json','bbox':','.join(map(str,plan['bounds'])),'bbox-crs':'http://www.opengis.net/def/crs/EPSG/0/27700','crs':'http://www.opengis.net/def/crs/EPSG/0/27700','limit':2000}
  path=fetch(root,k+'.geojson',base+'/items?'+urllib.parse.urlencode(params),rs,'OGL3; retain publisher/contributor credits')
  d=json.loads(path.read_text());assert d['type']=='FeatureCollection'
  if any(l.get('rel')=='next' for l in d.get('links',[])) or d.get('numberMatched',len(d['features']))>len(d['features']):raise ValueError('Incomplete vector query: '+k)
  print(k,len(d['features']),'features',path.stat().st_size,'bytes',flush=True)
 for name,url in DOCS.items():fetch(root,name,url,rs,'Publisher documentation; rights and notices retained',optional=name.endswith('.html'))
 bb=transform_bounds('EPSG:27700','EPSG:4326',*plan['bounds'],densify_pts=40)
 for name,key in RASTERS.items():
  url=JRC+key;p=root/(name+'.tif')
  fetch(root,name+'-listing.json',JRC+'?'+urllib.parse.urlencode({'format':'json','prefix':key,'limit':2}),rs,'Copernicus reuse, EC JRC/Google, Pekel et al.2016')
  if not p.exists():
   with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_TIMEOUT='30',GDAL_HTTP_MAX_RETRY='1',GDAL_HTTP_CAINFO=certifi.where(),VSI_CACHE=False):
    with rasterio.open('/vsicurl/'+url) as src:
     w=from_bounds(*bb,src.transform);x,y=math.floor(w.col_off),math.floor(w.row_off)
     w=Window(x,y,math.ceil(w.col_off+w.width)-x,math.ceil(w.row_off+w.height)-y)
     if w.width*w.height>100000:raise ValueError('Raster window budget exceeded')
     a=src.read(1,window=w);t=src.window_transform(w)
     profile={'driver':'GTiff','count':1,'dtype':str(a.dtype),'height':a.shape[0],'width':a.shape[1],'crs':src.crs,'transform':t,'compress':'LZW'}
     # Keep raw codes, including 0 no-observations in monthly history. Never mask it as physical absence.
     with rasterio.open(p,'w',**profile) as dst:dst.write(a,1)
     save(root/(name+'-window.json'),{'sourceUrl':url,'sourceCrs':str(src.crs),'sourceShape':list(src.shape),'sourceTransform':list(src.transform),'sourceNodata':src.nodata,'blockShape':list(src.block_shapes[0]),'window':[w.col_off,w.row_off,w.width,w.height],'windowTransform':list(t),'operation':'Native integer grid window; no reprojection/resampling; lossless re-encoding. Cell-centre selection only in analysis.','retrievedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wireBytesKnown':False,'parentSha256Known':False})
   print(name,a.shape,flush=True)
  rs.append({'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size,'url':url,'licence':'Copernicus reuse; Source: EC JRC/Google; Pekel et al.2016 DOI10.1038/nature20584','subset':json.loads((root/(name+'-window.json')).read_text()),'parentListing':json.loads((root/(name+'-listing.json')).read_text())})
 save(root/'acquisition.json',{'planSha256':PLAN_HASH,'files':rs,'retainedBytes':sum(f.get('bytes',0) for f in rs),'excess':'Complete intersecting API polygons may extend beyond frozen window. Raster compressed native blocks read remotely; no 10-degree TIFF downloaded in full; wire bytes unknown.','freezeOrderVerified':all(f.get('retrievedUtc',f.get('subset',{}).get('retrievedUtc','9999'))>plan['frozenUtc'] for f in rs)})
 print('Total retained',sum(f.get('bytes',0) for f in rs),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args();acquire(a.data)
