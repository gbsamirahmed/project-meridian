"""Compare two complete products; keep wall-clock metrics outside build identity."""
import argparse
import json
import riffelhorn_support as support
import riffelhorn_terrain as terrain


def compare(data, suffix):
    if not suffix or '/' in suffix or '\\' in suffix:
        raise ValueError('A separate sibling-product suffix is required')
    primary = data / support.PRODUCT
    rebuilt = data / (support.PRODUCT + suffix)
    original = json.loads((primary / 'manifest.json').read_text(encoding='utf8'))
    repeated = json.loads((rebuilt / 'manifest.json').read_text(encoding='utf8'))
    if original != repeated:
        raise ValueError('Rebuild manifest differs')
    for tile in original['files']:
        if terrain.digest(primary / tile['path']) != tile['sha256'] or terrain.digest(rebuilt / tile['path']) != tile['sha256']:
            raise ValueError('Rebuild tile differs: ' + tile['path'])
    if terrain.digest(primary / 'source-mosaic.vrt') != terrain.digest(rebuilt / 'source-mosaic.vrt'):
        raise ValueError('Source mosaic differs')
    record = {
        'productIdentity': original['identity'],
        'independentCompleteRebuild': True,
        'tileCount': len(original['files']),
        'allTileHashesMatch': True,
        'manifestSha256': terrain.digest(primary / 'manifest.json'),
        'sourceMosaicSha256': terrain.digest(primary / 'source-mosaic.vrt'),
        'generation': json.loads((data / support.EXPERIMENT / 'generation-metrics.json').read_text(encoding='utf8')),
        'rebuild': json.loads((data / support.EXPERIMENT / ('generation-metrics' + suffix + '.json')).read_text(encoding='utf8')),
    }
    support.save(support.REPO / 'docs/atlas/riffelhorn-support-reproducibility.json', record)
    print('IDENTICAL COMPLETE REBUILD', record['productIdentity'], record['tileCount'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix', default='-rebuild-check')
    args = parser.parse_args()
    compare(terrain.resolve_storage_roots(require_data=True).data, args.suffix)
