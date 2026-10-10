# WR007: historical GFS temperature-field acquisition, decoding and integrity pilot

**10 October 2026.** Public `gbsamirahmed/project-meridian`, main. Required and
verified clean starting checkpoint **`8782d6d92fd59dbb75ddf9157b5e3fdd8ef4c19d`**;
fetched origin/main matched at zero ahead/behind. Relevant [WR001–006](README.md),
[programme](research-programme.md), [source assessments](sources.md),
[temperature semantics](temperature-semantics.md), [acquisition gates](temperature-acquisition-gates.md),
[draft verification protocol](temperature-verification-protocol.md),
[legacy inventory](legacy-evidence-inventory.md), [Foundations engineering](../../foundations/engineering.md),
[economics](../../foundations/economics.md) and [external data layout](../../phase-4-migration-inventory.md)
were reviewed. Existing Weather code was inspected as engineering evidence, not
scientific authority. No private repository was accessed.

## 1. Executive conclusion and exact scope

**OUTCOME A — VERIFIED NUMERICAL FIELD.** One actual historical NOAA/NCEP GFS
operational 2 m temperature forecast was anonymously acquired through NOAA NODD,
decoded using **ecCodes 2.48.0** and independently using **GDAL 3.9.3 degrib/g2clib**.
All **1,038,240** grid points agree in identity, orientation, time, Kelvin units and
absence of missing values. Numerical agreement is **not bitwise equality**:
maximum difference **0.00002197265627046363 K**, fully explained by g2clib's
binary32 calculation. Its documented rounding profile reproduces every GDAL value
exactly and every difference satisfies a source-derived per-cell error bound.

The target is exactly **2025-01-15 00:00 UTC, +24 h, valid 2025-01-16 00:00 UTC**,
delivered **0.25° global latitude/longitude**, temperature at **2 m above model ground**.
No date/cycle/lead/field/model was substituted. This user-authorised target refines
WR006's historical next-task proposal, which mentioned 1 January; that proposal
remains unchanged as history. GFS is a research candidate, not a production choice.

This demonstrates finite source readability and numerical integrity in the checked
Windows environment. It does **not** demonstrate predictive skill, outdoor usefulness,
seasonal completeness, model elevation suitability, arbitrary packing, mobile/browser
deployment or sustainable global delivery. [WR006](midas-historical-measurement-support.md)
remains **Outcome C / reference Decision C**. Neither strict nor revised MIDAS targets
are adopted or reopened; both observation-based comparisons remain blocked.

Evidence labels: **OBSERVED** = inspected response/message/value; **DOCUMENTED** =
authoritative source or installed notice; **INFERRED** = engineering consequence;
**UNRESOLVED/BLOCKED** = unsupported fact or missing prerequisite. Catalogue evidence
alone is not numerical evidence, and hashes establish integrity, not accuracy/authenticity.

## 2. Discovery, source and bounded acquisition

Recursive filename/context discovery in the authorised external data root, allowing
case/extension/date variations and hidden environments, found no matching raw January
target GRIB or inventory. The retained September 2026 publications and their manifests
were not substituted. The original Earth Lab environment lacks ecCodes, but its
recorded base Python environment already has ecCodes 2.48.0. **No installation,
dependency change, source move or data-directory reorganisation occurred.** Only
owned external WR007 scratch was created; originals and accepted stores stayed intact.

[NOAA's NODD registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/) identifies the
anonymous bucket. Unlike the earlier GDEX listing-only route, this exact NOAA route
was inspected and read. No GDEX authentication/subset service was used. The registry
contains dated operational descriptions; they do not establish this historical
model's exact executable/suite revision. That revision remains **UNRESOLVED**.

**Parent:**
`gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024`,
[exact object](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024).
HEAD: HTTP 200, **537,858,357 bytes**, Last-Modified `2025-01-15 03:44:04 GMT`,
ETag `e9f55c2f3f45d6cdb3aac9e4b7a36aba`. Last-Modified is object delivery metadata,
not the forecast reference/valid time or a demonstrated operational issue time.
The oversized parent was **not downloaded**.

The [exact index](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024.idx)
returned 41,250 bytes, SHA256
`fa11be72ab29ea43520dc6a6fc8de81bd8e0e024c96da94ed05495bc43b39dcb`.
Its unique required line is
`581:415390073:d=2025011500:TMP:2 m above ground:24 hour fcst:`;
message 582 begins at 416264188. One inclusive range **415390073–416264187**
returned HTTP **206**, exact
`Content-Range: bytes 415390073-416264187/537858357`, Content-Length **874,115**,
matching parent ETag/modified time and **874,115 actual body bytes**.
No concatenated ranges, fallback download, redirects, retries, authentication,
cookies, credentials, paid account or licence acceptance were used.

The bounded acquisition helper refused unexpected range status/length before reading
the body and imposed streaming/request ceilings. The GRIB indicator declared the
same 874,115-byte length; edition 2 and terminal `7777` confirmed framing, followed
by actual decoder identity checks. Framing alone is not parameter verification.

**Raw SHA256:** `0b95fc06fe9ca08de57f9c5089b8fcd5d7b6a42977b35f669da65ec0f43f40e4`.
Input remains outside Git, named `gfs-2025011500-f024-t2m.grib2` in owned WR007 scratch.
The exact object/range is original provenance; this descriptive local name is not authority.
Acquisition started `2026-10-10T14:33:13.202647+00:00`; timestamps/HTTP evidence are
separate from deterministic numerical serialisation.

## 3. Actual message identity, tables and time

These are **OBSERVED message fields**, not inferred solely from an inventory name:

| Responsibility | Actual metadata and interpretation |
|---|---|
| Edition/producer | GRIB 2; centre **7**, subcentre **0**, US-NCEP (`kwbc`); master table **2**, local table **1** |
| Process | Operational status **0**, processed-data type **1** forecast, generating-process type **2** forecast, identifier **96**, background **0**. Exact binary/suite version unknown |
| Parameter | Discipline **0**, category **0**, number **0**: temperature, K. ecCodes friendly name `2 metre temperature` / `2t`; GDAL `TMP`; numeric keys are checked independently of these aliases |
| Vertical support | First fixed surface **103**, scale **0**, scaled value **2**, `heightAboveGround`, level **2**. Diagnostic at model-ground-relative 2 m, not skin/dew-point/potential temperature or station height |
| Time | Significance **1** start of forecast; date **20250115**, time **0000**, step-unit code **1** hours, forecast time/start/end **24**; validity **20250116 0000** |
| Product template | **4.0** / template number **0**; `stepType=instant`. No accumulation/mean interval. Reference + 86,400 s = valid time; GDAL independently reports Unix seconds 1736899200/1736985600 |
| Packing | **5.3** / representation number **3**, complex packing with second-order spatial differencing; 32,065 groups; bits-per-value metadata **13**, E=**0**, D=**2**, reference **22276.79296875** |
| Missingness | No bitmap (**0**), internal missing-value management **0**, actual missing count **0**. Both masks all valid; 1,038,240 finite decoded values |

[NCEP temperature table](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-2-0-0.shtml),
[fixed-surface table](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-5.shtml)
and [template 5.3](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp5-3.shtml)
were read on 10 October 2026. These living definitions support numeric interpretation;
they are not claims that this object uses the newest operational table/model version.
Installed ecCodes definitions and GDAL's actual PDT values are preserved in the receipts.
ecCodes' generic `missingValue=9999` is **not an encoded missing observation** here;
it is not used to mask temperatures. Bitmap/internal-missing variants are deliberately
unsupported by this finite utility, rather than assigned guessed sentinel rules.

## 4. Grid, indexing and coordinate integrity

Actual template **3.0**, `regular_ll`, **Ni=1440, Nj=721**, points **1,038,240**.
Scan mode **0**: increasing longitude along rows, decreasing latitude between rows,
no consecutive-j or alternating-row scan. Coordinates from ecCodes were compared at
**every point** against `latitude=90−0.25×row`, `longitude=0.25×column`; they match exactly.
First point **90° N, 0°**, last **90° S, 359.75°**. Both polar rows exist; there is
no duplicate 360° endpoint. Pole longitudes are angular labels at the same geographic
pole, not evidence of distinct spatial positions.

Earth shape **6**, spherical radius **6,371,229 m**. GDAL's CRS independently identifies
this sphere. This is **not an assertion of WGS84/EPSG:4326** or a reprojection.
The delivered regular grid is not the FV3 computational mesh. Native point registration
is preserved; GDAL's affine corner is `(-0.125,90.125)` with `(0.25,-0.25)` spacing so
its **pixel centres** identify the same points. Half-cell raster extents outside ±90°
must not be interpreted as atmospheric coverage outside the poles.

GDAL settings `GRIB_NORMALIZE_UNITS=NO` and `GRIB_ADJUST_LONGITUDE_RANGE=NO` prevent
automatic Celsius conversion and column rearrangement. No interpolation, filtering,
resampling, altitude correction or orientation change was performed. Representative
indices were fixed before reading their magnitudes:

| Row,column | Latitude | Original longitude | Reversible −180…180 label | ecCodes K |
|---|---:|---:|---:|---:|
| 160,0 | 50 | 0 | 0 | 282.52792968750003 |
| 520,0 | −40 | 0 | 0 | 285.8779296875 |
| 360,719 | 0 | 179.75 | 179.75 | 300.0579296875 |
| 360,720 | 0 | 180 | −180 | 300.0579296875 |
| 360,1439 | 0 | 359.75 | −0.25 | 299.8379296875 |
| 0,0 | 90 | 0 | 0 | 251.6679296875 |
| 720,0 | −90 | 0 | 0 | 247.6879296875 |

Longitude label mapping is `(lon+180) mod 360−180`; inverse is `label mod 360`.
The full array remains in 0–360 order. An additional fixed 55° N, 357° point is
retained in the local receipt, not used for a station or outdoor interpretation.

## 5. Numerical results and independent agreement

Primary ecCodes **float64 Kelvin** field statistics, unweighted across grid points:

| Statistic | Observed value |
|---|---:|
| Valid / missing | **1,038,240 / 0** |
| Minimum K | **222.76792968750001** |
| Maximum K | **311.3579296875** |
| Mean K | **277.1364545276141** |
| Population standard deviation K, ddof=0 | **20.013496061472782** |

These are decoding summaries, **not area-weighted global climate statistics**. No
temperature was rejected by a plausibility threshold and no precision was rounded
away. No Celsius field was produced; an eventual conversion must explicitly subtract
273.15 from valid values while retaining masks and original Kelvin authority.

The [GDAL driver documentation](https://gdal.org/en/stable/drivers/raster/grib.html)
and [version 3.9.3 driver source](https://github.com/OSGeo/gdal/blob/v3.9.3/frmts/grib/gribdataset.cpp)
identify its independent degrib/g2clib path. This comparison does not consist of two
Python wrappers around ecCodes. For actual template 5.3,
[g2clib `comunpack.c`](https://github.com/OSGeo/gdal/blob/v3.9.3/frmts/grib/degrib/g2clib/comunpack.c)
and [type definition](https://github.com/OSGeo/gdal/blob/v3.9.3/frmts/grib/degrib/g2clib/grib2.h)
show binary32 coefficients/output, even though GDAL exposes a float64 band.

| Comparison | Observed result |
|---|---:|
| Identical grid/coordinate anchors and time/parameter/units | Pass |
| Full-field mask agreement | **1,038,240 / 1,038,240** |
| Bit-identical / non-identical numerical cells | **41,322 / 996,918** |
| Maximum absolute difference K | **0.00002197265627046363** |
| Mean absolute difference K | **0.000008251567011652562** |
| Cells within analytical per-cell rounding bound | **1,038,240 / 1,038,240** |
| Maximum such bound K | **0.00003198380645266968** |
| Cells exactly matching g2clib rounding diagnostic | **1,038,240 / 1,038,240** |
| Unexplained differences | **0** |

For this E=0/D=2 packing, the integer lattice's decoded quantum is **0.01 K**.
The diagnostic reconstructs integers `X=round(100×T−R)`; maximum lattice residual
**3.637978807091713×10⁻¹²**, consistent with binary64 arithmetic. It predicts
`float32(float32(X)+float32(R))×float32(0.01)` in binary32, then promotes the result
to double. **This is an explanatory arithmetic check, not a third GRIB decoder**:
GDAL and ecCodes independently unpacked the actual source first.

The allowed per-cell bound is derived from two rounded operations and the rounded
decimal coefficient: `0.5 ULP32(X+R)×|D32| + |X+R|×|D32−0.01| + 0.5 ULP32(output)`,
plus a small binary64 round-off bound. The tool additionally requires **exact** agreement
with the documented rounding profile. This does not introduce a tolerance merely to
hide discrepancies, modify inputs, or treat 0.01 K encoding as meteorological accuracy.
Different packing/scaling requires new evidence, not automatic reuse of this profile.

## 6. Receipts, environment and reproducibility

[Utility/instructions](../../../scripts/weather-research/wr007/README.md),
[input pins](../../../scripts/weather-research/wr007/input-pins.json),
[metadata/integrity receipt](../../../scripts/weather-research/wr007/integrity-receipt.json)
and [focused tests](../../../scripts/weather-research/wr007/test_gfs_field_pilot.py)
are isolated and removable. The utility checks the actual message's numeric keys
before values, validates all native coordinates, compares independently decoded
arrays/masks and refuses unexplained differences or overwrite. Unsupported profile,
malformed/concatenated/truncated framing and checksum mismatch fail explicitly.

Windows AMD64, Python **3.12.6**. Existing base environment: ecCodes Python/native
**2.48.0**, NumPy **2.5.2**, cffi **2.1.1**, findlibs **0.1.3**, attrs **26.1.0**.
Existing Earth Lab environment: rasterio **1.4.3**, GDAL **3.9.3**, NumPy **2.5.3**.
No package was installed. Initial lookup through the Earth Lab interpreter missed
base-environment ecCodes; its `pyvenv.cfg` resolved the actual installed base tool.
The PyPI metadata check is counted but resulted in **no wheel download**.

Native identities: `eccodes.dll`, **3,819,008 bytes**, SHA256
`d11f2a2e977eb1e89774475a40ece996fb37353fca9d08db518f88c732e87880`;
`gdal-0c91f8aa17bf5518bc6a69e15438cc5c.dll`, **19,130,368 bytes**, SHA256
`0ec06c1a0fb46eb0fdde9d18f2ba87cef8ebb6f40ab4beaa7a47e8812d28a58a`.
These two binaries are not the complete transitive footprint: ecCodes' existing
47,550,464-byte `eccodes_memfs.dll` and other dependencies/resources remain relevant.
No native footprint reduction or target-platform result is claimed.

The full external deterministic receipt is **8,018 bytes**, SHA256
`108a6d1e6930dc4e8d6df821732601cb733fff57ebeecc8b12913e0198d17e21`.
It retains indexed numerical samples; the small committed copy omits samples and
adds acquisition/native/resource metadata. Transient acquisition timestamps are
not included in deterministic replay output. Decoded little-endian float64 array
SHA256: `01dad7249c0f441c65a4677455ce1340797dab82d0045a1e6fba95620fdb91e3`.
Two repeated real-data receipts match byte-for-byte; input remains byte-identical.
Native version or serialisation changes require a recorded new receipt, not rewriting history.

## 7. Rights, requests and resource accounting

The exact [NOAA NODD notice](https://registry.opendata.aws/noaa-gfs-bdp-pds/) permits
use of disseminated NOAA data, requests attribution, prohibits implied affiliation/
endorsement and requires modifications not be represented as original NOAA data.
**NOAA/NCEP Global Forecast System was accessed on 10 October 2026 through NOAA NODD.**
Reported statistics/decoded receipts are Meridian-derived research outputs, not
unaltered NOAA publications. This supports the bounded anonymous research pathway;
it is not commercial/offline legal clearance, a guaranteed archive retention period,
or an unlimited delivery-service entitlement. GDEX CC BY terms were not silently
applied to this distinct channel. No fee/account/contract was incurred or accepted.

Installed ecCodes native notice is **Apache 2.0**; rasterio is **BSD 3-clause**.
GDAL/degrib/g2clib and bundled codecs/native dependencies have their own notices.
Research uses existing binaries without redistributing them; a future package
requires an exact binary/resource notice inventory and applicable licence review.
This pilot neither changes the repository's software licence nor clears dependencies
or meteorological products for public distribution.

| Attempt | Response / body bytes | Purpose |
|---|---|---|
| 1 | Index 200 / **41,250** | Exact historical message selection |
| 2 | NODD registry 200 / **15,298** | Bucket identity and source reuse notice |
| 3 | Parent HEAD 200 / **0** | Size, ETag and range metadata |
| 4 | Range 206 / **874,115** | Sole scientific payload |
| 5 | ecCodes PyPI metadata 200 / **24,093** | Availability assessment; no install |
| 6 | GDAL driver documentation 200 / **60,662** | Unit/longitude defaults and decoder lineage |
| 7 | GDAL 3.9.3 driver source 200 / **107,939** | Version-specific independent implementation |
| 8 | g2clib unpack source 200 / **15,509** | Packing-rounding explanation |
| 9 | g2clib type header 200 / **15,927** | Binary32 output type |
| 10 | NCEP temperature table 200 / **17,059** | Numeric parameter and K |
| 11 | NCEP surface table 200 / **39,204** | Height-above-ground code |
| 12 | NCEP packing template 200 / **7,545** | Representation template semantics |

**12 attempts, zero retries/redirect follow-ups, 1,218,601 received response-body bytes**,
including all software/documentation bodies. One initialisation, lead, variable and
GRIB payload. Body accounting excludes unmeasured TLS/header overhead; requested Git
fetch/push are repository-control traffic, not scientific retrievals. No new wheels,
bulk requests, scientific publication, cloud or operational service. The controlled research retrievals remain within the 50 MB/20 ceilings. Full parent
transfer was avoided. **Accounting limitation:** the npm lint invocation emitted an
automatic npm-version update notice. Installed npm's notifier code establishes a
manifest lookup; its response-body bytes/retry count were not captured and its
ephemeral tool cache was unavailable after completion. There are **13 known research/
tooling request attempts (12 measured + that update lookup)**, but a fully measured
total task-network budget cannot be certified. Do not represent 1,218,601 as including
this incidental transfer or infer a ceiling breach without evidence. Further update
checks are disabled; no package installation followed. Git control/TLS overhead also
remains outside the response-body ledger.

Raw field **874,115 bytes**; one float64 field **8,305,920 bytes**; a separate byte
mask **1,038,240 bytes** plus metadata/headers. A GDAL intermediate is approximately
9.35 MB. Owned scratch also includes repeated comparison outputs, validation receipts,
source documentation and the application-only bundle. Final review measured
**30,627,082 bytes** of owned scratch including the reviewed diff. Adding both
real-test temporary intermediates gives a conservative **49,316,414-byte** bound;
the [validation log](../../development-log.md) records the snapshot context.
Real-test temporary intermediates are removed by their owned
temporary-directory lifecycle; source input is never removed. Peak tested scratch
stays below **150 MB**. Array lengths and scratch are not a runtime working-set
measurement; CPU/RAM/GPU, mobile suitability and production acquisition economics
were **not benchmarked**. Existing native libraries are not copied into owned scratch.

## 8. Validation, limitations and architectural implications

**29 synthetic guards + 1 opt-in real test pass, zero skips.** Real test runs the
complete independent comparison twice, checks deterministic receipts, refusal to
overwrite and unchanged input. Synthetic tests cover incorrect quantity/level/time,
units/orientation/grid/packing, unknown missingness, missing keys, checksum/framing,
wrap, masks and decoder disagreement; they are not evidence of real bitmap handling.
The rasterio/NumPy 2.5 shape deprecation warning is retained, not suppressed.

Seven existing publication-boundary tests pass. Lint, TypeScript and application-only
Vite build pass; the isolated build has no Weather materialisation plugin and no public
data copying. Existing optional-esbuild and large-bundle warnings remain. Full Weather
build, expensive scientific replays and forecast verification were not run: accepted
runtime, contracts, scientific inputs and publications did not change. No unrun suite
is claimed to pass. Complete diff/link/source/preservation checks precede commitment;
their exact receipts are recorded in the development log.

**INFERRED architecture constraints:** preserve original raw-message identity and
inventory/range provenance separately from decoded values; retain numeric parameter,
vertical diagnostic, reference/step/valid-time support, grid registration/scan/Earth
definition, masks, packing and decoder/resource versions. Friendly names, Float64
output declarations and filenames alone hide important semantics. Verification
receipts should precede resampling/quantisation/render products, whose error budgets
need separate tests. Range extraction is practically useful **for this exact object**,
not proof of lasting archive availability or a production access service.

Scientific source → decoded numerical field → derived products → publication →
presentation remain distinct responsibilities. No new tiles, schema/framework,
database, production adapter or native scientific core is selected. No conclusion
generalises to precipitation intervals, wind vectors, pressure, clouds, ensembles,
other models or geographic predictive skill. Global/regional/nowcast/ML/mountain,
uncertainty, reference verification, rights/costs and offline tracks remain intact.

## 9. Exactly one next bounded task — NOT BEGUN

**WEATHER — GFS NATIVE-GRID POINT-SAMPLING AND QUERY-SEMANTICS PILOT — NOT BEGUN.**

**Objective:** use this already pinned, independently decoded field to establish a
small error-explicit point-query behaviour with original grid/time/height/unit
qualification. This tests a real downstream numerical responsibility without
pretending that MIDAS verification or a production reader is now available.

**Required evidence/dependencies:** WR007 message/receipt, same immutable local input,
checked decoders and grid-coordinate authority. No new forecast/observation data or
device/toolchain/provider decision. A missing pin stops execution; do not reacquire
or change source implicitly.

**Scope:** error-blind deterministic coordinate-to-native-point indexing; longitude
wrap, poles, nearest-point ties, out-of-domain/non-finite requests and explicit time/
quantity rejection; return source-point coordinates and qualified Kelvin values.
Compare selected indices/values independently against both checked decoded arrays.
State nearest-point sampling's spatial support; no interpolation, altitude correction,
derived risk, forecast errors, provider selection, UI or universal Weather schema.

**Acceptance:** a finite documented query profile, reproducible real-point/index receipts
and rejection/boundary tests preserving raw/decoded identities; honest limitations and
any counterexample. Numerical query correctness is not predictive skill.

**Resource boundary:** reuse the one field; **zero new network requests/scientific
transfer, at most 25 MB additional owned scratch**, no paid dependency, production
publication or infrastructure. Preserve all accepted data and historical findings.

**Stop conditions:** conclude on finite sampling conformance or a precise numerical/
semantic blocker. Unsupported interpolation/other fields remain deferred; no expansion
to multiple dates, providers or application integration. Priorities may change with
evidence. **This subsequent task has not begun.**
