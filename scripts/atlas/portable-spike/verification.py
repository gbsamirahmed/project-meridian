"""Bounded projection verification and captured native payloads; no authority imports."""
from pathlib import Path
import hashlib
import json
import math
import os
import re
import stat
from rasterio.io import MemoryFile
from shapely.geometry import shape
from reader import ReadError, require, identity, finite_numbers

MAX_BYTES = 160 * 1024 * 1024
MAX_JSON = 8 * 1024 * 1024
MAX_MANIFEST = 64 * 1024
HEX = re.compile(r'[0-9a-f]{64}')

def digest(value):
    return isinstance(value, str) and HEX.fullmatch(value) is not None

def ordinary(path):
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode) and not (getattr(s, 'st_file_attributes', 0) & 1024),
            'projection-integrity', 'Projection members must be ordinary files, not links or directories.')
    return s

def bounded_bytes(path, limit, seal=None):
    s = ordinary(path)
    require(0 < s.st_size <= limit, 'projection-integrity', 'Projection member exceeds byte bound.')
    if seal: require(s.st_size == seal['bytes'], 'projection-integrity', 'Projection member size differs.')
    with path.open('rb') as stream: raw = stream.read(limit + 1)
    require(len(raw) == s.st_size and len(raw) <= limit, 'projection-integrity', 'Projection changed during capture.')
    if seal: require(hashlib.sha256(raw).hexdigest() == seal['sha256'], 'projection-integrity', 'Projection member identity differs.')
    return raw

def json_value(raw):
    # Check nesting before the recursive decoder allocates a structure.
    depth = 0; quoted = False; escaped = False
    try: text = raw.decode('utf-8-sig')
    except UnicodeError as e: raise ReadError('projection-integrity', 'Invalid UTF-8 JSON.') from e
    for c in text:
        if quoted:
            if escaped: escaped = False
            elif c == '\\': escaped = True
            elif c == '"': quoted = False
        elif c == '"': quoted = True
        elif c in '[{':
            depth += 1
            require(depth <= 64, 'projection-integrity', 'JSON nesting exceeds profile bound.')
        elif c in ']}': depth -= 1
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'projection-integrity', 'Duplicate JSON key.')
            result[key] = value
        return result
    def integer(token):
        require(len(token) <= 20 and abs(int(token)) <= 9007199254740991, 'projection-integrity', 'Unsafe JSON integer.')
        return int(token)
    def invalid_constant(_):
        raise ReadError('projection-integrity', 'Nonfinite JSON number.')
    try: value = json.loads(text, object_pairs_hook=pairs, parse_int=integer, parse_constant=invalid_constant)
    except json.JSONDecodeError as e: raise ReadError('projection-integrity', 'Malformed JSON member.') from e
    stack = [value]; count = 0
    while stack:
        item = stack.pop(); count += 1
        require(count <= 1000000, 'projection-integrity', 'JSON structure exceeds node bound.')
        if isinstance(item, dict): stack.extend(item.keys()); stack.extend(item.values())
        elif isinstance(item, list): stack.extend(item)
        elif isinstance(item, float): require(math.isfinite(item), 'projection-integrity', 'Nonfinite JSON number.')
        elif isinstance(item, str):
            require(not any(0xD800 <= ord(c) <= 0xDFFF for c in item), 'projection-integrity', 'Invalid Unicode surrogate.')
    return value

def _manifest_at(root, expected=None):
    root = Path(root)
    require(not root.is_symlink() and not root.is_junction(), 'projection-integrity', 'Linked projection root is unsupported.')
    m = json_value(bounded_bytes(root / 'manifest.json', MAX_MANIFEST))
    require(isinstance(m, dict), 'projection-integrity', 'Manifest must be an object.')
    require(m.get('schema') == 'atlas-read-projection-spike/v1' and m.get('profile') == 'meridian-atlas-read-contract/v1',
            'projection-incompatible', 'Unsupported projection schema/profile.')
    require(set(m) == {'schema','profile','referenceCheckpoint','preparedRevision','core','crs','pins','rasterFiles','files','coverage','projectionIdentity'},
            'projection-integrity', 'Unexpected or incomplete manifest fields.')
    require(digest(m['projectionIdentity']) and identity({k:v for k,v in m.items() if k != 'projectionIdentity'}) == m['projectionIdentity'],
            'projection-integrity', 'Projection manifest identity differs.')
    if expected is not None: require(m['projectionIdentity'] == expected, 'projection-integrity', 'Expected projection identity differs.')
    require(m['core'] == [2624000,1091000,2626000,1093000] and m['crs'] == 'EPSG:2056', 'projection-incompatible', 'Unsupported profile applicability.')
    require(digest(m['preparedRevision']) and isinstance(m['referenceCheckpoint'], str) and re.fullmatch('[0-9a-f]{40}', m['referenceCheckpoint']) is not None, 'projection-integrity', 'Invalid projection revision.')
    require(isinstance(m['pins'], dict) and 1 <= len(m['pins']) <= 3 and isinstance(m['rasterFiles'], dict) and len(m['rasterFiles']) == 6,
            'projection-integrity', 'Invalid profile population bound.')
    for pin, entry in m['pins'].items():
        require(digest(pin) and set(entry) == {'file','fingerprint','alias','records'} and entry['file'] == pin + '.json'
                and digest(entry['fingerprint']) and isinstance(entry['alias'],str)
                and type(entry['records']) is int and 1 <= entry['records'] <= 128, 'projection-integrity', 'Invalid generation entry.')
    require(isinstance(m['files'], dict) and len(m['files']) <= 16, 'projection-integrity', 'Invalid member count.')
    required = {'features.json','worldcover.json'} | {p['file'] for p in m['pins'].values()} | set(m['rasterFiles'].values())
    require(set(m['files']) == required, 'projection-integrity', 'Required projection closure differs.')
    for name, seal in m['files'].items():
        require(isinstance(name,str) and re.fullmatch(r'(features|worldcover|[0-9a-f]{64})\.(json|tif)',name) is not None,
                'projection-integrity', 'Unsafe projection member name.')
        require(isinstance(seal,dict) and set(seal) == {'bytes','sha256'} and type(seal['bytes']) is int
                and 0 < seal['bytes'] <= MAX_BYTES and digest(seal['sha256']), 'projection-integrity', 'Invalid member seal.')
    require(sum(s['bytes'] for s in m['files'].values()) <= MAX_BYTES, 'projection-integrity', 'Projection exceeds declared bound.')
    present = set()
    with os.scandir(root) as entries:
        for entry in entries:
            present.add(entry.name)
            require(len(present) <= 17, 'projection-integrity', 'Physical member count exceeds profile bound.')
    require(required | {'manifest.json'} <= present, 'projection-unavailable', 'Missing projection member.')
    require(present == required | {'manifest.json'}, 'projection-integrity', 'Unexpected projection member.')
    return m

def manifest_at(root, expected=None):
    try: return _manifest_at(root,expected)
    except ReadError: raise
    except OSError as e: raise ReadError('projection-unavailable','Missing projection member.') from e
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,OverflowError,RecursionError) as e:
        raise ReadError('projection-integrity','Malformed projection manifest.') from e

class Snapshot:
    """Validate all pins; hold verified raster bytes independently of mutable paths."""
    def __init__(self, root, expected=None):
        self.rasters = {}; self.generations = {}
        try:
            self.manifest = m = manifest_at(root, expected)
            metadata = {}
            for name, seal in m['files'].items():
                raw = bounded_bytes(Path(root)/name, MAX_JSON if name.endswith('.json') else MAX_BYTES, seal)
                if name.endswith('.tif'): self.rasters[name] = MemoryFile(raw)
                else: metadata[name] = json_value(raw)
            features = metadata['features.json']['features']
            require(isinstance(features,list) and len(features) == 38, 'projection-integrity', 'Native geometry population differs.')
            self.features = {f['identity']:f for f in features}
            require(len(self.features) == len(features), 'projection-integrity', 'Duplicate geometry identity.')
            self.worldcover = metadata['worldcover.json']
            require(len(self.worldcover['claims']) <= 32 and len({c['native']['fields']['code'] for c in self.worldcover['claims']}) == len(self.worldcover['claims']),
                    'projection-integrity', 'Duplicate or excessive native categories.')
            headers = {}
            for name, mem in self.rasters.items():
                with mem.open(driver='GTiff') as src:
                    require(src.driver == 'GTiff' and src.count == 1 and src.width * src.height <= 13000000,
                            'projection-integrity', 'Unsupported raster allocation.')
                    headers[name] = {'crs':str(src.crs),'shape':list(src.shape),'transform':list(src.transform)}
            for generation, pin in m['pins'].items():
                d = metadata[pin['file']]
                self.check_generation(d, generation, pin, headers)
                self.generations[generation] = d
        except (ReadError, OSError, ValueError, KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError) as e:
            self.close()
            if isinstance(e, ReadError): raise
            raise ReadError('projection-unavailable', 'Missing or malformed projection member.') from e

    def check_generation(self, d, generation, pin, headers):
        m = self.manifest
        require(set(d) == {'schema','answer','selectors','knowledge'} and d['schema'] == 'atlas-read-projection-generation/v1',
                'projection-integrity', 'Invalid generation structure.')
        a = d['answer']; pool = a['documents']
        require(set(a) == {'schema','generation','members','results','relationships','documents','regions','traversal','gap'}
                and a['schema'] == 'atlas-qualified-retrieval/v1' and a['generation'] == generation
                and a['gap'] is None and a['traversal'] is None, 'projection-integrity', 'Generation answer differs.')
        require(isinstance(pool,dict) and len(pool) <= 512 and all(digest(k) and identity(v) == k for k,v in pool.items()),
                'projection-integrity', 'Qualified document identity differs.')
        require(isinstance(a['members'],dict) and all(digest(v) for v in a['members'].values()), 'projection-integrity', 'Invalid component membership.')
        require(set(a['regions']) == set(d['knowledge']) == {'tryfan','riffelhorn'}, 'projection-integrity', 'Regional knowledge closure differs.')
        for region, refs in a['regions'].items():
            require(set(refs) == {'nativeRef','knowledgeRef'} and refs['nativeRef'] in pool, 'projection-integrity', 'Missing regional document.')
            k = d['knowledge'][region]
            if refs['knowledgeRef'] is None: require(k is None, 'projection-integrity', 'Unknown knowledge differs.')
            else:
                require(refs['knowledgeRef'] in pool and isinstance(k,dict) and set(k) == {'revision','acceptedAt'}, 'projection-integrity', 'Missing knowledge document.')
                doc = pool[refs['knowledgeRef']]
                require(k['revision'] == doc['identity'] and k['acceptedAt'] == doc['knowledgeTime']['acceptedAt'] and doc['nativeRef'] == refs['nativeRef'] and doc['region'] == region,
                        'projection-integrity', 'Knowledge binding differs.')
        records = {r['key']:r for r in a['results']}
        require(len(records) == len(a['results']) == pin['records'], 'projection-integrity', 'Duplicate or missing record.')
        selectors = {s['key']:s for s in d['selectors']}
        require(len(selectors) == len(d['selectors']) and set(selectors) == {k for k,r in records.items() if r['representation'] == 'local-scalar'},
                'projection-integrity', 'Scalar selector closure differs.')
        native_ids = {r['identity'] for r in records.values() if r['region'] == 'riffelhorn' and r['evidenceClass'] == 'source'}
        require(native_ids == set(self.features) | set(m['rasterFiles']), 'projection-integrity', 'Native qualified population differs.')
        for r in records.values():
            require(set(r) == {'key','identity','revision','evidenceClass','region','family','representation','componentIdentity','evidenceRef','qualificationRef','provenanceRef','rightsRef','support','temporal','knowledgeRef','relationshipRefs'}, 'projection-integrity', 'Qualified record structure differs.')
            require(isinstance(r['identity'],str) and r['key'] == ('derived:' if r['evidenceClass'] == 'derived' else r['region']+':')+r['identity'], 'projection-integrity', 'Qualified key differs.')
            require(r['region'] in a['regions'] and r['evidenceClass'] in ['source','derived'] and digest(r['revision']), 'projection-integrity', 'Invalid qualified identity.')
            component = 'terrainDerived' if r['evidenceClass'] == 'derived' else r['region'] + 'Registration'
            require(r['componentIdentity'] == a['members'].get(component) and r['knowledgeRef'] == a['regions'][r['region']]['knowledgeRef'],
                    'projection-integrity', 'Qualified membership or knowledge differs.')
            for ref in ['evidenceRef','qualificationRef','provenanceRef','rightsRef']:
                require(r[ref] in pool, 'projection-integrity', 'Missing qualified document.')
            body = pool[r['evidenceRef']]; provenance = pool[r['provenanceRef']]
            for ref in ['executionRef','regionalNativeRef']:
                if ref in provenance: require(provenance[ref] in pool, 'projection-integrity', 'Missing lineage document.')
            require(set(r['temporal']) == {'evidence-epoch','product-reference'}, 'projection-integrity', 'Temporal roles differ.')
            for t in r['temporal'].values():
                require(t['status'] in ['known','unknown'] and (t['status'] != 'known' or type(t['year']) is int and 1 <= t['year'] <= 9999), 'projection-integrity', 'Invalid native temporal qualification.')
            if r['representation'] == 'vector':
                f = self.features[r['identity']]; s = r['support']
                require(s['sha256'] == m['files']['features.json']['sha256'] and s['selector'] == r['identity'] and s['crs'] == f['nativeCrs'] == 'EPSG:2056' and r['family'] == f['family'] and r['revision'] == m['preparedRevision'] and list(shape(f['native']['geometry']).bounds) == s['bounds'], 'projection-integrity', 'Geometry binding differs.')
            if r['representation'] == 'raster':
                b = body['detail']['binding']; name = m['rasterFiles'][r['identity']]; h = headers[name]
                require(b['id'] == r['identity'] and b['family'] == r['family'] and r['revision'] == m['preparedRevision'] and b['input']['sha256'] == m['files'][name]['sha256'] and b['input']['bytes'] == m['files'][name]['bytes']
                        and all(h[k] == b['native'][k] for k in h) and r['support'] == b['native'], 'projection-integrity', 'Native raster binding differs.')
            if r['representation'] == 'local-scalar':
                s = selectors[r['key']]
                require(all(s[k] == r[k] for k in ['identity','revision','region','family','representation']) and s['point'] == r['support']['point']
                        and finite_numbers(s['point'],2) and len(s['cells']) <= 64 and all(finite_numbers(c,2) for c in s['cells'])
                        and s['product'] == body['methodRevision'] and r['revision'] == r['evidenceRef'], 'projection-integrity', 'Scalar binding differs.')
        edges = a['relationships']; by_id = {e['identity']:e for e in edges}
        require(len(edges) == len(by_id) <= 256, 'projection-integrity', 'Duplicate or excessive relationships.')
        for e in edges:
            require(identity({k:v for k,v in e.items() if k != 'identity'}) == e['identity'] and e['from'] in records and e['to'] in records and e['toRevision'] == records[e['to']]['revision'], 'projection-integrity', 'Relationship endpoint/revision differs.')
            if e['kind'] == 'consumes-qualified-source':
                source = e['via']['sourceArtifact']; target = pool[records[e['to']]['evidenceRef']]
                require(pool[records[e['from']]['evidenceRef']]['detail']['binding']['input'] == source and e['fromRevision'] == source['sha256'] and e['via']['preparedRevision'] == m['preparedRevision'] and any(x['identity'] == e['via']['identity'] for x in target['inputs']), 'projection-integrity', 'Source dependency differs.')
            else:
                require(e['kind'] == 'derived-input' and e['fromRevision'] == records[e['from']]['revision'] and any(x['identity'] == e['fromRevision'] for x in pool[records[e['to']]['evidenceRef']]['inputs']), 'projection-integrity', 'Derived dependency differs.')
        for key,r in records.items():
            if r['evidenceClass'] == 'derived':
                inputs = pool[r['evidenceRef']]['inputs']
                incoming = [e for e in edges if e['to'] == key]
                require({x['identity'] for x in inputs} == {e['via']['identity'] if e['kind'] == 'consumes-qualified-source' else e['fromRevision'] for e in incoming}, 'projection-integrity', 'Derived input closure differs.')
                slope = pool[r['evidenceRef']] if r['family'] == 'terrain-slope' else pool[records[incoming[0]['from']]['evidenceRef']]
                cells = [[c['x'],c['y']] for use in slope['sampling']['uses'] for c in use['cells']]
                require(selectors[key]['cells'] == cells, 'projection-integrity', 'Consumed native cell selectors differ.')
            require(set(r['relationshipRefs']) == {e['identity'] for e in edges if key in (e['from'],e['to'])}, 'projection-integrity', 'Relationship membership differs.')
        active = set(); done = set()
        def visit(key):
            require(key not in active, 'projection-integrity', 'Dependency cycle.')
            if key in done: return
            active.add(key)
            for edge in edges:
                if edge['from'] == key: visit(edge['to'])
            active.remove(key); done.add(key)
        for key in records: visit(key)

    def close(self):
        for mem in self.rasters.values(): mem.close()
        self.rasters.clear()
