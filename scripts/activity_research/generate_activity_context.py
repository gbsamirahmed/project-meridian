from __future__ import annotations

import argparse
from pathlib import Path

from activity_context_builder import build_activity_context


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a frozen private activity-context annotation catalogue."
    )
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--research-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--fallback-cache", type=Path, action="append", default=[])
    parser.add_argument("--max-dem-tiles", type=int, default=8_000)
    arguments = parser.parse_args()
    research_root = arguments.research_root.resolve()
    cache_root = (
        arguments.cache_root.resolve()
        if arguments.cache_root
        else research_root / "dem-cache" / "activity-context-terrarium-z15"
    )
    result = build_activity_context(
        arguments.export_root,
        research_root,
        arguments.repo_root,
        cache_root,
        arguments.fallback_cache,
        max(1, arguments.max_dem_tiles),
    )
    diagnostics = result["diagnostics"]
    print(f"Private CSV: {result['output_csv']}")
    print(f"Rows: {diagnostics['row_count']}")
    print(f"Recordings analysed: {diagnostics['recordings_successfully_analysed']}")
    print(f"Terrain-enriched rows: {diagnostics['terrain_enriched_row_count']}")
    print(f"DEM tiles downloaded: {diagnostics['dem']['downloaded_tiles']}")


if __name__ == "__main__":
    main()
