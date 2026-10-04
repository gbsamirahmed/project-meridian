"""Compact durable record from retained captures, not an external CI test."""
import json
from collections import Counter
import numpy as np
import copernicus_common as cp
import riffelhorn_terrain as rt
from riffelhorn_support import save

def run():
    data=rt.resolve_storage_roots(require_data=True).data;root=data/cp.EXPERIMENT
    manifest=cp.verify(data)
    common=json.loads((root/'captures/common.json').read_text());aws=json.loads((root/'captures/aws.json').read_text())
    if common.get('failure') or aws.get('failure') or common['pageErrors'] or aws['pageErrors']:raise ValueError('Incomplete evaluation')
    if common['productionHashes']!=aws['productionHashes']:raise ValueError('Production drift')
    for r in common['records']:
        for layer in ['hillshade','elevation','sky']:
            if r['state'][layer]!=aws['records'][0]['state'][layer]:raise ValueError('Presentation drift')
    responses=common['responses'];failed=common['failedRequests'];sizes=[f['bytes']for f in manifest['files']]
    result={'productIdentity':manifest['identity'],'baseline':common['baseline'],'date':common['date'],'browser':common['browserVersion'],'viewport':common['viewport'],
        'productionFileHashes':common['productionHashes'],'rendering':{'hillshade':common['records'][0]['state']['hillshade'],'elevation':common['records'][0]['state']['elevation'],'sky':common['records'][0]['state']['sky'],'exaggeration':1.45,'meshSize':128,'commonAwsPresentationMatches':True},
        'scenes':[{'scene':r['scene'],'camera':r['state']['camera'],'projection':r['state']['projection'],'terrain':r['state']['terrain'],'centerVisualElevationExaggerated':r['state']['centerElevation'],'settleMs':r['settleMs'],'newTileResponses':r['newTileResponses'],
            'visibleSources':{s:{'canonicalZooms':sorted(set(t['z']for t in tiles)),'states':dict(Counter(t['state']for t in tiles)),'demDimensions':sorted(set(t['dim']for t in tiles if t.get('dim')))}for s,tiles in r['state']['visibleDEMs'].items()},
            'capture':{'href':'${MERIDIAN_DATA_ROOT}/'+cp.EXPERIMENT+'/captures/'+r['filename'],'sha256':r['sha256']}}for r in common['records']],
        'awsControls':[{'scene':r['scene'],'camera':r['state']['camera'],'centerVisualElevationExaggerated':r['state']['centerElevation'],'capture':{'href':'${MERIDIAN_DATA_ROOT}/'+cp.EXPERIMENT+'/captures/'+r['filename'],'sha256':r['sha256']}}for r in aws['records']],
        'http':{'responses':len(responses),'uniqueTileUrls':len(set(r['url']for r in responses)),'statusCounts':dict(Counter(r['status']for r in responses)),
            'responseBodyBytesIncludingCacheRepeats':sum(r.get('bytes',0)for r in responses),'bodyInterpretation':'Not network wire volume; browser-cache responses can expose status 200/body again.',
            'localFailedRequests':dict(Counter(r['error']for r in failed if ':4182/tiles/'in r['url'])),'otherFailedRequests':dict(Counter(r['error']for r in failed if ':4182/tiles/'not in r['url'])),
            'pageErrors':common['pageErrors'],'consoleErrors':common['consoleErrors'],'cachePolicy':sorted(set(r['cacheControl']for r in responses)),'cors':sorted(set(r['cors']for r in responses)),
            'separateProbes':{'conditionalEtag':304,'missingBelowMinimumZoom':404,'interpretation':'Manual loopback HTTP probes, outside browser capture counts; no AWS fallback or zero terrain.'}},
        'tileSizesBytes':dict(zip(['min','median','p95','max'],map(float,np.percentile(sizes,[0,50,95,100])))),
        'bytesByZoom':{str(z):sum(f['bytes']for f in manifest['files']if f['path'].startswith(f'tiles/{z}/'))for z in range(8,14)},
        'limitations':'Local Chromium/software environment with explicit unavailable Weather fixture; not universal browser/CDN benchmark. Globe guard checked but local source has no world terrain or z0-7 parents; perimeter falls to flat map. Close faceting also exists in AWS control; no renderer diagnosis or fix.'}
    save(cp.REPO/'docs/atlas/copernicus-common-renderer.json',result);save(root/'renderer-summary.json',result)
    print(json.dumps(result['http'],indent=2))

if __name__=='__main__':run()
