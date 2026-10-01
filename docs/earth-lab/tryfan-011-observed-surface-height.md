# Lab 011 — observed surface-height structure

Research question: how much spatial structure exists in the paired 2021 Tryfan
DSM minus DTM, and at what scales? This is a measurement/diagnostic experiment,
not a reconstruction, semantic classification or a new Meridian cleanup phase.

**DSM−DTM is a difference between provider products, not automatically object
height or height above true ground. Low residual does not exclude a rock; high
residual does not identify a rock, shrub, tree or building.** Rocky features can
already be present in the provider's terrain classification. Exact return-level
classification and interpolation rules are not available in the retained metadata.

## Sources and registration

The [canonical catalogue](../atlas/tryfan-data-catalog.json) and retained manifest
identify Welsh Government national 2020–2023 LiDAR, **delivery 11, 2021-03-02**.
All 16 catalogue tiles covering the AOI share that acquisition date/delivery and
paired DTM/DSM links. The retained subsets came from bounded range reads of the
official [DTM COG](https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dtm_32bit_cog.tif)
and [DSM COG](https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dsm_32bit_cog.tif).
The [official tile catalogue](https://datamap.gov.wales/layers/geonode:welsh_government_lidar_tile_catalogue_2020_2023/metadata_detail)
and [historic reconnaissance](../atlas/tryfan-lidar-reconnaissance.md) preserve
the acquisition evidence. Licence: Open Government Licence v3.0; contains Welsh
Government information licensed under that licence. No source was reacquired.

Existing files under `${MERIDIAN_DATA_ROOT}/sources/atlas/tryfan/welsh-lidar-1m/rasters/`:

| Product | SHA-256 |
| --- | --- |
| `tryfan-004-dtm-1m.tif` | `49c131d7de62e0df35f8e02c2f8db3161bfd37f24fea56060fcbb9e6d109b326` |
| `tryfan-004-dsm-1m.tif` | `d54b4810c17968f434ebe538d92595b8d33a2d68528709c7f31c7f2c1f5dd25d` |

Both are float32, 3000 × 3000, EPSG:27700, 1 m pixels, bounds
`[264900,357800,267900,360800]`, affine `[1,0,264900,0,-1,360800]`.
Source nodata is −9999, with **zero missing cells** in either subset. Row zero
is north; column zero is west. The grids are identical: **no resampling or
alignment is performed**. Subtraction uses float64 arithmetic then float32 storage;
valid negative values are retained. Canonical residual nodata is NaN.

Vertical values are metres in retained terrain/source provenance, with ODN used
by the established terrain registration. Neither source TIFF encodes a vertical
CRS or band unit. This Lab does not pretend to independently establish an absolute
datum from EPSG:27700, which is horizontal. The same paired survey/provider,
delivery, grid and consistent existing metre-valued provenance support relative
subtraction without a vertical transformation. Independent survey accuracy,
classification error and absolute datum verification remain limitations.

## Quantitative results

All 9,000,000 cells are comparable. The signed residual has min **−11.56998 m**,
max **24.48001 m**, mean **0.30149 m**, median **0.14001 m**, population standard
deviation **0.66323 m**. There is no large unexplained uniform difference.

| Percentile | Residual (m) |
| --- | ---: |
| p01 | −0.01001 |
| p05 | 0.01001 |
| p25 | 0.06000 |
| p50 | 0.14001 |
| p75 | 0.29001 |
| p90 | 0.60999 |
| p95 | 1.07001 |
| p99 | 2.88000 |
| p99.5 | 4.21997 |
| p99.9 | 8.57001 |

**70.767%** has |residual| ≤0.25 m. Negative residuals occupy **1.13849%**,
mean −0.06828 m and median −0.03000 m among negative cells; **0.03068%** of the
AOI is below −0.25 m and **0.00463%** below −1 m. Nothing is clamped in the
canonical difference field.

Thresholds are strictly greater-than, non-semantic diagnostics. Components use
four-neighbour connectivity, so diagonally touching cells remain separate.
Footprints are cell area, not objects, volume or counts of physical features.

| Threshold (m) | AOI above threshold | Components | Largest footprint (m²) | Threshold area in ≥9 m² components |
| --- | ---: | ---: | ---: | ---: |
| >0.25 | 29.2023% | 243,250 | 643,750 | 84.17% |
| >0.5 | 12.3950% | 165,279 | 89,405 | 73.86% |
| >1 | 5.4376% | 84,243 | 12,294 | 67.78% |
| >2 | 1.8836% | 33,314 | 11,581 | 62.76% |
| >3 | 0.9288% | 14,986 | 8,953 | 66.20% |

At >1 m, isolated single-cell components account for **8.88% of threshold area**;
**51.25%** is in components ≥25 m² and **34.96%** in components ≥100 m².
Connectedness depends on the chosen threshold and connectivity and is not a
physical feature delineation. The metadata records footprint percentiles, local
mean/max/std, density, bounding-box fill/axis ratio and edge flags for the largest
30 components at each threshold.

The positive maximum at E267820.5, N360476.5 is spatially supported: its 5×5
neighbourhood ranges 18.92–24.48 m (median 22.30 m). This is not an isolated spike.
The negative maximum-magnitude difference at E265005.5, N359601.5 occurs on a
steep measured slope (~82.19°), with 30.5 m of 5 m DTM relief; its neighbourhood
contains both signs. It is only 5.5 m from a 1 km grid line, so source seam or
interpolation/classification effects cannot be excluded. Both extrema are valid
interior source cells, not output edge/nodata effects; no resampling was introduced.
No return-level evidence establishes their physical origin. They remain in outputs.

## Spatial scales and terrain relationship

Local residual maximum/range/std are measured over complete **1, 3, 5, 10 and
20 m square windows**. A 1 m window has zero internal variation by definition,
not evidence of a smooth surface. Boundary diagnostics lacking a complete window
are NaN. Even windows are anchored with their centre 0.5 m east/south of the
labelled cell; this is explicitly recorded, not a shift of the canonical residual.

Median residual range at 3/5/10/20 m is **0.230/0.370/0.670/1.240 m**.
Windows whose mean exceeds 1 m occupy **4.77/4.50/4.18/3.96%** of valid window
positions respectively. Coherent variation persists across several metres;
it is not all single-cell noise. Max/range can also propagate an isolated extreme,
so component support and mean/std must be considered alongside them.

Slope is calculated from the measured 1 m DTM gradient. Local DTM relief is
5×5 max−min. DTM departure from its 5×5 mean measures local form/roughness;
it is zero on an interior planar slope. It is not a new elevation surface and
does not distinguish rock from other terrain. Residual >1 m rises from **1.83%**
in 0–10° terrain to **29.87%** at 45–60° and **73.55%** at ≥60°.
This strong slope relationship makes ground-classification/interpolation differences
especially important; it is not proof of more elevated objects on steep slopes.

Algorithmically selected 100×100 m examples:

| Selection | BNG bounds | Mean residual | Mean 5 m DTM relief |
| --- | --- | ---: | ---: |
| Strongest block mean residual | [266800,360500,266900,360600] | 3.456 m | 0.401 m |
| Greatest relief where block mean residual ≤0.25 m | [266100,359400,266200,359500] | 0.242 m | 3.349 m |
| Greatest relief where block mean residual >1 m | [266400,359300,266500,359400] | 1.450 m | 9.262 m |
| Lowest mean local terrain relief | [266200,360400,266300,360500] | 0.097 m | 0.003 m |

These show that substantial geometric structure can already be in the DTM despite
little residual, and that residual concentrations are not confined to high-relief
terrain. They are diagnostic selections, not habitat or object labels.

Signed residual means aggregated into exact Lab 010 10 m cells have weak Pearson
correlations with unaltered red/green/blue reflectance: **0.175/0.162/0.220**.
This adds little to fine-scale interpretation. Different dates, shadows and 10 m
spatial averaging preclude semantic conclusions. Lab 010 outputs remain untouched.

## Products, identity and reproduction

The [metadata manifest](tryfan-011-observed-surface-height.json) contains input
hashes, processing parameters/toolchain, statistics, source sample coordinates,
component records and every output hash. Large products remain only under:

`${MERIDIAN_DATA_ROOT}/experiments/earth-lab/tryfan-011/observed-surface-height-v1/`

Products: signed 1 m residual TIFF; DTM 5 m local-relief/departure TIFFs;
residual 5/20 m range/std TIFFs; 1 m diagnostic RGB PNG; overview, distribution,
selected-crop figures and renderer legend. Sources are referenced, not duplicated.
Two consecutive runs produced identical product hashes and manifest identity:

`5d157f6f5a0819d732e5b87f07d299144eeac6c4e6b4c29823bf8eebb00ee04c`

From the repository root use the Python launcher explicitly. The verified
installation is Python 3.12.6, NumPy 2.5.2, Rasterio 1.4.3/GDAL 3.9.3,
Matplotlib 3.10.6 and Pillow 12.3.0. Existing Earth Lab requirements describe
the scientific environment; no new dependency was added for this Lab.

```powershell
py -3.12 scripts/earth_lab/observed_surface_height.py
py -3.12 scripts/earth_lab/deploy_observed_surface_height.py
py -3.12 -m unittest discover -s scripts/earth_lab -p test_observed_surface_height.py -v
py -3.12 -m unittest discover -s scripts/earth_lab -p test_reference_renderer.py -v
```

Tests consume the existing Lab 011 products; they do not regenerate previous Labs.
Rebuilding is unnecessary for visual inspection when recorded products exist.
Six Lab-specific tests pass, including exhaustive comparison of 512 small masks
against independent flood-fill connectivity, independent coordinate sampling,
signed/nodata handling, local-window calculations and planar-terrain behaviour.
Five existing renderer/bootstrap tests pass. The
[validation record](tryfan-011-validation.json) records successful UE 5.8.2
commandlet material/state validation, fixed-camera, Landscape geometry/collision,
Lab 009 restoration and Lab 010 validation. No perspective screenshot is claimed.

## Reversible fixed-camera inspection

Open [the reference renderer](../../renderers/unreal/tryfan-reference/README.md)
in UE 5.8.2, map `/Game/Tryfan_Lab004`. Use the Python console:

```python
import unreal, sys
sys.path.insert(0, unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir() + "Python"))
import setup_lab011_surface as lab011
lab011.validate()
```

Select and Pilot `Meridian_Lab004_Geometric_Camera`. Keep constrained 4:3,
35.2° HFOV, location `(52549.121743,-29494.947166,-16443.742374)` cm and rotation
`(30.341801,165.141998,0)`°. Do not move the camera or save incidental map changes.
Apply separately, inspecting the same viewport between commands:

```python
lab011.apply("lab010")                 # A: observed natural colour
lab011.apply("lab011")                 # B: quantitative positive residual
lab011.apply("lab011", overlay=True)   # C: residual + existing 50% photograph
lab011.apply("baseline")               # Optional preserved baseline
lab011.apply("lab009")                 # Restore existing reconstruction
```

The generated `/Game/MeridianLab011` texture/material uses the existing world UV
mapping, +X east/+Y south. It is a 3000×3000 1 m sRGB, uncompressed, clamped,
bilinear RGB visualization, not displacement or reconstructed detail. Display is
`viridis(clip(log1p(max(residual,0))/log(11),0,1))`: 0–10 m fixed log stretch,
≥10 m saturated. Negative differences are shown in signed offline diagnostics,
not this positive-only material. Use the external `lab011-renderer-legend.png`.
The material is unlit/emissive to avoid interpreting scene shading as residual
variation; exposure/post-processing may still alter apparent colour. No lighting
or atmosphere setting is changed. No terrain, collision or geometry is modified.

Lab 010's manual inspection is now reported complete by the product owner, subject
to its existing limitations; its identity and outputs are not rewritten. **Lab 011
fixed-camera manual interpretation remains pending.** No SceneCapture acceptance
is claimed. The previously reported “LIGHTING NEEDS TO BE REBUILT (578 unbuilt
objects)” remains a known fixture limitation; this Lab does not rebuild lighting.

## Scientific conclusion and remaining limits

**Yes: the DSM contains spatially coherent information beyond the DTM worth
retaining for later evidence-fusion work.** Much of the AOI has small differences,
but some positive regions persist over several metres and larger footprints.
Equally, the DTM already contains substantial terrain form. The residual is not
a complete inventory of missing three-dimensional structure, nor evidence that
all retained positive differences should become added geometry.

Outstanding interpretation requires independent evidence: ground classification,
survey uncertainty/return-level data, seams, steep-slope interpolation and manual
photograph localization. No rocks, vegetation, habitat classes, procedural texture,
new height geometry or reconstructed detail are introduced.

OBSERVED: paired provider DTM/DSM. DERIVED: difference/terrain diagnostics.
RENDERED: figures and quantitative material. INFERRED: cautious analytical
interpretation only, no semantic classes. RECONSTRUCTED: none.
