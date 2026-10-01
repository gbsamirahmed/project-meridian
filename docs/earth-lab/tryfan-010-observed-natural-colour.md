# LAB 010 — OBSERVED NATURAL-COLOUR SURFACE

Research question: what does the existing measured Tryfan terrain look like when
surfaced directly with measured Sentinel-2 natural colour? This is an observation
baseline, not reconstruction. No terrain, camera, Lab 009 controls, habitat,
geology, DSM-DTM, procedural detail or generated geometry contributes to its RGB.

## Observation selection and provenance

The [metadata manifest](tryfan-010-observed-natural-colour.json) audits all four
retained Lab 005C observations, including every retained band, its native grid,
source URL and verified SHA-256. Summer reuses Lab 005B's native windows, as Lab
005C did. Historical configurations, reports and source files were not rewritten.
No data were downloaded or duplicated into a new source collection.

| Observation | Acquisition UTC | AOI cloud | Snow/ice | SCL topographic shadow | Sun elevation |
| --- | --- | ---: | ---: | ---: | ---: |
| Winter | 2024-01-17 11:33:29.025 | 1.33% | 25.28% | 59.20% | 15.72° |
| Spring | 2026-04-30 11:21:31.024 | 0.33% | 0% | 6.00% | 51.07° |
| **Summer: selected** | **2026-07-12 11:33:31.024** | **0%** | **0%** | **1.84%** | **58.06°** |
| Autumn | 2024-11-27 11:34:21.025 | 1.53% | 0.57% | 62.35% | 15.77° |

All four have zero recorded AOI cloud-shadow and nodata. These quality fractions
come from the retained 20 m Scene Classification Layer, not a guarantee that every
10 m pixel is free from haze. Summer is selected for complete usable RGB coverage,
no cloud/snow and higher illumination, not simply because it is newest. Spring is
a useful different phenological observation but is not composited into this Lab.

Primary official product:
`S2A_MSIL2A_20260712T113331_N0512_R080_T30UVD_20260712T174812`.
Copernicus Data Space records the Level-2A bottom-of-atmosphere product, processing
baseline 05.12. Element 84 Earth Search/AWS supplies anonymous COG access to that
same product: `S2A_T30UVD_20260712T113332_L2A`. Acquisition time and mirror granule
time are distinct and retained. Native CRS is UTM zone 30N, EPSG:32630.

Copernicus Sentinel data permit processing under their
[free, full and open data terms](https://dataspace.copernicus.eu/terms-and-conditions)
and [Sentinel legal notice](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice).
Attribution: **Contains modified Copernicus Sentinel data 2026.** No commercial
web-map imagery is used.

## Deterministic processing

Use **B04 red, B03 green, B02 blue**, all native **10 m** measurements. Retained
405 × 405 native windows include the historical 500 m retrieval margin and cover
the complete destination AOI. Their recorded hashes and source URLs are verified
before processing. Other seasonal bands are audited, not used to alter colour.

1. Convert valid DN to reflectance using `DN × 0.0001 − 0.1`, as recorded in the
   retained collection metadata. DN zero is nodata; negative valid reflectance is
   preserved in the reflectance product.
2. Reproject once from EPSG:32630 to EPSG:27700 using bilinear interpolation and
   one GDAL worker. Crop to `[264900, 357800, 267900, 360800]` exactly.
3. Store three-band float32 reflectance separately. This does not discard the
   retained native DN source windows.
4. Apply the fixed Lab 005C common display stretch:
   `uint8(round(255 × clip((reflectance − 0.02) / 0.28, 0, 1)))`, gamma 1.
   This is a global display transform; no per-image histogram adjustment,
   local enhancement, sharpening, snow removal or shadow correction is applied.

Both geospatial outputs are **300 × 300 pixels at 10 m**, north-up, west-left,
with transform `[10, 0, 264900, 0, -10, 360800]`. There are **zero nodata cells**.
Independent inverse-coordinate sampling at all four corners and the centre checks
band order, reprojection and absence of mirroring/rotation. PNG bytes exactly match
the geospatial display RGB. Repeated processing gives identical product and
manifest hashes. Toolchain versions are recorded in the manifest.

**Sentinel-2 natural colour has 10 m native spatial resolution. Any finer raster
representation used by the renderer is interpolation and does not constitute
additional observed spatial detail.** This adapter needs no finer raster: it uses
the same 300 × 300 PNG with bilinear filtering.

External products live under
`${MERIDIAN_DATA_ROOT}/experiments/earth-lab/tryfan-010/observed-natural-colour-v1/`:

- `lab010-rgb-reflectance-10m.tif`: canonical derived reflectance.
- `lab010-natural-colour-10m.tif`: canonical derived display RGB.
- `lab010-natural-colour-10m.png`: renderer transport/preview.
- `lab010-manifest.json`: source audit, processing, hashes and identity.

Product identity:
`95da30643ea0d7b25408182cbea11adc2dd842ae1557b545d1de8e77c39c3dce`.
Individual SHA-256 values are in the tracked manifest. No raster enters Git.

## Unreal adapter and reversible inspection

The existing measured Landscape, 3025 × 3025 vertices, transform and fixed camera
are retained. Source acquisition is Welsh Government 1 m LiDAR, 2021-03-02; its
existing Landscape resampling does not introduce new measured resolution.

Generated assets are `/Game/MeridianLab010/T_Lab010_NaturalColour` and
`/Game/MeridianLab010/M_Lab010_ObservedNaturalColour`. Texture is sRGB display RGB,
300 × 300, uncompressed, bilinear, clamped, without synthetic mips/detail. Material connects
RGB to Base Color, fixed roughness **0.88** and specular **0**, with no normal map,
displacement or class controls. It remains lit by the existing reference scene;
scene lighting/tone mapping may change apparent colour. Acquisition shadows remain
baked into the observation, so additional Unreal shading can compound them.

Existing world-space mapping is `UV = WorldPosition.XY / 300000 + (0.5, 0.5)`.
The Landscape uses +X east, +Y south: north-west is UV (0,0), south-east (1,1).
No PNG flip, actor rotation, geometry change or camera movement is required.

From the repository root, with the existing Earth Lab scientific Python environment
and documented external-data root:

```powershell
python scripts/earth_lab/observed_natural_colour.py
python scripts/earth_lab/deploy_observed_natural_colour.py
python -m unittest discover -s scripts/earth_lab -p test_observed_natural_colour.py -v
```

Open the [reference renderer](../../renderers/unreal/tryfan-reference/README.md)
in Unreal 5.8.2 and `/Game/Tryfan_Lab004`. In the Python console:

```python
import unreal, sys
sys.path.insert(0, unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir() + "Python"))
import setup_lab010_surface as lab010
lab010.validate()
```

Validation recreates existing generated dependencies, exercises the states and
returns to Lab 009 without saving the map. It uses the established pre-Lab009
baseline record rather than treating whatever material is currently assigned as
a new baseline. Then select `Meridian_Lab004_Geometric_Camera` and **Pilot** it,
retaining constrained 4:3 framing. Do not move the camera or save incidental map
changes. Inspect/capture these exact states:

```python
lab010.apply("baseline")                 # A: reference/default terrain
lab010.apply("lab009")                   # B: existing reconstruction
lab010.apply("lab010")                   # C: observed natural colour
lab010.apply("lab010", overlay=True)     # D: observed colour + existing 50% photo
```

For each state, the existing real editor viewport may use `HighResShot 1280x960`.
Do not substitute the previously unreliable SceneCapture/ImagePlate pipeline.
Return with `lab010.apply("lab009")`; reopening the unsaved map also restores its
canonical saved material. Generated assets, pointers, logs and captures stay ignored.

## Validation and findings

[Validation evidence](tryfan-010-validation.json) records four passing Lab-specific
tests, repeat processing, source-hash verification and successful Unreal 5.8.2
null-RHI and normal D3D12 validation. All four states were exercised. Landscape
topology/registration/collision, fixed camera and Lab 009 validators passed.
The LFS map remains SHA-256
`85ef8f1cc9a9fda9b6f2ab3b911bd57831fe75c4009e5ad168ea4956165a260d`;
the canonical R16 and Lab 009 identity remain unchanged. No map was saved.

The overhead observed preview visibly contains spatially located green/brown
surface variation, bright areas and dark lake/shadow regions. These are spectral
colour patterns, not validated rock/grass classification. Unlike Lab 009's inferred
mixtures, their placement comes from one actual observation. That establishes an
honest spatial-colour baseline, but does not establish fixed-camera improvement.

**Manual fixed-camera visual acceptance remains pending.** No automated perspective
frames are presented as accepted evidence. During the A–D comparison record:

- whether recognition and large bright/green/brown boundaries improve;
- which silhouette/shape deficiencies persist with unchanged measured geometry;
- which missing details are smaller than a 10 m pixel;
- whether acquisition shadows confuse the photograph/Unreal lighting comparison.

No individual rock, vegetation geometry or material microstructure is observed or
reconstructed by this Lab. The 2026 summer observation, 2021 terrain and 2009
photograph differ in date and illumination. Do not infer that colour mismatch proves
a geometry defect, or that bright colour alone identifies exposed rock. Those
limitations are observations for subsequent research, not fixes introduced here.
