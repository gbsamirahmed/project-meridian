"""Offline same-level corridor feasibility, never an elevation reconciliation.

Planar grid cycles are tested through their dual: a permitted enclosing cycle
exists iff absent primal edges do not give an interior-to-exterior dual path.
No third-party graph dependency, prescribed ring or confidence/weighted score.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def edge_masks(eligible, difference, threshold):
    a = eligible & np.isfinite(difference) & (np.abs(difference) <= threshold)
    return a[:, :-1] & a[:, 1:], a[:-1] & a[1:]


def dual_flood(horizontal, vertical, seed):
    """Absent graph edges are traversable dual edges; return a certificate.

    A face (r,c) has four primal boundary edges. Reaching the exterior across
    an absent perimeter edge proves no eligible cycle separates the seed.
    Fixed N/E/S/W order provides deterministic shortest-hop failure witnesses.
    """
    rows, cols = vertical.shape[0], horizontal.shape[1]
    if horizontal.shape != (rows + 1, cols) or vertical.shape != (rows, cols + 1):
        raise ValueError('Primal edge arrays have incompatible shapes')
    r, c = seed
    if not (0 <= r < rows and 0 <= c < cols):
        raise ValueError('Seed face outside graph')
    previous = np.full(rows * cols, -2, dtype=np.int32)
    initial = r * cols + c
    previous[initial] = -1
    queue = deque([initial])
    while queue:
        i = queue.popleft(); r, c = divmod(i, cols)
        neighbors = ((r-1,c,horizontal[r,c]), (r,c+1,vertical[r,c+1]),
                     (r+1,c,horizontal[r+1,c]), (r,c-1,vertical[r,c]))
        for rr, cc, blocked in neighbors:
            if blocked:
                continue
            if not (0 <= rr < rows and 0 <= cc < cols):
                path = [i]
                while previous[path[-1]] >= 0:
                    path.append(int(previous[path[-1]]))
                path.reverse()
                return False, previous.reshape(rows, cols) != -2, np.array([divmod(j, cols) for j in path])
            j = rr * cols + cc
            if previous[j] == -2:
                previous[j] = i; queue.append(j)
    return True, previous.reshape(rows, cols) != -2, None


def feasibility(eligible, difference, seed, threshold=np.inf):
    return dual_flood(*edge_masks(eligible, difference, threshold), seed)


def minimum_threshold(eligible, difference, seed):
    if not feasibility(eligible, difference, seed)[0]:
        return None
    candidates = np.unique(np.abs(difference[eligible & np.isfinite(difference)]))
    low, high = 0, len(candidates)-1
    while low < high:
        mid = (low + high)//2
        if feasibility(eligible, difference, seed, candidates[mid])[0]:
            high = mid
        else:
            low = mid + 1
    return float(candidates[low])


def simple_cycles(vertices):
    """Decompose a grid-boundary walk at repeated vertices; no diagonal jumps."""
    stack, positions, result = [], {}, []
    for v in vertices:
        v = tuple(v)
        if v in positions:
            i = positions[v]
            cycle = stack[i:] + [v]
            if len(cycle) >= 5:
                result.append(cycle)
            for old in stack[i+1:]:
                del positions[old]
            stack = stack[:i+1]
        else:
            positions[v] = len(stack); stack.append(v)
    return result


def encloses(vertices, point):
    y, x = point; inside = False
    for (a,b),(c,d) in zip(vertices[:-1], vertices[1:]):
        if (a > y) != (c > y) and x < b + (y-a)*(d-b)/(c-a):
            inside = not inside
    return inside


def boundary_cycle(reached, seed):
    """A deterministic enclosing witness, not a shortest/final seamline.

    GDAL polygonization traces dual-face boundaries along primal edges. Expand
    collinear segments and split corner-touching walks into simple cycles.
    """
    from rasterio.features import shapes
    cycles = []
    for geometry, _ in shapes(reached.astype('uint8'), mask=reached, connectivity=4):
        ring = geometry['coordinates'][0]
        vertices = []
        for (x,y),(xx,yy) in zip(ring[:-1], ring[1:]):
            x,y,xx,yy = [int(round(v)) for v in (x,y,xx,yy)]
            dx,dy = np.sign(xx-x),np.sign(yy-y)
            if dx and dy:
                raise ValueError('Non-grid polygon boundary')
            vertices.extend([(y+k*dy,x+k*dx) for k in range(abs(xx-x)+abs(yy-y))])
        vertices.append(vertices[0])
        cycles.extend(c for c in simple_cycles(vertices) if encloses(c,(seed[0]+.5,seed[1]+.5)))
    if not cycles:
        raise ValueError('Separated face has no enclosing boundary cycle')
    return np.asarray(min(cycles, key=lambda c: (len(c),c)), dtype=np.int32)


def summary(a):
    a = np.asarray(a); a = a[np.isfinite(a)]
    if not a.size:
        return {'count':0}
    med = float(np.median(a))
    return {'count':int(a.size),'mean':float(a.mean()),'median':med,
            'nmad':float(1.4826*np.median(abs(a-med))), 'rms':float(np.sqrt(np.mean(a*a))),
            'min':float(a.min()),'p05':float(np.quantile(a,.05)),
            'p95':float(np.quantile(a,.95)),'p99':float(np.quantile(a,.99)),'max':float(a.max())}


def array_hash(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def regrid_exclusion(mask, source_transform, transform, shape):
    from rasterio.warp import reproject, Resampling
    a = np.full(shape,255,dtype='uint8')
    reproject(mask.astype('uint8'),a,src_transform=source_transform,src_crs=2056,
              dst_transform=transform,dst_crs=3857,src_nodata=255,dst_nodata=255,
              resampling=Resampling.max, num_threads=1)
    return a != 0


def verify_inputs(data):
    import regional_parents as p
    import copernicus_common as cp
    rt, sp = p.rt,p.sp
    plan = json.loads((p.REPO/'docs/atlas/seam-corridor-plan.json').read_text(encoding='utf8'))
    sources = {'swiss':sp.source_record(data),'common':cp.source_record(data)}
    products = {}
    for name, root in [('swiss',sp.PRODUCT),('common',cp.PRODUCT),('regionalParents',p.PRODUCT)]:
        manifest = json.loads((data/root/'manifest.json').read_text(encoding='utf8'))
        if rt.stable_id({k:v for k,v in manifest.items() if k != 'identity'}) != manifest['identity'] or manifest['identity'] != plan['products'][name]:
            raise ValueError('Frozen product identity mismatch: '+name)
        products[name] = manifest
    if products['swiss']['sourceIdentity'] != sources['swiss']['identity'] or products['common']['sourceIdentity'] != sources['common']['identity']:
        raise ValueError('Source lineage mismatch')
    if products['regionalParents']['parents'] != {k:plan['products'][k] for k in ['swiss','common']}:
        raise ValueError('Regional parent lineage mismatch')
    parents = p.verify(data,parents=False)
    raw = data/'experiments/atlas/global-reference-assessment-v1/fields-and-mask.npz'
    measurement = json.loads((p.REPO/'docs/atlas/global-reference-measurements.json').read_text(encoding='utf8'))
    with np.load(raw) as f:
        fields = {k:f[k] for k in f.files}
    for k,a in fields.items():
        if array_hash(a) != measurement['arrayHashes'][k]:
            raise ValueError('Retained overlap array drift: '+k)
    acquisition = json.loads((p.REPO/'docs/atlas/global-reference-acquisition.json').read_text(encoding='utf8'))
    assets = acquisition['assets']
    for key in ['sgi1973','sgi2016','sgi2023']:
        if rt.digest(data/assets[key]['path']) != assets[key]['sha256']:
            raise ValueError('Glacier inventory drift')
    record = {'sources':{k:v['identity'] for k,v in sources.items()},
              'products':plan['products'],'regionalFilesVerified':len(parents['files']),
              'sourceAssetsVerified':{k:len(v['assets']) for k,v in sources.items()},
              'overlapFileSha256':rt.digest(raw),'overlapArrayHashes':measurement['arrayHashes'],
              'glacierAssets':{k:{'path':assets[k]['path'],'sha256':assets[k]['sha256']} for k in ['sgi1973','sgi2016','sgi2023']}}
    return plan,products,fields,assets,record


def load_level(data,z,products,retained,ice):
    import rasterio
    from rasterio.transform import from_bounds
    from pyproj import Transformer
    import regional_parents as p
    import copernicus_common as cp
    rt,sp = p.rt,p.sp
    with np.load(data/p.PRODUCT/f'fields/z{z}.npz') as f:
        swiss,counts = f['heights'],f['counts']
    x0,x1,y0,y1,shape,extent = sp.hierarchy(z)
    span = rt.WORLD/(256*2**z)
    transform = rasterio.Affine(span,0,-rt.WORLD/2+x0*256*span,0,-span,rt.WORLD/2-y0*256*span)
    yy,xx = np.mgrid[:shape[0],:shape[1]]
    mx,my = transform*(xx+.5,yy+.5)
    inverse = Transformer.from_crs(3857,2056,always_xy=True,allow_ballpark=False)
    east,north = inverse.transform(mx,my)
    corner_e = [];corner_n=[]
    for dx,dy in [(0,0),(1,0),(0,1),(1,1),(.5,0),(.5,1),(0,.5),(1,.5)]:
        e,n = inverse.transform(*(transform*(xx+dx,yy+dy)))
        corner_e.append(e);corner_n.append(n)
    edge = np.minimum.reduce([a for e,n in zip(corner_e,corner_n) for a in [e-sp.BOUNDS[0],sp.BOUNDS[2]-e,n-sp.BOUNDS[1],sp.BOUNDS[3]-n]])
    diagonal = span/np.cosh(my/(rt.WORLD/(2*np.pi)))*np.sqrt(2)
    radius = np.hypot(east-sp.CENTRE[0],north-sp.CENTRE[1])
    common = np.full(shape,np.nan);files=[]
    common_rows = {r['path']:r for r in products['common']['files']}
    for ty in range(y0,y1+1):
        for tx in range(x0,x1+1):
            key=f'tiles/{z}/{tx}/{ty}.png'; row=common_rows.get(key)
            if row is None:
                continue
            path=data/cp.PRODUCT/key
            if rt.digest(path) != row['sha256']:
                raise ValueError('Common delivery changed: '+key)
            common[(ty-y0)*256:(ty-y0+1)*256,(tx-x0)*256:(tx-x0+1)*256]=rt.decode(path.read_bytes())
            files.append({'path':key,'sha256':row['sha256']})
    full = counts == 4**(14-z)
    swiss_valid = full & np.isfinite(swiss)
    valid = swiss_valid & np.isfinite(common)
    source_transform=from_bounds(*sp.BOUNDS,400,400)
    ice_masks={r:regrid_exclusion(mask,source_transform,transform,shape) for r,mask in ice.items()}
    water=regrid_exclusion(retained['coverNearest']==80,source_transform,transform,shape)
    snow=regrid_exclusion(retained['coverNearest']==70,source_transform,transform,shape)
    stable=~regrid_exclusion(~retained['primaryMask'],source_transform,transform,shape)
    bare=~regrid_exclusion(~retained['bareMask'],source_transform,transform,shape)
    a = np.where(valid,swiss,np.nan)
    gy,gx=np.gradient(a,span)
    slope=np.degrees(np.arctan(np.hypot(gx,gy)*np.cosh(my/(rt.WORLD/(2*np.pi)))))
    rough=abs(a-(np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1))/4)
    rough[[0,-1],:]=np.nan;rough[:,[0,-1]]=np.nan
    d=np.where(valid,swiss-common,np.nan)
    local=np.full(shape,np.nan)
    windows=np.lib.stride_tricks.sliding_window_view(np.pad(abs(d),1,constant_values=np.nan),(3,3))
    safe=valid & np.isfinite(windows).all(axis=(-2,-1))
    local[safe]=np.median(windows[safe],axis=(-2,-1))
    face_e=(east[:-1,:-1]+east[1:,1:])/2
    face_n=(north[:-1,:-1]+north[1:,1:])/2
    seed=tuple(np.unravel_index(np.argmin((face_e-sp.CENTRE[0])**2+(face_n-sp.CENTRE[1])**2),face_e.shape))
    return {'swiss':swiss,'common':common,'difference':d,'localMedianAbsolute':local,
            'counts':counts,'valid':valid,'east':east,'north':north,'edge':edge,'radius':radius,
            'diagonal':diagonal,'ice':ice_masks,'water':water,'snow':snow,'stable':stable,'bare':bare,
            'slope':slope,'roughness':rough,'seed':seed,'span':span,'commonFiles':files,
            'transform':transform}


def domain(f,edge=200,ice=250,stable=False,no_change=False):
    a=f['valid'] & (f['edge']>=edge) & (f['radius']>1500+f['diagonal']) & ~f['water']
    if not no_change:
        a &= ~f['ice'][ice] & ~f['snow']
    if stable:
        a &= f['stable']
    return a


def sectors(f):
    e,n=f['east']-2625000,f['north']-1092000
    return {'west': (e<=-abs(n)), 'south':(n<=-abs(e)),
            'east':(e>=abs(n)), 'north':(n>=abs(e)),
            'NW':(e<0)&(n>=0),'NE':(e>=0)&(n>=0),'SW':(e<0)&(n<0),'SE':(e>=0)&(n<0)}


def route_metrics(route,f,allowed):
    r,c=route.T;values=f['difference'][r,c];e=f['east'][r,c];n=f['north'][r,c]
    lengths=np.hypot(np.diff(e),np.diff(n))
    radius=f['radius'][r,c]
    worst=int(np.argmax(abs(values[:-1])))
    import copernicus_common as cp
    import riffelhorn_terrain as rt
    mx,my=f['transform']*(c+.5,r+.5)
    common_clearance=np.minimum.reduce([mx-cp.BOUNDS[0],cp.BOUNDS[2]-mx,my-cp.BOUNDS[1],cp.BOUNDS[3]-my])/np.cosh(my/(rt.WORLD/(2*np.pi)))
    return {'vertices':len(route)-1,'lengthMetres':float(lengths.sum()),'signedDifference':summary(values[:-1]),
            'absoluteDifference':summary(abs(values[:-1])), 'slopeDegrees':summary(f['slope'][r,c]),
            'roughnessMetres':summary(f['roughness'][r,c]), 'minimumSourceEdgeMetres':float(f['edge'][r,c].min()),
            'minimumProtectedClearanceMetres':float((radius-1500).min()),
            'integratedAbsoluteDifferenceMetresSquared':float(np.sum((abs(values[1:])+abs(values[:-1]))/2*lengths)),
            'stableVertexFraction':float(f['stable'][r,c].mean()),
            'glacier250Fraction':float(f['ice'][250][r,c].mean()),'snowClassFraction':float(f['snow'][r,c].mean()),
            'allNodesAllowed':bool(allowed[r,c].all()),
            'minimumCommonEdgeApproxGroundMetres':float(common_clearance.min()),
            'worstNode':{'LV95':[float(e[worst]),float(n[worst])],'signedDifferenceMetres':float(values[worst]),
                         'slopeDegrees':float(f['slope'][r[worst],c[worst]]),
                         'glacier250Excluded':bool(f['ice'][250][r[worst],c[worst]]),
                         'snowExcluded':bool(f['snow'][r[worst],c[worst]]),
                         'sourceEdgeMetres':float(f['edge'][r[worst],c[worst]])},
            'sectorAbsoluteDifference':{name:summary(abs(values[:-1])[mask[r[:-1],c[:-1]]]) for name,mask in sectors(f).items()}}


def obstruction_metrics(path,f,allowed):
    """Check the dual certificate and attribute crossed absent primal edges."""
    labels={'protected':f['radius']<=1500+f['diagonal'],'sourceEdge':f['edge']<200,
            'incompleteSupport':~f['valid'],'glacier250':f['ice'][250],
            'snow':f['snow'],'water':f['water']}
    counts={k:0 for k in labels}; inside_edges=[]
    for (r,c),(rr,cc) in zip(path[:-1],path[1:]):
        if rr==r-1 and cc==c: nodes=[(r,c),(r,c+1)]
        elif rr==r+1 and cc==c: nodes=[(r+1,c),(r+1,c+1)]
        elif cc==c-1 and rr==r: nodes=[(r,c),(r+1,c)]
        elif cc==c+1 and rr==r: nodes=[(r,c+1),(r+1,c+1)]
        else: raise ValueError('Invalid nonadjacent dual certificate')
        nr,nc=np.asarray(nodes).T
        if allowed[nr,nc].all():
            raise ValueError('Dual certificate crosses permitted graph edge')
        for key,mask in labels.items(): counts[key]+=int(mask[nr,nc].any())
        if f['valid'][nr,nc].all() and (f['edge'][nr,nc]>=200).all() and (f['radius'][nr,nc]>1500+f['diagonal'][nr,nc]).all():
            inside_edges.append(nodes)
    if inside_edges:
        nodes=np.asarray(inside_edges).reshape(-1,2);r,c=nodes.T
        supported={'edges':len(inside_edges),'glacier250EndpointFraction':float(f['ice'][250][r,c].mean()),
                   'snowEndpointFraction':float(f['snow'][r,c].mean()),
                   'rangeLV95':[float(f['east'][r,c].min()),float(f['north'][r,c].min()),float(f['east'][r,c].max()),float(f['north'][r,c].max())]}
    else: supported={'edges':0}
    return {'crossedAbsentEdges':len(path)-1,'overlappingReasonCounts':counts,'fullySupportedOutsideProtected':supported}


def run(data,suffix=''):
    import rasterio
    from rasterio.transform import from_bounds
    import pyproj
    import regional_parents as p
    import assess_global_reference as assessment
    rt=p.rt
    started=time.perf_counter()
    plan,products,retained,assets,verification=verify_inputs(data)
    ice,ice_record=assessment.glacier_footprints(data,assets,from_bounds(*p.sp.BOUNDS,400,400))
    if not np.array_equal(ice[250],retained['glacier250Mask']):
        raise ValueError('Official glacier mask regeneration differs from retained mask')
    out=data/('experiments/atlas/'+plan['version']+suffix)
    if (out/'manifest.json').exists():
        raise ValueError('Immutable diagnostic exists; use a distinct --suffix for rebuild')
    out.mkdir(parents=True,exist_ok=True)
    result={'baseline':plan['baseline'],'products':plan['products'],'heightPolicy':plan['heightPolicy'],
            'verification':verification,'glacierMasks':ice_record,'levels':{},
            'software':{'python':__import__('sys').version.split()[0],'numpy':np.__version__,'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':pyproj.__version__}}
    for z in plan['levels']:
        f=load_level(data,z,products,retained,ice);d=f['difference'];primary=domain(f)
        no_change=domain(f,no_change=True)
        scenarios={'primary':primary, 'edge100':domain(f,edge=100),'edge500':domain(f,edge=500),
                   'ice100':domain(f,ice=100),'ice500':domain(f,ice=500),'strictStable':domain(f,stable=True),
                   'noChangeExclusionControl':no_change,
                   'glacierOnlyAttribution':no_change & ~f['ice'][250],
                   'snowOnlyAttribution':no_change & ~f['snow']}
        masks={'full':f['counts']==4**(14-z),'partial':(f['counts']>0)&(f['counts']<4**(14-z)),
               'glacier250':f['ice'][250],'water':f['water'],'snow':f['snow'],'stable':f['stable']}
        field_summary={name:summary(f[name][primary]) for name in ['difference','localMedianAbsolute','slope','roughness','edge','radius']}
        usable=f['valid']&(f['radius']>1500+f['diagonal'])&(f['edge']>=200)
        field_summary['correlations']={name:float(np.corrcoef(abs(d[ok]),f[name][ok])[0,1]) for name in ['slope','roughness','edge','radius'] if (ok:=primary&np.isfinite(f[name])).sum()>1}
        lev={'shape':list(d.shape),'groundCellMetresNearCentre':float(f['span']/np.cosh((f['transform']*(0,d.shape[0]/2))[1]/(rt.WORLD/(2*np.pi)))),
             'maskCounts':{k:int((a & f['valid']).sum()) if k not in ['full','partial'] else int(a.sum()) for k,a in masks.items()},'domainNodes':int(primary.sum()),'evidenceFields':field_summary,
             'sectors':{name:{'domainNodes':int((primary&mask).sum()),'absoluteDifference':summary(abs(d[primary&mask])),
                              'bestAvailableDifference':float(np.min(abs(d[primary&mask]))) if (primary&mask).any() else None,
                              'excludedChangeFraction':float((f['ice'][250]|f['snow'])[usable&mask].mean()) if (usable&mask).any() else None}
                        for name,mask in sectors(f).items()}, 'scenarios':{},'thresholds':[],'commonFilesVerified':f['commonFiles']}
        witnesses={}
        for name,a in scenarios.items():
            possible,reached,path=feasibility(a,d,f['seed'])
            threshold=minimum_threshold(a,d,f['seed']) if possible else None
            entry={'domainNodes':int(a.sum()),'closedCycleAtUnlimitedDisagreement':bool(possible),'minimumThresholdMetres':threshold}
            if possible:
                yes,area,_=feasibility(a,d,f['seed'],threshold)
                route=boundary_cycle(area,f['seed'])
                if not np.all(a[route[:,0],route[:,1]]) or np.max(abs(d[route[:,0],route[:,1]]))>threshold:
                    raise ValueError('Invalid enclosing threshold witness')
                entry['route']=route_metrics(route,f,a)
                witnesses[name+'_cycle']=route
                entry['belowMinimumFeasible']=bool(feasibility(a,d,f['seed'],np.nextafter(threshold,-np.inf))[0])
                if entry['belowMinimumFeasible']:
                    raise ValueError('Minimum threshold is not tight')
            else:
                witnesses[name+'_escape']=path
                rr,cc=path.T
                entry['escapeFaces']=len(path)
                entry['escapeEndLV95']=[float(f['east'][rr[-1],cc[-1]]),float(f['north'][rr[-1],cc[-1]])]
                if name=='primary': entry['obstruction']=obstruction_metrics(path,f,a)
            lev['scenarios'][name]=entry
            print('CORRIDOR',z,name,'possible',possible,'minimum',threshold,flush=True)
        for t in plan['thresholdsMetres']:
            lev['thresholds'].append({'metres':t,'closedCycle':bool(feasibility(primary,d,f['seed'],t)[0]),
                                      'eligibleNodes':int((primary&(abs(d)<=t)).sum())})
        # A strip near the actual source rectangle is a control, not eligible seam support.
        ring=f['valid']&(f['edge']>=0)&(f['edge']<=f['diagonal']*1.5)
        lev['rectangleControl']={'stripDefinition':'Full-supported cells within 1.5 cell diagonals of native source boundary; not original whole-tile delivery frontier.',
                                'signedDifference':summary(d[ring]),'absoluteDifference':summary(abs(d[ring])),
                                'slopeDegrees':summary(f['slope'][ring]),'stableFraction':float(f['stable'][ring].mean()),
                                'changeExcludedFraction':float((f['ice'][250]|f['snow'])[ring].mean()),
                                'edgeDistanceMetres':summary(f['edge'][ring]),
                                'sectors':{name:summary(abs(d[ring&mask])) for name,mask in sectors(f).items()}}
        corner_masks={name:(abs(f['east']-e)<1000)&(abs(f['north']-n)<1000)&f['valid'] for name,e,n in
                      [('NW',2620000,1097000),('NE',2630000,1097000),('SW',2620000,1087000),('SE',2630000,1087000)]}
        lev['corners']={name:{'fullSupportedNodes':int(mask.sum()),'permittedNodes':int((mask&primary).sum()),
                             'absoluteDifference':summary(abs(d[mask])),
                             'changeExcludedFraction':float((f['ice'][250]|f['snow'])[mask].mean())}
                        for name,mask in corner_masks.items()}
        arrays={k:f[k] for k in ['difference','localMedianAbsolute','counts','slope','roughness','edge','radius','stable','water','snow']}
        arrays.update({'domain_'+k:a for k,a in scenarios.items()});arrays.update(witnesses)
        arrays['glacier250']=f['ice'][250]
        np.savez_compressed(out/f'z{z}-diagnostic.npz',**arrays)
        lev['arrayHashes']={k:array_hash(a) for k,a in arrays.items()}
        features=[]
        for name,route in witnesses.items():
            rr,cc=route.T
            if name.endswith('escape'):
                from pyproj import Transformer
                coords=np.column_stack(Transformer.from_crs(3857,2056,always_xy=True).transform(*(f['transform']*(cc+1,rr+1)))).tolist()
            else: coords=np.column_stack([f['east'][rr,cc],f['north'][rr,cc]]).tolist()
            features.append({'type':'Feature','properties':{'level':z,'scenario':name,'kind':'enclosing witness, NOT final seam' if name.endswith('cycle') else 'dual escape obstruction witness'},'geometry':{'type':'LineString','coordinates':coords}})
        p.sp.save(out/f'z{z}-witnesses-lv95.json',{'type':'FeatureCollection','coordinateReference':'EPSG:2056; explicitly native, not RFC7946 lon/lat','features':features})
        render_map(out,z,f,scenarios,witnesses)
        result['levels'][str(z)]=lev
    p.sp.save(out/'measurements.json',result)
    files=[{'path':file.name,'sha256':rt.digest(file),'bytes':file.stat().st_size} for file in sorted(out.iterdir()) if file.is_file()]
    manifest={'version':plan['version'],'planSha256':rt.repository_text_digest(p.REPO/'docs/atlas/seam-corridor-plan.json'),
              'toolSha256':rt.repository_text_digest(__file__),'inputs':verification,'files':files,'software':result['software'],
              'noTerrainOutput':True,'heightsUnmodified':True,'noVerticalTransformation':True}
    manifest['identity']=rt.stable_id(manifest)
    p.sp.save(out/'manifest.json',manifest)
    print('DIAGNOSTIC',manifest['identity'],'seconds',round(time.perf_counter()-started,2),flush=True)


def render_map(out,z,f,scenarios,witnesses):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(15,10))
    extent=(0,f['east'].shape[1],f['east'].shape[0],0)
    fields=[(abs(f['difference']),'Absolute native-reference disagreement (m)','magma',0,40),
            (f['slope'],'Swiss same-level slope (degrees)','terrain',0,60),
            (f['roughness'],'Swiss four-neighbour relief (m)','magma',0,10),
            (scenarios['primary'],'Permitted domain; glacier/change hard exclusions','Greens',0,1),
            (f['glacier250'] if 'glacier250' in f else f['ice'][250],'SGI union +250 m exclusion','Blues',0,1),
            (f['stable'],'Conservative stable-fit support (not seam mask)','Greens',0,1)]
    for ax,(a,title,cmap,low,high) in zip(axes.flat,fields):
        a=np.where(f['valid'],a,np.nan)
        im=ax.imshow(a,cmap=cmap,vmin=low,vmax=high,extent=extent);ax.set_title(title)
        ax.contour(f['radius'],levels=[1500],colors='cyan',linewidths=1)
        ax.contour(f['edge'],levels=[0,200],colors=['gray','white'],linewidths=.5)
        for name,route in witnesses.items():
            if name=='primary_escape' or name=='noChangeExclusionControl_cycle':
                ax.plot(route[:,1],route[:,0],color='red' if name.endswith('escape') else 'lime',linewidth=1)
        ax.set_xticks([]);ax.set_yticks([]);fig.colorbar(im,ax=ax,shrink=.7)
    fig.suptitle(f'z{z}: compatibility/support diagnostic; red = forbidden dual escape; green = rejected change-exclusion control')
    fig.tight_layout();fig.savefig(out/f'z{z}-evidence.png',dpi=130);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--suffix',default='');args=parser.parse_args()
    import re
    if args.suffix and not re.fullmatch(r'-[a-z0-9-]+',args.suffix):
        raise ValueError('Simple immutable named sibling only')
    import riffelhorn_terrain as rt
    run(rt.resolve_storage_roots(require_data=True).data,args.suffix)
