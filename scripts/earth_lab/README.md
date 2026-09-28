# Meridian Earth terrain AOI pipeline

This directory contains offline, config-driven tooling for bounded terrain-source discovery and extraction. It does not change the Journey/Forecast application or prepare Unreal assets.

Large inputs and outputs belong outside Git under `MERIDIAN_DATA_ROOT`. The default
remains the historical sibling `meridian-data` workspace, so the commands below
continue to reproduce the frozen Labs without rewriting their configs or provenance.
Set an absolute `MERIDIAN_DATA_ROOT` for root-aware tooling such as the Tryfan
Reference Renderer bootstrap. Historical Lab entry points that still accept explicit
paths retain the documented sibling paths until the controlled Phase 4 migration;
the environment variable does not silently rewrite an entry point that does not use
the shared resolver.

Private activities, personal routes and exports belong under the separate
`MERIDIAN_PRIVATE_ROOT`. No historical Earth Lab requires that root.

Create an isolated environment in the current data workspace and install the pinned requirements:

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

## Lab 003: geospatial observer placement

`unreal_place_observer.py` places a reusable editor camera from British National Grid
coordinates without changing the Landscape. Project preparation copies it and the
pure `observer_geometry.py` helpers into `Content/Python` as `place_observer.py` and
`observer_geometry.py`.

For the benchmark, open `/Game/Tryfan_Lab002_Corrected` and run
`Content/Python/place_observer.py` with **Tools → Execute Python Script**. It traces
the existing Landscape at observer E266100/N360200 and target E266405/N359387,
places the camera optical point 1.70 m above the observer surface, then derives the
full yaw and pitch needed to face the traced summit terrain point. Both traces ignore
non-Landscape actors and placement aborts before actor changes if either coordinate
has no Landscape hit. A small non-colliding sphere marks the observer ground point.
Actors are reused by label: `Meridian_Lab003_Observer_Camera` and
`Meridian_Lab003_Observer_Ground_Marker`. The script does not save the level.

For another target pair, import `place_observer` in Unreal's Python console and call:

```python
place_observer.place_observer(
    266100,
    360200,
    target_easting=266405,
    target_northing=359387,
    eye_height_m=1.70,
)
```

Heading-only mode remains available for reusable placement without a terrain target:

```python
place_observer.place_observer(266100, 360200, 157, eye_height_m=1.70)
```

The utility reads the BNG origin from the external runtime manifest. It maps east to
+X and south to +Y in centimetres. Target mode calculates geographic bearing, UE yaw
and UE pitch from the two traced 3D points; heading-only mode uses
`yaw = heading - 90°` normalized to `[-180°, 180°)` and zero pitch. The camera uses a
constrained 16:9 aspect ratio and Unreal's 60° **horizontal** perspective FOV, which
implies a 35.983° vertical FOV. A generated report containing both terrain heights,
distances and orientation is written to `Saved/meridian-observer-placement.json`
outside Git.

## Lab 004: expanded Tryfan photographic benchmark

Lab 004 is a separate 3 x 3 km AOI centred on the established BNG origin E266400,
N359300. It uses bounds E264900-267900 / N357800-360800 and leaves `tryfan-001`
and the accepted Lab 002 project untouched. Run the same bounded COG workflow:

```powershell
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\run_terrain_aoi.py --aoi scripts\earth_lab\aois\tryfan-004.json --data-root ..\meridian-data\earth-lab\tryfan-004
```

Prepare the 3025 x 3025 Landscape output as 24 x 24 components (2 x 2 subsections,
63 quads per subsection):

```powershell
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\run_unreal_landscape.py --terrain-root ..\meridian-data\earth-lab\tryfan-004 --output-root ..\meridian-data\earth-lab\tryfan-004\unreal-landscape-v1 --components-per-axis 24
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\prepare_unreal_project.py --manifest ..\meridian-data\earth-lab\tryfan-004\unreal-landscape-v1\unreal-landscape-manifest.json --project-root ..\meridian-data\earth-lab\tryfan-004\unreal-project\TryfanLab004 --benchmark docs\earth-lab\tryfan-004-benchmark.json --photo-overlay docs\earth-lab\tryfan-004-photo-overlay.json
```

The 3000 source cells become 3025 vertices across the unchanged 3 km bounds: 25
samples (0.833%) are added per axis by bilinear resampling, with no crop, pad,
smoothing, erosion, noise or missing-data fill. DTM remains the canonical bare-earth
Landscape; DSM is retained only as a measured comparison surface. At 3024 quads the
XY scale is 99.206349206 cm, giving exactly 3000 m. Local zero remains BNG
E266400/N359300 at 650 m ODN, +X east, +Y south, +Z up.

Lab 004 now separates two photographic roles. **004A geometric registration** uses
Tony Edwards' 21 February 2009 Geograph photograph, whose Wikimedia record publishes
both camera and depicted-place coordinates plus a 247 degree heading. The primary
metadata is docs/earth-lab/tryfan-004-benchmark.json; the original Robert J. Heath
work is preserved in tryfan-004-benchmark-robert-heath.json as historical provenance.
**004B visual quality** remains deliberately unselected.

The project pointer makes `Content/Python/place_observer.py` load 004A automatically.
The primary photographic calibration traces the actual imported Landscape at the
published camera coordinate and fixes the optical point 1.70 m above it. The published
247 degree true heading remains source metadata. Calibration runs may set
`MERIDIAN_CAMERA_HEADING_DEGREES` to a recovered photographic centre heading; this
changes camera yaw only and retains the established local BNG grid-convergence
correction. The recovered 253.55 degree solution therefore becomes BNG grid bearing
255.141999 degrees and Unreal yaw 165.141999 degrees. Roll remains zero. Photographic
pitch and lens/FOV are not published, so calibration runs must set
`MERIDIAN_CAMERA_PITCH_DEGREES` and may set
`MERIDIAN_HORIZONTAL_FOV_DEGREES`. The configured starting HFOV is 40 degrees.

The canonical summit is still traced on every run, but only to report the geometric
reference pitch (expected about +37.3847 degrees). It does not set photographic pitch
in calibration mode. The depicted-place coordinate also remains in metadata and the
placement report as a diagnostic only: the source-DTM audit shows that it is hidden
behind Tryfan's nearer shoulder. Unreal verifies the rendered `CameraComponent` and
camera-view forward vectors after placement. Repeated execution reuses
`Meridian_Lab004_Geometric_Camera` and
`Meridian_Lab004_Geometric_Ground_Marker`. The validated Landscape is not changed.


### Lab 004A photographic reference overlay

The prepared project enables Epic's built-in Image Plate plugin and deploys
`Content/Python/restore_lab004a_camera.py`,
`Content/Python/validate_lab004a_camera.py`, and
`Content/Python/setup_photo_overlay.py`. The canonical camera comes from
`docs/earth-lab/tryfan-004-photo-overlay.json`; it is never inferred from the
photograph at restore time.

Open `/Game/Tryfan_Lab004`, then restore and persist the canonical camera:

    import unreal; exec(open(unreal.Paths.project_content_dir() + "Python/restore_lab004a_camera.py", encoding="utf-8").read(), globals())

The restore script changes only `Meridian_Lab004_Geometric_Camera`, verifies that all
Landscape transforms remain byte-for-byte equivalent in its before/after snapshot,
uses Unreal's explicit `save_map` API, and fails if the post-save in-memory camera
does not match the strict calibration. Close and reopen Unreal, open
`/Game/Tryfan_Lab004`, and verify the state freshly loaded from disk:

    import unreal; exec(open(unreal.Paths.project_content_dir() + "Python/validate_lab004a_camera.py", encoding="utf-8").read(), globals())

Only after this reports PASS, enable the overlay:

    import unreal; MERIDIAN_REFERENCE_OVERLAY_ENABLED = True; MERIDIAN_REFERENCE_OVERLAY_OPACITY = 0.5; exec(open(unreal.Paths.project_content_dir() + "Python/setup_photo_overlay.py", encoding="utf-8").read(), globals())
This imports the external 640 x 480 Tony Edwards JPEG into the external Unreal
project, creates a translucent unlit Image Plate material, and attaches a 50% opacity
`Meridian_Lab004_Photographic_Reference` plate to the verified
`Meridian_Lab004_Geometric_Camera`. The camera is already constrained to 4:3, so the
native 4:3 photograph fills that camera frame without being stretched to the editor
viewport. The script refuses to attach if the camera position, rotation, HFOV, 4:3
aspect, or aspect constraint differs from the fixed Lab 004A calibration.

Toggle it off or on by rerunning the same script with:

    import unreal; MERIDIAN_REFERENCE_OVERLAY_ENABLED = False; exec(open(unreal.Paths.project_content_dir() + "Python/setup_photo_overlay.py", encoding="utf-8").read(), globals())
    import unreal; MERIDIAN_REFERENCE_OVERLAY_ENABLED = True; exec(open(unreal.Paths.project_content_dir() + "Python/setup_photo_overlay.py", encoding="utf-8").read(), globals())

Set opacity from 0 to 1 with `MERIDIAN_REFERENCE_OVERLAY_OPACITY`; for example:

    import unreal; MERIDIAN_REFERENCE_OVERLAY_ENABLED = True; MERIDIAN_REFERENCE_OVERLAY_OPACITY = 0.25; exec(open(unreal.Paths.project_content_dir() + "Python/setup_photo_overlay.py", encoding="utf-8").read(), globals())

The utility never changes the camera, Landscape, terrain, lighting, or atmosphere.
It writes a diagnostic report to `Saved/meridian-photo-overlay.json`. Save the level
if the Image Plate actor should persist; otherwise rerun the script after reopening.
### Lab 004A geographic diagnosis

Before changing camera or rendering parameters, run the source-DTM visibility audit:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\diagnose_photo_geometry.py --terrain-root ..\meridian-data\earth-lab\tryfan-004 --benchmark docs\earth-lab\tryfan-004-benchmark.json --output-root ..\meridian-data\earth-lab\tryfan-004\diagnostics\lab004a-geography

The script reads the 1 m source DTM without changing it. It writes a north-up plan
map, three elevation profiles, and a machine-readable line-of-sight report outside
Git. Published-heading, depicted-place, and canonical-summit rays remain separate.
The report treats Geograph subject coordinates as approximate primary-subject
locations rather than summit or image-centre measurements.

### Lab 004A DTM skyline calibration

The fixed-camera photographic calibration is reproducible from the source 1 m DTM:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\calibrate_photo_skyline.py --terrain-root ..\meridian-data\earth-lab\tryfan-004 --benchmark docs\earth-lab\tryfan-004-benchmark.json --image ..\meridian-data\earth-lab\tryfan-004\reference\tryfan-tony-edwards-2009.jpg --output-root ..\meridian-data\earth-lab\tryfan-004\diagnostics\lab004a-skyline

The extractor follows the bright-sky/dark-terrain boundary and explicitly down-weights
normalized image x=0.275–0.475, where cloud obscures the summit. DTM rays advance at
1 m with 0.025 degree angular spacing. For every heading/HFOV pair, pitch is solved as
vertical registration and the objective measures both residual angular shape and
slope; a simple vertical offset cannot by itself produce a good score.

The best fixed-camera solution is true heading 253.55 degrees, horizontal FOV 35.20
degrees and pitch +30.3418 degrees. Weighted angular RMSE is 0.5479 degrees and shape
correlation is 0.9621. Excluding every cloud-affected column recovers the same heading
and HFOV. By comparison, fixing the published 247 degree heading gives 2.0583 degrees
RMSE and a 2.64-times worse shape score even at its best FOV. The recovered framing
places the canonical summit near image x=197, left of centre and within the clouded
section, while the nearer northern shoulder and continuing ridge explain the observed
right-hand extent.

This supports retaining Tony Edwards as Lab 004A with a recovered photographic
calibration. The Geograph heading is useful but approximate by about 6.55 degrees.
Cloud prevents validation of the summit outline itself, and the bare-earth DTM cannot
reproduce rocks, vegetation or sub-metre crag silhouettes. The fixed-camera match is
strong enough that no camera-position perturbation search was run. Generated overlays,
residuals, heatmap and JSON remain outside Git under the external diagnostics folder.

### Lab 004B quantitative photographic alignment

Lab 004B measures, but does not replace, the canonical Lab 004A camera. Its tracked
configuration is `docs/earth-lab/tryfan-004b-photo-fit.json`; that file embeds a
value-for-value snapshot of the canonical 004A camera and the analysis aborts if the
snapshot differs from `tryfan-004-photo-overlay.json`.

Run the bounded analysis against the exact 3025-vertex DTM R16 imported by Unreal:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\fit_photo_alignment.py --config docs\earth-lab\tryfan-004b-photo-fit.json --output-root ..\meridian-data\earth-lab\tryfan-004\diagnostics\lab004b-photo-fit

The method SHA-verifies and decodes the final little-endian R16, extracts the same
cloud-aware photographic skyline used by 004A, and compares the full skyline and its
slope in angular/image space. It fixes roll, aspect, terrain transform and 1.70 m eye
height. Before fitting, it declares a conservative ±20 m Geograph marker envelope,
±2 degrees heading, ±3 degrees pitch and ±5 degrees HFOV. Camera Z always follows the
decoded terrain at the candidate XY; it is not an independent free parameter.

The bounded minimum moved 20 m east and 16 m north, reaching the easting bound. It
reduced angular RMSE from 0.54764 to 0.52327 degrees and the combined objective by
4.42%, but slightly worsened weighted pixel RMSE from 9.7852 to 9.8137 pixels. Clear-
sky angular RMSE improved only from 0.50494 to 0.48407 degrees. The fixed-position
sensitivity solution changed heading by only +0.05 degrees, pitch by -0.018 degrees
and HFOV by +0.025 degrees, with negligible improvement. Because the free-position
minimum is boundary-limited and does not improve pixel RMSE, no 004B Unreal camera is
promoted or deployed. Lab 004A remains the camera to inspect in Unreal.

Generated PNGs and the full JSON report remain outside Git under
`meridian-data/earth-lab/tryfan-004/diagnostics/lab004b-photo-fit`. The result supports
a strong broad terrain/photograph agreement but cannot distinguish the remaining
roughly half-degree skyline residual among Geograph marker uncertainty, automatic
skyline extraction, cloud, bare-earth representation and missing sub-metre crags.

## Lab 005A: terrain-derived surface analysis

Lab 005A is a read-only analysis of the exact SHA-verified 3025 x 3025 DTM R16
underlying the validated Lab 004 Unreal Landscape. It introduces no imagery,
land-cover, geology, hydrology, vegetation, snow, procedural detail or material
classification. Run:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\analyze_terrain_surface.py --config docs\earth-lab\tryfan-005a-surface-analysis.json

The 0.992063 m vertex grid produces slope/aspect with Horn's weighted 3 x 3
gradient. Aspect is downhill azimuth clockwise from BNG grid north and is undefined
below 0.5 degrees slope. A 5-sample separable binomial filter precedes second-
derivative curvature; Laplacian, downslope profile and horizontal plan curvature are
reported in inverse metres, with positive values defined as concave/hollow and
negative values as convex/ridge. Profile and plan curvature are undefined below one
degree slope.

Roughness is vertical RMS residual after removing a least-squares local plane. The
5, 15 and 51 sample windows cover approximately 5.0, 14.9 and 50.6 m, separating
near-cell irregularity, local terrain texture and broader landform breaks. It remains
geometry evidence rather than rock/grass/scree classification. Outputs are Float32
EPSG:27700 GeoTIFFs plus north-up diagnostic PNGs and JSON statistics under
`meridian-data/earth-lab/tryfan-004/diagnostics/lab005a-surface`; none are committed.
The complete 20-file output is deterministic and approximately 260 MB.

## Lab 005B: scalable Sentinel-2 surface evidence

Lab 005B adds independently observed surface evidence without changing Lab 004 or
Lab 005A. The tracked configuration is
`docs/earth-lab/tryfan-005b-sentinel2.json`. Run the bounded, reproducible workflow:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\analyze_surface_evidence.py --config docs\earth-lab\tryfan-005b-sentinel2.json

The official product record is CDSE Sentinel-2A Level-2A product
`S2A_MSIL2A_20260712T113331_N0512_R080_T30UVD_20260712T174812` (tile 30UVD,
12 July 2026 11:33:31 UTC, processing baseline 05.12). Three clear summer
candidates were checked against the actual Tryfan AOI with the 20 m scene
classification layer. All were cloud-free over the AOI; this one had the highest
sun elevation (58.06 degrees) and zero AOI cloud, cloud shadow, snow/ice and nodata.
CDSE remains the provenance authority. Anonymous bounded reads use the newer Earth
Search Sentinel-2 Collection-1 COG for the identical ESA product. The legacy COG
collection is deliberately not used because its post-baseline-04 offset metadata
and pixels are known to be ambiguous.

Only a 4 x 4 km native-grid window (the 3 x 3 km lab plus 500 m margin) is retained.
B02/B03/B04/B08 stay at native 10 m; B05/B06/B07/B8A/B11/B12 and SCL stay at native
20 m. These source windows remain in EPSG:32630. Reprojected analysis products use
exact 300 x 300 (10 m) and 150 x 150 (20 m) EPSG:27700 grids over the Lab AOI.
Continuous bands use bilinear reprojection and SCL uses nearest-neighbour. The
pipeline applies each STAC asset's scale/offset, masks cloud/shadow/cirrus/snow,
and leaves low-signal normalized differences undefined rather than emitting unstable
ratios.

The derived observations are NDVI, NDWI and a visible/NIR brightness proxy at 10 m,
plus NDMI, NDRE and a B11/B12 normalized contrast at 20 m. Their equations,
limitations and effective resolutions are written into the external report. Frozen
Lab 005A terrain fields are aggregated up to each Sentinel grid by area-weighted mean
and maximum; aspect is averaged circularly. Sentinel is never interpolated down to
one metre or described as one-metre evidence.

Generated native windows, aligned GeoTIFFs, five diagnostic PNGs and the full
machine-readable report are external under
`meridian-data/earth-lab/tryfan-005b/sentinel2-surface-evidence`. The workflow verifies
the canonical R16 SHA before processing and hashes every output. It introduces a
small provider-neutral `EvidenceQuery`/catalogue boundary so another AOI or future
free observation provider can use the same location/time/evidence concept without
turning this laboratory run into a global platform.

## Lab 005C: four-season Sentinel temporal evidence

Lab 005C consumes the frozen 005A terrain analysis and the frozen 005B summer
observation without modifying either. It adds three bounded Sentinel-2 Collection-1
COG subsets and compares winter, spring, summer and autumn on the same exact 10 m and
20 m EPSG:27700 grids:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\analyze_temporal_surface_evidence.py --config docs\earth-lab\tryfan-005c-temporal-evidence.json

The selected observations are 17 January 2024, 30 April 2026, the frozen 12 July
2026 reference, and 27 November 2024. Selection uses actual AOI SCL composition,
rather than tile cloud metadata alone. Cloud, cloud shadow, cirrus, invalid and
nodata classes are excluded. Genuine snow remains available as environmental
evidence, while a parallel snow-excluded view supports surface-persistence
statistics. Low-sun SCL class 2 and the terrain-derived cosine-incidence field remain
explicit illumination diagnostics; no topographic reflectance correction is applied.

Each date retains B02/B03/B04/B08 at 10 m and B05/B06/B07/B8A/B11/B12/SCL at
20 m. The Collection-1 scale 0.0001 and offset -0.1 are applied exactly as in 005B.
Natural-colour panels share one 0.02-0.30 reflectance display transform, so seasonal
brightness differences are not hidden by per-image stretching. Temporal median,
range, standard deviation and valid-count products remain at their source analysis
resolution. Diagnostic masks describe relative persistence, vegetation-related
variation, moisture-related variation, snow occurrence and illumination sensitivity;
none is a material or land-cover class.

External source subsets, aligned rasters, temporal fields, seven north-up diagnostic
figures and lab005c-report.json are written under
meridian-data/earth-lab/tryfan-005c/sentinel2-temporal-evidence. The report
SHA-verifies the canonical R16 and frozen 005B result, records every output hash and
separates snow-retained environmental statistics from snow-excluded surface
statistics. Two cached reruns must produce the same deterministic result and output
hash list.


## Lab 006: independent habitat and geological context

Lab 006 is the final evidence-gathering experiment before the first surface model.
It consumes the frozen 005A terrain and 005C temporal Sentinel reports by verified
SHA-256 and does not alter those products. Run the bounded workflow with:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\analyze_contextual_evidence.py --config docs\earth-lab\tryfan-006-contextual-evidence.json

The habitat source is Natural Resources Wales' Terrestrial Phase 1 Habitat Survey
through the official DataMapWales WFS. The retained source is an AOI-bounded GeoJSON
with all original attributes. Its field recording began in 1979 and national
lowland/upland coverage was completed during 1979-1997; DataMapWales published the
layer in 2023 under the Open Government Licence. This is independent named habitat
context, but its service metadata does not promise metre-scale positional accuracy
and it cannot be treated as a current square-metre survey. The original Phase 1
codes remain authoritative. A separate, documented broad grouping supports
cross-evidence summaries without replacing the source categories.

Geological context comes from the official BGS Geology 50K open WMS. Bedrock and
superficial-deposit map images are retained for the AOI together with bounded
GetFeatureInfo records that recover BGS unit names, lithology fields, colours,
nominal scale and release metadata. Cartographic label/boundary pixels are assigned
from the nearest already identified unit only in the derived aligned grid;
transparent superficial areas remain explicitly “no mapped deposit.” This is
1:50,000 contextual evidence under the OGL, not the separately licensed detailed
vector product and not evidence of rock texture, fractures or individual boulders.

Categorical identifiers are rasterized/reduced without interpolation onto the
existing 300 x 300 10 m and 150 x 150 20 m BNG grids. Those cell sizes are alignment
geometry, not source accuracy. The external result is under
meridian-data/earth-lab/tryfan-006/surface-context-evidence and contains cached
source subsets, aligned category GeoTIFFs, source lookup tables, six north-up
diagnostics, lab006-evidence-package.json and the complete machine report. The
evidence package keeps terrain, Sentinel, habitat and geology as separate channels,
each with source and scale metadata, so Lab 007 can query what evidence exists
without treating any one channel as final material truth.

The AOI is dominated by mapped dry heath (33.8%) and acid grassland (29.3%), with
scree (4.2%), flush/spring (4.1%), bog (2.5%) and smaller habitat contexts. The
mapped natural-rock and scree contexts are steeper than acid grassland (median
roughly 37.1 and 31.3 degrees versus 16.9 degrees), while mapped bog is gentler and
smoother (2.7 degrees; 0.07 m median ~15 m roughness). These physically sensible
relationships support using habitat as a coarse constraint, not a classifier.
The strict 005C persistent-low-NDVI mask overlaps only 2.4% of mapped rock/scree
cells (Jaccard 0.011), demonstrating scale, age and semantic disagreement that Lab
007 must retain rather than force.

BGS bedrock is varied across the small AOI: sandstone/siltstone units, Ordovician
rhyolite and microgranite intrusions, felsic tuffs and other volcaniclastic units.
Mapped superficial deposits cover about 40% of aligned cells; till (11.6%), talus
(8.6%), peat (8.3%), hummocky glacial deposits (4.5%) and head (3.9%) are the main
contexts. At the canonical Tryfan reference the aligned evidence is Phase 1 acid
dry dwarf-shrub heath over Capel Curig Volcanic Formation felsic tuff, with no
mapped superficial deposit. These units constrain broad substrate and cover
interpretation but cannot determine exposure, visual texture or sub-resolution
surface geometry.


## Lab 007: uncertain underlying surface model

Lab 007 is the first inference stage. It consumes only the frozen Lab 005A terrain,
Lab 005C temporal Sentinel and Lab 006 habitat/geology products; it verifies their
recorded hashes before processing and checks every consumed source product again
afterwards. Run it with:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\analyze_underlying_surface.py --config docs\earth-lab\tryfan-007-underlying-surface.json

The model is explicit bounded evidence fusion, not machine learning. It emits a
six-class vector (rock, scree_talus, heath, grass, wet_ground, other_unknown) for
each valid 10 m alignment cell. Terrain slope and approximately 15 m roughness
supply structural preferences. Four-season Sentinel NDVI/NDMI summaries supply
dated vegetation/moisture-related plausibility, with the strict persistent-low-NDVI
diagnostic capped at a negligible rock increment rather than used as a rock
detector. Historical NRW Phase 1 groups and BGS superficial contexts supply
categorical preferences. BGS bedrock contributes only weak broad context and cannot
establish exposure. Per-source budgets cap influence; missing families and
specificity-weighted Jensen-Shannon disagreement add positive support to
other_unknown. Final non-negative scores are normalized, and uncertainty is Shannon
entropy divided by ln(6).

Temporal character stays attached to every channel: terrain and geology are
structural/quasi-static context; NRW is historical contextual evidence surveyed in
1979-1997; Sentinel is dated dynamic observation from the four retained acquisition
dates. The model estimates broad underlying character only. It does not infer current
greenness, wetness, snow, seasonal appearance, objects, textures, fractures or
square-metre material truth. The 300 x 300 output grid is computation/alignment
geometry, not a claim that all sources have 10 m information resolution.

All 90,000 terrain cells receive a valid probability vector. Terrain, Sentinel and
BGS context cover 100%; historical habitat covers 99.48%, leaving 472 cells with
three major families. The BGS source is available everywhere: 35,982 cells have a
mapped superficial deposit and 54,018 are valid “none mapped,” which is explicitly
different from missing geology. The result is appropriately cautious. Mean normalized
entropy is 0.929 and mean other_unknown probability is 0.303; other_unknown is the
largest class in 79.14% of cells. This is low evidential confidence despite high
computational coverage, not a processing gap.

Physical tendencies remain visible without becoming deterministic labels. Mean rock
probability rises from 0.078 below 10 degrees slope to 0.139 above 60 degrees; wet
ground falls from 0.181 to 0.086. Mapped natural-rock cells average only 0.225 rock
probability, mapped scree averages 0.247 scree/talus, mapped bog averages 0.301 wet
ground, and mapped acid grassland averages 0.265 grass. BGS mapped talus averages
0.185 scree/talus and mapped peat averages 0.237 wet ground. High-conflict cells
have higher other_unknown (0.313 versus 0.265 in the low-conflict quartile).

At the canonical Tryfan point the retained evidence is steep/rough terrain
(37.31 degrees; 2.80 m approximately 15 m RMS), dated Sentinel median NDVI 0.380,
historical acid dry dwarf-shrub heath, Capel Curig Volcanic Formation felsic tuff,
and valid no mapped superficial deposit. The model returns rock 0.134, scree/talus
0.111, heath 0.240, grass 0.119, wet ground 0.080 and other/unknown 0.317, with
normalized entropy 0.934. The detailed source support and dates remain inspectable
in the canonical trace.

Generated GeoTIFFs, contribution rasters, twelve inspected diagnostic figures,
machine-readable evidence package and report are external under
meridian-data/earth-lab/tryfan-007/uncertain-underlying-surface. Two cached runs
produced deterministic result SHA-256
574ce8e07fb8752e90b149ef9c5638adcd1d5845818df608b94a65a5c75ccbc8.


## Lab 008: surface information-gap and uncertainty audit

Lab 008 audits the frozen Lab 007 result without changing its configuration, weights
or outputs. Run:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\analyze_surface_uncertainty.py --config docs\earth-lab\tryfan-008-uncertainty-audit.json

The audit SHA-verifies the frozen report, package, canonical trace and all 48 listed
Lab 007 outputs. It reconstructs the published probability fields from the stored
source contributions to within 2e-6, then performs counterfactual source removals in
a separate tryfan-008 output tree. These are information-value diagnostics, not a
replacement surface model.

Other/unknown being largest is not treated as total ignorance. Although it is
dominant in 79.14% of cells, those cells retain mean known-class probability mass
0.683 and 85.75% still have a leading meaningful class probability of at least 0.20.
The larger issue is weak separation within the meaningful classes: conditional
five-class entropy averages 0.943 and the mean top-two meaningful margin is 0.089.
Heath/grass is the leading pair in 58.89% of cells and grass/wet ground in 20.37%.
Documented overlapping pairs form a plausible, not proven, sub-grid mixture signal
in 45.13% of cells.

The deliberately diffuse Lab 007 prior already has normalized entropy 0.979. Evidence
reduces this to 0.929; conservative construction therefore explains much of the
absolute entropy level. High source conflict covers the upper quartile by definition
and correlates moderately with other/unknown (r=0.422), but almost not at all with
entropy (r=-0.045). Removing the conflict-to-unknown term lowers other/unknown by
0.020 yet raises entropy by 0.007, showing that disagreement changes where
uncertainty is represented rather than causing the broad class overlap.

The diagnostic flags are explicitly overlapping rather than an exact decomposition:
45.13% ontology ambiguity, 25.00% high source conflict, 22.68% weak class
discrimination, 22.38% coarse/contextual evidence dependence, 3.32% temporal
ambiguity and only 0.52% missing evidence. Missing-habitat cells are more uncertain
(0.942 versus 0.929) but are too few to explain the AOI result.

Ablation identifies unique information rather than just configured weight. Removing
NRW habitat produces the largest change: mean total-variation distance 0.091,
91.77% materially affected and 50.72% changing leading meaningful class. Geology
changes probabilities broadly (TVD 0.063; 73.34% materially affected) but changes
the meaningful leader in only 3.84%; its main value is uncertainty and talus/peat
context. Terrain has TVD 0.047 and changes the meaningful leader in 6.34%, supplying
the unique morphological constraint. Sentinel has the smallest global ablation
(TVD 0.024; 0.74% materially affected; 0.46% changing meaningful leader), but remains
the only recent dated spectral evidence and is not misleading.

The readiness diagnostic marks 46.21% as broad-tendency constrained, 37.10% as
guided mixture reconstruction and 16.70% as high reconstruction freedom. These
classes specify how much freedom a future renderer may use; they do not convert
inference into measured material truth.

The decision is Outcome B: acquire no additional evidence. Coverage is already
nearly complete, and no single scalable public source is demonstrated to resolve
the combined mutually exclusive ontology, coarse/contextual source scale, temporal
ambiguity and likely sub-grid mixtures at human reconstruction scale. Freeze evidence
gathering and proceed to Lab 009 with uncertainty preserved.

Six inspected diagnostics, six audit rasters and the deterministic report are
external under meridian-data/earth-lab/tryfan-008/surface-uncertainty-audit.
Two cached runs produced SHA-256
3996360c3ea9b379362704b22c5e06e8ecaf16870e14118ff8eabb1bcd02fac7.

## Lab 009: evidence-constrained surface reconstruction v0.1

Lab 009 is the first renderer-facing Earth Lab stage. It keeps the frozen Lab 007 six-class probabilities as the inference layer and uses frozen Lab 008 readiness only to control bounded reconstruction freedom. It does not reclassify the evidence. `other_unknown` never becomes a material; it raises a separate freedom field.

Run the deterministic offline reconstruction with:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\analyze_surface_reconstruction.py --config docs\earth-lab\tryfan-009-surface-reconstruction.json

The output uses the exact 3025 x 3025 Landscape vertex grid (0.992063492 m spacing). Lab 007 cell-centre evidence is bilinearly registered to the vertex grid; only the outermost evidence cell is extended to the AOI boundary. Five continuous visual controls (rock, scree/talus, heath, grass and wet ground) remain normalized. Measured slope, approximately 15 m roughness and terrain form provide bounded placement adjustments. Deterministic correlated fields at approximately 8 m, 29 m and 97 m supply reconstructed sub-cell structure; Lab 008's three regimes set amplitudes of 0.06, 0.15 and 0.25 in logit space.

The final deterministic result is SHA-256 `14f90941468166dc3937879e022e8fedff2d9d212eed5cfb1c5deb0407c6a859`. Two complete cached runs produced identical hashes and output inventories. Controls cover 100% of the terrain, sum to one within 2.39e-7, have neighbour correlations of 0.993-0.997, and differ from the aggregate Lab 007 known-class tendencies by at most 0.0077. Mean controls are rock 0.1299, scree/talus 0.1379, heath 0.2794, grass 0.2715 and wet ground 0.1813. Boundary jumps at inherited 10 m cell edges are small (0.0041-0.0071) and only 1.13-1.19 times ordinary adjacent-vertex jumps; inspected maps show no checkerboard or salt-and-pepper artefact.

Deploy and apply the reversible Unreal setup with:

    ..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\deploy_surface_reconstruction.py --config docs\earth-lab\tryfan-009-surface-reconstruction.json

Then open `/Game/Tryfan_Lab004` and run `Content/Python/setup_lab009_surface.py`. The setup imports two non-sRGB 3025 x 3025 mask textures, creates `/Game/MeridianLab009/M_Lab009_Surface`, and assigns it to the Landscape. The saved material has exactly two `SAMPLERTYPE_MASKS` samples and a restrained five-family colour mixture with roughness 0.88. The pre-009 material (`None`) is recorded in `Saved/meridian-lab009-baseline.json`; applying with `MERIDIAN_LAB009_ENABLED=False` restores it, and `True` reapplies Lab 009. Both directions were saved and validated without changing the Landscape or camera.

The saved map passes the canonical Landscape validator, canonical Lab 004A camera validator and read-only Lab 009 validator. The camera remains at `(52549.121743, -29494.947166, -16443.742374)` cm, rotation `(30.341801, 165.141998, 0)` degrees, HFOV 35.2 degrees and constrained 4:3 aspect. The Landscape remains at `(-150000, -150000, 0)` cm with scale `(99.206349, 99.206349, 150)`.

UE 5.8 SceneCapture is not accepted for the benchmark images. Its camera-bound ImagePlate render proxy remains in front of transient SceneCapture output even when the actor/component is hidden, moved or removed in the unsaved capture world. Those generated frames are explicitly marked invalid. Use the real editor camera for the three acceptance frames:

1. Open `/Game/Tryfan_Lab004`, select `Meridian_Lab004_Geometric_Camera`, and choose **Pilot**. Keep the viewport at the camera's constrained 4:3 framing.
2. Baseline: run

       import unreal; MERIDIAN_LAB009_ENABLED=False; MERIDIAN_LAB009_SAVE_MAP=False; exec(open(unreal.Paths.project_content_dir() + "Python/setup_lab009_surface.py", encoding="utf-8").read(), globals())

   then run `HighResShot 1280x960` in the Unreal console.
3. Lab 009: repeat with `MERIDIAN_LAB009_ENABLED=True`, then capture `HighResShot 1280x960`.
4. Reference comparison: with Lab 009 enabled, run

       import unreal; MERIDIAN_REFERENCE_OVERLAY_ENABLED=True; MERIDIAN_REFERENCE_OVERLAY_OPACITY=0.5; exec(open(unreal.Paths.project_content_dir() + "Python/setup_photo_overlay.py", encoding="utf-8").read(), globals())

   and capture the same 1280 x 960 frame.
5. Disable the overlay with the same command using `MERIDIAN_REFERENCE_OVERLAY_ENABLED=False`. Leave Lab 009 enabled. Do not save the temporary baseline material state.

Offline diagnostics show coherent, spatially varying reconstruction and no obvious source-grid artefacts. Whether the perspective result is visibly better than baseline, and what material defect dominates from the photographic benchmark, remain pending inspection of those manual frames. The current v0.1 material intentionally lacks observed albedo, material microstructure, detailed normals, vegetation geometry and individual rock objects.
