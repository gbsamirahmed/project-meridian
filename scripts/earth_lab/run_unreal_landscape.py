from __future__ import annotations

import argparse
import json
from pathlib import Path

from unreal_landscape import build_landscape_import


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a Meridian Earth AOI into validated Unreal Landscape heightmaps."
    )
    parser.add_argument("--terrain-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args()
    result = build_landscape_import(arguments.terrain_root, arguments.output_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
