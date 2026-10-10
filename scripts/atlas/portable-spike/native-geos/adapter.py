"""Sequential test-only substitution; reuse accepted scientific query assembly."""
from pathlib import Path
import sys
from types import SimpleNamespace
from contextlib import contextmanager
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'native-window'))
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'geometry-crs'))
from window import WindowShared
from native_proj import NativeProj
from native import NativeGeos
import reader

class Pinned:
    def __init__(self,session,pin):
        self.session=session;self.view=session.owner.pin(pin)
        self.view.features=session.features
    def __getattr__(self,name):return getattr(self.view,name)
    def read(self,q):
        with self.session.query_scope(),self.session.geometry.arena():return self.view.read(q)
    def outcome(self,q):
        with self.session.query_scope(),self.session.geometry.arena():return self.view.outcome(q)
    def close(self):self.view.close()
    def __enter__(self):return self
    def __exit__(self,*_):self.close()

class NativeSession:
    """Same captured scientific snapshot; separate GEOS context, no shared opaque pointers."""
    def __init__(self,root,identity):
        self.owner=WindowShared(root,identity);self.geometry=None;self.proj=None;self.previous=None
        try:
            self.geometry=NativeGeos();self.proj=NativeProj()
            # Interchange only serialised, verified native XY/XYZ geometries.
            self.features={key:self.geometry.from_wkb(g.wkb) for key,g in self.owner._features.items()}
            self.open_ms=self.owner.open_ms
        except Exception:
            if self.geometry:self.geometry.close()
            if self.proj:self.proj.close()
            self.owner.close();raise

    def __getattr__(self,name):return getattr(self.owner,name)

    def __enter__(self):
        reader.require(not self.owner.closed,'projection-closed','Projection owner is closed.')
        return self

    @classmethod
    def from_store(cls,store,expected_identity=None):
        identifier=store.selected() if expected_identity is None else expected_identity
        store.receipt(identifier)
        return cls(store.package(identifier),identifier)

    @contextmanager
    def query_scope(self):
        if self.previous is not None:raise RuntimeError('Nested session entry is unsupported.')
        names=['Point','Polygon','box','mapping','projected','shapely']
        self.previous={name:getattr(reader,name) for name in names}
        geometry=self.geometry
        reader.Point=geometry.point;reader.Polygon=geometry.polygon;reader.box=geometry.box
        reader.mapping=geometry.mapping
        reader.projected=lambda g,s,t:geometry.projected(g,s,t,self.proj)
        reader.shapely=SimpleNamespace(points=lambda xs,ys:(xs,ys),covers=lambda g,points:geometry.covers_points(g,*points))
        try:yield
        finally:
            for name,value in self.previous.items():setattr(reader,name,value)
            self.previous=None

    def pin(self,generation):return Pinned(self,generation)

    def close(self):
        # Preserve the accepted requirement to close all pin leases before the owner.
        self.owner.close()
        if self.previous is not None:
            for name,value in self.previous.items():setattr(reader,name,value)
            self.previous=None
        self.features.clear();self.geometry.close();self.proj.close()

    def __exit__(self,*_):self.close()
