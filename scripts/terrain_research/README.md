# High-resolution terrain research

This directory contains offline research tooling for comparing route-relevant analytical terrain sources. It does not change Meridian's production terrain, route timing, MapLibre rendering, or weather behaviour.

The Welsh experiment reads the official [DataMapWales LiDAR DTM](https://datamap.gov.wales/maps/lidar-data-download/) from its externally hosted national Cloud Optimized GeoTIFF. The source is a bare-earth terrain model in British National Grid and is published under the Open Government Licence; it may still contain residual vegetation, bridge-deck, or processing artefacts.

Install the isolated research requirements:

```powershell
py -m pip install -r scripts/terrain_research/requirements.txt
```

Run the Welsh DTM experiment with private input and output paths supplied explicitly:

```powershell
py scripts/terrain_research/run_wales_terrain_experiment.py --gpx-root <private-gpx-directory> --output-root <new-private-output-directory> --repo-root <meridian-repository>
```

The runner first verifies a 16 KiB HTTP range request against the official DataMapWales national DTM COG. It then caches only 256 × 256 blocks intersecting the selected route corridors, with an explicit 1 GB/5,000-block limit. It refuses private inputs or outputs inside the Git worktree.

Generated rasters, caches, route profiles, reports and plots belong outside Git. Tests use only synthetic terrain and geometry:

```powershell
py -m unittest discover -s scripts/terrain_research -p "test_*.py"
```
