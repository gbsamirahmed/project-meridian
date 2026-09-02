from __future__ import annotations

import argparse
from pathlib import Path

from archive_analysis import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inventory and privately summarize an offline Strava export."
    )
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--mode", choices=("sample", "full"), default="sample")
    parser.add_argument("--sample-size", type=int, default=18)
    arguments = parser.parse_args()
    if not (arguments.export_root / "activities.csv").is_file():
        parser.error("export root does not contain activities.csv")
    if not (arguments.export_root / "activities").is_dir():
        parser.error("export root does not contain an activities directory")
    result = run_analysis(
        arguments.export_root.resolve(),
        arguments.output_root.resolve(),
        arguments.mode,
        max(1, arguments.sample_size),
    )
    aggregate = result["aggregate"]
    print(
        "Analysis complete:",
        f"{aggregate['usable_timestamped_gps_count']}/"
        f"{aggregate['parsed_recording_count']} recordings with usable timestamped GPS",
    )
    print("Private report:", result["report_path"])


if __name__ == "__main__":
    main()
