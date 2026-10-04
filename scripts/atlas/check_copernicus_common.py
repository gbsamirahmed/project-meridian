"""External-product diagnostics only; normal CI uses synthetic tests instead."""
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import copernicus_common as cp
import riffelhorn_terrain as rt
from riffelhorn_support import save


def summary(a):
    a=np.asarray(a,dtype='float64')
    return {'count':a.size,'min':float(a.min()),'max':float(a.max()),'mean':float(a.mean()),'rms':float(np.sqrt(np.mean(a*a))),'p50':float(np.median(a)),'p95Absolute':float(np.percentile(np.abs(a),95))}


def posts(ds,x,y):
    # GDAL affine already includes Point half-cell registration; centre once.
    col=(x-ds.transform.c)/ds.transform.a-.5
    row=(y-ds.transform.f)/ds.transform.e-.5
    ix=np.floor(col).astype(int);iy=np.floor(row).astype(int)
    if np.any(ix<0) or np.any(iy<0) or np.any(ix+1>=ds.width) or np.any(iy+1>=ds.height):raise ValueError('Outside source support')
    result=np.zeros(col.shape,dtype='float64')
    for dx,dy,w in [(0,0,(1-(col-ix))*(1-(row-iy))),(1,0,(col-ix)*(1-(row-iy))),(0,1,(1-(col-ix))*(row-iy)),(1,1,(col-ix)*(row-iy))]:
        for k in range(col.size):result[k]+=float(ds.read(1,window=Window(ix[k]+dx,iy[k]+dy,1,1))[0,0])*w[k]
    return result


def run():
    data=rt.resolve_storage_roots(require_data=True).data; out=data/cp.PRODUCT
    manifest=cp.verify(data); experiment=data/cp.EXPERIMENT
    if rt.repository_text_digest(out/'source-mosaic.vrt')!=manifest['sourceVrtSha256']:raise ValueError('Source registration/mosaic record changed')
    rng=np.random.default_rng(20211004)
    with rasterio.open(out/'working/z13.tif')as fine, rasterio.open(out/'source-mosaic.vrt')as source:
        cols=rng.integers(1,fine.width-1,2048);rows=rng.integers(1,fine.height-1,2048)
        x,y=rasterio.transform.xy(fine.transform,rows,cols)
        lon,lat=Transformer.from_crs(3857,4326,always_xy=True).transform(x,y)
        expected=posts(source,np.asarray(lon),np.asarray(lat))
        actual=np.array([fine.read(1,window=Window(int(c),int(r),1,1))[0,0]for c,r in zip(cols,rows)])
        fidelity=summary(actual-expected)
    if fidelity['p95Absolute']>.002 or max(abs(fidelity['min']),abs(fidelity['max']))>.01:raise ValueError('Independent source transfer check failed')
    parents=[]
    for z in range(8,13):
        error=0.; encoded=0.
        with rasterio.open(out/f'working/z{z+1}.tif')as child,rasterio.open(out/f'working/z{z}.tif')as parent:
            for _,window in parent.block_windows(1):
                a=parent.read(1,window=window)
                b=cp.mean_parent(child.read(1,window=Window(window.col_off*2,window.row_off*2,window.width*2,window.height*2)))
                error=max(error,float(np.max(np.abs(a-b))))
                x0,y0,_,_=cp.extent(z);p=out/f'tiles/{z}/{x0+int(window.col_off)//256}/{y0+int(window.row_off)//256}.png'
                encoded=max(encoded,float(np.max(np.abs(rt.decode(p.read_bytes())-a))))
        parents.append({'zoom':z,'allPixelAggregationMaxDifferenceMetres':error,'encodingMaxDifferenceMetres':encoded})
        if error!=0 or encoded>1/512:raise ValueError('Parent rule/encoding mismatch')
    locations={'riffelhorn-ridge':[7.76121329,45.97910794],'alpine-valley':[7.75,46.12],'aosta-valley':[7.4,45.74],'gentler-bern':[7.35,46.92]}
    patches=[];fig,axes=plt.subplots(4,2,figsize=(12,14))
    for k,(name,location)in enumerate(locations.items()):
        mx,my=Transformer.from_crs(4326,3857,always_xy=True).transform(*location)
        levels=[]
        with rasterio.open(out/'working/z13.tif')as fine:
            for z in range(8,14):
                with rasterio.open(out/f'working/z{z}.tif')as ds:
                    row,col=ds.index(mx,my);factor=2**(13-z)
                    # Same physical patch (one z8 pixel's 32x32 finest support).
                    rootrow=row//2**(z-8);rootcol=col//2**(z-8)
                    w=Window(rootcol*2**(z-8),rootrow*2**(z-8),2**(z-8),2**(z-8))
                    a=ds.read(1,window=w)
                    original=fine.read(1,window=Window(w.col_off*factor,w.row_off*factor,w.width*factor,w.height*factor))
                    direct=original.astype('float64').reshape(a.shape[0],factor,a.shape[1],factor).mean(axis=(1,3))
                    levels.append({'zoom':z,'height':summary(a),'directFinestBlockMeanMaxDifference':float(np.max(np.abs(a-direct)))})
                    if z==13:axes[k,0].imshow(a,cmap='terrain');axes[k,0].set_title(name+' finest 32x32 support')
            axes[k,1].plot([v['zoom']for v in levels],[v['height']['min']for v in levels],label='minimum')
            axes[k,1].plot([v['zoom']for v in levels],[v['height']['max']for v in levels],label='maximum')
            axes[k,1].plot([v['zoom']for v in levels],[v['height']['mean']for v in levels],label='mean')
            axes[k,1].legend();axes[k,1].set_ylabel('EGM2008 m');axes[k,1].set_xlabel('delivery zoom');axes[k,1].grid(alpha=.3)
        patches.append({'name':name,'location':location,'levels':levels})
    experiment.mkdir(parents=True,exist_ok=True);fig.tight_layout();fig.savefig(experiment/'parent-patches.png',dpi=130);plt.close(fig)
    # Every PNG is exactly the independently encoded full-raster window: no
    # per-tile warp, duplicate border sample or clamp is introduced at joins.
    boundaries=[]
    for z in range(8,14):
        x0,y0,nx,ny=cp.extent(z);max_error=0;max_change=0;total=0.;count=0;minimum=float('inf');maximum=-float('inf');zeros=0
        with rasterio.open(out/f'working/z{z}.tif')as ds:
            for yy in range(ny):
                for xx in range(nx):
                    a=ds.read(1,window=Window(xx*256,yy*256,256,256));b=rt.decode((out/f'tiles/{z}/{x0+xx}/{y0+yy}.png').read_bytes())
                    total+=float(a.sum(dtype='float64'));count+=a.size;minimum=min(minimum,float(a.min()));maximum=max(maximum,float(a.max()));zeros+=int(np.count_nonzero(a==0))
                    if rt.encode(a)!=(out/f'tiles/{z}/{x0+xx}/{y0+yy}.png').read_bytes():raise ValueError('Independent tile window differs')
                    max_error=max(max_error,float(np.max(np.abs(a-b))))
                    if xx:
                        pair=ds.read(1,window=Window(xx*256-1,yy*256,2,256));max_change=max(max_change,float(np.max(np.abs(np.diff(pair,axis=1)))))
                    if yy:
                        pair=ds.read(1,window=Window(xx*256,yy*256-1,256,2));max_change=max(max_change,float(np.max(np.abs(np.diff(pair,axis=0)))))
        boundaries.append({'zoom':z,'allTileWindowMaxEncodingDifference':max_error,'naturalAdjacentSampleChangeAtTileJoinsMax':max_change,'fullRaster':{'count':count,'min':minimum,'max':maximum,'mean':total/count,'zeroCells':zeros},'interpretation':'Adjacent pixel centres need not have equal heights; same global raster used on both sides.'})
    rebuild=data/(cp.PRODUCT+'-rebuild'); other=cp.verify(data,'-rebuild')
    if manifest['identity']!=other['identity'] or manifest['files']!=other['files']:raise ValueError('Independent rebuild mismatch')
    result={'productIdentity':manifest['identity'],'sourceTransfer':fidelity,'parentRule':parents,'patches':patches,'tileBoundaries':boundaries,'independentRebuild':{'identity':other['identity'],'allTileHashesMatch':True,'workingRasterHashesMatch':manifest['workingHashes']==other['workingHashes']},'preparationAccuracyOnly':True}
    save(experiment/'checks.json',result);save(cp.REPO/'docs/atlas/copernicus-common-checks.json',result)
    print(json.dumps({'fidelity':fidelity,'identity':manifest['identity'],'rebuild':True},indent=2))

if __name__=='__main__':run()
