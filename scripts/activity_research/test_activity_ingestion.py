from __future__ import annotations

import gzip
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from archive_analysis import inventory_export
from evidence import explicit_pause_intervals, interpret_recording_states, terrain_requests
from models import ActivitySample, NormalizedActivity, RecordingEvent, RecordingState
from parsers import (
    detect_recording_format,
    merge_same_timestamp_samples,
    parse_recording,
    recording_key,
)


GPX = """<?xml version="1.0"?>
<gpx creator="Synthetic" xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
  <trk><trkseg>
    <trkpt lat="51.0" lon="-3.0"><ele>100</ele><time>2026-01-01T00:00:00Z</time>
      <extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>120</gpxtpx:hr></gpxtpx:TrackPointExtension></extensions>
    </trkpt>
    <trkpt lat="51.0001" lon="-3.0001"><time>2026-01-01T00:00:05Z</time></trkpt>
  </trkseg></trk>
</gpx>
"""

TCX = """<?xml version="1.0"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities><Activity Sport="Running"><Lap StartTime="2026-01-01T00:00:00Z">
    <TotalTimeSeconds>10</TotalTimeSeconds><DistanceMeters>20</DistanceMeters><Track>
      <Trackpoint><Time>2026-01-01T00:00:00Z</Time><Position><LatitudeDegrees>51</LatitudeDegrees><LongitudeDegrees>-3</LongitudeDegrees></Position></Trackpoint>
      <Trackpoint><Time>2026-01-01T00:00:10Z</Time><Position><LatitudeDegrees>51.0001</LatitudeDegrees><LongitudeDegrees>-3.0001</LongitudeDegrees></Position><HeartRateBpm><Value>130</Value></HeartRateBpm></Trackpoint>
    </Track>
  </Lap></Activity></Activities>
</TrainingCenterDatabase>
"""


def sample(index: int, seconds: int, latitude: float | None, longitude: float | None) -> ActivitySample:
    return ActivitySample(
        index=index,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds),
        latitude=latitude,
        longitude=longitude,
    )


class ActivityIngestionTests(unittest.TestCase):
    def test_compound_extension_detection_and_recording_keys(self) -> None:
        self.assertEqual(detect_recording_format("123.fit.gz"), ".fit.gz")
        self.assertEqual(detect_recording_format("123.GPX.GZ"), ".gpx.gz")
        self.assertEqual(detect_recording_format("123.tcx"), ".tcx")
        self.assertEqual(detect_recording_format("notes.zip"), ".zip")
        self.assertEqual(recording_key("123.fit.gz"), "123")

    def test_gpx_and_gz_parse_with_optional_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plain = root / "one.gpx"
            compressed = root / "two.gpx.gz"
            plain.write_text(GPX, encoding="utf-8")
            with gzip.open(compressed, "wt", encoding="utf-8") as stream:
                stream.write(GPX)
            for path in (plain, compressed):
                activity = parse_recording(path)
                self.assertEqual(len(activity.samples), 2)
                self.assertEqual(activity.samples[0].heart_rate_bpm, 120)
                self.assertIsNone(activity.samples[1].recorded_altitude_m)
                self.assertEqual(len(terrain_requests(activity)), 2)

    def test_tcx_gz_parses_timestamped_gps_lap_and_heart_rate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "one.tcx.gz"
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                stream.write(TCX)
            activity = parse_recording(path)
            self.assertEqual(len(activity.samples), 2)
            self.assertEqual(activity.samples[1].heart_rate_bpm, 130)
            self.assertEqual(len(activity.laps), 1)

    def test_malformed_xml_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.gpx"
            path.write_text("<gpx><trk>", encoding="utf-8")
            with self.assertRaises(Exception):
                parse_recording(path)

    def test_stationary_movement_anomaly_gap_and_timestamp_order(self) -> None:
        activity = NormalizedActivity(Path("synthetic.gpx"), ".gpx")
        activity.samples = [
            sample(0, 0, 51.0, -3.0),
            sample(1, 1, 51.0, -3.0),
            sample(2, 2, 51.0001, -3.0),
            sample(3, 3, 52.0, -3.0),
            sample(4, 120, 52.0001, -3.0),
            sample(5, 119, 52.0002, -3.0),
        ]
        states = [segment.state for segment in interpret_recording_states(activity)]
        self.assertEqual(
            states,
            [
                RecordingState.STATIONARY,
                RecordingState.MOVEMENT,
                RecordingState.ANOMALOUS,
                RecordingState.RECORDING_GAP,
                RecordingState.ANOMALOUS,
            ],
        )

    def test_slow_continuous_progression_is_not_stationary(self) -> None:
        activity = NormalizedActivity(Path("slow.gpx"), ".gpx")
        activity.samples = [
            sample(0, 0, 51.0, -3.0),
            sample(1, 5, 51.000018, -3.0),
        ]
        evidence = interpret_recording_states(activity)
        self.assertEqual(evidence[0].state, RecordingState.MOVEMENT)

    def test_missing_optional_gps_is_uncertain(self) -> None:
        activity = NormalizedActivity(Path("synthetic.fit"), ".fit")
        activity.samples = [sample(0, 0, None, None), sample(1, 1, 51, -3)]
        evidence = interpret_recording_states(activity)
        self.assertEqual(evidence[0].state, RecordingState.UNCERTAIN)

    def test_complementary_same_timestamp_fit_records_are_merged(self) -> None:
        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = ActivitySample(0, timestamp, 51, -3, device_distance_m=None)
        second = ActivitySample(1, timestamp, None, None, device_distance_m=100)
        third = ActivitySample(2, timestamp, 52, -3, device_distance_m=100)
        merged, merge_count, conflict_count = merge_same_timestamp_samples(
            [first, second, third]
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].device_distance_m, 100)
        self.assertEqual(merged[0].latitude, 51)
        self.assertEqual(merge_count, 2)
        self.assertEqual(conflict_count, 1)

    def test_explicit_pause_is_separate_from_timestamp_gap(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        activity = NormalizedActivity(Path("synthetic.fit"), ".fit")
        activity.samples = [sample(0, 0, 51, -3), sample(1, 20, 51.0001, -3)]
        activity.events = [
            RecordingEvent(start + timedelta(seconds=2), "timer", "stop_all"),
            RecordingEvent(start + timedelta(seconds=18), "timer", "start"),
        ]
        self.assertEqual(len(explicit_pause_intervals(activity)), 1)
        self.assertEqual(
            interpret_recording_states(activity)[0].state,
            RecordingState.EXPLICIT_PAUSE,
        )

    def test_csv_association_and_multiple_representations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            activities = root / "activities"
            activities.mkdir()
            (activities / "1.gpx").write_text(GPX, encoding="utf-8")
            (activities / "1.fit").write_bytes(b"synthetic")
            (activities / "2.gpx").write_text(GPX, encoding="utf-8")
            (root / "activities.csv").write_text(
                "Activity ID,Activity Date,Activity Type,Filename\n"
                '1,"Jan 1, 2026, 1:00:00 PM",Run,activities/1.gpx\n'
                '3,"Jan 2, 2026, 1:00:00 PM",Hike,activities/3.gpx\n',
                encoding="utf-8",
            )
            inventory = inventory_export(root)
            self.assertEqual(inventory["catalogue_rows"], 2)
            self.assertEqual(inventory["missing_referenced_files"], ["activities/3.gpx"])
            self.assertEqual(
                inventory["unassociated_recording_files"],
                ["activities/1.fit", "activities/2.gpx"],
            )
            self.assertEqual(len(inventory["multiple_recordings_by_key"]), 1)


if __name__ == "__main__":
    unittest.main()
