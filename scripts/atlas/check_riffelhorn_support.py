"""Preparation fidelity and expanded product disagreement, not accuracy/fusion."""
import json,math,time
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.transform import from_bounds
from rasterio.warp import reproject,Resampling
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import riffelhorn_support as sp
import riffelhorn_terrain as rt
from riffelhorn_reconciliation import stats,gaussian

def source_bilinear(ds,e,n):
    e,n=np.broadcast_arrays(e,n);px=(e-sp.BOUNDS[0])/.5-.5;py=(sp.BOUNDS[3]-n)/.5-.5
    x0=np.floor(px).astype(int);y0=np.floor(py).astype(int)
    xmin=int(x0.min());ymin=int(y0.min());xmax=int(x0.max())+1;ymax=int(y0.max())+1
    a=ds.read(1,window=Window(xmin,ymin,xmax-xmin+1,ymax-ymin+1)).astype(float)
    if np.any(a==-9999):raise ValueError('Nodata in reference samples')
    xx=x0-xmin;yy=y0-ymin;fx=px-x0;fy=py-y0
    return (a[yy,xx]*(1-fx)+a[yy,xx+1]*fx)*(1-fy)+(a[yy+1,xx]*(1-fx)+a[yy+1,xx+1]*fx)*fy

class ReuseAws(rt.AwsCache):
    def __init__(self,data):
        super().__init__(data/'cache/atlas/riffelhorn'/sp.VERSION/'aws-diagnostics');self.old=rt.AwsCache(data/rt.CACHE)
    def tile(self,z,x,y):
        if (self.old.root/f'{z}/{x%(2**z)}/{y}.png').exists():
            value=self.old.tile(z,x,y)
            for k,v in self.old.records.items():self.records[k]={**v,'cacheRoot':rt.CACHE}
            return value
        value=super().tile(z,x,y);key='/'.join(map(str,(z,x%(2**z),y)))
        self.records[key]['cacheRoot']='cache/atlas/riffelhorn/'+sp.VERSION+'/aws-diagnostics'
        return value

def run(data):
    m=sp.verify(data);out=data/sp.PRODUCT;exp=data/sp.EXPERIMENT;exp.mkdir(parents=True,exist_ok=True)
    fwd=Transformer.from_crs(2056,3857,always_xy=True,allow_ballpark=False);inv=Transformer.from_crs(3857,2056,always_xy=True,allow_ballpark=False)
    report={'identity':m['identity'],'fidelity':[],'tileBoundaryChecks':[],'interpretation':'Transfer fidelity and cross-product disagreement, not absolute accuracy or datum correction.'}
    with rasterio.open(out/'source-mosaic.vrt')as ds:
        # Five separate sectors: benchmark plus NW/NE/SW/SE support.
        sectors=[('benchmark',2625000,1092000),('northwest',2622200,1094800),('northeast',2627800,1094800),('southwest',2622200,1089200),('southeast',2627800,1089200)]
        vrt,_=sp.warped(ds,18,fwd)
        with vrt:
            for name,e,n in sectors:
                me,mn=fwd.transform(e,n);px,py=rt.pixel_xy(me,mn,18);tx,ty=int(math.floor((px+.5)/256)),int(math.floor((py+.5)/256))
                p=out/f'tiles/18/{tx}/{ty}.png'
                if not p.exists():raise ValueError('Missing sector tile')
                a=rt.decode(p.read_bytes());b=rt.tile_bounds(18,tx,ty);s=(b[2]-b[0])/256
                indices=np.arange(8,248,8);cx,cy=np.meshgrid(indices,indices);se,sn=inv.transform(b[0]+(cx+.5)*s,b[3]-(cy+.5)*s)
                report['fidelity'].append({'sector':name,'tile':[18,tx,ty],'encodedMinusIndependentSourceBilinear':stats(a[cy,cx]-source_bilinear(ds,se,sn))})
                # Independent 512-pixel target warp crossing adjacent web tiles.
                other=out/f'tiles/18/{tx+1}/{ty}.png'
                if not other.exists():continue
                joined=np.hstack((a,rt.decode(other.read_bytes())))
                reference=np.full((256,512),np.nan,dtype='float32')
                reproject(rasterio.band(ds,1),reference,src_transform=ds.transform,src_crs=ds.crs,src_nodata=-9999,dst_transform=from_bounds(b[0],b[1],b[2]+(b[2]-b[0]),b[3],512,256),dst_crs='EPSG:3857',dst_nodata=np.nan,resampling=Resampling.bilinear,num_threads=1,ERROR_THRESHOLD=0.0,COORDINATE_OPERATION=fwd.definition)
                strip=(joined-reference)[:,252:260]
                report['tileBoundaryChecks'].append({'sector':name,'encodedMinusIndependentJointWarp':stats(strip)})
        # 10 m LV95 diagnostic grid; 20x20 official cells per diagnostic cell.
        step=10;size=1000;swiss=ds.read(1,out_shape=(size,size),resampling=Resampling.average).astype(float)
        if np.any(swiss==-9999)or not np.all(np.isfinite(swiss)):raise ValueError('Unexpected nodata in diagnostic grid')
        ee,nn=np.meshgrid(sp.BOUNDS[0]+(np.arange(size)+.5)*step,sp.BOUNDS[3]-(np.arange(size)+.5)*step)
        aws=ReuseAws(data);global_h=np.empty_like(swiss)
        for row in range(0,size,50):
            me,mn=fwd.transform(ee[row:row+50],nn[row:row+50]);global_h[row:row+50]=aws.at_mercator(me,mn)
            print('DIAGNOSTIC',row+50,'of',size,flush=True)
        difference=swiss-global_h;distance=np.hypot(ee-sp.CENTRE[0],nn-sp.CENTRE[1]);slope=np.hypot(*np.gradient(swiss,step));smooth=gaussian(difference,250,step=step)
        report['expandedDifference']=stats(difference);report['protectedInteriorDifference']=stats(difference[distance<=sp.RADIUS]);report['sigma250Residual']=stats(difference-smooth)
        report['annuli']=[{'inner':a,'outer':b,'difference':stats(difference[(distance>=a)&(distance<b)])}for a,b in [(0,1500),(1500,2500),(2500,3500),(3500,5000)]]
        report['quadrants']={name:stats(difference[mask])for name,mask in {'NW':(ee<sp.CENTRE[0])&(nn>=sp.CENTRE[1]),'NE':(ee>=sp.CENTRE[0])&(nn>=sp.CENTRE[1]),'SW':(ee<sp.CENTRE[0])&(nn<sp.CENTRE[1]),'SE':(ee>=sp.CENTRE[0])&(nn<sp.CENTRE[1])}.items()}
        report['gentleSlopeDifference']=stats(difference[slope<.15]);report['steepSlopeDifference']=stats(difference[slope>1]);report['awsInputs']=aws.records
        report['oldCropAtSame10mGrid']=stats(difference[(ee>=2624000)&(ee<2626000)&(nn>=1091000)&(nn<1093000)])
        report['spatialCorrelation']={str(d):{'eastWest':float(np.corrcoef(difference[:,:-d//10].ravel(),difference[:,d//10:].ravel())[0,1]),'northSouth':float(np.corrcoef(difference[:-d//10].ravel(),difference[d//10:].ravel())[0,1])}for d in [250,500,1000,2000]}
        np.savez_compressed(exp/'diagnostic-10m.npz',swiss=swiss,aws=global_h,difference=difference,slope=slope)
        report['diagnosticGridSha256']=rt.digest(exp/'diagnostic-10m.npz')
        extent=(0,10,0,10);fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
        for ax,a,title,cmap,limits in [(axes[0],swiss,'Swiss source average at 10 m','terrain',(None,None)),(axes[1],difference,'Swiss minus AWS (m)','RdBu_r',(-200,200)),(axes[2],difference-smooth,'Residual after sigma 250 m (m)','RdBu_r',(-50,50))]:
            im=ax.imshow(a,extent=extent,origin='upper',cmap=cmap,vmin=limits[0],vmax=limits[1]);fig.colorbar(im,ax=ax,shrink=.75);ax.add_patch(plt.Circle((5,5),1.5,fill=False,color='black',lw=1.2));ax.plot([4,6,6,4,4],[4,4,6,6,4],color='black',ls='--',lw=.8);ax.set_title(title);ax.set_xlabel('km east from LV95 2620000');ax.set_ylabel('km north from 1087000')
        fig.savefig(exp/'expanded-fields.png',dpi=150);plt.close(fig)
        fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained')
        for ax,index,title in [(axes[0],500,'West–east at N1092000 (nearest 10 m row)'),(axes[1],500,'South–north at E2625000 (nearest 10 m column)')]:
            x=(np.arange(1000)+.5)*10
            a=swiss[index,:]if ax is axes[0]else swiss[::-1,index];b=global_h[index,:]if ax is axes[0]else global_h[::-1,index]
            ax.plot(x,a,label='Swiss');ax.plot(x,b,label='AWS');ax.axvspan(3500,6500,alpha=.1,color='green');ax.set_title(title);ax.set_ylabel('height (m), distinct product semantics');ax.legend();ax.grid(alpha=.2)
        fig.savefig(exp/'expanded-profiles.png',dpi=150);plt.close(fig)
    sp.save(exp/'numerical-evaluation.json',report)
    compact={k:v for k,v in report.items()if k!='awsInputs'};compact['awsTileCount']=len(report['awsInputs']);compact['fullReportSha256']=rt.digest(exp/'numerical-evaluation.json');sp.save(sp.REPO/'docs/atlas/riffelhorn-support-measurements.json',compact)
    print('REPORT',json.dumps(compact,indent=2),flush=True)

if __name__=='__main__':run(rt.resolve_storage_roots(require_data=True).data)
