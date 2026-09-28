from __future__ import annotations

import argparse
import json
from pathlib import Path

from unreal_landscape import LandscapeSettings, build_landscape_import


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a Meridian Earth AOI into validated Unreal Landscape heightmaps."
    )
    parser.add_argument("--terrain-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--components-per-axis", type=int, default=16)
    parser.add_argument("--vertical-origin-m-odn", type=float, default=650.0)
    parser.add_argument("--unreal-z-scale", type=float, default=150.0)
    arguments = parser.parse_args()
    quads_per_component = 63 * 2
    settings = LandscapeSettings(
        output_vertices=arguments.components_per_axis * quads_per_component + 1,
        components_per_axis=arguments.components_per_axis,
        vertical_origin_m_odn=arguments.vertical_origin_m_odn,
        unreal_z_scale=arguments.unreal_z_scale,
    )
    result = build_landscape_import(
        arguments.terrain_root, arguments.output_root, settings
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
