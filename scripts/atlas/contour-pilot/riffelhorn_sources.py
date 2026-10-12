"""Dormant genuine source binding. Approval is required before construction/use."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
from staged_continuation import MISSING,SWISS,check_shape_capacity
from staged_store import digest


class RiffelhornSources:
    scope='genuine'
    def __init__(self,data_root):
        self.data_root=Path(data_root)
        self.pins=json.loads(Path(__file__).with_name('input-pins.json').read_text())

    @staticmethod
    def memory_reader():
        from worker_supervision import api
        kernel,read=api();value=read(kernel.GetCurrentProcess())
        return value.working,value.peak

    def preflight(self,budget):
        if 'MERIDIAN_GUARD_MEMBER_BYTES' not in os.environ:
            raise ValueError('Genuine stages require the reviewed external controller')
        # Known 1000-square diagnostic, unchanged 256-quad ownership. Refuse an
        # unapproved/inadequate temporary profile without opening a source raster.
        check_shape_capacity((1000,1000),budget)
        for entry in self.pins['inputs']:
            path=self.data_root/entry['path']
            if digest(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:
                raise ValueError('Pinned source changed')

    @contextmanager
    def reader(self,name):
        from readers import SwissNativeReader,SwissCoarseReader,CopernicusReader
        if name==MISSING[1]:
            reader=CopernicusReader(self.data_root/self.pins['inputs'][4]['path'])
            try:yield reader
            finally:reader.close()
        else:
            native=SwissNativeReader(self.data_root,self.pins)
            try:
                if name==SWISS[0]:reader=native
                else:
                    transform=None
                    if name==MISSING[0]:
                        import pyproj
                        operation=self.pins['compoundPipeline']
                        for entry in self.pins['inputs'][5:]:
                            operation=operation.replace(Path(entry['path']).name,
                                str(self.data_root/entry['path']).replace('\\','/'))
                        transform=pyproj.Transformer.from_pipeline(operation)
                    reader=SwissCoarseReader(native,smoothing=name==SWISS[2],transform=transform)
                yield reader
            finally:native.close()

    def metadata(self,name):
        swiss=name!=MISSING[1];geographic=name in MISSING
        return {'scope':'genuine','core':[2624000,1091000,2626000,1093000],
            'globalContextMetres':250 if not swiss else 0,'geographic':geographic,
            'units':'m','verticalReference':'EGM2008' if geographic else 'LN02',
            'surface':'DTM' if swiss else 'DSM','horizontalReference':'CRS84' if geographic else 'EPSG:2056',
            'sourceRevision':'2024/2 swissALTI3D' if swiss else '2021 retained public GLO-30; sub-release unknown',
            'interval':10,'subsetInterval':20,'indexInterval':100,
            'inputPinsSha256':digest(Path(__file__).with_name('input-pins.json')),
            'transformation':'pinned full compound XY/height operation' if name==MISSING[0] else 'none',
            'representation':name,'rightsRef':'input pins and source-aware-contour-pilot.md; original notices apply',
            'sourceNotice':'©swisstopo; Swiss Open Government Data' if swiss else
                'Modified Copernicus data; Copernicus GLO-30 F derivative terms and full retained notice apply',
            'verticalReferenceCode':'EPSG:3855' if geographic else 'EPSG:5728',
            'gridNotice':'CHGeo2004/EGM2008 retained CC0/public-domain lineage; no new licence acceptance',
            'accuracy':'unknown; combined transformation accuracy -1','epoch':'source-specific, per-cell epoch unknown',
            'sourceBoundary':'retained subset/support boundary, not national coverage'}

    def height_diagnostic(self,store):
        from readers import SwissNativeReader,SwissCoarseReader,CopernicusReader
        from rerun import height_diagnostic
        import pyproj
        operation=self.pins['compoundPipeline']
        for entry in self.pins['inputs'][5:]:
            operation=operation.replace(Path(entry['path']).name,str(self.data_root/entry['path']).replace('\\','/'))
        # Retained scalar diagnostic arrays are not contour vertices. The legacy
        # diagnostic retains two million height differences for exact quantiles;
        # reserve a conservative byte workspace before readers/arrays are created.
        # The member cap may refuse this; do not use a different summary silently.
        store.check(reserve_bytes=64*1024**2)
        native=SwissNativeReader(self.data_root,self.pins)
        cop=CopernicusReader(self.data_root/self.pins['inputs'][4]['path'])
        try:
            return height_diagnostic(SwissCoarseReader(native,transform=pyproj.Transformer.from_pipeline(operation)),
                                     SwissCoarseReader(native),cop,store)
        finally:native.close();cop.close()
