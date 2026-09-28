"""Pure coordinate helpers for Meridian Earth observer placement."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LookAtOrientation:
    horizontal_distance_cm: float
    distance_3d_cm: float
    geographic_bearing_degrees: float
    unreal_yaw_degrees: float
    unreal_pitch_degrees: float


def _finite(name: str, value: float) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def bng_to_unreal_xy_cm(
    easting: float,
    northing: float,
    origin_easting: float,
    origin_northing: float,
) -> tuple[float, float]:
    """Map BNG metres to Unreal centimetres for +X east and +Y south."""
    easting = _finite("easting", easting)
    northing = _finite("northing", northing)
    origin_easting = _finite("origin_easting", origin_easting)
    origin_northing = _finite("origin_northing", origin_northing)
    return (
        (easting - origin_easting) * 100.0,
        (origin_northing - northing) * 100.0,
    )


def true_heading_to_local_grid_bearing_degrees(
    true_heading_degrees: float,
    reference_true_heading_degrees: float,
    reference_grid_bearing_degrees: float,
) -> float:
    """Apply the local projected-grid convergence to a true geographic heading."""
    true_heading = _finite("true_heading_degrees", true_heading_degrees) % 360.0
    reference_true = (
        _finite("reference_true_heading_degrees", reference_true_heading_degrees)
        % 360.0
    )
    reference_grid = (
        _finite("reference_grid_bearing_degrees", reference_grid_bearing_degrees)
        % 360.0
    )
    convergence = (
        reference_grid - reference_true + 180.0
    ) % 360.0 - 180.0
    return (true_heading + convergence) % 360.0


def geographic_heading_to_unreal_yaw_degrees(heading_degrees: float) -> float:
    """Convert clockwise-from-north heading to UE yaw (+X forward, +Y right)."""
    heading = _finite("heading_degrees", heading_degrees) % 360.0
    return (heading - 90.0 + 180.0) % 360.0 - 180.0


def look_at_orientation(
    observer_xyz_cm: tuple[float, float, float],
    target_xyz_cm: tuple[float, float, float],
) -> LookAtOrientation:
    """Derive bearing and UE yaw/pitch from optical and target world points."""
    if len(observer_xyz_cm) != 3 or len(target_xyz_cm) != 3:
        raise ValueError("observer_xyz_cm and target_xyz_cm must each contain three values")
    observer = tuple(
        _finite(f"observer_xyz_cm[{index}]", value)
        for index, value in enumerate(observer_xyz_cm)
    )
    target = tuple(
        _finite(f"target_xyz_cm[{index}]", value)
        for index, value in enumerate(target_xyz_cm)
    )
    delta_x = target[0] - observer[0]
    delta_y = target[1] - observer[1]
    delta_z = target[2] - observer[2]
    horizontal = math.hypot(delta_x, delta_y)
    distance_3d = math.hypot(horizontal, delta_z)
    if horizontal <= 1e-9:
        raise ValueError("observer and target must have distinct horizontal coordinates")
    bearing = math.degrees(math.atan2(delta_x, -delta_y)) % 360.0
    yaw = (math.degrees(math.atan2(delta_y, delta_x)) + 180.0) % 360.0 - 180.0
    pitch = math.degrees(math.atan2(delta_z, horizontal))
    return LookAtOrientation(horizontal, distance_3d, bearing, yaw, pitch)


def vertical_fov_degrees(horizontal_fov_degrees: float, aspect_ratio: float) -> float:
    """Return vertical FOV implied by a horizontal FOV and width/height ratio."""
    horizontal = _finite("horizontal_fov_degrees", horizontal_fov_degrees)
    aspect = _finite("aspect_ratio", aspect_ratio)
    if not 0.0 < horizontal < 180.0:
        raise ValueError("horizontal_fov_degrees must be between 0 and 180")
    if aspect <= 0.0:
        raise ValueError("aspect_ratio must be positive")
    radians = 2.0 * math.atan(math.tan(math.radians(horizontal) / 2.0) / aspect)
    return math.degrees(radians)
