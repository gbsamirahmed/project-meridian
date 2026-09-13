from __future__ import annotations

import argparse
import json
from pathlib import Path

from terrain_aoi import load_aoi, run


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query official Welsh LiDAR catalogues and extract one bounded terrain AOI."
    )
    parser.add_argument("--aoi", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    arguments = parser.parse_args()
    result = run(load_aoi(arguments.aoi), arguments.data_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
