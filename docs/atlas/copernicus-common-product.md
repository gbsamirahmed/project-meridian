# Bounded Copernicus common/coarse terrain product

Completed 2026-10-04, starting at `9f45d3ae7611f5b4710436d6de5318b0aa31ab29`,
clean `main`, locally recorded `origin/main` 0/0. This is a data/delivery evaluation,
not a production migration or a Swiss join. Production visual AWS, independent
analytical AWS z15, Weather, Traverse, strengthened IGOR, exaggeration 1.45,
satellite and camera/projection/lifecycle have **no source-code diff**.

## Decision and role

**MERIDIAN EVIDENCE:** Meridian can reproducibly prepare this frozen Copernicus
selection into a coherent local common/coarse pyramid. It is suitable as the
coarse-side asset for a bounded later Swiss hierarchy experiment, inside its
supported context. It is **not a complete global hierarchy**: z0–7, external
perimeter support and global missing-land/ocean/polar policies remain absent.
Landscape views can reach its perimeter; the flat exterior is retained as a
negative result, not hidden with AWS padding.

The common reference provides interpretable broad landforms, explicit height
semantics and predictable parent aggregation. It does not replace best available
regional terrain, manufacture fine detail, or become analytical elevation.
The [reference assessment](global-reference-assessment.md) established the source
choice; this task establishes a delivery product, not another source ranking.

## Frozen inputs and scope

**EXTERNAL EVIDENCE:** Copernicus GLO-30 is an edited DSM, not bare-earth DTM.
The retained public COG distribution documents the **2021 release**; exact
sub-release remains unestablished. It preserves base elevation posts while
removing duplicated edge posts and adding averaged overviews. Principal
TanDEM-X observations date from 2010–2015, with other filling epochs possible.
Heights are declared EGM2008 metres; retained TIFF horizontal identification
is EPSG:4326. See the [official collection](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM),
[handbook](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf)
and [distribution contract](https://copernicus-dem-30m.s3.amazonaws.com/readme.html).
Access/review date: 2026-10-04. No newer CDSE generation was substituted.

Six whole 3600×3600 float32 COGs are used:

| Asset (common `Copernicus_DSM_COG_10_…_DEM.tif` naming) | Status | SHA-256 |
|---|---|---|
| N45_00_E007_00 | Reused canonical assessment file | `638c155dd9a5f0b7ee818146def740093da33cee4606071b2bbf7ce3fa00ab95` |
| N46_00_E007_00 | Reused canonical assessment file | `426e3d1492d94e4f23d444843f852ff5be675da5c4c14e661b5642006864047d` |
| N45_00_E008_00 | Acquired from same public distribution | `02fac5d646f443f4f288a3d59b4cb995300e1c4fcbe4b5c1c6078a165a3d9ad4` |
| N46_00_E008_00 | Acquired from same public distribution | `47769664394ee1ff3b51f5c1b43a3441d7f7bce8d086d0ed2f3a892b895fae3e` |
| N47_00_E007_00 | Acquired from same public distribution | `5012dc32581b4aebbe71dec6f22507a2944b5e6b7f8fa301b0876f947976298b` |
| N47_00_E008_00 | Acquired from same public distribution | `4e2917429d65e049a4f1ddee2093f7fc50f11d22d0fd7cee85f5c8334186d7fe` |

Canonical sources total **254,113,117 bytes (254.11 MB)**; newly downloaded four
files total **169,741,575 bytes**. Original two files are referenced, not copied.
Provider ETag/MD5 checked for new transfers; all six SHA-256 hashes checked
before generation and verification. Exact URLs, HTTP receipts, access timestamps,
registration and source identity are in [acquisition](copernicus-common-acquisition.json).
Older source limitations/accuracy specifications remain qualified as in the
assessment; no per-post epoch, infill identity or measurement-resolution claim.

Two full XYZ roots, **z8/133/90 and z8/133/91**, define the product. Geographic
coverage is `[7.03125,45.089035564831015,8.4375,47.040182144806664]`, approximately
108 km east/west ×217 km north/south at this latitude. This encloses the entire
10×10 km Swiss support region with substantial landscape context, without using
Swiss heights. The single southern root would end at 46.07323°N, near the
benchmark, so the northern parent was retained. The two original E007 files
cannot supply complete roots extending to 8.4375°E; E008 and the narrow required
N47 support are the minimum additional whole distribution units.
The [preparation plan](copernicus-common-product-plan.json) was recorded before
generation. Acquisition coverage and delivery coverage deliberately differ.

## Delivery contract and processing

- XYZ / EPSG:3857; 256×256 **lossless RGB PNG, Terrarium**.
- Decode `R×256 + G + B/256 − 32768` metres; nearest quantization increment
  1/256 m, maximum encoding error 1/512 m. Installed MapLibre 6.11.2 supports
  this natively. Its Mapbox encoding quantizes at 0.1 m; custom decoding is
  available but unnecessary for this product.
- **EGM2008 height semantics preserved** (EPSG:3855 metadata). Reprojection is
  horizontal only; no LN02/AWS transformation or registration correction.
- Source Point registration is retained once through the affine transform;
  six inputs form one aligned VRT. GDAL performs exact horizontal reprojection
  (`ERROR_THRESHOLD=0`, single thread) with bilinear source sampling to a global
  z13 float32 grid. Tile extraction never performs independent tile warps.
- Parents are recursive **2×2 arithmetic means of unencoded elevations**,
  float64 accumulation and float32 storage. Encode each level independently;
  never average RGB bytes. Every parent uses the same Mercator grid origin.
- Mean weights represent equal **Web Mercator pixel area**, not equal physical
  ground area. This is a cartographic raster hierarchy, not volume integration,
  extrema preservation, hydrological conditioning or structural generalisation.
- Nodata/nonfinite support propagates through parent aggregation. Do not
  average around holes, encode alpha as elevation, extrapolate, or use zero
  heights/AWS as padding. The fixed complete-root build fails early if its
  finest selected support is incomplete; incomplete tiles are never published.

**EXTERNAL EVIDENCE:** Averaging is established raster overview practice;
GDAL documents weighted non-nodata averaging and distinguishes nearest,
bilinear and other filters. Meridian deliberately chooses stricter missing-support
propagation than GDAL's valid-sample average. Bilinear is used only for the finest
horizontal transfer; box means provide the defined low-pass hierarchy. There
was no justified need to compare a family of invented filters.
See [GDAL overviews](https://gdal.org/en/stable/programs/gdaladdo.html)
and [warping](https://gdal.org/en/stable/programs/gdalwarp.html).

### Information versus delivery scale

Source postings here are one arcsecond, approximately **21.5 m east/west and
30.9 m north/south** near Riffelhorn. Distributed posting is not independent
measurement resolution. Mercator output sample spacing depends on latitude:
near 45.979°N, z11≈53.12 m, z12≈26.56 m and z13≈13.28 m for 256-pixel tiles.
z12 undersamples the east/west posts locally. z13 avoids that loss by sampling
the interpolated source signal more finely, **without new observations**.
There is no universal isotropic source-information zoom. Higher zoom in the
renderer is overzoom of z13, not extra data. No z14+ delivery tiles are generated.

| Zoom | Tiles | PNG bytes |
|---|---:|---:|
| 8 | 2 | 318,338 |
| 9 | 8 | 1,230,915 |
| 10 | 32 | 4,700,323 |
| 11 | 128 | 17,722,600 |
| 12 | 512 | 65,674,961 |
| 13 | 2,048 | 237,989,861 |

Total **2,730 tiles / 327,636,998 bytes (327.64 MB)**. Working float32 pyramid:
416,136,764 bytes, separately retained for reproducibility/diagnostics. First
valid build took 103.60 s; independent build 102.43 s in this environment.
Tile min/median/p95/max: 11,890 /122,200 /138,316 /161,226 bytes.
These are bounded local observations, not global cost or CDN benchmarks.

## Numerical preparation and parent evidence

**MERIDIAN EVIDENCE:** [Checks](copernicus-common-checks.json) retain all results.
These test delivery/preparation fidelity, **not terrain accuracy**.

- Independent bilinear source-post evaluation at 2,048 seeded finest pixel
  centres: maximum absolute difference **0.00012196 m**, RMS **0.00004378 m**;
  p95 absolute 0.00009934 m. Thus no unintended datum adjustment or half-pixel
  registration error is indicated by this transfer check.
- Terrarium error over every tile: maximum **0.001953125 m**.
- Every parent pixel exactly matches the implemented unencoded 2×2 mean.
- Four matched physical patches (Riffelhorn rough ridge, alpine terrain north,
  Aosta valley, gentler Bern terrain) compared recursive means with direct
  float64 finest-grid block means: maximum discrepancy **0.00019837 m**.
- Full-raster mean across levels differs by less than **0.00000026 m**;
  no systematic mean drift is evident. Source-height extrema contract as
  expected: entire grid maximum 4541.96 m at z13→4440.45 m at z8; minimum
  103.00→107.31 m. A rough Riffelhorn patch's 2380–2852 m fine range collapses
  to its 2661 m coarse mean. This is deliberate scale loss, not missing detail
  magically recovered by overzoom.
- Every encoded tile equals the independent window from the single global
  working raster. Tile edges add only quantization; adjacent pixel centres
  naturally differ in mountainous terrain. The maximum adjacent difference
  at z13 tile joins is 59.57 m; it is not a claim of a seam step, since these
  are distinct sample positions on the same raster.
- A fresh independent build matched **every PNG hash, all working-raster
  hashes, VRT hash and immutable manifest identity**.

One initial rejected build produced only nodata because an `always_xy` pyproj
operation was incorrectly supplied as a GDAL explicit coordinate override.
The tool now lets GDAL handle EPSG axis mapping, checks complete support before
publishing a manifest, and has a synthetic regression test for that issue.
The failed external directory is separately named `-failed-axis-override`;
it is not the canonical product. One camera-capture assertion was also corrected
to tolerate floating-point longitude roundoff; no camera behavior was changed.

## Real-app renderer and delivery evaluation

Evaluation-only Vite tooling substitutes both visual DEM source contracts,
sets `minzoom:8`, `maxzoom:13`, native source bounds, and source credit. It
changes no production module. The misleading historical MapLibre internal
name `terrain-analysis-dem` still means **visual hillshade**, not analytical
route elevation. Normal Vite configuration never loads this plugin.

[Renderer record](copernicus-common-renderer.json) includes cameras, source
canonical zooms/DEM dimensions, fixed presentation, HTTP counts and capture hashes.
Full captures/network records are external. Chromium 151.0.7922.34, 1440×900,
DPR1, en-GB / Europe-London; actual browser version in the record is authoritative.
Weather publication was deliberately unavailable (503 fixture); Weather overlays,
route calculations and satellite imagery were not evaluated or changed here.

| Purpose | Centre lon/lat | Zoom | Pitch | Bearing |
|---|---|---:|---:|---:|
| Landscape | 7.76121329,45.97910794 | 9.4 | 45 | 0 |
| Planning | same | 11.4 | 45 | 0 |
| Close | same | 13.2 | 55 | 0 |
| Overzoom | same | 16.2 | 55 | 0 |
| Rotation | same | 13.2 | 55 | 180 |
| Gentle control | 7.35,46.92 | 11.4 | 45 | 0 |
| Internal z8 parent join | 7.76,46.07323062540835 | 10.4 | 55 | 90 |
| Zoom transition | benchmark | 11.95 and 12.05 | 45 | 0 |
| Return / cache | benchmark | 11.4 | 45 | 0 |
| Globe / Mercator guards | benchmark | 4.8 and 5.8 | 0 | 0 |

**MERIDIAN EVIDENCE, qualitative:** landscape and planning views communicate
broad ridges/valleys, and the internal parent join has no observed wall or black
void. Gentle terrain remains readable. Rotation retains the broad forms.
The two settled zoom-transition captures retain the major landforms; one
continuous camera zoom/rotation also completed without a page error. This is
not proof that every possible zoom transition is imperceptible.

Close relief becomes broad/smooth, with visible faceting/texture patches;
the AWS close control shows similar limitations. Overzoom produces no meaningful
fine structure, and this established camera looks into an enlarged local slope.
Native mesh size remains128; canonical DEM zooms vary by source and perspective
(geometry uses multiple LODs, visual relief typically finer tiles), never exceeding
13 for this source. A camera zoom is not the DEM information level.
`queryTerrainElevation` values include 1.45 exaggeration and scale/mesh sampling;
they are not unmodified source measurements or accuracy checks.

AWS landscape/planning controls have comparable broad terrain context. Copernicus
is not adopted for spectacle; the controlled product's main gain is interpretable
source semantics and reproducible parents. No tuning to mimic AWS took place.
Hillshade, elevation layer and sky configurations matched AWS controls exactly:
IGOR, 315° map anchor, historical colors/linear filtering, current continuous
strength curve and 1.45 exaggeration. Satellite suppression remains untouched.

**Negative coverage result:** landscape and parent-join views expose flat terrain
outside the finite eastern perimeter. Below z8 there are no visible local DEMs;
the globe guard correctly disables terrain at z4.8, and Mercator enables terrain
at z5.8 but receives no local geometry (queried height 0). This is renderer fallback,
not encoded zero or a valid global elevation statement. Local success cannot
establish world/continental support. No black interior void was seen in these
completed captures; no arbitrary edge was accepted as a future production seam.

The completed local run had **344 successful responses /204 distinct tile URLs**,
43,343,466 response-body bytes including cache repeats (not wire volume), and
25 local request cancellations (`ERR_ABORTED`) during navigation. No completed
local HTTP request failed; all settled visible DEMs were loaded. Other basemap
cancellations and two expected Weather503 console errors were retained. Return
to planning and close overzoom generated **zero new local responses**. Per-scene
settle times included a fixed1s capture delay and ranged roughly3.9–12.2s;
software browser rendering/live basemap contribute, so these are not load benchmarks.
Loopback server supplies CORS `*`, cache `public,max-age=3600`, SHA ETags and product
identity. Separate HTTP probes returned 304 for conditional reuse and 404 for an
absent lower level. No online data dependency is added to normal tests.

## Nodata, water, rights and provenance

All prepared pixels are finite, with no zero/nodata cells in this landlocked
delivery rectangle. Source-declared water editing and inland lake heights pass
through unchanged; this did not test their geodetic accuracy. Ocean/coastline,
absent land, polar coverage and latitude-varying global posting are explicitly
**unresolved**. No unnecessary ocean sample was acquired: this bounded land
product need not invent a global policy. Future global generation must resolve it.

The [GLO-30 F licence](https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf)
permits derivatives subject to applicable obligations. Existing source-specific
rights are inherited in metadata, including full modified-product attribution,
liability, non-endorsement and downstream requirements. The local browser gives
descriptive source credit plus a licence link; it is **not a complete public
distribution legal package**. Public delivery must include the applicable full
Article 6 notice/terms before publishing; no public service is introduced here.

[Atlas metadata](copernicus-common-metadata.json) uses the existing model without
an extension: frozen six-asset source selection, immediate contributor revision,
edited DSM, preserved EGM2008, scientific processing lineage, source posting versus
delivery/overzoom, distinct source/product coverage, scoped finite support, rights
and immutable product identity. It assigns **no protected interior or fallback**;
transition support stays unknown. Complete immediate dataset identity is not
complete upstream observation/infill provenance.

Product identity: `8f002dcbdeceb6aa37cc9eeef9f2d2060193b1eff7922ddb1d0535a6b8030da2`.
Source/product/manifest hashes and tool versions are in the
[generation record](copernicus-common-generation.json). Build identity excludes
wall-clock time; scientific parameters/source bytes and deterministic file hashes
define it. Canonical repository text is hashed with LF normalization.

## Scaling implications and next bounded step

**RESEARCH HYPOTHESES / DIRECTIONS:** The established transformation is a plausible
base for incrementally generated immutable source-aligned blocks, with aggregation
performed on unencoded heights. Do not monolithically warp the world like this
small selection. Shared origins, source halos, nodata/support masks and reproducible
cross-block parents would be required. Exact global compressed costs cannot be
extrapolated from alpine tiles. Prior source estimate is about0.892TB uncompressed
base postings; a full Mercator z0–13 tile grid has89,478,485 tiles. Applying this
local median blindly would give≈10.9TB: an illustrative storage warning, not a
forecast. Land-only generation, latitude-dependent information ceilings, packaging,
revisions and intermediate storage need deliberate later choices. No infrastructure
or world pyramid was implemented.

The smallest justified next implementation is the **bounded Copernicus+Swiss
hierarchy experiment**, using these identified products and documented Swiss
support/protected interior. It must explicitly define scale/parent-child selection,
height-reference accounting (LN02 versus EGM2008, no accepted correction), contributor
identity and finite evaluation extent/perimeter policy before composing anything.
It should test preservation of Swiss interior detail, parent continuity and source
transitions. This record does not establish that either seam or source selection
will work, and does not authorize extending to a generic resolver. Global
ocean/polar/lower-parent policy is a separate prerequisite for production/global
adoption, not something to conceal in this local join. Stop here.

## Locations and reproduction

External root is the documented sibling `meridian-data` or absolute
`MERIDIAN_DATA_ROOT`. No private estate was read.

- Sources: two canonical assessment files remain at their existing paths;
  four added inputs/receipts under `sources/atlas/riffelhorn/copernicus-common-2021-v1/`.
- Product: `derived/atlas/riffelhorn/riffelhorn-copernicus-common-v1/` contains
  `source-mosaic.vrt`, unencoded `working/z*.tif`, `tiles/`, `manifest.json`,
  `atlas-metadata.json`. Independent sibling `-rebuild` retains duplicate hashes.
- Evidence: `experiments/atlas/riffelhorn-copernicus-common-v1/` contains generation
  records, checks, parent-patch figure, renderer summary and 16 controlled captures.
- Git contains only tooling, metadata, compact records/tests and this report.

From repository root, using the established external scientific environment:

```powershell
$python = 'C:/Users/gbsam/Documents/Projects/meridian-data/earth-lab/.venv/Scripts/python.exe'
& $python scripts/atlas/copernicus_common.py acquire
# Canonical build is immutable; run prepare only when absent.
& $python scripts/atlas/copernicus_common.py prepare
& $python scripts/atlas/copernicus_common.py prepare --suffix=-rebuild
& $python scripts/atlas/check_copernicus_common.py
& $python scripts/atlas/build_copernicus_common_metadata.py
& $python scripts/atlas/copernicus_common.py verify
& $python scripts/atlas/copernicus_common.py serve
# In another terminal, while port4182 is serving:
node scripts/atlas/capture_copernicus_common.mjs common '<MERIDIAN_DATA_ROOT>/experiments/atlas/riffelhorn-copernicus-common-v1/captures'
node scripts/atlas/capture_copernicus_common.mjs aws '<MERIDIAN_DATA_ROOT>/experiments/atlas/riffelhorn-copernicus-common-v1/captures'
& $python scripts/atlas/record_copernicus_common_evaluation.py
```

For a repeat after immutable directories exist, use another explicit named
`--suffix=-...` build and compare its manifest; the retained canonical/rebuild
commands are the original reproduction sequence, not overwrite commands.
The checker expects the `-rebuild` sibling. Additional scientific requirements
are already in the existing external environment; no npm/package dependency added.

Validation: 29 synthetic Atlas Python tests; 160 active Node application/tool tests
passed, 1 existing optional skip. This includes 6 new synthetic terrain tests and 4
metadata/evaluation-policy tests. Lint, TypeScript and application-only Vite build
passed; existing large-chunk warning remains. Build deliberately omitted external
GFS publication validation and copying the large external publication estate.
No unrelated clock-dependent test was changed; none failed in this run. Source,
product, metadata/document references and final production-diff checks were run.

Application/synthetic validation commands (external empty test root deliberately
proves that normal tests do not need the acquired product):

```powershell
$env:MERIDIAN_DATA_ROOT = '<absolute empty directory outside the repository>'
$tests = Get-ChildItem scripts/atlas,scripts/weather,scripts/route,scripts/ui -Filter 'test_*.mjs' | ForEach-Object { $_.FullName }
node --test $tests
& $python -m unittest discover -s scripts/atlas -p 'test_*.py'
npm.cmd run lint
npx.cmd tsc -b
node --input-type=module -e "import {build} from 'vite'; import react from '@vitejs/plugin-react'; await build({configFile:false,plugins:[react()],publicDir:false,build:{outDir:'node_modules/.tmp/copernicus-common-app-build'}});"
```

Remove the temporary empty-root override before external-product commands.
