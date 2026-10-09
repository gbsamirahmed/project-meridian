"""One verified captured projection, explicit pinned leases; sequential desktop spike."""
from pathlib import Path
import sys
import time

# Only the existing independent spike is reused, never the Atlas authority.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reader import Reader, require
from verification import Snapshot
from shapely.geometry import shape

EXPERIMENT = 'shared-snapshot-experiment/v1'

class _PinnedView(Reader):
    """Reuse every accepted query method; only resource ownership differs."""
    def __init__(self, owner, generation):
        start = time.perf_counter()
        require(not owner.closed, 'projection-closed', 'Projection owner is closed.')
        require(isinstance(generation, str) and generation in owner._snapshot.generations,
                'projection-generation', 'Selected generation is unavailable; no fallback.')
        self._owner = owner
        self.root = owner.root
        self.snapshot = owner._snapshot
        self.manifest = self.snapshot.manifest
        data = self.snapshot.generations[generation]
        self.base = data['answer']; self.pool = self.base['documents']
        self.knowledge = data['knowledge']
        self.records = {r['key']: r for r in self.base['results']}
        self.selectors = {s['key']: s for s in data['selectors']}
        self.features = owner._features
        self.worldcover = self.snapshot.worldcover
        self.edges = self.base['relationships']
        self.generation = generation; self.closed = False
        self.startup_ms = (time.perf_counter() - start) * 1000
        owner._views.add(self)

    def close(self):
        if not self.closed:
            self.closed = True
            self._owner._views.remove(self)

class SharedProjection:
    """No global cache or path rereads; explicit lifetime for a fully verified snapshot."""
    def __init__(self, root, expected_identity):
        start = time.perf_counter()
        self.root = Path(root).absolute(); self.closed = True; self._views = set()
        self._snapshot = Snapshot(self.root, expected_identity)
        try:
            self._features = {k: shape(f['native']['geometry']) for k, f in self._snapshot.features.items()}
            self.closed = False
            self.open_ms = (time.perf_counter() - start) * 1000
        except Exception:
            self._snapshot.close()
            raise

    @classmethod
    def from_store(cls, store, expected_identity=None):
        # Installation selection is independent of the exact scientific pin on pin().
        identifier = store.selected() if expected_identity is None else expected_identity
        store.receipt(identifier)
        return cls(store.package(identifier), identifier)

    def pin(self, exact_generation):
        return _PinnedView(self, exact_generation)

    def close(self):
        if self.closed: return
        require(not self._views, 'projection-busy', 'Close all pinned views before releasing the shared snapshot.')
        self._snapshot.close(); self._features.clear(); self.closed = True

    def __enter__(self): return self
    def __exit__(self, *_): self.close()

def main():
    import argparse
    import json
    from reader import ReadError
    from store import Store
    parser=argparse.ArgumentParser(); parser.add_argument('--store',required=True)
    parser.add_argument('--identity'); parser.add_argument('--generation',required=True)
    parser.add_argument('--query',default='{"identity":"glaciers:683"}')
    args=parser.parse_args()
    try:
        with SharedProjection.from_store(Store(args.store),args.identity) as owner, owner.pin(args.generation) as view:
            outcome=view.outcome(json.loads(args.query))
        print(json.dumps(outcome,ensure_ascii=False,allow_nan=False))
        return 1 if outcome['kind']=='error' else 0
    except (ReadError,OSError,ValueError) as error:
        print(json.dumps({'kind':'error','code':error.code if isinstance(error,ReadError) else 'query-malformed',
                          'message':str(error) if isinstance(error,ReadError) else 'Check the explicit store and JSON request.'}))
        return 1

if __name__=='__main__': sys.exit(main())
