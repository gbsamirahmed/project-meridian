"""Read-only validation of a frozen pilot plan; no pilot runtime or store operations."""
from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT.parent / 'meridian-data'
BASE = 'f16ce63e7c8fd85b6465b0e2cdcd1d872e36df54'
PLAN = 'docs/research/tryfan-regional-pilot-plan.json'
OUT = 'docs/research/tryfan-regional-pilot-plan-results.json'
sys.path.insert(0, str(ROOT / 'scripts/atlas/pilot-acceptance'))
import assess as admission

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'

def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def safe_asset(root, path):
    # Evidence references are relative locators, never arbitrary or private paths.
    p = Path(path)
    require(not p.is_absolute() and '..' not in p.parts and 'meridian-private' not in path,
            'Unsafe retained locator')
    target = (root / p).resolve()
    require(target.is_relative_to(root.resolve()), 'Retained locator escapes data root')
    return target

def check_structure(p):
    require(p['schema'] == 'atlas-tryfan-regional-pilot-plan/v1' and p['startingCheckpoint'] == BASE,
            'Unknown plan schema or checkpoint')
    require(p['planningOnly'] and not p['nextTaskStarted'], 'Plan begins implementation')
    require(p['decision'] == 'C - IMPLEMENTABLE AS PLANNED' and p['nextTask'] ==
            'Tryfan pilot retained catalogue and immutable generation foundation', 'Wrong bounded next task')
    require(p['scope']['crs'] == 'EPSG:27700' and p['scope']['bounds'] == [264900,357800,267900,360800]
            and p['scope']['areaKm2'] == 9, 'Pilot support expanded')
    require([x['id'] for x in p['scope']['probes']] == ['summit','southern-observer','northern-context','outside'],
            'Inherited probe identities lost')
    require([x['id'] for x in p['families']] == ['terrain-common','terrain-regional','worldcover','nrw','appearance']
            and all(x['include'] for x in p['families']), 'Admission families changed')
    require(p['families'][3]['records'] == 193 and p['families'][3]['nativeCodes'] == 28,
            'Vector record/native vocabulary scope lost')
    require(p['families'][4]['identity'] == 'S2A_MSIL2A_20260712T113331_N0512_R080_T30UVD_20260712T174812'
            and p['families'][4]['observationUTC'] == '2026-07-12T11:33:31.024Z', 'Observation substituted')
    require(len(p['assets']) == 15 and len({x['path'] for x in p['assets']}) == 15
            and all(x['immutable'] for x in p['assets']), 'Duplicate/mutable retained input')
    for x in p['assets']:
        safe_asset(DATA, x['path'])
        require(len(x['sha256']) == 64 and x['bytes'] > 0, 'Missing retained identity')
    require(len(p['assetSets']) == 1 and p['assetSets'][0]['count'] == 295
            and p['assetSets'][0]['bytes'] == 23889573, 'Terrain manifest scope changed')
    require([x['family'] for x in p['registrationBindings']] == [x['id'] for x in p['families']] and
            all(x['source']['id'] and x['product']['id'] and x['metadata'] for x in p['registrationBindings']),
            'Concrete source/product registration references missing')
    require(p['scienceBasis']['selection']['requestedLevel'] == 'z14' and
            p['scienceBasis']['selection']['eligibilityReadHalfWidthM'] == 24 and
            len(p['scienceBasis']['historicalRefs']) == 4, 'Original selection/history context changed')
    require(p['query']['matrix'][-1]['property'] == 'place-evidence' and
            len(p['query']['matrix'][-1]['context']['fixedQuestions']) == 6, 'Integrated request not specified')
    require(p['scienceBasis']['contract'] == 'atlas-semantic-evidence/v1' and
            p['scienceBasis']['spacingMetres'] == 8 and p['scienceBasis']['properties'] == ['slope','area-ratio'] and
            p['scienceBasis']['counts'] == dict(initial=4,updatedTotal=6,current=4,historicalAWS=4,recomputed=2),
            'Original derivation basis changed')
    persist = p['persistence']; pub = p['publication']
    require(persist['immutable'] and persist['rootAtomic'] and persist['singleWriter'] and
            pub['allFamiliesSameRoot'] and pub['clientPinsGeneration'] and not pub['mutableGeneration'] and
            not pub['powerLossGuarantee'], 'Publication exceeds or weakens accepted boundary')
    require(persist['schema'] == 'atlas-tryfan-pilot-store/v1' and persist['semanticContract'] == 'atlas-semantic-evidence/v1', 'Store/contract version conflation')
    steps = pub['steps']
    require(len(steps) == len(set(steps)) and
            steps.index('validate-entire-candidate') < steps.index('write-flush-generation') <
            steps.index('write-flush-temp-pointer') < steps.index('atomic-rename-current'), 'Premature publication')
    require([u['id'] for u in p['updates']] == ['U1','U2'], 'Missing canonical or mixed update')
    u1,u2 = p['updates']
    require(u1['recompute'] == u2['recompute'] == 2 and u1['history'] == u2['history'] == 4,
            'Scoped recomputation/history changed')
    require(set(u1['unchanged']) >= {'southern-chain','WorldCover','NRW','appearance'}, 'Canonical unaffected evidence lost')
    require(set(u2['familiesChanged']) >= {'terrain','vector-inventory','derived-understanding'} and
            'all-native-evidence-bytes' in u2['unchanged'] and 'isolated' in u2['from'] and
            'registration/applicability' in u2['kind'], 'Mixed update fakes source change or replaces U1')
    require([f['id'] for f in p['failures']] == ['F1','F2','F3'], 'Failure injection coverage lost')
    routes = p['serving']['routes']
    require({r['path'] for r in routes if not r['generationRequired']} == {'/pilot/v1/current','/'},
            'Unpinned scientific read route')
    require(all('/g/{generation}/' in r['path'] for r in routes if r['generationRequired']),
            'Scientific request lacks generation')
    require(all(r['method'] == 'GET' or (r['method'] == 'POST' and r['path'].endswith('/query')) for r in routes),
            'HTTP writer or unbounded operation')
    require(p['serving']['limits'] == dict(requestBodyBytes=65536,workerQueue=32,readCacheBytes=67108864),
            'Missing finite serving bounds')
    require([q['id'] for q in p['query']['matrix']] == ['Q'+str(i).zfill(2) for i in range(1,22)] and
            all(q['probe'] in {x['id'] for x in p['scope']['probes']} for q in p['query']['matrix']),
            'Query fixture changed/unknown probe')
    require(p['query']['operationalStates'] == ['available','unavailable','invalid-request','excluded-by-context'],
            'Infrastructure/eligibility collapsed into physical unknown')
    require(p['acceptanceFrozen'] and [a['id'] for a in p['acceptance']] == list('ABCDEFGHIJKLMNOP'),
            'Acceptance cases missing/unfrozen')
    require(p['admission']['outstandingAcceptance'] == ['integrated-serving','mixed-family-coherent-publication'],
            'Outstanding admission obligations lost')
    ordered = []
    for sl in p['slices']:
        require(sl['id'] not in ordered and set(sl['dependsOn']).issubset(ordered), 'Slice dependency unordered/cyclic')
        require(sl['modules'] and all(m.startswith('pilots/atlas/tryfan/') and '..' not in Path(m).parts for m in sl['modules']),
                'Slice touches production/shared source')
        require(sl['stop'] and sl['acceptance'], 'Unbounded slice')
        ordered.append(sl['id'])
    require(ordered == ['S1','S2','S3','S4','S5','S6'], 'Slice scope changed')
    require(set(a for sl in p['slices'] for a in sl['acceptance']) == set('ABCDEFGHIJKLMNOP'), 'Exit test not assigned')
    for a in p['acceptance']:
        require(a['passCondition'], 'Missing acceptance condition')
    require(all(term in p['excluded'] for term in ['Weather','Traverse','newdata','production-renderer','meridian-private',
            'albedo','multiview','illumination-normalization','billing-Prime-Meridian']), 'Excluded responsibility reintroduced')
    require('productiondatabase' in p['defer'] and 'cloudprovider' in p['defer'] and 'CDN' in p['defer'] and
            not any(v in p['decideNow'] for v in p['defer']), 'Final infrastructure prematurely selected')
    require(p['instrumentation']['outsideIdentity'] and p['instrumentation']['productionSLA'] is None,
            'Metrics contaminate identity or invent SLA')
    return True

def assess():
    p = read(ROOT/PLAN)
    check_structure(p)
    require(digest(ROOT/p['admission']['manifest']) == p['admission']['sha256'], 'Admission altered')
    for f in p['foundations']:
        require(digest(ROOT/f['report']) == f['sha256'], 'Foundation report altered: '+f['report'])
    for metadata in p['metadataReceipts']:
        require(digest(ROOT/metadata['path']) == metadata['sha256'], 'Registration metadata altered')
    for path,h in p['scienceBasis']['methodFiles'].items():
        require(digest(ROOT/path) == h, 'Scientific method changed')
    for key in ['inputs','golden','protocol']:
        require(digest(ROOT/p['scienceBasis'][key]) == p['scienceBasis'][key+'Sha256'], 'Original proof basis changed')
    checked = {}
    for a in p['assets']:
        f = safe_asset(DATA,a['path'])
        require(f.stat().st_size == a['bytes'] and digest(f) == a['sha256'], 'Missing/corrupt retained asset '+a['path'])
        checked[a['path']] = dict(sha256=a['sha256'],bytes=a['bytes'])
    for group in p['assetSets']:
        manifest = safe_asset(DATA,group['manifest'])
        require(digest(manifest) == group['sha256'], 'Prepared manifest changed')
        entries = read(manifest)[group['entries']]
        require(len(entries) == group['count'] and sum(x['bytes'] for x in entries) == group['bytes'], 'Prepared inventory changed')
        for a in entries:
            relative = group['base']+'/'+a['path'];f=safe_asset(DATA,relative)
            require(f.stat().st_size == a['bytes'] and digest(f) == a['sha256'], 'Prepared payload changed')
            checked[relative] = dict(sha256=a['sha256'],bytes=a['bytes'])
    for relative in p['noImplementationPathsCreated']:
        require(not (ROOT/relative).exists(), 'Pilot implementation/store already created')
    return {'assessment':p['schema'],'startingCheckpoint':BASE,'decision':p['decision'],'planSha256':digest(ROOT/PLAN),
            'foundationReports':len(p['foundations']),'familyCount':len(p['families']),'selectedAssetCount':len(p['assets']),
            'uniqueRetainedFiles':len(checked),'retainedBytes':sum(a['bytes'] for a in checked.values()),
            'retainedInventorySha256':hashlib.sha256(encode(checked).encode()).hexdigest(),'sourceHashes':checked,
            'queryCases':21,'acceptanceCases':16,'orderedSlices':[s['id'] for s in p['slices']],
            'integratedServingImplemented':False,'mixedFamilyPublicationImplemented':False,'noPilotImplementation':True,
            'nextTask':p['nextTask'],'nextTaskStarted':False}

if __name__ == '__main__':
    value=assess();(ROOT/OUT).write_text(encode(value),encoding='utf-8',newline='\n')
    print(encode({k:v for k,v in value.items() if k!='sourceHashes'}))
