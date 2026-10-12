"""Bounded adapters for the proposed retained-input replay; not run on real inputs here."""
from contextlib import ExitStack
import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds

from pilot import CORE, CONTEXT, XY, block_mean, smooth
from windowed import Grid


class SwissNativeReader:
    shape = (4000,4000)
    def __init__(self, data_root, pins):
        self.stack = ExitStack()
        self.datasets = []
        self.cache = self.stack.enter_context(rasterio.Env(GDAL_CACHEMAX=32*1024**2,
            GDAL_NUM_THREADS='1', GDAL_PAM_ENABLED='NO'))
        try:
            for source in pins['inputs'][:4]:
                ds = self.stack.enter_context(rasterio.open(data_root/source['path']))
                if ds.crs.to_epsg()!=2056 or ds.shape!=(2000,2000) or ds.res!=(.5,.5) or ds.nodata!=-9999:
                    raise ValueError('Unexpected Swiss native profile')
                col = round((ds.bounds.left-CORE[0])/.5)
                row = round((ds.bounds.bottom-CORE[1])/.5)
                if col not in (0,2000) or row not in (0,2000):
                    raise ValueError('Unexpected Swiss tile origin')
                self.datasets.append((row,col,ds))
            if len({(row,col) for row,col,_ in self.datasets})!=4:
                raise ValueError('Incomplete/duplicate Swiss native tiling')
        except Exception:
            self.close()
            raise

    def close(self):
        self.stack.close()

    def read(self,row,r1,col,c1):
        if not (0<=row<r1<=4000 and 0<=col<c1<=4000) or max(r1-row,c1-col)>1052:
            raise ValueError('Unbounded/out-of-support source window')
        values = np.full((r1-row,c1-col),np.nan,dtype=np.float32)
        for tile_row,tile_col,ds in self.datasets:
            a,b = max(row,tile_row),min(r1,tile_row+2000)
            c,d = max(col,tile_col),min(c1,tile_col+2000)
            if a>=b or c>=d:
                continue
            window = Window(c-tile_col,2000-(b-tile_row),d-c,b-a)
            block = ds.read(1,window=window,masked=False)
            block[block==ds.nodata] = np.nan
            values[a-row:b-row,c-col:d-col] = block[::-1]
        return Grid(CORE[0]+.25+np.arange(col,c1)*.5,
                    CORE[1]+.25+np.arange(row,r1)*.5,values,row,col)


class SwissCoarseReader:
    shape = (1000,1000)
    def __init__(self,native,smoothing=False,transform=None):
        self.native,self.smoothing,self.transform = native,smoothing,transform

    def read(self,row,r1,col,c1):
        halo = 3 if self.smoothing else 0
        a,b,c,d = row-halo,r1+halo,col-halo,c1+halo
        aa,bb,cc,dd = max(a,0),min(b,1000),max(c,0),min(d,1000)
        averaged = block_mean(self.native.read(aa*4,bb*4,cc*4,dd*4).z)
        if halo:
            padded = np.full((b-a,d-c),np.nan)
            padded[aa-a:bb-a,cc-c:dd-c] = averaged
            values = smooth(padded)[halo:-halo,halo:-halo]
        else:
            values = averaged
        x,y = CORE[0]+1+np.arange(col,c1)*2.,CORE[1]+1+np.arange(row,r1)*2.
        if self.transform is not None:
            xx,yy = np.meshgrid(x,y)
            x,y,values = self.transform.transform(xx,yy,values,errcheck=True)
        return Grid(x,y,values,row,col)


class CopernicusReader:
    def __init__(self,path):
        self.ds = rasterio.open(path)
        ds = self.ds
        if ds.crs.to_epsg()!=4326 or ds.tags().get('AREA_OR_POINT')!='Point' or ds.shape!=(3600,3600):
            self.close()
            raise ValueError('Unexpected Copernicus native profile')
        corners = [XY.transform(x,y) for x in (CONTEXT[0],CONTEXT[2]) for y in (CONTEXT[1],CONTEXT[3])]
        window = from_bounds(min(p[0] for p in corners),min(p[1] for p in corners),
            max(p[0] for p in corners),max(p[1] for p in corners),ds.transform)
        self.col = int(np.floor(window.col_off))-1
        self.row = int(np.floor(window.row_off))-1
        right = int(np.ceil(window.col_off+window.width))+1
        bottom = int(np.ceil(window.row_off+window.height))+1
        self.shape = (bottom-self.row,right-self.col)
        if min(self.row,self.col)<0 or right>ds.width or bottom>ds.height or max(self.shape)>256:
            self.close()
            raise ValueError('Missing/unbounded Copernicus context')
        self.x0 = ds.transform.c+(self.col+.5)*ds.transform.a
        self.y0 = ds.transform.f+(bottom-.5)*ds.transform.e
        self.dx,self.dy = ds.transform.a,-ds.transform.e

    def close(self):
        self.ds.close()

    def read(self,row,r1,col,c1):
        if not (0<=row<r1<=self.shape[0] and 0<=col<c1<=self.shape[1]):
            raise ValueError('Copernicus window outside support')
        window = Window(self.col+col,self.row+self.shape[0]-r1,c1-col,r1-row)
        values = self.ds.read(1,window=window,masked=True).filled(np.nan)[::-1].copy()
        return Grid(self.x0+np.arange(col,c1)*self.dx,self.y0+np.arange(row,r1)*self.dy,
                    values,row,col)

    def sample(self,lon,lat):
        grid = self.read(0,self.shape[0],0,self.shape[1])
        col,row = (lon-self.x0)/self.dx,(lat-self.y0)/self.dy
        ci,ri = np.floor(col).astype(int),np.floor(row).astype(int)
        if (ci<0).any() or (ri<0).any() or (ci+1>=self.shape[1]).any() or (ri+1>=self.shape[0]).any():
            raise ValueError('Global sampling outside declared posts')
        fx,fy = col-ci,row-ri
        z = grid.z
        return ((1-fx)*(1-fy)*z[ri,ci]+fx*(1-fy)*z[ri,ci+1]+(1-fx)*fy*z[ri+1,ci]+fx*fy*z[ri+1,ci+1])
