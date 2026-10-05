"""Compact verified evidence ledger; does not generate or adjust terrain."""
import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
import two_band_transition as tb


def run(data):
    product=Path(data)/tb.PRODUCT; folder=Path(data)/tb.EXPERIMENT
    load=lambda p:json.loads(p.read_text(encoding='utf8'))
    manifest=load(product/'manifest.json')
    rebuilt=load(Path(str(product)+'-rebuild')/'manifest.json')
    assert rebuilt==manifest
    verification=load(folder/'output-verification.json')
    assert verification['inventoryIdentity']==manifest['identity']
    rows={row['path']:row for row in manifest['files']}
    inventory={}
    for strategy in sorted({r['strategy'] for r in rows.values()}):
        selected=[r for r in rows.values() if r['strategy']==strategy]
        sizes=sorted(r['bytes'] for r in selected)
        inventory[strategy]={'tileCount':len(selected),'byZoom':dict(sorted(Counter(str(r['z']) for r in selected).items(),key=lambda p:int(p[0]))),
            'pngBytes':sum(sizes),'maskBytes':sum((product/r['maskPath']).stat().st_size for r in selected),
            'representativePngBytes':{'minimum':sizes[0],'median':sizes[len(sizes)//2],'maximum':sizes[-1]}}
    captureFiles=[*sorted((folder/'captures').glob('*.json')),
                  folder/'common-navigation-control/common-navigation.json']
    captureFiles=[p for p in captureFiles if p.name!='satellite-readiness-attempt.json']
    reports=[]; total=Counter(); levels=set(); mesh=set(); production=None
    for path in captureFiles:
        report=load(path)
        assert not report.get('failure') and not report['pageErrors']
        if production is None:production=report['productionHashes']
        assert production==report['productionHashes']
        for name,digest in production.items():assert tb.rt.digest(tb.REPO/name)==digest
        for response in report['responses']:
            assert response['status']==200 and response['build']==manifest['config']['identity']
            key=urlsplit(response['url']).path.lstrip('/')
            assert key in rows
            levels.add(int(key.split('/')[2]))
            if not response.get('bodyUnavailable'):assert response['sha256']==rows[key]['sha256']
        for failure in report['failedRequests']:assert failure['error']=='net::ERR_ABORTED'
        states=[r['state'] for r in report['records']]
        states.extend(frame for n in report['navigation'] for frame in n['frames'])
        for state in states:
            mesh.update(d['z'] for d in state['usedDEMs'])
            assert state['terrain']=={'source':'terrain-dem','exaggeration':1.45}
            assert state['meshSize']==128
            assert state['hillshade']['paint']['hillshade-method']=='igor'
        localCancelled=sum('127.0.0.1:4185/tiles/' in r['url'] for r in report['failedRequests'])
        row={'file':path.relative_to(folder).as_posix(),'sha256':tb.rt.digest(path),
            'records':len(report['records']),'navigationSegments':len(report['navigation']),
            'terrainResponses':len(report['responses']),
            'completedBodies':sum(not r.get('bodyUnavailable') for r in report['responses']),
            'bodyUnavailable':sum(bool(r.get('bodyUnavailable')) for r in report['responses']),
            'cancelledTerrainRequests':localCancelled,'allCancelledRequests':len(report['failedRequests']),
            'consoleErrors':len(report['consoleErrors']),'browserVersion':report['browserVersion']}
        reports.append(row)
        total.update({k:row[k] for k in ['records','navigationSegments','terrainResponses','completedBodies','bodyUnavailable','cancelledTerrainRequests','allCancelledRequests','consoleErrors']})
    m=load(folder/'measurements.json'); independent=load(folder/'independent-checks.json')
    preflight=load(product/'preflight.json')
    diagnostic=load(folder/'diagnostic-rebuild.json');assert diagnostic['identical']
    for name,digest in diagnostic['files'].items():assert tb.rt.digest(folder/name)==digest
    for name in ['measurements.json','independent-checks.json','collar-lod.json','coarse-handoff.json','output-verification.json']:
        assert (folder/name).exists()
    completion={'schemaVersion':1,'baseline':'53b9efbc9e1e2d9393291a1b3fe90abcfcf3f7d0',
        'classification':'PARTIAL-ARCHITECTURALLY-USEFUL','productionChanged':False,
        'nextTask':'Atlas Terrain Hierarchy Contract; no further Riffelhorn elevation-method experiment',
        'build':manifest['config'],'inventoryIdentity':manifest['identity'],'inventory':inventory,
        'independentFullInventoryRebuildIdentical':True,'diagnosticRebuild':diagnostic,
        'verification':verification,
        'numerical':{k:m[k] for k in ['protectedSamples','protectedUnencodedDifference','outsideUnencodedDifference','protectedFineDeliveredDifference','boundaries','inducedGradient','lod','fineDetailEquations','radialBands']},
        'independentChecks':independent,'coarseHandoff':load(folder/'coarse-handoff.json'),
        'collarLod':load(folder/'collar-lod.json'),
        'captures':reports,'captureTotals':dict(total),'requestedTerrainLevels':sorted(levels),'usedMeshLevels':sorted(mesh),
        'productionHashes':production,
        'interpretation':'All accepted terrain response bodies verified against final output hashes. Request failures are navigation cancellations. Screenshot bytes/animation timing are not deterministic terrain claims. Shared pure-common control reproduces southern close-camera clipping; exact rendering cause is unestablished. Synthetic local pits and lower source-family handoff prevent full success.',
        'externalRecords':{name:tb.rt.digest(folder/name) for name in ['measurements.json','independent-checks.json','collar-lod.json','coarse-handoff.json','output-verification.json']},
        'supportPreflight':{'sha256':tb.rt.digest(product/'preflight.json'),'complete':preflight['complete'],
            'levels':{z:{'requiredTileCount':len(v['requiredTiles']),'missing':v['missing'],'supportedCircleCells':v['supportedCircleCells']} for z,v in preflight['levels'].items()}},
        'implementationFiles':{p.name:tb.rt.repository_text_digest(p) for p in sorted((tb.REPO/'scripts/atlas').glob('*two_band*')) if p.is_file()},
        'sourceIdentityPolicy':'Canonical source hashes and immutable product identities are verified by seam_corridor.verify_inputs; each used source PNG rechecked on read. No source writing operation.'}
    _,products,_,_,sourceVerification=tb.sc.verify_inputs(Path(data))
    assert {k:v['identity'] for k,v in products.items()}==manifest['config']['products']
    completion['finalSourceVerification']=sourceVerification
    tb.sp.save(tb.REPO/'docs/atlas/two-band-completion.json',completion)
    print(json.dumps({'inventory':inventory,'totals':dict(total),'identity':manifest['identity'],'diagnostics':diagnostic['count']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',type=Path,required=True)
    run(parser.parse_args().data)
