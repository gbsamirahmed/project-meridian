"""Read-only physical-wavelength diagnostic; never write terrain products."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window

def bands(height,spacing,edges,window=True,detrend=True):
    a=np.asarray(height,dtype='float64')
    if a.ndim!=2 or not np.isfinite(a).all() or spacing<=0:raise ValueError('Complete finite 2D terrain required')
    y,x=np.indices(a.shape);design=np.stack([np.ones(a.size),x.ravel(),y.ravel()],axis=1)
    residual=a-(design@np.linalg.lstsq(design,a.ravel(),rcond=None)[0]).reshape(a.shape) if detrend else a
    w=np.outer(np.hanning(a.shape[0]),np.hanning(a.shape[1])) if window else np.ones(a.shape)
    field=residual*w;power=abs(np.fft.fft2(field))**2/(a.size**2*np.mean(w*w))
    fy,fx=np.meshgrid(np.fft.fftfreq(a.shape[0],spacing),np.fft.fftfreq(a.shape[1],spacing),indexing='ij');freq=np.hypot(fx,fy)
    wavelength=np.divide(1,freq,out=np.full_like(freq,np.inf),where=freq>0)
    ranges=[(0,edges[0])]+list(zip(edges[:-1],edges[1:]))+[(edges[-1],float('inf'))]
    rows=[]
    for lo,hi in ranges:
        mask=(wavelength>=lo)&(wavelength<hi) if np.isfinite(hi) else wavelength>=lo
        rows.append({'lowerMetres':lo,'upperMetres':hi if np.isfinite(hi) else None,'rmsMetres':float(np.sqrt(power[mask].sum())),'coefficientCount':int(mask.sum())})
    total=float(np.sqrt(power.sum()));return {'bands':rows,'totalWindowCorrectedRms':total,'parsevalError':float(power.sum()-np.mean(field*field)/np.mean(w*w))}

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sample_native(path,center,n,step):
    with rasterio.open(path) as ds:
        if ds.crs.is_geographic:raise ValueError('Metric native CRS required')
        v=(np.arange(n)+.5-n/2)*step;xx,yy=np.meshgrid(center[0]+v,center[1]-v)
        rows,cols=rasterio.transform.rowcol(ds.transform,xx,yy,op=lambda x:x-.5);rows,cols=np.asarray(rows).reshape(n,n),np.asarray(cols).reshape(n,n)
        ir,ic=np.floor(rows).astype(int),np.floor(cols).astype(int);r0,c0=ir.min(),ic.min();r1,c1=ir.max()+2,ic.max()+2
        tile=ds.read(1,window=Window(c0,r0,c1-c0,r1-r0),masked=True).filled(np.nan)
        wy,wx=rows-ir,cols-ic;ir-=r0;ic-=c0
        values=(1-wy)*((1-wx)*tile[ir,ic]+wx*tile[ir,ic+1])+wy*((1-wx)*tile[ir+1,ic]+wx*tile[ir+1,ic+1])
        return values,{'path':str(path),'sha256':digest(path),'crs':str(ds.crs),'gridSpacing':list(ds.res),'centreNative':list(center),'operation':'Native cell-centred bilinear reconstruction at declared diagnostic samples; no vertical transform'}

def run(data):
    repo=Path(__file__).resolve().parents[2];plan=json.loads((repo/'docs/atlas/multiscale-representation-plan.json').read_text(encoding='utf8'));cfg=plan['terrainSpectrum'];n=cfg['sideCells'];step=cfg['spacingMetres'];result={'planSha256':digest(repo/'docs/atlas/multiscale-representation-plan.json'),'diagnostics':[]}
    paths={'tryfan':(data/'sources/atlas/tryfan/welsh-lidar-1m/rasters/tryfan-004-dtm-1m.tif',(266400,359300)),'riffelhorn':(data/'derived/atlas/riffelhorn/riffelhorn-swiss-support-v1/source-mosaic.vrt',(2625000,1092000))}
    for site,(source,centre) in paths.items():
        values,receipt=sample_native(source,centre,n,step);assert np.isfinite(values).all()
        gradient=np.gradient(values,step);slope=np.degrees(np.arctan(np.hypot(*gradient)))
        result['diagnostics'].append({'site':site,'nativeInput':receipt,'shape':list(values.shape),'spacingMetres':step,'slopeDegreesMedianP95':np.quantile(slope,[.5,.95]).tolist(),'spectrum':bands(values,step,cfg['wavelengthEdgesMetres'])})
    out=data/'experiments/atlas/multiscale-representation-v1';out.mkdir(parents=True,exist_ok=True);text=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n';(out/'spectrum.json').write_text(text,encoding='utf8',newline='\n');print(text)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args();run(a.data)
