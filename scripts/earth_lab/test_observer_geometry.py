from __future__ import annotations

import json
import math
import sys
import tempfile
import types
import unittest
from pathlib import Path

from pyproj import Geod, Transformer

from observer_geometry import (
    bng_to_unreal_xy_cm,
    geographic_heading_to_unreal_yaw_degrees,
    look_at_orientation,
    true_heading_to_local_grid_bearing_degrees,
    vertical_fov_degrees,
)


class ObserverGeometryTests(unittest.TestCase):
    def test_origin_maps_to_unreal_zero(self) -> None:
        self.assertEqual(
            bng_to_unreal_xy_cm(266400, 359300, 266400, 359300),
            (0.0, 0.0),
        )

    def test_lab003_benchmark_uses_east_and_south_axes(self) -> None:
        self.assertEqual(
            bng_to_unreal_xy_cm(266100, 360200, 266400, 359300),
            (-30000.0, -90000.0),
        )

    def _lab004_benchmark(self) -> dict:
        path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "earth-lab"
            / "tryfan-004-benchmark.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def test_lab004_tony_edwards_coordinates_transform_and_fit_aoi(self) -> None:
        benchmark = self._lab004_benchmark()
        transformer = Transformer.from_crs(
            "EPSG:4326", "EPSG:27700", always_xy=True
        )
        observer = benchmark["observer"]
        target = benchmark["view"]["target"]
        observer_e, observer_n = transformer.transform(
            observer["wgs84"]["longitude"], observer["wgs84"]["latitude"]
        )
        target_e, target_n = transformer.transform(
            target["wgs84"]["longitude"], target["wgs84"]["latitude"]
        )
        self.assertAlmostEqual(observer_e, observer["bng"]["easting"], places=6)
        self.assertAlmostEqual(observer_n, observer["bng"]["northing"], places=6)
        self.assertAlmostEqual(target_e, target["bng"]["easting"], places=6)
        self.assertAlmostEqual(target_n, target["bng"]["northing"], places=6)
        west, south, east, north = benchmark["terrain"]["bounds"]
        self.assertTrue(west <= observer_e <= east and south <= observer_n <= north)
        self.assertTrue(west <= target_e <= east and south <= target_n <= north)

    def test_lab004_published_heading_disagreement_is_preserved(self) -> None:
        benchmark = self._lab004_benchmark()
        observer = benchmark["observer"]["wgs84"]
        target = benchmark["view"]["target"]["wgs84"]
        bearing, _, _ = Geod(ellps="WGS84").inv(
            observer["longitude"],
            observer["latitude"],
            target["longitude"],
            target["latitude"],
        )
        bearing %= 360.0
        view = benchmark["view"]
        self.assertAlmostEqual(
            bearing,
            view["coordinate_derived_wgs84_geodesic_bearing_degrees"],
            places=9,
        )
        self.assertAlmostEqual(bearing, 254.3652412901705, places=9)
        self.assertAlmostEqual(
            view["published_heading_degrees"] - bearing,
            view["published_minus_geodesic_bearing_degrees"],
            places=9,
        )
        self.assertGreater(
            abs(view["published_minus_geodesic_bearing_degrees"]), 7.0
        )

    def test_lab004_fixes_geography_and_keeps_summit_pitch_diagnostic(self) -> None:
        benchmark = self._lab004_benchmark()
        view = benchmark["view"]
        observer_wgs = benchmark["observer"]["wgs84"]
        observer_bng = benchmark["observer"]["bng"]
        summit_bng = view["pitch_reference"]["bng"]
        expected = benchmark["derived_terrain_expectations"]

        geod = Geod(ellps="WGS84")
        transformer = Transformer.from_crs(
            "EPSG:4326", "EPSG:27700", always_xy=True
        )
        end_lon, end_lat, _ = geod.fwd(
            observer_wgs["longitude"],
            observer_wgs["latitude"],
            view["published_heading_degrees"],
            1.0,
        )
        end_e, end_n = transformer.transform(end_lon, end_lat)
        grid_bearing = math.degrees(
            math.atan2(
                end_e - observer_bng["easting"],
                end_n - observer_bng["northing"],
            )
        ) % 360.0
        self.assertAlmostEqual(
            grid_bearing,
            view["published_heading_bng_grid_bearing_degrees"],
            places=6,
        )
        self.assertAlmostEqual(
            geographic_heading_to_unreal_yaw_degrees(grid_bearing),
            expected["unreal_yaw_degrees"],
            places=6,
        )

        observer_xy = bng_to_unreal_xy_cm(
            observer_bng["easting"],
            observer_bng["northing"],
            266400.0,
            359300.0,
        )
        summit_xy = bng_to_unreal_xy_cm(
            summit_bng["easting"], summit_bng["northing"], 266400.0, 359300.0
        )
        target_orientation = look_at_orientation(
            (
                observer_xy[0],
                observer_xy[1],
                (expected["observer_elevation_m_odn"] + 1.7 - 650.0) * 100.0,
            ),
            (
                summit_xy[0],
                summit_xy[1],
                (expected["summit_elevation_m_odn"] - 650.0) * 100.0,
            ),
        )
        self.assertAlmostEqual(
            target_orientation.unreal_pitch_degrees,
            expected["unreal_pitch_degrees"],
            places=9,
        )
        self.assertNotAlmostEqual(
            target_orientation.unreal_yaw_degrees,
            expected["unreal_yaw_degrees"],
            places=3,
        )
        self.assertEqual(
            view["target"]["orientation_role"],
            "DIAGNOSTIC_ONLY_NOT_USED_FOR_CAMERA_ORIENTATION",
        )
        self.assertEqual(view["mode"], "published_heading_calibrated_pitch")
        self.assertIn(
            "DIAGNOSTIC_REFERENCE_ONLY",
            view["pitch_reference"]["orientation_role"],
        )
        self.assertEqual(
            expected["summit_derived_reference_pitch_degrees"],
            expected["unreal_pitch_degrees"],
        )
        self.assertIsNone(expected["calibrated_pitch_degrees"])
        self.assertEqual(
            benchmark["camera_calibration"]["calibrated_horizontal_fov_degrees"],
            40.0,
        )

    def test_lab004_pitch_trials_cannot_change_fixed_geography(self) -> None:
        benchmark = self._lab004_benchmark()
        observer = benchmark["observer"]
        view = benchmark["view"]
        fixed_xy = bng_to_unreal_xy_cm(
            observer["bng"]["easting"],
            observer["bng"]["northing"],
            266400.0,
            359300.0,
        )
        fixed_yaw = geographic_heading_to_unreal_yaw_degrees(
            view["published_heading_bng_grid_bearing_degrees"]
        )
        terrain_identity = (
            benchmark["terrain"]["source"],
            benchmark["terrain"]["bounds"],
            benchmark["terrain"]["survey_date"],
            benchmark["terrain"]["native_resolution_m"],
        )
        for pitch in (20.0, 25.0, 30.0):
            with self.subTest(pitch=pitch):
                self.assertAlmostEqual(fixed_xy[0], 52549.12174294889, places=6)
                self.assertAlmostEqual(fixed_xy[1], -29494.947166356724, places=6)
                self.assertAlmostEqual(fixed_yaw, 158.59199947759208, places=9)
                self.assertEqual(observer["eye_height_m"], 1.7)
                self.assertEqual(view["published_heading_degrees"], 247.0)
                self.assertEqual(
                    terrain_identity,
                    (
                        "Welsh Government national LiDAR 2020-2023",
                        [264900.0, 357800.0, 267900.0, 360800.0],
                        "2021-03-02",
                        1.0,
                    ),
                )
                self.assertTrue(-90.0 < pitch < 90.0)

    def test_true_heading_override_preserves_local_grid_convergence(self) -> None:
        benchmark = self._lab004_benchmark()
        view = benchmark["view"]
        published_grid = true_heading_to_local_grid_bearing_degrees(
            247.0,
            view["published_heading_degrees"],
            view["published_heading_bng_grid_bearing_degrees"],
        )
        recovered_grid = true_heading_to_local_grid_bearing_degrees(
            253.55,
            view["published_heading_degrees"],
            view["published_heading_bng_grid_bearing_degrees"],
        )
        self.assertAlmostEqual(published_grid, 248.59199947759208, places=9)
        self.assertAlmostEqual(recovered_grid, 255.14199947759208, places=9)
        self.assertAlmostEqual(
            geographic_heading_to_unreal_yaw_degrees(recovered_grid),
            165.14199947759208,
            places=9,
        )
        self.assertEqual(view["published_heading_degrees"], 247.0)
        self.assertEqual(
            benchmark["camera_calibration"]["recovered_skyline_heading_degrees"],
            253.55,
        )

    def test_heading_override_changes_orientation_only(self) -> None:
        benchmark = self._lab004_benchmark()
        observer = benchmark["observer"]
        view = benchmark["view"]
        fixed_xy = bng_to_unreal_xy_cm(
            observer["bng"]["easting"],
            observer["bng"]["northing"],
            266400.0,
            359300.0,
        )
        fixed_inputs = (
            fixed_xy,
            observer["eye_height_m"],
            benchmark["terrain"]["source"],
            benchmark["terrain"]["bounds"],
            benchmark["terrain"]["survey_date"],
            benchmark["terrain"]["native_resolution_m"],
        )
        yaws = []
        for heading in (247.0, 253.55, 260.0):
            grid = true_heading_to_local_grid_bearing_degrees(
                heading,
                view["published_heading_degrees"],
                view["published_heading_bng_grid_bearing_degrees"],
            )
            yaws.append(geographic_heading_to_unreal_yaw_degrees(grid))
            self.assertEqual(
                fixed_inputs,
                (
                    fixed_xy,
                    1.7,
                    "Welsh Government national LiDAR 2020-2023",
                    [264900.0, 357800.0, 267900.0, 360800.0],
                    "2021-03-02",
                    1.0,
                ),
            )
        self.assertEqual(len(set(yaws)), 3)

    def test_cardinal_headings_map_to_unreal_yaw(self) -> None:
        expected = {0: -90.0, 90: 0.0, 180: 90.0, 270: -180.0, 360: -90.0}
        for heading, yaw in expected.items():
            with self.subTest(heading=heading):
                self.assertEqual(geographic_heading_to_unreal_yaw_degrees(heading), yaw)

    def test_benchmark_heading_maps_to_southeast_yaw(self) -> None:
        self.assertEqual(geographic_heading_to_unreal_yaw_degrees(157), 67.0)

    def test_look_at_orientation_uses_unreal_axes_and_positive_up_pitch(self) -> None:
        orientation = look_at_orientation((0.0, 0.0, 100.0), (300.0, 400.0, 600.0))
        self.assertAlmostEqual(orientation.horizontal_distance_cm, 500.0)
        self.assertAlmostEqual(orientation.distance_3d_cm, math.sqrt(500000.0))
        self.assertAlmostEqual(orientation.geographic_bearing_degrees, 143.130102354156)
        self.assertAlmostEqual(orientation.unreal_yaw_degrees, 53.130102354156)
        self.assertAlmostEqual(orientation.unreal_pitch_degrees, 45.0)

    def test_horizontal_target_keeps_zero_pitch(self) -> None:
        orientation = look_at_orientation((0.0, 0.0, 10.0), (0.0, -100.0, 10.0))
        self.assertEqual(orientation.geographic_bearing_degrees, 0.0)
        self.assertEqual(orientation.unreal_yaw_degrees, -90.0)
        self.assertEqual(orientation.unreal_pitch_degrees, 0.0)

    def test_vertical_only_target_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "distinct horizontal"):
            look_at_orientation((1.0, 2.0, 3.0), (1.0, 2.0, 4.0))

    def test_sixty_degree_horizontal_fov_at_sixteen_by_nine(self) -> None:
        self.assertTrue(
            math.isclose(
                vertical_fov_degrees(60.0, 16.0 / 9.0),
                35.98339777135764,
                abs_tol=1e-12,
            )
        )

    def test_invalid_fov_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            vertical_fov_degrees(180.0, 16.0 / 9.0)

    def test_unreal_placement_uses_engine_look_at_and_camera_component_validation(self) -> None:
        source = Path(__file__).with_name("unreal_place_observer.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("unreal.MathLibrary.find_look_at_rotation(", source)
        self.assertIn("camera_component.get_forward_vector()", source)
        self.assertIn("camera_component.get_camera_view(0.0)", source)
        self.assertIn("published_heading_calibrated_pitch", source)
        self.assertIn("target_pitch_only=True", source)
        self.assertIn("MERIDIAN_CAMERA_HEADING_DEGREES", source)
        self.assertIn("MERIDIAN_CAMERA_PITCH_DEGREES", source)
        self.assertIn("MERIDIAN_HORIZONTAL_FOV_DEGREES", source)
        self.assertNotIn("\n    forward = camera.get_actor_forward_vector()", source)

    def test_unreal_exec_bootstrap_works_without_dunder_file(self) -> None:
        source_path = Path(__file__).with_name("unreal_place_observer.py")
        source = source_path.read_text(encoding="utf-8")
        original_unreal = sys.modules.get("unreal")
        original_path = list(sys.path)
        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                project_root = Path(temporary_directory)
                python_root = project_root / "Content" / "Python"
                python_root.mkdir(parents=True)
                (python_root / "observer_geometry.py").write_text(
                    Path(__file__).with_name("observer_geometry.py").read_text(
                        encoding="utf-8"
                    ),
                    encoding="utf-8",
                )
                fake_unreal = types.ModuleType("unreal")
                fake_unreal.Paths = types.SimpleNamespace(
                    project_dir=lambda: str(project_root)
                )
                sys.modules["unreal"] = fake_unreal
                namespace = {"__name__": "unreal_console_exec_test"}
                exec(compile(source, str(source_path), "exec"), namespace)
                self.assertNotIn("__file__", namespace)
                self.assertEqual(namespace["SCRIPT_DIRECTORY"], python_root.resolve())
                resolve_fov = namespace["_resolve_benchmark_fov"]
                validate_pitch = namespace["_validated_camera_pitch"]
                self.assertIsNone(validate_pitch(None))
                for pitch in (20.0, 25.0, 30.0):
                    self.assertEqual(validate_pitch(pitch), pitch)
                for invalid in (-90.0, 90.0, float("nan"), float("inf")):
                    with self.assertRaises(ValueError):
                        validate_pitch(invalid)
                calibration = {
                    "horizontal_fov_degrees": None,
                    "initial_calibration_horizontal_fov_degrees": 60.0,
                }
                self.assertEqual(
                    resolve_fov(calibration, None),
                    (60.0, "METADATA_INITIAL_CALIBRATION_PARAMETER"),
                )
                self.assertEqual(
                    resolve_fov(
                        {
                            "horizontal_fov_degrees": None,
                            "calibrated_horizontal_fov_degrees": 40.0,
                            "initial_calibration_horizontal_fov_degrees": 60.0,
                        },
                        None,
                    ),
                    (40.0, "METADATA_EXPLICIT_CALIBRATION_OVERRIDE"),
                )
                self.assertEqual(
                    resolve_fov(calibration, 42.0),
                    (42.0, "CALL_OVERRIDE"),
                )
                with self.assertRaisesRegex(ValueError, "FOV is unknown"):
                    resolve_fov({"horizontal_fov_degrees": None}, None)
        finally:
            sys.path[:] = original_path
            if original_unreal is None:
                sys.modules.pop("unreal", None)
            else:
                sys.modules["unreal"] = original_unreal

if __name__ == "__main__":
    unittest.main()
