"""One existing-kernel binding; no custom geometry maths or scientific authority."""
import ctypes as C
import hashlib
from importlib.metadata import distribution
import json
import math
import os
from pathlib import Path
from contextlib import contextmanager

class GeometryError(RuntimeError):
    pass

MESSAGE = C.CFUNCTYPE(None, C.c_char_p, C.c_void_p)
TRANSFORM = C.CFUNCTYPE(C.c_int, C.POINTER(C.c_double), C.POINTER(C.c_double), C.c_void_p)
TYPES = ('Point','LineString','LinearRing','Polygon','MultiPoint','MultiLineString','MultiPolygon','GeometryCollection')
MAX_WKB = 16 * 1024 * 1024

class Geometry:
    """Owned pointer and allocation token; borrowed children never escape as wrappers."""
    def __init__(self, owner, pointer, token):
        self.owner, self.pointer, self.token = owner, pointer, token

    def checked(self):
        if self.owner.closed or self.owner.owned.get(self.pointer) != self.token:
            raise GeometryError('Geometry is closed or no longer owned.')
        return self.pointer

    def close(self):
        if not self.owner.closed and self.owner.owned.get(self.pointer) == self.token:
            self.owner.lib.GEOSGeom_destroy_r(self.owner.ctx,self.pointer)
            del self.owner.owned[self.pointer]
        self.pointer = None

    def __del__(self):
        self.close()

    @property
    def geom_type(self):
        index = self.owner.call('GEOSGeomTypeId_r',self.checked())
        if not 0 <= index < len(TYPES): raise GeometryError('Unsupported geometry type.')
        return TYPES[index]

    @property
    def is_empty(self): return self.owner.predicate('GEOSisEmpty_r',self)
    @property
    def is_valid(self): return self.owner.predicate('GEOSisValid_r',self)
    @property
    def area(self): return self.owner.scalar('GEOSArea_r',self)
    @property
    def x(self): return self.owner.scalar('GEOSGeomGetX_r',self)
    @property
    def y(self): return self.owner.scalar('GEOSGeomGetY_r',self)

    @property
    def bounds(self):
        if self.is_empty: return (math.nan,)*4
        values=[C.c_double() for _ in range(4)]
        ok=self.owner.call('GEOSGeom_getExtent_r',self.checked(),*[C.byref(v) for v in values])
        self.owner.require(ok == 1,'Geometry bounds failed.')
        return tuple(v.value for v in values)

    def covers(self, other): return self.owner.predicate('GEOSCovers_r',self,other)
    def intersection(self, other):
        return self.owner.adopt(self.owner.call('GEOSIntersection_r',self.checked(),self.owner.argument(other)))

    @property
    def wkb(self): return self.owner.wkb(self)
    @property
    def __geo_interface__(self): return self.owner.mapping(self)

class NativeGeos:
    """Independent sequential re-entrant context, with explicit native ownership."""
    def __init__(self):
        if os.name != 'nt': raise GeometryError('Only the inventoried Windows binding is tested.')
        wheel=distribution('shapely')
        if wheel.version != '2.1.2': raise GeometryError('Installed wheel version requires review.')
        folder=Path(wheel.locate_file('shapely.libs')).resolve()
        libraries=list(folder.glob('geos_c-*.dll'))
        if len(libraries) != 1: raise GeometryError('Exact local GEOS C library unavailable.')
        self.directory_handle=os.add_dll_directory(str(folder))
        self.lib=C.CDLL(str(libraries[0])); self.ctx=None; self.closed=True
        self.owned={};self.serial=0;self.errors=[];self.notices=[]
        self.json_reader=self.wkb_reader=self.wkb_writer=None
        p,i,u,d,s,n=C.c_void_p,C.c_int,C.c_uint,C.c_double,C.c_char_p,C.c_size_t
        def bind(name,result,args):
            fn=getattr(self.lib,name);fn.restype=result;fn.argtypes=args
        bind('GEOSversion',s,[])
        bind('GEOS_init_r',p,[]);bind('GEOS_finish_r',None,[p])
        bind('GEOSContext_setErrorMessageHandler_r',p,[p,MESSAGE,p])
        bind('GEOSContext_setNoticeMessageHandler_r',p,[p,MESSAGE,p])
        bind('GEOSGeom_destroy_r',None,[p,p]);bind('GEOSFree_r',None,[p,p])
        bind('GEOSGeom_createPointFromXY_r',p,[p,d,d]);bind('GEOSGeom_createEmptyPolygon_r',p,[p])
        for prefix in ['GEOSGeoJSONReader','GEOSWKBReader','GEOSWKBWriter']:
            bind(prefix+'_create_r',p,[p]);bind(prefix+'_destroy_r',None,[p,p])
        bind('GEOSGeoJSONReader_readGeometry_r',p,[p,p,s])
        bind('GEOSWKBReader_read_r',p,[p,p,p,n])
        bind('GEOSWKBWriter_write_r',p,[p,p,p,C.POINTER(n)])
        for name in ['setOutputDimension','setByteOrder','setFlavor']:
            bind('GEOSWKBWriter_'+name+'_r',None,[p,p,i])
        bind('GEOSWKBWriter_setIncludeSRID_r',None,[p,p,C.c_ubyte])
        for name in ['GEOSGeomTypeId_r','GEOSGetNumGeometries_r','GEOSGetNumInteriorRings_r','GEOSGeom_getCoordinateDimension_r']:
            bind(name,i,[p,p])
        for name in ['GEOSisEmpty_r','GEOSisValid_r','GEOSHasM_r']: bind(name,C.c_ubyte,[p,p])
        bind('GEOSCovers_r',C.c_ubyte,[p,p,p]);bind('GEOSIntersection_r',p,[p,p,p])
        for name in ['GEOSArea_r','GEOSGeomGetX_r','GEOSGeomGetY_r']:
            bind(name,i,[p,p,C.POINTER(d)])
        bind('GEOSGeom_getExtent_r',i,[p,p]+[C.POINTER(d)]*4)
        bind('GEOSGetExteriorRing_r',p,[p,p]);bind('GEOSGetInteriorRingN_r',p,[p,p,i])
        bind('GEOSGetGeometryN_r',p,[p,p,i]);bind('GEOSGeom_getCoordSeq_r',p,[p,p])
        bind('GEOSCoordSeq_getSize_r',i,[p,p,C.POINTER(u)])
        bind('GEOSCoordSeq_getDimensions_r',i,[p,p,C.POINTER(u)])
        bind('GEOSCoordSeq_getOrdinate_r',i,[p,p,u,u,C.POINTER(d)])
        bind('GEOSGeom_transformXY_r',p,[p,p,TRANSFORM,p])
        bind('GEOSPrepare_r',p,[p,p]);bind('GEOSPreparedGeom_destroy_r',None,[p,p])
        bind('GEOSPreparedCovers_r',C.c_ubyte,[p,p,p])
        version=self.lib.GEOSversion().decode()
        if version != '3.13.1-CAPI-1.19.2':
            self.directory_handle.close();raise GeometryError('GEOS version requires explicit review.')
        self.identity={'version':version,'libraries':[{'name':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(folder.glob('*.dll'))]}
        def message(target):
            def callback(raw,_):
                # A Python exception must never escape through a C callback.
                try: target.append(raw.decode('utf-8',errors='replace')[:4096]);del target[:-16]
                except Exception: pass
            return MESSAGE(callback)
        self.error_callback=message(self.errors);self.notice_callback=message(self.notices)
        try:
            self.ctx=self.lib.GEOS_init_r()
            if not self.ctx: raise GeometryError('Context allocation failed.')
            self.closed=False
            self.lib.GEOSContext_setErrorMessageHandler_r(self.ctx,self.error_callback,None)
            self.lib.GEOSContext_setNoticeMessageHandler_r(self.ctx,self.notice_callback,None)
            self.json_reader=self.call('GEOSGeoJSONReader_create_r')
            self.wkb_reader=self.call('GEOSWKBReader_create_r')
            self.wkb_writer=self.call('GEOSWKBWriter_create_r')
            self.require(all([self.json_reader,self.wkb_reader,self.wkb_writer]),'Serialiser allocation failed.')
            for name,value in [('setByteOrder',1),('setFlavor',1),('setIncludeSRID',0)]:
                self.call('GEOSWKBWriter_'+name+'_r',self.wkb_writer,value)
        except Exception: self.close();raise

    def call(self,name,*args):
        if self.closed: raise GeometryError('Native context is closed.')
        self.errors.clear()
        return getattr(self.lib,name)(self.ctx,*args)

    def require(self,ok,message):
        if not ok: raise GeometryError(message+(' '+self.errors[-1] if self.errors else ''))

    def adopt(self,pointer):
        self.require(bool(pointer),'Native geometry operation failed.')
        self.serial+=1;self.owned[pointer]=self.serial
        return Geometry(self,pointer,self.serial)

    def argument(self,g):
        if not isinstance(g,Geometry) or g.owner is not self: raise GeometryError('Cross-context geometry is forbidden; interchange serialised bytes.')
        return g.checked()

    def scalar(self,name,g):
        value=C.c_double();self.require(self.call(name,self.argument(g),C.byref(value))==1,'Scalar operation failed.')
        return value.value

    def predicate(self,name,*geometries):
        result=self.call(name,*[self.argument(g) for g in geometries])
        self.require(result in (0,1),'Predicate failed; not false evidence.')
        return bool(result)

    def point(self,*args):
        xy=args[0] if len(args)==1 else args
        if len(xy)!=2 or not all(math.isfinite(v) for v in xy): raise GeometryError('Finite XY point required; no implicit Z.')
        return self.adopt(self.call('GEOSGeom_createPointFromXY_r',*xy))

    def polygon(self,shell=None,holes=None):
        if shell is None or len(shell)==0: return self.adopt(self.call('GEOSGeom_createEmptyPolygon_r'))
        rings=[]
        for source in [shell]+list(holes or []):
            ring=[list(p) for p in source]
            if len(ring)<3 or any(len(p)!=2 or not all(math.isfinite(v) for v in p) for p in ring):
                raise GeometryError('Bounded polygon constructor accepts finite XY rings.')
            if ring[0]!=ring[-1]:ring.append(ring[0][:])
            rings.append(ring)
        return self.from_json({'type':'Polygon','coordinates':rings})

    def box(self,x0,y0,x1,y1):
        # Preserve the reference constructor's CCW starting vertex, not just topology.
        return self.polygon([(x1,y0),(x1,y1),(x0,y1),(x0,y0),(x1,y0)])

    def from_json(self,data):
        # Query construction is XY only. Full native XYZ features use WKB interchange.
        def xy(value):
            if isinstance(value,(list,tuple)) and value and isinstance(value[0],(int,float)):
                if len(value)!=2 or not all(math.isfinite(v) for v in value):raise GeometryError('GeoJSON constructor is XY only.')
            elif isinstance(value,(list,tuple)):
                for v in value:xy(v)
            else:raise GeometryError('Malformed geometry coordinates.')
        if not isinstance(data,dict) or data.get('type') not in ['Point','LineString','Polygon','MultiPoint','MultiLineString','MultiPolygon']:raise GeometryError('Unsupported GeoJSON constructor.')
        xy(data.get('coordinates'))
        raw=json.dumps(data,allow_nan=False,separators=(',',':')).encode()
        if len(raw)>MAX_WKB:raise GeometryError('Geometry input exceeds bound.')
        return self.adopt(self.call('GEOSGeoJSONReader_readGeometry_r',self.json_reader,raw))

    def from_wkb(self,raw):
        if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_WKB:raise GeometryError('Bounded WKB bytes required.')
        buffer=C.create_string_buffer(raw)
        g=self.adopt(self.call('GEOSWKBReader_read_r',self.wkb_reader,buffer,len(raw)))
        if self.call('GEOSGeom_getCoordinateDimension_r',g.checked()) not in (2,3) or self.predicate('GEOSHasM_r',g):
            g.close();raise GeometryError('Only retained XY/XYZ interchange is supported.')
        return g

    def wkb(self,g):
        dim=self.call('GEOSGeom_getCoordinateDimension_r',self.argument(g))
        self.require(dim in (2,3),'Unsupported geometry dimensionality.')
        self.call('GEOSWKBWriter_setOutputDimension_r',self.wkb_writer,dim)
        size=C.c_size_t();pointer=self.call('GEOSWKBWriter_write_r',self.wkb_writer,g.checked(),C.byref(size))
        self.require(bool(pointer),'WKB serialisation failed.')
        try:
            self.require(size.value<=MAX_WKB,'WKB exceeds bound.')
            return C.string_at(pointer,size.value)
        finally:self.lib.GEOSFree_r(self.ctx,pointer)

    def mapping(self,g):
        pointer=self.argument(g)
        def coordinates(p):
            seq=self.call('GEOSGeom_getCoordSeq_r',p);self.require(bool(seq),'Coordinate sequence unavailable.')
            size=C.c_uint();dims=C.c_uint()
            self.require(self.call('GEOSCoordSeq_getSize_r',seq,C.byref(size))==1 and self.call('GEOSCoordSeq_getDimensions_r',seq,C.byref(dims))==1,'Coordinate access failed.')
            self.require(size.value<=100000 and dims.value in (2,3),'Coordinate extent unsupported.')
            result=[]
            for index in range(size.value):
                row=[]
                for dim in range(dims.value):
                    value=C.c_double();self.require(self.call('GEOSCoordSeq_getOrdinate_r',seq,index,dim,C.byref(value))==1,'Ordinate access failed.');row.append(value.value)
                result.append(tuple(row))
            return tuple(result)
        def visit(p):
            self.require(bool(p),'Borrowed component unavailable.')
            kind=self.call('GEOSGeomTypeId_r',p);self.require(0<=kind<len(TYPES),'Geometry type unsupported.')
            name=TYPES[kind]
            if kind in (0,1,2):
                values=coordinates(p);return {'type':name,'coordinates':values[0] if kind==0 and values else values}
            if kind==3:
                ring=self.call('GEOSGetExteriorRing_r',p)
                if not ring or not coordinates(ring):return {'type':name,'coordinates':()}
                count=self.call('GEOSGetNumInteriorRings_r',p);self.require(count>=0,'Hole access failed.')
                rings=[coordinates(ring)]+[coordinates(self.call('GEOSGetInteriorRingN_r',p,k)) for k in range(count)]
                return {'type':name,'coordinates':tuple(rings)}
            count=self.call('GEOSGetNumGeometries_r',p);self.require(count>=0,'Component access failed.')
            parts=[visit(self.call('GEOSGetGeometryN_r',p,k)) for k in range(count)]
            return {'type':name,'geometries':parts} if kind==7 else {'type':name,'coordinates':[v['coordinates'] for v in parts] if kind==6 else tuple(v['coordinates'] for v in parts)}
        return visit(pointer)

    def projected(self,g,source,target,proj):
        self.argument(g)
        if source==target:return g
        failures=[]
        def transform(x,y,_):
            try:
                xx,yy=proj.xy([x[0]],[y[0]],source,target);x[0],y[0]=xx[0],yy[0];return 1
            except Exception as error:failures.append(str(error));return 0
        callback=TRANSFORM(transform)
        pointer=self.call('GEOSGeom_transformXY_r',g.checked(),callback,None)
        if failures:
            if pointer:self.lib.GEOSGeom_destroy_r(self.ctx,pointer)
            raise GeometryError('CRS callback failed: '+failures[0])
        return self.adopt(pointer)

    def covers_points(self,g,xs,ys):
        import numpy as np
        xs,ys=np.asarray(xs),np.asarray(ys)
        if xs.shape!=ys.shape or xs.size>100000:raise GeometryError('Aligned bounded centre arrays required.')
        prepared=self.call('GEOSPrepare_r',self.argument(g));self.require(bool(prepared),'Prepared geometry failed.')
        try:
            answer=np.empty(xs.shape,dtype=bool)
            for k,(x,y) in enumerate(zip(xs.flat,ys.flat)):
                with self.temporary_point(float(x),float(y)) as point:
                    result=self.call('GEOSPreparedCovers_r',prepared,point.checked())
                    self.require(result in (0,1),'Centre predicate failed.');answer.flat[k]=bool(result)
        finally:self.lib.GEOSPreparedGeom_destroy_r(self.ctx,prepared)
        return answer

    @contextmanager
    def temporary_point(self,x,y):
        point=self.point(x,y)
        try:yield point
        finally:point.close()

    @contextmanager
    def arena(self):
        before=self.owned.copy()
        try:yield
        finally:
            for pointer,token in list(self.owned.items()):
                if before.get(pointer)!=token:
                    self.lib.GEOSGeom_destroy_r(self.ctx,pointer);del self.owned[pointer]

    def close(self):
        if not self.closed:
            for pointer in list(self.owned):self.lib.GEOSGeom_destroy_r(self.ctx,pointer)
            self.owned.clear()
            for name,pointer in [('GEOSGeoJSONReader',self.json_reader),('GEOSWKBReader',self.wkb_reader),('GEOSWKBWriter',self.wkb_writer)]:
                if pointer:getattr(self.lib,name+'_destroy_r')(self.ctx,pointer)
            self.lib.GEOS_finish_r(self.ctx);self.ctx=None;self.closed=True
        if self.directory_handle is not None:self.directory_handle.close();self.directory_handle=None

    def __enter__(self):return self
    def __exit__(self,*_):self.close()
