"""Reuse the sealed fixture adapter; substitute only the scoped CRS callback."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'native-window'))
from native_proj import NativeProj, comparison_binding
from replay import run

if __name__ == '__main__':
    with NativeProj() as binding, comparison_binding(binding):
        sys.exit(run())
