"""Offline retained-input adapter. No networking, source writes or product regeneration."""
import argparse, hashlib, io, json, math, sys, time
from pathlib import Path
import numpy as np
import pyproj
from PIL import Image

# Reproduction must use installed CRS resources; never acquire grids implicitly.
pyproj.network.set_network_enabled(False)

REPO=Path(__file__).resolve().parents[3]
PLAN=REPO/'docs/research/tryfan-qualified-query-plan.json'
PRODUCT=REPO/'src/atlas/terrain/metadata/tryfanProductRecord.json'
R=6378137.0

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def stable(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def geometry():
    plan=json.loads(PLAN.read_text());t=pyproj.Transformer.from_crs(27700,4326,always_xy=True)
    probes=[]
    for probe in plan['probes']:
        x,y=probe['centre'];h=plan['selection']['eligibilityReadHalfWidthM']
        ring=[]
        corners=[(x-h,y-h),(x+h,y-h),(x+h,y+h),(x-h,y+h),(x-h,y-h)]
        for a,b in zip(corners,corners[1:]):
            for f in np.linspace(0,1,9)[:-1]:ring.append(list(t.transform(a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1]))))
        ring.append(ring[0]);probes.append({**probe,'longitudeLatitude':list(t.transform(x,y)),
            'eligibilityFootprint':{'kind':'geojson','geometry':{'type':'Polygon','coordinates':[ring]}}})
    return {'planSha256':digest(PLAN),'probes':probes,'projection':{'pyproj':pyproj.__version__,'PROJ':pyproj.proj_version_str,'operation':t.description,'declaredAccuracyM':t.accuracy,'limits':'2D horizontal transformation only; no vertical harmonisation.'}}

def samples(data,requests):
    start=time.perf_counter();record=json.loads(PRODUCT.read_text())
    product=data/'derived/atlas/tryfan/tryfan-welsh-regional-v2'
    manifest=product/'manifest.json'
    if digest(manifest)!=record['manifestSha256']:raise ValueError('Frozen Welsh product manifest drift')
    inventory=json.loads(manifest.read_text())
    if inventory['identity']!=record['identity']:raise ValueError('Frozen Welsh product revision drift')
    files={v['path']:v for v in inventory['files']}
    source=data/record['source']['path']
    if digest(source)!=record['source']['sha256']:raise ValueError('Retained Welsh source changed')
    forward=pyproj.Transformer.from_crs(27700,3857,always_xy=True)
    inverse=pyproj.Transformer.from_crs(3857,27700,always_xy=True)
    plan=json.loads(PLAN.read_text());spacing=plan['derivation']['gridSpacingM']
    roots=[];checked={};read_bytes=0
    for request in requests:
        probe=next(p for p in plan['probes'] if p['id']==request['probe'])
        z=int(request['level'][1:]);family=request['family'];n=256*2**z;step=2*math.pi*R/n
        cache={};used=set();assets={}
        def pixel(ix,iy):
            nonlocal read_bytes
            tx,ty=ix//256,iy//256;key=f'{z}/{tx}/{ty}.png'
            path=(product/'tiles'/key) if family=='welsh-regional' else data/'cache/atlas/tryfan/second-region-proof/aws'/key
            if not path.is_file():raise FileNotFoundError('Required retained tile unavailable; acquisition prohibited: '+str(path))
            relative=path.relative_to(data).as_posix()
            if key not in cache:
                body=path.read_bytes();h=hashlib.sha256(body).hexdigest()
                if family=='welsh-regional' and h!=files['tiles/'+key]['sha256']:raise ValueError('Welsh tile drift: '+key)
                if relative in checked and checked[relative]!=h:raise ValueError('Input changed during proof')
                checked[relative]=h;read_bytes+=len(body)
                with Image.open(io.BytesIO(body)) as im:
                    if im.size!=(256,256) or im.mode!='RGB':raise ValueError('Unexpected retained Terrarium tile format')
                    a=np.asarray(im,dtype=np.float64)
                cache[key]=a[:,:,0]*256+a[:,:,1]+a[:,:,2]/256-32768
                assets[relative]={'href':'meridian-data://'+relative,'sha256':h,'bytes':len(body)}
            used.add((ix,iy));return float(cache[key][iy%256,ix%256])
        heights=[]
        # North-first rows; BNG grid spacing defines analysis grain, not source resolution.
        for oy in [spacing,0,-spacing]:
            row=[]
            for ox in [-spacing,0,spacing]:
                mx,my=forward.transform(probe['centre'][0]+ox,probe['centre'][1]+oy)
                px=(mx+math.pi*R)/step-.5;py=(math.pi*R-my)/step-.5
                ix,iy=math.floor(px),math.floor(py);fx,fy=px-ix,py-iy
                row.append((1-fy)*((1-fx)*pixel(ix,iy)+fx*pixel(ix+1,iy))+fy*((1-fx)*pixel(ix,iy+1)+fx*pixel(ix+1,iy+1)))
            heights.append(row)
        ix0=min(x for x,y in used);ix1=max(x for x,y in used)+1
        iy0=min(y for x,y in used);iy1=max(y for x,y in used)+1
        merc=[ix0*step-math.pi*R,math.pi*R-iy1*step,ix1*step-math.pi*R,math.pi*R-iy0*step]
        xs=[];ys=[]
        for a,b in [((merc[0],merc[1]),(merc[2],merc[1])),((merc[2],merc[1]),(merc[2],merc[3])),((merc[2],merc[3]),(merc[0],merc[3])),((merc[0],merc[3]),(merc[0],merc[1]))]:
            for f in np.linspace(0,1,17):
                x,y=inverse.transform(a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1]));xs.append(x);ys.append(y)
        # Conservative numerical footprint guard, not geodetic accuracy or new observation.
        bounds=[min(xs)-.01,min(ys)-.01,max(xs)+.01,max(ys)+.01]
        if max(abs(bounds[i]-probe['centre'][i%2]) for i in range(4))>24:raise ValueError('Frozen eligibility envelope does not contain actual read cells')
        root={'id':family+':'+probe['id'],'probe':probe['id'],'family':family,'level':request['level'],
            'heightSamplesM':heights,'assets':sorted(assets.values(),key=lambda a:a['href']),
            'actualUse':{'crs':'EPSG:27700','bounds':bounds,'nativeMercatorBounds':merc,'nativePixelWindow':[ix0,iy0,ix1,iy1],
                'usedPixelCount':len(used),'meaning':'Bounding rectangle of all bilinear source-cell footprints; densified transformed boundary +0.01m numerical guard. Logical pixel use differs from whole-PNG I/O.'},
            'upstream':{'product':record['version'],'revision':record['identity'],'sourceSubsetSha256':record['source']['sha256'],'manifestSha256':record['manifestSha256']} if family=='welsh-regional' else
                {'product':'aws-terrarium','revision':{'status':'unknown','reason':'Hosted global revision, contributors, surface meaning, epoch, information resolution and datum remain unknown.'}},
            'encoding':'RGB Terrarium, h=R*256+G+B/256-32768; quantization1/256m','analysisSpacingM':spacing}
        # Local retained artifact identity, not a fabricated upstream source release.
        root['revision']=stable({'family':family,'level':root['level'],'assets':root['assets']})
        roots.append(root)
    return {'roots':roots,'sourceChecks':{'welshSourceSha256':digest(source),'manifestSha256':digest(manifest),'selectedTileHashes':checked},
            'software':{'python':sys.version.split()[0],'numpy':np.__version__,'pyproj':pyproj.__version__},
            'measurement':{'seconds':time.perf_counter()-start,'tileBytesRead':read_bytes,'uniqueTileBytes':sum(v['bytes'] for v in {a['href']:a for r in roots for a in r['assets']}.values())}}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--geometry',action='store_true');parser.add_argument('--data',type=Path)
    args=parser.parse_args()
    result=geometry() if args.geometry else samples(args.data,json.load(sys.stdin))
    print(json.dumps(result,sort_keys=True,allow_nan=False))
