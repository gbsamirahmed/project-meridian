"""One bounded read-only JSON-lines worker. Paths come only from S1 catalogue locators.
No discovery, acquisition, resampling, geometry repair or persistent query cache.
"""
import hashlib, json, math, sys, time, base64, struct, zlib
from bisect import bisect_right
from pathlib import Path
import numpy as np
import rasterio
from pyproj import Transformer, __version__ as proj_version
from shapely.geometry import shape, Point, box
from shapely.validation import explain_validity
from affine import Affine

class NativeError(Exception):
    def __init__(self, code, message):
        super().__init__(message); self.code=code

def checked_file(record):
    if 'meridian-private' in record['path'].lower():
        raise NativeError('invalid-locator', 'Private data excluded before access')
    p=Path(record['path'])
    if not p.is_file(): raise NativeError('artifact-unavailable', 'Registered artifact unavailable')
    if p.stat().st_size!=record['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:
        raise NativeError('hash-mismatch', 'Registered retained bytes differ')
    return p

def cell_index(t,x,y,width,height):
    # Exact delivered rectilinear grid edges avoid inverse-affine cancellation at
    # native corners. No epsilon/snapping or inferred geospatial precision.
    if t.b!=0 or t.d!=0 or t.a<=0 or t.e>=0:
        raise NativeError('unsupported-representation','Only retained north-up rectilinear grid supported')
    right,bottom=t*(width,height)
    if not (t.c<=x<right and bottom<y<=t.f):return None
    column=bisect_right([t.c+i*t.a for i in range(width+1)],x)-1
    row=bisect_right([-(t.f+i*t.e) for i in range(height+1)],-y)-1
    return row,column

def members(features,x,y,bounds=None):
    target=box(*bounds) if bounds else Point(x,y); result=[]
    for f,g in features:
        # Rebuilt finite bbox candidate list, exact geometry predicate second.
        a,b,c,d=g.bounds; w,s,e,n=target.bounds
        if c<w or a>e or d<s or b>n: continue
        if g.intersects(target) if bounds else g.covers(target):
            result.append({'id':str(f['properties']['objectid']),
                'onBoundary':g.boundary.covers(target) if not bounds else None,
                **({'intersectionM2':g.intersection(target).area} if bounds else {})})
    return result

class Reader:
    def __init__(self, init):
        start=time.perf_counter(); self.core=init['core']; self.values=None; self.features=None
        self.forward=Transformer.from_crs(27700,4326,always_xy=True)
        self.inverse=Transformer.from_crs(4326,27700,always_xy=True)
        out={'families':{}}
        for family,record in init['artifacts'].items():
            if record.get('status')=='unavailable':
                out['families'][family]=record; continue
            path=checked_file(record)
            if family=='worldcover':
                with rasterio.open(path) as ds:
                    self.values=ds.read(1);self.t=ds.transform;self.width=ds.width;self.height=ds.height
                    if ds.crs.to_string()!='EPSG:4326' or self.values.shape!=(334,554) or str(self.values.dtype)!='uint8' or list(self.t)!=init['gridTransform'] or ds.nodata!=0:
                        raise NativeError('unsupported-representation', 'Registered native grid differs from retained receipt')
                    codes=[int(v) for v in np.unique(self.values)]
                    if any(c not in [0,10,20,30,50,60,80,100] for c in codes):
                        raise NativeError('corrupt-native-code', 'Unbound native code')
                    rr,cc=np.indices(self.values.shape)
                    self.east,self.north=self.inverse.transform(self.t.c+(cc+.5)*self.t.a,self.t.f+(rr+.5)*self.t.e)
                    out['families'][family]={'status':'available','grid':{'shape':[ds.height,ds.width],'cells':int(self.values.size),'crs':ds.crs.to_string(),'transform':list(self.t),'bounds':list(ds.bounds),'nodata':ds.nodata,'dtype':str(self.values.dtype),'nativeCodes':codes,'sampling':'Native angular categorical grid; nominal10m is not semantic accuracy.'}}
            elif family=='nrw':
                native=json.loads(path.read_text(encoding='utf-8-sig'))
                if native.get('crs',{}).get('properties',{}).get('name')!='urn:ogc:def:crs:EPSG::27700':
                    raise NativeError('unsupported-representation','NRW CRS differs from retained native reference')
                self.features=[]; seen=set(); records=[]
                for f in sorted(native['features'],key=lambda f:int(f['properties']['objectid'])):
                    props=f['properties'];id=str(props['objectid']);g=shape(f['geometry'])
                    if id in seen or g.geom_type not in ['Polygon','MultiPolygon'] or g.is_empty or not g.is_valid or not all(math.isfinite(v) for v in g.bounds):
                        raise NativeError('invalid-native-geometry','Duplicate/invalid native feature '+id+': '+explain_validity(g))
                    if any(not (v is None or isinstance(v,(str,int,float,bool))) or isinstance(v,float) and not math.isfinite(v) for v in props.values()):
                        raise NativeError('corrupt-native-value','Non-scalar native property')
                    seen.add(id);self.features.append((f,g));records.append({'id':id,'native':props,'bounds':list(g.bounds)})
                if len(seen)!=193:raise NativeError('unsupported-representation','Frozen NRW feature count differs')
                out['families'][family]={'status':'available','records':records,'featureCount':len(records),'codeCount':len(set(r['native']['phase1_code'] for r in records)),'index':'Sorted193 bbox records; exact native geometry, no repair.'}
        self.inverse.transform(-4,53); op=self.inverse.get_last_used_operation()
        out['transform']={'runtime':'pyproj '+proj_version,'operation':op.description,'accuracyM':op.accuracy,'axisOrder':'xy','qualification':'Declared operation accuracy is not local imagery/terrain registration accuracy; no network grid acquisition.'}
        self.initial=out;self.metrics={'initializationMilliseconds':(time.perf_counter()-start)*1000,'rasterArrayBytes':0 if self.values is None else int(self.values.nbytes+self.east.nbytes+self.north.nbytes),'bboxCoordinatesBytes':0 if self.features is None else len(self.features)*4*8,'nativeGeometryWkbBytes':0 if self.features is None else sum(len(g.wkb) for _,g in self.features)}
    def display(self,q):
        if self.values is None or self.features is None:raise NativeError('artifact-unavailable','Display requires registered native evidence')
        palette=q['palette']; rgba=np.zeros((self.height,self.width,4),dtype=np.uint8)
        for code in np.unique(self.values):rgba[self.values==code]=palette[str(int(code))]
        w,s,e,n=self.core
        rgba[:,:,3]=np.where((self.east>=w)&(self.east<e)&(self.north>=s)&(self.north<n),rgba[:,:,3],0)
        def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
        scan=b''.join(b'\x00'+row.tobytes() for row in rgba)
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',self.width,self.height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(scan,9))+chunk(b'IEND',b'')
        def coordinates(c):
            if isinstance(c[0],(int,float)):return list(self.forward.transform(*c))
            return [coordinates(v) for v in c]
        features=[]
        for f,g in self.features:
            features.append({'type':'Feature','id':str(f['properties']['objectid']),
                'properties':{'native':f['properties'],'nativeSupport':{'crs':'EPSG:27700','geometry':f['geometry']}},
                'geometry':{'type':f['geometry']['type'],'coordinates':coordinates(f['geometry']['coordinates'])}})
        merc=Transformer.from_crs(27700,3857,always_xy=True)
        probes=[]
        for p in q['probes']:
            x,y=merc.transform(*p['centre']); z=14; size=40075016.68557849;tx=(x+size/2)/size*2**z;ty=(size/2-y)/size*2**z
            probes.append({'id':p['id'],'pointBNG':p['centre'],'pointCRS84':list(self.forward.transform(*p['centre'])),
                'mercator':[x,y],'xyz':{'z':z,'x':math.floor(tx),'y':math.floor(ty),'pixel':[(tx%1)*256,(ty%1)*256]}})
        return {'worldcoverPNG':base64.b64encode(png).decode('ascii'),'nrw':{'type':'FeatureCollection','features':features},'probes':probes}
    def query(self,q):
        x,y=q['point']; crs=q['crs']
        if crs=='OGC:CRS84':
            lon,lat=x,y;x,y=self.inverse.transform(lon,lat)
        else:lon,lat=self.forward.transform(x,y)
        if not all(math.isfinite(v) for v in [x,y,lon,lat]):raise NativeError('invalid-coordinate','Transform produced nonfinite coordinate')
        w,s,e,n=self.core
        out={'pointBNG':[x,y],'pointCRS84':[lon,lat],'insideCore':w<=x<e and s<=y<n}
        if not out['insideCore']:return out
        bounds=q.get('support')
        if bounds and not(w<=bounds[0]<bounds[2]<=e and s<=bounds[1]<bounds[3]<=n):
            raise NativeError('invalid-support','Support must be finite ordered BNG rectangle inside core')
        if self.values is not None:
            idx=cell_index(self.t,lon,lat,self.width,self.height)
            if idx:
                r,c=idx;left,top=self.t*(c,r);right,bottom=self.t*(c+1,r+1)
                out['worldcover']={'row':r,'column':c,'parentRow':r+10464,'parentColumn':c+23753,'code':int(self.values[r,c]),'cellBounds':[left,bottom,right,top]}
            else:out['worldcover']={'gap':'outside-support'}
            if bounds:
                m=(self.east>=bounds[0])&(self.east<bounds[2])&(self.north>=bounds[1])&(self.north<bounds[3]);co,cn=np.unique(self.values[m],return_counts=True)
                out['worldcoverSupport']={'bounds':bounds,'crs':'EPSG:27700','cells':int(m.sum()),'counts':{str(int(k)):int(v) for k,v in zip(co,cn)},'selection':'Native cell centres inside half-open BNG rectangle; no resampling','meaning':'Assignment counts, not physical fractions; edge-only intersections excluded.'}
        if self.features is not None:out['nrw']=members(self.features,x,y,bounds)
        return out

def main():
    reader=None
    for line in sys.stdin:
        try:
            request=json.loads(line)
            if request['operation']=='init':
                if reader is not None:raise NativeError('invalid-request','Already initialized')
                reader=Reader(request);value={'metadata':reader.initial,'metrics':reader.metrics}
            elif request['operation']=='query' and reader is not None:value=reader.query(request)
            elif request['operation']=='display' and reader is not None:value=reader.display(request)
            else:raise NativeError('invalid-request','Unsupported worker operation')
            answer={'value':value}
        except Exception as e:answer={'error':{'code':getattr(e,'code','native-reader-error'),'message':str(e)}}
        print(json.dumps(answer,ensure_ascii=False,sort_keys=True,allow_nan=False),flush=True)
if __name__=='__main__':main()
