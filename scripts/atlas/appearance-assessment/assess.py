"""Finite retained-metadata assessment, not an AppearanceHierarchy or imagery processor.
Read-only external assets; output only the small repository assessment receipt.
"""
from pathlib import Path
import hashlib, json, math
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT.parent / 'meridian-data'
PRODUCT = DATA / 'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1'
OUT = ROOT / 'docs/research/riffelhorn-appearance-assessment-results.json'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def intersect(a, b):
    c = [max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])]
    return c if c[0] < c[2] and c[1] < c[3] else None

def support(bounds, point=None, area=None):
    if (point is None) == (area is None):
        raise ValueError('Exactly one point or area required')
    coordinates = point if point is not None else area
    if len(coordinates) != (2 if point is not None else 4) or not all(math.isfinite(v) for v in coordinates):
        raise ValueError('Finite native coordinates required')
    if area is not None and (area[0] >= area[2] or area[1] >= area[3]):
        raise ValueError('Positive-area support required')
    if point is not None:
        inside = bounds[0] <= point[0] < bounds[2] and bounds[1] <= point[1] < bounds[3]
        return {'relation': 'inside' if inside else 'outside', 'crs': 'EPSG:2056', 'point': point}
    clip = intersect(bounds, area)
    return {'relation': 'outside' if clip is None else 'inside' if clip == area else 'partial',
            'crs': 'EPSG:2056', 'requested': area, 'supportedIntersection': clip}

def level(levels, sample):
    if not math.isfinite(sample) or sample <= 0:
        raise ValueError('Positive finite delivery sampling budget required')
    # Declared proof policy: coarsest available sampling no larger than budget.
    # This is not an information-quality ranking or screen-space LOD algorithm.
    eligible = [x for x in levels if x['groundSampleMetresAtRiffelhorn'] <= sample]
    return min(eligible, key=lambda x: x['zoom']) if eligible else max(levels, key=lambda x: x['zoom'])

def assess(manifest, query):
    s = support(manifest['sourceBounds'], point=query.get('point'), area=query.get('area'))
    purpose = query['purpose']
    if purpose in ('illumination-independent', 'corrected-appearance'):
        return {'kind': 'unsupported', 'reason': 'no retained estimate of requested processing/physical class', 'support': s,
                'ordinaryRGBSubstituted': False}
    if purpose == 'acquisition-geometry':
        return {'kind': 'known-unknown', 'support': s, 'acquisition': manifest['acquisition'],
                'upstreamOrthorectificationGeometry': 'UNKNOWN', 'radiometricCalibration': 'UNKNOWN',
                'geometry2026Substituted': False} if s['relation'] != 'outside' else {'kind': 'outside-support', 'support': s}
    if purpose not in ('source-derived', 'map-display'):
        raise ValueError('Unassessed purpose')
    if query.get('requireCurrentState'):
        return {'kind': 'unsupported', 'reason': '2023 mosaic is not a current-state assertion', 'support': s}
    if s['relation'] == 'outside':
        return {'kind': 'outside-support' if query.get('pinnedRegional') else 'conditional-display-service',
                'support': s, 'candidate': None if query.get('pinnedRegional') else 'maptiler-satellite-v2',
                'liveAvailabilityVerified': False, 'equivalentRegionalProvenance': False}
    selected = level(manifest['levels'], query['deliveryBudgetMetres'])
    return {'kind': 'qualified-regional' if s['relation'] == 'inside' else 'partial-regional',
            'support': s, 'product': manifest['id'], 'revision': manifest['identity'],
            'representation': {'zoom': selected['zoom'], 'groundSamplingMetresAtRiffelhorn': selected['groundSampleMetresAtRiffelhorn']},
            'origin': manifest['origin'], 'acquisition': manifest['acquisition'],
            'lineage': manifest['lineage'], 'rights': manifest['rights'],
            'scale': {'distributedGridMetres': manifest['distributedGridMetres'],
                      'nominalSourceInformationMetres': manifest['nominalSourceInformationMetres'],
                      'newInformationFromResampling': False},
            'limitations': ['processed RGB, not albedo', 'visibility and per-pixel acquisition geometry unknown',
                            'source illumination retained', 'alpha is support, not confidence'],
            'outsidePart': 'unresolved; optional conditional MapTiler display candidate' if s['relation'] == 'partial' else None}

def alpha_at(manifest, point, zoom):
    # Inspect delivery support only. No RGB statistics, classification or correction.
    import numpy as np
    x, y = Transformer.from_crs(manifest['nativeCRS'], manifest['delivery']['crs'], always_xy=True).transform(*point)
    size = manifest['delivery']['tileSize']
    half = math.pi * 6378137
    px = (x + half) / (2 * half) * (2 ** zoom) * size
    py = (half - y) / (2 * half) * (2 ** zoom) * size
    tx, ty = math.floor(px / size), math.floor(py / size)
    field = PRODUCT / f'fields/{zoom}/{tx}/{ty}.npz'
    if not field.exists():
        return {'zoom': zoom, 'tile': [tx, ty], 'delivered': False, 'alpha': None}
    with np.load(field) as data:
        alpha = float(data['rgba'][3, math.floor(py) % size, math.floor(px) % size])
    return {'zoom': zoom, 'tile': [tx, ty], 'delivered': True, 'alpha': alpha,
            'meaning': 'area-support fraction; no visibility/confidence assertion'}

def verify_entries(root, entries, path_key):
    total = 0
    for entry in entries:
        path = root / entry[path_key]
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError('Retained asset changed: ' + str(path))
        total += entry['bytes']
    return {'files': len(entries), 'bytes': total, 'allHashesMatch': True}

def build():
    baseline_path = ROOT / 'docs/atlas/swissimage-source-derived-baseline.json'
    baseline = read(baseline_path)
    m = read(PRODUCT / 'manifest.json')
    # Identity comes from retained authoritative metadata, never newly invented names.
    if m['sources'] != baseline['source']['assets'] or m['identity'] != baseline['product']['identity'] or m['recipeSha256'] != baseline['product']['recipeSha256']:
        raise ValueError('Baseline and retained manifest source records differ')
    sources = verify_entries(DATA, m['sources'], 'path')
    prepared = verify_entries(PRODUCT, m['files'], 'path')
    multiview_path = ROOT / 'docs/atlas/swiss-multiview-input-manifest.json'
    multi = read(multiview_path)
    multiview = verify_entries(DATA / 'experiments/atlas/swiss-alpine-multiview-discovery-v1', multi['files'], 'file')
    if not multi['noAerialPixels']:
        raise ValueError('Parked pixel assumption changed')
    queries = {
        'A-ordinary': {'purpose': 'source-derived', 'point': [2625240, 1092530], 'deliveryBudgetMetres': 1},
        'B-steep': {'purpose': 'source-derived', 'point': [2624805, 1092330], 'deliveryBudgetMetres': 0.25},
        'C-outside-display': {'purpose': 'map-display', 'point': [2623900, 1092000]},
        'C-outside-pinned': {'purpose': 'source-derived', 'point': [2623900, 1092000], 'pinnedRegional': True},
        'D-physical': {'purpose': 'illumination-independent', 'point': [2625240, 1092530]},
        'E-geometry': {'purpose': 'acquisition-geometry', 'point': [2624805, 1092330]},
        'boundary': {'purpose': 'source-derived', 'area': [2623990, 1091990, 2624010, 1092010], 'deliveryBudgetMetres': 1},
        'regional-parent': {'purpose': 'source-derived', 'point': [2625240, 1092530], 'deliveryBudgetMetres': 14},
        'current-state': {'purpose': 'source-derived', 'point': [2625240, 1092530], 'requireCurrentState': True},
    }
    answers = {key: {'query': query, 'answer': assess(m, query)} for key, query in queries.items()}
    answers['B-steep']['answer']['retainedPatchQualification'] = {
        'source': 'docs/atlas/swissimage-source-derived-baseline.json#sourcePatches.steep',
        'surfaceAreaFactorP05P50P95': baseline['sourcePatches']['steep']['surfaceAreaFactorP05P50P95'],
        'nominalTangentFootprintMetresP05P50P95': baseline['sourcePatches']['steep']['nominalTangentFootprintMetresP05P50P95'],
        'meaning': 'retained whole 60m patch; not occlusion or confidence'}
    alpha = [alpha_at(m, p, z) for p, z in [([2625240,1092530],18),([2624805,1092330],18),
            ([2625240,1092530],12),([2624000,1092000],18),([2623990,1092000],18)]]
    mp = ROOT / 'docs/atlas/appearance-baseline-metadata.json'
    facts = {'manifestSha256': digest(PRODUCT / 'manifest.json'), 'productIdentity': m['identity'],
             'recipeSha256': m['recipeSha256'], 'sourceVerification': sources, 'preparedVerification': prepared,
             'parkedMetadataVerification': multiview, 'noAerialPixels': True,
             'support': m['sourceBounds'],
             'levels': [{**{k:v for k,v in item.items() if k != 'tiles'}, 'tileCount': len(item['tiles'])} for item in m['levels']],
             'delivery': m['delivery'],
             'footprintAttribution': 'Source asset footprints are known; contributing raw exposures per location are UNKNOWN',
             'queries': answers, 'deliveryAlphaChecks': alpha,
             'maptilerRetainedMetadata': read(mp),
             'scenarioF': {'kind': 'conceptual-only', 'frameBenchmarkSeparateFrom2023': True,
                           'multipleSourceReferences': True, 'perObservationGeometry': True,
                           'pushbroomTimeDependentGeometryNotFramePose': True, 'fusedRepresentationExists': False},
             'sourceFamily': baseline['source']['sourceFamily'], 'sourceMetadata': baseline['source'],
             'inputMetadataSha256': {str(p.relative_to(ROOT)).replace('\\','/'): digest(p) for p in [baseline_path,mp,multiview_path]}}
    logical = json.dumps(facts, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
    return {'assessment': 'riffelhorn-appearance-metadata/v1', 'decision': 'C - SUCCESS',
            'resolutionConclusion': 'B - generic machinery plus bounded appearance-specific eligibility',
            'methodSha256': digest(Path(__file__)), 'logicalSha256': hashlib.sha256(logical).hexdigest(), 'logical': facts}

if __name__ == '__main__':
    result = build()
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'decision': result['decision'], 'logicalSha256': result['logicalSha256'],
                     'sources': result['logical']['sourceVerification'], 'prepared': result['logical']['preparedVerification'],
                     'alpha': result['logical']['deliveryAlphaChecks']}, ensure_ascii=True))
