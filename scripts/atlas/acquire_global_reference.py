"""One bounded reference/overlap input selection; never imported by the app."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from urllib.request import Request, urlopen
import rasterio
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
import riffelhorn_support as support
import riffelhorn_terrain as terrain

ROOT = 'sources/atlas/riffelhorn/global-reference-assessment-v1'
REPO = Path(__file__).resolve().parents[2]
ASSETS = {
    **{f'cop{n}': f'https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N{n}_00_E007_00_DEM/Copernicus_DSM_COG_10_N{n}_00_E007_00_DEM.tif' for n in [45,46]},
    **{f'sgi{year}': f'https://doi.glamos.ch/data/inventory/inventory_sgi{year}_r{release}.zip' for year,release in [(1973,1976),(2016,2020),(2023,2026)]},
    'ln02-grid':'https://cdn.proj.org/ch_swisstopo_chgeo2004_ETRS89_LN02.tif',
    'egm2008-grid':'https://cdn.proj.org/us_nga_egm08_25.tif',
    'cop-readme':'https://copernicus-dem-30m.s3.amazonaws.com/readme.html',
    'cop-registry':'https://registry.opendata.aws/copernicus-dem/',
    'cop-handbook':'https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf',
    'cop-licence':'https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf',
    'swiss-grid-readme':'https://cdn.proj.org/ch_swisstopo_README.txt',
    'nga-grid-readme':'https://cdn.proj.org/us_nga_README.txt',
    'joerd-sources':'https://raw.githubusercontent.com/tilezen/joerd/master/docs/data-sources.md',
    'joerd-formats':'https://raw.githubusercontent.com/tilezen/joerd/master/docs/formats.md',
    'joerd-attribution':'https://raw.githubusercontent.com/tilezen/joerd/master/docs/attribution.md',
    'cop-tile-list':'https://copernicus-dem-30m.s3.amazonaws.com/tileList.txt',
}
WORLDCOVER='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N45E006_Map.tif'


def acquire(data):
    base=data/ROOT
    base.mkdir(parents=True,exist_ok=True)

    def download(item):
        key,url=item
        filename=url.split('/')[-1] or 'index.html'
        path=base/key/filename
        receipt=base/key/'receipt.json'
        if path.exists():
            record=json.loads(receipt.read_text(encoding='utf8'))
            if terrain.digest(path)!=record['sha256']:raise ValueError('Frozen input changed: '+key)
            return key,record
        path.parent.mkdir(parents=True,exist_ok=True)
        part=path.with_suffix(path.suffix+'.part')
        with urlopen(Request(url,headers={'User-Agent':'Meridian-bounded-terrain-reference-assessment'}),timeout=90)as response:
            headers=dict(response.headers)
            with part.open('wb')as output:
                while body:=response.read(1024*1024):output.write(body)
        part.replace(path)
        # Single-part S3 ETags additionally attest these complete COG files.
        etag=headers.get('ETag',headers.get('Etag','')).strip('"')
        if key.startswith('cop')and path.suffix=='.tif'and len(etag)==32:
            if hashlib.md5(path.read_bytes()).hexdigest()!=etag:raise ValueError('Provider ETag mismatch')
        record={'url':url,'path':path.relative_to(data).as_posix(),'sha256':terrain.digest(path),'bytes':path.stat().st_size,'acquiredAt':datetime.now(timezone.utc).isoformat(),'headers':headers}
        support.save(receipt,record)
        print('ACQUIRED',key,record['bytes'],flush=True)
        return key,record

    with ThreadPoolExecutor(max_workers=2)as pool:assets=dict(pool.map(download,ASSETS.items()))
    wc=base/'worldcover'/'riffelhorn-window.tif'
    wc_record=base/'worldcover'/'receipt.json'
    if not wc.exists():
        wc.parent.mkdir(parents=True,exist_ok=True)
        with urlopen(Request(WORLDCOVER,method='HEAD'),timeout=60)as response:headers=dict(response.headers)
        bounds=transform_bounds(2056,4326,*support.BOUNDS,densify_pts=41)
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_MULTIRANGE='SERIAL'),rasterio.open('/vsicurl/'+WORLDCOVER)as ds:
            w=from_bounds(*bounds,transform=ds.transform)
            window=Window(int(w.col_off)-5,int(w.row_off)-5,int(w.width)+12,int(w.height)+12)
            classes=ds.read(1,window=window)
            profile=ds.profile.copy();profile.update(width=window.width,height=window.height,transform=ds.window_transform(window),compress='deflate')
            with rasterio.open(wc,'w',**profile)as output:output.write(classes,1)
            record={'url':WORLDCOVER,'path':wc.relative_to(data).as_posix(),'sha256':terrain.digest(wc),'bytes':wc.stat().st_size,'acquiredAt':datetime.now(timezone.utc).isoformat(),'headers':headers,'window':[window.col_off,window.row_off,window.width,window.height],'upstreamFullAssetSha256':'unknown: bounded HTTP range selection; retained ETag identifies remote object','format':'Source categorical pixels copied without class resampling'}
        support.save(wc_record,record)
    assets['worldcover']=json.loads(wc_record.read_text(encoding='utf8'))
    if terrain.digest(wc)!=assets['worldcover']['sha256']:raise ValueError('WorldCover selection changed')
    for key in ['cop45','cop46']:
        with rasterio.open(data/assets[key]['path'])as ds:
            assets[key]['raster']={'shape':list(ds.shape),'crs':str(ds.crs),'transform':list(ds.transform)[:6],'nodata':ds.nodata,'tags':ds.tags(),'overviews':ds.overviews(1)}
    record={'version':'global-reference-assessment-v1','assets':assets,'protocolSha256':terrain.digest(REPO/'docs/atlas/global-reference-protocol.json')}
    record['identity']=terrain.stable_id(record)
    support.save(base/'acquisition.json',record)
    support.save(REPO/'docs/atlas/global-reference-acquisition.json',record)
    print('INPUT IDENTITY',record['identity'],flush=True)


if __name__=='__main__':
    acquire(terrain.resolve_storage_roots(require_data=True).data)
