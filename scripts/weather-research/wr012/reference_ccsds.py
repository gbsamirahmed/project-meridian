"""Finite independent GRIB interpretation using shared libaec, never ecCodes.

Only the three pinned WR011 messages and their evidenced profiles are supported.
This is not an independent CCSDS algorithm or a general-purpose GRIB decoder.
ABI/constants: upstream libaec v1.1.3 include/libaec.h.in (BSD-2-Clause).
"""
from __future__ import annotations

import argparse
from array import array
import ctypes
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
PIN = HERE / 'input-pins.json'


class ReferenceError(ValueError): pass


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False)+'\n').encode('utf-8')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(65536), b''): h.update(b)
    return h.hexdigest()


def signed_magnitude(value, width):
    sign = 1 << (width-1)
    return -(value & (sign-1)) if value & sign else value


def split_message(body):
    if (len(body) < 20 or body[:4] != b'GRIB' or body[7] != 2
        or int.from_bytes(body[8:16], 'big') != len(body) or body[-4:] != b'7777'):
        raise ReferenceError('Malformed/truncated/concatenated GRIB2 message')
    offset = 16; sections = {}; order = []
    while offset < len(body)-4:
        size = int.from_bytes(body[offset:offset+4], 'big')
        if size < 5 or offset+size > len(body)-4: raise ReferenceError('Invalid section extent')
        number = body[offset+4]
        if number in sections: raise ReferenceError('Repeated section unsupported')
        sections[number] = body[offset:offset+size]; order.append(number); offset += size
    if order != [1, 2, 3, 4, 5, 6, 7] or offset != len(body)-4:
        raise ReferenceError('Unsupported section structure')
    return sections


def parse(body):
    s = split_message(body); one, g, p, d = [s[k] for k in [1, 3, 4, 5]]
    if len(one) != 21 or len(g) != 72 or len(d) != 25 or len(s[6]) != 6 or s[6][5] != 255:
        raise ReferenceError('Unsupported identification/grid/packing/bitmap structure')
    def u(b, a, n): return int.from_bytes(b[a:a+n], 'big')
    ref = datetime(u(one, 12, 2), *one[14:19], tzinfo=timezone.utc)
    grid = {'template': u(g, 12, 2), 'points': u(g, 6, 4), 'earth_shape': g[14],
        'nx': u(g, 30, 4), 'ny': u(g, 34, 4), 'basic_angle': u(g, 38, 4), 'subdivisions': u(g, 42, 4),
        'north': signed_magnitude(u(g, 46, 4), 32)/1e6, 'origin': u(g, 50, 4)/1e6,
        'resolution_component_flags': g[54], 'south': signed_magnitude(u(g, 55, 4), 32)/1e6,
        'last_longitude': u(g, 59, 4)/1e6, 'dx': u(g, 63, 4)/1e6, 'dy': u(g, 67, 4)/1e6,
        'scan': g[71], 'section3_sha256': hashlib.sha256(g).hexdigest()}
    if (grid['template'], grid['earth_shape'], grid['nx'], grid['ny'], grid['points'],
        grid['basic_angle'], grid['subdivisions'], grid['north'], grid['south'], grid['origin'],
        grid['last_longitude'], grid['dx'], grid['dy'], grid['scan']) != (0, 6, 1440, 721, 1038240, 0, 4294967295, 90, -90, 180, 179.75, .25, .25, 0):
        raise ReferenceError('Unsupported native grid/order')
    template = u(p, 7, 2)
    if (template, len(p)) not in [(0, 34), (8, 58)] or p[17] != 1 or p[28] != 255:
        raise ReferenceError('Unsupported temporal/vertical template')
    start_lead = u(p, 18, 4); valid = ref+timedelta(hours=start_lead)
    temporal = {'template': template, 'reference_time': ref.isoformat().replace('+00:00', 'Z'),
                'lead_to_start_hours': start_lead, 'kind': 'instant', 'valid_time': valid.isoformat().replace('+00:00', 'Z')}
    if template == 8:
        end = datetime(u(p, 34, 2), *p[36:41], tzinfo=timezone.utc)
        duration, increment = u(p, 49, 4), u(p, 54, 4)
        if (p[41], u(p, 42, 4), p[46], p[47], p[48], p[53], increment) != (1, 0, 1, 2, 1, 13, 450):
            raise ReferenceError('Unsupported interval statistic/increment')
        if duration <= 0 or end != valid+timedelta(hours=duration): raise ReferenceError('Contradictory interval')
        temporal.update(kind='accumulation', interval_start=valid.isoformat().replace('+00:00', 'Z'),
                        interval_end=end.isoformat().replace('+00:00', 'Z'), valid_time=end.isoformat().replace('+00:00', 'Z'),
                        duration_seconds=duration*3600, increment_seconds=increment, statistic=1)
    scale, height = p[23], u(p, 24, 4)
    if p[22] == 103 and scale == 0: vertical = {'surface_code': 103, 'height_m': height, 'reference': 'model ground'}
    elif p[22] == 1 and scale == 255 and height == 4294967295: vertical = {'surface_code': 1, 'height_m': None, 'reference': 'surface without encoded altitude'}
    else: raise ReferenceError('Unsupported vertical support')
    packing = {'template': u(d, 9, 2), 'points': u(d, 5, 4), 'reference': struct.unpack_from('>f', d, 11)[0],
        'binary_scale': signed_magnitude(u(d, 15, 2), 16), 'decimal_scale': signed_magnitude(u(d, 17, 2), 16),
        'bits': d[19], 'original_type': d[20], 'flags': d[21], 'block_size': d[22], 'rsi': u(d, 23, 2)}
    if (packing['template'], packing['points'], packing['decimal_scale'], packing['original_type'],
        packing['flags'], packing['block_size'], packing['rsi']) != (42, 1038240, 0, 0, 14, 32, 128):
        raise ReferenceError('Unsupported finite CCSDS profile')
    if packing['bits'] not in (12, 16) or packing['binary_scale'] not in (-5, -18, -6) or not math.isfinite(packing['reference']):
        raise ReferenceError('Unsupported scaling/precision')
    return {'edition': 2, 'centre': u(one, 5, 2), 'subcentre': u(one, 7, 2), 'master_table': one[9],
        'local_table': one[10], 'significance_reference': one[11], 'production_status': one[19], 'processed_type': one[20],
        'parameter': [body[6], p[9], p[10]], 'process': p[13], 'process_type': p[11], 'temporal': temporal,
        'vertical': vertical, 'grid': grid, 'packing': packing, 'bitmap': 'none',
        'section2_sha256': hashlib.sha256(s[2]).hexdigest()}, s[7][5:]


def check_identity(m, fp):
    e = fp['expected']
    if (m['centre'], m['subcentre'], m['master_table'], m['local_table'], m['processed_type'], m['process'], m['parameter']) != (98, 0, 33, 1, 1, 158, [e[k] for k in ['discipline', 'parameterCategory', 'parameterNumber']]):
        raise ReferenceError('Producer/parameter/edition mismatch')
    if (m['significance_reference'], m['production_status'], m['process_type'], m['grid']['resolution_component_flags']) != (1, 0, 2, 48):
        raise ReferenceError('Reference/status/component-frame mismatch')
    if (m['temporal']['reference_time'], m['temporal']['valid_time'], m['vertical']['surface_code']) != ('2025-01-15T00:00:00Z', '2025-01-16T00:00:00Z', e['typeOfFirstFixedSurface']):
        raise ReferenceError('Wrong time/level')
    if m['vertical']['height_m'] != (e['level'] if e['typeOfFirstFixedSurface'] == 103 else None): raise ReferenceError('Wrong height')
    for a, b in [('reference', 'referenceValue'), ('binary_scale', 'binaryScaleFactor'), ('decimal_scale', 'decimalScaleFactor'), ('bits', 'bitsPerValue')]:
        if m['packing'][a] != e[b]: raise ReferenceError('Packing identity mismatch')
    expected_kind = 'accumulation' if e['productDefinitionTemplateNumber'] == 8 else 'instant'
    if m['temporal']['kind'] != expected_kind: raise ReferenceError('Wrong temporal support')
    if m['grid']['section3_sha256'] != fp['section3_sha256']: raise ReferenceError('Pinned grid changed')
    m['native_unit'] = e['units']
    m['unit_authority'] = 'retained WR011 scoped WMO/ECMWF definitions; not a new independent parameter dictionary'


class AecStream(ctypes.Structure):
    _fields_ = [('next_in', ctypes.POINTER(ctypes.c_ubyte)), ('avail_in', ctypes.c_size_t), ('total_in', ctypes.c_size_t),
                ('next_out', ctypes.POINTER(ctypes.c_ubyte)), ('avail_out', ctypes.c_size_t), ('total_out', ctypes.c_size_t),
                ('bits_per_sample', ctypes.c_uint), ('block_size', ctypes.c_uint), ('rsi', ctypes.c_uint), ('flags', ctypes.c_uint),
                ('state', ctypes.c_void_p)]


def process_memory():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('faults', ctypes.c_ulong),
                    *[(n, ctypes.c_size_t) for n in ('peak_working', 'working', 'peak_paged', 'paged', 'peak_nonpaged', 'nonpaged', 'pagefile', 'peak_pagefile')]]
    k = ctypes.WinDLL('kernel32'); k.GetCurrentProcess.restype = ctypes.c_void_p
    api = ctypes.WinDLL('psapi'); api.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    c = Counters(); c.cb = ctypes.sizeof(c)
    if not api.GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(c), c.cb): raise ReferenceError('Memory measurement unavailable')
    return {'peak_working_set_bytes': int(c.peak_working), 'working_set_bytes': int(c.working)}


def unpack(payload, packing, library):
    if ctypes.sizeof(AecStream) != 72 or ctypes.sizeof(ctypes.c_void_p) != 8: raise ReferenceError('Unsupported ABI')
    # Only pinned, immutable inputs reach this native call, never arbitrary corrupt fixtures.
    if packing['bits'] not in (12, 16) or packing['flags'] != 14: raise ReferenceError('Unsupported integer storage')
    buf = (ctypes.c_ubyte*len(payload)).from_buffer_copy(payload)
    output = (ctypes.c_ubyte*(packing['points']*2))()
    stream = AecStream(next_in=buf, avail_in=len(payload), next_out=output, avail_out=len(output),
                       bits_per_sample=packing['bits'], block_size=packing['block_size'], rsi=packing['rsi'], flags=packing['flags'])
    call = library.aec_buffer_decode; call.argtypes = [ctypes.POINTER(AecStream)]; call.restype = ctypes.c_int
    status = call(ctypes.byref(stream))
    if status or stream.total_out != len(output) or stream.avail_out or stream.total_in != len(payload):
        raise ReferenceError(f'Incomplete/native decode: status={status}, input={stream.total_in}/{len(payload)}, output={stream.total_out}/{len(output)}')
    integers = array('H'); integers.frombytes(bytes(output))
    if sys.byteorder == 'little': integers.byteswap()  # Encoded AEC_DATA_MSB requests big-endian uint16.
    if max(integers) >= 2**packing['bits']: raise ReferenceError('Integer precision overflow')
    scale = 2.0**packing['binary_scale']; ref = packing['reference']
    values = array('d', (ref+x*scale for x in integers))  # Actual D=0, exact dyadic binary64 arithmetic.
    if sys.byteorder != 'little': values.byteswap()
    return values, {'status': status, 'input_bytes_consumed': int(stream.total_in), 'output_integer_bytes': int(stream.total_out),
                    'integer_minimum': min(integers), 'integer_maximum': max(integers),
                    'flags_used': packing['flags'], 'output_integer_order': 'big endian uint16', 'output_values': 'little endian binary64'}


def run(path, identity, library_path, output):
    pin = json.loads(PIN.read_text(encoding='utf-8')); fp = pin['fields'][identity]
    if output.resolve().is_relative_to(HERE.parents[2]) or any(p.exists() for p in (output, output.with_suffix('.json'))):
        raise ReferenceError('Output must be new and external to Git')
    if path.stat().st_size != fp['input']['bytes'] or digest(path) != fp['input']['sha256']:
        raise ReferenceError('Raw input identity mismatch')
    if library_path.stat().st_size != pin['aec']['bytes'] or digest(library_path) != pin['aec']['sha256']:
        raise ReferenceError('Pinned existing libaec absent/mismatched')
    if sys.platform != 'win32': raise ReferenceError('Only tested Windows64 ABI is authorised by this profile')
    kernel = ctypes.WinDLL('kernel32'); kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]; kernel.GetModuleHandleW.restype = ctypes.c_void_p
    if kernel.GetModuleHandleW('eccodes.dll') or kernel.GetModuleHandleW('eccodes_memfs.dll'):
        raise ReferenceError('Reference process already loads ecCodes')
    m, payload = parse(path.read_bytes()); check_identity(m, fp)
    library = ctypes.CDLL(str(library_path.resolve()))
    values, receipt = unpack(payload, m['packing'], library)
    if kernel.GetModuleHandleW('eccodes.dll') or any(x.startswith('eccodes') for x in sys.modules):
        raise ReferenceError('Reference path calls/loads ecCodes')
    with output.open('xb') as f: values.tofile(f)
    if digest(path) != fp['input']['sha256']: raise ReferenceError('Source mutated')
    result = {'metadata': m, 'decompression': receipt, 'raw_input': fp['input'],
              'values_sha256': digest(output), 'values_bytes': output.stat().st_size,
              'implementation': 'WR012 stdlib raw-section/scale reader plus existing libaec buffer API',
              'independence': 'B: independent GRIB interpretation with shared low-level CCSDS libaec, not an independent CCSDS algorithm',
              'ecCodes_loaded_in_reference': False, 'python': sys.version.split()[0], 'libaec': pin['aec']}
    result['process_memory'] = process_memory()
    output.with_suffix('.json').write_bytes(canonical(result))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--input', type=Path, required=True)
    p.add_argument('--field', choices=['temperature', 'precipitation', 'wind_u'], required=True)
    p.add_argument('--libaec', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); run(a.input, a.field, a.libaec, a.output)
