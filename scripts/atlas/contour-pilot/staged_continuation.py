"""Staged, source-specific derivation; genuine stages require separate approval.

This module imports no raster/numerical library until the stage gate has passed.
No historical output is regenerated or retired by the synthetic entry point.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time

from staged_store import Budget,StageStore,encode,digest

MISSING=('swiss-egm-diagnostic','copernicus-native')
SWISS=('swiss-native','swiss-2m','swiss-smoothed')


@dataclass(frozen=True)
class Permit:
    scope: str
    stage: int
    approved: bool
    profile_sha256: str
    checkpoint_sha256: str|None=None
    controller_sha256: str|None=None

    def require(self,scope,stage,budget,checkpoint=None):
        if not self.approved or self.scope!=scope or self.stage!=stage or self.profile_sha256!=budget.sha256:
            raise PermissionError('Explicit matching stage/profile approval is absent')
        if stage==2 and (not checkpoint or digest(checkpoint)!=self.checkpoint_sha256):
            raise PermissionError('Stage 2 needs separate approval of the exact Stage 1 checkpoint')


def historical_inventory(root,inventory_path,expected_sha,summary):
    """Verify only retained files/JSON; never opens or decodes source rasters."""
    root=Path(root).resolve();inventory_path=Path(inventory_path).resolve()
    if digest(inventory_path)!=expected_sha:raise ValueError('Historical inventory seal changed')
    old=json.loads(inventory_path.read_text())
    entries=[]
    for entry in old['inventory']:
        item=dict(entry);parts=Path(item['path']).parts
        item['role']='final' if len(parts)>3 and parts[3] in SWISS and item.get('vertices',0) else 'intermediate'
        if not item.get('vertices',0):item['role']='control'
        entries.append(item)
    entries.append({'path':str(inventory_path.relative_to(root)).replace('\\','/'),
        'bytes':inventory_path.stat().st_size,'sha256':expected_sha,'vertices':0,'role':'control'})
    paths={str((root/item['path']).resolve()) for item in entries}
    actual={str(p.resolve()) for p in root.rglob('*') if p.is_file()}
    if actual!=paths:raise ValueError('Historical root has unexpected or missing evidence')
    if (len(entries)!=summary['files'] or sum(e['bytes'] for e in entries)!=summary['bytes']
            or sum(e.get('vertices',0) for e in entries)!=summary['stored']
            or sum(e.get('vertices',0) for e in entries if e['role']=='final')!=summary['final']):
        raise ValueError('Historical resource totals changed')
    for item in entries:
        path=root/item['path']
        if digest(path)!=item['sha256'] or path.stat().st_size!=item['bytes']:
            raise ValueError('Historical file changed')
    return entries


def check_shape_capacity(shape,budget):
    """Reject a conservative allocation that cannot fit, never change partitions."""
    quads=min(256,shape[0]-1)*min(256,shape[1]-1)
    if 4*quads>budget.temporary:
        raise ValueError(f'Contour allocation reservation {4*quads} exceeds temporary ceiling {budget.temporary}')


def validate_lines(lines,metadata):
    """Unmodified contour topology/partition controls; never simplifies geometry."""
    import numpy as np
    from shapely.geometry import LineString,box
    from shapely.ops import unary_union
    from pilot import XY,metric
    bounds=metadata['core'];mid_x=(bounds[0]+bounds[2])/2;mid_y=(bounds[1]+bounds[3])/2
    partitions=[box(a,b,c,d) for a,c in ((bounds[0],mid_x),(mid_x,bounds[2]))
                for b,d in ((bounds[1],mid_y),(mid_y,bounds[3]))]
    result={'partitionMaxDisplacement':0.,'partitionMaxLengthDifference':0.,'roundtripMaxMetres':0.}
    for coords in lines:
        array=np.asarray(coords)
        if not np.isfinite(array).all() or len(coords)<2:raise ValueError('Invalid coordinates')
        line=LineString(coords)
        if not line.is_simple or line.length==0:raise ValueError('Invalid unsimplified line topology')
        if coords[0]==coords[-1] and (len(coords)<4 or not line.is_ring):raise ValueError('Invalid closed contour')
        projected=metric(array,metadata['geographic']) if metadata['scope']=='genuine' else array
        if metadata['scope']=='genuine':
            lon,lat=XY.transform(projected[:,0],projected[:,1])
            xx,yy=XY.transform(lon,lat,direction='INVERSE')
            error=float(np.hypot(xx-projected[:,0],yy-projected[:,1]).max())
            result['roundtripMaxMetres']=max(result['roundtripMaxMetres'],error)
            if error>.01:raise ValueError('XY roundtrip gate')
        original=LineString(projected).intersection(box(*bounds))
        if original.is_empty:continue
        combined=unary_union([original.intersection(part) for part in partitions])
        distance=original.hausdorff_distance(combined);difference=abs(original.length-combined.length)
        if distance>1e-6 or difference>1e-6:raise ValueError('Partition continuity gate')
        result['partitionMaxDisplacement']=max(result['partitionMaxDisplacement'],distance)
        result['partitionMaxLengthDifference']=max(result['partitionMaxLengthDifference'],difference)
    return result


def derive_product(name,source_set,store,levels,*,reference=None):
    from windowed import extract,stitch
    with source_set.reader(name) as reader:
        check_shape_capacity(reader.shape,store.budget)
        fragments=store.execution/(name+'-fragments')
        extraction=extract(reader,levels,fragments,store)
    target=store.execution/name;target.mkdir()
    metadata=source_set.metadata(name)
    stats={'levels':{},'vertices':0,'lines':0,'closedLines':0}
    for level in levels:
        fragment=fragments/f'{level}.ndjson';count=store.registry[str(fragment.resolve())]['vertices']
        # Includes JSON input, stitching/canonical ordering and validation copies.
        with store.workspace(count*8):
            records=store.level_records(fragment)
            lines=stitch(records)
            vertices=sum(map(len,lines));store.geometry.processed('stitched',vertices)
            controls=validate_lines(lines,metadata)
            path=target/f'{level}.ndjson'
            with store.open_geometry(path,'diagnostic' if reference else 'final',bool(reference)) as stream:
                for index,line in enumerate(lines):
                    store.append(stream,{'level':level,'index':level%100==0,
                        'twentyMetreSubset':level%20==0,'line':index,'coordinates':line},len(line))
            observed={'vertices':vertices,'lines':len(lines),'closed':sum(p[0]==p[-1] for p in lines),
                'sha256':digest(path),'controls':controls}
            if reference:
                expected=reference['geometry']['levels'][str(level)]
                if any(observed[k]!=expected[k] for k in ('vertices','lines','closed','sha256')):
                    store.atomic_json(store.execution/f'{name}-mismatch.json',
                        {'state':'mismatch','level':level,'expected':expected,'observed':observed})
                    raise ValueError('Fresh geometry differs from canonical reference')
            stats['levels'][str(level)]=observed;stats['vertices']+=vertices
            stats['lines']+=len(lines);stats['closedLines']+=observed['closed']
            # Persist the comparison before retiring this exact fresh level file.
            store.atomic_json(store.execution/f'{name}-progress.json',
                {'state':'verified-levels' if reference else 'generated-levels','geometry':stats,
                 'resources':store.snapshot()})
            if reference:
                store.retire(path,expected_hash=observed['sha256'],receipt=store.execution/f'{name}-retirement.json')
        # Extraction fragments are fresh staging only, never historical evidence.
        store.retire(fragment,expected_hash=digest(fragment),receipt=store.execution/f'{name}-fragment-retirement.json')
    from importlib.metadata import version
    processing={'packages':{package:version(package) for package in ('numpy','contourpy','rasterio','pyproj','shapely')},
        'methodSha256':{filename:digest(Path(__file__).with_name(filename)) for filename in
            ('staged_continuation.py','staged_store.py','windowed.py','readers.py','riffelhorn_sources.py')},
        'qualification':'Operational method seals differ from historical receipts; canonical geometry/meaning compared explicitly'}
    product={'id':name,'meaning':metadata,'geometry':stats,'extraction':extraction,'processingRevision':processing,
             'simplification':'none; historical rejected candidate not executed'}
    if reference and product['meaning']!=reference['meaning']:
        raise ValueError('Scientific product meaning differs')
    store.atomic_json(target/'manifest.json',product)
    return product


def comparisons(source_set,store,canonical,levels):
    """Unsmoothed/unsimplified source-specific comparisons, one pair/level at a time."""
    import numpy as np
    from shapely.geometry import LineString,box
    from shapely.ops import unary_union
    from pilot import metric
    result={}
    for level in levels:
        if level%20:continue
        rows={}
        for a,b in ((SWISS[0],SWISS[1]),(SWISS[1],SWISS[2]),MISSING):
            paths=[store.root/canonical[name]/f'{level}.ndjson' for name in (a,b)]
            count=sum(store.registry[str(p.resolve())]['vertices'] for p in paths)
            with store.workspace(count*8):
                geometries=[]
                for name,path in zip((a,b),paths):
                    metadata=source_set.metadata(name);bounds=metadata['core']
                    common=box(bounds[0]+7,bounds[1]+7,bounds[2]-7,bounds[3]-7)
                    records=store.level_records(path)
                    lines=[]
                    for record in records:
                        coordinates=np.asarray(record['coordinates'])
                        if source_set.scope=='genuine':coordinates=metric(coordinates,metadata['geographic'])
                        lines.append(LineString(coordinates))
                    geometries.append(unary_union(lines).intersection(common))
                ga,gb=geometries
                rows[a+' versus '+b]={'firstLengthMetres':ga.length,'secondLengthMetres':gb.length,
                    'hausdorffMetres':None if ga.is_empty or gb.is_empty else ga.hausdorff_distance(gb),
                    'qualification':'represented geometry/support diagnostic, not source error or terrain accuracy'}
        result[str(level)]=rows
    return result


class Continuation:
    """An explicit stage boundary; Stage 1 can never call Stage 2 implicitly."""
    def __init__(self,source_set,budget,levels):
        self.sources=source_set;self.budget=budget;self.levels=tuple(levels)

    def stage1(self,permit,root,execution,inventory,written,canonical,*,controller_receipt=None):
        started=time.monotonic()
        permit.require(self.sources.scope,1,self.budget)
        self.sources.preflight(self.budget) # no output or source read before approval
        store=StageStore(root,execution,self.budget,inventory,written=written,memory_reader=self.sources.memory_reader,
                         external_receipt=controller_receipt)
        store.started=started
        try:
            products={name:derive_product(name,self.sources,store,self.levels) for name in MISSING}
            combined=dict(canonical,**{name:str((store.execution/name).relative_to(store.root)) for name in MISSING})
            diagnostics={'comparisons20m':comparisons(self.sources,store,combined,self.levels),
                'heightDiagnostic':self.sources.height_diagnostic(store)}
            store.verify_immutable()
            checkpoint=store.execution/'checkpoint.json'
            value={'state':'awaiting-stage-2-owner-review','scope':self.sources.scope,
                'profileSha256':self.budget.sha256,'levels':list(self.levels),'products':products,
                'canonical':combined,'diagnostics':diagnostics,
                'resources':store.snapshot(),'inventory':store.sealed_inventory()}
            store.atomic_json(checkpoint,value)
            return checkpoint
        except BaseException as error:
            store.atomic_json(store.execution/'incomplete.json',{'state':'incomplete','reason':str(error),
                'resources':store.snapshot()},emergency=True)
            raise

    def stage2(self,permit,root,execution,checkpoint,*,prior_controller=None,startup_inventory=(),controller_receipt=None):
        started=time.monotonic()
        permit.require(self.sources.scope,2,self.budget,checkpoint)
        prior=json.loads(Path(checkpoint).read_text())
        if prior['state']!='awaiting-stage-2-owner-review' or prior['scope']!=self.sources.scope:
            raise ValueError('Incomplete or incompatible Stage 1 checkpoint')
        if prior['profileSha256']!=self.budget.sha256 or prior['levels']!=list(self.levels):
            raise ValueError('Changed profile or levels')
        import os
        effective=min(self.budget.working,int(os.environ.get('MERIDIAN_GUARD_MEMBER_BYTES',self.budget.working)))
        if effective!=prior['resources']['effectiveWorkerCeilingBytes']:
            raise PermissionError('Worker memory allocation changed across stages; separate policy review required')
        self.sources.preflight(self.budget)
        inventory=prior['inventory']+[{'path':str(Path(checkpoint).resolve().relative_to(Path(root).resolve())),
            'bytes':Path(checkpoint).stat().st_size,'sha256':digest(checkpoint),'vertices':0,'role':'control'}]
        elapsed=prior['resources']['activeElapsedSeconds']
        if self.sources.scope=='genuine':
            if not prior_controller or digest(prior_controller)!=permit.controller_sha256:
                raise PermissionError('Genuine Stage 2 needs the reviewed Stage 1 controller closure')
            closure=json.loads(Path(prior_controller).read_text())
            if not closure['success'] or not closure['workerHandshakeVerified']:
                raise ValueError('Prior controller did not verify successful workload/cleanup')
            elapsed=closure['totalActiveSeconds']
            inventory.append({'path':str(Path(prior_controller).resolve().relative_to(Path(root).resolve())),
                'bytes':Path(prior_controller).stat().st_size,'sha256':digest(prior_controller),'vertices':0,'role':'control'})
        inventory.extend(startup_inventory)
        store=StageStore(root,execution,self.budget,inventory,
            written=prior['resources']['geometry']['cumulativeWrittenVertices'],
            work=prior['resources']['geometry']['processingVerticesByStage'],
            elapsed=elapsed,memory_reader=self.sources.memory_reader,external_receipt=controller_receipt)
        store.started=started
        try:
            results={}
            for name in MISSING+SWISS:
                manifest=store.root/prior['canonical'][name]/'manifest.json'
                reference=json.loads(manifest.read_text())
                # Historical manifests predate this adapter. The source set keeps
                # their scientific interpretation explicit, not their code hashes.
                if 'meaning' not in reference:
                    metadata=self.sources.metadata(name)
                    for key in ('units','verticalReference','surface','horizontalReference','sourceRevision','interval','subsetInterval','indexInterval'):
                        if reference.get(key)!=metadata.get(key):raise ValueError('Historical scientific meaning mismatch: '+key)
                    reference['meaning']=metadata
                results[name]=derive_product(name,self.sources,store,self.levels,reference=reference)
            repeated={'comparisons20m':comparisons(self.sources,store,prior['canonical'],self.levels),
                      'heightDiagnostic':self.sources.height_diagnostic(store)}
            if repeated!=prior['diagnostics']:raise ValueError('Qualified diagnostic replay differs')
            store.verify_immutable()
            store.atomic_json(store.execution/'completion.json',{'state':'complete-replay-comparisons',
                'scope':self.sources.scope,'results':results,'resources':store.snapshot(),
                'limitations':['same numerical method, not independent-algorithm conformance',
                    'mixed-source/height interpretation requires qualified diagnostics']})
            return store.execution/'completion.json'
        except BaseException as error:
            store.atomic_json(store.execution/'incomplete.json',{'state':'incomplete','reason':str(error),
                'resources':store.snapshot()},emergency=True)
            raise
