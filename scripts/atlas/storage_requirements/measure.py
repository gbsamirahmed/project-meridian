"""Read-only inventory of named retained manifests and repository evidence. No acquisition.
Run from repository root; --check compares deterministic output without modifying it.
Payload sizes are stat-checked, not rehashed: retained manifest hashes are verified.
"""
from pathlib import Path
import argparse,hashlib,json,math,statistics,sys
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'scripts'))
from meridian_paths import resolve_storage_roots
OUT=REPO/'docs/research/atlas-storage-requirements-measurements.json'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def quantile(values,q):
    if not values or not 0<=q<=1:raise ValueError('Nonempty population and quantile in [0,1] required')
    a=sorted(values);position=(len(a)-1)*q;i=math.floor(position);f=position-i
    return a[i]*(1-f)+a[min(i+1,len(a)-1)]*f

def summarize(files):
    seen=set();groups={}
    for f in files:
        if f['path'] in seen or not isinstance(f['bytes'],int) or f['bytes']<0:raise ValueError('Duplicate path or invalid size')
        seen.add(f['path']);groups.setdefault(f['path'].split('/')[0],[]).append(f['bytes'])
    return {k:{'objects':len(v),'bytes':sum(v),'minBytes':min(v),'medianBytes':statistics.median(v),'p95Bytes':quantile(v,.95),'maxBytes':max(v)} for k,v in sorted(groups.items())}

def raw_grid_bytes(area_m2,spacing_m,bands,bytes_per_sample):
    if area_m2<0 or spacing_m<=0 or bands<=0 or bytes_per_sample<=0:raise ValueError('Invalid grid dimensions')
    return area_m2/spacing_m**2*bands*bytes_per_sample

def build():
    roots=resolve_storage_roots(repository_root=REPO,require_data=True);receipts={}
    def record(rel):
        p=REPO/rel;receipts[rel]=digest(p);return json.loads(p.read_text(encoding='utf-8-sig'))
    welsh=record('src/atlas/terrain/metadata/tryfanProductRecord.json')
    support=record('docs/atlas/riffelhorn-support-product.json');sr=record('docs/atlas/riffelhorn-support-reproducibility.json')
    initial=record('docs/atlas/riffelhorn-regional-product.json');cop=record('docs/atlas/copernicus-common-generation.json')
    imagery=record('docs/atlas/swissimage-source-derived-baseline.json')
    definitions=[
      ('tryfan-welsh-regional-v2',welsh['manifestSha256']),
      ('riffelhorn-regional-terrain-v1',initial['manifestSha256']),
      ('riffelhorn-swiss-support-v1',sr['manifestSha256']),
      ('riffelhorn-copernicus-common-v1',cop['manifestSha256']),
      ('riffelhorn-swissimage-baseline-v1','3c8b50fb9d7721b678abc46b9450495b417ccafff15d4ee8a67d9d6a3fee4934')]
    products=[]
    for name,expected in definitions:
        prefix='derived/atlas/'+('tryfan/' if name.startswith('tryfan') else 'riffelhorn/')+name
        p=roots.data_path(prefix,'manifest.json',must_exist=True);h=digest(p)
        if h!=expected:raise ValueError('Retained manifest changed: '+name)
        manifest=json.loads(p.read_text(encoding='utf-8'));files=manifest['files']
        for f in files:
            path=(p.parent/f['path']).resolve()
            path.relative_to(p.parent.resolve())
            if path.stat().st_size!=f['bytes']:raise ValueError('Retained payload size drift: '+str(path))
        products.append({'id':name,'revision':manifest['identity'],'manifest':prefix+'/manifest.json','manifestSha256':h,'manifestBytes':p.stat().st_size,'groups':summarize(files),'payloadFilesStatChecked':len(files)})
    common=record('docs/atlas/copernicus-common-renderer.json');semantic=record('docs/atlas/semantic-comparison-sources.json');water=record('docs/atlas/water-check-sources.json')
    proof=record('docs/research/tryfan-qualified-query-results.json');pinned=record('docs/research/tryfan-qualified-query-inputs.json')
    compact=lambda obj:len(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
    contexts=[c['context'] for c in proof['evidence']['collections'][:-1]]
    claims=[c['claims'][0] for c in proof['evidence']['collections'][:-1]]
    uses=[r['receipt']['inputs'][0] for r in proof['results']]
    semfiles=semantic['files']
    return {'assessment':'atlas-storage-processing-serving-requirements','startingCheckpoint':'1c2d10e522f54e60f83bae2e416008bd1a241eb1','measurementScope':'Named manifests verified by SHA; listed payload sizes checked via stat, no payload hashing or reprocessing; repository receipt arithmetic and logical serialization sizes, not network/memory/throughput benchmarks. No directory-wide/private scan.',
      'evidenceSha256':receipts,'products':products,
      'reportedArchiveAndWorking':{'welsh':{'sourceBytes':welsh['source']['bytes'],'workingBytes':welsh['workingBytes'],'sourceAreaKm2':9},'swissOriginal':{'sourceBytes':sum(a['bytes'] for a in initial['source']['inputs']),'sourceAreaKm2':4},'swissSupport':{**support['preparationSummary'],'sourceAreaKm2':100},'copernicus':{'sourceBytes':cop['sourceBytes'],'workingBytes':cop['workingRasterBytes'],'generationSeconds':cop['generationSeconds'],'sourceAreaMeaning':'six 1-degree native COGs; delivered aligned rectangle differs from source footprint'},'imagery':imagery['storage']},
      'semanticReceipts':{'mountainFileEntries':len(semfiles),'mountainSourceDocumentBytes':sum(f['bytes'] for f in semfiles if 'bytes' in f),'mountainEntriesWithUnknownBytes':[f['file'] for f in semfiles if 'bytes' not in f],'worldcoverCropBytes':sum(f['bytes'] for f in semfiles if f['file'].endswith('-worldcover.tif')),'waterSourceDocumentBytes':water['retainedBytes'],'waterPriorRecordedDirectoryBytes':water['totalDirectoryBytes'],'qualification':'Receipts include documentation/excess smallest official units; not all are physical claim payloads; prior recorded directory size is not a current directory scan.'},
      'qualifiedProof':{'resultFileBytes':(REPO/'docs/research/tryfan-qualified-query-results.json').stat().st_size,'pinnedInputFileBytes':(REPO/'docs/research/tryfan-qualified-query-inputs.json').stat().st_size,'localTileBytes':sum(a['bytes'] for r in pinned['roots'] for a in r['assets']),'rootSubsets':len(pinned['roots']),'claimRevisions':len(proof['results']),'currentResults':len(proof['currentResults']),'recomputed':len(proof['recomputed']),'directInputUses':len(uses),'derivedOnDerivedUses':sum(u['kind']=='claim' for u in uses),'compactClaimsBytes':sum(map(compact,claims)),'compactContextsBytes':sum(map(compact,contexts)),'compactReceiptsBytes':sum(compact(r['receipt']) for r in proof['results']),'qualification':'Compact byte counts serialize logical components separately; sum is not total storage or one heavy object per raster cell. Trace/diagnostic repetition inflates full proof bundle.'},
      'reportedLocalDelivery':common['http'],
      'scalingIllustrations':{'kind':'hypothetical raw arithmetic; not measured compressed storage, source information, cost or recommended products','regionAreaKm2':1000,'oneMetreFloat32SingleBandBytes':raw_grid_bytes(1e9,1,1,4),'quarterMetreRGB8BaseBytes':raw_grid_bytes(1e9,.25,3,1),'quarterMetreRGB8IdealInfinitePyramidBytes':raw_grid_bytes(1e9,.25,3,1)*4/3,'fullXYZLevels0to13Addresses':sum(4**z for z in range(14))}}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=build();text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if args.check:
        if OUT.read_text(encoding='utf-8')!=text:raise SystemExit('Deterministic measurement drift')
    else:OUT.write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({'mode':'check' if args.check else 'record','sha256':digest(OUT),'products':len(result['products']),'payloadFilesStatChecked':sum(p['payloadFilesStatChecked'] for p in result['products'])}))
