# WR008: GFS native-grid point-sampling and query semantics

**10 October 2026.** Public main, starting checkpoint
**`5b58274a1b8e4e5cb88b8f79496e0f0456cf6aea`**. Clean tree and exact main/origin/main
alignment after fetch, zero divergence. Read relevant WR001–007 evidence,
[programme](research-programme.md), [register](research-register.md),
[sources](sources.md), [temperature semantics](temperature-semantics.md),
[compatibility](forecast-reference-compatibility.md), Foundations engineering/economics
and external-data preservation conventions. Existing WR007 utility/pins/tests are
reused unchanged. No private access, dataset acquisition or production modification.

## 1. Conclusion and evidence scope

**OUTCOME A — VERIFIED NATIVE-GRID QUERY SEMANTICS**, within one pinned real GFS
temperature field and the finite Windows query profile below. **19 nearest and 15
qualified bilinear queries** agree with independently decoded GDAL values and its
separate sampling kernel. Four polar-cap bilinear requests are explicitly unsupported;
nine malformed/invalid requests are rejected. Nothing is silently replaced or discarded.

Maximum independent sampled difference **0.000018310546863631316 K**, mean absolute
difference **0.00000735700540718319 K**. Actual contributing-node decoder differences
pass WR007's exact binary32 rounding check. Weights match exactly; GDAL's bilinear
result equals the independently calculated dot product for every accepted fixture.
No unexplained difference. Agreement establishes numerical sampling, **not weather
accuracy, a finer meteorological resolution, route performance or offline suitability**.

[WR006](midas-historical-measurement-support.md) stays **Outcome C / reference Decision C**.
Strict and revised MIDAS targets remain blocked. No forecasts are compared against
observations and no GFS/UKV ranking, blending, provider choice or production API follows.

Labels: **OBSERVED** = actual input/query/measurement; **VALIDATED** = finite numerical
guard/replay/comparison; **INFERRED** = engineering implication; **PROPOSED** = future
work; **UNRESOLVED/BLOCKED** = missing evidence. Synthetic mathematical tests are
explicitly separate from real-data evidence and predictive verification.

## 2. Immutable input and actual grid

The [WR007 field](historical-gfs-temperature-field-pilot.md) is locally present in
its previously recorded owned research scratch. Size and SHA256 were checked before
sampling. No recursive data-root search was needed after that exact pin was found;
no legacy derived publication was substituted, copied, moved or decoded instead.

| Identity | Actual retained evidence |
|---|---|
| Raw message | `gfs-2025011500-f024-t2m.grib2`, **874,115 bytes**, SHA256 `0b95fc06fe9ca08de57f9c5089b8fcd5d7b6a42977b35f669da65ec0f43f40e4` |
| Source | NOAA/NCEP GFS through NOAA NODD, `gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024`, message 581; original range/provenance in WR007 |
| Time | Reference **2025-01-15 00 UTC**, +24 h, valid **2025-01-16 00 UTC**, instantaneous template 4.0 |
| Quantity | GRIB 2 discipline/category/number **0/0/0**, fixed surface **103**, **2 m above model ground**, **K** |
| Grid | Template 3.0 `regular_ll`, **1440 columns × 721 rows**, 1,038,240 points, scan mode **0** |
| Geometry | Latitude **90 to −90**, descending by **0.25°**; longitude **0 to 359.75**, increasing by **0.25°**; point registration, no duplicate 360° column |
| Earth | Shape 6 sphere, radius **6,371,229 m**; no claim of WGS84/EPSG:4326 or a new coordinate transformation |
| Packing/missingness | Retained template 5.3, E=0/D=2, second-order differencing; zero bitmap/internal missing values, all finite |
| Decoded authority | Little-endian float64 field SHA256 `01dad7249c0f441c65a4677455ce1340797dab82d0045a1e6fba95620fdb91e3`, re-established in WR008 |

WR007 checks actual numeric metadata and every latitude/longitude before values
are used. WR008 derives dimensions, increments, orientation and bounds from that
validated metadata and rejects unsupported geometry. Its mathematics is not an
unverified nominal 0.25° assumption. The delivered grid remains distinct from the
FV3 computational mesh. Arrays are not transposed or reordered.

Native storage `values[row,column]` → logical grid node → angular coordinates:
`lat = north−row×dy`, `lon = west+column×dx`. GDAL's half-cell affine corner is
`(-0.125,90.125)`; **pixel centres** identify these same native nodes. Apparent raster
extents outside ±90° are not additional geographic coverage. Latitude is not periodic.

## 3. Frozen research query contract

[Query profile](../../../scripts/weather-research/wr008/query-profile.json) frozen
at **2026-10-10T16:20:04.046987+00:00**, before WR008 temperatures were queried:
SHA256 **`adaf7d3ae0365906302d1d56f8e73399bb40be50dc1879bc666d8acb3fc574be`**.
Nineteen coordinate fixtures × two methods, plus nine invalid structures = **47
ordered results**. Locations reflect geometric coverage and terrain-region relevance,
not expected temperature realism, forecast agreement or a station selection.

Input has exactly named `latitude`, `longitude`, `method`; no implicit axis order.
Methods are `NEAREST` and `BILINEAR`, case-sensitive. Finite numeric longitude may
be outside the canonical range: reduce modulo 360, retain the original input and
return [0,360) native and [−180,180) public labels. Longitude wraps, never clamps.
Latitude outside [−90,90], non-finite values, booleans/strings/null, missing/extra
keys and unsupported methods fail explicitly. Binary64 coordinate precision is
finite: sub-ULP modulo endpoint rounding to 360 is canonicalised to zero, rather
than an out-of-bounds column. Equivalent representable ±360 fixtures agree exactly;
arbitrary decimal strings are not promised infinite-precision equivalence.

A receipt has common, inseparable field/source/grid/time/height/unit/hash/version
context and individual query status, original/normalised coordinate, method,
Kelvin value, node indices/coordinates/values and weights. The compact committed
receipt refers to the full deterministic receipt hash; a detached temperature
number is not a qualified scientific answer. There is no arbitrary valid-time
request: this pilot has one explicit field; extra time keys are malformed queries.

### Nearest definition

**Nearest in angular grid-coordinate space**, independently by row and cyclic
column. It is **not geographically nearest by great-circle/geodesic distance**.
Independent-axis rounding minimises that chosen coordinate-space distance for
this regular grid, apart from the documented pole equivalence convention. Exact
halfway ties use increasing index: south/east. `floor` plus an explicit fractional
comparison avoids language-specific bankers' rounding and arbitrary tie tolerance.
Column 1440 wraps to zero; pole rows use canonical column zero because different
longitude labels represent the same physical pole. Original query longitude remains
visible. A synthetic spherical-distance counterexample shows that angular-axis and
geographic nearest definitions differ; neither is advertised as universally preferable.

### Qualified bilinear definition

Let fractional column/row coordinates be `c+u`, `r+v`, with integer northwest
indices. Weights are `(1−v)(1−u), (1−v)u, v(1−u), vu` on the four native nodes.
The next longitude column is cyclic: 1439 → 0 is a **0.25° interval** using an
unwrapped longitude chart, not 359.75° separation. The 180/−180 label boundary is
likewise continuous. No latitude wrap, extrapolation, elevation adjustment or
array modification occurs.

Both bounding rows must be non-polar. For this field the permitted latitude
interval is **[−89.75,89.75]**. At the southern endpoint, choose the adjacent
interior rows with weight one on −89.75; never invent a second south-polar row.
Exact poles and open polar caps return `UNSUPPORTED_POLAR_CAP_BILINEAR`. The
singular polar longitude geometry is deliberately outside this finite bilinear
contract; nearest remains available as an explicitly requested method, never fallback.

Weights must be finite, non-negative and sum to one within **8 eps64** (four-term
arithmetic guard). **All four nodes must be valid, including zero-weight nodes**:
any explicit mask returns `MISSING_CONTRIBUTING_NODE`; an unmasked non-finite node
returns `UNINTERPRETABLE_NODE`. This conservative policy is explicit, without
renormalisation or silent nearest substitution. Actual input missingness is zero;
mask tests are synthetic, not a GRIB bitmap demonstration.

## 4. Independent sampling and numerical rules

Primary: existing Python **3.12.6**, ecCodes Python/native **2.48.0**, NumPy **2.5.2**.
Reference: separate existing Python **3.12.6**, rasterio **1.4.3**, GDAL **3.9.3**,
NumPy **2.5.3**, independent degrib/g2clib decoding. No packages installed. SciPy
is absent; its absence did not require adding a dependency.

Reference reuses WR007's GDAL identity/units/time/geometry guards. GDAL's inverse
affine and georeferenced pixel sampling independently determine nearest indices,
with periodic-edge and pole adapters. Bilinear nodes come from that affine mapping
and original GRIB windows. A small four-node patch spanning the periodic seam uses
unwrapped coordinates; GDAL's **warp bilinear kernel** samples its centre at the
requested coordinate, with source and destination in the same verified sphere CRS.
The 0.001° destination pixel is only a one-point numerical probe, not a resampled
forecast publication or increased meteorological resolution. Units/longitude defaults
are disabled. No hidden reprojection or copy of a full output grid is introduced.

The installed `rasterio.warp.reproject` documentation and a synthetic affine
two-by-two patch were inspected/tested locally. Existing version-specific GDAL
decoder documentation/source and licences remain [WR007 evidence](sources.md#wr007-exact-field-and-independent-decoder-evidence);
they were not freshly fetched. The comparison uses genuinely different decoding
and interpolation routines, not two interfaces to one sampler. **Boundary, pole and
missing policies are shared explicit research choices**; their rejection is tested,
not independently validated as the only scientifically possible policy.

Before accepting a sample, every independently decoded contributing value must
pass WR007's exact g2clib rounding-profile check. For bilinear differences, the
allowance is the weighted absolute contributing decoder residual plus a separate
float64 arithmetic bound. Nearest uses its exact selected-node residual.
Define `P = 1+360/dx+180/dy`; weight comparison bound is **32 eps64 × P**;
kernel/value arithmetic bound is **128 eps64 × maximum node magnitude × P**.
These conservative operation/coordinate-conditioning guards were fixed before
real sampling, not tuned to disagreements. Actual weight residual and GDAL-kernel
versus independently formed dot-product residual are **zero** on all fixtures.
The allowances are numerical error guards, not meteorological uncertainty bars.

| Real comparison category | Actual result |
|---|---:|
| Nearest / supported bilinear | **19 / 15**, all pass |
| Numerical queries compared | **34** |
| Native-node value comparisons | **20**: 19 selected nearest nodes plus one exact-input bilinear result |
| Exact native input-node comparisons | **2**: one coordinate under both methods |
| Unsupported polar bilinear status comparisons | **4**, same explicit policy |
| Invalid structure/type/range requests | **9**, internally rejected; no independent invalid-parser claim |
| Maximum / mean absolute independent difference K | **0.000018310546863631316 / 0.00000735700540718319** |
| Maximum weight difference / GDAL kernel versus dot-product K | **0 / 0** |
| Unexplained numerical / node / coordinate differences | **0** |

## 5. Frozen locations and actual temperatures

All values are **K**, original forecast units. Decimal display below preserves the
recorded numerical values; no plausibility filtering, correction or Celsius conversion.
Precise coordinates are fixtures in named terrain regions, not verified summit
positions or scientific station observations. NN is the selected native value;
BI is an angular interpolated diagnostic, not an actual sub-grid measurement.

| Fixture | Latitude, input longitude ° | NN K | BI K / explicit status |
|---|---|---:|---|
| Native node | 50, 0 | 282.52792968750003 | 282.52792968750003 |
| Longitude halfway | 50, 0.125 | 282.27792968750003 | 282.40292968750003 |
| Latitude halfway | 49.875, 0 | 282.7079296875 | 282.6179296875 |
| Four-node interior | 49.9, 0.1 | 282.52792968750003 | 282.29672968750003 |
| Northern | 62.3, −6.4 | 281.7879296875 | 281.9255296875 |
| Southern | −40.12, 175.13 | 295.8679296875 | 292.1264256874999 |
| Antimeridian | 12.3, 179.875 | 299.3279296875 | 299.3509296875 |
| Equivalent negative | 12.3, −180.125 | 299.3279296875 | 299.3509296875 |
| Equivalent +360 | 12.3, 539.875 | 299.3279296875 | 299.3509296875 |
| Periodic zero seam | 3.3, −0.125 | 300.7579296875 | 300.8039296875 |
| Equivalent seam | 3.3, 359.875 | 300.7579296875 | 300.8039296875 |
| North cap | 89.875, 20 | 251.76792968750001 | UNSUPPORTED_POLAR_CAP_BILINEAR |
| South cap | −89.875, 20 | 247.6879296875 | UNSUPPORTED_POLAR_CAP_BILINEAR |
| North pole | 90, 123 | 251.6679296875 | UNSUPPORTED_POLAR_CAP_BILINEAR |
| South pole | −90, −44 | 247.6879296875 | UNSUPPORTED_POLAR_CAP_BILINEAR |
| North BI endpoint | 89.75, 20.125 | 251.76792968750001 | 251.76792968750001 |
| South BI endpoint | −89.75, 20.125 | 247.4079296875 | 247.4079296875 |
| Scottish Highlands | 56.8, −5.0 | 278.9379296875 | 278.9059296875 |
| Alpine region | 45.975, 7.775 | 260.4879296875 | 261.5437296875 |

The Alpine/Scottish differences between methods demonstrate interpolation's numerical
effect only. Actual terrain elevation, model orography, exposure, coastal/surface
support, inversions and representativeness remain unmeasured. Querying a summit or
narrow valley coordinate does not mean it is resolved. This remains the model's
ground-relative 2 m diagnostic on its delivered grid, **not necessarily actual air
temperature 2 m above the real terrain**. No lapse-rate correction, altitude
downscaling or local accuracy inference is introduced.

## 6. Replay, synthetic evidence and resources

[Utility and commands](../../../scripts/weather-research/wr008/README.md),
[input/profile pins](../../../scripts/weather-research/wr008/input-pins.json),
[compact receipt](../../../scripts/weather-research/wr008/sampling-receipt.json)
and [tests](../../../scripts/weather-research/wr008/test_gfs_point_sampling.py)
are isolated, removable and do not enter production imports. Exact full external
receipt: **50,170 bytes**, SHA256
**`f2bfcbc338217744b5aafaa1311ab0a0b76ce500a0e6527729c2ffd65e720a21`**.
Repeated real runs are byte-identical, including every node/weight/result/error.
Input and decoded values/masks remain unchanged and read-only during queries.
Transient memory/timing measurements are separate from deterministic science.

**36 synthetic tests + one opt-in real replay test pass, zero skips**. Synthetic
constant and affine fields, convex bounds, exact nodes, halfway ties, spherical
counterexample, wrap/seam, poles/caps/endpoints, no latitude periodicity, invalid
structures/types/non-finite coordinates, masks/zero weights, unfrozen profiles,
wrong grids/orientation, missing reference cases, disagreement and immutability
are mathematical/guard evidence. The real test repeats both decoding/sampling paths,
checks all 47 outcomes, comparison counts, unchanged source and receipt fingerprint.
No synthetic case becomes an actual missing GFS record or empirical skill result.
Existing rasterio/NumPy 2.5 shape deprecation warnings are retained.

One standalone measured run, using Windows PSAPI process counters:

| Resource | Observed value / qualification |
|---|---|
| Primary baseline working set | **34,750,464 bytes**, after NumPy import before ecCodes decode |
| Primary before queries / after comparison working set | **100,913,152 / 101,900,288 bytes** |
| Primary lifetime peak working set | **117,510,144 bytes**, includes decoding/temporary coordinate arrays/imports |
| Reference baseline / after working set | **50,237,440 / 64,339,968 bytes** |
| Reference lifetime peak working set | **89,501,696 bytes**, includes GDAL decode/cache/imports |
| Sum of separate peaks | **207,011,840 bytes**, conservative concurrent upper bound, **not measured simultaneous total** |
| Primary / reference peak PagefileUsage counters | **742,977,536 / 706,576,384 bytes**; Windows process commit counters, not resident RAM or actual disk writes |
| Complete elapsed / reference elapsed | **1.3733954 / 0.2232134 s**, one standalone local run, includes startup/decoding; no cold-start or throughput benchmark |
| GDAL intermediate scratch | **9,346,222 bytes**, removed each reference run; raw WR007 source borrowed in place, no source copy |
| New scientific/documentation retrievals | **0 requests / 0 scientific bytes**; no network lookup or package install in scripts/tests |

Owned scratch final size and a conservative intermediate bound are recorded with
validation in the [development log](../../development-log.md). They remain below
**150 MB**. Decoding transient coordinate arrays is reused from WR007; the query
experiment does not need permanent full-field copies. Working sets include native
resources and cache effects; no allocation attribution, mobile budget, route-scale
performance, battery/GPU or production footprint follows.

Automatic npm/pip update checks are disabled; validation invokes installed node
executables directly. No external documentation was fetched or dataset acquired.
Git fetch/push are required repository control; their traffic and unrelated OS
activity are unmetered. **Zero total network traffic is not claimed.** There are no
paid dependencies, cloud resources, source moves or external data-directory changes.
NOAA source attribution and existing software notice limitations remain WR007's;
no binary is redistributed and no new commercial/offline legal clearance is asserted.

## 7. Architectural implications and open limits

**INFERRED:** point/route consumers need qualified field/time/height/native-grid/source
identity, method name, original/normalised query coordinate, selected nodes/weights
and explicit unsupported/missing/error states. A method choice is scientifically
visible; renderer caches and interpolated presentation cannot silently become source
authority. Shared concepts can outlive providers, but this regular-grid indexing,
cyclic longitude and polar policy do not automatically transfer to rotated,
projected, curvilinear, unstructured or limited-area grids. No permanent interpolation
library, tile encoding, database, cloud, production API or universal schema is chosen.

Actual bitmap interpolation, geographic-nearest semantics, alternative polar
schemes, model terrain/surface support, regional grids, route performance and empirical
forecast verification remain unsupported/unresolved. Numerical precision bounds are
not uncertainty estimates. Global/regional, ensemble, precipitation/cloud/wind/pressure,
mountain, observation/nowcasting, provenance, offline and cost tracks remain active.
WR008 expands the earlier no-interpolation WR007 proposal only because this task
explicitly authorised qualified bilinear research; historical conclusions stay intact.

Validation runs, documentation links/full diff, WR007 receipt/input immutability and
Atlas/Weather preservation are recorded in the development log. Full Weather
materialisation and expensive unrelated scientific replays are excluded; no unrun
suite is represented as passing. No application integration or later task began.

## 8. Exactly one next bounded task — NOT BEGUN

**WEATHER — HISTORICAL GFS PRECIPITATION-INTERVAL SEMANTICS AND DECODING PILOT — NOT BEGUN.**

**Objective:** expand scientific capability beyond instantaneous temperature by
establishing one actual accumulated-precipitation message's physical quantity,
interval/time metadata, units, missingness and independent numerical decoding.
Temperature's instantaneous interpretation must not be reused for accumulation.

**Required evidence/dependencies:** separate acquisition authorisation; a unique
authoritative inventory/object, actual parameter/level/time-template definitions,
lawful bounded extraction and compatible installed decoders. Prefer the same Jan 15
2025 00 UTC/+24 product family for controlled provenance, but do not assume a
0–24-hour accumulation or substitute another interval silently. Establish the actual
encoded accumulation interval before interpreting values. No reference eligibility
or production-provider choice is required; WR006 remains blocked.

**Scope/acceptance:** one cycle, lead, variable and GRIB message; source/hash/packing/
grid/interval/unit/mask receipt and independent numerical agreement or a precise
negative result. Distinguish accumulated amount, average/rate and valid-time endpoint.
No forecast errors, derived rainfall risk, routing, new tiles or production ingestion.

**Proposed resource limits:** at most **50 MB new transfer, 20 retrieval attempts,
150 MB owned scratch**, no paid dependency/account/cloud and no full oversized
product download. Reconfirm these limits in the separately authorised task.

**Stop:** after this finite interval/decoding result or an exact source/tool/rights
blocker. Do not collect multiple fields/periods or reinterpret precipitation as
verified local weather. This adds information beyond more temperature/route refinements;
future priorities remain revisable. **The subsequent task has not begun.**
