"""Numerical evaluation of the fixed regional prototype, separate from route analysis."""
import json
import math
from pathlib import Path
import numpy as np
from pyproj import Transformer
from riffelhorn_terrain import (AwsCache, BOUNDS, CACHE, PRODUCT, SOURCE, SIZE,
    decode, digest, inspect_sources, pixel_xy, tile_bounds, verify, resolve_storage_roots)

data=resolve_storage_roots(require_data=True).data
manifest=verify(data);source,_,_,_=inspect_sources(data)
aws=AwsCache(data/CACHE);product=data/PRODUCT
forward=Transformer.from_crs(2056,3857,always_xy=True,allow_ballpark=False)
inverse=Transformer.from_crs(3857,2056,always_xy=True,allow_ballpark=False)
tiles={}


def summary(values):
    a=np.asarray(values,dtype='float64')
    return {'count':int(a.size),'mean':float(a.mean()),'rms':float(np.sqrt(np.mean(a*a))),
        'min':float(a.min()),'max':float(a.max()),'p95abs':float(np.percentile(np.abs(a),95))}


def swiss(e,n):
    x=np.clip((np.asarray(e)-BOUNDS[0])/.5-.5,0,source.shape[1]-1)
    y=np.clip((BOUNDS[3]-np.asarray(n))/.5-.5,0,source.shape[0]-1)
    x0=np.floor(x).astype(int);y0=np.floor(y).astype(int)
    x1=np.minimum(x0+1,source.shape[1]-1);y1=np.minimum(y0+1,source.shape[0]-1)
    fx=x-x0;fy=y-y0
    return (source[y0,x0]*(1-fx)+source[y0,x1]*fx)*(1-fy)+(source[y1,x0]*(1-fx)+source[y1,x1]*fx)*fy


def resolved(z,x,y):
    key=(z,x,y)
    if key not in tiles:
        p=product/f'tiles/{z}/{x}/{y}.png'
        tiles[key]=decode(p.read_bytes()) if p.exists()else aws.at_tile(z,x,y)
    return tiles[key]


def composed(e,n,z=18):
    xx,yy=pixel_xy(e,n,z);xx,yy=np.broadcast_arrays(xx,yy)
    x0=np.floor(xx).astype(int);y0=np.floor(yy).astype(int)
    def samples(x,y):
        v=np.empty(x.shape,dtype='float64');pairs=np.stack([x//SIZE,y//SIZE],axis=-1)
        for tx,ty in np.unique(pairs.reshape(-1,2),axis=0):
            mask=(pairs[...,0]==tx)&(pairs[...,1]==ty)
            v[mask]=resolved(z,int(tx),int(ty))[y[mask]%SIZE,x[mask]%SIZE]
        return v
    fx=xx-x0;fy=yy-y0
    return (samples(x0,y0)*(1-fx)+samples(x0+1,y0)*fx)*(1-fy)+(samples(x0,y0+1)*(1-fx)+samples(x0+1,y0+1)*fx)*fy


ee,nn=np.meshgrid(np.linspace(BOUNDS[0]+50,BOUNDS[2]-50,40),np.linspace(BOUNDS[1]+50,BOUNDS[3]-50,40))
me,mn=forward.transform(ee,nn);s=swiss(ee,nn);a=aws.at_mercator(me,mn)
gradient=np.hypot((swiss(ee+1,nn)-swiss(ee-1,nn))/2,(swiss(ee,nn+1)-swiss(ee,nn-1))/2)
report={'productIdentity':manifest['identity'],'sourceMinusAwsOverlap':summary(s-a),
    'lowSlopeSubsetMinusAws':summary((s-a)[gradient<.1]),
    'interpretation':'Differences between products, not a datum transformation or accuracy score; low-slope subset is diagnostic only',
    'boundaryTransects':[],'sourceVsEncodedPixels':{},'scaleDifferences':{}}

# Check actual target pixel centres against independent source-grid bilinear sampling.
ce,cn=forward.transform(2624809.668,1092252.405);px,py=pixel_xy(ce,cn,18)
tx,ty=math.floor((px+.5)/SIZE),math.floor((py+.5)/SIZE)
b=tile_bounds(18,tx,ty);step=(b[2]-b[0])/SIZE
indices=np.arange(16,240,8);cx,cy=np.meshgrid(indices,indices)
xe,yn=b[0]+(cx+.5)*step,b[3]-(cy+.5)*step
se,sn=inverse.transform(xe,yn)
decoded=resolved(18,tx,ty)[cy,cx]
report['sourceVsEncodedPixels']={'tile':[18,tx,ty],'differences':summary(decoded-swiss(se,sn))}
for z in [14,15,16,17,18]:report['scaleDifferences'][str(z)]=summary(composed(me,mn,z)-s)

for side in ['west','east','south','north']:
    for f in [.25,.5,.75]:
        offsets=np.arange(-50,51,dtype='float64')
        if side in ['west','east']:
            e=np.full_like(offsets,BOUNDS[0]if side=='west'else BOUNDS[2])+offsets
            n=np.full_like(offsets,BOUNDS[1]+2000*f)
            inside_e=(BOUNDS[0]+.5)if side=='west'else (BOUNDS[2]-.5);inside_n=n[0]
        else:
            e=np.full_like(offsets,BOUNDS[0]+2000*f)
            n=np.full_like(offsets,BOUNDS[1]if side=='south'else BOUNDS[3])+offsets
            inside_e=e[0];inside_n=(BOUNDS[1]+.5)if side=='south'else(BOUNDS[3]-.5)
        xe,yn=forward.transform(e,n);values=composed(xe,yn)
        imx,imy=forward.transform(inside_e,inside_n)
        report['boundaryTransects'].append({'side':side,'fraction':f,'offsetMetres':offsets.tolist(),
            'composedHeights':values.tolist(),'awsHeights':aws.at_mercator(xe,yn).tolist(),
            'insideSwissMinusAws':float(swiss(inside_e,inside_n)-aws.at_mercator(imx,imy)),
            'maxAdjacent1mDifference':float(np.max(np.abs(np.diff(values))))})

# Optional retained Mapterhorn comparison: no new service traffic or terrain acquisition.
reference=Path('test-results/atlas-terrain-foundation/numeric/mapterhorn-17-68361-46641.bin')
if reference.exists():
    from PIL import Image
    from io import BytesIO
    rgb=np.asarray(Image.open(BytesIO(reference.read_bytes())).convert('RGB'),dtype='float64')
    mt=rgb[...,0]*256+rgb[...,1]+rgb[...,2]/256-32768
    assert mt.shape==(512,512)
    direct=np.block([[resolved(18,136722,93282),resolved(18,136723,93282)],
                     [resolved(18,136722,93283),resolved(18,136723,93283)]])
    report['retainedMapterhornReference']={'path':reference.as_posix(),'sha256':digest(reference),
        'tile':[17,68361,46641],'swissDirectMinusMapterhorn':summary(direct-mt),
        'limitation':'Prior live service snapshot, not independent truth or a new provider evaluation'}
else:report['retainedMapterhornReference']={'available':False}

report['awsInputs']=aws.records
out=data/'experiments/atlas/riffelhorn-regional-terrain-v1';out.mkdir(parents=True,exist_ok=True)
p=out/'numerical-evaluation.json';p.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items()if k not in ['boundaryTransects','awsInputs']},indent=2))
print('BOUNDARIES',[(v['side'],v['fraction'],round(v['insideSwissMinusAws'],3),round(v['maxAdjacent1mDifference'],3))for v in report['boundaryTransects']])
print('REPORT',str(p),digest(p))
