"""Independent bounded source-transfer/parent checks; optional external-data CLI."""
import argparse,json,math
from pathlib import Path
import numpy as np
import rasterio,pyproj
from riffelhorn_support import save
import riffelhorn_terrain as rt
from tryfan_product import source_record,PRODUCT

def check(data):
    source=source_record(data);out=data/PRODUCT;m=json.loads((out/'manifest.json').read_text());errors=[];encoded=[]
    with rasterio.open(source) as s: a=s.read(1);transform=s.transform
    # Invert the exact recorded forward operation, rather than fitting registration.
    inverse=pyproj.Transformer.from_pipeline(m['processing']['horizontalOperation'])
    with rasterio.open(out/'working/z17.tif') as d:
        for f in m['files']:
            z,x,y=map(int,Path(f['path']).with_suffix('').parts[1:])
            if z!=17:continue
            decoded=rt.decode((out/f['path']).read_bytes());r,c=np.mgrid[8:256:16,8:256:16];w,s,e,n=rt.tile_bounds(z,x,y)
            xx=w+(c+.5)*(e-w)/256;yy=n-(r+.5)*(n-s)/256
            bx,by=inverse.transform(xx,yy,direction=pyproj.enums.TransformDirection.INVERSE)
            col=(bx-transform.c)/transform.a-.5;row=(by-transform.f)/transform.e-.5
            i=np.floor(col).astype(int);j=np.floor(row).astype(int);fx=col-i;fy=row-j
            expected=(a[j,i]*(1-fx)+a[j,i+1]*fx)*(1-fy)+(a[j+1,i]*(1-fx)+a[j+1,i+1]*fx)*fy
            rr=round((n-d.transform.f)/d.transform.e)+r;cc=round((w-d.transform.c)/d.transform.a)+c
            value=d.read(1,window=rasterio.windows.Window(int(cc.min())-8,int(rr.min())-8,256,256))[r,c]
            errors.extend((value-expected).ravel());encoded.extend((decoded[r,c]-value).ravel())
    parents=[]
    for z in range(14,17):
        diffs=[]
        with rasterio.open(out/f'working/z{z}.tif') as p,rasterio.open(out/f'working/z{z+1}.tif') as c:
            for _,win in p.block_windows(1):
                b=p.read(1,window=win);v=c.read(1,window=rasterio.windows.Window(win.col_off*2,win.row_off*2,win.width*2,win.height*2)).astype('float64');expected=(v[0::2,0::2]+v[0::2,1::2]+v[1::2,0::2]+v[1::2,1::2])/4
                np.testing.assert_array_equal(np.isfinite(b),np.isfinite(expected));diffs.extend((b-expected)[np.isfinite(b)])
        parents.append({'parent':z,'maxFloat32Rounding':float(np.max(abs(np.array(diffs))))})
    def stats(v):
        v=np.asarray(v);return {'samples':len(v),'rms':float(np.sqrt(np.mean(v*v))),'maxAbs':float(np.max(abs(v))),'p95Abs':float(np.percentile(abs(v),95))}
    result={'sourceToFinestUnencoded':stats(errors),'encoding':stats(encoded),'independentParentRule':parents,'sourceHashAfter':rt.digest(source),'manifestSha256':rt.digest(out/'manifest.json')}
    save(data/'experiments/atlas/tryfan-second-region-proof/numerical-checks.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);check(p.parse_args().data)
