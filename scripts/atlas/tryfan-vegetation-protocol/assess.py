"""Read-only vegetation protocol diagnostics. No correction model or corrected arrays."""
from pathlib import Path
import importlib.util,json,hashlib,math
from collections import deque
import numpy as np
import rasterio
from rasterio.features import shapes
from pyproj import Transformer
import shapely
from shapely.geometry import shape
from shapely.ops import transform as geom_transform,unary_union
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
DATA=ROOT.parent/'meridian-data'
OUT=ROOT/'docs/research'
PREFIX='tryfan-vegetation-protocol'
PLAN_SHA='1754a4cddc32d1b7ed76032f9009e813475c542ab0d2514f1e13596aad32394c'
spec=importlib.util.spec_from_file_location('previous',ROOT/'scripts/atlas/tryfan-illumination-normalization/experiment.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,ensure_ascii=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def quant(a):return previous.quant(np.asarray(a))
def pearson(a,b):
    return float(np.corrcoef(a,b)[0,1]) if len(a)>1 and np.std(a)>0 and np.std(b)>0 else None

def class_support(ds,code):
    native=ds.read(1)
    geoms=[shape(g) for g,v in shapes((native==code).astype('uint8'),transform=ds.transform) if v==1]
    tr=Transformer.from_crs(ds.crs,27700,always_xy=True);geometry=geom_transform(tr.transform,unary_union(geoms));op=tr.get_last_used_operation()
    return geometry,{'sourceCrs':ds.crs.to_string(),'targetCrs':'EPSG:27700','operation':op.description,'statedAccuracyMetres':op.accuracy,'notMeasuredLocalRegistrationAccuracy':True}

def guarded_support(geometry,points,distance):
    pts=shapely.points(points)
    inside=shapely.covers(geometry,pts)
    dist=shapely.distance(geometry.boundary,pts)
    # Outside is NOT evidence of a physical absence. This only defines eligibility.
    return (inside&(dist>=distance)).reshape(100,100),np.where(inside,dist,0).reshape(100,100)

def components(mask):
    seen=np.zeros_like(mask,bool);sizes=[]
    for y,x in zip(*np.nonzero(mask)):
        if seen[y,x]:continue
        seen[y,x]=True;todo=deque([(y,x)]);n=0
        while todo:
            r,c=todo.popleft();n+=1
            for rr,cc in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if 0<=rr<mask.shape[0] and 0<=cc<mask.shape[1] and mask[rr,cc] and not seen[rr,cc]:
                    seen[rr,cc]=True;todo.append((rr,cc))
        sizes.append(n)
    return sorted(sizes,reverse=True)

def train_region(fold,guard=100):
    # Fixed500m quadrants; Euclidean distance from the closed heldout square.
    rr,cc=np.indices((100,100));x=5+10*cc;y=995-10*rr
    west=500*(fold%2);south=500*(1-fold//2)
    dx=np.maximum(np.maximum(west-x,x-west-500),0)
    dy=np.maximum(np.maximum(south-y,y-south-500),0)
    return np.hypot(dx,dy)>=guard

def block_rows(mask,mu,rgb):
    rows=[]
    for r in range(10):
        for c in range(10):
            block=np.zeros_like(mask);block[r*10:r*10+10,c*10:c*10+10]=True;m=mask&block
            if m.any():rows.append({'id':f'{r}:{c}','quadrant':previous.FOLDS[(r>=5)*2+(c>=5)],'cells':int(m.sum()),'muMedian':float(np.median(mu[m])),'brightnessMedian':float(np.median((rgb@previous.WEIGHTS)[m]))})
    return rows

def support_gate(mask,mu,rgb,plan):
    g=plan['prospectiveFeasibilityGates'];minimum=plan['spatialDesign']['minimumCellsPerOccupiedBlock']
    folds=previous.fold_grid();rows=[];fail=[]
    if mask.sum()<g['minimumTotalCells']:fail.append('total cells')
    for i,name in enumerate(previous.FOLDS):
        test=mask&(folds==i);train=mask&train_region(i,plan['spatialDesign']['futureTrainGuardMetres'])
        tb=block_rows(test,mu,rgb);rb=block_rows(train,mu,rgb)
        tm=np.asarray([b['muMedian'] for b in rb if b['cells']>=minimum])
        tq=quant(mu[train]);eq=quant(mu[test])
        row={'heldout':name,'testCells':int(test.sum()),'trainCellsAfter100mGuard':int(train.sum()),'testOccupied100mBlocks':sum(b['cells']>=minimum for b in tb),'trainOccupied100mBlocks':sum(b['cells']>=minimum for b in rb),'trainingMuP05P50P95':tq,'testMuP05P50P95':eq,'trainMuSpread':tq[2]-tq[0] if tq else 0,'testMuSpread':eq[2]-eq[0] if eq else 0,'trainBlockMedianMuSpread':float(np.diff(np.percentile(tm,[5,95]))[0]) if len(tm) else 0,'testWithinTrainingP05P95Fraction':float(np.mean((mu[test]>=tq[0])&(mu[test]<=tq[2]))) if tq and test.any() else 0}
        tests=[('testCells','minimumHeldoutCellsEachQuadrant'),('trainCellsAfter100mGuard','minimumTrainingCellsAfterGuard'),('testOccupied100mBlocks','minimumHeldoutOccupiedBlocksEachQuadrant'),('trainOccupied100mBlocks','minimumTrainingOccupiedBlocksAfterGuard'),('trainMuSpread','minimumTrainingMuP95MinusP05'),('testMuSpread','minimumHeldoutMuP95MinusP05'),('trainBlockMedianMuSpread','minimumTrainingOccupiedBlockMedianMuP95MinusP05'),('testWithinTrainingP05P95Fraction','minimumHeldoutWithinTrainingP05P95Fraction')]
        row['failures']=[key for key,limit in tests if row[key]<g[limit]]
        fail += [name+': '+s for s in row['failures']];rows.append(row)
    return {'passed':not fail,'failures':fail,'folds':rows}

def lag_stats(mask,mu,rgb,distances):
    brightness=rgb@previous.WEIGHTS;rows=[]
    for distance in distances:
        n=distance//10
        for direction in ['E','N']:
            a=(slice(None),slice(None,-n)) if direction=='E' else (slice(n,None),slice(None))
            b=(slice(None),slice(n,None)) if direction=='E' else (slice(None,-n),slice(None))
            ok=mask[a]&mask[b]
            rows.append({'distanceMetres':distance,'direction':direction,'endpointPairs':int(ok.sum()),'brightnessPearson':pearson(brightness[a][ok],brightness[b][ok]),'muPearson':pearson(mu[a][ok],mu[b][ok])})
    return rows

def spectral(rgb,mask):
    a=rgb[mask];edges=[]
    for axis in [0,1]:
        l=(slice(None,-1),slice(None)) if axis==0 else (slice(None),slice(None,-1))
        r=(slice(1,None),slice(None)) if axis==0 else (slice(None),slice(1,None))
        ok=mask[l]&mask[r];v,w=rgb[l][ok],rgb[r][ok];edges.append(np.abs(v-w)/((v+w)/2))
    e=np.concatenate(edges)
    return {'RoverG':quant(a[:,0]/a[:,1]),'BoverG':quant(a[:,2]/a[:,1]),'adjacentEligibleEdges':len(e),'perBandNormalizedGradientP05P50P95':{b:quant(e[:,i]) for i,b in enumerate(previous.BANDS)},'nonfiniteValues':int((~np.isfinite(a)).sum()),'negativeValues':int((a<0).sum()),'aboveOneValues':int((a>1).sum())}

def mask_hash(mask):return hashlib.sha256(np.packbits(mask.ravel(),bitorder='little').tobytes()).hexdigest()

def run():
    if sha(HERE/'assessment-plan.json')!=PLAN_SHA:raise ValueError('Predeclared assessment plan changed')
    plan=read(HERE/'assessment-plan.json')
    protocol,meta,rgb,scl,ns,z,transform,points,basis=previous.load()
    az=protocol['sourceSun']['azimuthDegrees'];el=protocol['sourceSun']['elevationDegrees']
    sg=previous.sun(az,el,basis);mu=ns@sg;blocked,raySupport,horizon=previous.rays(z,transform,points,sg)
    positive=np.isfinite(rgb).all(axis=-1)&(rgb>0).all(axis=-1)
    base=positive&(scl==4)&(mu>=.3)&raySupport&~blocked
    with rasterio.open(DATA/meta['inputs']['scl']['path']) as ds:
        sclgeom,scloperation=class_support(ds,4);sclguard,scldist=guarded_support(sclgeom,points,20)
        tx=Transformer.from_crs(27700,ds.crs,always_xy=True);x,y=tx.transform(points[:,0],points[:,1]);inv=~ds.transform
        cols=np.floor(inv.a*x+inv.b*y+inv.c).astype(int);rows=np.floor(inv.d*x+inv.e*y+inv.f).astype(int)
        sourceSclCells=(rows*ds.width+cols).reshape(100,100)
        nativeSCL=ds.read(1)[rows,cols].reshape(100,100)
    semroot=DATA/'derived/atlas/semantic-comparison-v1';receipts=read(ROOT/'docs/atlas/semantic-comparison-sources.json');files={f['file']:f for f in receipts['files']};verified=[]
    for name in ['tryfan-worldcover.tif','nrw-vegetation-full-features.json','nrw-survey-area.json','worldcover-manual.pdf','jncc-handbook.pdf','nrw-vegetation-metadata.txt']:
        f=files.get(name) or next(f for f in receipts['extraMetadata'] if f['file']==name)
        p=semroot/name
        if sha(p)!=f['sha256']:raise ValueError('Changed retained semantic source '+name)
        verified.append({'path':str(p.relative_to(DATA)).replace(chr(92),'/'),'sha256':f['sha256'],'bytes':p.stat().st_size})
    with rasterio.open(semroot/'tryfan-worldcover.tif') as ds:
        wcgeom,wcoperation=class_support(ds,30);wcguard,wcdist=guarded_support(wcgeom,points,20)
        tx=Transformer.from_crs(27700,ds.crs,always_xy=True);x,y=tx.transform(points[:,0],points[:,1]);inv=~ds.transform
        cc=np.floor(inv.a*x+inv.b*y+inv.c).astype(int);rr=np.floor(inv.d*x+inv.e*y+inv.f).astype(int)
        if not ((cc>=0)&(cc<ds.width)&(rr>=0)&(rr<ds.height)).all():raise ValueError('Native WorldCover support missing')
        wc=ds.read(1)[rr,cc].reshape(100,100);wcCells=(rr*ds.width+cc).reshape(100,100)
    features=read(semroot/'nrw-vegetation-full-features.json')['features'];geoms=[shape(f['geometry']) for f in features];pts=shapely.points(points)
    memberships=[shapely.covers(g,pts).reshape(100,100) for g in geoms]
    heath=unary_union([g for g,f in zip(geoms,features) if f['properties']['phase1_code']=='D.1.1' and f['properties']['label']=='D.1.1' and f['properties']['mosaicpoly'] is None])
    nrwguard,nrwdist=guarded_support(heath,points,20)
    rawHeath=shapely.covers(heath,pts).reshape(100,100)
    geometricGood=positive&(mu>=.3)&raySupport&~blocked
    geometryUnion=unary_union([shape(g) for g,v in shapes(geometricGood.astype('uint8'),transform=rasterio.transform.from_origin(265900,359800,10,10)) if v==1])
    geometryDistance=shapely.distance(geometryUnion.boundary,pts).reshape(100,100)
    masks={'P1':base&sclguard,'P2':base&sclguard&wcguard,'P3':base&sclguard&wcguard&nrwguard}
    slope=np.degrees(np.arccos(ns[:,:,2]));aspect=np.mod(np.degrees(np.arctan2(ns[:,:,0],ns[:,:,1])),360)
    height=previous.aggregate(z)[previous.CORE]
    result={'revision':'tryfan-vegetation-assessment-results/v1','planSha256':sha(HERE/'assessment-plan.json'),'methodSha256':sha(__file__),'oldProtocolSha256':sha(previous.FROZEN),'metadata':meta,'semanticSources':verified,'nativeSupportTransformOperations':{'SCL':scloperation,'WorldCover':wcoperation},'numericRuntime':{'numpy':np.__version__,'rasterio':rasterio.__version__,'GDAL':rasterio.__gdal_version__,'shapely':shapely.__version__},'sourceSCLLookupMismatchCells':int((nativeSCL!=scl).sum()),'noCorrectionModelFitted':True,'correctedArraysProduced':0,'coreCells':10000,'SCL4BeforeGeometry':int((scl==4).sum()),'SCL4AfterOriginalGeometry':int(base.sum()),'constructionCounts':{'P1':int((base&sclguard).sum()),'P2WC30BeforeWCGuard':int((base&sclguard&(wc==30)).sum()),'P2AfterWCGuard':int((base&sclguard&wcguard).sum()),'P3StrictNonMosaicHeathBeforeNRWGuard':int((base&sclguard&wcguard&rawHeath).sum()),'P3AfterNRWGuard':int((base&sclguard&wcguard&nrwguard).sum())},'maskCountsOverlapping':{'invalidRGB':int((~positive).sum()),'notSCL4':int((scl!=4).sum()),'muBelow0point3':int((mu<.3).sum()),'incompleteRay':int((~raySupport).sum()),'modelBlockedWithin1km':int(blocked.sum())},'oldGateReproduced':previous.gate(mu,positive&np.isin(scl,[4,5])&(mu>=.3)&raySupport&~blocked,scl,previous.fold_grid()),'candidates':{}}
    for name,mask in masks.items():
        sizes=components(mask);blocks=block_rows(mask,mu,rgb)
        nrw={};missing=mask.copy();multi=np.zeros_like(scl)
        for f,m in zip(features,memberships):
            selected=m&mask;multi+=selected;missing &=~m
            code=f['properties']['phase1_code'];nrw[code]=nrw.get(code,0)+int(selected.sum())
        nrw={k:v for k,v in sorted(nrw.items()) if v}
        subgroups={k:previous.summary(rgb,mu,mask&np.logical_or.reduce([m for f,m in zip(features,memberships) if f['properties']['phase1_code']==k])) for k in nrw}
        codes,counts=np.unique(wc[mask],return_counts=True)
        result['candidates'][name]={'cells':int(mask.sum()),'logicalMaskSha256':mask_hash(mask),'retainedNRWFeatureIDsUsed':[str(f['properties']['objectid']) for f,m in zip(features,memberships) if (m&mask).any()],'distanceToCoreOrInvalidRadiometryGeometryBoundaryP05P50P95Metres':quant(geometryDistance[mask]),'selectedAnalysisAreaM2':int(mask.sum())*100,'notPhysicalVegetationArea':True,'nativeSCLCellsUsed':len(np.unique(sourceSclCells[mask])),'nativeWorldCoverCellsUsed':len(np.unique(wcCells[mask])),'components4Connected':{'count':len(sizes),'largestCells':sizes[:10],'largestFraction':sizes[0]/sum(sizes) if sizes else 0,'sizeP05P50P95':quant(sizes)},'blocks100m':blocks,'occupiedBlocksAtLeast20Cells':sum(b['cells']>=20 for b in blocks),'slopeP05P50P95':quant(slope[mask]),'elevationP05P50P95':quant(height[mask]),'aspect45DegreeBinCounts':np.histogram(aspect[mask],bins=np.arange(0,361,45))[0].tolist(),'nativeWCCodeCounts':{str(int(c)):int(n) for c,n in zip(codes,counts)},'NRWCodeIncidenceCounts':nrw,'NRWNoReturnedSupportCells':int(missing.sum()),'NRWMultipleMembershipCells':int((multi>1).sum()),'NRWSubgroupBaseline':subgroups,'nativeSCLBoundaryDistanceP05P50P95Metres':quant(scldist[mask]),'nativeWC30BoundaryDistanceP05P50P95Metres':quant(wcdist[mask]),'historicalNRWHeathBoundaryDistanceP05P50P95Metres':quant(nrwdist[mask]),'baseline':previous.summary(rgb,mu,mask),'baselineQuadrants':{q:previous.summary(rgb,mu,mask&(previous.fold_grid()==i)) for i,q in enumerate(previous.FOLDS)},'spectral':spectral(rgb,mask),'dependence':lag_stats(mask,mu,rgb,plan['spatialDesign']['lagDistancesMetres']),'feasibility':support_gate(mask,mu,rgb,plan)}
    result['decision']='A - NOT JUSTIFIED (tested candidates and fixed heldout design)' if all(not v['feasibility']['passed'] for v in result['candidates'].values()) else 'REQUIRES explicit scientific assessment; gate pass alone is not protocol justification'
    write(OUT/(PREFIX+'-results.json'),result)
    generate(rgb,mu,masks,wc,slope,result)
    print(json.dumps({k:{'cells':v['cells'],'gate':v['feasibility']} for k,v in result['candidates'].items()},ensure_ascii=True))
    return result

def generate(rgb,mu,masks,wc,slope,result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':8,'svg.hashsalt':'tryfan-vegetation-v1'})
    extent=[265900,266900,358800,359800]
    fig,axes=plt.subplots(2,3,figsize=(10,7),layout='constrained')
    axes[0,0].imshow(np.clip((rgb-.02)/.28,0,1),extent=extent);axes[0,0].set_title('Uncorrected July L2A RGB\nfixed010 display transfer')
    im=axes[0,1].imshow(mu,extent=extent,vmin=0,vmax=1,cmap='viridis');fig.colorbar(im,ax=axes[0,1],label='Conditional mean-Sun incidence mu');axes[0,1].set_title('10m aggregated terrain normals')
    from matplotlib.colors import ListedColormap,BoundaryNorm
    colors={0:'#ffffff',10:'#006400',20:'#ffbb22',30:'#ffff4c',40:'#f096ff',50:'#fa0000',60:'#b4b4b4',70:'#f0f0f0',80:'#0064c8',90:'#0096a0',95:'#00cf75',100:'#fae6a0'}
    codes=sorted(int(c) for c in np.unique(wc));mapped=np.zeros_like(wc)
    for i,c in enumerate(codes):mapped[wc==c]=i
    im=axes[0,2].imshow(mapped,extent=extent,cmap=ListedColormap([colors[c] for c in codes]),norm=BoundaryNorm(np.arange(len(codes)+1)-.5,len(codes)))
    fig.colorbar(im,ax=axes[0,2],ticks=range(len(codes))).ax.set_yticklabels([str(c) for c in codes]);axes[0,2].set_title('Native WC2021 codes\n30=grassland (dated)')
    for ax,(name,mask) in zip(axes[1],masks.items()):
        ax.imshow(mask,extent=extent,vmin=0,vmax=1,cmap='Greens');ax.set_title(name+f": {int(mask.sum())} cells; no correction")
    for ax in axes.ravel():
        ax.set_xlabel('EPSG27700 east/m');ax.set_ylabel('north/m')
        for x in np.arange(266000,266900,100):ax.axvline(x,c='grey',lw=.3,alpha=.4)
        for y in np.arange(358900,359800,100):ax.axhline(y,c='grey',lw=.3,alpha=.4)
        ax.axvline(266400,c='red',lw=.7);ax.axhline(359300,c='red',lw=.7)
    fig.savefig(OUT/(PREFIX+'-populations.png'),dpi=140,metadata={'Software':'Meridian retained vegetation diagnostics'});plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(10,6),layout='constrained')
    for i,(name,mask) in enumerate(masks.items()):
        axes[0,i].hist(mu[mask],bins=np.linspace(.3,1,15));axes[0,i].set_title(name+' incidence distribution');axes[0,i].set_xlim(.3,1);axes[0,i].set_xlabel('mu');axes[0,i].set_ylabel('Selected10m cells')
        for direction in ['E','N']:
            rows=[r for r in result['candidates'][name]['dependence'] if r['direction']==direction];axes[1,i].plot([r['distanceMetres'] for r in rows],[r['brightnessPearson'] for r in rows],marker='o',label=direction)
        axes[1,i].set_title('Uncorrected brightness endpoint Pearson\nP3 sparse long-lag pairs are unreliable',fontsize=8);axes[1,i].set_xlabel('Separation/metres');axes[1,i].set_ylabel('Descriptive Pearson; not effectiveN');axes[1,i].set_ylim(-1,1);axes[1,i].set_xlim(0,310);axes[1,i].legend()
    fig.savefig(OUT/(PREFIX+'-support.png'),dpi=140,metadata={'Software':'Meridian retained vegetation diagnostics'});plt.close(fig)

if __name__=='__main__':run()
