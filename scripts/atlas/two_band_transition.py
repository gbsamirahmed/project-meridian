"""One frozen visual representation experiment. No source or runtime mutation."""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import threading
import time
import numpy as np
from pyproj import Transformer
import regional_parents as p
import seam_corridor as sc
import terrain_hierarchy as h

rt,sp,cp=p.rt,p.sp,p.cp
REPO=p.REPO
SPEC=REPO/'docs/atlas/riffelhorn-final-reconciliation-experiment.json'
VERSION='riffelhorn-two-band-transition-v1'
PRODUCT='derived/atlas/riffelhorn/'+VERSION
EXPERIMENT='experiments/atlas/'+VERSION


def quintic(t):
    t=np.clip(np.asarray(t,dtype=float),0,1)
    return 1-10*t**3+15*t**4-6*t**5


def weights(radius):
    return quintic((radius-1500)/2500),quintic((radius-3000)/1000)


def weight_derivative(radius,start,width):
    t=np.clip((radius-start)/width,0,1)
    return -30*t*t*(1-t)**2/width


def compose(s,c,sb,cb,radius):
    """Exact declared band operator; pure endpoint branches avoid cancellation."""
    b,d=weights(radius)
    out=np.array(c,dtype=float,copy=True)
    inner=radius<=1500; mixed=(radius>1500)&(radius<4000)
    if np.any(~np.isfinite(s[inner|mixed])) or np.any(~np.isfinite(sb[mixed])) or np.any(~np.isfinite(cb[mixed])):
        raise ValueError('Incomplete regional or broad transition support')
    out[inner]=s[inner]
    out[mixed]=(cb+b*(sb-cb)+d*(s-sb)+(1-d)*(c-cb))[mixed]
    labels=np.zeros(radius.shape,dtype='uint8')
    labels[inner]=1;labels[mixed & (radius<=3000)]=2;labels[mixed & (radius>3000)]=3
    return out,b,d,labels


def sample_grid(a,z,x0,y0,gx,gy):
    """Global pixel-centre coordinates; require four finite parent neighbours."""
    x=gx-x0*256;y=gy-y0*256
    ix=np.floor(x).astype(int);iy=np.floor(y).astype(int)
    inside=(ix>=0)&(iy>=0)&(ix+1<a.shape[1])&(iy+1<a.shape[0])
    ix=np.clip(ix,0,a.shape[1]-2);iy=np.clip(iy,0,a.shape[0]-2)
    wx=x-np.floor(x);wy=y-np.floor(y)
    valid=inside & np.isfinite(a[iy,ix])&np.isfinite(a[iy,ix+1])&np.isfinite(a[iy+1,ix])&np.isfinite(a[iy+1,ix+1])
    out=(1-wy)*((1-wx)*a[iy,ix]+wx*a[iy,ix+1])+wy*((1-wx)*a[iy+1,ix]+wx*a[iy+1,ix+1])
    return np.where(valid,out,np.nan)


class Transition:
    def __init__(self,data,suffix='',verify=True):
        self.data=Path(data);self.out=self.data/(PRODUCT+suffix);self.lock=threading.RLock()
        self.spec=json.loads(SPEC.read_text(encoding='utf8'))
        if verify:
            _,self.products,self.retained,self.assets,self.verification=sc.verify_inputs(self.data)
        else:
            self.products={k:json.loads((self.data/root/'manifest.json').read_text(encoding='utf8')) for k,root in [('swiss',sp.PRODUCT),('common',cp.PRODUCT),('regionalParents',p.PRODUCT)]}
            self.retained=dict(np.load(self.data/'experiments/atlas/global-reference-assessment-v1/fields-and-mask.npz'))
            self.verification={}
        if {k:v['identity'] for k,v in self.products.items()}!=self.spec['inputs']:
            raise ValueError('Frozen products differ')
        self.rows={k:{r['path']:r for r in v['files']} for k,v in self.products.items()}
        self.fields={}
        for z in [12,13,14]:
            with np.load(self.data/p.PRODUCT/f'fields/z{z}.npz') as a:
                values=a['heights'];counts=a['counts']
            self.fields[z]=np.where(counts==4**(14-z),values,np.nan)
        # Same restriction basis as the frozen decomposition, no sensor-PSF claim.
        x0,x1,y0,y1,shape,_=sp.hierarchy(13); common=np.full(shape,np.nan)
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                common[(y-y0)*256:(y-y0+1)*256,(x-x0)*256:(x-x0+1)*256]=self.read_common(13,x,y)
        valid=np.isfinite(self.fields[13])&np.isfinite(common)
        self.cb,counts=p.parent_grid(np.where(valid,common,np.nan),valid.astype('uint32'),12)
        self.cb[counts!=4]=np.nan
        self.inverse=Transformer.from_crs(3857,2056,always_xy=True,allow_ballpark=False)
        self.forward=Transformer.from_crs(2056,3857,always_xy=True,allow_ballpark=False)
        self.config={'version':VERSION,'specSha256':rt.repository_text_digest(SPEC),'products':self.spec['inputs'],
                     'toolSha256':rt.repository_text_digest(__file__),'height':'heterogeneous native LN02 / EGM2008; synthetic visual representation',
                     'labels':{'0':'source-derived common','1':'source-derived regional','2':'derived broad transition, regional detail retained','3':'derived broad plus detail taper','4':'derived parent'},
                     'operator':'Cb+b(Sb-Cb)+d(S-Sb)+(1-d)(C-Cb); b/d not confidence or convex source weights',
                     'software':{'numpy':np.__version__,'pyproj':__import__('pyproj').__version__,'pillow':__import__('PIL').__version__},
                     'implementationInterpretation':'z12 controls use global pixel-centre interpolation; unencoded z12 T aggregated to11/10. Exact common below10. Cached output is sparse evaluated inventory. Change masks use retained 25m historical250m-buffer proxy; no new fit.'}
        self.config['identity']=rt.stable_id(self.config)
        self.out.mkdir(parents=True,exist_ok=True)
        build=self.out/'build.json'
        if build.exists() and json.loads(build.read_text(encoding='utf8'))!=self.config:
            raise ValueError('Immutable build differs; named sibling required')
        sp.save(build,self.config)

    def source_body(self,kind,z,x,y):
        key=f'tiles/{z}/{x}/{y}.png';row=self.rows[kind].get(key)
        if row is None:raise FileNotFoundError('Missing '+kind+' tile '+key)
        path=self.data/(sp.PRODUCT if kind=='swiss' else cp.PRODUCT)/key
        body=path.read_bytes()
        if __import__('hashlib').sha256(body).hexdigest()!=row['sha256']:
            raise ValueError('Immutable '+kind+' input changed')
        return body

    @lru_cache(maxsize=160)
    def read_common(self,z,x,y):
        return rt.decode(self.source_body('common',z,x,y))

    def common(self,z,x,y):
        if z<=13:return self.read_common(z,x,y).copy()
        factor=2**(z-13);cx,cy=x//factor,y//factor
        a=self.read_common(13,cx,cy);padded=np.pad(a,1,mode='edge')
        for dx,dy in [(dx,dy) for dx in [-1,0,1] for dy in [-1,0,1] if dx or dy]:
            if f'tiles/13/{cx+dx}/{cy+dy}.png' not in self.rows['common']:continue
            b=self.read_common(13,cx+dx,cy+dy)
            rs=slice(0,1) if dy<0 else slice(257,258) if dy>0 else slice(1,257)
            cs=slice(0,1) if dx<0 else slice(257,258) if dx>0 else slice(1,257)
            br=slice(255,256) if dy<0 else slice(0,1) if dy>0 else slice(0,256)
            bc=slice(255,256) if dx<0 else slice(0,1) if dx>0 else slice(0,256)
            padded[rs,cs]=b[br,bc]
        return h.overzoom(padded,z,x,y)

    def coordinates(self,z,x,y):
        span=rt.WORLD/(256*2**z)
        yy,xx=np.indices((256,256));gx=x*256+xx+.5;gy=y*256+yy+.5
        mx=-rt.WORLD/2+gx*span;my=rt.WORLD/2-gy*span
        e,n=self.inverse.transform(mx,my)
        return e,n,np.hypot(e-2625000,n-1092000),gx,gy

    def broad(self,z,gx,gy):
        x0,_,y0,_,_,_=sp.hierarchy(12);scale=2**(z-12)
        return (sample_grid(self.fields[12],12,x0,y0,gx/scale-.5,gy/scale-.5),
                sample_grid(self.cb,12,x0,y0,gx/scale-.5,gy/scale-.5))

    def regional(self,z,x,y):
        if z>=15:return rt.decode(self.source_body('swiss',z,x,y))
        x0,_,y0,_,_,_=sp.hierarchy(z)
        out=np.full((256,256),np.nan);r,c=(y-y0)*256,(x-x0)*256
        a=self.fields[z]
        if r>=0 and c>=0 and r+256<=a.shape[0] and c+256<=a.shape[1]:
            out[:]=a[r:r+256,c:c+256]
        return out

    def candidate_tiles(self,z):
        from rasterio.warp import transform_bounds
        bounds=transform_bounds(2056,3857,2621000,1088000,2629000,1096000,densify_pts=41)
        span=rt.WORLD/(2**z)
        x0=int(np.floor((bounds[0]+rt.WORLD/2)/span));x1=int(np.floor((bounds[2]+rt.WORLD/2)/span))
        y0=int(np.floor((rt.WORLD/2-bounds[3])/span));y1=int(np.floor((rt.WORLD/2-bounds[1])/span))
        return [(x,y) for y in range(y0,y1+1) for x in range(x0,x1+1)]

    def preflight(self):
        result={'levels':{},'specSha256':self.config['specSha256'],'complete':True}
        for z in range(12,19):
            required=[];missing=[];checked=0
            for x,y in self.candidate_tiles(z):
                e,n,r,gx,gy=self.coordinates(z,x,y)
                if not np.any(r<4000):continue
                required.append([x,y]);m=r<4000
                sb,cb=self.broad(z,gx,gy)
                if np.any(~np.isfinite(sb[m])) or np.any(~np.isfinite(cb[m])):
                    missing.append({'tile':[x,y],'reason':'broad interpolation support'})
                try:s=self.regional(z,x,y)
                except FileNotFoundError:
                    missing.append({'tile':[x,y],'reason':'fine delivery support'});continue
                if np.any(~np.isfinite(s[m])):missing.append({'tile':[x,y],'reason':'complete regional cells'})
                self.common(z,x,y);checked+=int(m.sum())
            result['levels'][str(z)]={'requiredTiles':required,'missing':missing,'supportedCircleCells':checked}
            result['complete'] &= not missing
            print('SUPPORT',z,len(required),'missing',len(missing),flush=True)
        sp.save(self.out/'preflight.json',result)
        if not result['complete']:raise ValueError('Frozen support prerequisite failed')
        return result

    @lru_cache(maxsize=192)
    def values(self,z,x,y):
        if not 8<=z<=18:raise FileNotFoundError('Finite evaluation levels8-18')
        c=self.common(z,x,y)
        if z<10:
            return c,np.zeros(c.shape),np.zeros(c.shape),np.zeros(c.shape,dtype='uint8')
        if z in [10,11]:
            parts=[self.values(z+1,x*2+dx,y*2+dy) for dy in range(2) for dx in range(2)]
            joined=[np.block([[parts[0][i],parts[1][i]],[parts[2][i],parts[3][i]]]) for i in range(4)]
            t,_=p.aggregate(joined[0],np.ones((512,512),dtype='uint32'))
            b,_=p.aggregate(joined[1],np.ones((512,512),dtype='uint32'))
            d,_=p.aggregate(joined[2],np.ones((512,512),dtype='uint32'))
            labels=np.where(b>0,4,0).astype('uint8')
            # Pure outside footprints retain canonical common rather than drift.
            t=np.where(labels==0,c,t)
            return t,b,d,labels
        e,n,r,gx,gy=self.coordinates(z,x,y)
        if not np.any(r<4000):
            return c,np.zeros(c.shape),np.zeros(c.shape),np.zeros(c.shape,dtype='uint8')
        s=self.regional(z,x,y);sb,cb=self.broad(z,gx,gy)
        return compose(s,c,sb,cb,r)

    def tile(self,strategy,z,x,y):
        if strategy not in ['transition','common','regional','hard']:raise ValueError('Frozen controls only')
        leaf=f'{strategy}/{z}/{x}/{y}';path=self.out/f'tiles/{leaf}.png';receipt=self.out/f'receipts/{leaf}.json'
        with self.lock:
            if path.exists():
                row=json.loads(receipt.read_text(encoding='utf8'));body=path.read_bytes()
                if rt.digest(path)!=row['sha256'] or row['buildIdentity']!=self.config['identity']:raise ValueError('Evaluation cache changed')
                return body,row
            e,n,r,_,_=self.coordinates(z,x,y)
            if strategy=='transition':a,b,d,labels=self.values(z,x,y)
            elif strategy=='common':a=self.common(z,x,y);b=d=np.zeros(a.shape);labels=np.zeros(a.shape,dtype='uint8')
            else:
                # Same frozen regional-parent hard handoff. Pure regional control
                # is interpreted only inside its complete support, never outside.
                if z in [12,13] and f'tiles/{z}/{x}/{y}.png' in self.rows['regionalParents']:
                    a=rt.decode((self.data/p.PRODUCT/f'tiles/{z}/{x}/{y}.png').read_bytes());labels=np.ones(a.shape,dtype='uint8')
                elif z>=14 and f'tiles/{z}/{x}/{y}.png' in self.rows['swiss']:
                    a=rt.decode(self.source_body('swiss',z,x,y));labels=np.ones(a.shape,dtype='uint8')
                else:a=self.common(z,x,y);labels=np.zeros(a.shape,dtype='uint8')
                b=d=labels.astype(float)
            body=rt.encode(a)
            metadata=self.out/f'contributions/{leaf}.npz';metadata.parent.mkdir(parents=True,exist_ok=True)
            iy=np.clip(((1097000-n)/25).astype(int),0,399);ix=np.clip(((e-2620000)/25).astype(int),0,399)
            valid=(e>=2620000)&(e<=2630000)&(n>=1087000)&(n<=1097000)
            change=np.where(valid,self.retained['glacier250Mask'][iy,ix],0).astype('uint8')
            np.savez_compressed(metadata,broadWeight=b,detailWeight=d,labels=labels,changeProxy=change,changeClassificationKnown=valid)
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
            row={'strategy':strategy,'z':z,'x':x,'y':y,'path':path.relative_to(self.out).as_posix(),'sha256':rt.digest(path),
                 'bytes':len(body),'maskPath':metadata.relative_to(self.out).as_posix(),'maskSha256':rt.digest(metadata),
                 'buildIdentity':self.config['identity'],'labels':{str(i):int((labels==i).sum()) for i in np.unique(labels)},
                 'heightReference':'heterogeneous LN02/EGM2008' if np.any(labels>=2) else 'LN02' if np.all(labels==1) else 'EGM2008',
                 'maxQuantizationM':float(np.max(abs(rt.decode(body)-a)))}
            sp.save(receipt,row);return body,row

    def inventory(self):
        rows=[]
        for path in sorted((self.out/'receipts').rglob('*.json')):
            row=json.loads(path.read_text(encoding='utf8'))
            for key,sha in [('path','sha256'),('maskPath','maskSha256')]:
                if rt.digest(self.out/row[key])!=row[sha]:raise ValueError('Output hash changed')
            with np.load(self.out/row['maskPath']) as a:
                if np.any(a['broadWeight']< -1e-12) or np.any(a['broadWeight']>1+1e-12) or np.any(a['detailWeight']< -1e-12) or np.any(a['detailWeight']>1+1e-12):raise ValueError('Invalid band weight')
                if row['labels']!={str(i):int((a['labels']==i).sum()) for i in np.unique(a['labels'])}:raise ValueError('Label drift')
            rows.append(row)
        manifest={'config':self.config,'files':rows,'coverage':'Sparse bounded evaluated inventory, not full global or national coverage',
                  'provenance':'Band/operator metadata reconstruct signed contributions; weights are not confidence; parent weights are mean influence, not complete reconstruction without parent operation'}
        manifest['identity']=rt.stable_id(manifest);sp.save(self.out/'manifest.json',manifest);return manifest


def serve(t,port):
    import re
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                m=re.fullmatch(r'/tiles/(transition|common|regional|hard)/(\d+)/(\d+)/(\d+)\.png',self.path)
                if not m:raise FileNotFoundError('Unsupported path')
                body,row=t.tile(m[1],*map(int,m.groups()[1:]));status=200
            except FileNotFoundError:body=b'';row={};status=404
            except Exception as e:print('TILE ERROR',repr(e),flush=True);body=b'';row={};status=500
            self.send_response(status)
            for k,v in {'Access-Control-Allow-Origin':'*','Access-Control-Expose-Headers':'X-Meridian-Height,X-Meridian-Build',
                        'Content-Type':'image/png','Content-Length':str(len(body)),'Cache-Control':'public,max-age=3600' if status==200 else 'no-store'}.items():self.send_header(k,v)
            if row:self.send_header('X-Meridian-Height',row['heightReference']);self.send_header('X-Meridian-Build',row['buildIdentity'])
            self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def log_message(self,*args):pass
    print('SERVING',port,t.config['identity'],flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['preflight','serve','inventory','rebuild'])
    parser.add_argument('--data',type=Path,required=True);parser.add_argument('--suffix',default='');parser.add_argument('--port',type=int,default=4185)
    args=parser.parse_args();t=Transition(args.data,args.suffix)
    if args.command=='preflight':t.preflight()
    elif args.command=='serve':serve(t,args.port)
    elif args.command=='rebuild':
        old=json.loads((args.data/PRODUCT/'manifest.json').read_text(encoding='utf8'))
        for row in old['files']:t.tile(row['strategy'],row['z'],row['x'],row['y'])
        new=t.inventory()
        if new!=old:raise ValueError('Independent rebuild differs')
        print('REBUILT',new['identity'])
    else:print('INVENTORY',t.inventory()['identity'])
