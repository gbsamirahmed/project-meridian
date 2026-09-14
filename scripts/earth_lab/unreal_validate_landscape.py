"""Run inside Unreal Editor after importing a Meridian Earth Landscape."""

from __future__ import annotations

import json
import os
from pathlib import Path

import unreal


def _vector(vector: unreal.Vector) -> list[float]:
    return [float(vector.x), float(vector.y), float(vector.z)]


manifest_value = os.environ.get("MERIDIAN_LANDSCAPE_MANIFEST")
if manifest_value:
    manifest_path = Path(manifest_value)
else:
    source_config = (
        Path(unreal.Paths.project_dir()) / "meridian-landscape-source.json"
    )
    source = json.loads(source_config.read_text(encoding="utf-8"))
    manifest_path = Path(source["manifest"])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
expected = manifest["unreal_landscape"]
landscapes = unreal.EditorLevelLibrary.get_all_level_actors_of_class(
    unreal.LandscapeProxy
)
if len(landscapes) != 1:
    raise RuntimeError(f"Expected exactly one Landscape, found {len(landscapes)}")

landscape = landscapes[0]
scale = landscape.get_actor_scale3d()
origin, extent = landscape.get_actor_bounds(False)
dimensions_cm = [float(extent.x * 2.0), float(extent.y * 2.0), float(extent.z * 2.0)]
expected_dimensions_cm = [
    value * 100.0 for value in expected["expected_world_dimensions_m"]
]
xy_tolerance_cm = max(float(expected["xy_scale_cm"]) * 2.0, 2.0)

checks = {
    "xy_scale_matches": (
        abs(float(scale.x) - float(expected["xy_scale_cm"])) < 1e-6
        and abs(float(scale.y) - float(expected["xy_scale_cm"])) < 1e-6
    ),
    "z_scale_matches": (
        abs(float(scale.z) - float(expected["z_scale"])) < 1e-6
    ),
    "width_matches": (
        abs(dimensions_cm[0] - expected_dimensions_cm[0]) <= xy_tolerance_cm
    ),
    "height_matches": (
        abs(dimensions_cm[1] - expected_dimensions_cm[1]) <= xy_tolerance_cm
    ),
}
report = {
    "manifest": str(manifest_path),
    "landscape_name": landscape.get_actor_label(),
    "actor_location_cm": _vector(landscape.get_actor_location()),
    "actor_scale": _vector(scale),
    "bounds_origin_cm": _vector(origin),
    "bounds_extent_cm": _vector(extent),
    "bounds_dimensions_cm": dimensions_cm,
    "checks": checks,
    "passed": all(checks.values()),
}
report_path = (
    Path(unreal.Paths.project_saved_dir()) / "meridian-landscape-validation.json"
)
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
unreal.log(f"MERIDIAN_LANDSCAPE_VALIDATION {json.dumps(report)}")
if not report["passed"]:
    raise RuntimeError(f"Landscape validation failed; see {report_path}")
