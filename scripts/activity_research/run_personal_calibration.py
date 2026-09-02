from __future__ import annotations

import argparse
from pathlib import Path

from personal_calibration_experiment import run_personal_calibration_experiment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a bounded private Meridian terrain and movement-calibration experiment."
    )
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--ingestion-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--sample-count", type=int, default=32)
    arguments = parser.parse_args()
    export_root = arguments.export_root.resolve()
    ingestion_root = arguments.ingestion_root.resolve()
    output_root = arguments.output_root.resolve()
    if not (export_root / "activities.csv").is_file() or not (export_root / "activities").is_dir():
        parser.error("export root must contain activities.csv and activities/")
    if not (ingestion_root / "activity-summaries.json").is_file():
        parser.error("ingestion root must contain activity-summaries.json")
    if export_root == output_root or export_root in output_root.parents:
        parser.error("output root must not be inside the immutable source export")
    results = run_personal_calibration_experiment(
        export_root,
        ingestion_root,
        output_root,
        max(10, min(60, arguments.sample_count)),
    )
    print(f"Prepared {results['selection']['prepared_count']} selected activities")
    print(f"Terrain tiles: {results['dem']['required_tiles']}")
    print(f"Source archive unchanged: {results['source_archive_unchanged']}")
    print(f"Private report: {output_root / 'report-private.md'}")


if __name__ == "__main__":
    main()
