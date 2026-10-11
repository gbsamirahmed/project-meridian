"""WR013 disposable bounded-subset reader; standard library only, no GRIB fallback.

The supplied identity is the caller's trusted manifest SHA256. Checksums detect
inconsistency; they do not establish source authenticity or meteorological skill.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys

VERSION = 'meridian-wr013-package-v1'
MAX_BYTES = 1_000_000


class PackageError(ValueError):
    pass


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def digest(body):
    return hashlib.sha256(body).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise PackageError('Duplicate metadata key')
        result[key] = value
    return result


def parse(body):
    def constant(value):
        raise PackageError('Non-finite JSON constant: ' + value)
    try:
        return json.loads(body, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, ValueError, TypeError) as e:
        raise PackageError('Malformed metadata or request') from e


def number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def memory():
    """Optional Windows process counters; loaded before the cooperative guard."""
    if sys.platform != 'win32':
        return {'status': 'NOT MEASURED: Windows PSAPI profile only'}
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('faults', ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ['peak_working_set', 'working_set', 'peak_paged_pool',
              'paged_pool', 'peak_nonpaged_pool', 'nonpaged_pool', 'pagefile', 'peak_pagefile']]
    c = Counters()
    c.cb = ctypes.sizeof(c)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    call = ctypes.WinDLL('psapi', use_last_error=True).GetProcessMemoryInfo
    call.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    if not call(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
        raise OSError(ctypes.get_last_error(), 'GetProcessMemoryInfo failed')
    return {name + '_bytes': int(getattr(c, name)) for name in
            ['working_set', 'peak_working_set', 'pagefile', 'peak_pagefile']}


def stamp(value):
    if not isinstance(value, str) or not value.endswith('Z'):
        raise PackageError('UTC timestamp required')
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError as e:
        raise PackageError('Unsupported timestamp') from e


def temporal(t):
    ref, valid = stamp(t['reference_time']), stamp(t['valid_time'])
    if valid < ref:
        raise PackageError('Validity precedes reference')
    if t['kind'] == 'instant':
        if any(k in t for k in ('interval_start', 'interval_end', 'duration_seconds')):
            raise PackageError('Instant/interval contradiction')
    elif t['kind'] == 'accumulation':
        start, end = stamp(t['interval_start']), stamp(t['interval_end'])
        duration = t.get('duration_seconds', t.get('interval_duration_seconds'))
        if (type(duration) is not int or duration <= 0 or start < ref or end != valid
                or end - start != timedelta(seconds=duration) or t['statistical_process_code'] != 1):
            raise PackageError('Contradictory accumulation')
    else:
        raise PackageError('Unsupported temporal support')


def component(root, name):
    if not isinstance(name, str) or Path(name).name != name or '\\' in name or ':' in name:
        raise PackageError('Unsafe component name')
    p = root / name
    if p.resolve().parent != root.resolve() or not p.is_file():
        raise PackageError('Missing or redirected component')
    if p.stat().st_size > MAX_BYTES:
        raise PackageError('Component exceeds research bound')
    return p.read_bytes()


class Package:
    def __init__(self, root, identity):
        self.root = Path(root)
        body = component(self.root, 'manifest.json')
        if digest(body) != identity:
            raise PackageError('Manifest identity mismatch')
        self.identity = identity
        self.manifest = parse(body)
        try:
            m = self.manifest
            if m['version'] != VERSION or not isinstance(m['fields'], list) or not 1 <= len(m['fields']) <= 3:
                raise PackageError('Unsupported package version or field count')
            self.fields = {}
            self.values = {}
            for f in m['fields']:
                self.validate_field(f)
                fid = f['field_id']
                if fid in self.fields:
                    raise PackageError('Ambiguous field identity')
                body = component(self.root, f['payload']['filename'])
                g = f['subset']
                count = g['rows'] * g['columns']
                if (f['payload']['encoding'] != 'IEEE754-binary64-little-endian-row-major'
                        or len(body) != count * 8 or len(body) != f['payload']['bytes']
                        or digest(body) != f['payload']['sha256']):
                    raise PackageError('Payload identity/precision/size mismatch')
                values = struct.unpack('<' + str(count) + 'd', body)
                if not all(math.isfinite(x) for x in values):
                    raise PackageError('Unsupported missing/non-finite payload')
                self.fields[fid], self.values[fid] = f, values
        except (KeyError, TypeError, OverflowError, struct.error) as e:
            raise PackageError('Incomplete or malformed scientific metadata') from e

    @staticmethod
    def validate_field(f):
        if not isinstance(f['field_id'], str) or not f['field_id']:
            raise PackageError('Missing field identifier')
        s, g, m = f['source_grid'], f['subset'], f['encoded_metadata']
        if (s['grid_type'], s['template'], s['scanning_mode'], s['earth_shape']) != ('regular_ll', 0, 0, 6):
            raise PackageError('Unsupported source geometry')
        for k in ('rows', 'columns'):
            if type(s[k]) is not int or type(g[k]) is not int or g[k] < 2:
                raise PackageError('Unsupported subset dimensions')
        for k in ('dx', 'dy', 'north', 'longitude_origin', 'radius_m'):
            if not number(s[k]):
                raise PackageError('Invalid source geometry')
        if s['dx'] <= 0 or s['dy'] <= 0 or s['radius_m'] <= 0 or s['columns'] * s['dx'] != 360:
            raise PackageError('Unsupported longitude/spacing geometry')
        if s['north'] != 90 or s['north'] - (s['rows'] - 1) * s['dy'] != -90:
            raise PackageError('Unsupported source latitude geometry')
        for k, size in [('row_start', 'rows'), ('column_start', 'columns')]:
            if type(g[k]) is not int or g[k] < 0 or g[k] + g[size] > s[size]:
                raise PackageError('Invalid native subset indices')
        north = s['north'] - g['row_start'] * s['dy']
        west = (s['longitude_origin'] + g['column_start'] * s['dx']) % 360
        if (g['north'] != north or g['south'] != north - (g['rows'] - 1) * s['dy']
                or g['west_0_360'] != west or g['east_unwrapped'] != west + (g['columns'] - 1) * s['dx']
                or g['east_unwrapped'] >= 360 or g['periodic'] is not False or g['north'] > 89.75 or g['south'] < -89.75):
            raise PackageError('Unsupported subset bounds, polar or wrapping geometry')
        if (m['units'] != f['native_unit'] or m['Ni'] != s['columns'] or m['Nj'] != s['rows']
                or m['scanningMode'] != s['scanning_mode']
                or m['radius'] != s['radius_m'] or m['shapeOfTheEarth'] != s['earth_shape']
                or m['iDirectionIncrementInDegrees'] != s['dx'] or m['jDirectionIncrementInDegrees'] != s['dy']
                or m['latitudeOfFirstGridPointInDegrees'] != s['north']
                or m['longitudeOfFirstGridPointInDegrees'] != s['longitude_origin']):
            raise PackageError('Encoded/interpreted metadata disagreement')
        temporal(f['temporal'])
        t = f['temporal']
        reference = f"{m['dataDate']:08d}{m['dataTime']:04d}"
        validity = f"{m['validityDate']:08d}{m['validityTime']:04d}"
        if (stamp(t['reference_time']).strftime('%Y%m%d%H%M') != reference
                or stamp(t['valid_time']).strftime('%Y%m%d%H%M') != validity
                or (t['kind'] == 'instant' and (m['productDefinitionTemplateNumber'], m['stepType']) != (0, 'instant'))
                or (t['kind'] == 'accumulation' and (m['productDefinitionTemplateNumber'], m['stepType'],
                      m['typeOfStatisticalProcessing']) != (8, 'accum', 1))):
            raise PackageError('Encoded/interpreted temporal disagreement')
        # This apparatus admits the inspected hourly steps only, not all GRIB
        # time-unit/template families. The encoded increment is kept separately.
        if m['indicatorOfUnitOfTimeRange'] != 1 or m['stepUnits'] != 1:
            raise PackageError('Unsupported encoded step units')
        start = stamp(t['reference_time']) + timedelta(hours=m['forecastTime'])
        if t['kind'] == 'instant':
            if start != stamp(t['valid_time']) or m['startStep'] != m['endStep'] or m['endStep'] != m['forecastTime']:
                raise PackageError('Contradictory encoded instantaneous step')
        elif (m['indicatorOfUnitForTimeRange'] != 1 or m['numberOfTimeRange'] != 1
              or m['numberOfMissingInStatisticalProcess'] != 0
              or start != stamp(t['interval_start'])
              or start + timedelta(hours=m['lengthOfTimeRange']) != stamp(t['interval_end'])
              or m['startStep'] != m['forecastTime'] or m['endStep'] != m['forecastTime'] + m['lengthOfTimeRange']):
            raise PackageError('Contradictory encoded interval support')
        v = f['vertical']
        if v['first_surface_code'] == 103:
            if v['reference'] != 'model ground' or not number(v['height_m']) or v['height_m'] <= 0:
                raise PackageError('Unsupported height reference')
        elif v['first_surface_code'] == 1:
            if v['reference'] != 'surface, no encoded altitude' or v['height_m'] is not None:
                raise PackageError('Surface interpreted as height')
        else:
            raise PackageError('Unsupported vertical structure')
        if (v['first_surface_code'] != m['typeOfFirstFixedSurface']
                or (v['first_surface_code'] == 103 and v['height_m'] != m['level'])
                or f['parameter']['codes'] != [m[k] for k in ('discipline', 'parameterCategory', 'parameterNumber')]
                or f['parameter']['centre'] != m['centre']
                or f['parameter']['master_table'] != m['tablesVersion']
                or f['parameter']['local_table'] != m['localTablesVersion']):
            raise PackageError('Parameter/vertical mapping mismatch')
        p = f['provenance']
        for seal in (p['raw_input']['sha256'], f['source_grid']['section3_sha256'], f['payload']['sha256']):
            if not isinstance(seal, str) or len(seal) != 64 or any(c not in '0123456789abcdef' for c in seal):
                raise PackageError('Missing provenance seal')
        if f['missingness'] != {'profile': 'all finite; no bitmap or sentinel', 'missing_cells': 0}:
            raise PackageError('Unsupported missingness profile')
        if f['ensemble'] != {'kind': 'deterministic', 'member': None}:
            raise PackageError('Unsupported ensemble structure')

    def query(self, q):
        def fail(status):
            return {'status': status}
        if not isinstance(q, dict) or set(q) - {'field_id', 'latitude', 'longitude', 'method', 'expect'}:
            return fail('INVALID_QUERY')
        if not {'field_id', 'latitude', 'longitude', 'method'} <= set(q):
            return fail('INVALID_QUERY')
        if not isinstance(q['field_id'], str) or q['field_id'] not in self.fields:
            return fail('UNKNOWN_FIELD')
        if not number(q['latitude']) or not number(q['longitude']) or not -90 <= q['latitude'] <= 90:
            return fail('INVALID_QUERY')
        if q['method'] not in ('NEAREST', 'BILINEAR'):
            return fail('UNSUPPORTED_METHOD')
        f = self.fields[q['field_id']]
        if 'expect' in q:
            expect = q['expect']
            supported = {'native_unit': f['native_unit'], 'vertical': f['vertical'],
                         'temporal_kind': f['temporal']['kind'], 'temporal': f['temporal']}
            if not isinstance(expect, dict) or any(k not in supported or v != supported[k] for k, v in expect.items()):
                return fail('ASSUMPTION_MISMATCH')
        s, g = f['source_grid'], f['subset']
        lon = float(q['longitude']) % 360
        if lon == 360:
            lon = 0.0
        lat = float(q['latitude'])
        if not g['south'] <= lat <= g['north'] or not g['west_0_360'] <= lon <= g['east_unwrapped']:
            return fail('OUTSIDE_EXTENT')
        # Source-native arithmetic retains the original origin; no array roll.
        y = (s['north'] - lat) / s['dy'] - g['row_start']
        x = ((lon - s['longitude_origin']) % 360) / s['dx'] - g['column_start']
        if q['method'] == 'NEAREST':
            r, c = math.floor(y), math.floor(x)
            r += int(y - r >= .5)
            c += int(x - c >= .5)
            indices, weights = [(r, c)], [1.0]
        else:
            r, c = min(math.floor(y), g['rows'] - 2), min(math.floor(x), g['columns'] - 2)
            v, u = y - r, x - c
            indices = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            weights = [(1-v)*(1-u), (1-v)*u, v*(1-u), v*u]
        if any(not 0 <= r < g['rows'] or not 0 <= c < g['columns'] for r, c in indices):
            raise PackageError('Native index outside subset')
        if not all(math.isfinite(w) and 0 <= w <= 1 for w in weights) or abs(math.fsum(weights)-1) > 8*sys.float_info.epsilon:
            raise PackageError('Invalid interpolation weights')
        nodes = []
        for (r, c), w in zip(indices, weights):
            value = self.values[q['field_id']][r*g['columns']+c]
            nodes.append({'source_row': r+g['row_start'], 'source_column': c+g['column_start'],
                          'latitude': g['north']-r*s['dy'], 'longitude_0_360': g['west_0_360']+c*s['dx'],
                          'weight': w, 'native_value': value})
        return {'status': 'OK', 'field_id': q['field_id'], 'method': q['method'],
                'normalised_coordinate': {'latitude': lat, 'longitude_0_360': lon},
                'native_value': math.fsum(n['weight']*n['native_value'] for n in nodes),
                'native_unit': f['native_unit'], 'temporal': f['temporal'], 'vertical': f['vertical'],
                'parameter': f['parameter'], 'nodes': nodes, 'package_identity': self.identity,
                'raw_input_sha256': f['provenance']['raw_input']['sha256'],
                'interpretation': 'model-grid forecast; bounded subset; no terrain correction or forecast-skill claim'}


def guard(root, requests):
    """Cooperative Python audit guard, not an operating-system security sandbox."""
    allowed = {Path(__file__).resolve(), requests.resolve()}
    # Inventory only the finite package's immediate components before the hook.
    allowed.update(p.resolve() for p in root.iterdir() if p.is_file())
    opened = []
    blocked_imports = {'eccodes', 'numpy', 'rasterio', 'osgeo', 'socket', 'urllib', 'subprocess'}
    def audit(event, args):
        if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.spawn')):
            raise PackageError('Offline network/process operation rejected')
        if event == 'import' and args[0].split('.')[0] in blocked_imports:
            raise PackageError('Scientific/network/process import rejected')
        if event == 'open':
            target, mode, flags = args
            if not isinstance(target, (str, bytes)):
                raise PackageError('Unknown file descriptor access')
            p = Path(target).resolve()
            write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            if p not in allowed or (mode and any(c in mode for c in 'wax+')) or flags & write_flags:
                raise PackageError('Read outside isolated package or write rejected')
            opened.append('package/'+p.name if p.parent == root.resolve() else p.name)
    sys.addaudithook(audit)
    return opened


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--requests', type=Path, required=True)
    parser.add_argument('--isolate', action='store_true')
    args = parser.parse_args()
    # Preload datetime's standard-library parser before restricting file reads.
    stamp('2025-01-15T00:00:00Z')
    before = memory()
    opened = guard(args.package, args.requests) if args.isolate else None
    package = Package(args.package, args.identity)
    if args.requests.stat().st_size > MAX_BYTES:
        raise PackageError('Request body exceeds research bound')
    queries = parse(args.requests.read_bytes())
    if not isinstance(queries, list) or len(queries) > 100:
        raise PackageError('Request count exceeds research bound')
    results = [package.query(q) for q in queries]
    receipt = {'schema': 'meridian-wr013-offline-replay-v1', 'package_identity': args.identity,
               'results': results, 'isolation': {'audit_guard_enabled': args.isolate,
               'opened_components': sorted(set(opened or [])),
               'scientific_modules_loaded': sorted(k for k in sys.modules if k.split('.')[0] in {'eccodes', 'numpy', 'rasterio', 'osgeo'}),
               'python_isolated': bool(sys.flags.isolated), 'python_no_site': bool(sys.flags.no_site),
               'qualification': 'cooperative audit guard and isolated stdlib process; not hostile-code OS sandbox'},
               'resources': {'before': before, 'after': memory()}}
    sys.stdout.buffer.write(canonical(receipt))


if __name__ == '__main__':
    main()
