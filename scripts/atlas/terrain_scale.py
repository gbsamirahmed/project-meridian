"""Offline restriction/prolongation diagnostic; never generate terrain tiles."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def lift(a, fine_shape, fine_origin, coarse_origin, factor):
    """Pixel-centre bilinear prolongation; all four neighbours must be finite."""
    yy, xx = np.indices(fine_shape)
    x = (xx + fine_origin[0] + .5) / factor - .5 - coarse_origin[0]
    y = (yy + fine_origin[1] + .5) / factor - .5 - coarse_origin[1]
    ix, iy = np.floor(x).astype(int), np.floor(y).astype(int)
    valid = (ix >= 0) & (iy >= 0) & (ix+1 < a.shape[1]) & (iy+1 < a.shape[0])
    ix = np.clip(ix, 0, a.shape[1]-2); iy = np.clip(iy, 0, a.shape[0]-2)
    wx, wy = x-np.floor(x), y-np.floor(y)
    out = ((1-wy)*((1-wx)*a[iy,ix]+wx*a[iy,ix+1])
           + wy*((1-wx)*a[iy+1,ix]+wx*a[iy+1,ix+1]))
    return np.where(valid, out, np.nan)


def components(s, c, sb, cb):
    return {'raw':s-c, 'broad':sb-cb, 'swissDetail':s-sb,
            'commonDetail':c-cb, 'detailDifference':(s-sb)-(c-cb),
            'asymmetricSwissBroadMinusCommon':sb-c}


def stats(a):
    a = np.asarray(a); a = a[np.isfinite(a)]
    if not len(a):
        return {'count':0}
    med = float(np.median(a))
    return {'count':int(a.size), 'mean':float(a.mean()), 'median':med,
            'nmad':float(1.4826*np.median(abs(a-med))),
            'rms':float(np.sqrt(np.mean(a*a))),
            **{k:float(v) for k,v in zip(['min','p05','p50','p95','p99','max'],
                                         np.quantile(a,[0,.05,.5,.95,.99,1]))}}


def energy(d,b,r):
    """Exact uncentred second-moment accounting, not fractions of terrain error."""
    raw = float(np.mean(d*d)); broad = float(np.mean(b*b))
    detail = float(np.mean(r*r)); cross = float(2*np.mean(b*r))
    return {'rawMeanSquare':raw,'broadMeanSquare':broad,
            'detailDifferenceMeanSquare':detail,'twiceCrossMoment':cross,
            'closure':raw-broad-detail-cross,
            'broadDetailCorrelation':correlation(b,r)}


def correlation(a,b):
    good = np.isfinite(a) & np.isfinite(b)
    if good.sum() < 3 or np.std(a[good]) == 0 or np.std(b[good]) == 0:
        return None
    return float(np.corrcoef(a[good],b[good])[0,1])


def lag_correlation(a,mask,lag):
    pairs = mask[:, :-lag] & mask[:, lag:]
    vertical = mask[:-lag] & mask[lag:]
    return {'eastWest':correlation(a[:,:-lag][pairs],a[:,lag:][pairs]),
            'northSouth':correlation(a[:-lag][vertical],a[lag:][vertical]),
            'eastWestPairs':int(pairs.sum()),'northSouthPairs':int(vertical.sum())}


def sample(a,z,e,n):
    from analyze_regional_parents import sample_field
    return sample_field(a,z,e,n)


def sample_tiles(data,product,manifest,z,e,n,receipts):
    """Read-only sampling; missing regional delivery is absent, never fallback."""
    from pyproj import Transformer
    import regional_parents as p
    x,y=Transformer.from_crs(2056,3857,always_xy=True).transform(e,n)
    gx=(x+p.rt.WORLD/2)/p.rt.WORLD*256*2**z-.5
    gy=(p.rt.WORLD/2-y)/p.rt.WORLD*256*2**z-.5
    ix,iy=np.floor(gx).astype(int),np.floor(gy).astype(int)
    wx,wy=gx-ix,gy-iy; parts=[]; rows={v['path']:v for v in manifest['files']}
    for dx,dy in [(0,0),(1,0),(0,1),(1,1)]:
        px,py=ix+dx,iy+dy; a=np.full(e.shape,np.nan)
        for tx,ty in sorted(set(zip(px//256,py//256))):
            key=f'tiles/{z}/{tx}/{ty}.png'
            if key not in rows:
                continue
            path=data/product/key
            if p.rt.digest(path)!=rows[key]['sha256']:
                raise ValueError('Fine profile tile changed: '+key)
            receipts[key]=rows[key]['sha256']
            height=p.rt.decode(path.read_bytes())
            m=(px//256==tx)&(py//256==ty);a[m]=height[py[m]%256,px[m]%256]
        parts.append(a)
    a,b,c,d=parts
    return (1-wy)*((1-wx)*a+wx*b)+wy*((1-wx)*c+wx*d)


def run(data,suffix):
    import sys
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import rasterio
    from rasterio.transform import from_bounds
    import pyproj
    import regional_parents as p
    import seam_corridor as sc
    import assess_global_reference as assessment
    plan_path=p.REPO/'docs/atlas/terrain-scale-plan.json'
    plan=json.loads(plan_path.read_text(encoding='utf8'))
    _,products,retained,assets,verification=sc.verify_inputs(data)
    if {k:v['identity'] for k,v in products.items()} != plan['products']:
        raise ValueError('Frozen product identity changed')
    ice,_=assessment.glacier_footprints(data,assets,from_bounds(*p.sp.BOUNDS,400,400))
    np.testing.assert_array_equal(ice[250],retained['glacier250Mask'])
    f=sc.load_level(data,13,products,retained,ice)
    original_hashes={k:sc.array_hash(f[k]) for k in ['swiss','common','counts']}
    valid=f['valid']; s=f['swiss']; c=f['common']
    counts=valid.astype('uint32')
    working={'swiss':np.where(valid,s,np.nan),'common':np.where(valid,c,np.nan)}
    heights={}; supports={}
    for z in [12,11]:
        for key in working:
            heights[key],support=p.parent_grid(working[key],counts,z)
        heights={k:v.copy() for k,v in heights.items()}
        counts=support; working=heights.copy()
        supports[z]=(heights.copy(),counts.copy())
    out=data/('experiments/atlas/'+plan['version']+suffix)
    if (out/'manifest.json').exists():
        raise ValueError('Immutable diagnostic exists; choose another suffix')
    out.mkdir(parents=True,exist_ok=True)
    result={'baseline':plan['baseline'],'products':plan['products'],
            'heightPolicy':'Native LN02 and EGM2008; no transform, offset or registration',
            'verification':verification,'commonFilesRead':f['commonFiles'],
            'software':{'python':sys.version,'numpy':np.__version__,'rasterio':rasterio.__version__,
                        'gdal':rasterio.__gdal_version__,'pyproj':pyproj.__version__},
            'levels':{},'profiles':{},'fineProfiles':{},'fineProfileFilesRead':{},
            'sourceInputsUnchanged':True,'arrayHashes':{}}
    arrays={}; x0,_,y0,_,_,_=p.sp.hierarchy(13)
    masks={'all':valid & (f['edge']>=200),
           'stableCandidates':f['stable'],
           'steepNonIce':(f['slope']>=45) & ~f['ice'][250] & ~f['snow'] & ~f['water'],
           'glacierChangeProxy':f['ice'][250],
           'protected':f['radius']<=1500}
    fig,axs=plt.subplots(2,3,figsize=(13,9),layout='constrained')
    for z in plan['broadZooms']:
        fields,support=supports[z]; full=support==4**(13-z)
        xx,_,yy,_,_,_=p.sp.hierarchy(z)
        sb=lift(np.where(full,fields['swiss'],np.nan),s.shape,(x0*256,y0*256),(xx*256,yy*256),2**(13-z))
        cb=lift(np.where(full,fields['common'],np.nan),s.shape,(x0*256,y0*256),(xx*256,yy*256),2**(13-z))
        comp=components(s,c,sb,cb)
        good=valid & np.isfinite(sb) & np.isfinite(cb) & (f['edge']>=200)
        closure=comp['raw']-comp['broad']-comp['detailDifference']
        if np.max(abs(closure[good]))>1e-10:
            raise ValueError('Algebraic decomposition failed')
        # Independently retained regional parents validate the restriction basis.
        with np.load(data/p.PRODUCT/f'fields/z{z}.npz') as retained_parent:
            aggregation_error=fields['swiss'][full]-retained_parent['heights'][full]
        row={'groundPostingNearRiffelhornM':13.28*2**(13-z),
             'closureMaxM':float(np.max(abs(closure[good]))),
             'retainedSwissParentDifference':stats(aggregation_error),'strata':{}}
        for label,mask in masks.items():
            m=good & mask
            row['strata'][label]={'components':{k:stats(a[m]) for k,a in comp.items()},
                                 'energy':energy(comp['raw'][m],comp['broad'][m],comp['detailDifference'][m]),
                                 'absoluteSlopeCorrelation':{k:correlation(abs(a[m]),f['slope'][m]) for k,a in comp.items()}}
        row['spatialCorrelation']={k:{str(lag*13.28):lag_correlation(a,good,lag) for lag in [2,8,38,75]}
                                   for k,a in comp.items() if k in ['raw','broad','detailDifference']}
        row['sectors']={label:{k:stats(a[good & m]) for k,a in comp.items()} for label,m in [
            ('NW',(f['east']<2625000)&(f['north']>=1092000)),('NE',(f['east']>=2625000)&(f['north']>=1092000)),
            ('SW',(f['east']<2625000)&(f['north']<1092000)),('SE',(f['east']>=2625000)&(f['north']<1092000))]}
        result['levels'][str(z)]=row
        for k,a in {'swissBroad':sb,'commonBroad':cb,**comp,'valid':good}.items():
            arrays[f'z{z}_{k}']=a
        for col,key in enumerate(['raw','broad','swissDetail']):
            ax=axs[12-z,col]
            im=ax.imshow(np.where(good,comp[key],np.nan),vmin=-50,vmax=50,cmap='RdBu_r')
            ax.set_title(f'z13 → z{z}: {key} (m)');ax.set_axis_off()
            ax.contour(f['radius'],levels=[1500],colors='black',linewidths=.6)
            ax.contour(f['ice'][250],levels=[.5],colors='purple',linewidths=.4)
        for name,(start,end) in plan['profilesLV95'].items():
            length=float(np.linalg.norm(np.array(end)-start));distance=np.linspace(0,length,int(length/20)+1)
            e=start[0]+distance/length*(end[0]-start[0]);n=start[1]+distance/length*(end[1]-start[1])
            values={k:sample(a,13,e,n) for k,a in {'swiss':s,'common':c,'swissBroad':sb,'commonBroad':cb,**comp}.items()}
            result['profiles'][f'{name}-broad{z}']={'endpointsLV95':[start,end],'distanceM':distance.tolist(),
                'values':{k:[float(v) if np.isfinite(v) else None for v in a] for k,a in values.items()}}
            if z==12:
                fine=sample_tiles(data,p.sp.PRODUCT,products['swiss'],plan['fineProfileZoom'],e,n,result['fineProfileFilesRead'])
                result['fineProfiles'][name]={'zoom':plan['fineProfileZoom'],'count':int(np.isfinite(fine).sum()),
                    'rawFineSwissMinusCommon':stats(fine-values['common']),
                    'fineSwissMinusBroadSwiss':stats(fine-values['swissBroad']),
                    'fineSwissMinusZ13Swiss':stats(fine-values['swiss']),
                    'values':[float(v) if np.isfinite(v) else None for v in fine]}
    fig.colorbar(im,ax=axs,shrink=.65,label='metres; native-height difference, not error')
    fig.savefig(out/'decomposition.png',dpi=140,metadata={'Software':'Meridian diagnostic'});plt.close(fig)
    fig,axes=plt.subplots(4,2,figsize=(14,12),layout='constrained')
    for r,name in enumerate(plan['profilesLV95']):
        q=result['profiles'][f'{name}-broad12']; distance=q['distanceM']; v=q['values']
        for k in ['swiss','swissBroad','common','commonBroad']:
            axes[r,0].plot(distance,v[k],label=k)
        axes[r,0].plot(distance,result['fineProfiles'][name]['values'],label='Swiss z16',lw=.7,color='black')
        for k in ['raw','broad','swissDetail','commonDetail']:
            axes[r,1].plot(distance,v[k],label=k)
        axes[r,0].set_title(name);axes[r,0].set_ylabel('native height (m)')
        axes[r,1].set_ylabel('component (m)');axes[r,1].axhline(0,color='black',lw=.4)
    axes[0,0].legend();axes[0,1].legend()
    axes[3,0].set_xlabel('profile distance (m)');axes[3,1].set_xlabel('profile distance (m)')
    fig.savefig(out/'profiles.png',dpi=140,metadata={'Software':'Meridian diagnostic'});plt.close(fig)
    arrays.update({k:f[k] for k in ['swiss','common','stable','slope','radius','edge']})
    arrays['glacier250']=f['ice'][250]
    for k,a in arrays.items():
        np.save(out/(k+'.npy'),a,allow_pickle=False)
        result['arrayHashes'][k]=sc.array_hash(a)
    if original_hashes!={k:sc.array_hash(f[k]) for k in original_hashes}:
        raise ValueError('Diagnostic modified input arrays')
    (out/'measurements.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf8')
    files=[{'path':v.name,'sha256':p.rt.digest(v),'bytes':v.stat().st_size} for v in sorted(out.iterdir()) if v.is_file()]
    helpers=['terrain_scale.py','seam_corridor.py','regional_parents.py','analyze_regional_parents.py','assess_global_reference.py']
    manifest={'protocol':plan,'protocolSha256':p.rt.repository_text_digest(plan_path),
              'tools':{k:p.rt.repository_text_digest(p.REPO/'scripts/atlas'/k) for k in helpers},
              'files':files,'arrayHashes':result['arrayHashes'],'products':plan['products']}
    manifest['identity']=p.rt.stable_id(manifest)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'identity':manifest['identity'],'path':str(out),'bytes':sum(v['bytes'] for v in files)}))
    return result,manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True);parser.add_argument('--suffix',default='')
    args=parser.parse_args();run(args.data,args.suffix)
