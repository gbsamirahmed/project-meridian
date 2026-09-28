from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np

from surface_reconstruction import (
    VISUAL_CLASSES,
    coherent_field,
    neighbor_correlation,
    reconstruct_controls,
    reconstruction_freedom,
    sha256_file,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "docs" / "earth-lab" / "tryfan-009-surface-reconstruction.json"


def synthetic_inputs(shape: tuple[int, int] = (96, 96)):
    probabilities = np.full((*shape, 6), 1.0 / 6.0, dtype=np.float32)
    readiness = np.full(shape, 2, dtype=np.uint8)
    slope = np.full(shape, 20.0, dtype=np.float32)
    roughness = np.full(shape, 0.35, dtype=np.float32)
    curvature = np.zeros(shape, dtype=np.float32)
    return probabilities, readiness, slope, roughness, curvature


def reconstruct(inputs, *, seed: int = 42):
    return reconstruct_controls(
        *inputs,
        seed=seed,
        vertex_spacing_m=1.0,
        scales_m=(8.0, 29.0, 97.0),
        scale_weights=(0.45, 0.35, 0.20),
        regime_amplitudes={"1": 0.06, "2": 0.15, "3": 0.25},
        terrain_settings={
            "slope_ramp_degrees": (18.0, 50.0),
            "gentle_ramp_degrees": (5.0, 24.0),
            "roughness_ramp_m_rms": (0.15, 1.20),
            "curvature_scale_per_m": 0.18,
            "maximum_logit_adjustment": 0.45,
        },
    )


class SurfaceReconstructionTests(unittest.TestCase):
    def test_output_is_finite_bounded_and_normalized(self):
        result = reconstruct(synthetic_inputs())
        controls = result["controls"]
        self.assertEqual(controls.shape[-1], len(VISUAL_CLASSES))
        self.assertTrue(np.all(np.isfinite(controls)))
        self.assertGreaterEqual(float(np.min(controls)), 0.0)
        self.assertLessEqual(float(np.max(controls)), 1.0)
        np.testing.assert_allclose(np.sum(controls, axis=-1), 1.0, atol=1e-6)

    def test_reconstruction_is_deterministic(self):
        inputs = synthetic_inputs()
        first = reconstruct(inputs, seed=904007)
        second = reconstruct(inputs, seed=904007)
        for name in ("controls", "freedom", "procedural_field", "terrain_influence"):
            np.testing.assert_array_equal(first[name], second[name])

    def test_different_seed_changes_placement_not_aggregate_semantics(self):
        inputs = synthetic_inputs()
        first = reconstruct(inputs, seed=1)["controls"]
        second = reconstruct(inputs, seed=2)["controls"]
        self.assertGreater(float(np.mean(np.abs(first - second))), 0.001)
        self.assertLess(float(np.max(np.abs(np.mean(first, axis=(0, 1)) - np.mean(second, axis=(0, 1))))), 0.02)

    def test_unknown_increases_freedom_without_becoming_material(self):
        low = np.full((8, 8, 6), 0.0, dtype=np.float32)
        low[..., :5] = 0.19
        low[..., 5] = 0.05
        high = low.copy()
        high[..., :5] *= 0.55 / 0.95
        high[..., 5] = 0.45
        entropy_low = np.full((8, 8), 0.8, dtype=np.float32)
        readiness = np.full((8, 8), 2, dtype=np.uint8)
        low_freedom = reconstruction_freedom(low[..., 5], entropy_low, readiness)
        high_freedom = reconstruction_freedom(high[..., 5], entropy_low, readiness)
        self.assertGreater(float(np.mean(high_freedom)), float(np.mean(low_freedom)))

        common = list(synthetic_inputs((8, 8)))
        common[0] = low
        low_controls = reconstruct(tuple(common), seed=5)["controls"]
        common[0] = high
        high_controls = reconstruct(tuple(common), seed=5)["controls"]
        np.testing.assert_allclose(low_controls, high_controls, atol=1e-6)

    def test_high_freedom_remains_spatially_coherent(self):
        inputs = list(synthetic_inputs((192, 192)))
        inputs[1][:] = 3
        result = reconstruct(tuple(inputs), seed=12)
        for index in range(len(VISUAL_CLASSES)):
            self.assertGreater(neighbor_correlation(result["controls"][..., index]), 0.85)

    def test_uniform_uncertainty_does_not_collapse_to_one_material(self):
        result = reconstruct(synthetic_inputs(), seed=9)["controls"]
        self.assertLess(float(np.percentile(np.max(result, axis=-1), 99)), 0.35)

    def test_terrain_conditioning_is_bounded_and_directionally_sensible(self):
        inputs = list(synthetic_inputs((64, 64)))
        inputs[2][:32] = 5.0
        inputs[3][:32] = 0.05
        inputs[4][:32] = 0.08
        inputs[2][32:] = 58.0
        inputs[3][32:] = 1.8
        inputs[4][32:] = -0.08
        result = reconstruct(tuple(inputs), seed=11)
        controls = result["controls"]
        self.assertGreater(float(np.mean(controls[32:, :, 0])), float(np.mean(controls[:32, :, 0])))
        self.assertGreater(float(np.mean(controls[:32, :, 4])), float(np.mean(controls[32:, :, 4])))
        self.assertLessEqual(float(np.max(result["terrain_influence"])), 0.45)

    def test_correlated_field_has_no_run_specific_state(self):
        first = coherent_field((100, 120), seed=7, vertex_spacing_m=1.0, scales_m=(8, 30), weights=(0.6, 0.4))
        second = coherent_field((100, 120), seed=7, vertex_spacing_m=1.0, scales_m=(8, 30), weights=(0.6, 0.4))
        np.testing.assert_array_equal(first, second)
        self.assertGreater(neighbor_correlation(first), 0.9)

    def test_unreal_integration_preserves_camera_and_terrain_transforms(self):
        setup_source = (ROOT / "scripts" / "earth_lab" / "unreal_surface_reconstruction.py").read_text(encoding="utf-8")
        capture_source = (ROOT / "scripts" / "earth_lab" / "unreal_capture_surface_reconstruction.py").read_text(encoding="utf-8")
        self.assertIn("SAMPLERTYPE_MASKS", setup_source)
        self.assertIn("camera_mismatches", setup_source)
        self.assertNotIn("camera.set_actor_location", setup_source)
        self.assertNotIn("camera.set_actor_rotation", setup_source)
        self.assertNotIn("landscape.set_actor_location", setup_source)
        self.assertNotIn("landscape.set_actor_scale", setup_source)
        self.assertIn("optical_component.get_world_location()", capture_source)
        self.assertIn("optical_component.get_world_rotation()", capture_source)

    def test_deployed_unreal_sources_match_repository_when_available(self):
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        project = (ROOT / config["unreal"]["project"]).resolve().parent
        mappings = {
            ROOT / "scripts" / "earth_lab" / "unreal_surface_reconstruction.py": project / "Content" / "Python" / "setup_lab009_surface.py",
            ROOT / "scripts" / "earth_lab" / "unreal_capture_surface_reconstruction.py": project / "Content" / "Python" / "capture_lab009_surface.py",
            ROOT / "scripts" / "earth_lab" / "unreal_validate_surface_reconstruction.py": project / "Content" / "Python" / "validate_lab009_surface.py",
        }
        for source, deployed in mappings.items():
            if deployed.is_file():
                self.assertEqual(source.read_bytes(), deployed.read_bytes())

    def test_frozen_input_identities_match_configuration_when_available(self):
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        frozen = config["frozen_inputs"]
        paths = {
            ROOT / frozen["lab007_root"] / "lab007-report.json": frozen["lab007_report_sha256"],
            ROOT / frozen["lab008_root"] / "lab008-report.json": frozen["lab008_report_sha256"],
            ROOT / frozen["canonical_r16"]["path"]: frozen["canonical_r16"]["sha256"],
        }
        for path, expected in paths.items():
            if path.is_file():
                self.assertEqual(sha256_file(path), expected)


if __name__ == "__main__":
    unittest.main()
