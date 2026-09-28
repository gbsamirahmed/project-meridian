from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_origin

from prepare_unreal_project import prepare_project
from unreal_landscape import (
    LandscapeSettings,
    _write_heightmaps,
    decode_elevation_m,
    encode_elevation_m,
    resample_full_extent,
)


class UnrealLandscapeTests(unittest.TestCase):
    def test_recommended_landscape_layout_is_consistent(self) -> None:
        settings = LandscapeSettings()
        settings.validate()
        self.assertEqual(settings.quads_per_axis, 2016)

    def test_lab004_layout_is_3025_vertices_and_three_kilometres(self) -> None:
        settings = LandscapeSettings(output_vertices=3025, components_per_axis=24)
        settings.validate()
        self.assertEqual(settings.quads_per_axis, 3024)
        self.assertAlmostEqual(3000.0 / settings.quads_per_axis, 0.9920634920634921)

    def test_encoding_round_trip_is_within_half_a_quantization_step(self) -> None:
        settings = LandscapeSettings()
        values = np.linspace(300.46, 989.13, 10000, dtype=np.float64).reshape(100, 100)
        encoded = encode_elevation_m(
            values, settings.vertical_origin_m_odn, settings.unreal_z_scale
        )
        decoded = decode_elevation_m(
            encoded, settings.vertical_origin_m_odn, settings.unreal_z_scale
        )
        tolerance_m = settings.unreal_z_scale / 128.0 / 100.0 / 2.0
        self.assertLessEqual(float(np.max(np.abs(decoded - values))), tolerance_m)

    def test_missing_values_are_refused(self) -> None:
        values = np.array([[650.0, np.nan]], dtype=np.float64)
        with self.assertRaisesRegex(ValueError, "missing terrain"):
            encode_elevation_m(values, 650.0, 150.0)

    def test_resampling_preserves_extent_and_orientation(self) -> None:
        source = np.array(
            [[100.0, 200.0], [300.0, 400.0]], dtype=np.float32
        )
        transform = from_origin(10.0, 30.0, 1.0, 1.0)
        output, output_transform = resample_full_extent(
            source, transform, rasterio.crs.CRS.from_epsg(27700), None, 3
        )
        self.assertEqual(output.shape, (3, 3))
        self.assertLess(float(output[0, 0]), float(output[-1, 0]))
        self.assertLess(float(output[0, 0]), float(output[0, -1]))
        self.assertEqual(
            rasterio.transform.array_bounds(3, 3, output_transform),
            rasterio.transform.array_bounds(2, 2, transform),
        )

    def test_png_and_r16_preserve_identical_uint16_values(self) -> None:
        encoded = np.arange(25, dtype=np.uint16).reshape(5, 5) + 32760
        with tempfile.TemporaryDirectory() as temporary:
            files = _write_heightmaps(encoded, Path(temporary) / "height")
            png = np.asarray(
                Image.open(Path(temporary) / files["png"]["path"]), dtype=np.uint16
            )
            raw = np.fromfile(
                Path(temporary) / files["r16"]["path"], dtype="<u2"
            ).reshape(5, 5)
            np.testing.assert_array_equal(png, encoded)
            np.testing.assert_array_equal(raw, encoded)

    def test_project_preparation_uses_manifest_settings(self) -> None:
        manifest = {
            "representation": {"type": "Unreal Landscape"},
            "unreal_landscape": {
                "quads_per_axis": 2016,
                "quads_per_section": 63,
                "sections_per_component": 4,
                "components": [16, 16],
                "xy_scale_cm": 99.206349206,
                "z_scale": 150.0,
                "expected_world_dimensions_m": [2000.0, 2000.0],
            },
            "coordinate_frame": {
                "local_origin_bng": {
                    "easting": 266400.0,
                    "northing": 359300.0,
                    "elevation_m_odn": 650.0,
                }
            },
            "surfaces": {
                "dtm": {
                    "output": {
                        "files": {
                            "png": {"path": "terrain-dtm.png"},
                            "r16": {
                                "path": "terrain-dtm.r16",
                                "sha256": "fixture-r16-sha256",
                            },
                        }
                    }
                }
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "output" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            benchmark_path = root / "benchmark.json"
            benchmark_path.write_text(
                json.dumps({"benchmark_id": "fixture"}), encoding="utf-8"
            )
            overlay_path = root / "photo-overlay.json"
            overlay_path.write_text(
                json.dumps({"overlay_id": "fixture"}), encoding="utf-8"
            )
            project_file = prepare_project(
                manifest_path,
                root / "project",
                benchmark_path=benchmark_path,
                photo_overlay_path=overlay_path,
            )
            self.assertTrue(project_file.exists())
            guide = (root / "project" / "IMPORT.md").read_text(encoding="utf-8")
            self.assertIn("2017 x 2017", guide)
            self.assertIn("99.206349206", guide)
            self.assertIn("Flip Y Axis", guide)
            self.assertIn("terrain-dtm.r16", guide)
            self.assertIn("fixture-r16-sha256", guide)
            self.assertIn("X=-100000.000000, Y=-100000.000000, Z=0", guide)
            self.assertIn("Enable Edit Layers", guide)
            validator_path = (
                root
                / "project"
                / "Content"
                / "Python"
                / "validate_landscape.py"
            )
            self.assertTrue(validator_path.exists())
            validator = validator_path.read_text(encoding="utf-8")
            self.assertIn("EditorActorSubsystem", validator)
            self.assertIn("LandscapeStreamingProxy", validator)
            self.assertIn("geometry_actors = [landscape]", validator)
            self.assertIn("component.section_base_x", validator)
            self.assertIn("Cannot derive Landscape bounds from an empty actor collection", validator)
            self.assertNotIn("No LandscapeStreamingProxy actors are loaded", validator)
            self.assertNotIn("EditorLevelLibrary", validator)
            observer_path = (
                root / "project" / "Content" / "Python" / "place_observer.py"
            )
            geometry_path = (
                root / "project" / "Content" / "Python" / "observer_geometry.py"
            )
            overlay_script_path = (
                root / "project" / "Content" / "Python" / "setup_photo_overlay.py"
            )
            overlay_helper_path = (
                root / "project" / "Content" / "Python" / "photo_overlay.py"
            )
            restore_camera_path = (
                root
                / "project"
                / "Content"
                / "Python"
                / "restore_lab004a_camera.py"
            )
            validate_camera_path = (
                root
                / "project"
                / "Content"
                / "Python"
                / "validate_lab004a_camera.py"
            )
            self.assertTrue(observer_path.exists())
            self.assertTrue(geometry_path.exists())
            self.assertTrue(overlay_script_path.exists())
            self.assertTrue(overlay_helper_path.exists())
            self.assertTrue(restore_camera_path.exists())
            self.assertTrue(validate_camera_path.exists())
            observer = observer_path.read_text(encoding="utf-8")
            self.assertIn("line_trace_multi", observer)
            self.assertIn("target_easting", observer)
            self.assertIn("look_at_orientation", observer)
            self.assertIn("Meridian_Lab004_Geometric_Camera", observer)
            self.assertIn("def place_benchmark(", observer)
            self.assertIn("meridian-benchmark-source.json", observer)
            source = json.loads(
                (root / "project" / "meridian-landscape-source.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(source["manifest"], str(manifest_path.resolve()))
            benchmark_pointer = json.loads(
                (root / "project" / "meridian-benchmark-source.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(benchmark_pointer["benchmark"], str(benchmark_path.resolve()))
            overlay_pointer = json.loads(
                (root / "project" / "meridian-photo-overlay-source.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(overlay_pointer["config"], str(overlay_path.resolve()))
            descriptor = json.loads(project_file.read_text(encoding="utf-8"))
            self.assertIn(
                {"Name": "ImagePlate", "Enabled": True},
                descriptor["Plugins"],
            )


if __name__ == "__main__":
    unittest.main()
