"""Frozen adapter for the resource variant; no fixture data enters SharedProjection."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
from shared import SharedProjection
from conformance import first_difference


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--projection', required=True); parser.add_argument('--fixtures', required=True)
    args = parser.parse_args(); root = Path(args.fixtures)
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    for name, seal in manifest['files'].items():
        raw = (root/name).read_bytes()
        if len(raw) != seal['bytes'] or hashlib.sha256(raw).hexdigest() != seal['sha256']:
            raise ValueError('Frozen fixture seal differs.')
    requests = json.loads((root/'requests.json').read_text(encoding='utf-8'))['cases']
    expected = json.loads((root/'expected.json').read_text(encoding='utf-8'))['cases']
    docs = json.loads((root/'documents.json').read_text(encoding='utf-8'))['documents']
    projection = json.loads((Path(args.projection)/'manifest.json').read_text(encoding='utf-8'))
    passed = failed = errors = 0; views = {}
    with SharedProjection(args.projection, projection['projectionIdentity']) as owner:
        try:
            for case in requests:
                pin = manifest['publications'][case['publication']]['generation']
                if pin not in views: views[pin] = owner.pin(pin)
                actual = views[pin].outcome(case['query']); wanted = expected[case['id']]
                if wanted['kind'] == 'answer':
                    wanted = {'kind':'answer', 'value':{**wanted['value'], 'documents':{ref:docs[ref] for ref in wanted['documentRefs']}}}
                else: errors += 1
                difference = first_difference(wanted, actual)
                if difference: failed += 1
                else: passed += 1
                print(json.dumps({'case':case['id'], 'status':'FAIL' if difference else 'PASS', 'difference':difference}))
            print(json.dumps({'summary':{'selected':len(requests), 'passed':passed, 'failed':failed, 'skipped':0, 'expectedErrors':errors}, 'ownerOpenMs':owner.open_ms, 'pinnedViews':len(views)}))
        finally:
            for view in views.values(): view.close()
    return 1 if failed else 0

if __name__ == '__main__': sys.exit(run())
