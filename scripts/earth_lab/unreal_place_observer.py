"""Place or update a geospatial observer on an existing Unreal Landscape.

Executing this file with no arguments loads the prepared project benchmark and places
the observer against its traced terrain target. For heading-only placement, call
``place_observer(easting, northing, heading_degrees)`` from Unreal Python.

The Landscape is only queried through collision. The script never sculpts,
resamples, reimports, moves, or otherwise edits terrain.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import unreal


def _resolve_script_directory() -> Path:
    """Locate deployed sibling modules for both file and Unreal-console execution."""
    file_value = globals().get("__file__")
    if file_value:
        return Path(file_value).resolve().parent

    # Unreal's documented exec(open(...).read()) pattern does not populate
    # __file__. Prepared Earth Lab projects always deploy this script and its
    # sibling modules together beneath the project's Content/Python directory.
    project_python = (
        Path(unreal.Paths.project_dir()).resolve() / "Content" / "Python"
    )
    if not (project_python / "observer_geometry.py").is_file():
        raise RuntimeError(
            "Cannot locate observer_geometry.py: __file__ is unavailable and "
            f"the prepared-project module is missing at {project_python}"
        )
    return project_python


SCRIPT_DIRECTORY = _resolve_script_directory()
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

from observer_geometry import (  # noqa: E402
    bng_to_unreal_xy_cm,
    geographic_heading_to_unreal_yaw_degrees,
    look_at_orientation,
    true_heading_to_local_grid_bearing_degrees,
    vertical_fov_degrees,
)

BENCHMARK_EASTING = 266100.0
BENCHMARK_NORTHING = 360200.0
BENCHMARK_TARGET_EASTING = 266405.0
BENCHMARK_TARGET_NORTHING = 359387.0
DEFAULT_EYE_HEIGHT_M = 1.70
DEFAULT_HORIZONTAL_FOV_DEGREES = 60.0
DEFAULT_ASPECT_RATIO = 16.0 / 9.0
CAMERA_LABEL = "Meridian_Lab004_Geometric_Camera"
MARKER_LABEL = "Meridian_Lab004_Geometric_Ground_Marker"
MARKER_RADIUS_CM = 10.0
TRACE_HALF_HEIGHT_CM = 1_000_000.0
OPTICAL_POSITION_TOLERANCE_CM = 0.1
FORWARD_VECTOR_TOLERANCE = 1e-6


def _validated_camera_pitch(value: float | None) -> float | None:
    """Validate an explicit photographic pitch calibration in Unreal degrees."""
    if value is None:
        return None
    pitch = float(value)
    if not math.isfinite(pitch) or not -90.0 < pitch < 90.0:
        raise ValueError(
            "MERIDIAN_CAMERA_PITCH_DEGREES must be finite and strictly between -90 and 90"
        )
    return pitch


def _coordinate_frame() -> dict[str, float]:
    source_path = Path(unreal.Paths.project_dir()) / "meridian-landscape-source.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    manifest_path = Path(source["manifest"]).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    origin = manifest["coordinate_frame"]["local_origin_bng"]
    return {
        "easting": float(origin["easting"]),
        "northing": float(origin["northing"]),
        "elevation_m_odn": float(origin["elevation_m_odn"]),
        "manifest": str(manifest_path),
    }


def _one_actor_with_label(
    actors: list[unreal.Actor], label: str, expected_class: type
) -> unreal.Actor | None:
    matches = [actor for actor in actors if actor.get_actor_label() == label]
    if len(matches) > 1:
        raise RuntimeError(f"Expected at most one actor labelled {label!r}; found {len(matches)}")
    if matches and not isinstance(matches[0], expected_class):
        raise RuntimeError(
            f"Actor labelled {label!r} is {matches[0].get_class().get_name()}, "
            f"not {expected_class.__name__}"
        )
    return matches[0] if matches else None


def _logical_landscape_for_hit(actor: unreal.Actor | None) -> unreal.Actor | None:
    if actor is None:
        return None
    if isinstance(actor, unreal.LandscapeStreamingProxy):
        return actor.get_landscape_actor()
    if isinstance(actor, unreal.Landscape):
        return actor
    return None


def _trace_landscape(
    world: unreal.World,
    x_cm: float,
    y_cm: float,
    actors_to_ignore: list[unreal.Actor],
    coordinate_name: str,
) -> tuple[float, unreal.Actor, unreal.Actor]:
    hits = unreal.SystemLibrary.line_trace_multi(
        world,
        unreal.Vector(x_cm, y_cm, TRACE_HALF_HEIGHT_CM),
        unreal.Vector(x_cm, y_cm, -TRACE_HALF_HEIGHT_CM),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        True,
        actors_to_ignore,
        unreal.DrawDebugTrace.NONE,
        True,
    )
    encountered: list[str] = []
    for hit in hits or []:
        values = hit.to_dict()
        hit_actor = values.get("hit_actor")
        if hit_actor is not None:
            encountered.append(hit_actor.get_path_name())
        landscape = _logical_landscape_for_hit(hit_actor)
        if values.get("blocking_hit") and landscape is not None:
            impact = values["impact_point"]
            return float(impact.z), hit_actor, landscape
    raise RuntimeError(
        f"Observer placement refused: {coordinate_name} vertical trace found no "
        f"Landscape at Unreal X={x_cm:.3f}, Y={y_cm:.3f} cm "
        f"(encountered={encountered or ['none']})"
    )


def _set_actor_pose(
    actor: unreal.Actor, location: unreal.Vector, rotation: unreal.Rotator
) -> None:
    if not actor.set_actor_location(location, False, True):
        raise RuntimeError(f"Could not move {actor.get_actor_label()} to {location}")
    if not actor.set_actor_rotation(rotation, True):
        raise RuntimeError(f"Could not rotate {actor.get_actor_label()} to {rotation}")


def place_observer(
    easting: float,
    northing: float,
    heading_degrees: float | None = None,
    *,
    target_easting: float | None = None,
    target_northing: float | None = None,
    eye_height_m: float = DEFAULT_EYE_HEIGHT_M,
    horizontal_fov_degrees: float = DEFAULT_HORIZONTAL_FOV_DEGREES,
    aspect_ratio: float = DEFAULT_ASPECT_RATIO,
    target_pitch_only: bool = False,
    heading_bng_grid_degrees: float | None = None,
    camera_pitch_degrees: float | None = None,
) -> dict[str, Any]:
    """Create/reposition an observer using heading, target, or heading-plus-target pitch."""
    target_requested = target_easting is not None or target_northing is not None
    if target_requested and (target_easting is None or target_northing is None):
        raise ValueError("target_easting and target_northing must be supplied together")
    if not target_requested and heading_degrees is None:
        raise ValueError("Supply heading_degrees or a target BNG easting/northing")
    if target_pitch_only and (
        not target_requested
        or heading_degrees is None
        or heading_bng_grid_degrees is None
    ):
        raise ValueError(
            "target_pitch_only requires target coordinates, published heading, "
            "and its BNG grid bearing"
        )

    eye_height_m = float(eye_height_m)
    horizontal_fov_degrees = float(horizontal_fov_degrees)
    aspect_ratio = float(aspect_ratio)
    camera_pitch_degrees = _validated_camera_pitch(camera_pitch_degrees)
    if not math.isfinite(eye_height_m) or eye_height_m <= 0.0:
        raise ValueError("eye_height_m must be positive and finite")

    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = editor.get_editor_world()
    if world is None:
        raise RuntimeError("No Unreal editor world is open")

    frame = _coordinate_frame()
    x_cm, y_cm = bng_to_unreal_xy_cm(
        easting, northing, frame["easting"], frame["northing"]
    )
    vertical_fov = vertical_fov_degrees(horizontal_fov_degrees, aspect_ratio)

    actors = list(actor_subsystem.get_all_level_actors())
    camera = _one_actor_with_label(actors, CAMERA_LABEL, unreal.CameraActor)
    marker = _one_actor_with_label(actors, MARKER_LABEL, unreal.StaticMeshActor)
    ignored = [
        actor for actor in actors
        if _logical_landscape_for_hit(actor) is None
    ]
    terrain_z_cm, hit_actor, landscape = _trace_landscape(
        world, x_cm, y_cm, ignored, "observer"
    )

    eye_z_cm = terrain_z_cm + eye_height_m * 100.0
    camera_location_xyz = (x_cm, y_cm, eye_z_cm)
    target_report: dict[str, Any] | None = None
    target_hit_actor: unreal.Actor | None = None
    target_landscape: unreal.Actor | None = None
    summit_reference_pitch_degrees: float | None = None
    pitch_source: str

    if target_requested:
        assert target_easting is not None and target_northing is not None
        target_x_cm, target_y_cm = bng_to_unreal_xy_cm(
            target_easting,
            target_northing,
            frame["easting"],
            frame["northing"],
        )
        target_z_cm, target_hit_actor, target_landscape = _trace_landscape(
            world, target_x_cm, target_y_cm, ignored, "target"
        )
        if target_landscape.get_path_name() != landscape.get_path_name():
            raise RuntimeError(
                "Observer and target traces resolved to different logical Landscapes"
            )
        orientation = look_at_orientation(
            camera_location_xyz, (target_x_cm, target_y_cm, target_z_cm)
        )
        # Unreal derives the pitch convention from the traced target. Exact-target
        # mode also uses its yaw. Hybrid photographic mode replaces only yaw with
        # the projection-aware published heading while retaining the traced pitch.
        target_rotation = unreal.MathLibrary.find_look_at_rotation(
            unreal.Vector(*camera_location_xyz),
            unreal.Vector(target_x_cm, target_y_cm, target_z_cm),
        )
        horizontal_distance_cm = orientation.horizontal_distance_cm
        distance_3d_cm = orientation.distance_3d_cm
        summit_reference_pitch_degrees = float(target_rotation.pitch)
        if target_pitch_only:
            assert heading_degrees is not None
            assert heading_bng_grid_degrees is not None
            geographic_bearing = float(heading_degrees) % 360.0
            yaw_degrees = geographic_heading_to_unreal_yaw_degrees(
                heading_bng_grid_degrees
            )
            if camera_pitch_degrees is None:
                pitch_degrees = summit_reference_pitch_degrees
                orientation_mode = "published_heading_terrain_pitch"
                pitch_source = "TRACED_SUMMIT_GEOMETRIC_REFERENCE"
            else:
                pitch_degrees = camera_pitch_degrees
                orientation_mode = "published_heading_calibrated_pitch"
                pitch_source = "EXPLICIT_PHOTOGRAPHIC_CALIBRATION"
            camera_rotation = unreal.Rotator(
                pitch=pitch_degrees, yaw=yaw_degrees, roll=0.0
            )
            target_role = "diagnostic_vertical_pitch_reference_only"
        else:
            camera_rotation = target_rotation
            yaw_degrees = float(camera_rotation.yaw)
            pitch_degrees = float(camera_rotation.pitch)
            geographic_bearing = orientation.geographic_bearing_degrees
            orientation_mode = "target_bng"
            pitch_source = "TRACED_TARGET_LOOK_AT"
            target_role = "horizontal_and_vertical_look_at"
        target_report = {
            "bng": [float(target_easting), float(target_northing)],
            "terrain_world_location_cm": [target_x_cm, target_y_cm, target_z_cm],
            "terrain_elevation_m_odn": frame["elevation_m_odn"] + target_z_cm / 100.0,
            "orientation_role": target_role,
            "coordinate_derived_bng_grid_bearing_degrees": (
                orientation.geographic_bearing_degrees
            ),
            "summit_derived_reference_pitch_degrees": (
                summit_reference_pitch_degrees
            ),
        }
    else:
        assert heading_degrees is not None
        geographic_bearing = float(heading_degrees) % 360.0
        yaw_degrees = geographic_heading_to_unreal_yaw_degrees(heading_degrees)
        pitch_degrees = 0.0
        horizontal_distance_cm = None
        distance_3d_cm = None
        orientation_mode = "heading_only"
        pitch_source = "FIXED_ZERO_HEADING_ONLY"
        camera_rotation = unreal.Rotator(
            pitch=pitch_degrees, yaw=yaw_degrees, roll=0.0
        )

    camera_location = unreal.Vector(*camera_location_xyz)

    with unreal.ScopedEditorTransaction("Place Meridian Earth observer"):
        if camera is None:
            camera = actor_subsystem.spawn_actor_from_class(
                unreal.CameraActor, camera_location, camera_rotation
            )
            if camera is None:
                raise RuntimeError("Unreal failed to create the observer CameraActor")
            camera.set_actor_label(CAMERA_LABEL, True)
        _set_actor_pose(camera, camera_location, camera_rotation)
        camera.set_actor_enable_collision(False)
        camera_component = camera.camera_component
        camera_component.set_field_of_view(horizontal_fov_degrees)
        camera_component.set_aspect_ratio(aspect_ratio)
        camera_component.set_constraint_aspect_ratio(True)

        marker_location = unreal.Vector(x_cm, y_cm, terrain_z_cm + MARKER_RADIUS_CM)
        if marker is None:
            marker = actor_subsystem.spawn_actor_from_class(
                unreal.StaticMeshActor, marker_location, unreal.Rotator()
            )
            if marker is None:
                raise RuntimeError("Unreal failed to create the observer ground marker")
            marker.set_actor_label(MARKER_LABEL, True)
        sphere = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
        if sphere is None:
            raise RuntimeError("Engine sphere mesh required for the observer marker is unavailable")
        marker.static_mesh_component.set_static_mesh(sphere)
        marker.set_actor_scale3d(unreal.Vector(0.2, 0.2, 0.2))
        marker.set_actor_enable_collision(False)
        _set_actor_pose(marker, marker_location, unreal.Rotator())

    optical_location = camera.camera_component.get_world_location()
    optical_error_cm = math.dist(
        (float(optical_location.x), float(optical_location.y), float(optical_location.z)),
        camera_location_xyz,
    )
    if optical_error_cm > OPTICAL_POSITION_TOLERANCE_CM:
        raise RuntimeError(
            f"Camera optical position differs from the requested eye point by {optical_error_cm:.3f} cm"
        )

    actor_forward = camera.get_actor_forward_vector()
    actor_forward_values = (
        float(actor_forward.x),
        float(actor_forward.y),
        float(actor_forward.z),
    )
    component_forward = camera_component.get_forward_vector()
    component_forward_values = (
        float(component_forward.x),
        float(component_forward.y),
        float(component_forward.z),
    )
    camera_view = camera_component.get_camera_view(0.0)
    view_forward = unreal.MathLibrary.get_forward_vector(camera_view.rotation)
    view_forward_values = (
        float(view_forward.x),
        float(view_forward.y),
        float(view_forward.z),
    )
    forward_alignment_error = None
    view_forward_alignment_error = None
    forward_alignment_reference = None
    if target_report is not None:
        if orientation_mode in {
            "published_heading_terrain_pitch",
            "published_heading_calibrated_pitch",
        }:
            expected = unreal.MathLibrary.get_forward_vector(camera_rotation)
            expected_forward = (
                float(expected.x),
                float(expected.y),
                float(expected.z),
            )
            forward_alignment_reference = "published_heading_and_traced_pitch"
        else:
            target_world = target_report["terrain_world_location_cm"]
            optical_xyz = (
                float(optical_location.x),
                float(optical_location.y),
                float(optical_location.z),
            )
            delta = tuple(target_world[index] - optical_xyz[index] for index in range(3))
            delta_length = math.sqrt(sum(value * value for value in delta))
            expected_forward = tuple(value / delta_length for value in delta)
            forward_alignment_reference = "traced_target"
        forward_alignment_error = math.dist(
            component_forward_values, expected_forward
        )
        view_forward_alignment_error = math.dist(
            view_forward_values, expected_forward
        )
        if (
            forward_alignment_error > FORWARD_VECTOR_TOLERANCE
            or view_forward_alignment_error > FORWARD_VECTOR_TOLERANCE
        ):
            raise RuntimeError(
                "Rendered CameraComponent does not match the requested orientation: "
                f"component forward-vector error {forward_alignment_error:.9f}, "
                f"camera-view forward-vector error {view_forward_alignment_error:.9f}"
            )

    report = {
        "schema_version": 2,
        "map": world.get_path_name(),
        "coordinate_frame": {
            "origin_bng": [frame["easting"], frame["northing"], frame["elevation_m_odn"]],
            "axis_mapping": {"+X": "east", "+Y": "south", "+Z": "up"},
            "units": "centimetres",
            "manifest": frame["manifest"],
        },
        "observer": {
            "bng": [float(easting), float(northing)],
            "eye_height_m": eye_height_m,
            "terrain_world_location_cm": [x_cm, y_cm, terrain_z_cm],
            "terrain_elevation_m_odn": frame["elevation_m_odn"] + terrain_z_cm / 100.0,
            "camera_optical_location_cm": [
                float(optical_location.x), float(optical_location.y), float(optical_location.z)
            ],
        },
        "target": target_report,
        "orientation": {
            "mode": orientation_mode,
            "geographic_bearing_degrees": geographic_bearing,
            "unreal_yaw_degrees": yaw_degrees,
            "unreal_pitch_degrees": pitch_degrees,
            "unreal_roll_degrees": 0.0,
            "pitch_source": pitch_source,
            "summit_derived_reference_pitch_degrees": (
                summit_reference_pitch_degrees
            ),
            "horizontal_distance_m": (
                horizontal_distance_cm / 100.0 if horizontal_distance_cm is not None else None
            ),
            "distance_3d_m": distance_3d_cm / 100.0 if distance_3d_cm is not None else None,
            "actor_forward_vector": list(actor_forward_values),
            "camera_component_forward_vector": list(component_forward_values),
            "camera_view_forward_vector": list(view_forward_values),
            "forward_alignment_reference": forward_alignment_reference,
            "forward_alignment_error": forward_alignment_error,
            "camera_view_forward_alignment_error": view_forward_alignment_error,
            "camera_component_world_rotation": {
                "pitch": float(camera_component.get_world_rotation().pitch),
                "yaw": float(camera_component.get_world_rotation().yaw),
                "roll": float(camera_component.get_world_rotation().roll),
            },
            "camera_view_rotation": {
                "pitch": float(camera_view.rotation.pitch),
                "yaw": float(camera_view.rotation.yaw),
                "roll": float(camera_view.rotation.roll),
            },
        },
        "camera": {
            "horizontal_fov_degrees": horizontal_fov_degrees,
            "aspect_ratio": aspect_ratio,
            "implied_vertical_fov_degrees": vertical_fov,
        },
        "terrain_trace": {
            "observer_hit_actor": hit_actor.get_path_name(),
            "observer_logical_landscape": landscape.get_path_name(),
            "target_hit_actor": target_hit_actor.get_path_name() if target_hit_actor else None,
            "target_logical_landscape": (
                target_landscape.get_path_name() if target_landscape else None
            ),
        },
        "actors": {
            "camera": camera.get_path_name(),
            "marker": marker.get_path_name(),
            "marker_centre_cm": [x_cm, y_cm, terrain_z_cm + MARKER_RADIUS_CM],
            "marker_radius_cm": MARKER_RADIUS_CM,
        },
        "saved_automatically": False,
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / "meridian-observer-placement.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(
        "Meridian observer placed: "
        f"BNG E{float(easting):.3f} N{float(northing):.3f}, "
        f"terrain Z={terrain_z_cm:.3f} cm, eye Z={eye_z_cm:.3f} cm, "
        f"bearing={geographic_bearing:.3f}°, UE yaw={yaw_degrees:.3f}°, "
        f"UE pitch={pitch_degrees:.3f}°"
    )
    unreal.log(f"Observer placement report: {report_path}")
    return report



def _resolve_benchmark_fov(
    calibration: dict[str, Any],
    override_degrees: float | None,
) -> tuple[float, str]:
    """Select an explicit placement FOV without presenting it as measured."""
    if override_degrees is not None:
        return float(override_degrees), "CALL_OVERRIDE"
    measured = calibration.get("horizontal_fov_degrees")
    if measured is not None:
        return float(measured), "METADATA_MEASURED_OR_DERIVED"
    calibrated = calibration.get("calibrated_horizontal_fov_degrees")
    if calibrated is not None:
        return float(calibrated), "METADATA_EXPLICIT_CALIBRATION_OVERRIDE"
    initial = calibration.get("initial_calibration_horizontal_fov_degrees")
    if initial is None:
        raise ValueError(
            "Benchmark FOV is unknown and no initial calibration is configured; "
            "supply horizontal_fov_degrees explicitly"
        )
    return float(initial), "METADATA_INITIAL_CALIBRATION_PARAMETER"


def place_benchmark(
    benchmark_path: str | Path,
    *,
    horizontal_fov_degrees: float | None = None,
    camera_pitch_degrees: float | None = None,
    camera_heading_degrees: float | None = None,
) -> dict[str, Any]:
    """Place a camera from machine-readable Earth Lab benchmark metadata."""
    path = Path(benchmark_path).resolve()
    benchmark = json.loads(path.read_text(encoding="utf-8"))
    observer = benchmark["observer"]
    observer_bng = observer["bng"]
    view = benchmark["view"]
    calibration = benchmark["camera_calibration"]
    placement_fov, placement_fov_source = _resolve_benchmark_fov(
        calibration, horizontal_fov_degrees
    )
    published_heading = float(view["published_heading_degrees"])
    published_grid_bearing = float(
        view["published_heading_bng_grid_bearing_degrees"]
    )
    if camera_heading_degrees is None:
        placement_heading = published_heading
        placement_heading_source = "PUBLISHED_SOURCE_METADATA"
    else:
        placement_heading = float(camera_heading_degrees)
        if not math.isfinite(placement_heading):
            raise ValueError("MERIDIAN_CAMERA_HEADING_DEGREES must be finite")
        placement_heading %= 360.0
        placement_heading_source = "EXPLICIT_PHOTOGRAPHIC_CALIBRATION"
    placement_grid_bearing = true_heading_to_local_grid_bearing_degrees(
        placement_heading,
        published_heading,
        published_grid_bearing,
    )
    target = view.get("target")
    view_mode = view.get("mode")
    if view_mode in {
        "published_heading_terrain_pitch",
        "published_heading_calibrated_pitch",
    }:
        pitch_reference = view.get("pitch_reference")
        if not pitch_reference:
            raise ValueError(
                f"{view_mode} requires a pitch_reference"
            )
        if (
            view_mode == "published_heading_calibrated_pitch"
            and camera_pitch_degrees is None
        ):
            raise ValueError(
                "Lab 004A photographic calibration requires "
                "MERIDIAN_CAMERA_PITCH_DEGREES"
            )
        pitch_bng = pitch_reference["bng"]
        report = place_observer(
            float(observer_bng["easting"]),
            float(observer_bng["northing"]),
            heading_degrees=placement_heading,
            target_easting=float(pitch_bng["easting"]),
            target_northing=float(pitch_bng["northing"]),
            eye_height_m=float(observer["eye_height_m"]),
            horizontal_fov_degrees=placement_fov,
            aspect_ratio=float(calibration["aspect_ratio"]),
            target_pitch_only=True,
            heading_bng_grid_degrees=placement_grid_bearing,
            camera_pitch_degrees=camera_pitch_degrees,
        )
    elif view.get("mode") == "terrain_target":
        if not target:
            raise ValueError("terrain_target benchmark requires a target")
        target_bng = target["bng"]
        report = place_observer(
            float(observer_bng["easting"]),
            float(observer_bng["northing"]),
            target_easting=float(target_bng["easting"]),
            target_northing=float(target_bng["northing"]),
            eye_height_m=float(observer["eye_height_m"]),
            horizontal_fov_degrees=placement_fov,
            aspect_ratio=float(calibration["aspect_ratio"]),
        )
    elif view.get("mode") == "heading":
        report = place_observer(
            float(observer_bng["easting"]),
            float(observer_bng["northing"]),
            heading_degrees=float(view["heading_degrees"]),
            eye_height_m=float(observer["eye_height_m"]),
            horizontal_fov_degrees=placement_fov,
            aspect_ratio=float(calibration["aspect_ratio"]),
        )
    else:
        raise ValueError(f"Unsupported benchmark view mode: {view.get('mode')!r}")
    report["benchmark"] = {
        "path": str(path),
        "benchmark_id": benchmark["benchmark_id"],
        "fov_provenance": calibration["provenance"],
        "fov_calibration_status": calibration["calibration_status"],
        "placement_horizontal_fov_degrees": placement_fov,
        "placement_fov_source": placement_fov_source,
        "placement_pitch_degrees": report["orientation"]["unreal_pitch_degrees"],
        "placement_pitch_source": report["orientation"]["pitch_source"],
        "published_heading_degrees": published_heading,
        "placement_true_heading_degrees": placement_heading,
        "placement_heading_source": placement_heading_source,
        "placement_bng_grid_bearing_degrees": placement_grid_bearing,
        "placement_unreal_yaw_degrees": report["orientation"]["unreal_yaw_degrees"],
        "summit_derived_reference_pitch_degrees": (
            report["orientation"]["summit_derived_reference_pitch_degrees"]
        ),
        "photographic_parameter_status": (
            "HEADING_PITCH_AND_HORIZONTAL_FOV_MAY_BE_RECOVERED_PHOTOGRAPHIC_"
            "CALIBRATIONS_NOT_MEASURED_IMAGE_METADATA"
        ),
        "depicted_place_diagnostic": target,
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / "meridian-observer-placement.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if view_mode == "published_heading_calibrated_pitch":
        unreal.log("=== Meridian Lab 004A photographic calibration ===")
        unreal.log(
            f"Fixed camera BNG: E{float(observer_bng['easting']):.3f} "
            f"N{float(observer_bng['northing']):.3f}"
        )
        unreal.log(
            "Traced terrain elevation: "
            f"{report['observer']['terrain_elevation_m_odn']:.3f} m ODN; "
            f"eye height: {float(observer['eye_height_m']):.2f} m"
        )
        unreal.log(
            f"Published source heading: {published_heading:.3f} deg true "
            "(preserved as metadata)"
        )
        unreal.log(
            f"Applied camera heading: {placement_heading:.3f} deg true "
            f"({placement_heading_source}); local grid bearing: "
            f"{placement_grid_bearing:.6f} deg; converted Unreal yaw: "
            f"{report['orientation']['unreal_yaw_degrees']:.6f} deg"
        )
        unreal.log(
            f"Calibrated pitch: {report['orientation']['unreal_pitch_degrees']:.3f} deg; "
            f"calibrated horizontal FOV: {placement_fov:.3f} deg"
        )
        unreal.log(
            "Summit-derived geometric reference pitch: "
            f"{report['orientation']['summit_derived_reference_pitch_degrees']:.3f} deg"
        )
        unreal.log(
            "Heading override, pitch and horizontal FOV are recovered/calibrated "
            "photographic parameters; they are not measured image metadata."
        )
    return report


def main() -> dict[str, Any]:
    benchmark_pointer = Path(unreal.Paths.project_dir()) / "meridian-benchmark-source.json"
    if benchmark_pointer.is_file():
        pointer = json.loads(benchmark_pointer.read_text(encoding="utf-8"))
        return place_benchmark(
            pointer["benchmark"],
            horizontal_fov_degrees=globals().get(
                "MERIDIAN_HORIZONTAL_FOV_DEGREES"
            ),
            camera_pitch_degrees=globals().get(
                "MERIDIAN_CAMERA_PITCH_DEGREES"
            ),
            camera_heading_degrees=globals().get(
                "MERIDIAN_CAMERA_HEADING_DEGREES"
            ),
        )
    return place_observer(
        BENCHMARK_EASTING,
        BENCHMARK_NORTHING,
        target_easting=BENCHMARK_TARGET_EASTING,
        target_northing=BENCHMARK_TARGET_NORTHING,
        eye_height_m=DEFAULT_EYE_HEIGHT_M,
        horizontal_fov_degrees=DEFAULT_HORIZONTAL_FOV_DEGREES,
    )


if __name__ == "__main__":
    main()
