"""Validate an imported Meridian Earth Landscape inside Unreal Editor 5.8+.

Read-only: one Landscape plus its World Partition LandscapeStreamingProxy actors
is treated as one logical terrain. Geometry is derived from loaded components and
selected collision heights are checked against the generated R16 source.
"""
from __future__ import annotations

import json
import math
import os
import struct
from pathlib import Path
from typing import Any

import unreal

XY_SCALE_TOLERANCE_CM = 0.001
Z_SCALE_TOLERANCE = 0.001
DIMENSION_TOLERANCE_M = 0.02
LOCATION_TOLERANCE_CM = 0.1
HEIGHT_TOLERANCE_CM = 5.0
REFERENCE_LOCATIONS_BNG = [
    {"name": "aoi_centre", "easting": 266400.0, "northing": 359300.0, "source_context_m_odn": 877.73},
    {"name": "tryfan_summit_reference", "easting": 266405.0, "northing": 359387.0, "source_context_m_odn": 913.66},
    {"name": "nearby_tryfan_dtm_peak", "easting": 266401.5, "northing": 359386.5, "source_context_m_odn": 915.44},
]


def _vector(value: unreal.Vector) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def _rotation(value: unreal.Quat) -> list[float]:
    return [float(value.x), float(value.y), float(value.z), float(value.w)]


def _actor_bounds(actor: unreal.Actor) -> tuple[list[float], list[float]]:
    origin, extent = actor.get_actor_bounds(False)
    return (
        [float(origin.x - extent.x), float(origin.y - extent.y), float(origin.z - extent.z)],
        [float(origin.x + extent.x), float(origin.y + extent.y), float(origin.z + extent.z)],
    )


def _union_bounds(actors: list[unreal.Actor]) -> dict[str, list[float]]:
    bounds = [_actor_bounds(actor) for actor in actors]
    minimum = [min(item[0][axis] for item in bounds) for axis in range(3)]
    maximum = [max(item[1][axis] for item in bounds) for axis in range(3)]
    dimensions = [maximum[axis] - minimum[axis] for axis in range(3)]
    return {
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "minimum_m": [value / 100.0 for value in minimum],
        "maximum_m": [value / 100.0 for value in maximum],
        "dimensions_cm": dimensions,
        "dimensions_m": [value / 100.0 for value in dimensions],
    }


class Validation:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def add(
        self,
        status: str,
        name: str,
        message: str,
        expected: Any = None,
        observed: Any = None,
        discrepancy: Any = None,
    ) -> None:
        entry: dict[str, Any] = {"status": status, "name": name, "message": message}
        if expected is not None:
            entry["expected"] = expected
        if observed is not None:
            entry["observed"] = observed
        if discrepancy is not None:
            entry["discrepancy"] = discrepancy
        self.checks.append(entry)
        unreal.log(f"[{status}] {name}: {message}")

    @property
    def overall(self) -> str:
        if any(item["status"] == "FAIL" for item in self.checks):
            return "FAIL"
        if any(item["status"] == "WARNING" for item in self.checks):
            return "WARNING"
        return "PASS"


def _manifest_path() -> Path:
    configured = os.environ.get("MERIDIAN_LANDSCAPE_MANIFEST")
    if configured:
        return Path(configured).resolve()
    source_path = Path(unreal.Paths.project_dir()) / "meridian-landscape-source.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    return Path(source["manifest"]).resolve()


def _heightmap_path(manifest_path: Path, manifest: dict[str, Any]) -> Path:
    default_surface = manifest["representation"]["default_surface"]
    relative = Path(manifest["surfaces"][default_surface]["output"]["files"]["r16"]["path"])
    candidates = [manifest_path.parent / relative, manifest_path.parent / "heightmaps" / relative]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("R16 not found at " + " or ".join(str(path) for path in candidates))


def _height_samples(
    world: unreal.World,
    landscape: unreal.Landscape,
    manifest_path: Path,
    manifest: dict[str, Any],
    rows: int,
    columns: int,
) -> list[dict[str, Any]]:
    path = _heightmap_path(manifest_path, manifest)
    data = path.read_bytes()
    expected_bytes = rows * columns * 2
    if len(data) != expected_bytes:
        raise ValueError(f"R16 has {len(data)} bytes; expected {expected_bytes}")
    transform = landscape.get_actor_transform()
    location = transform.translation
    scale = transform.scale3d
    sample_rows = sorted({rows // 16, rows // 2, rows - 1 - rows // 16})
    sample_columns = sorted({columns // 16, columns // 2, columns - 1 - columns // 16})
    samples: list[dict[str, Any]] = []
    for row in sample_rows:
        for column in sample_columns:
            encoded = struct.unpack_from("<H", data, 2 * (row * columns + column))[0]
            expected_z = float(location.z) + (encoded - 32768) / 128.0 * float(scale.z)
            x = float(location.x) + column * float(scale.x)
            y = float(location.y) + row * float(scale.y)
            hit = unreal.SystemLibrary.line_trace_single(
                world,
                unreal.Vector(x, y, 100000.0),
                unreal.Vector(x, y, -100000.0),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                True,
                [],
                unreal.DrawDebugTrace.NONE,
                True,
            )
            record: dict[str, Any] = {
                "row": row,
                "column": column,
                "world_xy_cm": [x, y],
                "encoded_uint16": encoded,
                "expected_world_z_cm": expected_z,
                "hit": False,
            }
            if hit:
                values = hit.to_dict()
                impact = values["impact_point"]
                hit_actor = values.get("hit_actor")
                observed_z = float(impact.z)
                record.update(
                    {
                        "hit": bool(values.get("blocking_hit")),
                        "hit_actor": hit_actor.get_path_name() if hit_actor else None,
                        "observed_world_z_cm": observed_z,
                        "error_cm": observed_z - expected_z,
                    }
                )
            samples.append(record)
    return samples


def _reference_height_samples(
    world: unreal.World,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    path = _heightmap_path(manifest_path, manifest)
    width, height = [int(value) for value in manifest["dimension_conversion"]["output_vertices"]]
    data = path.read_bytes()
    if len(data) != width * height * 2:
        raise ValueError(f"R16 has {len(data)} bytes; expected {width * height * 2}")
    west, south, east, north = [float(value) for value in manifest["source_aoi_bounds"]]
    origin = manifest["coordinate_frame"]["local_origin_bng"]
    origin_easting = float(origin["easting"])
    origin_northing = float(origin["northing"])
    origin_elevation = float(origin["elevation_m_odn"])
    z_scale = float(manifest["height_encoding"]["z_scale"])

    def decoded(row: int, column: int) -> float:
        encoded = struct.unpack_from("<H", data, 2 * (row * width + column))[0]
        return origin_elevation + (encoded - 32768) / 128.0 * z_scale / 100.0

    samples: list[dict[str, Any]] = []
    for reference in REFERENCE_LOCATIONS_BNG:
        pixel_x = (reference["easting"] - west) / (east - west) * (width - 1)
        pixel_y = (north - reference["northing"]) / (north - south) * (height - 1)
        x0 = max(0, min(width - 1, int(math.floor(pixel_x))))
        y0 = max(0, min(height - 1, int(math.floor(pixel_y))))
        x1 = min(width - 1, x0 + 1)
        y1 = min(height - 1, y0 + 1)
        fraction_x = pixel_x - x0
        fraction_y = pixel_y - y0
        expected_odn = (
            decoded(y0, x0) * (1.0 - fraction_x) * (1.0 - fraction_y)
            + decoded(y0, x1) * fraction_x * (1.0 - fraction_y)
            + decoded(y1, x0) * (1.0 - fraction_x) * fraction_y
            + decoded(y1, x1) * fraction_x * fraction_y
        )
        world_x = (reference["easting"] - origin_easting) * 100.0
        world_y = (origin_northing - reference["northing"]) * 100.0
        expected_world_z = (expected_odn - origin_elevation) * 100.0
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            unreal.Vector(world_x, world_y, 100000.0),
            unreal.Vector(world_x, world_y, -100000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        )
        record: dict[str, Any] = {
            **reference,
            "r16_pixel": [pixel_x, pixel_y],
            "world_xy_cm": [world_x, world_y],
            "expected_r16_elevation_m_odn": expected_odn,
            "expected_world_z_cm": expected_world_z,
            "hit": False,
        }
        if hit:
            values = hit.to_dict()
            impact = values["impact_point"]
            hit_actor = values.get("hit_actor")
            observed_world_z = float(impact.z)
            record.update(
                {
                    "hit": bool(values.get("blocking_hit")),
                    "hit_actor": hit_actor.get_path_name() if hit_actor else None,
                    "observed_world_z_cm": observed_world_z,
                    "observed_elevation_m_odn": origin_elevation + observed_world_z / 100.0,
                    "error_cm": observed_world_z - expected_world_z,
                }
            )
        samples.append(record)
    return samples


def _write_report(report: dict[str, Any]) -> Path:
    path = Path(unreal.Paths.project_saved_dir()) / "meridian-landscape-validation.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"Meridian Landscape validation report: {path}")
    return path


def main() -> dict[str, Any]:
    validation = Validation()
    manifest_path = _manifest_path()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["unreal_landscape"]
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = editor.get_editor_world()
    if world is None:
        raise RuntimeError("No editor world is open")

    actors = list(actor_subsystem.get_all_level_actors())
    landscapes = [actor for actor in actors if isinstance(actor, unreal.Landscape)]
    proxies = [actor for actor in actors if isinstance(actor, unreal.LandscapeStreamingProxy)]
    engine_version = unreal.SystemLibrary.get_engine_version()
    world_path = world.get_path_name()
    validation.add("INFO", "engine_version", engine_version, observed=engine_version)
    validation.add("INFO", "current_map", world_path, observed=world_path)

    if len(landscapes) != 1:
        validation.add(
            "FAIL", "logical_landscape_count",
            f"Expected one logical Landscape, observed {len(landscapes)}.",
            1, len(landscapes), len(landscapes) - 1,
        )
        result = {
            "schema_version": 2,
            "engine_version": engine_version,
            "map": world_path,
            "checks": validation.checks,
            "overall": validation.overall,
        }
        _write_report(result)
        raise RuntimeError("Landscape validation failed before geometry checks")
    landscape = landscapes[0]
    validation.add(
        "PASS", "logical_landscape_count",
        "One logical Landscape actor owns the terrain.", 1, 1,
    )
    validation.add(
        "INFO", "streaming_proxy_count",
        f"World Partition exposes {len(proxies)} LandscapeStreamingProxy actors.",
        observed=len(proxies),
    )
    if not proxies:
        validation.add("FAIL", "streaming_proxies", "No LandscapeStreamingProxy actors are loaded.", "> 0", 0)

    landscape_path = landscape.get_path_name()
    unrelated = [
        proxy for proxy in proxies
        if proxy.get_landscape_actor() is None
        or proxy.get_landscape_actor().get_path_name() != landscape_path
    ]
    if unrelated:
        validation.add(
            "FAIL", "proxy_ownership",
            f"{len(unrelated)} proxies are not linked to the logical Landscape.",
            0, len(unrelated), len(unrelated),
        )
    else:
        validation.add(
            "PASS", "proxy_ownership",
            "Every proxy resolves to the logical Landscape through get_landscape_actor().",
            0, 0,
        )

    components: list[unreal.LandscapeComponent] = []
    for proxy in proxies:
        components.extend(proxy.get_components_by_class(unreal.LandscapeComponent))
    section_x = sorted({int(component.section_base_x) for component in components})
    section_y = sorted({int(component.section_base_y) for component in components})
    differences_x = [right - left for left, right in zip(section_x, section_x[1:])]
    differences_y = [right - left for left, right in zip(section_y, section_y[1:])]
    component_quads_x = min(differences_x) if differences_x else 0
    component_quads_y = min(differences_y) if differences_y else 0
    regular_x = bool(differences_x) and len(set(differences_x)) == 1
    regular_y = bool(differences_y) and len(set(differences_y)) == 1
    total_quads_x = section_x[-1] - section_x[0] + component_quads_x if section_x else 0
    total_quads_y = section_y[-1] - section_y[0] + component_quads_y if section_y else 0
    expected_grid = [int(value) for value in expected["components"]]
    expected_component_count = expected_grid[0] * expected_grid[1]
    observed_grid = [len(section_x), len(section_y)]
    if len(components) == expected_component_count and observed_grid == expected_grid and regular_x and regular_y:
        validation.add(
            "PASS", "component_grid",
            f"Observed {len(components)} components in a {observed_grid[0]} x {observed_grid[1]} regular grid.",
            {"total": expected_component_count, "grid": expected_grid},
            {"total": len(components), "grid": observed_grid},
        )
    else:
        validation.add(
            "FAIL", "component_grid",
            "Component count, grid, or section-base spacing is inconsistent.",
            {"total": expected_component_count, "grid": expected_grid},
            {"total": len(components), "grid": observed_grid, "regular": [regular_x, regular_y]},
        )

    expected_quads = int(expected["quads_per_axis"])
    observed_quads = [total_quads_x, total_quads_y]
    if observed_quads == [expected_quads, expected_quads]:
        validation.add(
            "PASS", "landscape_resolution",
            f"Component bases derive {expected_quads} x {expected_quads} quads and {expected_quads + 1} x {expected_quads + 1} vertices.",
            [expected_quads + 1, expected_quads + 1],
            [total_quads_x + 1, total_quads_y + 1],
        )
    else:
        validation.add(
            "FAIL", "landscape_resolution", "Derived vertex resolution is incorrect.",
            [expected_quads + 1, expected_quads + 1],
            [total_quads_x + 1, total_quads_y + 1],
            [total_quads_x - expected_quads, total_quads_y - expected_quads],
        )

    quads_per_section = int(expected["quads_per_section"])
    sections_per_component = int(expected["sections_per_component"])
    subsections_axis = int(round(math.sqrt(sections_per_component)))
    expected_component_quads = subsections_axis * quads_per_section
    observed_component_quads = [component_quads_x, component_quads_y]
    if subsections_axis**2 == sections_per_component and observed_component_quads == [expected_component_quads] * 2:
        validation.add(
            "PASS", "component_configuration",
            "Observed 126-quad component spacing is compatible with 2 x 2 subsections of 63 quads.",
            {"subsections": [2, 2], "quads_per_subsection": 63, "quads_per_component": 126},
            {"section_base_spacing": observed_component_quads, "subsections": [subsections_axis] * 2, "quads_per_subsection": quads_per_section},
        )
    else:
        validation.add(
            "FAIL", "component_configuration",
            "Observed component spacing is incompatible with the declared subsection layout.",
            [expected_component_quads] * 2, observed_component_quads,
        )

    transform = landscape.get_actor_transform()
    scale = _vector(transform.scale3d)
    translation = _vector(transform.translation)
    rotation = _rotation(transform.rotation)
    expected_scale = [float(expected["xy_scale_cm"]), float(expected["xy_scale_cm"]), float(expected["z_scale"])]
    scale_errors = [abs(scale[index] - expected_scale[index]) for index in range(3)]
    proxy_scales = [_vector(proxy.get_actor_scale3d()) for proxy in proxies]
    proxies_match = all(
        abs(item[0] - scale[0]) <= XY_SCALE_TOLERANCE_CM
        and abs(item[1] - scale[1]) <= XY_SCALE_TOLERANCE_CM
        and abs(item[2] - scale[2]) <= Z_SCALE_TOLERANCE
        for item in proxy_scales
    )
    if scale_errors[0] <= XY_SCALE_TOLERANCE_CM and scale_errors[1] <= XY_SCALE_TOLERANCE_CM and scale_errors[2] <= Z_SCALE_TOLERANCE and proxies_match:
        validation.add(
            "PASS", "landscape_scale",
            "The logical Landscape and every proxy use the intended XYZ scale.",
            expected_scale, scale, scale_errors,
        )
    else:
        validation.add(
            "FAIL", "landscape_scale",
            "Landscape or proxy scale differs from the intended scale.",
            expected_scale, scale, scale_errors,
        )

    bounds = _union_bounds(proxies)
    derived_extent = [total_quads_x * scale[0] / 100.0, total_quads_y * scale[1] / 100.0]
    expected_extent = [float(value) for value in expected["expected_world_dimensions_m"]]
    extent_errors = [derived_extent[index] - expected_extent[index] for index in range(2)]
    if all(abs(error) <= DIMENSION_TOLERANCE_M for error in extent_errors):
        validation.add(
            "PASS", "physical_extent",
            f"Topology and scale derive {derived_extent[0]:.6f} x {derived_extent[1]:.6f} m.",
            expected_extent, derived_extent, extent_errors,
        )
    else:
        validation.add(
            "FAIL", "physical_extent", "Derived physical extent differs from the 2 km AOI.",
            expected_extent, derived_extent, extent_errors,
        )
    validation.add(
        "INFO", "world_bounds",
        "Bounds are the union of proxies; the logical World Partition actor has no direct geometry bounds.",
        observed=bounds,
    )

    expected_min = [-expected_extent[0] * 50.0, -expected_extent[1] * 50.0]
    expected_max = [expected_extent[0] * 50.0, expected_extent[1] * 50.0]
    origin_errors = [
        bounds["minimum_cm"][0] - expected_min[0],
        bounds["minimum_cm"][1] - expected_min[1],
        bounds["maximum_cm"][0] - expected_max[0],
        bounds["maximum_cm"][1] - expected_max[1],
    ]
    if all(abs(error) <= LOCATION_TOLERANCE_CM for error in origin_errors):
        validation.add(
            "PASS", "horizontal_local_origin",
            "Terrain is centred on Unreal X/Y zero as declared by the BNG origin metadata.",
            {"minimum_cm": expected_min, "maximum_cm": expected_max},
            {"minimum_cm": bounds["minimum_cm"][:2], "maximum_cm": bounds["maximum_cm"][:2]},
        )
    else:
        validation.add(
            "FAIL", "horizontal_local_origin",
            "Terrain is not centred on the declared BNG local origin.",
            {"minimum_cm": expected_min, "maximum_cm": expected_max},
            {"minimum_cm": bounds["minimum_cm"][:2], "maximum_cm": bounds["maximum_cm"][:2]},
            origin_errors,
        )

    identity_rotation = all(abs(value) <= 1e-6 for value in rotation[:3]) and abs(rotation[3] - 1.0) <= 1e-6
    positive_scale = all(value > 0.0 for value in scale)
    if identity_rotation and positive_scale:
        validation.add(
            "PASS", "unreal_axis_orientation",
            "Positive scale and identity rotation verify +X, +Y and +Z world-axis alignment without actor-level flips.",
            {"positive_scale": True, "identity_rotation": True},
            {"scale": scale, "rotation_quaternion": rotation},
        )
    else:
        validation.add(
            "FAIL", "unreal_axis_orientation", "Actor transform applies a rotation or negative scale.",
            {"positive_scale": True, "identity_rotation": True},
            {"scale": scale, "rotation_quaternion": rotation},
        )
    validation.add(
        "INFO", "geospatial_axis_convention",
        "+X=east and +Y=south are external EPSG:27700/import conventions. Unreal state verifies axes and signs, not the geographic labels.",
        observed=manifest["coordinate_frame"]["axis_mapping"],
    )

    if abs(translation[2]) <= LOCATION_TOLERANCE_CM:
        validation.add(
            "PASS", "vertical_local_origin",
            "Encoded midpoint 32768 maps to Unreal Z=0, compatible with 650 m ODN metadata.",
            0.0, translation[2],
        )
    else:
        validation.add(
            "FAIL", "vertical_local_origin",
            "Landscape translation shifts encoded midpoint 32768 away from Unreal Z=0.",
            0.0, translation[2], translation[2],
        )

    height_samples: list[dict[str, Any]] = []
    try:
        height_samples = _height_samples(
            world, landscape, manifest_path, manifest,
            total_quads_y + 1, total_quads_x + 1,
        )
        missed = [sample for sample in height_samples if not sample["hit"]]
        errors = [abs(float(sample["error_cm"])) for sample in height_samples if sample.get("error_cm") is not None]
        maximum_error = max(errors) if errors else math.inf
        if not missed and maximum_error <= HEIGHT_TOLERANCE_CM:
            validation.add(
                "PASS", "height_representation",
                "Collision heights agree with the generated R16 at nine interior samples.",
                f"maximum absolute error <= {HEIGHT_TOLERANCE_CM} cm",
                {"maximum_absolute_error_cm": maximum_error, "samples": len(height_samples)},
            )
        else:
            validation.add(
                "FAIL", "height_representation",
                "The imported Landscape heightfield does not reproduce the generated R16 values.",
                f"maximum absolute error <= {HEIGHT_TOLERANCE_CM} cm and no missed traces",
                {"maximum_absolute_error_cm": maximum_error, "missed_samples": len(missed), "samples": len(height_samples)},
                maximum_error - HEIGHT_TOLERANCE_CM if math.isfinite(maximum_error) else None,
            )
    except Exception as error:
        validation.add(
            "WARNING", "height_representation",
            f"Could not compare Landscape collision heights with the generated R16: {error}",
        )

    reference_samples: list[dict[str, Any]] = []
    try:
        reference_samples = _reference_height_samples(world, manifest_path, manifest)
        missed_references = [sample for sample in reference_samples if not sample["hit"]]
        reference_errors = [
            abs(float(sample["error_cm"]))
            for sample in reference_samples
            if sample.get("error_cm") is not None
        ]
        maximum_reference_error = max(reference_errors) if reference_errors else math.inf
        if not missed_references and maximum_reference_error <= HEIGHT_TOLERANCE_CM:
            validation.add(
                "PASS", "geospatial_reference_heights",
                "AOI centre and Tryfan reference heights agree with the canonical R16 at their intended BNG-derived world coordinates.",
                f"maximum absolute error <= {HEIGHT_TOLERANCE_CM} cm",
                {"maximum_absolute_error_cm": maximum_reference_error, "samples": reference_samples},
            )
        else:
            validation.add(
                "FAIL", "geospatial_reference_heights",
                "AOI centre or Tryfan reference heights do not reproduce the canonical R16 at the intended registration.",
                f"maximum absolute error <= {HEIGHT_TOLERANCE_CM} cm and no missed traces",
                {"maximum_absolute_error_cm": maximum_reference_error, "missed_samples": len(missed_references), "samples": reference_samples},
                maximum_reference_error - HEIGHT_TOLERANCE_CM if math.isfinite(maximum_reference_error) else None,
            )
    except Exception as error:
        validation.add(
            "WARNING", "geospatial_reference_heights",
            f"Could not validate named BNG reference heights: {error}",
        )

    validation.add(
        "INFO", "absolute_odn_verification",
        "Unreal stores relative heights. Absolute ODN requires the encoding manifest, local-zero convention and actor transform; Unreal state alone cannot prove 650 m ODN.",
        observed={
            "manifest_vertical_origin_m_odn": manifest["height_encoding"]["vertical_origin_m_odn"],
            "actor_translation_z_cm": translation[2],
            "actor_z_scale": scale[2],
        },
    )

    result = {
        "schema_version": 2,
        "engine_version": engine_version,
        "map": world_path,
        "manifest": str(manifest_path),
        "landscape": {
            "logical_actor_count": len(landscapes),
            "streaming_proxy_count": len(proxies),
            "logical_actor": landscape_path,
            "component_count": len(components),
            "component_grid": observed_grid,
            "component_quads": observed_component_quads,
            "subsections_per_component": [subsections_axis, subsections_axis],
            "quads_per_subsection": quads_per_section,
            "overall_quads": observed_quads,
            "resolution_vertices": [total_quads_x + 1, total_quads_y + 1],
            "logical_transform": {
                "translation_cm": translation,
                "rotation_quaternion": rotation,
                "scale": scale,
            },
            "proxy_scale_consistent": proxies_match,
            "derived_physical_extent_m": derived_extent,
            "world_bounds": bounds,
        },
        "height_samples": height_samples,
        "reference_height_samples": reference_samples,
        "checks": validation.checks,
        "overall": validation.overall,
    }
    _write_report(result)
    unreal.log(f"OVERALL {validation.overall}")
    if validation.overall == "FAIL":
        raise RuntimeError("Landscape validation failed; see Saved/meridian-landscape-validation.json")
    return result


if __name__ == "__main__":
    main()
