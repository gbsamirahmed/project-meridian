# High-resolution terrain research

This directory contains offline research tooling for comparing route-relevant analytical terrain sources. It does not change Meridian's production terrain, route timing, MapLibre rendering, or weather behaviour.

The Welsh experiment reads the official [DataMapWales LiDAR DTM](https://datamap.gov.wales/maps/lidar-data-download/) from its externally hosted national Cloud Optimized GeoTIFF. The England experiment uses the official [Environment Agency LIDAR Composite DTM 1m](https://environment.data.gov.uk/dataset/13787b9a-26a4-4775-8523-806d13af58fc) through bounded WCS 2.0.1 numerical subsets. Both are bare-earth terrain models in British National Grid and are published under the Open Government Licence; both can still contain survey, filtering, surface-removal, bridge, or processing artefacts.

Install the isolated research requirements:

```powershell
py -m pip install -r scripts/terrain_research/requirements.txt
```

Run the Welsh DTM experiment with private input and output paths supplied explicitly:

```powershell
py scripts/terrain_research/run_wales_terrain_experiment.py --gpx-root <private-gpx-directory> --output-root <new-private-output-directory> --repo-root <meridian-repository>
```

The runner first verifies a 16 KiB HTTP range request against the official DataMapWales national DTM COG. It then caches only 256 × 256 blocks intersecting the selected route corridors, with an explicit 1 GB/5,000-block limit. It refuses private inputs or outputs inside the Git worktree.

Run the England generalisation experiment with the private Welsh result supplied
for cross-region comparison:

```powershell
py scripts/terrain_research/run_england_terrain_experiment.py --gpx-root <private-gpx-directory> --output-root <new-private-output-directory> --repo-root <meridian-repository> --wales-results <private-wales-results.json>
```

The England runner verifies the current WCS coverage metadata and a 10 × 10 m
Float32 GeoTIFF subset before requesting terrain. It uses fixed 1,024 m blocks,
bounded retries, conservative request pacing, a 64-block per-route limit, a
320-block aggregate limit, and a 750 MB byte/cache limit. The WCS and data reuse
remain subject to the DSP fair-use policy, dataset attribution, and OGL terms.

Generated rasters, caches, route profiles, reports and plots belong outside Git. Tests use only synthetic terrain and geometry:

```powershell
py -m unittest discover -s scripts/terrain_research -p "test_*.py"
```
