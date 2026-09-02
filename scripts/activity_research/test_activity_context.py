from __future__ import annotations

import inspect
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from activity_context import (
    INSERTED_COLUMNS,
    RecordingFeatures,
    TerrainFeatures,
    classify_terrain_profile,
    infer_context,
)
from activity_context_builder import (
    build_activity_context,
    catalogue_layout,
    source_recording_fingerprint,
    validate_output,
)
from terrain_experiment import TERRARIUM_ZOOM, TerrariumTileCache


def recording(**overrides: object) -> RecordingFeatures:
    values: dict[str, object] = {
        "usable_timestamped_gps": True,
        "sample_count": 1000,
        "interpreted_segment_count": 999,
        "movement_segment_count": 900,
        "movement_distance_m": 10_000.0,
        "movement_duration_s": 7200.0,
        "median_speed_mps": 1.4,
        "p10_speed_mps": 0.8,
        "p90_speed_mps": 2.0,
        "walking_duration_fraction": 0.8,
        "running_duration_fraction": 0.05,
        "intermediate_duration_fraction": 0.15,
        "longest_walking_phase_s": 1800.0,
        "longest_running_phase_s": 20.0,
        "walking_running_transition_count": 0,
        "stationary_seconds": 60.0,
        "pause_seconds": 0.0,
        "gap_seconds": 0.0,
        "uncertain_seconds": 0.0,
        "anomalous_segment_fraction": 0.0,
        "cadence_coverage": 0.0,
        "median_cadence_rpm": None,
        "explicit_pause_count": 0,
        "long_stationary_episode_count": 0,
    }
    values.update(overrides)
    return RecordingFeatures(**values)


def terrain(**overrides: object) -> TerrainFeatures:
    values: dict[str, object] = {
        "available": True,
        "distance_m": 10_000.0,
        "ascent_m": 120.0,
        "descent_m": 120.0,
        "elevation_range_m": 90.0,
        "ascent_per_km": 12.0,
        "meaningful_gradient_fraction": 0.2,
        "steep_gradient_fraction": 0.02,
        "sustained_climb_m": 180.0,
        "sustained_descent_m": 180.0,
        "gradient_p10": -0.05,
        "gradient_median": 0.0,
        "gradient_p90": 0.05,
    }
    values.update(overrides)
    return TerrainFeatures(**values)


class ContextInferenceTests(unittest.TestCase):
    def test_inference_boundary_cannot_receive_name_or_description(self) -> None:
        self.assertEqual(
            list(inspect.signature(infer_context).parameters),
            ["activity_type", "recording", "terrain"],
        )

    def test_run_type_is_not_used_as_running_evidence(self) -> None:
        guess = infer_context("Run", recording(), terrain())
        self.assertEqual(guess.mode, "walk")
        self.assertFalse(guess.non_run_type_contributed)

    def test_sustained_running_on_hilly_terrain_is_trail_run(self) -> None:
        guess = infer_context(
            "Run",
            recording(
                median_speed_mps=3.0,
                walking_duration_fraction=0.05,
                running_duration_fraction=0.85,
                intermediate_duration_fraction=0.10,
                longest_running_phase_s=1200.0,
            ),
            terrain(
                ascent_per_km=45.0,
                elevation_range_m=320.0,
                meaningful_gradient_fraction=0.5,
                steep_gradient_fraction=0.2,
                sustained_climb_m=900.0,
            ),
        )
        self.assertEqual(guess.mode, "trail_run")

    def test_distinct_sustained_phases_are_mixed(self) -> None:
        guess = infer_context(
            "Run",
            recording(
                walking_duration_fraction=0.45,
                running_duration_fraction=0.40,
                intermediate_duration_fraction=0.15,
                longest_walking_phase_s=600.0,
                longest_running_phase_s=500.0,
            ),
            terrain(),
        )
        self.assertEqual(guess.mode, "mixed")

    def test_non_run_type_is_only_a_broad_prior(self) -> None:
        cycle = infer_context("Ride", recording(median_speed_mps=6.0), terrain())
        self.assertEqual(cycle.mode, "cycle")
        self.assertTrue(cycle.non_run_type_contributed)
        self.assertEqual(cycle.representative, "no")

    def test_surface_party_load_and_conditions_remain_unknown(self) -> None:
        guess = infer_context("Run", recording(), terrain())
        self.assertEqual(
            (guess.terrain_surface, guess.party, guess.load, guess.conditions),
            ("unknown", "unknown", "unknown", "unknown"),
        )

    def test_terrain_profile_requires_combined_evidence(self) -> None:
        self.assertEqual(classify_terrain_profile(terrain(ascent_per_km=3, elevation_range_m=20, meaningful_gradient_fraction=0.03)), "flat")
        self.assertEqual(classify_terrain_profile(terrain()), "rolling")
        self.assertEqual(classify_terrain_profile(terrain(ascent_per_km=40, elevation_range_m=240)), "hilly")
        self.assertEqual(
            classify_terrain_profile(
                terrain(
                    ascent_per_km=45,
                    elevation_range_m=650,
                    steep_gradient_fraction=0.2,
                    sustained_climb_m=1000,
                )
            ),
            "mountainous",
        )


class CatalogueTests(unittest.TestCase):
    def test_duplicate_original_headers_and_values_are_preserved(self) -> None:
        header = ["Activity Name", "Activity Type", "Activity Description", "Elapsed Time", "Elapsed Time", "Filename"]
        original = [["Synthetic label", "Run", "Synthetic description", "10", "9", "activities/example.gpx"]]
        layout = catalogue_layout(header)
        guess = infer_context("Run", recording(), terrain())
        inserted = [
            guess.codex_values()[column] if column.startswith("codex_") else ""
            for column in INSERTED_COLUMNS
        ]
        output_header = header[: layout.insertion_index] + list(INSERTED_COLUMNS) + header[layout.insertion_index :]
        output_rows = [original[0][: layout.insertion_index] + inserted + original[0][layout.insertion_index :]]
        validate_output(header, original, output_header, output_rows, layout)
        self.assertTrue(all(output_rows[0][layout.insertion_index + index] == "" for index, column in enumerate(INSERTED_COLUMNS) if column.startswith("human_")))

    def test_recording_fingerprint_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "synthetic.fit"
            path.write_bytes(b"first")
            before = source_recording_fingerprint(root)
            path.write_bytes(b"second")
            after = source_recording_fingerprint(root)
            self.assertNotEqual(before["content_sha256"], after["content_sha256"])

    def test_terrain_cache_reads_fallback_without_copying_or_downloading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = root / "primary"
            fallback = root / "fallback"
            tile = (16_384, 16_384)
            fallback_path = fallback / str(TERRARIUM_ZOOM) / str(tile[0]) / f"{tile[1]}.png"
            fallback_path.parent.mkdir(parents=True)
            Image.fromarray(np.full((256, 256, 3), (128, 0, 0), dtype=np.uint8), "RGB").save(fallback_path)
            cache = TerrariumTileCache(primary, fallback_roots=[fallback])
            cache.prepare_tiles([tile], concurrency=1)
            self.assertEqual(cache.fallback_cache_hits, 1)
            self.assertEqual(cache.downloaded_tiles, 0)
            self.assertFalse(cache._path(tile).exists())

    def test_private_paths_inside_repository_are_rejected_before_io(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory).resolve()
            with self.assertRaisesRegex(ValueError, "outside the Git repository"):
                build_activity_context(
                    repo / "private-export",
                    repo / "private-research",
                    repo,
                    repo / "private-cache",
                )


if __name__ == "__main__":
    unittest.main()
