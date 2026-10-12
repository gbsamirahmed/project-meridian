"""Read-only simplification investigation on declared retained contour families."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ[key]='1'
os.environ['PROJ_NETWORK']='OFF';os.environ['GDAL_PAM_ENABLED']='NO'
import argparse
import hashlib
import json
from pathlib import Path
import time
from pilot import memory, canonical, digest
from topology_generalisation import conservative_simplify

def investigate(data_root, output):
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    root = data_root/'experiments/atlas/source-aware-contours-v1'
    inventory = root/'execution-3/inventory.json'
    expected = json.loads(Path(__file__).with_name('genuine-rerun-receipt.json').read_text())
    if digest(inventory) != expected['inventorySha256']:
        raise ValueError('Retained inventory identity changed')
    sealed = {item['path']:item for item in json.loads(inventory.read_text())['inventory']}
    results = {}
    for product in ('swiss-native','swiss-2m','swiss-smoothed'):
        family = [];hashes = {}
        for level in (2490,2500,2510):
            relative = f'execution-3/processing/run-1/{product}/{level}.ndjson'
            path = root/relative
            if digest(path) != sealed[relative]['sha256']: raise ValueError('Changed contour evidence')
            hashes[str(level)] = digest(path)
            with path.open('rb') as stream:
                for body in stream:
                    family.append(json.loads(body)['coordinates'])
        vertices = sum(map(len,family))
        if vertices*3 > 100_000: raise ValueError('Declared temporary geometry bound')
        # Replay the candidate calculation, never source raster processing. Only
        # hashes/counts are retained; original masters remain the usable evidence.
        first,stats = conservative_simplify(family)
        payload_hash = hashlib.sha256(canonical(first)).hexdigest()
        del first
        second,again = conservative_simplify(family)
        if stats != again or hashlib.sha256(canonical(second)).hexdigest() != payload_hash:
            raise ValueError('Generalisation replay differs')
        del second
        results[product] = {'levelsMetres':[2490,2500,2510], 'lineCount':len(family),
            'inputHashes':hashes,'candidatePayloadSha256':payload_hash,
            'repeatabilityWithinSelectedFamily':True, 'statistics':stats,
            'temporaryGeometryReservationVertices':vertices*3,
            'fullProductTopologyValidated':False,'simplifiedOutputAdopted':False}
        if time.monotonic()-started > 60: raise ValueError('Investigation elapsed limit')
    receipt = {'products':results,'elapsedSeconds':time.monotonic()-started,
        'peakWorkingSetBytes':memory()[1],'requests':0,'sourceDEMsOpened':0,
        'retainedScientificOutputsModified':False,'generatedContourPayloadFiles':0}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt),flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); investigate(args.data_root,args.output)
