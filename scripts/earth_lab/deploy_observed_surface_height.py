"""Deploy Lab 011 helpers; canonical map and existing Lab products are untouched."""
from pathlib import Path
import json
import shutil

from deploy_observed_natural_colour import deploy as deploy_lab010
from meridian_paths import resolve_storage_roots


def deploy():
    repo = Path(__file__).resolve().parents[2]
    root = resolve_storage_roots(repository_root=repo, require_data=True).data
    output = root / "experiments/earth-lab/tryfan-011/observed-surface-height-v1"
    if not (output / "lab011-manifest.json").is_file():
        raise FileNotFoundError("Build Lab 011 diagnostics before deployment")
    deploy_lab010()
    renderer = repo / "renderers/unreal/tryfan-reference"
    shutil.copy2(repo / "scripts/earth_lab/unreal_observed_surface_height.py",
                 renderer / "Content/Python/setup_lab011_surface.py")
    (renderer / "meridian-lab011-source.json").write_text(
        json.dumps({"repository_root": str(repo), "output_root": str(output)}, indent=2)+"\n", encoding="utf-8")
    print("Lab 011 deployed; canonical map not edited")


if __name__ == "__main__":
    deploy()
