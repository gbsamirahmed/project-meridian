"""Deploy repository-owned Lab 009 Unreal scripts and source pointers."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def deploy(config_path: Path) -> dict[str, str]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    repo = config_path.parents[2]
    project_file = (repo / config["unreal"]["project"]).resolve()
    project_root = project_file.parent
    python_root = project_root / "Content" / "Python"
    python_root.mkdir(parents=True, exist_ok=True)
    copies = {
        repo / "scripts" / "earth_lab" / "unreal_surface_reconstruction.py": python_root / "setup_lab009_surface.py",
        repo / "scripts" / "earth_lab" / "unreal_capture_surface_reconstruction.py": python_root / "capture_lab009_surface.py",
        repo / "scripts" / "earth_lab" / "unreal_validate_surface_reconstruction.py": python_root / "validate_lab009_surface.py",
    }
    for source, target in copies.items():
        shutil.copy2(source, target)
        if source.read_bytes() != target.read_bytes():
            raise RuntimeError(f"Deployed copy differs: {target}")
    output_root = (repo / config["output_root"]).resolve()
    pointer = {"schema_version": 1, "config": str(config_path), "output_root": str(output_root)}
    pointer_path = project_root / "meridian-lab009-source.json"
    pointer_path.write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")
    return {"project": str(project_file), "setup_script": str(copies[next(iter(copies))]), "pointer": str(pointer_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(deploy(args.config), indent=2))


if __name__ == "__main__":
    main()
