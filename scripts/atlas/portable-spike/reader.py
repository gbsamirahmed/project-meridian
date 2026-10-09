"""Independent finite-profile reader. No Atlas, fixture or network query imports."""
from pathlib import Path
import copy
import datetime
import hashlib
import json
import math
import re
import time
import numpy as np
import pyproj
import rasterio
from rasterio.windows import Window
from shapely.geometry import Point, Polygon, box, mapping, shape
from shapely.ops import transform
import shapely

pyproj.network.set_network_enabled(False)

class ReadError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

def require(ok, code, message):
    if not ok:
        raise ReadError(code, message)

def canonical(value, level=0):
    """Reference pretty identity encoding, independently serialised; not a transport."""
    if isinstance(value, float):
        require(math.isfinite(value), 'projection-integrity', 'Nonfinite JSON number.')
        if value == 0: return '0'
        text = repr(value)
        if 1e-6 <= abs(value) < 1e21:
            if 'e' in text:
                from decimal import Decimal
                text = format(Decimal(text), 'f')
            return text[:-2] if text.endswith('.0') else text
        text = text.replace('.0e', 'e')
        return re.sub(r'e([+-])0+(\d+)', r'e\1\2', text)
    if isinstance(value, list) or isinstance(value, dict):
        if not value: return '[]' if isinstance(value,list) else '{}'
        indent = '  ' * (level+1)
        if isinstance(value,list): parts = [canonical(v,level+1) for v in value]
        else:
            # JSON.stringify enumerates array-index object keys numerically first.
            indexed = lambda k: k.isascii() and k.isdigit() and str(int(k)) == k and int(k) < 4294967295
            keys = sorted(value, key=lambda k: (0,int(k)) if indexed(k) else (1,k.encode('utf-16-be')))
            parts = [json.dumps(k,ensure_ascii=False)+': '+canonical(value[k],level+1) for k in keys]
        a,b = ('[',']') if isinstance(value,list) else ('{','}')
        return a+'\n'+indent+(',\n'+indent).join(parts)+'\n'+'  '*level+b
    return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':'))

def identity(value):
    return hashlib.sha256((canonical(value)+'\n').encode()).hexdigest()

def projected(geometry,source,target):
    if source == target: return geometry
    return transform(pyproj.Transformer.from_crs(source,target,always_xy=True).transform,geometry)

def finite_numbers(v,n):
    return isinstance(v,list) and len(v)==n and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in v)

class Reader:
    def __init__(self, root, generation, expected_projection=None):
        from verification import Snapshot
        start=time.perf_counter(); self.root=Path(root).absolute(); self.closed=True
        self.snapshot=getattr(self, "snapshot_type", Snapshot)(self.root, expected_projection)
        try:
            self.manifest=self.snapshot.manifest
            require(isinstance(generation,str) and generation in self.snapshot.generations,'projection-generation','Selected generation is unavailable; no fallback.')
            data=self.snapshot.generations[generation]
            self.base=data['answer']; self.pool=self.base['documents']; self.knowledge=data['knowledge']
            self.records={r['key']:r for r in self.base['results']}
            self.selectors={s['key']:s for s in data['selectors']}
            self.features={k:shape(f['native']['geometry']) for k,f in self.snapshot.features.items()}
            self.worldcover=self.snapshot.worldcover; self.edges=self.base['relationships']
            self.generation=generation; self.closed=False
            self.startup_ms=(time.perf_counter()-start)*1000
        except Exception:
            self.snapshot.close()
            raise

    def close(self):
        self.snapshot.close(); self.closed=True

    def __enter__(self): return self

    def __exit__(self, *_): self.close()

    def validate(self,q):
        need=lambda ok,msg: require(ok,'query-invalid',msg)
        need(isinstance(q,dict),'Query must be a structured object.')
        need(q.get('region') in [None,'tryfan','riffelhorn','exe'],'Unknown region; no fallback.')
        for k in ['identity','feature','product']:
            if k in q: need(isinstance(q[k],str) and bool(q[k]),'Expected a nonempty '+k+' identity.')
        need(not('point' in q and 'area' in q),'Point and area are exclusive.')
        if 'point' in q or 'area' in q:
            need(q.get('region') is not None,'Spatial queries require an explicit region and native query CRS.')
            for k,n in [('point',2),('area',4)]:
                if k in q:
                    need(finite_numbers(q[k],n),'Invalid finite spatial support.')
                    if k=='area': need(q[k][0]<q[k][2] and q[k][1]<q[k][3],'Area bounds must be ordered.')
            need(q.get('crs') in ['EPSG:2056','EPSG:4326','OGC:CRS84'],'Explicit supported query CRS required; no inferred CRS.')
            require(q['region']=='riffelhorn','profile-unsupported','Only Riffelhorn spatial selection is projected.')
        elif 'crs' in q: need(False,'CRS requires point or area.')
        if 'time' in q:
            t=q['time']; need(isinstance(t,dict) and t.get('role') in ['evidence-epoch','product-reference'],'Unsupported time role.')
            if t.get('unknown') is True: need(set(t)=={'role','unknown'},'Unknown is distinct from a dated interval.')
            else: need(set(t)=={'role','start','end'} and all(isinstance(t[k],int) and not isinstance(t[k],bool) and 1<=t[k]<=9999 for k in ['start','end']) and t['start']<=t['end'],'Only inclusive calendar-year qualification is supported in this adapter.')
        need(not set(q)-{'region','identity','feature','product','point','area','crs','time','families','representation','evidenceClass','revision','spatialSupport','knowledge','relatedTo'},'Unsupported qualified predicates.')
        need(q.get('evidenceClass') in [None,'source','derived'] and q.get('representation') in [None,'vector','raster','source-product-metadata','local-scalar','native-cell-summary'],'Unsupported evidence class/representation.')
        if 'families' in q: need(isinstance(q['families'],list) and bool(q['families']) and all(isinstance(f,str) and f in {r['family'] for r in self.records.values()} for f in q['families']),'Unsupported family.')
        if 'revision' in q: need(isinstance(q['revision'],str) and bool(re.fullmatch('[0-9a-f]{64}',q['revision'])),'Revision must be an exact SHA256.')
        need(q.get('spatialSupport') in [None,'location','consumed'] and ('spatialSupport' not in q or ('point' in q or 'area' in q)) and (q.get('spatialSupport')!='consumed' or q.get('evidenceClass')=='derived'),'Consumed support requires a derived spatial query; scalar location is not a patch.')
        if 'knowledge' in q:
            k=q['knowledge']; need(isinstance(k,dict),'Invalid knowledge qualification.')
            if set(k)=={'unknown'}: need(k['unknown'] is True,'Unknown must be explicit.')
            elif set(k)=={'revision'}: need(isinstance(k['revision'],str) and bool(re.fullmatch('[0-9a-f]{64}',k['revision'])),'Exact active registration revision required.')
            else:
                need(set(k)=={'start','end'},'Closed knowledge UTC interval required; open/ambiguous intervals unsupported.')
                for value in k.values():
                    need(isinstance(value,str),'Invalid knowledge timestamp.')
                    try: valid=datetime.datetime.strptime(value,'%Y-%m-%dT%H:%M:%S.%fZ').isoformat(timespec='milliseconds')+'Z'==value
                    except ValueError: valid=False
                    need(valid,'Use exact UTC millisecond knowledge timestamps, not physical dates.')
                need(k['start']<=k['end'],'Knowledge interval unordered.')
        if 'relatedTo' in q:
            t=q['relatedTo']; need(isinstance(t,dict) and set(t)=={'identity','direction','depth'} and t['direction'] in ['inputs','dependents'] and t['depth'] in ['direct','transitive'],'Invalid relationship traversal.')
            require(any(r['identity']==t['identity'] for r in self.records.values()),'relationship-missing','Selected relationship identity is absent from this pin.')

    def geometry(self,q):
        if 'point' not in q and 'area' not in q: return None
        if 'point' in q: g=Point(q['point'])
        else:
            x0,y0,x1,y1=q['area']; ring=[]
            for a,b in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
                ring.extend((a[0]+(b[0]-a[0])*n/32,a[1]+(b[1]-a[1])*n/32) for n in range(32))
            g=Polygon(ring)
        g=projected(g,'EPSG:4326' if q['crs']=='OGC:CRS84' else q['crs'],'EPSG:2056').intersection(box(*self.manifest['core']))
        if g.geom_type!='Point' and g.area==0: g=Polygon()
        return g

    def closure(self,t):
        seeds={r['key'] for r in self.records.values() if r['identity']==t['identity']}
        front=seeds; reached=set(); forward=t['direction']=='dependents'; a,b=('from','to') if forward else ('to','from')
        while front:
            next_keys={e[b] for e in self.edges if e[a] in front}-reached
            reached.update(next_keys)
            if t['depth']=='direct': break
            front=next_keys
        reached-=seeds
        edges=[e['identity'] for e in self.edges if e[a] in seeds|reached and e[b] in reached]
        return reached,edges

    def matches(self,r,q):
        for k in ['identity','region','evidenceClass','representation','revision']:
            if k in q and q[k]!=r[k]: return False
        body=self.pool[r['evidenceRef']]
        product=body.get('productSelector',body.get('methodRevision',r['identity']))
        if 'product' in q and q['product']!=product: return False
        if 'feature' in q and (r['evidenceClass']=='derived' or r['representation']!='vector' or q['feature']!=r['identity']): return False
        if 'families' in q and r['family'] not in q['families']: return False
        if 'time' in q:
            t=q['time']; v=r['temporal'][t['role']]
            if t.get('unknown'):
                if v['status']!='unknown': return False
            elif v['status']!='known' or not t['start']<=v['year']<=t['end']: return False
        if 'knowledge' in q:
            k=q['knowledge']; v=self.knowledge[r['region']]
            if k.get('unknown'): return v is None
            if v is None: return False
            if 'revision' in k: return k['revision']==v['revision']
            return k['start']<=v['acceptedAt']<=k['end']
        return True

    def raster(self,r,g,body):
        binding=body['detail']['binding']; native=binding['native']; crs=native['crs']
        g=projected(g,'EPSG:2056',crs); affine=rasterio.Affine(*native['transform'][:6]); height,width=native['shape']
        if g.geom_type=='Point':
            col,row=(~affine)*(g.x,g.y); row,col=math.floor(row),math.floor(col)
            if not(0<=row<height and 0<=col<width): return None
            selection={'kind':'native-cell','row':row,'column':col,'crs':crs,'point':[g.x,g.y]}; window=Window(col,row,1,1)
        else:
            if box(*native['bounds']).intersection(g).area<=0: return None
            x0,y0,x1,y1=g.bounds; c0,r0=(~affine)*(x0,y1); c1,r1=(~affine)*(x1,y0)
            left,top=max(0,math.floor(c0)),max(0,math.floor(r0)); right,bottom=min(width,math.ceil(c1)),min(height,math.ceil(r1))
            selection={'kind':'native-window-candidates','window':[left,top,max(0,right-left),max(0,bottom-top)],'crs':crs,'exactQueryPolygon':json.loads(json.dumps(mapping(g))),'meaning':'conservative native window; not assertion that every pixel intersects query; height samples not bulk materialized'}
            window=Window(*selection['window'])
        if selection['kind']!='native-cell' and r['family']!='worldcover':
            payload={'kind':'support-selection','selection':selection,'value':'not requested; no height aggregation/interpolation'}
        else:
            with self.snapshot.rasters[self.manifest['rasterFiles'][r['identity']]].open(driver='GTiff') as src:
                require(str(src.crs)==crs and list(src.shape)==native['shape'] and list(src.transform)==native['transform'],'projection-integrity','Native raster header differs.')
                values=src.read(1,window=window)
                if selection['kind']=='native-cell':
                    value=float(values[0,0]); nodata=not math.isfinite(value) or value==src.nodata
                    if r['family']=='worldcover':
                        code=int(value); collection=self.worldcover
                        claim=next((c for c in collection['claims'] if c['native']['fields']['code']==code),None)
                        require(claim is not None,'projection-integrity','Unbound native WorldCover classification.')
                        payload={'kind':'gap' if nodata else 'native-category','reason':'no-observation' if nodata else None,'nativeCode':code,'nativeClaim':claim,'selection':selection,'physicalAbsenceInferred':False}
                    else:
                        payload={'kind':'gap' if nodata else 'native-height','reason':'no-observation' if nodata else None,'nativeValue':None if nodata else value,'selection':selection,'unit':{'status':'unknown','reason':'unit not explicitly declared in prepared raster binding; provider records remain referenced; do not infer from CRS'},'vertical':body['qualification']['vertical'],'physicalAccuracy':'not established by grid spacing'}
                else:
                    aff=src.window_transform(window); rows,cols=np.indices(values.shape); xs=aff.c+(cols+.5)*aff.a; ys=aff.f+(rows+.5)*aff.e
                    selected=values[shapely.covers(g,shapely.points(xs,ys))]; codes,counts=np.unique(selected,return_counts=True)
                    payload={'kind':'native-classification-counts','counts':{str(int(k)):int(n) for k,n in zip(codes,counts)},'selectedCellCentres':int(selected.size),'selection':selection,'countMeaning':'sampled native cell centres within qualified query, not physical area fractions or confidence','emptyMeaning':'no sampled cell centre; not physical absence'}
        result=copy.deepcopy(body); result['detail']['selection']=selection; result['detail']['payload']=payload
        return result

    def read(self,q):
        require(not self.closed,'projection-closed','Reader snapshot is closed.')
        self.validate(q); g=self.geometry(q)
        reached, traversed=self.closure(q['relatedTo']) if 'relatedTo' in q else (None,[])
        documents={ref:self.pool[ref] for region in self.base['regions'].values() for ref in region.values() if ref is not None}
        results=[]
        for key,r in sorted(self.records.items()):
            if not self.matches(r,q) or (reached is not None and key not in reached): continue
            body=self.pool[r['evidenceRef']]
            if g is not None:
                if g.is_empty: continue
                if r['representation']=='vector':
                    geom=self.features[r['identity']]
                    if not (geom.covers(g) if g.geom_type=='Point' else geom.intersection(g).area>0): continue
                elif r['representation']=='raster':
                    body=self.raster(r,g,body)
                    if body is None: continue
                elif r['representation']=='local-scalar':
                    s=self.selectors[key]
                    if q.get('spatialSupport')=='consumed':
                        ok=any((x-.25<=g.x<x+.25 and y-.25<=g.y<y+.25) if g.geom_type=='Point' else box(x-.25,y-.25,x+.25,y+.25).intersection(g).area>0 for x,y in s['cells'])
                    else:
                        x,y=s['point']; ok=(g.x==x and g.y==y) if g.geom_type=='Point' else g.covers(Point(x,y)) and x<g.bounds[2] and y<g.bounds[3]
                    if not ok: continue
                else: continue
            selected=copy.deepcopy(r)
            selected['evidenceRef']=identity(body); documents[selected['evidenceRef']]=body
            for field in ['qualificationRef','rightsRef','provenanceRef']:
                ref=r[field]; documents[ref]=self.pool[ref]
            provenance=documents[r['provenanceRef']]
            if 'executionRef' in provenance: documents[provenance['executionRef']]=self.pool[provenance['executionRef']]
            results.append(selected)
        wanted=set(traversed)|{ref for r in results for ref in r['relationshipRefs']}
        answer = {'schema':self.base['schema'],'generation':self.generation,'members':self.base['members'],'results':results,
                'relationships':[e for e in self.edges if e['identity'] in wanted],'documents':documents,'regions':self.base['regions'],
                'traversal':{'selection':q['relatedTo'],'relationshipRefs':traversed} if 'relatedTo' in q else None,
                'gap':None if results else {'reason':'no-matching-qualified-evidence','physicalAbsenceInferred':False}}

        # Returned data cannot mutate the pinned reader's qualified records/documents.
        return copy.deepcopy(answer)

    def outcome(self,q):
        try: return {'kind':'answer','value':self.read(q)}
        except ReadError as e: return {'kind':'error','code':e.code,'message':str(e)}


def main():
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--projection',required=True); parser.add_argument('--generation',required=True); parser.add_argument('--query',required=True); parser.add_argument('--identity')
    args=parser.parse_args()
    try:
        with Reader(args.projection,args.generation,args.identity) as reader:
            result=reader.outcome(json.loads(args.query))
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
        return 1 if result['kind']=='error' else 0
    except (ReadError,OSError,ValueError) as error:
        print(json.dumps({'kind':'error','code':error.code if isinstance(error,ReadError) else 'query-malformed','message':str(error) if isinstance(error,ReadError) else 'Use a valid JSON query and available projection.'})); return 1

if __name__=='__main__':
    import sys
    sys.exit(main())
