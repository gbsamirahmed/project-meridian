from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from calibration_model import (
    ActivityObservations,
    MovementObservation,
    activity_folds,
    cross_validate,
    generic_tobler_speed_mps,
)
from models import ActivitySample, NormalizedActivity
from personal_calibration_experiment import _candidate_is_usable
from terrain_experiment import (
    MovementPoint,
    TERRARIUM_ZOOM,
    TerrainVariant,
    TerrariumTileCache,
    accepted_movement_segment_indices,
    build_movement_chains,
    build_terrain_profile,
    resample_movement_chains,
)


def activity_sample(index: int, seconds: int, latitude: float, longitude: float) -> ActivitySample:
    return ActivitySample(
        index,
        datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds),
        latitude,
        longitude,
    )


def synthetic_summary(label: str) -> dict[str, object]:
    return {
        "catalogue_label": label,
        "usable_timestamped_gps": True,
        "descriptive_speed_signature": "predominantly_moderate_progression",
        "movement_duration_s": 3600,
        "movement_distance_m": 5000,
        "movement_speed_median_mps": 1.4,
        "movement_speed_p90_mps": 2.2,
        "state_counts": {"continuous_movement": 1000, "gps_anomaly": 0},
        "state_seconds": {"continuous_movement": 3600, "uncertain": 0},
    }


class MovementEvidenceTests(unittest.TestCase):
    def test_very_slow_coherent_progression_remains_movement(self) -> None:
        activity = NormalizedActivity(Path("synthetic.fit"), ".fit")
        activity.samples = [
            activity_sample(index, index * 30, 51 + index * 0.000045, -3)
            for index in range(8)
        ]
        accepted = accepted_movement_segment_indices(activity)
        self.assertEqual(accepted, set(range(7)))
        points = resample_movement_chains(build_movement_chains(activity))
        self.assertGreater(len(points), 3)
        self.assertAlmostEqual(points[-1].movement_elapsed_s, 210, delta=1)

    def test_low_speed_back_and_forth_jitter_is_not_all_accepted(self) -> None:
        activity = NormalizedActivity(Path("jitter.fit"), ".fit")
        activity.samples = [
            activity_sample(index, index * 10, 51 + (0.00004 if index % 2 else 0), -3)
            for index in range(9)
        ]
        accepted = accepted_movement_segment_indices(activity)
        self.assertLess(len(accepted), 8)

    def test_catalogue_label_does_not_affect_candidate_quality(self) -> None:
        self.assertEqual(
            _candidate_is_usable(synthetic_summary("Run")),
            _candidate_is_usable(synthetic_summary("Hike")),
        )


class TerrainExperimentTests(unittest.TestCase):
    def test_terrarium_numeric_decode_matches_meridian_formula(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = TerrariumTileCache(Path(directory))
            point = MovementPoint(0, 0, 0, 0, 0, 0, 0)
            tile_x, tile_y = next(iter(cache.required_tiles([point])))
            path = cache._path((tile_x, tile_y))
            path.parent.mkdir(parents=True)
            pixels = np.zeros((256, 256, 3), dtype=np.uint8)
            pixels[:, :, :] = (128, 123, 128)
            Image.fromarray(pixels, "RGB").save(path)
            self.assertEqual(TERRARIUM_ZOOM, 15)
            self.assertAlmostEqual(cache.sample([point])[0], 123.5, places=6)

    def test_terrain_profile_reports_smoothing_and_hysteresis_losses(self) -> None:
        points = [
            MovementPoint(0, 51, -3, index * 10, index * 10, index * 10, index * 10)
            for index in range(9)
        ]
        elevations = [100, 101, 100, 105, 106, 105, 110, 109, 112]
        profile = build_terrain_profile(
            points,
            elevations,
            TerrainVariant("synthetic", 10, 1, 2, 20),
        )
        self.assertLessEqual(profile.processed_positive_variation_m, profile.raw_positive_variation_m)
        self.assertLessEqual(profile.ascent_after_hysteresis_m, profile.processed_positive_variation_m)
        self.assertEqual(len(profile.gradients), len(points))


def synthetic_activity(key: str, ratio: float, gradient_offset: float) -> ActivityObservations:
    observations: list[MovementObservation] = []
    elapsed = 0.0
    cumulative_distance = 0.0
    for index in range(120):
        gradient = -0.18 + (index % 12) * 0.03 + gradient_offset
        generic = generic_tobler_speed_mps(gradient)
        distance = 20.0
        duration = distance / (generic * ratio)
        elapsed += duration
        cumulative_distance += distance
        observations.append(
            MovementObservation(
                key,
                gradient,
                distance,
                duration,
                generic * ratio,
                generic,
                (index + 1) / 120,
                cumulative_distance,
                max(0, gradient) * cumulative_distance,
            )
        )
    return ActivityObservations(
        key,
        "synthetic",
        observations,
        elapsed,
        cumulative_distance,
        300,
        False,
    )


class CalibrationTests(unittest.TestCase):
    def test_activity_folds_never_split_an_activity(self) -> None:
        activities = [synthetic_activity(f"a-{index}", 1.2, index * 0.001) for index in range(12)]
        folds = activity_folds(activities)
        flattened = [key for fold in folds for key in fold]
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual(set(flattened), {activity.key for activity in activities})

    def test_personal_curve_improves_known_transparent_scale(self) -> None:
        activities = [synthetic_activity(f"a-{index}", 1.25, (index - 6) * 0.001) for index in range(15)]
        validation = cross_validate(activities)
        self.assertLess(
            validation["personal"]["median_absolute_percentage_error"],
            validation["generic"]["median_absolute_percentage_error"],
        )
        self.assertLess(validation["personal"]["median_absolute_percentage_error"], 15)


if __name__ == "__main__":
    unittest.main()
