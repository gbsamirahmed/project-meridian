"""One desktop C-API binding experiment; no custom CRS maths or reader replacement."""
import ctypes as C
from contextlib import contextmanager
import hashlib
from importlib.metadata import distribution
import math
import os
from pathlib import Path


# Compatibility identity copied from the accepted native-window closure, not CRS maths.
PIPELINE = "proj=pipeline step inv proj=somerc lat_0=46.9524055555556 lon_0=7.43958333333333 k_0=1 x_0=2600000 y_0=1200000 ellps=bessel step proj=push v_3 step proj=cart ellps=bessel step proj=helmert x=674.374 y=15.056 z=405.346 step inv proj=cart ellps=WGS84 step proj=pop v_3 step proj=unitconvert xy_in=rad xy_out=deg"

class BindingError(RuntimeError):
    pass


class Info(C.Structure):
    _fields_ = [("major", C.c_int), ("minor", C.c_int), ("patch", C.c_int),
                ("release", C.c_char_p), ("version", C.c_char_p),
                ("searchpath", C.c_char_p), ("paths", C.POINTER(C.c_char_p)),
                ("path_count", C.c_size_t)]


class NativeProj:
    """Owned sequential context; explicitly pinned resources and longitude-first axes."""
    def __init__(self):
        if os.name != 'nt':
            raise BindingError('Only the inventoried Windows wheel layout is tested.')
        wheel = distribution('pyproj')
        if wheel.version != '3.7.2':
            raise BindingError('Wheel version needs review; no binary fallback.')
        root = Path(wheel.locate_file('')).resolve()
        libraries = list((root/'pyproj.libs').glob('proj_9-*.dll'))
        data = root/'pyproj/proj_dir/share/proj'
        if len(libraries) != 1 or not (data/'proj.db').is_file():
            raise BindingError('Exact local PROJ DLL/database unavailable.')
        self.directory_handle = os.add_dll_directory(str(libraries[0].parent))
        self.lib = C.CDLL(str(libraries[0]))
        self.ctx = None; self.operations = {}; self.closed = True
        p, s, i, d, n = C.c_void_p, C.c_char_p, C.c_int, C.POINTER(C.c_double), C.c_size_t
        def bind(name, result, args):
            fn = getattr(self.lib, name); fn.restype = result; fn.argtypes = args
        bind('proj_info', Info, [])
        bind('proj_context_create', p, [])
        bind('proj_context_destroy', p, [p])
        bind('proj_context_set_search_paths', None, [p, i, C.POINTER(s)])
        bind('proj_context_set_enable_network', i, [p, i])
        bind('proj_context_is_network_enabled', i, [p])
        bind('proj_create_crs_to_crs', p, [p, s, s, p])
        bind('proj_normalize_for_visualization', p, [p, p])
        bind('proj_as_proj_string', s, [p, p, i, C.POINTER(s)])
        bind('proj_destroy', p, [p])
        bind('proj_errno_reset', i, [p])
        bind('proj_errno', i, [p])
        bind('proj_trans_generic', n, [p, i, d, n, n, d, n, n, d, n, n, d, n, n])
        info = self.lib.proj_info()
        if (info.major, info.minor, info.patch) != (9, 5, 1):
            self.directory_handle.close()
            raise BindingError('Native PROJ version needs review.')
        self.identity = {'version': info.version.decode(),
                         'dllSha256': hashlib.sha256(libraries[0].read_bytes()).hexdigest(),
                         'databaseSha256': hashlib.sha256((data/'proj.db').read_bytes()).hexdigest()}
        try:
            self.ctx = self.lib.proj_context_create()
            if not self.ctx: raise BindingError('PROJ context allocation failed.')
            paths = (s*1)(str(data).encode('utf-8'))
            self.lib.proj_context_set_search_paths(self.ctx, 1, paths)
            self.lib.proj_context_set_enable_network(self.ctx, 0)
            if self.lib.proj_context_is_network_enabled(self.ctx):
                raise BindingError('PROJ network must be disabled.')
            self.closed = False
        except Exception:
            self.close(); raise

    def operation(self, source, target):
        if self.closed: raise BindingError('CRS context is closed.')
        source = 'EPSG:4326' if source == 'OGC:CRS84' else source
        target = 'EPSG:4326' if target == 'OGC:CRS84' else target
        if source not in ('EPSG:2056', 'EPSG:4326') or target not in ('EPSG:2056', 'EPSG:4326'):
            raise BindingError('Unsupported CRS; no inferred operation.')
        key = (source, target)
        if key not in self.operations:
            raw = self.lib.proj_create_crs_to_crs(self.ctx, source.encode(), target.encode(), None)
            if not raw: raise BindingError('Cannot resolve exact CRS operation.')
            try: normal = self.lib.proj_normalize_for_visualization(self.ctx, raw)
            finally: self.lib.proj_destroy(raw)
            if not normal: raise BindingError('Cannot normalise longitude/easting-first axes.')
            text = self.lib.proj_as_proj_string(self.ctx, normal, 0, None)
            if not text:
                self.lib.proj_destroy(normal)
                raise BindingError('Cannot record resolved operation.')
            definition = text.decode().replace('+', '')
            # Native-window closure is bound to this exact checked horizontal operation.
            if key == ('EPSG:2056', 'EPSG:4326') and definition != PIPELINE:
                self.lib.proj_destroy(normal)
                raise BindingError('Native-window operation differs; no sampled fallback.')
            self.operations[key] = (normal, definition)
        return self.operations[key]

    def xy(self, xs, ys, source, target):
        op, _ = self.operation(source, target)
        xs, ys = tuple(xs), tuple(ys)
        if len(xs) != len(ys) or not all(math.isfinite(v) for v in xs+ys):
            raise BindingError('Finite aligned XY arrays required.')
        if not xs: return (), ()
        x = (C.c_double*len(xs))(*xs); y = (C.c_double*len(ys))(*ys)
        self.lib.proj_errno_reset(op)
        count = self.lib.proj_trans_generic(op, 1, x, C.sizeof(C.c_double), len(xs),
                                            y, C.sizeof(C.c_double), len(ys),
                                            None, 0, 0, None, 0, 0)
        if count != len(xs) or self.lib.proj_errno(op) or not all(math.isfinite(v) for v in tuple(x)+tuple(y)):
            raise BindingError('Coordinate transformation failed; not empty evidence.')
        return tuple(x), tuple(y)

    def projected(self, geometry, source, target):
        if self.closed: raise BindingError('CRS context is closed.')
        if source == target: return geometry
        from shapely.ops import transform
        def callback(xs, ys, z=None):
            if z is not None: raise BindingError('Vertical transformation is outside this profile.')
            return self.xy(xs, ys, source, target)
        return transform(callback, geometry)

    def close(self):
        for op, _ in self.operations.values(): self.lib.proj_destroy(op)
        self.operations.clear()
        if self.ctx: self.lib.proj_context_destroy(self.ctx); self.ctx = None
        self.closed = True
        if self.directory_handle is not None:
            self.directory_handle.close(); self.directory_handle = None

    def __enter__(self): return self
    def __exit__(self, *_): self.close()


@contextmanager
def comparison_binding(binding):
    """Test-only sequential override, restored even on failure; never used by production."""
    import reader
    previous = reader.projected
    reader.projected = binding.projected
    try: yield
    finally: reader.projected = previous
