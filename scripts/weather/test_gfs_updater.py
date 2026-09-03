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


def write_catalogue(root, value):
    (root / "latest.json").write_text(json.dumps(catalogue(value)), encoding="utf-8")


def arguments(root):
    return argparse.Namespace(output_root=root, hours="1-24", run=None, candidate_count=12,
        reference_time=None, keep_downloads=False, watch=False, poll_minutes=60,
        check_only=False)


def resolution(value):
    return SimpleNamespace(run_time=value, date=value.date(), cycle=value.hour,
                           timesteps=(), cloud_records=(), wind_records=(),
                           temperature_records=(), checked_candidates=())


def create_recognised_run(root, value):
    directory = root / value.strftime("%Y%m%dT%HZ")
    for field_id, subdir in updater.FIELD_PATHS.items():
        field_dir = directory / subdir
        field_dir.mkdir(parents=True, exist_ok=True)
        manifest = {"model": "NOAA GFS", "product": "pgrb2.0p25", "runTime": iso(value),
                    "field": {"id": field_id}}
        (field_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (field_dir / "validation.json").write_text("{}", encoding="utf-8")
        (field_dir / "tiles").mkdir()
    return directory


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
            self.assertEqual(events, ["build", "validate", "validate", "publish"])
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
    def test_unrecognised_content_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "20260101T06Z"; directory.mkdir()
            (directory / "unexpected.txt").write_text("not generated")
            with self.assertRaisesRegex(ValueError, "unrecognised"):
                updater.validate_run(directory, verify_png=False)


class PromotionTests(unittest.TestCase):
    def test_windows_busy_rename_copies_revalidates_and_removes_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / ".work" / "20260101T06Z"
            source.mkdir(parents=True); (source / "asset").write_text("complete")
            destination = root / "20260101T06Z"
            with patch.object(updater.os, "replace", side_effect=PermissionError("busy")), \
                 patch.object(updater.time, "sleep"), \
                 patch.object(updater, "validate_run", return_value=catalogue(NEW)) as validate:
                updater.promote_run(source, destination, root, "20260101T06Z")
            self.assertEqual((destination / "asset").read_text(), "complete")
            self.assertFalse((destination / ".meridian-publishing").exists())
            self.assertFalse(source.exists()); validate.assert_called_once_with(destination)

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
