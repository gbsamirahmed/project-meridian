# Meridian Earth terrain AOI pipeline

This directory contains offline, config-driven tooling for bounded terrain-source discovery and extraction. It does not change the Journey/Forecast application or prepare Unreal assets.

Large inputs and outputs belong in the sibling `meridian-data` workspace. Create an isolated environment there and install the pinned requirements:

```powershell
py -m venv ..\meridian-data\earth-lab\.venv
..\meridian-data\earth-lab\.venv\Scripts\python.exe -m pip install -r scripts\earth_lab\requirements.txt
```

Run an AOI from the repository root:

```powershell
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\run_terrain_aoi.py --aoi scripts\earth_lab\aois\tryfan-001.json --data-root ..\meridian-data\earth-lab\tryfan-001
```

The runner queries bounded DataMapWales historic and national tile catalogues, selects the finest DTM resolution and then the newest survey when resolutions tie, and refuses to substitute the national model if a genuinely finer historic source wins. For the national source it reads only the configured AOI from the official DTM and DSM Cloud Optimized GeoTIFFs. Missing pixels remain nodata. It writes local rasters, catalogue snapshots, a runtime manifest, an elevation preview, and an analytical hillshade under the supplied data root.

The current extraction adapter handles the national COG. A future AOI whose best source is a finer historic tiled ZIP stops after discovery so that archive layout can be reviewed explicitly rather than silently falling back.

Run the synthetic, network-free tests:

```powershell
..\meridian-data\earth-lab\.venv\Scripts\python.exe -m unittest discover -s scripts\earth_lab -p "test_*.py"
```
