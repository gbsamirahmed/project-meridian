"""Deterministic lossless window builder; accepted projection only, no fixture answers."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
from window import Snapshot, WindowSnapshot, SCHEMA, BASE, SOURCE, SOURCE_NAME, PROCESSING, identity, bounded_bytes, MAX_BYTES, require
from closure import derive,WINDOW
import rasterio
from rasterio.windows import Window


def build(source,output):
    source=Path(source).resolve();output=Path(output).absolute()
    repo=Path(__file__).resolve().parents[4];data=repo.parent/'meridian-data'
    require(not output.exists() and not any(output==p or p in output.parents for p in [repo,data,source]),'projection-output','Use a new owned external output, outside authoritative directories.')
    proof=derive();start=time.perf_counter()
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='window-candidate-',dir=output.parent))
    snapshot=Snapshot(source,BASE)
    try:
        original=snapshot.manifest
        for name,seal in original['files'].items():
            if name==SOURCE_NAME:continue
            (stage/name).write_bytes(bounded_bytes(source/name,MAX_BYTES,seal))
        native=None
        for d in snapshot.generations.values():
            for r in d['answer']['results']:
                if r['identity']=='dsm:'+SOURCE:native=d['answer']['documents'][r['evidenceRef']]['detail']['binding']['native']
        with snapshot.rasters[SOURCE_NAME].open(driver='GTiff') as src:
            pixels=src.read(1,window=Window(*WINDOW));profile=src.profile.copy()
            profile.update(width=WINDOW[2],height=WINDOW[3],transform=src.window_transform(Window(*WINDOW)),
                           tiled=True,blockxsize=256,blockysize=256,compress='DEFLATE',predictor=3,num_threads=1)
            temp=stage/'crop.tmp'
            with rasterio.open(temp,'w',**profile) as dst:
                dst.write(pixels,1);dst.update_tags(AREA_OR_POINT='Point')
        raw=temp.read_bytes();seal={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()};name=seal['sha256']+'.tif'
        os.rename(temp,stage/name)
        with rasterio.open(stage/name) as check:
            require(check.read(1).tobytes()==pixels.tobytes(),'projection-integrity','Extracted pixel bits changed.')
            stored={'shape':list(check.shape),'transform':list(check.transform),'crs':str(check.crs),'dtype':check.dtypes[0],'nodata':check.nodata}
        outer={'schema':SCHEMA,'profile':original['profile'],'sourceProjection':original,'pins':original['pins'],
               'files':{**{k:v for k,v in original['files'].items() if k!=SOURCE_NAME},name:seal},
               'window':{'sourceIdentity':'dsm:'+SOURCE,'sourceMember':SOURCE_NAME,'sourceSeal':original['files'][SOURCE_NAME],
                         'sourceNative':native,'sourceWindow':WINDOW,'storedMember':name,'pixelSha256':hashlib.sha256(pixels.astype('<f4',copy=False).tobytes()).hexdigest(),'pixelEncoding':'IEEE754-binary32-le-row-major/v1','storedNative':stored,'processing':PROCESSING,'closure':proof}}
        outer['projectionIdentity']=identity(outer)
        (stage/'manifest.json').write_text(json.dumps(outer,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        verified=WindowSnapshot(stage,outer['projectionIdentity']);verified.close()
        os.rename(stage,output)
        return {'projectionIdentity':outer['projectionIdentity'],'bytes':sum(p.stat().st_size for p in output.iterdir()),
                'dsmBytes':seal['bytes'],'sourceWindow':WINDOW,'buildMs':(time.perf_counter()-start)*1000}
    finally:snapshot.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps(build(a.source,a.output),sort_keys=True))
