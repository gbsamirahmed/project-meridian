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


## Lab 002: Unreal Landscape preparation

Convert an extracted AOI to Unreal-ready DTM and DSM heightmaps:

```powershell
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\run_unreal_landscape.py --terrain-root ..\meridian-data\earth-lab\tryfan-001 --output-root ..\meridian-data\earth-lab\tryfan-001\unreal-landscape-v1
```

The converter refuses missing cells and repository-local output. It bilinearly resamples
the full 2000 x 2000 m AOI from 2000 x 2000 source cells to Unreal's recommended
2017 x 2017 Landscape layout. It emits verified 16-bit PNG and little-endian R16 files
plus a runtime manifest with source bounds, coordinate reconstruction, dimensions,
scales, hashes, elevation ranges, and round-trip error. DTM is the default; DSM is
retained as an alternative measured surface.

Prepare a minimal external Unreal project and an exact import guide:

```powershell
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\prepare_unreal_project.py --manifest ..\meridian-data\earth-lab\tryfan-001\unreal-landscape-v1\unreal-landscape-manifest.json --project-root ..\meridian-data\earth-lab\tryfan-001\unreal-project\TryfanLab002
```

Open the generated `TryfanLab002.uproject` and follow its `IMPORT.md`. The generated
project includes an in-editor validator at `Content/Python/validate_landscape.py`.
Open `/Game/Tryfan_Lab002_Corrected`, then use **Execute Python Script** on that file.
Under UE 5.8 it enumerates actors through `EditorActorSubsystem`. A normal level is
validated from the components and bounds owned directly by its root `Landscape`;
a World Partition level remains supported through linked `LandscapeStreamingProxy`
actors. The validator traces nine interior collision heights against the canonical
R16 and checks the AOI centre, Tryfan summit reference, nearby DTM peak and AOI high
point at their BNG-derived world positions. Results use PASS, FAIL and UNVERIFIED
and are written to `Saved/meridian-landscape-validation.json`; a failure never
mutates the Landscape.

The accepted Lab 002 level is `/Game/Tryfan_Lab002_Corrected`: one normal Landscape,
no streaming proxies, location `(-100000,-100000,0)` cm, zero rotation and scale
`(99.206349206,99.206349206,150)`. Its UE 5.8.2 report is OVERALL PASS for topology,
2 km extent, registration and imported collision-height agreement. Generated
heightmaps, projects, editor caches, reports and screenshots stay under
`meridian-data` and are not committed.
