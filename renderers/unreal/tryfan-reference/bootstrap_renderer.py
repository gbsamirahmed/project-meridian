"""Deploy reproducible dependencies for the preserved Tryfan renderer.

The calibrated map and curated project configuration are durable source. This
bootstrap deploys repository-owned Python and writes machine-local source pointers;
it never edits or saves the map.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


RENDERER_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RENDERER_ROOT.parents[2]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from meridian_paths import resolve_storage_roots  # noqa: E402


EXPECTED_FILES = {
    "landscape_manifest": (
        Path("earth-lab/tryfan-004/unreal-landscape-v1/unreal-landscape-manifest.json"),
        "59d72fa28e67f59002acf7c947b9571708682459c07972f091069d3c3b51f34c",
    ),
    "canonical_r16": (
        Path("earth-lab/tryfan-004/unreal-landscape-v1/heightmaps/tryfan-004-dtm-1m-landscape-3025.r16"),
        "31cbe763dac4072772ac9bcb4a3217b78eba0c10265e576ede708154288f6bf6",
    ),
    "reference_photo": (
        Path("earth-lab/tryfan-004/reference/tryfan-tony-edwards-2009.jpg"),
        "09ccb9ade2bdae3818bfc8e8444bd93f8865d4a55fa9290332b5a78f89afd3cb",
    ),
    "lab009_report": (
        Path("earth-lab/tryfan-009/surface-reconstruction-v0.1/lab009-report.json"),
        "9822577d3d34b7844e2371e219213dfda73830e2121b6aa02c28d484fb95d8b2",
    ),
    "lab009_package": (
        Path("earth-lab/tryfan-009/surface-reconstruction-v0.1/lab009-reconstruction-package.json"),
        "7111d1857374eef76e5ac26ef3a719be09b9f6a55cb570c0aa74e42b634facd8",
    ),
    "lab009_surface_controls": (
        Path("earth-lab/tryfan-009/surface-reconstruction-v0.1/unreal/lab009-surface-controls-rgba.png"),
        "becd36431182b1d368bc2e6bd9c09e3f0719d1f6d9e1ec320a8b2b02f6d386be",
    ),
    "lab009_context_controls": (
        Path("earth-lab/tryfan-009/surface-reconstruction-v0.1/unreal/lab009-context-controls-rgba.png"),
        "4934799aab82cea4d694ee9edd51680d59ebae9c2001bdfd77cb5703f71a0b90",
    ),
}

PYTHON_SOURCES = {
    "validate_landscape.py": "unreal_validate_landscape.py",
    "place_observer.py": "unreal_place_observer.py",
    "observer_geometry.py": "observer_geometry.py",
    "photo_overlay.py": "photo_overlay.py",
    "setup_photo_overlay.py": "unreal_photo_overlay.py",
    "restore_lab004a_camera.py": "unreal_restore_camera.py",
    "validate_lab004a_camera.py": "unreal_validate_camera.py",
    "setup_lab009_surface.py": "unreal_surface_reconstruction.py",
    "capture_lab009_surface.py": "unreal_capture_surface_reconstruction.py",
    "validate_lab009_surface.py": "unreal_validate_surface_reconstruction.py",
    "validate_reference_renderer.py": "unreal_validate_reference_renderer.py",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_external_inputs(data_root: Path) -> dict[str, str]:
    verified: dict[str, str] = {}
    for name, (relative_path, expected_hash) in EXPECTED_FILES.items():
        path = data_root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Required renderer input is missing: {path}")
        observed_hash = sha256(path)
        if observed_hash != expected_hash:
            raise RuntimeError(
                f"Renderer input hash mismatch for {name}: expected "
                f"{expected_hash}, observed {observed_hash} ({path})"
            )
        verified[name] = observed_hash

    report = json.loads(
        (data_root / EXPECTED_FILES["lab009_report"][0]).read_text(encoding="utf-8")
    )
    expected_result = "14f90941468166dc3937879e022e8fedff2d9d212eed5cfb1c5deb0407c6a859"
    if report.get("deterministic_result_sha256") != expected_result:
        raise RuntimeError("Lab 009 deterministic result identity is not the frozen value")
    return verified


def bootstrap(data_root: Path, renderer_root: Path = RENDERER_ROOT) -> dict[str, object]:
    data_root = data_root.resolve()
    renderer_root = renderer_root.resolve()
    verified = verify_external_inputs(data_root)

    map_path = renderer_root / "Content" / "Tryfan_Lab004.umap"
    expected_map_hash = "85ef8f1cc9a9fda9b6f2ab3b911bd57831fe75c4009e5ad168ea4956165a260d"
    if not map_path.is_file() or sha256(map_path) != expected_map_hash:
        raise RuntimeError("Preserved Tryfan_Lab004.umap is missing or has changed")

    python_root = renderer_root / "Content" / "Python"
    python_root.mkdir(parents=True, exist_ok=True)
    deployed: list[str] = []
    source_root = REPOSITORY_ROOT / "scripts" / "earth_lab"
    for target_name, source_name in PYTHON_SOURCES.items():
        source = source_root / source_name
        target = python_root / target_name
        shutil.copy2(source, target)
        if source.read_bytes() != target.read_bytes():
            raise RuntimeError(f"Deployed Python differs from repository source: {target}")
        deployed.append(target.relative_to(renderer_root).as_posix())

    landscape_manifest = data_root / EXPECTED_FILES["landscape_manifest"][0]
    lab009_root = data_root / "earth-lab/tryfan-009/surface-reconstruction-v0.1"
    pointers = {
        "meridian-landscape-source.json": {"manifest": str(landscape_manifest)},
        "meridian-benchmark-source.json": {
            "benchmark": str(REPOSITORY_ROOT / "docs/earth-lab/tryfan-004-benchmark.json")
        },
        "meridian-photo-overlay-source.json": {
            "config": str(REPOSITORY_ROOT / "docs/earth-lab/tryfan-004-photo-overlay.json")
        },
        "meridian-lab009-source.json": {
            "schema_version": 1,
            "config": str(
                REPOSITORY_ROOT / "docs/earth-lab/tryfan-009-surface-reconstruction.json"
            ),
            "output_root": str(lab009_root),
        },
    }
    for name, payload in pointers.items():
        (renderer_root / name).write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )

    return {
        "renderer_root": str(renderer_root),
        "data_root": str(data_root),
        "external_inputs_verified": verified,
        "deployed_python": deployed,
        "source_pointers": sorted(pointers),
        "map_sha256": expected_map_hash,
        "map_modified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy reproducible dependencies for the Tryfan Reference Renderer."
    )
    parser.add_argument("--data-root", type=Path)
    arguments = parser.parse_args()
    data_root = (
        arguments.data_root.resolve()
        if arguments.data_root is not None
        else resolve_storage_roots(repository_root=REPOSITORY_ROOT, require_data=True).data
    )
    print(json.dumps(bootstrap(data_root), indent=2))


if __name__ == "__main__":
    main()
