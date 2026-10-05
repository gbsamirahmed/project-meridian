# Riffelhorn regional-preserving parent diagnostic

2026-10-05. Baseline `6e2687e11626501a11fa7e87e89d523d3572694d`.
Status: **regional LOD relationship demonstrated; spatial/common handoff unresolved;
no production adoption or final hierarchy contract**.

**MERIDIAN EVIDENCE (M)** means this identified local diagnostic.
**EXTERNAL EVIDENCE (E)** means retained official source/installed implementation facts.
**RESEARCH HYPOTHESES / DIRECTIONS (H)** remain scoped proposals.

## Hypothesis and frozen products

The [plan](regional-parent-plan.json) was recorded before implementation: a coarse
parent derived from Swiss terrain might remove the source-change component of
interior refinement, while leaving its geographic disagreement with common terrain
unresolved. No reconciliation, new acquisition or vertical correction was permitted.

Both complete source/product catalogues passed their existing verifiers before use:

| Product | Immutable identity | Semantics |
| --- | --- | --- |
| [Swiss support](riffelhorn-swiss-support-product.md) | `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea` | 100 official 2024 swissALTI3D inputs, 10 km square, distributed 0.5 m LV95 grid, DTM, LN02; original z12–18 immutable |
| [Common/coarse](copernicus-common-product.md) | `8f002dcbdeceb6aa37cc9eeef9f2d2060193b1eff7922ddb1d0535a6b8030da2` | Six frozen 2021 public GLO-30 COGs, exact sub-release unknown; edited DSM, one-arcsecond posts, EGM2008; z8–13 with explicit higher delivery overzoom |

The protected interior remains radius1.5 km around LV95 [2625000,1092000].
Source support remains [2620000,1087000,2630000,1097000], with at least3.5 km
surrounding source. Neither extent is an accepted geographic seamline.
The [previous hierarchy](terrain-hierarchy-prototype.md) remains the historical
control: H1 common13→Swiss14 RMS39.82 m, large moving spatial walls, exact fine Swiss.

All production `src/`, normal Vite configuration and dependency files are unchanged:
AWS visual terrain; independent AWS analytical256px/z15; IGOR315° map anchor and
strength curve; exaggeration1.45; satellite suppression; Weather, Traverse,
atmosphere, projection and lifecycle. Evaluation Weather503 is the retained
terrain-only fixture, not a production change. No private estate was inspected.

## Existing levels and chosen basis (M, E)

Inspection of `scripts/atlas/riffelhorn_support.py:warped/prepare` established that
original Swiss z12–17 are **independent GDAL area-average warps** from native source;
z18 is bilinear. They are not an exact recursive parent chain. Existing lower
Swiss levels already yield small within-family refinement changes; the previous
H0 first common11→Swiss12 jump was still39.77 m RMS. Replacing the family, rather
than lack of any Swiss coarse tiles, was the large source-change problem.

The separate derivative uses **unencoded Swiss z14 area-averaged elevations** with
the exact existing warp contract (float32 source warp, then float64 aggregation).
All25 complete z14 basis tiles reproduce original z14 PNG bytes exactly.
This is the appropriate coarse basis for the specific13→14 question, not a claim
that z14 contains all Swiss information. It avoids regenerating the fine estate.

Locally, source grid spacing remains0.5 m, delivery z18 samples about0.415 m,
z14 about6.64 m, and z13/12/11/10 about13.28/26.56/53.12/106.24 m. Latitude and
256px delivery are part of these calculations. They are sample spacings, not
independent observation resolution. z18 slightly oversamples the source grid;
MapLibre mesh/loaded-parent detail is separate. The original independently warped
z14–18 are retained, so this does **not** demonstrate a fully recursive z18→z0
regional pyramid or certify every fine representation choice.

## Parent rule and partial support

`scripts/atlas/regional_parents.py` creates a separate diagnostic:

1. Read the same100 verified native source assets through a new lightweight VRT.
2. Warp unencoded z14 with the original horizontal-only operation.
3. Accept a finite basis cell only if its corners and edge midpoints lie within
   the native source bounds with a0.5 m guard. This sampled footprint check is
   conservative for this small smoothly transformed rectangle; it is not a generic
   exact polygon-intersection guarantee. Rejected perimeter cells stay absent.
4. Recursively sum supported elevations and exact supported basis-cell counts in
   aligned2×2 blocks. Uniform weights represent **Web Mercator base-cell area**,
   not ground-area mass. Accumulation/parent storage are float64; no encoded child
   averaging or recursive quantization drift.
5. Encode each complete parent independently as256px XYZ/Mercator Terrarium PNG.
   Increment1/256 m; measured maximum encoding error≤1/512 m.

At level z, full support is count `4^(14-z)`. Count0 has NaN height; partial count
has the mean of its **observed subset**, not a valid estimate of the entire cell.
No zero terrain, extrapolation, Copernicus padding or blend is supplied. All cells
with nonzero counts have one source contributor: Swiss LN02. Support fraction is
not confidence and is not a Swiss/Copernicus mixing weight.

Offline NPZ fields retain heights and uint32 counts at z10–14. Only whole complete
tiles with the additional original perimeter guard are eligible for MapLibre.
Partial tiles are never served as complete Swiss DEMs. This separates supported
cells, complete tiles and the larger tile envelope explicitly.

| Level | Complete cells | Partial cells | Unsupported cells | Complete tiles |
| --- | ---: | ---: | ---: | ---: |
| 14 basis | 2,263,632 | 0 | 947,632 | 25 |
| 13 | 565,153 | 1,512 | 481,911 | 4 |
| 12 | 140,923 | 1,103 | 447,798 | 1 |
| 11 | 35,001 | 647 | 226,496 | 0 |
| 10 | 8,654 | 371 | 122,047 | 0 |

The absence of complete11/10 tiles is a **delivery/support limit**, not absence
of all useful coarse Swiss cells. Native support was not enlarged to satisfy it.

## Numerical LOD result (M)

[Measurements](regional-parent-measurements.json) use the same705 protected
100 m-grid points as H1, with cell-centred bilinear sampling of delivered fields.
They are preparation/compatibility measurements, not physical accuracy or the
exact displacement of every rendered mesh vertex.

| Transition | RMS height change (m) | Range (m) | Meaning |
| --- | ---: | --- | --- |
| Frozen control common13→Swiss14 | 39.8249 | −102.57…+96.95 | Unrelated estimates |
| Derived Swiss13→original Swiss14 | **0.7107** | −3.27…+5.96 | Same-family refinement |
| Derived Swiss12→derived Swiss13 | 1.3165 | −7.34…+8.28 | Same-family refinement |
| Offline Swiss11→Swiss12 | 2.8982 | −15.81…+17.09 | Coarser summarization |
| Offline Swiss10→Swiss11 | 6.2732 | −31.52…+41.83 | Larger footprint/ordinary loss of local extrema |
| Delivered common11→derived Swiss12 | **39.7680** | −101.08…+98.50 | Source change relocates downward |

Every recursive parent equals its declared unencoded aggregation exactly:
aggregation residual0 and support counts exact. Original Swiss14→15/15→16/16→17/
17→18 RMS remains0.4405/0.2633/0.1496/0.0724 m, unchanged from H1.
All705 protected fine samples at each14–18 have **zero modification** between
control and diagnostic. Coarse summaries legitimately change point heights and
extrema; that is distinct from adjusting the underlying authoritative fine terrain
to hide a seam. The original sources and delivery files remain immutable.

## Coarsening against common terrain (M)

Native LN02 and EGM2008 remain distinct. No datum transformation, fitted offset
or registration correction was applied. The prior+0.166…+0.752 m diagnostic remains
unaccepted; combined accuracy is unknown. It cannot explain tens-of-metres differences.

| Level | Full-cell median Swiss−common (m) | NMAD (m) | RMS (m) | RMS at fixed705 protected points (m) |
| --- | ---: | ---: | ---: | ---: |
| 14 | −1.595 | 4.653 | 20.010 | 39.827 |
| 13 | −1.479 | 4.381 | 19.953 | 39.757 |
| 12 | −1.384 | 4.102 | 19.818 | 39.596 |
| 11 | −1.241 | 3.755 | 19.480 | 39.137 |
| 10 | −1.140 | 3.490 | 18.800 | 38.373 |

Full-cell counts change with coarsening; the fixed-point column controls that
population difference. The full-support field retains negative southern/eastern
structure plus large ridge/glacier-region outliers. Sector, slope-centre and
roughness strata are retained; unsupported neighborhoods do not enter roughness.
The previous stable mask was hash-verified and reused solely for a **coarse-cell
centre diagnostic**: a coarse footprint can span glacier/nonstable classes, so this
is not a new certified stable-area mean or accepted co-registration fit.

These all-terrain/cell results are not interchangeable with the earlier stable
GLO-30-source comparison (RMS5.93 m). Population, delivery filtering and sampling
support differ. Coarsening attenuates some fine differences but does not cause the
surfaces to converge sufficiently for a natural handoff. No inference is made
about levels below10; the finite support and persistent trend justify stopping.
Difference/support maps and identical-coordinate profiles remain outside Git.

## Footprint growth and where the incompatibility moves

The retained supported basis is approximately99.794 km² of physical terrain.
Its area-equivalent support is constant through the chain; Swiss is never extended.
The surrounding grid/tile envelope grows substantially. All areas below are
**projected Mercator km²**, not physical land area or validated product coverage.

| Level | Tile envelope | Complete-cell area | Partial-cell footprint | Unsupported envelope |
| --- | ---: | ---: | ---: | ---: |
| 14 | 293.16 | 206.65 | 0 | 29.5% |
| 13 | 382.90 | 206.37 | 0.55 | 46.0% |
| 12 | 861.53 | 205.84 | 1.61 | 75.9% |
| 11 | 1,531.61 | 204.50 | 3.78 | 86.4% |
| 10 | 3,063.22 | 202.25 | 8.67 | 93.1% |

Whole delivered regional tiles cover95.73 projected km² at12/13, inside native
support; useful full cells outside those tiles remain offline. Protected intent
and minimum3.5 km native surrounding support remain unchanged. Propagating a tile
identity without its support would grossly overstate the regional footprint.

All frontier strips of the one complete z12 tile and four z13 tiles were evaluated,
not selected for favorable appearance. Adjacent delivered Swiss/common cell
differences reach **48.40 m at12** and **61.77 m at13**. These include terrain
slope as well as source disagreement; pure-common and excess-over-common controls
are retained. The coarse frontier is an inset tile boundary, not the official
source edge. It can move with level. The old H1 fine14/16/18 frontier is unchanged,
so its previously measured167/~45 m differences remain applicable to those exact
unchanged tiles. Cross-level maxima have different spacing/footprints and are not
one universal seam score.

Thus the13→14 interior jump is removed, but the first delivered source change moves
to11→12 and the same-level geographic edge remains. Moving it is not reconciliation.

## Renderer and continuous navigation (M)

The isolated loopback4184 stream offers two CLI-only strategies:

- **Control:** exact previous H1 selection, common below14, supported original
  Swiss14–18; common elsewhere, including explicit overzoom above common13.
- **Regional:** replace only fully supported12/13 tiles with derived Swiss parents;
  original Swiss14–18 exact; common elsewhere. Offline partial11/10 cells stay absent
  from delivery. Source availability is independent of requested detail level.

`regional_parent_evaluation.mjs` changes both visual delivery contracts in memory
with min8/max18 and the same finite common bounds. No normal startup imports it.
Installed MapLibre6.11.2 still uses one terrain source,128 mesh, loaded-parent reuse
and DEM-neighbor backfill; there is no cross-source DEM fusion. Presentation remains
the frozen production IGOR/exaggeration/atmosphere policy. This is one local
diagnostic stream, not a production resolver or common-height terrain product.

Viewport1440×900/DPR1, Chromium151.0.7922.34, localeen-GB/Europe-London. Benchmark
[7.76121329,45.97910794]; exact cameras, bounds, used/requested DEMs and hashes are
in [renderer evidence](regional-parent-renderer.json).

| Purpose | Camera zoom/pitch/bearing | Actual settled geometry DEM levels (regional) |
| --- | --- | --- |
| Landscape | 9.4/45/0 | 8 |
| Planning | 11.4/45/0 | 9–10 |
| Close context | 13.2/55/0 | 10–13 |
| Interior parent | 14.2/0/0, then180 | 13 |
| Interior child | 15.2/0/0 | 13–14 |
| Interior detail | 16.2/0/0 | 14–15 |
| Pitched interior | 14.2/30/0, then180;15.2/30/0;16.2/45/0 | Separately recorded, same requested source contract |
| West/south edges | 15.2/55/0; west also180 | Multiple loaded levels across support |

The unpitched interior-parent footprint is about4.2×2.6 km in LV95; the pitched
parent about5.2×3.1 km. Both remain inside the10 km source selection, though the
larger scene extends beyond the protected circle. Wide context views include the
regional edge and are not claimed to be interior-only.

The pitched parent comparison visibly matters: the control's still-common geometry
suppresses the summit shape while finer Swiss hillshade is already present. A
Swiss-derived parent carries the summit/ridge form into the subsequent fine Swiss
view. Channels/ledges remain in fine relief; rotations preserve source information.
Fine child/detail captures converge between strategies, as expected from identical
selected terrain. Top-down screenshots alone would understate the silhouette change.

The bounded continuous sequence independently tests interior14.2→15.2→16.2→14.2
with rotation, then moves west/outside and returns to planning. Nine moving samples
and a midpoint/end capture per leg record loaded DEM levels and exaggerated center
height. Interior used levels progress13→13/14→14/15 and back13. Within the sampled
supported interior there is no large unrelated-family refinement; relief continues
to sharpen. This warm-cache sampled sequence and pitched static checks do **not**
certify invisible motion for every ridge, cold-load state, camera or device.
MapLibre reuse/loading and geometry versus hillshade levels still differ.

West/south bands and walls remain conspicuous under lateral movement and rotation;
fine-level edge captures are effectively unchanged. Coarse source changes can also
appear patchwise in wider views because relief and geometry request different
levels. Regional parent propagation is not a justification for enabling it globally
at planning scale. No supported interior black/flat void appeared; finite common
perimeter/z0–7 and global water policy remain unresolved. Satellite was not a new
comparison; suppression is untouched.

Across four completed runs,1,935 local responses were200, zero completed HTTP
failures/page errors, and24 request failures were `ERR_ABORTED` navigation
cancellations. Returned body volume205.47 MB includes cache repeats and is not
wire throughput. Interior return/rotation reused cache (zero new responses in
recorded return legs). All capture reports retain native contributor/product/height
headers and body hashes. MapLibre queries include1.45 exaggeration and loaded mesh
behavior; they are not analytical elevations. Existing basemap sprite/filter and
expected Weather-fixture warnings were retained. Owned servers were stopped.

## Provenance, cost and validation

The separate derivative identity is
`b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672`.
[Terrain Product metadata](regional-parent-product.json) uses the existing model:
known Swiss source/revision, preserved LN02, processing operation/basis, delivery
versus offline support, protected intent and unresolved transition. No type extension
or production metadata import was needed. The derivative has one contributor;
the evaluation stream records whether a response is this parent derivative,
original Swiss or original common. There are no mixed cells or confidence claims.
Source-specific rights remain inherited; no public service is launched.

Five compressed field/support files and30 complete PNGs (25 basis checks plus5 new
parents) occupy **14.69 MB**, including3.54 MB tiles; the five new parent PNGs total
0.632 MB. Generation79.02 s; independent rebuild81.23 s (both include input
verification). All35 file hashes,
source-VRT hash, support counts and complete manifest identity match exactly.
The100 canonical Swiss assets, original11,429 Swiss tiles, six common assets and
2,730 common tiles were verified; no canonical product was overwritten. The separate
adapter cache contains1,387 checked terrain tiles (125.05 MB) and0.522 MB of
contributor masks, covering numerical controls and browser requests. It is not
included in the new-parent cost or a complete pyramid. Browser/capture costs are
bounded observations, not benchmarks.

Validation:38 synthetic Atlas Python tests;167 active Node application/model tests,
one existing optional skip; lint, TypeScript and application-only Vite build pass.
New tests cover complete/partial/absent support, weighted observed means, global
parent alignment, metadata/native-height semantics, isolated visual transform and
protected-interior/source-change invariants. Tests use an empty external-root
override and need no terrain service. Existing rasterio/NumPy deprecation and large
bundle warnings remain. No unrelated clock-dependent test changed or failed.
Metadata, documentation references, source/product hashes and production diff were
checked. Build omits unrelated GFS publication validation/copying.

## Conclusion and smallest next investigation

**M:** the13→14 source-change component collapses from39.82 to0.71 m RMS when the
parent belongs to the Swiss family. A **regional terrain pyramid** is therefore a
justified concept for supported internal refinement. It needs per-level support,
explicit partial cells, immutable source/derivation identity, native height semantics
and a separately defined geographic/common handoff. This is not the final contract.

**M:** no natural handoff is found through10. The delivered stream moves its large
source jump to11→12, and same-level spatial disagreement remains. LOD consistency
and spatial reconciliation are measurably distinct, but both interact with finite
support and loading. This diagnostic separates their causes; it does not produce
an acceptable complete hierarchy. Outcome: **internal consistency improves, no
accepted common handoff**. No production change.

**H — single smallest next investigation:** one bounded **support-aware same-level
boundary assessment** on the problematic west/south frontier and its neighboring
valid Swiss cells. Separate loss caused by whole-tile publication from genuine
Swiss/common disagreement, using these native-height parent/support fields and
retained stable-terrain evidence. Establish the support and physical requirements
for any later transition representation while preserving the protected interior.
No transition method, further acquisition, height correction or generic resolver is
authorized or implemented by this recommendation. Stop here.

## External estate and exact reproduction

Under `MERIDIAN_DATA_ROOT` (documented sibling default):

- `derived/atlas/riffelhorn/riffelhorn-regional-parents-v1/`: lightweightVRT,
  fields/support, complete tiles, manifest, Atlas metadata; `-rebuild` independent.
- `derived/atlas/riffelhorn/riffelhorn-terrain-hierarchy-v1-regional-parent-control/`:
  separate inherited common/fine adapter cache with contributor masks/receipts.
- `experiments/atlas/riffelhorn-regional-parents-v1/`: generation timings,
  measurements, profiles/figures, capture/request logs and oblique checks.

From repository root with the retained scientific environment:

```powershell
$python='C:/Users/gbsam/Documents/Projects/meridian-data/earth-lab/.venv/Scripts/python.exe'
& $python scripts/atlas/regional_parents.py prepare
& $python scripts/atlas/regional_parents.py prepare --suffix=-rebuild
& $python scripts/atlas/regional_parents.py verify
& $python scripts/atlas/analyze_regional_parents.py
& $python scripts/atlas/regional_parents.py serve --port 4184
# Separate terminal, after SERVING appears; sequential fresh browser runs:
node scripts/atlas/capture_regional_parents.mjs control '<DATA>/experiments/atlas/riffelhorn-regional-parents-v1/captures'
node scripts/atlas/capture_regional_parents.mjs regional '<DATA>/experiments/atlas/riffelhorn-regional-parents-v1/captures'
node scripts/atlas/capture_regional_parents.mjs control '<DATA>/experiments/atlas/riffelhorn-regional-parents-v1/oblique' oblique
node scripts/atlas/capture_regional_parents.mjs regional '<DATA>/experiments/atlas/riffelhorn-regional-parents-v1/oblique' oblique
# Stop owned server; verify retained evidence/metadata:
& $python scripts/atlas/finish_regional_parents.py
```

`prepare` refuses an existing immutable build; these are the original commands.
Use another explicit named sibling for a repeat and compare its manifest; never
overwrite a source product. Native scientific inputs are retained, not reacquired.
Normal `npm.cmd run dev` remains AWS and requires none of these products/services.
Capture reproduction is controlled, not bitwise reproducible across live basemap,
browser/driver/UI timing; product/support reproduction is bitwise verified.

```powershell
$env:MERIDIAN_DATA_ROOT='<absolute empty directory outside repository>'
& $python -m unittest discover -s scripts/atlas -p 'test_*.py'
$tests=Get-ChildItem scripts/atlas,scripts/weather,scripts/route,scripts/ui -Filter 'test_*.mjs' | ForEach-Object { $_.FullName }
node --test $tests
npm.cmd run lint
npx.cmd tsc -b
node --input-type=module -e "import {build} from 'vite';import react from '@vitejs/plugin-react';await build({configFile:false,plugins:[react()],publicDir:false,build:{outDir:'node_modules/.tmp/regional-parent-app-build'}});"
```

Remove the empty-root override before external-product commands. Large assets,
outputs and captures remain outside Git. No new dependency, Lab or follow-on
experiment was introduced.
