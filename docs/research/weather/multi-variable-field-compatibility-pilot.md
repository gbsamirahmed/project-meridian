# WR010: multi-variable field compatibility and candidate scientific contract

**10 October 2026.** Starting public main **`8bb52c70325f966097c8487a8a698dd7f45db070`**,
clean and aligned with fetched origin/main, zero divergence. Actual
[WR007](historical-gfs-temperature-field-pilot.md), [WR008](gfs-native-grid-point-sampling.md),
[WR009](historical-gfs-precipitation-interval-pilot.md), their utilities/pins/receipts,
[programme](research-programme.md), [register](research-register.md),
[source notes](sources.md), [compatibility](forecast-reference-compatibility.md) and
Foundations [roadmap](../../foundations/roadmap.md), engineering/economics/decisions
were reviewed before edits. Accepted historical evidence remains unchanged.

## 1. Decision and boundaries

**OUTCOME A — VERIFIED REPRESENTATIVE MULTI-VARIABLE COMPATIBILITY**, limited to
five genuine messages from one delivered historical GFS grid/run/end-time and
the checked Windows decoder profile. Existing instantaneous temperature and
six-hour APCP accumulation are reused. New earth-relative 10 m U/V wind and
instantaneous atmospheric-column cloud percentage are independently decoded.
Their common encoded grid, provenance and integrity responsibilities coexist
with distinct physical units, vertical support, temporal support and vector basis.

This supports a **candidate research contract**, not a production API or universal
Weather framework. Fractions are represented by one continuous percentage field;
categories, pressure/model levels, ensemble members, actual bitmap cases, other
grids/providers and interval means remain unvalidated. This is not complete
weather coverage, provider interchangeability or meteorological skill. [WR006
strict and revised MIDAS Decision C](midas-historical-measurement-support.md#6-formal-decision-and-possible-protocol-change)
stays BLOCKED; no observations, forecast errors or application work occurred.

Grades: **OBSERVED** actual input/metadata/values; **VALIDATED** finite independent
checks and deterministic replay; **RETAINED VALIDATED** earlier accepted experiment;
**INFERRED** engineering consequence; **PROPOSED** candidate/next experiment;
**UNRESOLVED** missing evidence. Synthetic tests establish rejection invariants,
not scientific compatibility of unacquired products.

## 2. Discovery, predeclaration and source access

Recursive filename/extension/context discovery in the authorised external data
root found **zero additional raw GRIB candidates**. No huge unrelated data,
legacy publication or private repository was inspected as a substitute. The exact
WR007 and WR009 inputs were borrowed in place; no copies or reorganisation.

WR009's proposed maximum **three new messages** is retained, within the current
20 requests/50 MB response bodies/150 MB scratch ceilings. No extra scalar was
acquired simply to fill a table. On **2026-10-10T17:37:15.113837Z**, before numerical
values/acquisition, froze the unique UGRD/VGRD 10 m instantaneous f024 entries
and **instantaneous** TCDC atmospheric-column entry. The separate 18–24 h mean
TCDC is listed but not acquired. Fixed numeric parameters, units, vertical intent,
run/validity/PDT, grid/ensemble/missingness rejection criteria, query coordinates
and comparison arithmetic are retained in the [pins](../../../scripts/weather-research/wr010/input-pins.json).

**Explicit correction before values:** the preliminary expected cloud surface code
200 was wrong. Actual encoded code **10**, supported by retained NCEP Table 4.5,
means entire atmosphere. The original freeze and dated correction both remain
in the pins. Intended product/column/level did not change; no silent source substitution.

| Message / frozen inventory | Inclusive byte range | Acquired bytes / raw SHA256 |
|---|---|---|
| 588 UGRD, 10 m, `24 hour fcst` | 421036204–421999709 | 963,506 / `6ed439d0b10e5cdeb2ab81b452f2f27f4afc93e4f06a0988b38122e56ada2fcf` |
| 589 VGRD, 10 m, `24 hour fcst` | 421999710–422944345 | 944,636 / `d0113e2831a29ec6095a3eb139bb7d9d57947b4f36da3b46a3b5f70425e05e58` |
| 636 TCDC, entire atmosphere, `24 hour fcst` | 444289883–445124587 | 834,705 / `752e73b0170ecbf7689ad0970219a138286249b2bacc0d2b753952a10e3b1b5c` |

[NOAA exact parent](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024)
HEAD: **537,858,357 bytes**, ETag `e9f55c2f3f45d6cdb3aac9e4b7a36aba`, matching
the [retained index](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024.idx)
SHA256 `fa11be72ab29ea43520dc6a6fc8de81bd8e0e024c96da94ed05495bc43b39dcb`.
Index reused locally, zero new index transfer. All three ranges return **206**,
exact Content-Range/Content-Length/body size, conditional If-Match; no full parent
download, redirect, retry or concatenation. Actual GRIB framing and metadata,
rather than inventory names, establish identities. ETag is not a cryptographic
scientific integrity proof. Exact historical executable/suite revision remains unknown.

Retained [NOAA NODD notice](https://registry.opendata.aws/noaa-gfs-bdp-pds/) inspected
locally on 10 October, with WR009's same-day retrieval identity: NOAA data reuse,
attribution, no endorsement and modified-material qualification. **Credit NOAA/NCEP
GFS through NOAA NODD**; receipts are Meridian-derived research. No new notice
request, account, credentials, agreements, paid service or provider contact.
Research access does not establish unlimited service use, future archive continuity,
complete commercial/offline distribution or decoder-binary redistribution clearance.

## 3. Exact field evidence and support matrix

All five: NOAA/NCEP GFS, centre **7**, master/local tables **2/1**, generating
process **96**, operational deterministic forecast codes; reference
**2025-01-15 00 UTC**, valid/end **2025-01-16 00 UTC**. The delivered grid is
not the underlying FV3 computational mesh. Friendly decoder aliases are secondary
to numeric parameter/surface/template codes.

| Field / evidence | Parameter | Native units / vertical support | Temporal support |
|---|---|---|---|
| Temperature / RETAINED VALIDATED WR007–008 | 0/0/0 | K; code 103, 2 m above model ground | PDT 4.0 instant, +24 h |
| Total precipitation / RETAINED VALIDATED WR009 | 0/1/8 | kg/m²; code 1, ground/water surface | PDT 4.8 accumulation: Jan 15 18 UTC–Jan 16 00 UTC, 21,600 s; stat 1, lead to start 18 h/end 24 h |
| U wind / VALIDATED WR010 | 0/2/2 | m/s; code 103, 10 m above model ground | PDT 4.0 instant, +24 h |
| V wind / VALIDATED WR010 | 0/2/3 | m/s; same 10 m support | PDT 4.0 instant, +24 h |
| Total cloud cover / VALIDATED WR010 | 0/6/1 | **%**, code **10**, entire atmospheric column; no physical height inferred from level alias 0 | PDT 4.0 instant, +24 h; not the adjacent interval mean |

New parameter authority retrieved **10 October 2026**: NCEP
[momentum 4.2-0-2](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-2-0-2.shtml)
(page revision 9 June 2026), [cloud 4.2-0-6](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-2-0-6.shtml)
(16 September 2025), [component flags 3.3](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table3-3.shtml)
(created 11 May 2005). Retained [surface table 4.5](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-5.shtml)
and WR009's time/statistical definitions were read locally. Living definitions
do not pin the historical model binary or establish skill.

**Wind pairing VALIDATED:** parameter identities, native units, model/product/table
identity, reference/validity/instant support, 10 m level, grid and masks match.
Actual Section 3 octet 55 flags **48**, bit 5 zero, `uvRelativeToGrid=0`: U eastward,
V northward, rather than directions tied to decreasing array-row latitude. Pairing
does not establish speed/direction conventions, gusts, physical wind accuracy,
terrain exposure or a vector basis at the poles. No derived wind product was computed.

**Cloud:** continuous encoded percentage, not a categorical codebook, fraction
0–1, observed cloud, optical depth, cloud base or altitude. No conversion applied.
Cloud overlap/model diagnostic methodology and local interpretation remain
unresolved; numeric parameter/percentage/column support is established.

## 4. Grid, encoding and independent numerical checks

**VALIDATED:** all five raw Section 3 blocks share SHA256
`2f05f13897b18b42bb2790905e2476fce9a2e07b89f63499a12da9e202f3367f`.
Same **encoded grid**, stronger than nominal resolution or compatible coordinates:
template 3.0 regular_ll, 1440 × 721 = **1,038,240 nodes**, scan 0; latitude 90→−90
descending .25°, longitude 0→359.75 ascending .25°, periodic longitude, no duplicate
360 endpoint, non-periodic latitude. Sphere shape 6/radius **6,371,229 m**, not an
asserted WGS84 datum. GDAL affine centres/CRS and every primary coordinate checked;
no transpose, resampling or grid coercion. New packing template 5.3, second-order
spatial differencing; E=0, D=2 for wind, D=1 for cloud. R values/packing details
remain in the receipt; quantisation is not meteorological uncertainty.

Existing ecCodes Python/native **2.48.0**, Python 3.12.6/NumPy 2.5.2 versus genuinely
independent GDAL **3.9.3**/degrib/g2clib, rasterio 1.4.3/NumPy 2.5.3. Native units
and original longitude layout explicitly selected. No installation. Raw Section 4
template octets, parameter/level/time/unit aliases independently agree.

Before values, froze integer-lattice/exact binary32-domain proof and the inspected
GDAL g2clib multiply/add/decimal-coefficient arithmetic. Every new decoded cell
must equal its predicted independent binary32 result **exactly**, and its residual
must also satisfy the analytical per-cell rounding bound. No tolerance was fitted
to results. This arithmetic explanation is not a third GRIB decoder.

| New field | Native min / max | Unweighted node mean | Maximum ecCodes–GDAL difference / maximum derived bound |
|---|---|---:|---|
| U, m/s | −25.91633544921875 / 24.97366455078125 | −0.14961697372175511 | 0.0000014495849605111744 / 0.000002753652698821516 |
| V, m/s | −31.36997314453125 / 22.31002685546875 | −0.24399057787999404 | 0.0000014495849605111744 / 0.0000028755510102086924 |
| Cloud, % | 0 / 100 | 63.38923428109108 | 0.000004577636715907829 / 0.00000835657141506907 |

**1,038,240 finite cells per field; zero missing, matching masks, all predicted
binary32 cells exact, zero unexplained disagreements.** Cloud has 77,381 zero
cells and no negative values. U/V negative values are legitimate signed components,
not negative precipitation or missing sentinels. No plausibility filtering or clamp.
All actual fields have no bitmap/internal missingness; synthetic rejection does
not validate genuine missing encodings. Means are not area-weighted climatology
or accuracy measures. Earlier temperature/APCP results are retained, not reclassified.

## 5. Small spatial reuse experiment

Seven coordinates/methods frozen before values for **each new field**; 21 receipts,
15 successful numerical comparisons (**six nearest, nine bilinear**) and six
explicit rejection receipts. WR008 mathematics reused unchanged; its temperature-
labelled keys are explicitly adapted to `native_value` plus this field's own unit.
No production shared sampler introduced.

| Query latitude, longitude ° / method | U m/s | V m/s | Cloud % |
|---|---:|---:|---:|
| 50,0 nearest (exact node) | −3.23633544921875 | −0.01997314453125 | 100 |
| 49.9,0.1 bilinear | −3.233935449218748 | −0.18077314453125184 | 89.35199999999985 |
| −40.1,359.9 bilinear | 4.700864550781217 | −4.028373144531283 | 61.05599999999423 |
| −40.1,−0.1 bilinear | Identical to preceding | Identical | Identical |
| 90,40 nearest | −2.96633544921875 | −5.78997314453125 | 100 |
| 89.875,0 bilinear | UNSUPPORTED_POLAR_CAP_BILINEAR | Same | Same |
| 91,0 nearest | LATITUDE_OUT_OF_RANGE | Same | Same |

Independent GDAL-decoded nodes/affine geometry plus separately implemented NumPy
weights/dot arithmetic agree. Maximum successful query differences: U
**0.00000017166137711299712 m/s**, V **0.0000003623962401277936 m/s**, cloud
**0.000001342773444434897 percentage points**. Predeclared bound is weighted actual
node decoding residual plus `128 × eps64 × magnitude × (1 + 360/dx + 180/dy)`;
weights have their own arithmetic guard. This checks new numerical/node reuse;
it **does not claim a new independent GDAL-warp kernel validation**, already
established for the WR008 finite temperature profile.

Axis-nearest is angular-coordinate nearest, not globally geodesic nearest.
South/east tie rules, cyclic longitude and canonical pole column retained. Bilinear
uses four finite native nodes, interior latitude domain [−89.75,89.75], no polar
extrapolation, missing-node renormalisation or nearest fallback. The pole row is a
numerical fixture; wind's geographic component basis there is degenerate. These
operations add no atmospheric resolution, terrain accuracy, conservative-area
remapping or route-query performance evidence. APCP geometry is compatible, but
no new APCP point-query experiment was performed.

## 6. Cross-field compatibility judgement

The [machine matrix](../../../scripts/weather-research/wr010/integrity-receipt.json)
keeps equality axes separate; no friendly-name join implies interchangeability.

| Axis | Evidence-backed judgement |
|---|---|
| Source/reference/end-valid | All same parent/model/run and endpoint; separate raw message/decoded hashes and parameter identities |
| Grid | All byte-identical, independently checked; provider/grid-generic compatibility untested |
| Temporal | T/U/V/cloud same instant; APCP same endpoint but different six-hour support: **not interchangeable** |
| Vertical | U/V same 10 m; temperature 2 m, precipitation surface and cloud entire column differ; no vertical transformation |
| Units | U/V same m/s; K, kg/m², % incompatible quantities. Possible K↔°C or %↔proportion are named conversions, not native equality; none applied |
| Missingness | Same actual no-missing profile, different field identities; no general sentinel rule or proof for real bitmap cases |
| Components | U/V form a numerically aligned earth-relative pair; independent scalars cannot become a vector merely by shared grid/time |
| Fraction/category | One continuous percent diagnostic qualified for angular arithmetic; categorical interpolation remains unsupported |
| Ensemble | Actual PDT0/8 deterministic codes, ensemble keys absent; **not member zero** of an ensemble; member/products/probabilities unresolved |
| Vertical families | Three actual height/surface/column meanings distinguished; pressure/hybrid/model levels untested |
| Scientific quality | Decoding/query integrity proven locally; model accuracy, observation equivalence, mountain suitability and operational continuity untested |

## 7. Minimal candidate scientific contract — PROPOSED

Implementation-neutral concepts, not a storage schema, programming-language model
or accepted API:

| Common intrinsic element | Required qualification / extension seam |
|---|---|
| Dataset/product/source identity | Producer/model/product/edition where known; table/process identifiers; unknown suite version explicit |
| Provenance | Original object/range/acquisition conditions, raw size/hash, decoder/version/verification, decoded seal; hashes do not prove authenticity or physical accuracy |
| Forecast reference and temporal support | Discriminate **instant(time)**, **interval statistic(start,end,duration,statistic,range qualifiers)**, **unknown/unsupported(reason)**; valid endpoint and lead-to-start/end are separate |
| Parameter and units | Numeric identity plus physical interpretation/native unit; labelled conversion/derived-product identity separate |
| Vertical support | Surface, fixed model-relative height, whole column; future pressure/model/hybrid coordinates require their own reference/metadata, not a universal level number |
| Horizontal geometry | Encoded grid identity, native logical/storage ordering, coordinate system/Earth shape/registration, domain/periodicity; geographic query labels do not alter grid |
| Encoding/values/missingness | Native precision/packing/mask rules, valid/finite/missing states, quantity-specific constraints; do not treat NaN, zero or 9999 as universal missing |
| Optional vector relationship | Component identities, common supports/units, coordinate basis, rotation requirement and pair/mask policy; no implicit speed/direction |
| Optional ensemble identity | Deterministic distinguished from member/control/perturbation, product/member dimension and probabilities; unsupported structure fails rather than member zero |
| Evidence/quality | Metadata-only, single/independent numerical decoding, query verification and empirical skill are separate claims |
| Query qualification | Method, input/normalised coordinate, nodes/weights, support/status/time/unit/source, missing/error policy and terrain representativeness limits |

Invariants: positive accumulation duration and consistent UTC bounds; matching vector
supports before pairing; no temporal or vertical interpolation by array convenience;
no category bilinear; finite weights/native values; invalid/unknown query support
explicit. Unknown facts can be retained as metadata, but cannot silently qualify a
scientific numerical operation. Tested adapter rejects unsupported statistics and
ensemble structures instead of implementing them speculatively.

Distinct layers: **raw scientific source → decoded numerical field → derived
product → immutable publication → query/presentation**. Display units/styles,
map modes, activity/route context, caches, Workspace, saved collections and sharing
are not intrinsic field identity. Atlas terrain elevation is contextual evidence,
not model orography; Guide context cannot make a forecast safety-qualified.

Extension seams: add a documented source adapter, temporal/vertical/basis interpreter
and narrow conformance cases while preserving old identities. New grid families
need geometry/method evidence; member dimensions need member semantics; new packing
needs decoder/missingness proof. This supports replaceable implementations without
choosing database, file format, library, renderer, frontend, mobile or cloud architecture.

## 8. Reproducibility, validation and resources

[Isolated instructions](../../../scripts/weather-research/wr010/README.md),
[utility](../../../scripts/weather-research/wr010/field_compatibility.py),
[tests](../../../scripts/weather-research/wr010/test_field_compatibility.py),
[pins](../../../scripts/weather-research/wr010/input-pins.json) and
[receipt](../../../scripts/weather-research/wr010/integrity-receipt.json).
Deterministic scientific JSON: **58,383 bytes**, SHA256
**`112c4ffa01e1eae0a850cc2c4d0b3bebba9de8cae34cebbba9e3d8f82bbb7216`**.
Acquisition/resource observations separated from deterministic science. Two real
test replays match byte-for-byte and the committed scientific content. Raw/decoded
arrays stay immutable. Preserved local replay differs from guaranteed future archive
retrievability. Inputs and generated arrays stay outside Git.

**24 synthetic tests + one real three-field double replay**, zero skips, passed.
Wrong unit/level/time/grid/frame, component mismatch, accumulation inconsistency,
unsupported packing/member/statistic, missing/non-finite data, evidence/provenance,
polar/invalid queries and deterministic serialisation fail explicitly. Prior
WR007/008/009 real regressions and publication/documentation/preservation checks
are recorded with exact results in the development log. No unsupported family
became validated by synthetic tests or table inclusion.

Controlled requests: **seven**, no retry/redirect: HEAD 0 bytes, ranges
963,506 + 944,636 + 834,705, technical tables 39,554 + 20,373 + 3,255;
**2,806,029 response-body bytes**, including documentation. Three new payloads,
**2,742,847 raw bytes**, one cycle/lead. No retrieval during numerical runs/tests;
no package updates/installs/accounts/paid/cloud/data-materialising builds. Git
control, HTTP/TLS overhead and unrelated OS traffic are unmetered; **no certified
zero-total-network or full-network budget claim**.

Sequential temporary reference outputs at most **9,346,173 bytes** per field,
removed. Actual final scratch/conservative concurrent bound in the development
log, below 150 MB. One standalone full run: primary Windows PSAPI peak working set
**193,986,560 bytes**; maximum separate reference peak **91,373,568 bytes**. Their
sum **285,360,128** is a conservative bound from separate lifetime peaks, not a
measured simultaneous total. Process commit/PagefileUsage is not resident RAM or
disk writes. These are Windows research measurements, not mobile/performance budgets.

No production/shared contracts, frontend, Atlas, legacy Weather, raw inputs or
earlier pins/receipts changed. Preservation baseline checked before edits; final
gate checks all 42 statuses, 113 hashes and 40,842 Weather files again. No expensive
unrelated scientific replay, full Weather build or observational verification.
Existing NumPy/rasterio deprecation and application-build warnings are retained;
no dependency changes were made to suppress them.

## 9. Programme implications and exactly one next task — NOT BEGUN

Distinct representative families now have bounded real evidence, making another
single-variable GFS pilot less informative. Highest portability uncertainty is
whether these semantic responsibilities survive another producer/product lineage;
same-parent byte identity cannot establish that. Global/regional, ensembles,
mountain weather, observations/nowcasting, ML, uncertainty and offline delivery
remain first-class; WR006 is not reopened and no provider is selected.

**CROSS-PROVIDER FIELD-CONTRACT CONFORMANCE PILOT — NOT BEGUN.**

**Objective:** test the WR010 candidate concepts against one independently produced
global forecast product, preferably a lawful ECMWF IFS Open Data candidate, with
one instantaneous near-surface scalar and a matched wind pair where documentation
and access permit. This is semantic/numerical portability, not model comparison skill.

**Evidence/dependencies:** exact current product/parameter/level/reference/validity,
native grid, component frame and source-specific research-use terms; existing
decoder support and preserved WR010 cases. Source choice is a research candidate,
not production selection. No claim of available historical January 2025 overlap;
one error-blind current/historical cycle may be fixed after public access checks.

**Scope/resources:** at most three new messages, one run/end-time, ≤20 requests,
≤50 MB bodies and ≤150 MB scratch, no paid/accounts/dependencies/production changes.
Metadata/rights predeclaration precedes values. Use existing decoders; stop on
unsupported grid/packing or blocked access rather than silently translate meaning.

**Acceptance:** reproducible numerical/provenance receipts and compatibility/
rejection evidence showing what carries over and which source-specific adapters
are needed; an honest negative or partial result is acceptable. No forecast errors,
provider superiority, final schema or forced regridding. A different temporal,
vertical or coordinate interpretation should revise the candidate contract explicitly.

**Stop:** conclude after that finite cross-provider conformance gate; no further
acquisition, ensemble programme, MIDAS research, application or production architecture.
This is the sole proposed subsequent task and has not begun.
