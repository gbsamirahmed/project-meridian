"""Frozen retained-data residual experiment. Baseline gate precedes all fitting.
No acquisition; only new bounded research outputs, no retained-input writes.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, math
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT.parent/'meridian-data'
HERE=Path(__file__).parent
OUT=ROOT/'docs/research'
FROZEN=ROOT/'scripts/atlas/illumination-assessment/future-evaluation.json'
FROZEN_SHA='0e1b884bd64c94effffeb1cb024f01c6f385d87eda73f20fa134f0a2add5ca28'
_spec=importlib.util.spec_from_file_location('retained_illumination',ROOT/'scripts/atlas/illumination-assessment/assess.py')
old=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(old)
BANDS=['B04','B03','B02']
FOLDS=['NW','NE','SW','SE']
TRANSFORM=from_origin(264900,360800,10,10)
CORE=np.s_[100:200,100:200]
WEIGHTS=np.array([.2126,.7152,.0722])

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def quant(a):return [float(v) for v in np.percentile(a,[5,50,95])] if len(a) else None

def decode(dn):return np.where(dn==0,np.nan,dn.astype(float)*.0001-.1)
def aggregate(z):
    if z.shape!=(3000,3000):raise ValueError('Unexpected frozen terrain grid')
    return z.reshape(300,10,300,10).mean(axis=(1,3))
def fold_grid():
    r,c=np.indices((100,100));return (r>=50).astype(int)*2+(c>=50).astype(int)
def sun(az,el,basis):
    a,e=math.radians(az),math.radians(el)
    return old.grid_sun({'unitENU':[math.cos(e)*math.sin(a),math.cos(e)*math.cos(a),math.sin(e)]},*basis)

def rays(z,transform,points,sg):
    """Actual used scope: one native1m terrain ray per10m core centre,2..1000m."""
    inv=~transform;h=np.linalg.norm(sg[:2]);direction=sg[:2]/h
    d=np.arange(2,1001,dtype=float);blocked=np.zeros(len(points),bool);supported=np.ones(len(points),bool)
    horizon=np.full(len(points),np.nan)
    for start in range(0,len(points),128):
        pts=points[start:start+128];xy=pts[:,None,:]+d[None,:,None]*direction
        cc=np.floor(inv.a*xy[:,:,0]+inv.b*xy[:,:,1]+inv.c).astype(int)
        rr=np.floor(inv.d*xy[:,:,0]+inv.e*xy[:,:,1]+inv.f).astype(int)
        bc=np.floor(inv.a*pts[:,0]+inv.b*pts[:,1]+inv.c).astype(int)
        br=np.floor(inv.d*pts[:,0]+inv.e*pts[:,1]+inv.f).astype(int)
        inside=(cc>=0)&(rr>=0)&(cc<z.shape[1])&(rr<z.shape[0])
        heights=z[np.clip(rr,0,z.shape[0]-1),np.clip(cc,0,z.shape[1]-1)]
        base=z[br,bc]
        support=np.all(inside&np.isfinite(heights)&(heights!=-9999),axis=1)&np.isfinite(base)&(base!=-9999)
        excess=(heights-base[:,None])/d[None,:]
        blocked[start:start+len(pts)]=np.any(excess>sg[2]/h,axis=1)&support
        supported[start:start+len(pts)]=support
        horizon[start:start+len(pts)]=np.degrees(np.arctan(np.max(excess,axis=1)))
    return blocked.reshape(100,100),supported.reshape(100,100),horizon.reshape(100,100)

def summary(rgb,mu,mask):
    a=rgb[mask];m=mu[mask]
    def metric(v):
        r=float(np.corrcoef(v,m)[0,1]) if len(v)>1 and np.std(v)>0 and np.std(m)>0 else None
        return {'pearson':r,'absPearson':abs(r) if r is not None else None,'std':float(np.std(v)) if len(v) else None,'p05p50p95':quant(v)}
    return {'cells':int(mask.sum()),'muP05P50P95':quant(m),'brightness':metric(a@WEIGHTS),'bands':{b:metric(a[:,i]) for i,b in enumerate(BANDS)}}

def gate(mu,eligible,scl,folds):
    rows=[];failures=[]
    for cls in [4,5]:
        allm=eligible&(scl==cls);total=int(allm.sum())
        if total<100:failures.append(f'SCL{cls} overall {total}<100')
        for i,name in enumerate(FOLDS):
            test=allm&(folds==i);train=allm&(folds!=i)
            spread=float(np.diff(np.percentile(mu[train],[5,95]))[0]) if train.sum() else 0.
            rows.append({'SCL':cls,'heldout':name,'totalEligible':total,'heldoutCells':int(test.sum()),'trainingCells':int(train.sum()),'trainingMuP95MinusP05':spread})
            if test.sum()<20:failures.append(f'SCL{cls} {name} heldout {int(test.sum())}<20')
            if spread<.2:failures.append(f'SCL{cls} {name} training mu spread {spread:.12f}<0.2')
    return {'passed':not failures,'folds':rows,'failures':failures}

def texture(rgb,eligible,scl,folds):
    stats={}
    for cls in [4,5]:
        per=[]
        for axis in [0,1]:
            left=(slice(None,-1),slice(None)) if axis==0 else (slice(None),slice(None,-1))
            right=(slice(1,None),slice(None)) if axis==0 else (slice(None),slice(1,None))
            ok=eligible[left]&eligible[right]&(scl[left]==cls)&(scl[right]==cls)&(folds[left]==folds[right])
            a,b=rgb[left][ok],rgb[right][ok];per.append(np.abs(a-b)/((a+b)/2))
        edges=np.concatenate(per,axis=0)
        stats[str(cls)]={'edges':len(edges),'perBandNormalizedGradientP05P50P95':{b:quant(edges[:,i]) for i,b in enumerate(BANDS)}}
    return stats

def load():
    if sha(FROZEN)!=FROZEN_SHA:raise ValueError('Frozen entry criteria changed')
    protocol=read(FROZEN);receipt=DATA/'earth-lab/tryfan-005c/sentinel2-temporal-evidence/lab005c-report.json'
    if sha(receipt)!='06fe074eb64ad1fa675467a572c506e50d040429214a7d3acee8258c955d3fa8':raise ValueError('Changed temporal receipt')
    entries=[f for f in read(receipt)['input_files'] if f['season']=='summer' and f['band'] in ['red','green','blue','scl']]
    source={};grids={};arrays={}
    for f in entries:
        path=Path(f['path'])
        if sha(path)!=f['sha256']:raise ValueError('Changed retained raster')
        key=f['band'];source[key]={'path':str(path.relative_to(DATA)).replace(chr(92),'/'),'sha256':f['sha256'],'bytes':path.stat().st_size}
        with rasterio.open(path) as ds:
            grids[key]={'crs':ds.crs.to_string(),'shape':[ds.height,ds.width],'transform':list(ds.transform)[:6],'nodata':ds.nodata}
            native=ds.read(1);dest=np.full((300,300),np.nan if key!='scl' else 0,dtype=float)
            reproject(decode(native) if key!='scl' else native,dest,src_transform=ds.transform,src_crs=ds.crs,src_nodata=np.nan if key!='scl' else 0,dst_transform=TRANSFORM,dst_crs='EPSG:27700',dst_nodata=np.nan if key!='scl' else 0,resampling=Resampling.bilinear if key!='scl' else Resampling.nearest,num_threads=1)
            arrays[key]=dest[CORE]
    path=DATA/'sources/atlas/tryfan/welsh-lidar-1m/rasters/tryfan-004-dtm-1m.tif'
    if sha(path)!=protocol['terrainSourceSha256']:raise ValueError('Changed retained terrain')
    with rasterio.open(path) as ds:
        z=ds.read(1);transform=ds.transform
        if ds.crs.to_epsg()!=27700 or z.shape!=(3000,3000) or list(ds.bounds)!=protocol['retainedFootprintEPSG27700']:raise ValueError('Wrong frozen terrain support')
        if np.any(z==-9999) or not np.isfinite(z).all():raise ValueError('Incomplete retained terrain')
    ns=old.normals(aggregate(z),10)[CORE]
    lon,lat=Transformer.from_crs(27700,4326,always_xy=True).transform(266400,359300)
    basis=old.grid_basis(lon,lat,27700)
    rr,cc=np.indices((100,100));points=np.stack((265905+cc*10,359795-rr*10),axis=-1).reshape(-1,2)
    rgb=np.stack([arrays[k] for k in ['red','green','blue']],axis=-1);scl=arrays['scl'].astype(int)
    meta={'protocolSha256':sha(FROZEN),'implementationPlanSha256':sha(HERE/'execution-plan.json'),'methodSha256':sha(__file__),'sharedGeometryMethodSha256':sha(ROOT/'scripts/atlas/illumination-assessment/assess.py'),'inputs':source,'nativeGrids':grids,'terrain':{'path':str(path.relative_to(DATA)).replace(chr(92),'/'),'sha256':sha(path),'bytes':path.stat().st_size,'actualReadBoundsEPSG27700':protocol['retainedFootprintEPSG27700'],'normalAnalysisGridMetres':10,'rayNativeSamplingMetres':1,'rayRadiusMetres':1000},'retainedMetadataSha256':{p:sha(ROOT/p) for p in ['docs/earth-lab/tryfan-005c-temporal-evidence.json','docs/earth-lab/tryfan-010-observed-natural-colour.json','docs/atlas/tryfan-second-region-proof.json']},'core':protocol['evaluationCoreEPSG27700'],'sourceSun':protocol['sourceSun'],'reconstructedSunAtCore':{'official':old.solar('2026-07-12T11:33:31.024Z',lon,lat),'granule':old.solar('2026-07-12T11:36:51.535Z',lon,lat),'notPixelTimeBounds':True},'basisTrueEastBNG':basis[0].tolist(),'basisTrueNorthBNG':basis[1].tolist(),'SCLCounts':{str(i):int((scl==i).sum()) for i in np.unique(scl)},'slopeDegreesP05P50P95':quant(np.degrees(np.arccos(ns[:,:,2])).ravel())}
    return protocol,meta,rgb,scl,ns,z,transform,points,basis

def baseline():
    protocol,meta,rgb,scl,ns,z,transform,points,basis=load()
    az=protocol['sourceSun']['azimuthDegrees'];el=protocol['sourceSun']['elevationDegrees'];folds=fold_grid()
    sg=sun(az,el,basis);mu=ns@sg
    blocked,support,horizon=rays(z,transform,points,sg)
    positive=np.isfinite(rgb).all(axis=-1)&(rgb>0).all(axis=-1)
    eligible=positive&np.isin(scl,[4,5])&(mu>=.3)&support&~blocked
    result={'revision':'tryfan-residual-baseline/v1','metadata':meta,'cells':10000,'maskCountsOverlapping':{'nonpositiveOrInvalidRGB':int((~positive).sum()),'excludedSCL':int((~np.isin(scl,[4,5])).sum()),'incidenceBelow0point3':int((mu<.3).sum()),'incompleteRay':int((~support).sum()),'modelBlockedWithin1km':int(blocked.sum()),'eligible':int(eligible.sum()),'excluded':int((~eligible).sum())},'gate':gate(mu,eligible,scl,folds),'strata':{str(c):{'whole':summary(rgb,mu,eligible&(scl==c)),'folds':{name:summary(rgb,mu,eligible&(scl==c)&(folds==i)) for i,name in enumerate(FOLDS)}} for c in [4,5]},'baselineTexture':texture(rgb,eligible,scl,folds),'baselineRatios':{str(c):{'RoverG':quant((rgb[:,:,0]/rgb[:,:,1])[eligible&(scl==c)]),'BoverG':quant((rgb[:,:,2]/rgb[:,:,1])[eligible&(scl==c)])} for c in [4,5]},'numericCounts':{'nonfiniteValues':int((~np.isfinite(rgb)).sum()),'negativeValues':int((rgb<0).sum()),'aboveOneValues':int((rgb>1).sum())},'baselineOnly':True,'noFittingYet':True,'rayVisibilityBeyond1km':'UNKNOWN','nonTerrainOccluders':'UNKNOWN'}
    write(OUT/'tryfan-illumination-normalization-baseline.json',result)
    return result,(rgb,scl,mu,eligible,blocked,horizon)

def run():
    result,arrays=baseline()
    # Gate is a whole-design prerequisite. Never drop a stratum/fold or weaken minimums.
    if result['gate']['passed']:
        raise RuntimeError('This stopped-experiment implementation has no correction path; a new authorization is required')
    logical={'revision':'tryfan-residual-normalization-stopped/v1','decision':'D - INCONCLUSIVE (predeclared insufficient-evidence stop)', 'baselineSha256':sha(OUT/'tryfan-illumination-normalization-baseline.json'),'gateFailures':result['gate']['failures'],'fittedModels':0,'correctedCells':0,'correctedRepresentationPublished':False,'sensitivity':'NOT RUN; nominal design failed before fitting','heldoutNormalizationBenefit':'NOT EVALUABLE','informationPreservationAfterCorrection':'NOT EVALUABLE','spectralDamageAfterCorrection':'NOT EVALUABLE','originalInputsUnmodified':True,'protocolSha256':sha(FROZEN),'implementationPlanSha256':sha(HERE/'execution-plan.json'),'methodSha256':sha(__file__)}
    write(OUT/'tryfan-illumination-normalization-results.json',logical)
    return result,logical,arrays

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--baseline',action='store_true');args=a.parse_args()
    if args.baseline:
        result,arrays=baseline();print(json.dumps({'gate':result['gate'],'masks':result['maskCountsOverlapping']}))
    else:
        result,logical,arrays=run()
        import visuals
        visuals.generate(arrays,result)
        print(json.dumps(logical))
