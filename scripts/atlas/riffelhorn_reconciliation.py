"""Offline, bounded reconciliation diagnostics; not an Atlas runtime module.

Uses only verified retained Swiss inputs and cached AWS tiles. Never downloads.
Outputs diagnostic 2 m LV95 fields, not a web terrain pyramid or corrected DEM.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyproj import Transformer
import riffelhorn_terrain as rt

VERSION = 'riffelhorn-reconciliation-v1'
STEP = 2.0


class FrozenAws(rt.AwsCache):
    def tile(self, z, x, y):
        if not (self.root / f'{z}/{x % (2**z)}/{y}.png').exists():
            raise FileNotFoundError(f'Offline AWS input missing: {z}/{x}/{y}')
        return super().tile(z, x, y)


def stats(a):
    a = np.asarray(a, dtype=float).ravel()
    median = np.median(a)
    return {'count': int(a.size), 'mean': float(a.mean()), 'median': float(median),
            'nmad': float(1.4826*np.median(np.abs(a-median))),
            'std': float(a.std()), 'rms': float(np.sqrt(np.mean(a*a))),
            'percentiles': dict(zip(['min','p01','p05','p25','p50','p75','p95','p99','max'],
                                   map(float, np.percentile(a, [0,1,5,25,50,75,95,99,100]))))}


def gaussian(a, sigma_metres, step=STEP):
    """Separable Gaussian, truncated at 3 sigma, reflected diagnostic edges."""
    sigma = sigma_metres/step
    radius = max(1, math.ceil(3*sigma))
    x = np.arange(-radius, radius+1)
    kernel = np.exp(-.5*(x/sigma)**2); kernel /= kernel.sum()
    out = np.asarray(a, dtype=float)
    for axis in (0, 1):
        padding = [(0,0)]*2; padding[axis] = (radius,radius)
        padded = np.pad(out, padding, mode='reflect')
        n = 1 << (padded.shape[axis]+kernel.size-2).bit_length()
        shape = [1,1]; shape[axis] = n//2+1
        result = np.fft.irfft(np.fft.rfft(padded,n=n,axis=axis)*
                             np.fft.rfft(kernel,n=n).reshape(shape), n=n, axis=axis)
        select = [slice(None)]*2; select[axis] = slice(2*radius,2*radius+out.shape[axis])
        out = result[tuple(select)]
    return out


def bilinear(a, east, north, spacing=STEP):
    x = np.clip((np.asarray(east)-rt.BOUNDS[0])/spacing-.5,0,a.shape[1]-1)
    y = np.clip((rt.BOUNDS[3]-np.asarray(north))/spacing-.5,0,a.shape[0]-1)
    x,y = np.broadcast_arrays(x,y)
    x0=np.floor(x).astype(int); y0=np.floor(y).astype(int)
    x1=np.minimum(x0+1,a.shape[1]-1); y1=np.minimum(y0+1,a.shape[0]-1)
    fx=x-x0; fy=y-y0
    return (a[y0,x0]*(1-fx)+a[y0,x1]*fx)*(1-fy)+(a[y1,x0]*(1-fx)+a[y1,x1]*fx)*fy


def distance(east, north):
    e,n = np.broadcast_arrays(east,north)
    return np.maximum(0,np.minimum.reduce([e-rt.BOUNDS[0],rt.BOUNDS[2]-e,
                                          n-rt.BOUNDS[1],rt.BOUNDS[3]-n]))


def weights(dist, width):
    return np.minimum(1, dist/np.maximum(width,STEP))


def adaptive_width(difference, dist, alpha=3):
    """GRASS/Petrasova principle; explicitly NOT a port of r.patch.smooth.

    Nearest edge mismatch extrapolated inward; smooth width at sigma 30 m to
    temper corner/along-edge variability. No cap to force width into the AOI.
    Alpha bounds the D/width term only, not total slope or along-edge gradients.
    """
    h,w = difference.shape
    yy,xx=np.indices((h,w))
    side=np.argmin(np.stack([xx,w-1-xx,yy,h-1-yy]),axis=0)
    edge=np.choose(side,[difference[:,0][:,None]+np.zeros_like(difference),
                         difference[:,-1][:,None]+np.zeros_like(difference),
                         difference[0,:][None,:]+np.zeros_like(difference),
                         difference[-1,:][None,:]+np.zeros_like(difference)])
    width=gaussian(np.maximum(STEP,np.abs(edge)/math.tan(math.radians(alpha))),30)
    return width


def fit_translation(d, sx, sy):
    """Diagnostic robust gradient regression; not validated co-registration."""
    A=np.column_stack([sx.ravel(),sy.ravel(),np.ones(sx.size)])
    b=d.ravel(); c=np.linalg.lstsq(A,b,rcond=None)[0]
    for _ in range(10):
        r=b-A@c; scale=max(1e-6,1.4826*np.median(np.abs(r-np.median(r))))
        w=np.minimum(1,1.345*scale/np.maximum(np.abs(r),1e-12))
        c=np.linalg.lstsq(A*np.sqrt(w[:,None]),b*np.sqrt(w),rcond=None)[0]
    return c,stats(b-A@c)


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


def run(data):
    original=rt.verify(data)
    source,_,records,catalog_hash=rt.inspect_sources(data)
    swiss=source.reshape(1000,4,1000,4).mean(axis=(1,3),dtype=np.float64)
    e,n=np.meshgrid(rt.BOUNDS[0]+(np.arange(1000)+.5)*STEP,
                    rt.BOUNDS[3]-(np.arange(1000)+.5)*STEP)
    forward=Transformer.from_crs(2056,3857,always_xy=True,allow_ballpark=False)
    me,mn=forward.transform(e,n)
    aws=FrozenAws(data/rt.CACHE); global_dem=aws.at_mercator(me,mn)
    d=swiss-global_dem; dist=distance(e,n)
    out=data/'experiments/atlas'/VERSION
    out.mkdir(parents=True,exist_ok=True)
    low={s:gaussian(d,s) for s in (10,30,100,250)}
    sy,sx=np.gradient(gaussian(swiss,30),STEP); sy=-sy
    slope=np.hypot(sx,sy); rough=swiss-gaussian(swiss,30)
    landform=swiss-gaussian(swiss,100)
    gy,gx=np.gradient(d,STEP)
    report={'version':VERSION,'interpretation':'Product differences, not accuracy or a physical bias field',
            'analysisGrid':{'crs':'EPSG:2056','spacingMetres':STEP,'shape':[1000,1000],
                            'regionalSampling':'4x4 source area average; sub-2 m detail not evaluated',
                            'awsSampling':'cached z15 cross-tile pixel-centre bilinear'},
            'difference':stats(d),'differenceGradient':stats(np.hypot(gx,gy)),
            'frequencyDiagnostics':{},'spatialDependence':{},'relationships':{},
            'translationDiagnostics':{},'methods':{},'transects':[]}
    for s,L in low.items():
        interior=dist>=3*s
        report['frequencyDiagnostics'][str(s)]={'sigmaMetres':s,'low':stats(L),
            'high':stats(d-L),'interiorHigh':stats((d-L)[interior]),
            'lowStdRatio':float(L.std()/d.std()),
            'edgeRule':'reflection; not observations outside AOI; 3 sigma interior also reported'}
    for axis,name in ((0,'northSouth'),(1,'eastWest')):
        rows=[]
        for lag in (1,2,4,8,16,32,64,128,256):
            a=d[:-lag,:] if axis==0 else d[:,:-lag]
            b=d[lag:,:] if axis==0 else d[:,lag:]
            rows.append({'lagMetres':lag*STEP,'correlation':float(np.corrcoef(a.ravel(),b.ravel())[0,1]),
                         'semivarianceMetresSquared':float(.5*np.mean((a-b)**2))})
        report['spatialDependence'][name]=rows
    for name,v in [('elevation',swiss),('slope30m',slope),('roughness30mAbs',np.abs(rough)),('landform100m',landform)]:
        cuts=np.percentile(v,[0,20,40,60,80,100]); rows=[]
        for i in range(5):
            mask=(v>=cuts[i]) & (v<=cuts[i+1] if i==4 else v<cuts[i+1])
            rows.append({'range':[float(cuts[i]),float(cuts[i+1])],'difference':stats(d[mask])})
        report['relationships'][name]={'correlation':float(np.corrcoef(d.ravel(),v.ravel())[0,1]),'bins':rows}
    sample=np.s_[10::20,10::20]
    c,residual=fit_translation(d[sample],sx[sample],sy[sample])
    report['translationDiagnostics']['whole']={'eastNorthVerticalCoefficientsMetres':c.tolist(),'residual':residual}
    for name,sel in [('NW',np.s_[:500,:500]),('NE',np.s_[:500,500:]),('SW',np.s_[500:,:500]),('SE',np.s_[500:,500:])]:
        c,r=fit_translation(d[sel][::20,::20],sx[sel][::20,::20],sy[sel][::20,::20])
        report['translationDiagnostics'][name]={'eastNorthVerticalCoefficientsMetres':c.tolist(),'residual':r}
    report['translationDiagnostics']['caution']='No stable-terrain/epoch mask or control points; coefficients are diagnostic, not physical shifts to apply'
    # Two justified controls, not a production terrain recommendation.
    width=adaptive_width(d,dist)
    weight={'hard':np.ones_like(d),'linear250':weights(dist,250),'adaptive3deg':weights(dist,width)}
    surfaces={k:global_dem+w*d for k,w in weight.items()}
    pure=dist>=500; steep=slope>=np.percentile(slope,90)
    for name,w in weight.items():
        C=surfaces[name]; cy,cx=np.gradient(C,STEP); wy,wx=np.gradient(w,STEP)
        delta=C-swiss; hp=C-gaussian(C,10); sh=swiss-gaussian(swiss,10)
        summit=np.unravel_index(np.argmax(swiss),swiss.shape)
        report['methods'][name]={'pureRegionalFraction':float(np.mean(w==1)),
            'weight':stats(w),'modifiedRegional':stats(delta),
            'interior500mChange':stats(delta[pure]),'steepDecileChange':stats(delta[steep]),
            'detail10mInteriorRmsRatio':float(np.sqrt(np.mean(hp[pure]**2))/np.sqrt(np.mean(sh[pure]**2))),
            'detail10mInteriorCorrelation':float(np.corrcoef(hp[pure],sh[pure])[0,1]),
            'weightGradientDisagreementTerm':stats(np.abs(d)*np.hypot(wx,wy)),
            'slopeGradient':stats(np.hypot(cx,cy)),
            'regionalGridMaximum':{'coordinate':[float(e[summit]),float(n[summit])],
                'regional':float(swiss[summit]),'candidateAtSamePoint':float(C[summit]),
                'change':float(delta[summit]),'candidateMaximum':float(C.max())}}
    report['adaptiveWidthMetres']=stats(width)
    report['edgeWidthRequirementsMetres']={str(alpha):stats(np.abs(np.concatenate([d[0],d[-1],d[:,0],d[:,-1]]))/math.tan(math.radians(alpha))) for alpha in (1,3,5)}
    # Reuse native 0.5 m heights for 1 m profiles, independently of 2 m averaging.
    offsets=np.arange(-100,1001,dtype=float)
    for side in ('west','east','south','north'):
        for fraction in (.1,.25,.5,.75,.9):
            if side in ('west','east'):
                pe=rt.BOUNDS[0]+offsets if side=='west' else rt.BOUNDS[2]-offsets
                pn=np.full_like(pe,rt.BOUNDS[1]+2000*fraction)
            else:
                pn=rt.BOUNDS[1]+offsets if side=='south' else rt.BOUNDS[3]-offsets
                pe=np.full_like(pn,rt.BOUNDS[0]+2000*fraction)
            gm=aws.at_mercator(*forward.transform(pe,pn)); sm=bilinear(source,pe,pn,.5)
            localdist=distance(pe,pn); valid=offsets>=0
            ww={'hard':valid.astype(float),'linear250':weights(localdist,250),
                'adaptive3deg':weights(localdist,bilinear(width,pe,pn))}
            curves={name:gm+w*(sm-gm) for name,w in ww.items()}
            report['transects'].append({'side':side,'fraction':fraction,'sampleSpacingMetres':1.0,'offsetMeaning':'inward distance', 'offsetMetres':offsets.tolist(),
                'aws':gm.tolist(),'regionalClampedOutside':sm.tolist(),
                'methods':{name:{'heights':curve.tolist(),
                    'maxAdjacentSampleBoundaryWindow':float(np.max(np.abs(np.diff(curve[:201])))),
                    'maxAdjacentSampleWhole':float(np.max(np.abs(np.diff(curve)))),
                    'outsideChangeMax':float(np.max(np.abs(curve[~valid]-gm[~valid])))} for name,curve in curves.items()}})
    # Four corner bisectors, inward distance on both axes, same native sampling.
    for east,north in ((0,0),(0,1),(1,0),(1,1)):
        pe=(rt.BOUNDS[2]-offsets if east else rt.BOUNDS[0]+offsets)
        pn=(rt.BOUNDS[3]-offsets if north else rt.BOUNDS[1]+offsets)
        gm=aws.at_mercator(*forward.transform(pe,pn)); sm=bilinear(source,pe,pn,.5)
        dd=distance(pe,pn); valid=offsets>=0
        ww={'hard':valid.astype(float),'linear250':weights(dd,250),'adaptive3deg':weights(dd,bilinear(width,pe,pn))}
        curves={name:gm+w*(sm-gm) for name,w in ww.items()}
        report['transects'].append({'side':('N' if north else 'S')+('E' if east else 'W'),'fraction':None,
            'sampleSpacingMetres':math.sqrt(2),'offsetMeaning':'equal inward coordinate displacement on each axis; arclength = sqrt(2) * offset',
            'offsetMetres':offsets.tolist(),'aws':gm.tolist(),'regionalClampedOutside':sm.tolist(),
            'methods':{name:{'heights':v.tolist(),'maxAdjacentSampleBoundaryWindow':float(np.max(np.abs(np.diff(v[:201])))),
                'maxAdjacentSampleWhole':float(np.max(np.abs(np.diff(v)))),
                'outsideChangeMax':float(np.max(np.abs(v[~valid]-gm[~valid])))} for name,v in curves.items()}})
    # Input tile header lineage and original source-tile joins, not causal masks.
    report['awsInputs']=aws.records
    report['sourceGridJoinDiagnostics']={name:{'differenceAdjacent2m':stats(np.diff(d,axis=axis).take(499,axis=axis)),
        'regionalAdjacent2m':stats(np.diff(swiss,axis=axis).take(499,axis=axis))} for name,axis in [('east2625000',1),('north1092000',0)]}
    np.savez(out/'fields.npz',swiss=swiss,aws=global_dem,difference=d,low100=low[100],
             weight_linear250=weight['linear250'],weight_adaptive3deg=weight['adaptive3deg'],adaptive_width=width)
    extent=[2624,2626,1091,1093]
    fig,axes=plt.subplots(2,3,figsize=(14,8),layout='constrained')
    fields=[(d,'Swiss − AWS (m)',150),(low[100],'Difference: Gaussian σ100 m',150),
            (d-low[100],'Residual to σ100 m (m)',30),
            (surfaces['linear250']-swiss,'250 m feather: change to Swiss (m)',150),
            (surfaces['adaptive3deg']-swiss,'Adaptive 3°: change to Swiss (m)',150),
            (weight['adaptive3deg'],'Adaptive regional contribution',None)]
    for ax,(v,label,limit) in zip(axes.ravel(),fields):
        im=ax.imshow(v,extent=extent,cmap='RdBu_r' if limit else 'viridis',vmin=-limit if limit else 0,vmax=limit if limit else 1)
        ax.set_title(label);ax.set_xlabel('LV95 easting (km)');ax.set_ylabel('LV95 northing (km)');fig.colorbar(im,ax=ax,shrink=.75)
    fig.suptitle('Riffelhorn: diagnostic products, not an accuracy map or a datum correction')
    fig.savefig(out/'difference-and-controls.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for ax,side in zip(axes.ravel(),('west','south','east','north')):
        row=next(v for v in report['transects'] if v['side']==side and v['fraction']==.5)
        ax.plot(offsets,row['aws'],label='AWS',color='black',linestyle='--')
        for name,v in row['methods'].items():ax.plot(offsets,v['heights'],label=name)
        ax.axvline(0,color='grey');ax.set_title(side+' midpoint');ax.set_xlabel('Distance inward from AOI edge (m)');ax.set_ylabel('Elevation (m)');ax.legend(fontsize=8)
    fig.savefig(out/'profiles.png',dpi=150);plt.close(fig)
    write_json(out/'analysis.json',report)
    outputs={p.name:{'sha256':rt.digest(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'}
    manifest={'version':VERSION,'parentProductIdentity':original['identity'],
        'parentManifestSha256':rt.digest(data/rt.PRODUCT/'manifest.json'),
        'scriptSha256CanonicalLf':rt.repository_text_digest(Path(__file__)),
        'sourceCatalogSha256CanonicalLf':catalog_hash,'sourceInputs':records,
        'awsInputs':aws.records,'outputs':outputs,
        'provenance':'All candidate weights retained; no physical vertical correction; diagnostic blends have no established common height datum',
        'support':'Original 2 x 2 km rectangle only; no new acquisitions or downloads',
        'methods':{'linear250':'G + min(distance/250,1)*(S-G)',
            'adaptive3deg':'G + min(distance/width,1)*(S-G); width=sigma30m smooth(abs(nearest edge difference)/tan(3deg)), minimum 2m'},
        'runtime':{'numpy':np.__version__,'matplotlib':matplotlib.__version__}}
    manifest['identity']=rt.stable_id(manifest);write_json(out/'manifest.json',manifest)
    print(json.dumps({'output':str(out),'identity':manifest['identity'],'difference':report['difference'],
                      'methods':report['methods'],'adaptiveWidthMetres':report['adaptiveWidthMetres']},indent=2))


def verify_analysis(data):
    out=data/'experiments/atlas'/VERSION
    m=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    identity=m.pop('identity')
    if rt.stable_id(m)!=identity:raise ValueError('Analysis identity mismatch')
    if m['scriptSha256CanonicalLf']!=rt.repository_text_digest(__file__):raise ValueError('Analysis code changed; regenerate explicitly')
    for name,v in m['outputs'].items():
        if rt.digest(out/name)!=v['sha256']:raise ValueError('Analysis output changed: '+name)
    parent=rt.verify(data)
    if parent['identity']!=m['parentProductIdentity']:raise ValueError('Parent terrain product changed')
    aws=FrozenAws(data/rt.CACHE)
    for key,v in m['awsInputs'].items():
        z,x,y=map(int,key.split('/'));aws.tile(z,x,y)
        if aws.records[key]!=v:raise ValueError('AWS provenance changed: '+key)
    m['identity']=identity
    return m


def serve_controls(data, port=4180):
    """Capture-only native prepared-Swiss tiles with diagnostic contributor weights.

    No analytical path; no network acquisition. Unknown coarse tiles redirect to
    the same production AWS service. High-zoom missing cached parents fail honestly.
    Results cached only in RAM; normal startup never imports this module.
    """
    m=verify_analysis(data)
    out=data/'experiments/atlas'/VERSION
    with np.load(out/'fields.npz') as fields:width=fields['adaptive_width']
    inverse=Transformer.from_crs(3857,2056,always_xy=True,allow_ballpark=False)
    aws=FrozenAws(data/rt.CACHE); bodies={}; lock=threading.RLock()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            match=re.fullmatch(r'/tiles/(hard|linear250|adaptive3deg)/(\d+)/(\d+)/(\d+)\.png',self.path)
            if not match:self.send_error(404);return
            method,z,x,y=match.groups();z,x,y=map(int,(z,x,y))
            if not 0<=z<=18 or not 0<=x<2**z or not 0<=y<2**z:self.send_error(400);return
            p=data/rt.PRODUCT/f'tiles/{z}/{x}/{y}.png'
            try:
                if not p.exists() and z<=15:
                    self.send_response(302);self.send_header('Location',rt.AWS.format(z=z,x=x,y=y))
                    self.send_header('Access-Control-Allow-Origin','*');self.end_headers();return
                key=(method,z,x,y)
                with lock:
                    if key not in bodies:
                        G=aws.at_tile(z,x,y)
                        if p.exists():
                            S=rt.decode(p.read_bytes())
                            b=rt.tile_bounds(z,x,y);step=(b[2]-b[0])/rt.SIZE
                            ee,nn=np.meshgrid(b[0]+(np.arange(rt.SIZE)+.5)*step,b[3]-(np.arange(rt.SIZE)+.5)*step)
                            e,n=inverse.transform(ee,nn);d=distance(e,n)
                            mask=np.asarray(rt.Image.open(data/rt.PRODUCT/f'masks/{z}/{x}/{y}.png'))!=0
                            w=mask.astype(float) if method=='hard' else weights(d,250 if method=='linear250' else bilinear(width,e,n))*mask
                            C=G+w*(S-G)
                            body=p.read_bytes() if method=='hard' else rt.encode(C)
                        else:body=rt.encode(G)
                        bodies[key]=body
                    body=bodies[key]
                self.send_response(200);self.send_header('Content-Type','image/png')
                self.send_header('Content-Length',str(len(body)));self.send_header('Access-Control-Allow-Origin','*')
                self.send_header('Cache-Control','no-store');self.send_header('X-Meridian-Analysis',m['identity'])
                self.end_headers();self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
            except Exception as error:
                print('TILE ERROR',self.path,str(error),flush=True);self.send_error(502,'Frozen terrain input unavailable')
        def log_message(self,*args):pass
    print('SERVING isolated reconciliation controls',port,m['identity'],flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path)
    parser.add_argument('--serve',action='store_true')
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--port',type=int,default=4180)
    args=parser.parse_args()
    data=args.data_root or rt.resolve_storage_roots(require_data=True).data
    if args.serve:serve_controls(data,args.port)
    elif args.verify:print('VERIFIED ANALYSIS',verify_analysis(data)['identity'])
    else:run(data)
