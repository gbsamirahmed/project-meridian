"""Bounded acquisition receipts for a frozen semantic crosswalk experiment.
No classification, source ranking, runtime or production imports.
"""
import argparse, datetime, hashlib, json, math, urllib.request, urllib.parse
from pathlib import Path
import rasterio
import ssl, certifi
TLS = ssl.create_default_context(cafile=certifi.where())
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds

URLS = {
 'worldcover-manual.pdf': ('https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf', {}),
 'nrw-vegetation-full-features.json': ('https://datamap.gov.wales/geoserver/ows', {'service':'WFS','version':'1.0.0','request':'GetFeature','typename':'geonode:nrw_phase1_vegetation_voronoi','outputFormat':'application/json','srsName':'EPSG:27700','bbox':'264900,357800,267900,360800,EPSG:27700','maxFeatures':2000}),
 'nrw-survey-area.json': ('https://datamap.gov.wales/geoserver/ows', {'service':'WFS','version':'1.0.0','request':'GetFeature','typename':'geonode:nrw_phase1_survey_area','outputFormat':'application/json','srsName':'EPSG:27700','bbox':'264900,357800,267900,360800,EPSG:27700','maxFeatures':2000}),
 'glamos.zip': ('https://doi.glamos.ch/data/inventory/inventory_sgi2016_r2020.zip', {}),
 'jncc-codes.xls': ('https://data.jncc.gov.uk/data/9578d07b-e018-4c66-9c1b-47110f14df2a/phase-1-habitat-dominant-species-codes-2008.xls', {}),
 'jncc-handbook.pdf': ('https://data.jncc.gov.uk/data/9578d07b-e018-4c66-9c1b-47110f14df2a/handbook-phase-1-habitat-survey-revised-2016.pdf', {}),
 'nrw-group.html': ('https://datamap.gov.wales/layergroups/geonode:nrw_terrestrial_phase_1_habitat_survey', {}),
 'worldcover-rights.html': ('https://esa-worldcover.org/en/data-access', {}),
 'swisstopo-rights.html': ('https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices', {}),
 'geocover-structure.html': ('https://www.geo.admin.ch/en/new-structure-of-the-swissgeocover2d-datasets-on-mapgeoadminch', {}),
 'glamos-rights.html': ('https://doi.glamos.ch/data/inventory/inventory_sgi2016_r2020.html', {}),
}
for part in ['bedrock','unconsolidated']:
 URLS['geocover-'+part+'.json']=('https://api3.geo.admin.ch/rest/services/all/MapServer/identify', {'geometry':'2624000,1091000,2626000,1093000','geometryType':'esriGeometryEnvelope','sr':2056,'layers':'all:ch.swisstopo.geologie-swissgeocover2d_'+part,'mapExtent':'2624000,1091000,2626000,1093000','imageDisplay':'1000,1000,96','tolerance':0,'returnGeometry':'true','geometryFormat':'geojson','lang':'en'})

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value): Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def url_for(base,params): return base+('?' + urllib.parse.urlencode(params) if params else '')

def acquire(root,plan):
 root.mkdir(parents=True,exist_ok=True)
 if sha('docs/atlas/semantic-comparison-plan.json')!='62739330a5931120dbdcf14743b5be6f8acc5da5dfc3acbe6747e0aaa0daacd7':raise ValueError('Frozen plan changed')
 frozen=Path('docs/atlas/semantic-comparison-sources.json')
 if frozen.exists():
  for f in json.loads(frozen.read_text(encoding='utf-8'))['files']:
   if f.get('sha256') and (root/f['file']).exists() and sha(root/f['file'])!=f['sha256']:raise ValueError('Retained source differs: '+f['file'])
 receipts=[]
 for name,(base,params) in URLS.items():
  path=root/name;url=url_for(base,params)
  if not path.exists() and name.endswith('.html'):
   receipts.append({'file':name,'url':url,'status':'Rights verified through authoritative web documentation; optional local HTML not retained'})
   continue
  if not path.exists():
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Meridian bounded research metadata'}),timeout=30,context=TLS) as r:
    size=r.headers.get('Content-Length')
    if size and int(size)>12000000: raise ValueError('acquisition budget exceeded')
    data=r.read(12000001)
    if len(data)>12000000: raise ValueError('acquisition budget exceeded')
   path.write_bytes(data)
  receipt={'file':name,'url':url,'bytes':path.stat().st_size,'sha256':sha(path),'retainedUtcFromFilesystem':datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat(),'licence':'CC-BY-4.0' if name=='glamos.zip' else ('swisstopo OGD source-credit terms' if name.startswith('geocover') else ('OGL3 with NRW/OS notices' if name.startswith('nrw') else 'See named rights/primary documentation'))}
  receipts.append(receipt)
 for site,tile in [('tryfan','N51W006'),('riffelhorn','N45E006')]:
  path=root/(site+'-worldcover.tif')
  url=f'https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
  if not path.exists():
   bounds=transform_bounds(plan['sites'][site]['crs'],'EPSG:4326',*plan['sites'][site]['bounds'],densify_pts=40)
   with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='25',GDAL_HTTP_MAX_RETRY='1',VSI_CACHE=False):
    with rasterio.open('/vsicurl/'+url) as src:
     w=from_bounds(*bounds,src.transform)
     w=Window(math.floor(w.col_off),math.floor(w.row_off),int(w.width)+2,int(w.height)+2)
     data=src.read(1,window=w);tr=src.window_transform(w)
     profile=src.profile;profile.update(width=data.shape[1],height=data.shape[0],transform=tr,tiled=False,compress='LZW')
     with rasterio.open(path,'w',**profile) as dest:dest.write(data,1)
     save(root/(site+'-worldcover-window.json'),{'url':url,'sourceCrs':str(src.crs),'sourceShape':list(src.shape),'sourceTransform':list(src.transform),'window':[w.col_off,w.row_off,w.width,w.height],'windowTransform':list(tr)})
  with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=25,context=TLS) as r:headers={k:r.headers.get(k) for k in ['ETag','Last-Modified','Content-Length']}
  receipts.append({'file':path.name,'bytes':path.stat().st_size,'sha256':sha(path),'url':url,'parentHeadersCheckedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parentHeaders':headers,'subsetDefinition':json.loads((root/(site+'-worldcover-window.json')).read_text()),'licence':'CC-BY-4.0, ESA WorldCover 2021 and modified Sentinel credit','operation':'Native grid window read, no reprojection/resampling; lossless uint8 GeoTIFF re-encoding; mask is applied only in analysis.','completeParentHashKnown':False,'wireBytesKnown':False})
 save(root/'acquisition.json',{'planSha256':sha('docs/atlas/semantic-comparison-plan.json'),'files':receipts,'excess':'GLAMOS smallest published unit is the 9.79MB national inventory ZIP; only intersecting glacier/debris features enter comparison. API responses retain complete intersecting feature geometries beyond the fixed windows. WC reads native compressed COG blocks, not whole 3-degree products; transfer bytes unknown.','exclusions':'No national TLM archive, UKCEH restricted raster, imagery or elevation acquired.'})
 print('Retained source/document bytes',sum(r.get('bytes',0) for r in receipts),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args()
 plan=json.loads(Path('docs/atlas/semantic-comparison-plan.json').read_text())
 acquire(a.data,plan)
if __name__=='__main__':main()
