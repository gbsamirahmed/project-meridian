from __future__ import annotations

import math
from pathlib import Path
from typing import Any


def validate_opacity(value: float) -> float:
    opacity = float(value)
    if not math.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
        raise ValueError("Overlay opacity must be finite and between 0 and 1")
    return opacity


def aspect_ratio(width: int, height: int) -> float:
    if int(width) <= 0 or int(height) <= 0:
        raise ValueError("Image dimensions must be positive")
    return int(width) / int(height)


def resolve_repo_path(config_path: Path, path_convention: str) -> Path:
    path = Path(path_convention)
    if path.is_absolute():
        return path.resolve()
    repository_root = config_path.resolve().parents[2]
    return (repository_root / path).resolve()


def signed_angle_delta_degrees(observed: float, expected: float) -> float:
    return (float(observed) - float(expected) + 180.0) % 360.0 - 180.0


def camera_mismatches(
    observed: dict[str, Any],
    expected: dict[str, Any],
    *,
    location_tolerance_cm: float = 0.2,
    rotation_tolerance_degrees: float = 0.01,
    fov_tolerance_degrees: float = 0.01,
    aspect_tolerance: float = 1e-5,
) -> list[str]:
    mismatches: list[str] = []
    for axis in ("x", "y", "z"):
        difference = abs(
            float(observed["location_cm"][axis])
            - float(expected["location_cm"][axis])
        )
        if difference > location_tolerance_cm:
            mismatches.append(
                f"camera {axis.upper()} differs by {difference:.6f} cm"
            )
    for field in ("pitch", "yaw", "roll"):
        difference = abs(
            signed_angle_delta_degrees(
                observed["rotation_degrees"][field],
                expected["rotation_degrees"][field],
            )
        )
        if difference > rotation_tolerance_degrees:
            mismatches.append(
                f"camera {field} differs by {difference:.6f} degrees"
            )
    fov_difference = abs(
        float(observed["horizontal_fov_degrees"])
        - float(expected["horizontal_fov_degrees"])
    )
    if fov_difference > fov_tolerance_degrees:
        mismatches.append(f"camera HFOV differs by {fov_difference:.6f} degrees")
    aspect_difference = abs(
        float(observed["aspect_ratio"]) - float(expected["aspect_ratio"])
    )
    if aspect_difference > aspect_tolerance:
        mismatches.append(f"camera aspect ratio differs by {aspect_difference:.9f}")
    if not bool(observed["constrain_aspect_ratio"]):
        mismatches.append("camera does not constrain its 4:3 aspect ratio")
    return mismatches
