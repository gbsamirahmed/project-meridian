"""Deterministic automatic GFS update, publication, recovery and retention tests."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import gfs_updater as updater
import gfs_weather_builder as core

OLD = datetime(2026, 1, 1, tzinfo=timezone.utc)
NEW = datetime(2026, 1, 1, 6, tzinfo=timezone.utc)
LATER = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def catalogue(value):
    name = value.strftime("%Y%m%dT%HZ")
    fields = {}
    for field_id, subdir in updater.FIELD_PATHS.items():
        path = "/".join(p for p in (name, subdir, "manifest.json") if p)
        fields[field_id] = {
            "runTime": iso(value), "firstValidTime": iso(value + timedelta(hours=1)),
            "lastValidTime": iso(value + timedelta(hours=24)), "timestepCount": 24,
            "manifest": path,
        }
    return {"schemaVersion": 2, "model": "NOAA GFS", "product": "pgrb2.0p25",
            "generatedAt": iso(value + timedelta(hours=1)), "fields": fields}


def catalogue_for_artifact(value, artifact):
    result = catalogue(value)
    for entry in result["fields"].values():
        parts = entry["manifest"].split("/")
        parts[0] = artifact
        entry["manifest"] = "/".join(parts)
    return result


def write_catalogue(root, value):
    (root / "latest.json").write_text(json.dumps(catalogue(value)), encoding="utf-8")


def write_legacy_catalogue(root, value):
    result = catalogue(value)
    result["fields"].pop("pressure_msl")
    (root / "latest.json").write_text(json.dumps(result), encoding="utf-8")


def arguments(root):
    return argparse.Namespace(output_root=root, hours="1-24", run=None, candidate_count=12,
        reference_time=None, keep_downloads=False, watch=False, poll_minutes=60,
        check_only=False)


def resolution(value):
    return SimpleNamespace(run_time=value, date=value.date(), cycle=value.hour,
                           timesteps=(), cloud_records=(), wind_records=(),
                           temperature_records=(), pressure_records=(),
                           checked_candidates=())


def create_recognised_run(root, value, field_ids=None):
    directory = root / value.strftime("%Y%m%dT%HZ")
    selected = set(field_ids or updater.FIELD_PATHS)
    for field_id, subdir in updater.FIELD_PATHS.items():
        if field_id not in selected:
            continue
        field_dir = directory / subdir
        field_dir.mkdir(parents=True, exist_ok=True)
        manifest = {"model": "NOAA GFS", "product": "pgrb2.0p25", "runTime": iso(value),
                    "field": {"id": field_id}}
        (field_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (field_dir / "validation.json").write_text("{}", encoding="utf-8")
        (field_dir / "tiles").mkdir()
    return directory


def validate_fixture_field(directory, field_id, date, verify_png=True):
    if not directory.is_dir():
        raise ValueError("missing field")
    manifest_path = directory / "manifest.json"
    validation_path = directory / "validation.json"
    tiles = directory / "tiles"
    if not manifest_path.is_file() or not validation_path.is_file() or not tiles.is_dir():
        raise ValueError("incomplete field")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["field"]["id"] != field_id or manifest["runTime"] != iso(date):
        raise ValueError("wrong field or cycle")
    return manifest


class DiscoveryTests(unittest.TestCase):
    def test_incomplete_newer_cycle_is_skipped_without_rechecking_current(self):
        args = SimpleNamespace(run=None, reference_time=None, candidate_count=2,
                               require_all_fields=True)
        with patch.object(core, "discover_latest_archive_date", return_value=NEW.date()), \
             patch.object(core, "candidate_run_times", return_value=[NEW, OLD]) as candidates, \
             patch.object(core, "probe_run", side_effect=ValueError("missing ceiling")) as probe:
            self.assertIsNone(core.resolve_run(args, updater.HOURS, newer_than=OLD))
        candidates.assert_called_once()
        probe.assert_called_once_with(NEW, updater.HOURS, True)


class UpdateTests(unittest.TestCase):
    def test_same_cycle_previous_schema_fields_are_staged_for_reuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = create_recognised_run(
                root, NEW, set(updater.FIELD_PATHS) - {"pressure_msl"}
            )
            staged = root / ".20260101T06Z-update-building" / "20260101T06Z"
            with patch.object(updater, "validate_field", side_effect=validate_fixture_field):
                result = updater.stage_reusable_fields(source, staged, "20260101T06Z")
            self.assertEqual(set(result["fields"]), set(updater.FIELD_PATHS) - {"pressure_msl"})
            self.assertFalse((staged / "pressure-msl").exists())
            self.assertTrue((staged / "cloud-cover" / "manifest.json").is_file())
            self.assertTrue((staged / "manifest.json").is_file())

    def test_different_cycle_fields_are_never_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = create_recognised_run(root, NEW)
            with self.assertRaisesRegex(ValueError, "exact same model cycle"):
                updater.stage_reusable_fields(source, root / "staged", "20260101T12Z")

    def test_previous_schema_same_cycle_reuses_nine_and_builds_only_pressure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy_fields = set(updater.FIELD_PATHS) - {"pressure_msl"}
            old_run = create_recognised_run(root, NEW, legacy_fields)
            write_legacy_catalogue(root, OLD)
            before = (root / "latest.json").read_bytes()
            built = []
            def build(args, _resolution, _hours):
                run = args.output_root / "20260101T06Z"
                built.extend(field for field, subdir in updater.FIELD_PATHS.items()
                             if not (run / subdir / "manifest.json").is_file())
                create_recognised_run(args.output_root, NEW, built)
            def validate_run(path, verify_png=True):
                if not (path / "pressure-msl" / "manifest.json").is_file():
                    raise ValueError("missing pressure_msl")
                return catalogue_for_artifact(NEW, path.name)
            with patch.object(core, "resolve_run", return_value=resolution(NEW)) as discover, \
                 patch.object(core, "build_resolved_run", side_effect=build), \
                 patch.object(updater, "validate_field", side_effect=validate_fixture_field), \
                 patch.object(updater, "validate_run", side_effect=validate_run), \
                 patch.object(updater, "prune_runs", return_value=[]):
                result = updater.update_once(arguments(root))
            self.assertEqual(discover.call_args.kwargs["newer_than"], OLD - timedelta(seconds=1))
            self.assertEqual(built, ["pressure_msl"])
            self.assertEqual(set(result["reusedFields"]), legacy_fields)
            self.assertGreater(result["hardLinkedFiles"], 0); self.assertEqual(result["copiedFiles"], 0)
            self.assertNotEqual((root / "latest.json").read_bytes(), before)
            self.assertFalse((old_run / "pressure-msl").exists())
            artifact = updater.schema_artifact_name("20260101T06Z")
            self.assertTrue((root / artifact / "pressure-msl" / "manifest.json").is_file())
            self.assertTrue(all(entry["manifest"].startswith(f"{artifact}/")
                                for entry in updater.read_catalogue(root)["fields"].values()))

    def test_live_previous_schema_cycle_can_publish_a_distinct_complete_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = create_recognised_run(root, NEW, set(updater.FIELD_PATHS) - {"pressure_msl"})
            write_legacy_catalogue(root, NEW)
            before = (root / "latest.json").read_bytes()
            def build(args, _resolution, _hours):
                create_recognised_run(args.output_root, NEW, {"pressure_msl"})
            def validate(path, verify_png=True):
                if path == base:
                    raise ValueError("previous schema")
                return catalogue_for_artifact(NEW, path.name)
            with patch.object(core, "resolve_run", return_value=resolution(NEW)) as discover, \
                 patch.object(core, "build_resolved_run", side_effect=build), \
                 patch.object(updater, "validate_field", side_effect=validate_fixture_field), \
                 patch.object(updater, "validate_run", side_effect=validate), \
                 patch.object(updater, "prune_runs", return_value=[]):
                result = updater.update_once(arguments(root))
            self.assertEqual(discover.call_args.kwargs["newer_than"],
                             NEW - timedelta(seconds=1))
            self.assertNotEqual((root / "latest.json").read_bytes(), before)
            self.assertTrue(base.exists())
            self.assertNotEqual(result["artifact"], base.name)

    def test_invalid_same_cycle_field_is_regenerated_with_missing_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); write_legacy_catalogue(root, OLD)
            source = create_recognised_run(root, NEW, set(updater.FIELD_PATHS) - {"pressure_msl"})
            cloud_manifest = source / "cloud-cover" / "manifest.json"
            invalid = json.loads(cloud_manifest.read_text()); invalid["field"]["id"] = "wrong"
            cloud_manifest.write_text(json.dumps(invalid))
            built = []
            def build(args, _resolution, _hours):
                run = args.output_root / "20260101T06Z"
                built.extend(field for field, subdir in updater.FIELD_PATHS.items()
                             if not (run / subdir / "manifest.json").is_file())
                create_recognised_run(args.output_root, NEW, built)
            def validate_run(path, verify_png=True):
                if not (path / "pressure-msl" / "manifest.json").is_file():
                    raise ValueError("invalid cloud and missing pressure")
                return catalogue_for_artifact(NEW, path.name)
            with patch.object(core, "resolve_run", return_value=resolution(NEW)), \
                 patch.object(core, "build_resolved_run", side_effect=build), \
                 patch.object(updater, "validate_field", side_effect=validate_fixture_field), \
                 patch.object(updater, "validate_run", side_effect=validate_run), \
                 patch.object(updater, "prune_runs", return_value=[]):
                result = updater.update_once(arguments(root))
            self.assertEqual(set(built), {"cloud_cover", "pressure_msl"})
            self.assertNotIn("cloud_cover", result["reusedFields"])

    def test_incomplete_timestep_invalidates_the_whole_reuse_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = create_recognised_run(root, NEW)
            staged = root / "staged"
            def validate(directory, field_id, date, verify_png=True):
                if directory == source / "visibility-surface":
                    raise ValueError("missing f012 tile")
                return validate_fixture_field(directory, field_id, date, verify_png)
            with patch.object(updater, "validate_field", side_effect=validate):
                result = updater.stage_reusable_fields(source, staged, "20260101T06Z")
            self.assertNotIn("visibility_surface", result["fields"])
            self.assertFalse((staged / "visibility-surface").exists())

    def test_future_required_field_uses_the_same_generic_reuse_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = create_recognised_run(root, NEW)
            existing_fields = set(updater.FIELD_PATHS)
            with patch.dict(updater.FIELD_PATHS, {"future_field": "future-field"}), \
                 patch.object(updater, "validate_field", side_effect=validate_fixture_field):
                result = updater.stage_reusable_fields(source, root / "staged", "20260101T06Z")
            self.assertEqual(set(result["fields"]), existing_fields)
            self.assertNotIn("future_field", result["fields"])

    def test_complete_existing_ten_field_candidate_is_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); write_legacy_catalogue(root, OLD)
            candidate = create_recognised_run(root, NEW)
            with patch.object(core, "resolve_run", return_value=resolution(NEW)), \
                 patch.object(core, "build_resolved_run") as build, \
                 patch.object(updater, "validate_run", return_value=catalogue(NEW)), \
                 patch.object(updater, "prune_runs", return_value=[]):
                result = updater.update_once(arguments(root))
            build.assert_not_called(); self.assertFalse(result["generated"])
            self.assertTrue((candidate / "pressure-msl").is_dir())
            self.assertEqual(set(updater.read_catalogue(root)["fields"]), set(updater.FIELD_PATHS))

    def test_failed_new_run_build_preserves_previous_schema_catalogue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_recognised_run(root, NEW, set(updater.FIELD_PATHS) - {"pressure_msl"})
            write_legacy_catalogue(root, OLD); before = (root / "latest.json").read_bytes()
            with patch.object(core, "resolve_run", return_value=resolution(NEW)) as discover, \
                 patch.object(core, "build_resolved_run", side_effect=RuntimeError("pressure failed")), \
                 patch.object(updater, "validate_field", side_effect=validate_fixture_field):
                with self.assertRaisesRegex(RuntimeError, "pressure failed"):
                    updater.update_once(arguments(root))
            self.assertEqual(discover.call_args.kwargs["newer_than"], OLD - timedelta(seconds=1))
            self.assertEqual((root / "latest.json").read_bytes(), before)
            self.assertFalse((root / "20260101T06Z" / "pressure-msl").exists())
            self.assertTrue((root / ".20260101T06Z-update-building" / ".meridian-update").is_file())

    def test_subsequent_new_run_can_publish_complete_required_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old_run = create_recognised_run(root, NEW, set(updater.FIELD_PATHS) - {"pressure_msl"})
            write_legacy_catalogue(root, OLD); before = (root / "latest.json").read_bytes()
            def build(args, _resolution, _hours):
                create_recognised_run(args.output_root, NEW, {"pressure_msl"})
            def validate_run(path, verify_png=True):
                if path == old_run and not (path / "pressure-msl").exists():
                    raise ValueError("previous schema")
                return catalogue_for_artifact(NEW, path.name)
            with patch.object(core, "resolve_run", return_value=resolution(NEW)) as discover, \
                 patch.object(core, "build_resolved_run", side_effect=build), \
                 patch.object(updater, "validate_field", side_effect=validate_fixture_field), \
                 patch.object(updater, "validate_run", side_effect=validate_run), \
                 patch.object(updater, "prune_runs", return_value=[]):
                result = updater.update_once(arguments(root))
            self.assertEqual(discover.call_args.kwargs["newer_than"], OLD - timedelta(seconds=1))
            self.assertTrue(result["generated"]); self.assertNotEqual((root / "latest.json").read_bytes(), before)
            self.assertEqual(set(updater.read_catalogue(root)["fields"]), set(updater.FIELD_PATHS))
            self.assertTrue(old_run.exists())

    def test_no_rebuild_when_catalogue_is_current(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); write_catalogue(root, OLD)
            with patch.object(core, "resolve_run", return_value=None) as discover, \
                 patch.object(updater, "prune_runs", return_value=[]) as prune, \
                 patch.object(core, "build_resolved_run") as build:
                result = updater.update_once(arguments(root))
            self.assertFalse(result["generated"]); build.assert_not_called(); prune.assert_called_once()
            self.assertEqual(discover.call_args.kwargs["newer_than"], OLD)

    def test_newer_usable_run_builds_validates_then_publishes_atomically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); write_catalogue(root, OLD); before = (root / "latest.json").read_bytes()
            events = []
            def build(args, _resolution, _hours):
                events.append("build"); (args.output_root / "20260101T06Z").mkdir(parents=True)
            def validate(path, verify_png=True):
                events.append("validate"); self.assertTrue(path.exists()); return catalogue(NEW)
            original_write = core.write_json_atomically
            def publish(path, value):
                events.append("publish"); self.assertTrue((root / "20260101T06Z").is_dir())
                original_write(path, value)
            with patch.object(core, "resolve_run", return_value=resolution(NEW)), \
                 patch.object(core, "build_resolved_run", side_effect=build), \
                 patch.object(updater, "validate_run", side_effect=validate), \
                 patch.object(core, "write_json_atomically", side_effect=publish), \
                 patch.object(updater, "prune_runs", return_value=[]):
                result = updater.update_once(arguments(root))
            self.assertEqual(events, ["build", "validate", "validate", "publish", "validate"])
            self.assertNotEqual((root / "latest.json").read_bytes(), before)
            self.assertEqual(updater.read_catalogue(root)["fields"]["gust_surface"]["runTime"], iso(NEW))
            self.assertTrue(result["generated"])

    def test_discovery_network_failure_leaves_latest_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); write_catalogue(root, OLD); before = (root / "latest.json").read_bytes()
            with patch.object(core, "resolve_run", side_effect=core.SourceUnavailableError("offline")):
                with self.assertRaises(core.SourceUnavailableError): updater.update_once(arguments(root))
            self.assertEqual((root / "latest.json").read_bytes(), before)

    def test_generation_or_validation_failure_leaves_latest_unchanged(self):
        for failure_point in ("generation", "validation"):
            with self.subTest(failure_point=failure_point), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); write_catalogue(root, OLD); before = (root / "latest.json").read_bytes()
                def build(args, _resolution, _hours):
                    (args.output_root / "20260101T06Z").mkdir(parents=True)
                    if failure_point == "generation": raise RuntimeError("download stopped")
                validator = RuntimeError("invalid dataset") if failure_point == "validation" else catalogue(NEW)
                with patch.object(core, "resolve_run", return_value=resolution(NEW)), \
                     patch.object(core, "build_resolved_run", side_effect=build), \
                     patch.object(updater, "validate_run", side_effect=validator):
                    with self.assertRaises(RuntimeError): updater.update_once(arguments(root))
                self.assertEqual((root / "latest.json").read_bytes(), before)

    def test_lock_rejects_a_duplicate_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with updater.update_lock(root):
                with self.assertRaises(BlockingIOError):
                    with updater.update_lock(root): pass

    def test_retention_failure_cannot_fail_an_already_published_update(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); write_catalogue(root, OLD)
            (root / "20260101T06Z").mkdir()
            with patch.object(core, "resolve_run", return_value=resolution(NEW)), \
                 patch.object(core, "build_resolved_run") as build, \
                 patch.object(updater, "validate_run", return_value=catalogue(NEW)), \
                 patch.object(updater, "prune_runs", side_effect=OSError("busy")):
                result = updater.update_once(arguments(root))
            build.assert_not_called()
            self.assertEqual(result["run"], iso(NEW)); self.assertEqual(result["removed"], [])
            self.assertEqual(updater.read_catalogue(root)["fields"]["cloud_ceiling"]["runTime"], iso(NEW))


class WatchTests(unittest.TestCase):
    def test_keyboard_interrupt_stops_watch_after_a_completed_check(self):
        args = arguments(Path("unused")); args.watch = True; args.poll_minutes = 15
        with patch.object(updater, "update_once", return_value={"generated": False}), \
             patch.object(updater.time, "sleep", side_effect=KeyboardInterrupt), \
             patch.object(updater, "log") as log:
            updater.run_command(args)
        self.assertIn("Weather updater stopped; live catalogue preserved",
                      [call.args[0] for call in log.call_args_list])


class RunValidationTests(unittest.TestCase):
    def test_catalogue_requires_pressure_as_the_tenth_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = catalogue(OLD)
            value["fields"].pop("pressure_msl")
            (root / "latest.json").write_text(json.dumps(value), encoding="utf-8")
            with patch.object(updater, "log") as log:
                self.assertIsNone(updater.read_catalogue(root))
            self.assertIn("Expected all required fields", log.call_args.args[0])

    def test_missing_required_field_directory_is_an_explicit_schema_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = create_recognised_run(
                Path(temporary), OLD, set(updater.FIELD_PATHS) - {"pressure_msl"}
            )
            with patch.object(updater, "validate_field", return_value={}), \
                 patch.object(core, "field_catalog_entry", return_value={}):
                with self.assertRaisesRegex(ValueError, "missing required pressure_msl"):
                    updater.validate_run(directory, verify_png=False)

    def test_unrecognised_content_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "20260101T06Z"; directory.mkdir()
            (directory / "unexpected.txt").write_text("not generated")
            with self.assertRaisesRegex(ValueError, "unrecognised"):
                updater.validate_run(directory, verify_png=False)


class PromotionTests(unittest.TestCase):
    def test_schema_artifact_identity_changes_with_required_fields(self):
        current = updater.schema_artifact_name("20260101T06Z")
        with patch.dict(updater.FIELD_PATHS, {"future_field": "future-field"}):
            future = updater.schema_artifact_name("20260101T06Z")
        self.assertNotEqual(current, future)
        self.assertTrue(current.startswith("20260101T06Z-fields-"))

    def test_completed_schema_artifact_is_published_after_interrupted_pointer_update(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = create_recognised_run(root, NEW, set(updater.FIELD_PATHS) - {"pressure_msl"})
            artifact = updater.schema_artifact_name("20260101T06Z")
            complete_root = root / "completed"; complete_root.mkdir()
            complete = create_recognised_run(complete_root, NEW)
            complete.rename(root / artifact)
            write_legacy_catalogue(root, OLD)
            def validate(path, verify_png=True):
                if path == base:
                    raise ValueError("previous schema")
                return catalogue_for_artifact(NEW, path.name)
            with patch.object(core, "resolve_run", return_value=resolution(NEW)), \
                 patch.object(core, "build_resolved_run") as build, \
                 patch.object(updater, "validate_run", side_effect=validate), \
                 patch.object(updater, "prune_runs", return_value=[]):
                result = updater.update_once(arguments(root))
            build.assert_not_called()
            self.assertFalse(result["generated"])
            self.assertEqual(result["artifact"], artifact)
            self.assertTrue(all(entry["manifest"].startswith(f"{artifact}/")
                                for entry in updater.read_catalogue(root)["fields"].values()))

    def test_completed_published_schema_transaction_is_cleaned_on_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = updater.schema_artifact_name("20260101T06Z")
            destination = create_recognised_run(root, NEW)
            destination.rename(root / artifact)
            (root / "latest.json").write_text(
                json.dumps(catalogue_for_artifact(NEW, artifact)), encoding="utf-8"
            )
            work = root / ".20260101T06Z-update-building"; work.mkdir()
            (work / ".meridian-update").write_text("20260101T06Z")
            (work / "latest.json").write_text("{}")
            with patch.object(updater, "validate_run",
                              return_value=catalogue_for_artifact(NEW, artifact)):
                updater.cleanup_completed_transaction(root, "20260101T06Z")
            self.assertTrue((root / artifact).exists()); self.assertFalse(work.exists())

    def test_windows_busy_rename_copies_revalidates_and_removes_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / ".work" / "20260101T06Z"
            source.mkdir(parents=True); (source / "asset").write_text("complete")
            destination = root / "20260101T06Z"
            with patch.object(updater.os, "replace", side_effect=PermissionError("busy")), \
                 patch.object(updater.time, "sleep"), \
                 patch.object(updater, "publication_copy",
                              wraps=updater.publication_copy) as clone, \
                 patch.object(updater, "validate_run", return_value=catalogue(NEW)) as validate:
                updater.promote_run(source, destination, root, "20260101T06Z")
            self.assertEqual((destination / "asset").read_text(), "complete")
            self.assertFalse((destination / ".meridian-publishing").exists())
            self.assertFalse(source.exists()); validate.assert_called_once_with(destination)
            self.assertGreater(clone.call_count, 0)

    def test_atomic_catalogue_publication_retries_a_windows_file_share(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(core, "write_json_atomically",
                              side_effect=[PermissionError("busy"), None]) as write, \
                 patch.object(updater.os, "name", "nt"), \
                 patch.object(updater.time, "sleep") as sleep:
                updater.publish_catalogue(root, catalogue(NEW))
            self.assertEqual(write.call_count, 2)
            sleep.assert_called_once_with(1)

    def test_marked_interrupted_copy_resumes_without_renaming(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / ".work" / "20260101T06Z"
            source.mkdir(parents=True); (source / "asset").write_text("complete")
            destination = root / "20260101T06Z"; destination.mkdir()
            (destination / ".meridian-publishing").write_text("20260101T06Z")
            with patch.object(updater.os, "replace") as rename, \
                 patch.object(updater, "validate_run", return_value=catalogue(NEW)):
                updater.promote_run(source, destination, root, "20260101T06Z")
            rename.assert_not_called(); self.assertEqual((destination / "asset").read_text(), "complete")
            self.assertFalse((destination / ".meridian-publishing").exists())


class RecoveryAndRetentionTests(unittest.TestCase):
    def test_interrupted_staging_discards_partial_pressure_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / ".20260101T06Z-update-building"; work.mkdir()
            (work / ".meridian-update").write_text("20260101T06Z")
            run = work / "20260101T06Z"
            pressure = run / "pressure-msl"; (pressure / "tiles").mkdir(parents=True)
            (pressure / "manifest.json").write_text("{}")
            def validate(_directory, field_id, _date, verify_png=True):
                if field_id == "pressure_msl":
                    raise ValueError("partial pressure")
                return {}
            with patch.object(updater, "validate_field", side_effect=validate):
                updater.repair_staging(work, "20260101T06Z")
            self.assertFalse(pressure.exists())
            self.assertTrue((work / ".meridian-update").exists())

    def test_interrupted_staging_discards_only_incomplete_generated_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / ".20260101T06Z-update-building"; work.mkdir()
            (work / ".meridian-update").write_text("20260101T06Z")
            run = work / "20260101T06Z"
            (run / "tiles").mkdir(parents=True)
            field = run / "cloud-cover"; (field / "tiles").mkdir(parents=True)
            def validate(_directory, field_id, _date, verify_png=True):
                if field_id == "cloud_cover": raise ValueError("partial")
                return {}
            with patch.object(updater, "validate_field", side_effect=validate):
                updater.repair_staging(work, "20260101T06Z")
            self.assertTrue((run / "tiles").exists()); self.assertFalse(field.exists())
            self.assertTrue((work / ".meridian-update").exists())

    def test_marked_stale_generated_transaction_is_pruned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / ".20251231T18Z-update-building"; work.mkdir()
            (work / ".meridian-update").write_text("20251231T18Z")
            generated = work / "20251231T18Z"; (generated / "tiles").mkdir(parents=True)
            (generated / "manifest.json").write_text("{}")
            (generated / "validation.json").write_text("{}")
            removed = updater.prune_stale_transactions(root, "20260101T00Z")
            self.assertEqual(removed, ["20251231T18Z"]); self.assertFalse(work.exists())

    def test_unmarked_nonempty_staging_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); write_catalogue(root, OLD)
            work = root / ".20260101T06Z-update-building"; work.mkdir(); (work / "unknown").write_text("keep")
            with patch.object(core, "resolve_run", return_value=resolution(NEW)):
                with self.assertRaises(ValueError): updater.update_once(arguments(root))
            self.assertTrue((work / "unknown").exists())
            self.assertEqual(updater.read_catalogue(root)["fields"]["precipitation"]["runTime"], iso(OLD))

    def test_retention_keeps_current_and_one_previous_complete_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            oldest = datetime(2025, 12, 31, 12, tzinfo=timezone.utc)
            previous = datetime(2025, 12, 31, 18, tzinfo=timezone.utc)
            old_dir = create_recognised_run(root, oldest)
            prior_dir = create_recognised_run(root, previous)
            current_dir = create_recognised_run(root, OLD)
            write_catalogue(root, OLD)
            def valid(path, verify_png=True):
                if path.name == prior_dir.name: return catalogue(previous)
                raise ValueError("not complete")
            with patch.object(updater, "validate_run", side_effect=valid):
                removed = updater.prune_runs(root)
            self.assertEqual(removed, [old_dir.name]); self.assertFalse(old_dir.exists())
            self.assertTrue(prior_dir.exists()); self.assertTrue(current_dir.exists())

    def test_retention_never_considers_current_or_newer_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); current = create_recognised_run(root, OLD)
            newer = create_recognised_run(root, NEW); write_catalogue(root, OLD)
            with patch.object(updater, "validate_run", side_effect=ValueError("none")):
                self.assertEqual(updater.prune_runs(root), [])
            self.assertTrue(current.exists()); self.assertTrue(newer.exists())


if __name__ == "__main__":
    unittest.main()
