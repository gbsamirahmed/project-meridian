"""Synthetic packaging controls; no DEM or genuine contour derivation."""
import io
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import build

class BundleTests(unittest.TestCase):
    def record(self):return {'level':2500,'index':True,'twentyMetreSubset':True,'line':0,
                             'coordinates':[[2624000.25,1091000.25],[2625000.123456789,1092000.987654321]]}
    def test_preserves_exact_values(self):
        record=self.record();before=json.dumps(record)
        self.assertEqual(build.validate_record(record,2500),2)
        self.assertEqual(json.dumps(record),before)
    def test_no_geographic_or_wrong_datum_assumption(self):
        record=self.record();record['coordinates'][0]=[7.7,45.9]
        with self.assertRaisesRegex(ValueError,'footprint'):build.validate_record(record,2500)
    def test_rejects_invalid_elevation_and_index(self):
        record=self.record();record['index']=False
        with self.assertRaisesRegex(ValueError,'classification'):build.validate_record(record,2500)
        with self.assertRaisesRegex(ValueError,'classification'):build.validate_record(self.record(),2510)
    def test_rejects_nonfinite_and_single_point(self):
        record=self.record();record['coordinates'][0][0]=float('nan')
        with self.assertRaises(ValueError):build.validate_record(record,2500)
        record=self.record();record['coordinates']=record['coordinates'][:1]
        with self.assertRaises(ValueError):build.validate_record(record,2500)
    def test_byte_limit_precedes_write(self):
        raw=io.BytesIO();writer=build.BoundedWriter(raw,3)
        writer.write(b'abc')
        with self.assertRaises(ValueError):writer.write(b'd')
        self.assertEqual(raw.getvalue(),b'abc')
    def test_verbatim_packaging_and_20m_subset(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);record=self.record();raw=json.dumps(record,separators=(',',':')).encode()+b'\n'
            for name in build.PRODUCTS:
                folder=root/name;folder.mkdir();levels={}
                for level in range(2000,3201,10):
                    body=raw if level==2500 else b'';path=folder/f'{level}.ndjson';path.write_bytes(body)
                    levels[str(level)]={'sha256':build.digest(path),'vertices':2 if body else 0,'lines':1 if body else 0,'closed':0}
                (folder/'manifest.json').write_text(json.dumps({'id':name,'horizontalReference':'EPSG:2056','verticalReference':'LN02',
                    'surface':'DTM','units':'m','interval':10,'subsetInterval':20,'sourceRevision':'synthetic','rights':'synthetic',
                    'processingRevision':{},'limitations':[],'geometry':{'levels':levels}}))
            stream=io.BytesIO()
            with patch.object(build,'EXPECTED',((2,1,2,1),)*3):build.package_products(stream,root)
            self.assertEqual(stream.getvalue().count(raw.rstrip()),3)
            for variant in json.loads(stream.getvalue())['variants']:
                self.assertEqual(variant['lines'],[record]);self.assertEqual(variant['counts']['20']['vertices'],2)
            (root/build.PRODUCTS[0]/'2500.ndjson').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'seal changed'):build.package_products(io.BytesIO(),root)

if __name__=='__main__':unittest.main()
