"""Verify diagnostic build/support identity and retain compact Atlas records."""
import copy
import json
from pathlib import Path
import regional_parents as p

sp, rt = p.sp, p.rt


def known(v):
    return {'status': 'known', 'value': v}


def unknown(reason):
    return {'status': 'unknown', 'reason': reason}


def finish(data):
    m = p.verify(data, parents=True); second = p.verify(data, '-rebuild', parents=False)
    if m != second:
        raise ValueError('Independent rebuild identity differs')
    for suffix in ['', '-rebuild']:
        if rt.repository_text_digest(data / (p.PRODUCT + suffix) / 'source-mosaic.vrt') != m['sourceVrtSha256']:
            raise ValueError('Source VRT lineage differs')
    original = json.loads((p.REPO / 'docs/atlas/riffelhorn-support-product.json').read_text(encoding='utf8'))['product']
    product = copy.deepcopy(original)
    product.update({'id': 'riffelhorn-swiss-regional-parents-diagnostic', 'name': 'Swiss-derived regional parent diagnostic (no spatial reconciliation)', 'version': known(p.VERSION), 'revision': known(m['identity'])})
    contributor = {'kind': 'source', 'id': 'swissalti3d-riffelhorn-support-selection', 'revision': known(m['sourceIdentity'])}
    product['vertical']['from'] = contributor
    base = '${MERIDIAN_DATA_ROOT}/' + p.PRODUCT
    ref = {'href': base + '/manifest.json', 'sha256': rt.digest(data / p.PRODUCT / 'manifest.json')}
    product['lineage'] = {'contributors': [contributor], 'contributorList': 'complete', 'spatialMapping': 'uniform',
        'processing': [{'method': m['basis'], 'software': m['software'], 'parameters': {'basisZoom': 14, 'verticalTransformation': 'none'}, 'record': ref},
                       {'method': m['parentRule'], 'parameters': {'minimumDiagnosticZoom': 10, 'partialMeanDeliverable': False}, 'record': ref}],
        'limitations': 'Only Swiss contributes to nonzero supported diagnostic cells. counts/4^(14-z) is retained base-cell support, not confidence or a Swiss/Copernicus blend. Original Swiss fine tiles remain immutable and are referenced by the separate evaluation stream.'}
    product['delivery'].update({'tileTemplate': base + '/tiles/{z}/{x}/{y}.png', 'zoom': {'min': 12, 'max': known(14)},
        'availability': '25 complete basis tiles at14, four derived at13, one at12; no complete tile at11/10. Offline NPZ fields at10-14 retain full, partial and absent support.',
        'resampling': known(m['parentRule'])})
    product['sourceInformation'] = {'description': 'Original 0.5 m distributed Swiss grid, not independent measurement resolution. z14 basis is area-averaged at about6.64 m locally; z13-10 summarize it. Original z14-18 delivery remains untouched.',
        'informationCeiling': known('No new observations or fine information beyond the Swiss source; diagnostic only coarsens the z14 signal. Not a regenerated complete fine pyramid.')}
    area = {'kind': 'asset', 'asset': ref, 'crs': known({'name': 'WGS 84 / Pseudo-Mercator', 'identifier': 'EPSG:3857'}),
            'interpretation': 'fields/z*.npz: nonzero counts mark supported subsets, fullCount marks complete cells; tile files mark complete delivered tiles. Tile envelopes include unsupported cells, not expanded Swiss coverage.'}
    product['spatial']['coverage'] = known(area)
    product['spatial']['validSupport'] = known({'area': area, 'purpose': 'Diagnostic coarse summaries of complete or explicitly partial Swiss support',
        'basis': 'Eight z14 cell-footprint checks plus finite source data; recursive exact support counts. Not production transition support or certified generic geometry.'})
    product['spatial']['transitionSupport'] = unknown('No geographic reconciliation tested or accepted. Same-level Swiss/common edge remains unsupported as a production join.')
    product['nodata'] = known('Count0 => NaN; partial => observed-subset mean with exact count, never delivered as a whole terrain tile. No common/AWS padding or zero terrain.')
    product.pop('fallback', None)
    product['generation'] = {'timestamp': unknown('Build time excluded from deterministic identity; execution durations retained separately'), 'buildRecord': ref}
    product['documentation'] = ['docs/atlas/regional-parent-diagnostic.md', 'docs/atlas/regional-parent-plan.json', 'docs/atlas/regional-parent-measurements.json']
    generation = json.loads((data / p.EXPERIMENT / 'generation.json').read_text(encoding='utf8'))
    checks = {'identity': m['identity'], 'rebuildIdentity': second['identity'], 'filesMatched': len(m['files']), 'basisTilesByteIdentical': m['basisTilesByteIdentical'],
              'maxQuantizationM': m['maxQuantizationM'], 'levels': m['levels'], 'generation': generation,
              'rebuildGeneration': json.loads((data / p.EXPERIMENT / 'generation-rebuild.json').read_text(encoding='utf8')),
              'fileHashList': m['files'], 'parents': m['parents']}
    adapter = p.h.Hierarchy(data, 14, '-regional-parent-control', verify=False)
    inventory = adapter.inventory()
    checks['adapterCache'] = {'identity': inventory['identity'], 'tiles': len(inventory['files']),
        'tileBytes': sum(r['bytes'] for r in inventory['files']),
        'maskBytes': sum((adapter.out / r['maskPath']).stat().st_size for r in inventory['files'])}
    sp.save(data / p.EXPERIMENT / 'adapter-inventory.json', checks['adapterCache'])
    sp.save(p.REPO / 'docs/atlas/regional-parent-product.json', {'schemaVersion': 1, 'product': product, 'checks': checks})
    sp.save(data / p.PRODUCT / 'atlas-metadata.json', product)
    summaries = {}
    for key, provider, directory in [('control', 'control', 'captures'), ('regional', 'regional', 'captures'), ('control-oblique', 'control', 'oblique'), ('regional-oblique', 'regional', 'oblique')]:
        path = data / p.EXPERIMENT / directory / (provider + '.json')
        if not path.exists():
            continue
        raw = json.loads(path.read_text(encoding='utf8')); records = []
        for row in raw['records']:
            state = row['state']
            records.append({'scene': row['scene'], 'camera': state['camera'], 'bounds': state['bounds'], 'centerExaggeratedElevation': state['centerElevation'],
                'usedDEMLevels': sorted(set(t['z'] for t in state['usedDEMs'])), 'geometryLevels': sorted(set(t['z'] for t in state['visibleDEMs']['terrain-dem'])),
                'reliefLevels': sorted(set(t['z'] for t in state['visibleDEMs']['terrain-analysis-dem'])), 'captureSha256': row['sha256'], 'filename': row['filename'], 'newTileResponses': row['newTileResponses']})
        summaries[key] = {'sourceReportSha256': rt.digest(path), 'browserVersion': raw['browserVersion'], 'viewport': raw['viewport'], 'records': records,
            'navigation': raw.get('navigation', []), 'responses': len(raw['responses']), 'statusCounts': {str(s): sum(r['status'] == s for r in raw['responses']) for s in set(r['status'] for r in raw['responses'])},
            'contributorResponseCounts': {str(s): sum(r.get('contributor') == s for r in raw['responses']) for s in set(r.get('contributor') for r in raw['responses'])},
            'responseBytes': sum(r.get('bytes', 0) for r in raw['responses']), 'failedRequests': raw['failedRequests'], 'pageErrors': raw['pageErrors'], 'failure': raw.get('failure'), 'productionHashes': raw['productionHashes']}
    sp.save(p.REPO / 'docs/atlas/regional-parent-renderer.json', summaries)
    print(json.dumps({'identity': m['identity'], 'files': len(m['files']), 'generation': generation, 'captures': list(summaries)}, indent=2))


if __name__ == '__main__':
    finish(rt.resolve_storage_roots(require_data=True).data)
