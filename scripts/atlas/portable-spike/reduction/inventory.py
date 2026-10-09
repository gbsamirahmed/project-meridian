"""Read-only source-grid, rights and dependency inventory; stdout metadata only."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
from shared import SharedProjection
import numpy
import pyproj
import rasterio
import shapely
from rasterio.warp import transform_bounds


def run(root):
    root=Path(root); manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    pin=next(k for k,v in manifest['pins'].items() if v['alias']=='after')
    rows=[]
    with SharedProjection(root,manifest['projectionIdentity']) as owner, owner.pin(pin) as view:
        for record in view.records.values():
            if record['representation']!='raster': continue
            body=view.pool[record['evidenceRef']]; binding=body['detail']['binding']
            name=manifest['rasterFiles'][record['identity']]
            with view.snapshot.rasters[name].open(driver='GTiff') as src:
                envelope=transform_bounds('EPSG:2056',src.crs,*manifest['core'],densify_pts=128)
                c0,r0=(~src.transform)*(envelope[0],envelope[3]); c1,r1=(~src.transform)*(envelope[2],envelope[1])
                left,top=max(0,math.floor(c0)),max(0,math.floor(r0))
                right,bottom=min(src.width,math.ceil(c1)),min(src.height,math.ceil(r1))
                rows.append({'identity':record['identity'],'member':name,'seal':manifest['files'][name],
                    'family':record['family'],'native':binding['native'],'qualification':body['qualification'],
                    'temporal':record['temporal'],'source':binding['sourceRecord'],'input':binding['input'],
                    'preparationRevision':body['preparationRevision'],'rightsRef':record['rightsRef'],
                    'rights':view.pool[record['rightsRef']], 'compression':str(src.compression),
                    'blockShapes':src.block_shapes,'overviews':src.overviews(1),'imageStructure':src.tags(ns='IMAGE_STRUCTURE'),
                    'coreEnvelopeWindowEstimate':[left,top,right-left,bottom-top],
                    'estimateMeaning':'128-segment transformed core envelope; inventory estimate, not whole-profile crop completeness proof'})
        members=[{'name':name,**seal} for name,seal in manifest['files'].items()]
        versions={n:importlib.metadata.version(n) for n in ['numpy','rasterio','shapely','pyproj']}
        licences={n:{k:importlib.metadata.metadata(n).get(k) for k in ['License','License-Expression']} for n in versions}
        return {'schema':'atlas-projection-resource-inventory/v1','projectionIdentity':manifest['projectionIdentity'],
            'preparedRevision':manifest['preparedRevision'],'core':manifest['core'],'pins':manifest['pins'],
            'memberBytes':sum(s['bytes'] for s in manifest['files'].values())+(root/'manifest.json').stat().st_size,
            'rasterBytes':sum(r['seal']['bytes'] for r in rows),'rasters':rows,'members':members,
            'dependencies':{'python':sys.version.split()[0],'platform':platform.platform(),'versions':versions,
                'gdal':rasterio.__gdal_version__,'proj':pyproj.proj_version_str,'geos':shapely.geos_version_string,'installedLicenceMetadata':licences},
            'manifestSha256':hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--projection',required=True)
    print(json.dumps(run(parser.parse_args().projection),sort_keys=True,indent=2,ensure_ascii=False))
