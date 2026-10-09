"""One versioned physical crop binding; original scientific records stay untouched."""
from pathlib import Path
import hashlib
import os
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'reduction'))
from reader import Reader, ReadError, require, identity
from verification import Snapshot, bounded_bytes, json_value, digest, MAX_BYTES, MAX_JSON, manifest_at as v1_manifest_at
from store import Store
from shared import SharedProjection
from rasterio.io import MemoryFile
from rasterio.windows import Window
from rasterio import Affine
from shapely.geometry import shape
from closure import derive, WINDOW

SCHEMA='atlas-native-window-experiment/v1'
BASE='a34ac6745abe92904d6af089ae8dff888d3527d6588c395ee3b03750d9e08a1c'
SOURCE='638c155dd9a5f0b7ee818146def740093da33cee4606071b2bbf7ce3fa00ab95'
SOURCE_NAME=SOURCE+'.tif'
PROCESSING={'method':'native-grid-window-storage/v1','resampling':'none','notice':'Modified Copernicus DEM: lossless native-grid subset; original scientific source identity retained. Upstream attribution and licence obligations remain applicable. No redistribution clearance is asserted.','terms':'https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf'}


def manifest_at(root,expected=None):
    try:
        root=Path(root)
        require(not root.is_symlink() and not root.is_junction(),'projection-integrity','Linked projection root is unsupported.')
        m=json_value(bounded_bytes(root/'manifest.json',65536))
        if isinstance(m,dict) and m.get('schema')=='atlas-read-projection-spike/v1':
            original=v1_manifest_at(root,expected)
            require(original['projectionIdentity']==BASE,'projection-incompatible','Only the accepted v1 baseline is supported.')
            return original
        require(isinstance(m,dict) and m.get('schema')==SCHEMA and m.get('profile')=='meridian-atlas-read-contract/v1','projection-incompatible','Unsupported window schema/profile.')
        require(set(m)=={'schema','profile','sourceProjection','pins','files','window','projectionIdentity'},'projection-integrity','Window manifest fields differ.')
        require(digest(m['projectionIdentity']) and identity({k:v for k,v in m.items() if k!='projectionIdentity'})==m['projectionIdentity'],'projection-integrity','Window identity differs.')
        if expected is not None:require(m['projectionIdentity']==expected,'projection-integrity','Expected window identity differs.')
        original=m['sourceProjection']
        require(original['projectionIdentity']==BASE and identity({k:v for k,v in original.items() if k!='projectionIdentity'})==BASE,'projection-integrity','Original source-projection binding differs.')
        require(m['pins']==original['pins'],'projection-integrity','Scientific pins differ.')
        w=m['window']
        require(set(w)=={'sourceIdentity','sourceMember','sourceSeal','sourceNative','sourceWindow','storedMember','pixelSha256','pixelEncoding','storedNative','processing','closure'},'projection-integrity','Window binding fields differ.')
        require(w['processing']==PROCESSING,'projection-integrity','Storage method/modification notice differs.')
        require(w['pixelEncoding']=='IEEE754-binary32-le-row-major/v1','projection-incompatible','Unsupported pixel identity encoding.')
        require(w['sourceIdentity']=='dsm:'+SOURCE and w['sourceMember']==SOURCE_NAME and w['sourceSeal']==original['files'][SOURCE_NAME]
                and w['sourceWindow']==WINDOW and w['closure']==derive(),'projection-integrity','Source grid or closure differs.')
        name=w['storedMember']
        require(isinstance(name,str) and re.fullmatch(r'[0-9a-f]{64}\.tif',name) is not None and name!=SOURCE_NAME and digest(w['pixelSha256']),'projection-integrity','Invalid separate storage identity.')
        require(isinstance(m['files'],dict) and set(m['files'])==(set(original['files'])-{SOURCE_NAME})|{name},'projection-integrity','Window physical closure differs.')
        for k,v in m['files'].items():
            require(isinstance(v,dict) and set(v)=={'sha256','bytes'} and digest(v['sha256']) and type(v['bytes']) is int and 0<v['bytes']<=MAX_BYTES,'projection-integrity','Member seal differs.')
            if k!=name:require(v==original['files'][k],'projection-integrity','Unchanged member differs.')
        require(m['files'][name]['sha256']+'.tif'==name and m['files'][name]['bytes']<12*1024*1024,'projection-integrity','Window size/filename differs.')
        require(sum(v['bytes'] for v in m['files'].values())<=MAX_BYTES,'projection-integrity','Window exceeds byte bound.')
        present=set()
        with os.scandir(root) as entries:
            for entry in entries:
                present.add(entry.name)
                require(len(present)<=17,'projection-integrity','Physical member count exceeds bound.')
        require(present==set(m['files'])|{'manifest.json'},'projection-integrity','Missing or unexpected physical member.')
        return m
    except ReadError:raise
    except OSError as e:raise ReadError('projection-unavailable','Missing window member.') from e
    except (ValueError,KeyError,TypeError,AttributeError,IndexError) as e:raise ReadError('projection-integrity','Malformed window manifest or unsupported operation.') from e


class NativeGrid:
    """Captured crop translated into the few absolute-grid operations Reader uses."""
    def __init__(self,mem,native,offset):self.mem=mem;self.native=native;self.offset=offset
    def open(self,driver='GTiff'):return NativeDataset(self.mem.open(driver=driver),self.native,self.offset)
    def close(self):self.mem.close()

class NativeDataset:
    def __init__(self,src,native,offset):
        self.src=src;self.shape=tuple(native['shape']);self.transform=Affine(*native['transform'][:6]);self.crs=src.crs;self.nodata=src.nodata;self.offset=offset
    def __enter__(self):return self
    def __exit__(self,*_):self.src.close()
    def read(self,index,window):
        c,r,w,h=window.flatten();left,top,width,height=self.offset
        require(w>0 and h>0 and all(float(v).is_integer() for v in [c,r,w,h]) and left<=c and top<=r and c+w<=left+width and r+h<=top+height,
                'projection-integrity','Absolute source window is unavailable; never return empty evidence.')
        return self.src.read(index,window=Window(c-left,r-top,w,h))
    def window_transform(self,window):return self.transform*Affine.translation(window.col_off,window.row_off)

class WindowSnapshot(Snapshot):
    def __init__(self,root,expected=None):
        self.rasters={};self.generations={}
        try:
            outer=self.storage_manifest=manifest_at(root,expected)
            if outer['schema']=='atlas-read-projection-spike/v1':
                Snapshot.__init__(self,root,expected);self.storage_manifest=self.manifest;return
            original=self.manifest=outer['sourceProjection'];w=outer['window'];metadata={};headers={}
            for name,seal in outer['files'].items():
                raw=bounded_bytes(Path(root)/name,MAX_JSON if name.endswith('.json') else MAX_BYTES,seal)
                if name.endswith('.json'):metadata[name]=json_value(raw);continue
                mem=MemoryFile(raw);key=SOURCE_NAME if name==w['storedMember'] else name
                self.rasters[key]=mem
                with mem.open(driver='GTiff') as src:
                    require(src.driver=='GTiff' and src.count==1 and src.width*src.height<=13000000,'projection-integrity','Unsupported raster allocation.')
                    if name==w['storedMember']:
                        n=w['sourceNative'];left,top,width,height=WINDOW
                        require(n['shape']==[3600,3600] and n['crs']=='EPSG:4326' and src.shape==(height,width)
                                and str(src.crs)==n['crs'] and src.transform==Affine(*n['transform'][:6])*Affine.translation(left,top)
                                and src.dtypes==('float32',) and src.nodata is None and src.tags().get('AREA_OR_POINT')==n['tags']['AREA_OR_POINT'],'projection-integrity','Stored native-window header differs.')
                        require(w['storedNative']=={'shape':list(src.shape),'transform':list(src.transform),'crs':str(src.crs),'dtype':src.dtypes[0],'nodata':src.nodata},'projection-integrity','Local stored-grid metadata differs.')
                        require(hashlib.sha256(src.read(1).astype('<f4',copy=False).tobytes()).hexdigest()==w['pixelSha256'],'projection-integrity','Decoded window pixels differ.')
                        headers[key]={k:n[k] for k in ['crs','shape','transform']}
                    else:headers[key]={'crs':str(src.crs),'shape':list(src.shape),'transform':list(src.transform)}
                if name==w['storedMember']:self.rasters[key]=NativeGrid(mem,w['sourceNative'],WINDOW)
            self.features={f['identity']:f for f in metadata['features.json']['features']}
            require(len(self.features)==38,'projection-integrity','Native features differ.')
            self.worldcover=metadata['worldcover.json']
            for pin,entry in original['pins'].items():
                d=metadata[entry['file']]
                self.check_generation(d,pin,entry,headers)
                for r in d['answer']['results']:
                    if r['identity']==w['sourceIdentity']:
                        require(d['answer']['documents'][r['evidenceRef']]['detail']['binding']['native']==w['sourceNative'],'projection-integrity','Original source grid differs.')
                self.generations[pin]=d
        except (ReadError,OSError,ValueError,KeyError,TypeError,AttributeError,IndexError) as e:
            self.close()
            if isinstance(e,ReadError):raise
            raise ReadError('projection-integrity','Invalid native-window content.') from e

class WindowReader(Reader):snapshot_type=WindowSnapshot
class WindowShared(SharedProjection):snapshot_type=WindowSnapshot
class WindowStore(Store):
    snapshot_type=WindowSnapshot
    reader_type=WindowReader
    manifest_reader=staticmethod(manifest_at)
