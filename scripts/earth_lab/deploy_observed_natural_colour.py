"""Deploy Lab 010 adapter using existing renderer bootstrap; no map editing."""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import experiment_paths
from meridian_paths import resolve_storage_roots


def deploy():
    repo = Path(__file__).resolve().parents[2]
    renderer = repo / "renderers/unreal/tryfan-reference"
    spec = importlib.util.spec_from_file_location("tryfan_bootstrap", renderer / "bootstrap_renderer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = resolve_storage_roots(repository_root=repo, require_data=True).data
    module.bootstrap(root)
    output = root / "experiments/earth-lab/tryfan-010/observed-natural-colour-v1"
    if not (output / "lab010-manifest.json").is_file():
        raise FileNotFoundError("Build the Lab 010 observed products first")
    shutil.copy2(repo / "scripts/earth_lab/unreal_observed_natural_colour.py", renderer / "Content/Python/setup_lab010_surface.py")
    (renderer / "meridian-lab010-source.json").write_text(json.dumps({"repository_root": str(repo), "output_root": str(output)}, indent=2))
    print("Lab 010 deployed; preserved map not edited")


if __name__ == "__main__":
    deploy()
