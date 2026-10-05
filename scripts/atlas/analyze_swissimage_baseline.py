"""Geographic source/display probes and geometric support diagnostics; no correction."""
import argparse, json, math
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image
from pyproj import Transformer
import rasterio
from rasterio.windows import from_bounds
import swissimage_baseline as s

def signal(rgb):
    a=s.linear(rgb);l=np.sum(a*np.array([.2126,.7152,.0722]),axis=-1)
    return {'samples':int(l.size),'linearLuminanceP05P50P95':np.percentile(l,[5,50,95]).tolist(),
      'linearMean':float(l.mean()),'linearStd':float(l.std()),
      'encodedLumaAtMost5Fraction':float(np.mean(np.sum(rgb*np.array([.2126,.7152,.0722]),axis=-1)<=5)),
      'exactBlackFraction':float(np.mean(np.all(rgb==0,axis=-1)))}

@lru_cache(maxsize=64)
def tile(root,z,x,y):
    p=Path(root)/f'tiles/{z}/{x}/{y}.png'
    return np.asarray(Image.open(p)) if p.exists() else None

def sample(root,z,merc):
    px=(merc[0]+s.WORLD/2)/s.WORLD*2**z*s.SIZE-.5
    py=(s.WORLD/2-merc[1])/s.WORLD*2**z*s.SIZE-.5
    ix,iy=math.floor(px),math.floor(py);wx,wy=px-ix,py-iy
    out=np.zeros(4)
    for dx,dy,w in [(0,0,(1-wx)*(1-wy)),(1,0,wx*(1-wy)),(0,1,(1-wx)*wy),(1,1,wx*wy)]:
        a=tile(str(root),z,(ix+dx)//s.SIZE,(iy+dy)//s.SIZE)
        if a is not None:out+=w*a[(iy+dy)%s.SIZE,(ix+dx)%s.SIZE]
    return out

def probes(repo,data,out):
    sources=s.Sources(data,s.verify_sources(repo,data));to_geo=Transformer.from_crs(2056,4326,always_xy=True);to_merc=Transformer.from_crs(2056,3857,always_xy=True)
    report={'patches':{},'method':'Fixed native patches; colour statistics assume sRGB, not reflectance. Geometry is existing native Swiss 0.5m VRT. Stretch = sqrt(1+|gradient|^2), tangent footprint nominal0.25m*stretch; renderer exaggeration separately.', 'probes':[]}
    height=data/'derived/atlas/riffelhorn/riffelhorn-swiss-support-v1/source-mosaic.vrt'
    try:
        with rasterio.open(height) as dem:
            for name,(x,y,side) in s.PATCHES.items():
                a,tr=sources.window((x-side/2,y-side/2,x+side/2,y+side/2));rgb=s.encoded(a[:3]).transpose(1,2,0)
                Image.fromarray(rgb).save(out/f'{name}-source.png')
                h=dem.read(1,window=from_bounds(x-side/2,y-side/2,x+side/2,y+side/2,dem.transform)).astype('float64');gy,gx=np.gradient(h,.5,.5);g=np.hypot(gx,gy)
                slope=np.degrees(np.arctan(g));stretch=np.sqrt(1+g*g);display_stretch=np.sqrt(1+(1.45*g)**2)
                patch=signal(rgb);patch.update({'centreLV95':[x,y],'sideMetres':side,'slopeDegreesP05P50P95':np.percentile(slope,[5,50,95]).tolist(),
                      'surfaceAreaFactorP05P50P95':np.percentile(stretch,[5,50,95]).tolist(),
                      'nominalTangentFootprintMetresP05P50P95':np.percentile(.25*stretch,[5,50,95]).tolist(),
                      'rendererExaggeratedAreaFactorP05P50P95':np.percentile(display_stretch,[5,50,95]).tolist(),
                      'stretchAbove2Fraction':float((stretch>2).mean()),'stretchAbove5Fraction':float((stretch>5).mean())})
                lum=np.sum(s.linear(rgb)*np.array([.2126,.7152,.0722]),axis=-1)
                patch['nativeGradientEnergy']=float(np.mean(np.diff(lum,axis=0)**2)+np.mean(np.diff(lum,axis=1)**2))
                points=[]
                # Same 31x31 geographic sample lattice for every display; boundaries inset 1m.
                for j,yy in enumerate(np.linspace(y-side/2+1,y+side/2-1,31)):
                    for i,xx in enumerate(np.linspace(x-side/2+1,x+side/2-1,31)):
                        px=round((xx-tr.c)/.1-.5);py=round((tr.f-yy)/.1-.5)
                        merc=to_merc.transform(xx,yy)
                        p={'id':f'{name}-{j}-{i}','patch':name,'row':j,'column':i,'lv95':[xx,yy],'lonlat':list(to_geo.transform(xx,yy)),
                           'sourceRGB':rgb[py,px].tolist(),'preparedRGBByLevel':{str(z):sample(out,z,merc)[:3].tolist() for z in range(12,19)}}
                        report['probes'].append(p);points.append(p)
                # Recompute a bounded finest tile independently for transfer fidelity.
                merc=to_merc.transform(x,y);tx=math.floor((merc[0]+s.WORLD/2)/s.WORLD*2**18);ty=math.floor((s.WORLD/2-merc[1])/s.WORLD*2**18)
                expected=sources.finest(18,tx,ty);stored=s.read_field(out,18,tx,ty)
                patch['independentTransferMaxLinearDifference']=float(np.max(abs(expected-stored)))
                patch['finestEncodedVersusUnencodedMaxCodeDifference']=float(np.max(abs(np.asarray(Image.open(out/f'tiles/18/{tx}/{ty}.png')).astype(int)-s.rgba(expected).astype(int))))
                # Matched same-grid encoded parent signal differences are scale generalisation, not transfer error.
                patch['levelSignals']={str(z):signal(np.asarray([p['preparedRGBByLevel'][str(z)] for p in points])) for z in range(12,19)}
                report['patches'][name]=patch
    finally:sources.close()
    s.save(out/'source-diagnostics.json',report)
    s.save(out/'probe-locations.json',[{k:p[k] for k in ('id','patch','lonlat')} for p in report['probes']])
    Image.fromarray(np.zeros((s.SIZE,s.SIZE,4),dtype='uint8')).save(out/'transparent.png')

def captures(out,capture):
    src=json.loads((out/'source-diagnostics.json').read_text(encoding='utf8'));r=json.loads((capture/'capture.json').read_text(encoding='utf8'))
    index={p['id']:p for p in src['probes']};result={'scenes':[],'limits':'Map.project followed by terrain unproject checks first-visible support; <=2m horizontal roundtrip required. Nearest displayed pixel sampling, inherited atmosphere/filtering, and native-vs-render mesh differences remain. Correlation is signal retention evidence, not radiometric calibration or accuracy.'}
    for scene in r['scenes']:
        image=np.asarray(Image.open(capture/scene['filename']).convert('RGB'));patches={}
        # Select the actual visible imagery tile level where available; ordinary raster zoom otherwise.
        visible=scene['state'].get('usedImagery') or [];zoom=max((c['z'] for c in visible if c['state']=='loaded'),default=min(18,math.floor(scene['scene']['zoom'])))
        for name in s.PATCHES:
            rows=[]
            for p in scene['state']['probes']:
                if p['patch']!=name or not p['visibleScreen']:continue
                original=index[p['id']];ll=original['lonlat'];hit=p['firstSurface']
                err=math.hypot((hit[0]-ll[0])*111320*math.cos(math.radians(ll[1])),(hit[1]-ll[1])*111320)
                x,y=map(lambda a:int(round(a)),p['screen'])
                if err>2 or not 0<=x<image.shape[1] or not 0<=y<image.shape[0]:continue
                # The UI occupies the left sidebar / upper toolbar; do not mistake it for terrain signal.
                if x<410 or y<95:continue
                zz=zoom
                if scene['mode']=='regional':
                    lng,lat=ll;hits=[]
                    for c in visible:
                        z=c['z'];cx=math.floor((lng+180)/360*2**z);cy=math.floor((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)
                        if c['state']=='loaded' and c['x']==cx and c['y']==cy:hits.append(z)
                    if not hits:continue
                    zz=max(hits)
                rows.append((original,np.asarray(image[y,x]),err,x,y,zz))
            if len(rows)<10:patches[name]={'traceableSamples':len(rows),'state':'insufficient first-visible unoccluded screen support'};continue
            displayed=np.asarray([a[1] for a in rows]);prepared=np.asarray([a[0]['preparedRGBByLevel'][str(a[5])] for a in rows])
            dl=np.sum(s.linear(displayed)*np.array([.2126,.7152,.0722]),axis=-1);pl=np.sum(s.linear(prepared)*np.array([.2126,.7152,.0722]),axis=-1)
            # Geographic-lattice neighbours (same map spacing) allow a frequency comparison without comparing camera pixels to 0.1m pixels.
            lattice={(a[0]['row'],a[0]['column']):(i,a) for i,a in enumerate(rows)};changes=[]
            for (j,i),(k,a) in lattice.items():
                for key in ((j+1,i),(j,i+1)):
                    if key in lattice:changes.append(float(dl[k]-dl[lattice[key][0]]))
            patches[name]={'traceableSamples':len(rows),'sampledRegionalLevels':sorted({a[5] for a in rows}),'uniqueDisplayPixels':len({(a[3],a[4]) for a in rows}), 'display':signal(displayed),
                          'matchedPrepared':signal(prepared),'linearLuminanceCorrelation':float(np.corrcoef(dl,pl)[0,1]) if dl.std()>0 and pl.std()>0 else None,
                          'geographicGradientEnergy':float(np.mean(np.square(changes))) if changes else None,
                          'maxRoundtripMetres':max(a[2] for a in rows),'sampleRectangle':[min(a[3] for a in rows),min(a[4] for a in rows),max(a[3] for a in rows),max(a[4] for a in rows)]}
        result['scenes'].append({'mode':scene['mode'],'camera':scene['scene']['id'],'regionalLoadedZoom':zoom,'patches':patches})
    s.save(capture/'signal-diagnostics.json',result)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['probes','captures']);p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--captures',type=Path)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2]
    if a.command=='probes':probes(repo,a.data,a.out)
    else:captures(a.out,a.captures)
