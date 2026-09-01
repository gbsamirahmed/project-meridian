from __future__ import annotations

import unittest
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import build_gfs_precipitation_poc as builder


def record(start: int, end: int, offset: int = 0) -> builder.InventoryRecord:
    return builder.InventoryRecord(
        offset=offset,
        end_offset=offset + 99,
        description=f"APCP surface {start}-{end} hour acc fcst",
        start_step=start,
        end_step=end,
    )


class InventoryPlanningTests(unittest.TestCase):
    def test_inventory_parser_keeps_every_apcp_interval(self) -> None:
        inventory = "\n".join(
            [
                "1:0:d=2026083012:APCP:surface:6-8 hour acc fcst:",
                "2:100:d=2026083012:APCP:surface:0-8 hour acc fcst:",
                "3:200:d=2026083012:TMP:2 m above ground:8 hour fcst:",
            ]
        )

        records = builder.parse_inventory(inventory)

        self.assertEqual([(item.start_step, item.end_step) for item in records], [(6, 8), (0, 8)])
        self.assertEqual([(item.offset, item.end_offset) for item in records], [(0, 99), (100, 199)])

    def test_planner_uses_shortest_valid_six_hour_bucket(self) -> None:
        inventories = {
            hour: [record(0, hour)] for hour in range(1, 7)
        }
        inventories[7] = [record(6, 7), record(0, 7)]
        inventories[8] = [record(6, 8), record(0, 8)]

        plan = builder.plan_timesteps(inventories, list(range(1, 9)))

        self.assertEqual(
            [step.derivation_start_step for step in plan],
            [0, 0, 0, 0, 0, 0, 6, 6],
        )

    def test_planner_rejects_an_interval_without_a_prior_baseline(self) -> None:
        inventories = {
            1: [record(0, 1)],
            2: [record(1, 3)],
        }

        with self.assertRaisesRegex(ValueError, "honest one-hour interval"):
            builder.plan_timesteps(inventories, [1, 2])


class CloudInventoryTests(unittest.TestCase):
    def inventory(self, hour: int) -> str:
        return "\n".join(
            [
                f"1:0:d=2026083012:TCDC:low cloud layer:{hour} hour fcst:",
                f"2:100:d=2026083012:TCDC:entire atmosphere:0-{hour} hour ave fcst:",
                f"3:200:d=2026083012:TCDC:entire atmosphere:{hour} hour fcst:",
                f"4:300:d=2026083012:TCDC:high cloud layer:{hour} hour fcst:",
                f"5:400:d=2026083012:TMP:2 m above ground:{hour} hour fcst:",
            ]
        )

    def test_selects_exact_instantaneous_entire_atmosphere_record(self) -> None:
        for hour in (1, 6, 12, 24):
            with self.subTest(hour=hour):
                selected = builder.select_instantaneous_cloud_record(
                    self.inventory(hour), hour
                )
                self.assertEqual(selected.offset, 200)
                self.assertEqual(selected.end_offset, 299)
                self.assertEqual(selected.forecast_hour, hour)

    def test_rejects_average_without_instantaneous_record(self) -> None:
        inventory = "\n".join(
            [
                "1:0:d=2026083012:TCDC:entire atmosphere:0-6 hour ave fcst:",
                "2:100:d=2026083012:TMP:2 m above ground:6 hour fcst:",
            ]
        )
        with self.assertRaisesRegex(ValueError, "exactly one instantaneous"):
            builder.select_instantaneous_cloud_record(inventory, 6)

    def test_rejects_wrong_cloud_layer(self) -> None:
        inventory = "\n".join(
            [
                "1:0:d=2026083012:TCDC:low cloud layer:12 hour fcst:",
                "2:100:d=2026083012:TMP:2 m above ground:12 hour fcst:",
            ]
        )
        with self.assertRaisesRegex(ValueError, "exactly one instantaneous"):
            builder.select_instantaneous_cloud_record(inventory, 12)

    def test_rejects_ambiguous_duplicates(self) -> None:
        inventory = "\n".join(
            [
                "1:0:d=2026083012:TCDC:entire atmosphere:24 hour fcst:",
                "2:100:d=2026083012:TCDC:entire atmosphere:24 hour fcst:",
                "3:200:d=2026083012:TMP:2 m above ground:24 hour fcst:",
            ]
        )
        with self.assertRaisesRegex(ValueError, "found 2"):
            builder.select_instantaneous_cloud_record(inventory, 24)


class CloudEncodingTests(unittest.TestCase):
    def test_uint8_png_round_trip_is_byte_exact(self) -> None:
        values = np.arange(builder.TILE_SIZE * builder.TILE_SIZE, dtype=np.uint16)
        values = (values % 101).reshape((builder.TILE_SIZE, builder.TILE_SIZE)).astype(
            np.float32
        )
        values[0, 0] = np.nan
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cloud.png"
            builder.encode_cloud_png(values, path)
            decoded = builder.decode_cloud_png(path)
        expected = np.rint(np.nan_to_num(values, nan=255)).astype(np.uint8)
        self.assertTrue(np.array_equal(decoded, expected))
        self.assertEqual(int(decoded[0, 0]), builder.CLOUD_NO_DATA_VALUE)
        self.assertEqual(int(decoded[0, 1]), int(values[0, 1]))

    def test_zero_cloud_is_valid_and_not_no_data(self) -> None:
        values = np.zeros((builder.TILE_SIZE, builder.TILE_SIZE), dtype=np.float32)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clear.png"
            builder.encode_cloud_png(values, path)
            decoded = builder.decode_cloud_png(path)
        self.assertTrue(np.all(decoded == 0))

    def test_substantive_out_of_range_cloud_fails(self) -> None:
        values = np.zeros((builder.TILE_SIZE, builder.TILE_SIZE), dtype=np.float32)
        values[5, 5] = 100.1
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "0..100"):
                builder.encode_cloud_png(values, Path(directory) / "bad.png")

    def test_antimeridian_sampling_is_periodic(self) -> None:
        values = np.broadcast_to(
            np.arange(builder.EXPECTED_NI, dtype=np.float32),
            (builder.EXPECTED_NJ, builder.EXPECTED_NI),
        )
        west = builder.source_value_at(values, -179.9, 0.0)
        east_wrapped = builder.source_value_at(values, 180.1, 0.0)
        self.assertAlmostEqual(west, east_wrapped, places=5)


class CloudMetadataTests(unittest.TestCase):
    def metadata(self) -> dict[str, object]:
        return {
            "shortName": "tcc",
            "units": "%",
            "stepType": "instant",
            "endStep": 6,
            "forecastTime": 6,
            "Ni": builder.EXPECTED_NI,
            "Nj": builder.EXPECTED_NJ,
            "iDirectionIncrementInDegrees": 0.25,
            "jDirectionIncrementInDegrees": 0.25,
            "jScansPositively": 0,
            "iScansNegatively": 0,
            "typeOfLevel": "atmosphere",
            "validityDate": 20260831,
            "validityTime": 1800,
        }

    def test_validates_parameter_level_grid_and_valid_time(self) -> None:
        builder.validate_cloud_metadata(
            self.metadata(),
            datetime(2026, 8, 31, 12, tzinfo=timezone.utc),
            6,
        )

    def test_rejects_averaged_cloud_metadata(self) -> None:
        metadata = self.metadata()
        metadata["stepType"] = "avg"
        with self.assertRaisesRegex(ValueError, "stepType"):
            builder.validate_cloud_metadata(
                metadata,
                datetime(2026, 8, 31, 12, tzinfo=timezone.utc),
                6,
            )


class WindInventoryTests(unittest.TestCase):
    def inventory(self, hour: int) -> str:
        return "\n".join(
            [
                f"1:0:d=2026083012:UGRD:10 m above ground:{hour} hour fcst:",
                f"2:100:d=2026083012:VGRD:10 m above ground:{hour} hour fcst:",
                f"3:200:d=2026083012:UGRD:80 m above ground:{hour} hour fcst:",
                f"4:300:d=2026083012:VGRD:1000 mb:{hour} hour fcst:",
                f"5:400:d=2026083012:TMP:2 m above ground:{hour} hour fcst:",
            ]
        )

    def test_selects_exact_instantaneous_10m_pair(self) -> None:
        for hour in (1, 6, 12, 24):
            with self.subTest(hour=hour):
                u_record, v_record = builder.select_instantaneous_wind_records(
                    self.inventory(hour), hour
                )
                self.assertEqual((u_record.component, u_record.offset), ("UGRD", 0))
                self.assertEqual((v_record.component, v_record.offset), ("VGRD", 100))

    def test_rejects_wrong_level_without_10m_pair(self) -> None:
        inventory = "\n".join(
            [
                "1:0:d=2026083012:UGRD:80 m above ground:6 hour fcst:",
                "2:100:d=2026083012:VGRD:80 m above ground:6 hour fcst:",
                "3:200:d=2026083012:TMP:2 m above ground:6 hour fcst:",
            ]
        )
        with self.assertRaisesRegex(ValueError, "UGRD 10 m"):
            builder.select_instantaneous_wind_records(inventory, 6)

    def test_rejects_ambiguous_component(self) -> None:
        inventory = "\n".join(
            [
                "1:0:d=2026083012:UGRD:10 m above ground:12 hour fcst:",
                "2:100:d=2026083012:UGRD:10 m above ground:12 hour fcst:",
                "3:200:d=2026083012:VGRD:10 m above ground:12 hour fcst:",
                "4:300:d=2026083012:TMP:2 m above ground:12 hour fcst:",
            ]
        )
        with self.assertRaisesRegex(ValueError, "found 2"):
            builder.select_instantaneous_wind_records(inventory, 12)


class WindMetadataTests(unittest.TestCase):
    def metadata(self, component: str) -> dict[str, object]:
        return {
            "shortName": "10u" if component == "UGRD" else "10v",
            "units": "m s**-1",
            "stepType": "instant",
            "endStep": 6,
            "forecastTime": 6,
            "Ni": builder.EXPECTED_NI,
            "Nj": builder.EXPECTED_NJ,
            "iDirectionIncrementInDegrees": 0.25,
            "jDirectionIncrementInDegrees": 0.25,
            "jScansPositively": 0,
            "iScansNegatively": 0,
            "typeOfLevel": "heightAboveGround",
            "level": 10,
            "gridType": "regular_ll",
            "uvRelativeToGrid": 0,
            "latitudeOfFirstGridPointInDegrees": 90.0,
            "longitudeOfFirstGridPointInDegrees": 0.0,
            "latitudeOfLastGridPointInDegrees": -90.0,
            "longitudeOfLastGridPointInDegrees": 359.75,
            "dataDate": 20260831,
            "dataTime": 1200,
            "validityDate": 20260831,
            "validityTime": 1800,
        }

    def test_validates_both_earth_relative_components(self) -> None:
        run_time = datetime(2026, 8, 31, 12, tzinfo=timezone.utc)
        for component in ("UGRD", "VGRD"):
            with self.subTest(component=component):
                builder.validate_wind_metadata(
                    self.metadata(component), run_time, 6, component
                )

    def test_rejects_grid_relative_vectors(self) -> None:
        metadata = self.metadata("UGRD")
        metadata["uvRelativeToGrid"] = 1
        with self.assertRaisesRegex(ValueError, "uvRelativeToGrid"):
            builder.validate_wind_metadata(
                metadata,
                datetime(2026, 8, 31, 12, tzinfo=timezone.utc),
                6,
                "UGRD",
            )


class WindEncodingTests(unittest.TestCase):
    def test_packed_vector_png_round_trip_is_code_exact(self) -> None:
        u = np.full((builder.TILE_SIZE, builder.TILE_SIZE), -12.4, dtype=np.float32)
        v = np.full((builder.TILE_SIZE, builder.TILE_SIZE), 7.8, dtype=np.float32)
        u[0, 0] = 0.0
        v[0, 0] = 0.0
        u[0, 1] = np.nan
        v[0, 1] = np.nan
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wind.png"
            builder.encode_wind_png(u, v, path)
            u_codes, v_codes = builder.decode_wind_png(path)
        expected_u = round(-12.4 / builder.WIND_COMPONENT_SCALE_MPS) + builder.WIND_COMPONENT_BIAS
        expected_v = round(7.8 / builder.WIND_COMPONENT_SCALE_MPS) + builder.WIND_COMPONENT_BIAS
        self.assertEqual(int(u_codes[2, 2]), expected_u)
        self.assertEqual(int(v_codes[2, 2]), expected_v)
        self.assertEqual(int(u_codes[0, 0]), builder.WIND_COMPONENT_BIAS)
        self.assertEqual(int(v_codes[0, 0]), builder.WIND_COMPONENT_BIAS)
        self.assertEqual(int(u_codes[0, 1]), builder.WIND_NO_DATA_CODE)
        self.assertEqual(int(v_codes[0, 1]), builder.WIND_NO_DATA_CODE)

    def test_rejects_mismatched_component_no_data(self) -> None:
        u = np.zeros((builder.TILE_SIZE, builder.TILE_SIZE), dtype=np.float32)
        v = np.zeros((builder.TILE_SIZE, builder.TILE_SIZE), dtype=np.float32)
        u[1, 1] = np.nan
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no-data masks"):
                builder.encode_wind_png(u, v, Path(directory) / "bad.png")

    def test_antimeridian_component_sampling_is_periodic(self) -> None:
        values = np.broadcast_to(
            np.arange(builder.EXPECTED_NI, dtype=np.float32),
            (builder.EXPECTED_NJ, builder.EXPECTED_NI),
        )
        self.assertAlmostEqual(
            builder.source_value_at(values, -179.9, 0.0),
            builder.source_value_at(values, 180.1, 0.0),
            places=5,
        )


class CatalogueTests(unittest.TestCase):
    def manifest(self, field_id: str, run: str) -> dict[str, object]:
        return {
            "runTime": run,
            "timesteps": [
                {"validTime": "2026-08-31T01:00:00Z"},
                {"validTime": "2026-08-31T02:00:00Z"},
            ],
        }

    def test_independent_publication_preserves_prior_field_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            builder.publish_catalog_field(
                root,
                "precipitation",
                self.manifest("precipitation", "2026-08-31T00:00:00Z"),
                "run-a/manifest.json",
            )
            builder.publish_catalog_field(
                root,
                "cloud_cover",
                self.manifest("cloud_cover", "2026-08-30T18:00:00Z"),
                "run-b/cloud-cover/manifest.json",
            )
            builder.publish_catalog_field(
                root,
                "wind_10m",
                self.manifest("wind_10m", "2026-08-30T12:00:00Z"),
                "run-c/wind-10m/manifest.json",
            )
            catalog = json.loads((root / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            set(catalog["fields"]),
            {"precipitation", "cloud_cover", "wind_10m"},
        )
        self.assertEqual(
            catalog["fields"]["precipitation"]["runTime"],
            "2026-08-31T00:00:00Z",
        )
        self.assertEqual(
            catalog["fields"]["cloud_cover"]["runTime"],
            "2026-08-30T18:00:00Z",
        )
        self.assertEqual(
            catalog["fields"]["wind_10m"]["runTime"],
            "2026-08-30T12:00:00Z",
        )

    def test_legacy_precipitation_pointer_is_preserved_when_cloud_publishes(self) -> None:
        legacy = {
            "schemaVersion": 1,
            "model": "NOAA GFS",
            "product": "pgrb2.0p25",
            "variable": "precipitation",
            "runTime": "2026-08-30T12:00:00Z",
            "generatedAt": "2026-08-30T12:30:00Z",
            "firstValidTime": "2026-08-30T13:00:00Z",
            "lastValidTime": "2026-08-31T12:00:00Z",
            "timestepCount": 24,
            "manifest": "old/manifest.json",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "latest.json").write_text(json.dumps(legacy), encoding="utf-8")
            builder.publish_catalog_field(
                root,
                "cloud_cover",
                self.manifest("cloud_cover", "2026-08-31T00:00:00Z"),
                "new/cloud-cover/manifest.json",
            )
            catalog = json.loads((root / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            catalog["fields"]["precipitation"]["manifest"], "old/manifest.json"
        )


if __name__ == "__main__":
    unittest.main()
