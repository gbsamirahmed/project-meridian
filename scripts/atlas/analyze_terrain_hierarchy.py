"""Reuse frozen overlap fields; diagnose scale/spatial support without fitting."""
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyproj import Transformer
import terrain_hierarchy as h
import riffelhorn_terrain as rt
import riffelhorn_support as sp

def stats(v):
    v=np.asarray(v);v=v[np.isfinite(v)]
    if not len(v):return {'n':0}
    med=float(np.median(v))
    return {'n':int(len(v)),'median':med,'mean':float(v.mean()),'nmad':float(1.4826*np.median(abs(v-med))),'rms':float(np.sqrt(np.mean(v*v))),'min':float(v.min()),'max':float(v.max()),'p05':float(np.quantile(v,.05)),'p95':float(np.quantile(v,.95))}

def run(data,gate,suffix):
    out=data/h.EXPERIMENT;out.mkdir(parents=True,exist_ok=True)
    p=data/'experiments/atlas/global-reference-assessment-v1/fields-and-mask.npz'
    fields=np.load(p);expected=json.loads((h.REPO/'docs/atlas/global-reference-measurements.json').read_text())['arrayHashes']
    for key in fields.files:
        if hashlib.sha256(fields[key].tobytes()).hexdigest()!=expected[key]:raise ValueError('Frozen overlap array drift: '+key)
    swiss=fields['swissLn02'];diff=fields['copernicusRaw'];stable=fields['primaryMask'].astype(bool)
    # Stored raw field is Swiss minus Copernicus; explicitly verify that convention.
    np.testing.assert_allclose(diff,swiss-fields['copernicus'],atol=1e-8,equal_nan=True)
    y,x=np.mgrid[:400,:400];xx=2620000+(x+.5)*25;yy=1097000-(y+.5)*25
    radius=np.hypot(xx-2625000,yy-1092000);edge=np.minimum.reduce([xx-2620000,2630000-xx,yy-1087000,1097000-yy])
    result={'baseline':'74ea75b1577fbdd7a85af3a1989ac8aee42c54f0','frozenOverlapSha256':rt.digest(p),'heightPolicy':'Native Swiss LN02 minus Copernicus EGM2008, no accepted datum/registration adjustment','stableAll':stats(diff[stable]),'spatialGroups':{},'slopes':{},'sectors':{},'edges':{},'protectedInterior':{},'parentChild':{}}
    for name,mask in [('protected',radius<=1500),('support-1500-3000',(radius>1500)&(radius<=3000)),('support-3000-4500',(radius>3000)&(radius<=4500)),('outer',radius>4500),('glacier-buffer',fields['glacier250Mask'].astype(bool))]:
        result['spatialGroups'][name]={'all':stats(diff[mask]),'stable':stats(diff[mask&stable])}
    for lo,hi in [(0,250),(250,500),(500,1000),(1000,2000),(2000,3500),(3500,5001)]:result['edges'][f'{lo}-{hi}m']={'all':stats(diff[(edge>=lo)&(edge<hi)]),'stable':stats(diff[stable&(edge>=lo)&(edge<hi)])}
    for lo,hi in [(5,15),(15,25),(25,40)]:result['slopes'][f'{lo}-{hi}deg']=stats(diff[stable&(fields['slope']>=lo)&(fields['slope']<hi)])
    for name,mask in [('NW',(xx<2625000)&(yy>=1092000)),('NE',(xx>=2625000)&(yy>=1092000)),('SW',(xx<2625000)&(yy<1092000)),('SE',(xx>=2625000)&(yy<1092000))]:result['sectors'][name]={'all':stats(diff[mask]),'stable':stats(diff[mask&stable])}
    # Local 25 m residual from 3x3 mean is a roughness diagnostic, not a mask.
    pad=np.pad(swiss,1,mode='edge');mean=sum(pad[i:i+400,j:j+400]for i in range(3)for j in range(3))/9
    rough=abs(swiss-mean)
    result['roughness']={f'{lo}-{hi}m':stats(diff[stable&(rough>=lo)&(rough<hi)])for lo,hi in [(0,1),(1,3),(3,1000)]}
    fig,axes=plt.subplots(1,3,figsize=(15,5));extent=[-5,5,-5,5]
    im=axes[0].imshow(diff,extent=extent,cmap='RdBu_r',vmin=-30,vmax=30);axes[0].set_title('Swiss LN02 − Copernicus EGM2008 (m)');fig.colorbar(im,ax=axes[0])
    axes[1].imshow(stable,extent=extent,cmap='gray');axes[1].set_title('Retained candidate stable support')
    axes[2].imshow(rough,extent=extent,vmin=0,vmax=5,cmap='magma');axes[2].set_title('25 m surface / 3×3 mean residual (m)')
    for ax in axes:
        ax.add_patch(plt.Circle((0,0),1.5,fill=False,color='lime'));ax.set_xlabel('LV95 east offset (km)');ax.set_ylabel('north offset (km)')
    fig.tight_layout();fig.savefig(out/'support-diagnostics.png',dpi=140);plt.close(fig)
    hierarchy=h.Hierarchy(data,gate,suffix,verify=False)
    to3857=Transformer.from_crs(2056,3857,always_xy=True)
    def sample(strategy,z,e,n):
        mx,my=to3857.transform(e,n);world=rt.WORLD;gx=(mx+world/2)/world*256*2**z-.5;gy=(world/2-my)/world*256*2**z-.5
        ix=np.floor(gx).astype(int);iy=np.floor(gy).astype(int);wx=gx-ix;wy=gy-iy
        values=[];labels=[]
        for ox,oy in [(0,0),(1,0),(0,1),(1,1)]:
            px=ix+ox;py=iy+oy;v=np.zeros(px.shape);lab=np.zeros(px.shape)
            for tx,ty in set(zip((px//256).ravel(),(py//256).ravel())):
                mask=(px//256==tx)&(py//256==ty);body,row=hierarchy.tile(strategy,z,int(tx),int(ty));a=rt.decode(body)
                v[mask]=a[py[mask]%256,px[mask]%256];lab[mask]=row['contributor']
            values.append(v);labels.append(lab)
        a,b,c,d=values
        return (1-wy)*((1-wx)*a+wx*b)+wy*((1-wx)*c+wx*d),labels[0]
    # Tile-edge strips: inside Swiss complete tile against an absent neighboring tile.
    for z in [14,16,18]:
        candidates=[]
        for key in hierarchy.swiss_files:
            parts=key.split('/')
            if len(parts)!=4 or int(parts[1])!=z:continue
            tx=int(parts[2]);ty=int(parts[3].split('.')[0])
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                if f'tiles/{z}/{tx+dx}/{ty+dy}.png'not in hierarchy.swiss_files:candidates.append((tx,ty,dx,dy))
        # Fixed deterministic sample distributed around all four edges, not chosen by outcome.
        chosen=[]
        for direction in [(1,0),(-1,0),(0,1),(0,-1)]:
            group=sorted(c for c in candidates if c[2:]==direction)
            for idx in sorted(set([0,len(group)//2,len(group)-1])):chosen.append(group[idx])
        rows=[]
        for tx,ty,dx,dy in chosen:
            a=rt.decode(hierarchy.tile('H1',z,tx,ty)[0]);b=rt.decode(hierarchy.tile('H1',z,tx+dx,ty+dy)[0])
            jump=(b[:,0]-a[:,-1])if dx==1 else (a[:,0]-b[:,-1])if dx==-1 else (b[0,:]-a[-1,:])if dy==1 else (a[0,:]-b[-1,:])
            ca=rt.decode(hierarchy.tile('common',z,tx,ty)[0]);cb=rt.decode(hierarchy.tile('common',z,tx+dx,ty+dy)[0])
            cj=(cb[:,0]-ca[:,-1])if dx==1 else (ca[:,0]-cb[:,-1])if dx==-1 else (cb[0,:]-ca[-1,:])if dy==1 else (ca[0,:]-cb[-1,:])
            rows.append({'tile':[z,tx,ty],'neighbor':[dx,dy],'adjacentCellDifference':stats(jump),'commonAdjacentControl':stats(cj),'joinExcessOverCommonControl':stats(jump-cj)})
        result.setdefault('hardBoundaries',{})[str(z)]=rows
    # Protected interior samples: compare exact Swiss delivered field, and level shifts.
    ee=xx[::4,::4];nn=yy[::4,::4];inside=np.hypot(ee-2625000,nn-1092000)<=1500
    for z in [13,14,15,16,18]:
        vals,labels=sample('H1',z,ee[inside],nn[inside]);common,_=sample('common',z,ee[inside],nn[inside]);base,_=sample('H0',z,ee[inside],nn[inside])
        result['protectedInterior'][str(z)]={'samples':len(vals),'regionalSamples':int((labels==1).sum()),'versusH0Swiss':stats(vals-base),'versusCommon':stats(vals-common)}
    ev,nv=ee[inside],nn[inside]
    coarse,_=sample('H0',11,ev,nv);first,first_labels=sample('H0',12,ev,nv)
    common12,_=sample('common',12,ev,nv)
    result['H0Onset']={'11-12':stats(first-coarse),'z12versusCommon':stats(first-common12),'regionalSamplesAt12':int((first_labels==1).sum()),'samples':len(first)}
    previous=None
    for z in [12,13,14,15,16,17,18]:
        vals,_=sample('H1',z,ev,nv)
        if previous is not None:result['parentChild'][f'{z-1}-{z}']=stats(vals-previous)
        previous=vals
    # One-metre transects centered on each actual selected z16 hard tile edge.
    from pyproj import Transformer as T
    back=T.from_crs(3857,2056,always_xy=True)
    profiles=[]
    for row in result['hardBoundaries']['16']:
        z,tx,ty=row['tile'];dx,dy=row['neighbor'];left,bottom,right,top=rt.tile_bounds(z,tx,ty)
        mx=right if dx==1 else left if dx==-1 else (left+right)/2;my=bottom if dy==1 else top if dy==-1 else (bottom+top)/2
        e,n=back.transform(mx,my);along=np.arange(-100,101,dtype=float)
        es=e+along if dx else np.full(along.shape,e);ns=np.full(along.shape,n)if dx else n+along
        vals,labs=sample('H1',16,es,ns);co,_=sample('common',16,es,ns)
        profiles.append({'tile':row['tile'],'direction':row['neighbor'],'lv95':[e,n],'maxAdjacent1m':float(np.max(abs(np.diff(vals)))),'positionsM':along.tolist(),'heightM':vals.tolist(),'commonM':co.tolist(),'labels':labs.tolist()})
    sp.save(out/'boundary-profiles.json',profiles)
    result['transects']=[{k:r[k]for k in ['tile','direction','lv95','maxAdjacent1m']}for r in profiles]
    fig,axes=plt.subplots(3,4,figsize=(16,9))
    for ax,row in zip(axes.flat,profiles):
        ax.plot(row['positionsM'],row['heightM'],label='H1 native composite');ax.plot(row['positionsM'],row['commonM'],label='common');ax.set_title(str(row['tile'])+str(row['direction']));ax.set_xlabel('distance (m)')
    axes[0,0].legend();fig.tight_layout();fig.savefig(out/'boundary-profiles.png',dpi=130);plt.close(fig)
    result['product']=hierarchy.inventory()['identity'];sp.save(h.REPO/'docs/atlas/terrain-hierarchy-measurements.json',result)
    print(json.dumps({k:result[k]for k in ['stableAll','protectedInterior','parentChild','transects']},indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--gate',type=int,default=14);p.add_argument('--suffix',default='');a=p.parse_args();run(rt.resolve_storage_roots(require_data=True).data,a.gate,a.suffix)
