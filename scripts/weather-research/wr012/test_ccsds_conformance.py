"""Synthetic rejection/invariant tests; separately opted-in genuine three-field replay."""
import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import ccsds_conformance as pilot
import reference_ccsds as ref


def synthetic_message(interval=False):
    """Synthetic metadata only: no scientific payload or invented historical evidence."""
    def section(number, size):
        b = bytearray(size); b[:4] = size.to_bytes(4, 'big'); b[4] = number; return b
    def put(b, offset, value, size): b[offset:offset+size] = value.to_bytes(size, 'big')
    one = section(1, 21); put(one, 5, 98, 2); one[9:12] = bytes([33, 1, 1])
    put(one, 12, 2025, 2); one[14:19] = bytes([1, 15, 0, 0, 0]); one[20] = 1
    g = section(3, 72); put(g, 6, 1038240, 4); g[14] = 6
    for offset, value in [(30, 1440), (34, 721), (42, 4294967295), (46, 90000000), (50, 180000000),
                          (55, (1 << 31)+90000000), (59, 179750000), (63, 250000), (67, 250000)]: put(g, offset, value, 4)
    g[54] = 48
    p = section(4, 58 if interval else 34); put(p, 7, 8 if interval else 0, 2)
    p[11] = 2; p[13] = 158; p[17] = 1; put(p, 18, 0 if interval else 24, 4)
    p[22] = 103; put(p, 24, 2, 4); p[28] = 255
    if interval:
        put(p, 34, 2025, 2); p[36:41] = bytes([1, 16, 0, 0, 0]); p[41] = 1
        p[46:49] = bytes([1, 2, 1]); put(p, 49, 24, 4); p[53] = 13; put(p, 54, 450, 4)
    d = section(5, 25); put(d, 5, 1038240, 4); put(d, 9, 42, 2); put(d, 15, 32773, 2)
    d[19:23] = bytes([12, 0, 14, 32]); put(d, 23, 128, 2)
    bitmap = section(6, 6); bitmap[5] = 255
    blocks = [one, section(2, 17), g, p, d, bitmap, section(7, 5)]
    header = bytearray(b'GRIB\x00\x00\x00\x02'+b'\x00'*8)
    put(header, 8, 16+sum(map(len, blocks))+4, 8)
    return bytes(header)+b''.join(map(bytes, blocks))+b'7777'


class SyntheticTests(unittest.TestCase):
    def mutated(self, number, offset, value):
        body = bytearray(synthetic_message(number == 4 and offset >= 34))
        at = 16
        while body[at+4] != number: at += int.from_bytes(body[at:at+4], 'big')
        body[at+offset] = value
        return body

    def test_synthetic_valid_profile(self): self.assertEqual(ref.parse(synthetic_message())[0]['packing']['binary_scale'], -5)
    def test_synthetic_interval(self): self.assertEqual(ref.parse(synthetic_message(True))[0]['temporal']['duration_seconds'], 86400)
    def test_magic(self): self.assertRaises(ref.ReferenceError, ref.parse, b'no GRIB')
    def test_truncated(self): self.assertRaises(ref.ReferenceError, ref.parse, synthetic_message()[:-1])
    def test_concatenated(self): self.assertRaises(ref.ReferenceError, ref.parse, synthetic_message()*2)
    def test_bad_section_extent(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(3, 3, 1))
    def test_missing_section(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(2, 4, 9))
    def test_duplicate_section(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(2, 4, 1))
    def test_bitmap_unsupported(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(6, 5, 0))
    def test_scan_unsupported(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(3, 71, 128))
    def test_origin_unsupported(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(3, 50, 1))
    def test_grid_template(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(3, 13, 40))
    def test_packing_template(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(5, 10, 0))
    def test_decimal_scale(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(5, 18, 1))
    def test_unsupported_precision(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(5, 19, 24))
    def test_flags(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(5, 21, 8))
    def test_block(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(5, 22, 16))
    def test_time_unit(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(4, 17, 13))
    def test_statistic(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(4, 46, 0))
    def test_zero_duration(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(4, 52, 0))
    def test_increment(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(4, 57, 0))
    def test_vertical(self): self.assertRaises(ref.ReferenceError, ref.parse, self.mutated(4, 22, 100))
    def test_signed_scale(self): self.assertEqual(ref.signed_magnitude(32786, 16), -18)
    def test_receipt_determinism(self): self.assertEqual(ref.canonical({'b': 2, 'a': 1}), ref.canonical({'a': 1, 'b': 2}))
    def test_receipt_nonfinite(self): self.assertRaises(ValueError, ref.canonical, {'bad': float('nan')})
    def test_unknown_field_identity(self):
        m, _ = ref.parse(synthetic_message()); p = json.loads(ref.PIN.read_text(encoding='utf-8'))['fields']['temperature']
        m['parameter'][2] = 1; self.assertRaises(ref.ReferenceError, ref.check_identity, m, p)
    def test_wrong_reference(self):
        m, _ = ref.parse(synthetic_message()); p = json.loads(ref.PIN.read_text(encoding='utf-8'))['fields']['temperature']
        m['temporal']['reference_time'] = '2025-01-14T00:00:00Z'; self.assertRaises(ref.ReferenceError, ref.check_identity, m, p)
    def test_wrong_height(self):
        m, _ = ref.parse(synthetic_message()); p = json.loads(ref.PIN.read_text(encoding='utf-8'))['fields']['temperature']
        m['vertical']['height_m'] = 10; self.assertRaises(ref.ReferenceError, ref.check_identity, m, p)
    def test_comparison_shape(self): self.assertRaises(ref.ReferenceError, pilot.compare, np.zeros(3), np.zeros(3), {'binary_scale': -5})
    def test_comparison_missing(self):
        a = np.zeros((721, 1440)); b = a.copy(); b[4, 5] = np.nan
        self.assertRaises(ref.ReferenceError, pilot.compare, a, b, {'binary_scale': -5})
    def test_disagreement_not_passed(self):
        a = np.zeros((721, 1440)); b = a.copy(); b[4, 5] = 2**-18
        self.assertRaises(ref.ReferenceError, pilot.compare, a, b, {'binary_scale': -18})
    def test_exact_synthetic_comparison(self):
        a = np.zeros((721, 1440)); self.assertEqual(pilot.compare(a, a, {'binary_scale': -5})['exact_equal_cells'], 1038240)
    def test_absent_dependency_no_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertRaises(FileNotFoundError, pilot.run, Path(tmp), Path(tmp)/'absent.dll', Path(tmp)/'receipt.json', Path(tmp)/'resources.json')
    def test_abi_size(self): self.assertEqual(ref.ctypes.sizeof(ref.AecStream), 72)
    def test_reference_no_eccodes_import(self):
        import ast
        tree = ast.parse((ref.HERE/'reference_ccsds.py').read_text(encoding='utf-8'))
        imported = [n.names[0].name if isinstance(n, ast.Import) else n.module for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any(n and ('eccodes' in n or 'ifs_contract' in n) for n in imported))


class GenuineReplay(unittest.TestCase):
    @unittest.skipUnless(os.getenv('MERIDIAN_WR011_INPUTS') and os.getenv('MERIDIAN_WR012_LIBAEC'), 'Pinned local raw inputs and existing libaec required; no fallback')
    def test_actual_three_fields_and_deterministic_repeat(self):
        with tempfile.TemporaryDirectory(prefix='wr012-test-') as tmp:
            t = Path(tmp); results = []
            for i in range(2):
                results.append(pilot.run(Path(os.environ['MERIDIAN_WR011_INPUTS']), Path(os.environ['MERIDIAN_WR012_LIBAEC']), t/f'{i}.json', t/f'{i}-resources.json'))
            self.assertEqual(ref.canonical(results[0]), ref.canonical(results[1]))
            self.assertTrue(all(v['comparison']['exact_equal_cells'] == 1038240 for v in results[0]['fields'].values()))
            self.assertTrue(all(not v['reference']['ecCodes_loaded_in_reference'] for v in results[0]['fields'].values()))


if __name__ == '__main__': unittest.main()
