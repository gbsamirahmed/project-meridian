"""Proposed revised Riffelhorn replay. Requires separate owner approval; not run here."""
import argparse
import gc
import json
from pathlib import Path
import time

from pilot import (canonical,digest,verify_inputs,XY,CORE,LEVELS,NOTICE,metric)
from pilot import memory
from resource_guard import confine_process
from windowed import (Ledger,extract,finish_product,load_level,simplification_check,
                      LimitsReached,MAX_LEVEL_VERTICES)
from readers import SwissNativeReader,SwissCoarseReader,CopernicusReader
import numpy as np
import pyproj
from shapely.geometry import LineString,box
from shapely.ops import unary_union
import shapely


def read_lines(path,ledger):
    records = load_level(path,ledger)
    return [record['coordinates'] for record in records]


def geometry_controls(folder,levels,geographic,ledger):
    partitions = [box(x,y,x+1000,y+1000) for y in (CORE[1],CORE[1]+1000)
                  for x in (CORE[0],CORE[0]+1000)]
    stats = {'partitionMaxDisplacement':0.,'partitionMaxLengthDifference':0.,
             'roundtripMaxMetres':0.}
    for level in levels:
        lines = read_lines(folder/f'{level}.ndjson',ledger)
        projected = [metric(np.asarray(line),geographic).tolist() for line in lines]
        for index,line in enumerate(projected):
            coords = np.asarray(line)
            lon,lat = XY.transform(coords[:,0],coords[:,1])
            xx,yy = XY.transform(lon,lat,direction='INVERSE')
            stats['roundtripMaxMetres'] = max(stats['roundtripMaxMetres'],float(np.hypot(xx-coords[:,0],yy-coords[:,1]).max()))
            original = LineString(line).intersection(box(*CORE))
            pieces = []
            for partition in partitions:
                piece = original.intersection(partition)
                if not piece.is_empty:pieces.append(piece)
            joined = unary_union(pieces)
            if not original.is_empty:
                displacement = original.hausdorff_distance(joined)
                difference = abs(original.length-joined.length)
                if displacement>1e-6 or difference>1e-6:
                    raise ValueError('Delivery partition reconstruction failed')
                stats['partitionMaxDisplacement'] = max(stats['partitionMaxDisplacement'],displacement)
                stats['partitionMaxLengthDifference'] = max(stats['partitionMaxLengthDifference'],difference)
        ledger.check(reserve_bytes=32*1024**2)
    if stats['roundtripMaxMetres']>.01:
        raise ValueError('XY roundtrip failed')
    return stats


def global_simplification(folder,levels,geographic,ledger):
    """All non-empty level pairs, resident one pair at a time; baseline retained."""
    result = {'maxDisplacement':0.,'collapsedRings':0,'introducedCrossings':0,
              'levelPairsTested':0,'allPairsTested':True}
    def projected(level):
        return [metric(np.asarray(line),geographic).tolist() for line in
                read_lines(folder/f'{level}.ndjson',ledger)]
    for index,level in enumerate(levels):
        a = projected(level)
        check = simplification_check(a)
        result['maxDisplacement'] = max(result['maxDisplacement'],check['maxDisplacement'])
        result['collapsedRings'] += check['collapsedRings']
        result['introducedCrossings'] += check['introducedCrossings']
        if not a:continue
        original_a = [LineString(line) for line in a]
        simple_a = [line.simplify(2.,preserve_topology=True) for line in original_a]
        for other in levels[index+1:]:
            ledger.check(reserve_bytes=32*1024**2)
            b = projected(other)
            if not b:continue
            if sum(map(len,a))+sum(map(len,b))>MAX_LEVEL_VERTICES:
                raise LimitsReached('Simplification pair exceeds bounded geometry workspace')
            original_b = [LineString(line) for line in b]
            simple_b = [line.simplify(2.,preserve_topology=True) for line in original_b]
            tree = shapely.STRtree(simple_b)
            for i,line in enumerate(simple_a):
                for j in tree.query(line,predicate='intersects'):
                    if not original_a[i].intersects(original_b[j]):
                        result['introducedCrossings'] += 1
            result['levelPairsTested'] += 1
            del b,original_b,simple_b,tree
        del a,original_a,simple_a
        gc.collect()
    result['accepted'] = result['maxDisplacement']<=2. and result['collapsedRings']==0 and result['introducedCrossings']==0
    return result


def comparison(folder,ledger):
    result = {}
    common = box(CORE[0]+7,CORE[1]+7,CORE[2]-7,CORE[3]-7)
    for level in range(2000,3201,20):
        geometries = {}
        for name in ('swiss-native','swiss-2m','swiss-smoothed','swiss-egm-diagnostic','copernicus-native'):
            lines = read_lines(folder/name/f'{level}.ndjson',ledger)
            geographic = name in ('swiss-egm-diagnostic','copernicus-native')
            geometries[name] = unary_union([LineString(metric(np.asarray(line),geographic)) for line in lines]).intersection(common)
        distances = {}
        for a,b in (('swiss-native','swiss-2m'),('swiss-2m','swiss-smoothed'),
                    ('swiss-egm-diagnostic','copernicus-native')):
            ga,gb = geometries[a],geometries[b]
            distances[a+' versus '+b] = {'hausdorffMetres':None if ga.is_empty or gb.is_empty else ga.hausdorff_distance(gb),
                'firstLengthMetres':ga.length,'secondLengthMetres':gb.length,
                'qualification':'geometry diagnostic; not source error/accuracy or terrain change'}
        result[str(level)] = distances
        ledger.check(reserve_bytes=32*1024**2)
    return result


def height_diagnostic(transformed,coarse,cop,ledger):
    offsets,differences = [],[]
    for row in range(0,1000,256):
        for col in range(0,1000,256):
            end_row,end_col = min(row+256,1000),min(col+256,1000)
            grid = transformed.read(row,end_row,col,end_col)
            raw = coarse.read(row,end_row,col,end_col)
            offsets.append((grid.z-raw.z).ravel())
            differences.append((cop.sample(grid.x,grid.y)-grid.z).ravel())
            ledger.check(reserve_bytes=32*1024**2)
    def describe(parts):
        values = np.concatenate(parts)
        valid = values[np.isfinite(values)]
        return {'count':len(valid),'invalid':len(values)-len(valid),'min':float(valid.min()),
            'max':float(valid.max()),'mean':float(valid.mean()),
            'p05MedianP95':np.percentile(valid,[5,50,95]).tolist()}
    return {'transformedHeightMinusLn02':describe(offsets),
        'copernicusDsmMinusTransformedSwissDtm':describe(differences),
        'combinedTransformationAccuracy':'unknown (-1)',
        'qualification':'different represented surfaces/epochs/supports; no correction/accuracy claim'}


def run(data_root,output,budget_root=None,initial_vertices=0,elapsed_offset=0.,working_set=512*1024**2):
    if output.exists():raise ValueError('Fresh owned output directory required')
    output.mkdir(parents=True)
    ledger = Ledger(budget_root or output,bytes_limit=150_000_000-65536,
        memory_limit=working_set,seconds_limit=1200-elapsed_offset)
    ledger.vertices = initial_vertices
    guard = confine_process(working_set=working_set);guard.pop('jobHandle')
    pins = json.loads(Path(__file__).with_name('input-pins.json').read_text())
    verify_inputs(data_root,pins)
    pipeline = pins['compoundPipeline']
    for source in pins['inputs'][5:]:
        pipeline = pipeline.replace(Path(source['path']).name,str(data_root/source['path']).replace('\\','/'))
    transform = pyproj.Transformer.from_pipeline(pipeline)
    versions = {'contourpy':'1.4.0','numpy':np.__version__,'PROJ':pyproj.proj_version_str,
        'methodFiles':{name:digest(Path(__file__).with_name(name)) for name in
            ('windowed.py','readers.py','resource_guard.py','rerun.py','pilot.py')}}
    runs = []
    try:
        for index in (1,2):
            folder = output/f'run-{index}';folder.mkdir()
            native = SwissNativeReader(data_root,pins)
            cop = None
            try:
                cop = CopernicusReader(data_root/pins['inputs'][4]['path'])
                coarse = SwissCoarseReader(native)
                transformed = SwissCoarseReader(native,transform=transform)
                sources = [('swiss-native',native,'LN02','DTM','EPSG:2056'),
                    ('swiss-2m',coarse,'LN02','DTM','EPSG:2056'),
                    ('swiss-smoothed',SwissCoarseReader(native,smoothing=True),'LN02','DTM','EPSG:2056'),
                    ('swiss-egm-diagnostic',transformed,'EGM2008','DTM','CRS84'),
                    ('copernicus-native',cop,'EGM2008','DSM','CRS84')]
                products = {}
                for name,reader,vertical,surface,horizontal in sources:
                    print(json.dumps({'run':index,'product':name,'phase':'extract',
                        'vertices':ledger.vertices,'bodyBytes':ledger.bytes}),flush=True)
                    fragments = folder/(name+'-fragments')
                    extraction = extract(reader,LEVELS,fragments,ledger)
                    geometry = finish_product(fragments,LEVELS,folder/name,ledger)
                    controls = geometry_controls(folder/name,LEVELS,horizontal=='CRS84',ledger)
                    controls['simplification2m'] = global_simplification(folder/name,LEVELS,horizontal=='CRS84',ledger)
                    product = {'id':name,'inputPinsSha256':digest(Path(__file__).with_name('input-pins.json')),
                        'units':'m','verticalReference':vertical,'surface':surface,'horizontalReference':horizontal,
                        'processingRevision':versions,'interval':10,'subsetInterval':20,'indexInterval':100,
                        'sourceRevision':'2024/2 swissALTI3D' if surface=='DTM' else '2021 retained public GLO-30; sub-release unknown',
                        'rights':'Swiss OGD; ©swisstopo' if surface=='DTM' else NOTICE+'; GLO-30 F downstream obligations',
                        'extraction':extraction,'geometry':geometry,'controls':controls,
                        'limitations':['source sample centres, not guaranteed cell averages','per-cell epoch/accuracy remain qualified',
                            'native sample-domain boundary differs from observation coverage','transformed product diagnostic only' if name=='swiss-egm-diagnostic' else 'no source fusion']}
                    ledger.json(folder/name/'manifest.json',product)
                    products[name] = product
                    print(json.dumps({'run':index,'product':name,'phase':'validated',
                        'vertices':ledger.vertices,'bodyBytes':ledger.bytes,'peak':ledger.peak}),flush=True)
                receipt = {'products':products,'heightDiagnostic':height_diagnostic(transformed,coarse,cop,ledger),
                    'comparisons20m':comparison(folder,ledger),'methods':versions}
                ledger.json(folder/'receipt.json',receipt)
                runs.append(receipt)
            finally:
                native.close()
                if cop is not None:cop.close()
            gc.collect()
        if canonical(runs[0])!=canonical(runs[1]):raise ValueError('Two-run deterministic mismatch')
        verify_inputs(data_root,pins)
        ledger.check()
        ledger.json(output/'completion.json',{'deterministic':True,'sourcesUnchanged':True,
            'peakWorkingSet':ledger.peak,'storedVertices':ledger.vertices,'bytesBeforeReceipt':ledger.bytes,
            'elapsedSeconds':time.monotonic()-ledger.start,'guard':guard})
    except Exception as error:
        # The 64 KiB reserved above is for failure evidence, even when the main
        # ledger refuses further writes. It is not a geometry-budget refund.
        current,peak = memory()
        stop = canonical({'status':'incomplete','reason':str(error),
            'geometryAccounting':ledger.resource_counters(),
            'workerPeakWorkingSetBytes':max(ledger.peak,peak),
            'workerCurrentWorkingSetBytes':current,
            'elapsedSeconds':time.monotonic()-ledger.start,
            'observedScratchBytesBeforeStop':sum(p.stat().st_size for p in ledger.root.rglob('*') if p.is_file()),
            'registeredBytesBeforeStop':ledger.bytes})+b'\n'
        if len(stop)>65536:raise RuntimeError('Reserved stop receipt size exceeded') from error
        with (output/'stopped.json').open('xb') as stream:
            if stream.write(stop)!=len(stop):raise OSError('Partial stop receipt write') from error
            stream.flush()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner-approved-riffelhorn',action='store_true')
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--budget-root',type=Path)
    parser.add_argument('--initial-vertices',type=int,default=0)
    parser.add_argument('--elapsed-offset',type=float,default=0.)
    parser.add_argument('--working-set-ceiling',type=int,default=512*1024**2)
    args = parser.parse_args()
    if not args.owner_approved_riffelhorn:
        parser.error('Separate owner approval is required; source files were not opened')
    if not 0<args.working_set_ceiling<=512*1024**2 or args.initial_vertices<0 or args.elapsed_offset<0:
        parser.error('Operational accounting cannot enlarge the approved limits')
    run(args.data_root,args.output,args.budget_root,args.initial_vertices,args.elapsed_offset,args.working_set_ceiling)
