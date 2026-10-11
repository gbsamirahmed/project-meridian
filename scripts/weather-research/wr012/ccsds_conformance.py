"""WR012 finite comparison; primary ecCodes and a separate shared-libaec reader."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'wr011'))
import ifs_contract_pilot as previous
import reference_ccsds as reference

Error = reference.ReferenceError


def checked_pin():
    p = json.loads(reference.PIN.read_text(encoding='utf-8'))
    for name, seal in p['dependencies'].items():
        if reference.digest(HERE.parent / name) != seal:
            raise Error('Preserved WR007-WR011 evidence changed')
    if p['comparison_predeclaration']['absolute_tolerance'] != 0:
        raise Error('Declared exact-comparison rule changed')
    return p


def compare(a, b, packing):
    """No alignment guessing or tolerance fitting; these actual finite grids only."""
    if a.shape != (721, 1440) or b.shape != a.shape or a.dtype != np.float64 or b.dtype != np.float64:
        raise Error('Unexpected shape/precision')
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise Error('Unsupported missing/non-finite profile')
    difference = np.abs(a-b)
    index = int(np.argmax(difference)); row, col = divmod(index, 1440)
    maximum = float(difference.flat[index]); nonzero = a != 0
    relative = float(np.max(difference[nonzero]/np.abs(a[nonzero]))) if np.any(nonzero) else 0.0
    result = {'compared_cells': int(a.size), 'primary_finite': int(a.size), 'reference_finite': int(b.size),
        'primary_missing': 0, 'reference_missing': 0, 'mask_agreement': True,
        'exact_equal_cells': int(np.count_nonzero(a == b)), 'maximum_absolute_difference': maximum,
        'mean_absolute_difference': float(difference.mean()), 'maximum_relative_difference_nonzero_primary': relative,
        'zero_primary_differences': int(np.count_nonzero(difference[~nonzero])),
        'maximum_difference_in_quantisation_steps': maximum/(2.0**packing['binary_scale']),
        'absolute_tolerance': 0, 'passed': maximum == 0,
        'largest_difference': {'row': row, 'column': col, 'latitude': 90-.25*row,
            'longitude_modulo360': (180+.25*col) % 360,
            'primary': float(a[row, col]), 'reference': float(b[row, col]),
            'tie_rule': 'first native row-major cell; zero means no disagreement'}}
    if not result['passed']: raise Error('Declared exact numerical comparison failed: '+json.dumps(result))
    return result


def align_metadata(m, raw):
    """Validate coordinates/semantics independently before comparing native indices."""
    g = raw['grid']; t = raw['temporal']; v = raw['vertical']
    pairs = [('nx', 'Ni'), ('ny', 'Nj'), ('north', 'latitudeOfFirstGridPointInDegrees'),
        ('south', 'latitudeOfLastGridPointInDegrees'), ('origin', 'longitudeOfFirstGridPointInDegrees'),
        ('last_longitude', 'longitudeOfLastGridPointInDegrees'), ('dx', 'iDirectionIncrementInDegrees'),
        ('dy', 'jDirectionIncrementInDegrees'), ('scan', 'scanningMode'), ('earth_shape', 'shapeOfTheEarth'),
        ('resolution_component_flags', 'resolutionAndComponentFlags')]
    if any(g[a] != m[b] for a, b in pairs): raise Error('Independent grid alignment mismatch')
    if raw['parameter'] != [m[k] for k in ('discipline', 'parameterCategory', 'parameterNumber')]:
        raise Error('Parameter mismatch')
    if raw['native_unit'] != m['units'] or v['surface_code'] != m['typeOfFirstFixedSurface']:
        raise Error('Unit/vertical reference mismatch')
    if v['height_m'] != (m['level'] if m['typeOfFirstFixedSurface'] == 103 else None): raise Error('Height mismatch')
    if t['reference_time'] != '2025-01-15T00:00:00Z' or t['valid_time'] != '2025-01-16T00:00:00Z':
        raise Error('Reference/valid-time mismatch')
    if t['kind'] != ('accumulation' if m['productDefinitionTemplateNumber'] == 8 else 'instant'):
        raise Error('Temporal family mismatch')
    if t['lead_to_start_hours'] != m['forecastTime']: raise Error('Forecast-time mismatch')
    if t['kind'] == 'accumulation' and (t['duration_seconds'] != m['lengthOfTimeRange']*3600 or t['increment_seconds'] != m['timeIncrement']):
        raise Error('Accumulation support mismatch')


def loaded_aec():
    kernel = ctypes.WinDLL('kernel32')
    kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]; kernel.GetModuleHandleW.restype = ctypes.c_void_p
    kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
    handle = kernel.GetModuleHandleW('aec.dll')
    if not handle: raise Error('Primary libaec module identity unavailable')
    buf = ctypes.create_unicode_buffer(32768)
    if not kernel.GetModuleFileNameW(handle, buf, len(buf)): raise Error('Primary module provenance unavailable')
    return reference.digest(Path(buf.value))


def run(inputs, libaec, output, resources):
    p = checked_pin(); old = previous.checked_pin()
    if output == resources or any(x.exists() or x.resolve().is_relative_to(HERE.parents[2]) for x in (output, resources)):
        raise Error('Use new external receipt/resource paths')
    if reference.digest(libaec) != p['aec']['sha256']: raise Error('Existing libaec identity mismatch')
    started = time.perf_counter(); before = previous.spatial.process_memory(); records = {}; children = []
    accepted = json.loads((HERE.parent/'wr011/integrity-receipt.json').read_text(encoding='utf-8'))['scientific_receipt']
    peak_temporary = 0
    for identity in ('temperature', 'precipitation', 'wind_u'):
        fp = p['fields'][identity]; path = inputs/fp['input']['filename']
        a, mask, m, sections, primary = previous.primary(path, old['fields'][identity])
        seal = hashlib.sha256(a.astype('<f8', copy=False).tobytes()).hexdigest()
        if seal != accepted['fields'][identity]['decoded_float64_sha256']: raise Error('Primary replay differs from WR011')
        if loaded_aec() != p['aec']['sha256']: raise Error('Primary shared library identity changed')
        with tempfile.TemporaryDirectory(prefix='wr012-reference-', dir=output.parent) as tmp:
            target = Path(tmp)/'values.f64'
            result = subprocess.run([sys.executable, '-B', str(HERE/'reference_ccsds.py'), '--input', str(path),
                '--field', identity, '--libaec', str(libaec), '--output', str(target)],
                capture_output=True, text=True, timeout=60)
            if result.returncode: raise Error('Independent reader failed: '+result.stderr)
            raw = json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
            if target.stat().st_size != a.size*8: raise Error('Reference byte count mismatch')
            align_metadata(m, raw['metadata'])
            if raw['metadata']['grid']['section3_sha256'] != hashlib.sha256(sections[3]).hexdigest():
                raise Error('Independent encoded grid identity mismatch')
            b = np.fromfile(target, dtype='<f8').reshape(a.shape)
            comparison = compare(a, b, raw['metadata']['packing'])
            if raw['values_sha256'] != seal: raise Error('Exact decoded-byte identity differs')
            peak_temporary = max(peak_temporary, sum(x.stat().st_size for x in Path(tmp).iterdir()))
            children.append(raw.pop('process_memory'))
            records[identity] = {'reference': raw, 'primary_decoder': primary,
                'primary_decoded_sha256': seal, 'primary_matches_preserved_WR011': True,
                'metadata_alignment': 'raw Section3 and independent geometry/time/parameter checked before same-native-index comparison; no rotation',
                'comparison': comparison}
            del b
        if reference.digest(path) != fp['input']['sha256']: raise Error('Raw source mutated')
        del a, mask
    receipt = {'schema': 'wr012-qualified-numerical-conformance-v1', 'outcome': 'A',
        'attribution': accepted['attribution'], 'copyright': accepted['copyright'],
        'pins_sha256': reference.digest(reference.PIN), 'predeclaration': p['comparison_predeclaration'],
        'utility_sha256': {name: reference.digest(HERE/name) for name in ('ccsds_conformance.py', 'reference_ccsds.py')},
        'independence': 'B: independent GRIB unpacking interpretation and scaling; same low-level libaec DLL as ecCodes',
        'fields': records, 'limitations': ['No independent CCSDS entropy algorithm validation',
            'Only three pinned no-bitmap D0 Windows64 profiles; no general decoder or GDAL upgrade',
            'Retained producer unit/parameter dictionaries; no new independent local-parameter vocabulary',
            'No forecast skill, observation validation or production-readiness claim']}
    output.write_bytes(reference.canonical(receipt))
    resources.write_bytes(reference.canonical({'primary_before': before, 'primary_after': previous.spatial.process_memory(),
        'reference_children': children, 'maximum_temporary_bytes': peak_temporary, 'seconds': time.perf_counter()-started,
        'controlled_retrievals_during_replay': 0, 'scientific_transfer_bytes': 0}))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--libaec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--resources', type=Path, required=True)
    a = parser.parse_args(); run(a.inputs, a.libaec, a.output, a.resources)
