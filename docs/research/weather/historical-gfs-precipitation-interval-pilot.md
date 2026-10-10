# WR009: historical GFS precipitation-interval semantics and decoding

**10 October 2026.** Clean public main at required checkpoint
**`71e73ecad4e1e086f83097c1dcf1e62cff9592c5`**; fetched origin/main, exact alignment,
zero divergence before changes. [WR007](historical-gfs-temperature-field-pilot.md),
[WR008](gfs-native-grid-point-sampling.md), [WR006](midas-historical-measurement-support.md),
[compatibility](forecast-reference-compatibility.md), [programme](research-programme.md),
[register](research-register.md), [sources](sources.md), Foundations
[engineering](../../foundations/engineering.md)/[economics](../../foundations/economics.md)
and external-data preservation were reviewed. Existing WR007–008 utilities/pins/
receipts remain unchanged. No private access, production change or later task.

## 1. Decision and finite scope

**OUTCOME A — VERIFIED PRECIPITATION FIELD AND INTERVAL SEMANTICS**, for this one
actual message, packing/grid/time profile and checked Windows environment.
NOAA/NCEP GFS **2025-01-15 00 UTC**, ending at **+24 hours / 2025-01-16 00 UTC**,
contains a **six-hour total precipitation accumulation, 18–24 h**, not an assumed
24-hour total. Actual PDT 4.8 octets and two decoder metadata paths support this
interpretation. ecCodes/GDAL independently decode **1,038,240 cells**, all
bit-identical, zero missing/negative values, with **zero numerical tolerance**.
Repeat scientific receipts and the raw input checksum match.

The exact encoded native grid matches WR007. This supports shared finite field
identity/provenance/grid/integrity responsibilities alongside **distinct temporal
and quantity semantics**. It does not establish precipitation skill, phase, local
intensity, mountain performance, general archive continuity or a production core.
[WR006 reference Decision C](midas-historical-measurement-support.md#6-formal-decision-and-possible-protocol-change)
remains BLOCKED; no forecast errors or observation comparisons were calculated.

Labels: **OBSERVED** actual response/message/decoded value; **VALIDATED** finite
guard/replay/independent comparison; **DOCUMENTED** primary definition;
**INFERRED** architectural implication; **PROPOSED** next evidence;
**UNRESOLVED/BLOCKED** unsupported property. Synthetic and real results are separate.

WR008 proposed one accumulated message, 50 MB/20 requests/150 MB scratch and
explicit interval identification. WR009 authorises that acquisition and adds
multi-variable contract assessment; limits/safeguards are retained. No discrepancy
requires weakening a rule. Its preference for the same cycle/f024 family is met;
no date, model, grid or lead substitution. WR010 has not begun.

## 2. Local discovery, source and acquisition

Recursive filename/extension/context discovery throughout the authorised external
data root found **zero candidate raw GRIB/APCP/Jan-15 inputs**. No large unrelated
scientific file was read and no legacy September publication substituted.
WR007's raw temperature input stayed in place for Section 3/hash comparison
and unchanged regression tests. No source move/copy, data-directory reorganisation or deletion.

[Exact NOAA NODD inventory](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024.idx),
SHA256 `fa11be72ab29ea43520dc6a6fc8de81bd8e0e024c96da94ed05495bc43b39dcb`,
lists **two** APCP surface messages ending at f024. Before numerical values,
freeze the unique **message 596**, `18-24 hour acc fcst`, to investigate the
lead/duration distinction; message 597, `0-1 day acc fcst`, is listed but **not
acquired or decoded**. No selection depended on precipitation magnitudes.
Selection timestamp **2026-10-10T16:59:38.373968+00:00** is retained in the pins.

| Acquisition identity | Inspected evidence |
|---|---|
| [Authoritative parent](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024) | `gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024`, HEAD 200, **537,858,357 bytes**; not downloaded |
| Frozen index line | `596:426116442:d=2025011500:APCP:surface:18-24 hour acc fcst:` |
| Next offset | **426459670**, start of message 597, used only to bound message 596 |
| Inclusive range | **426116442–426459669**, length **343,228 bytes** |
| HTTP proof | 206, `Content-Range: bytes 426116442-426459669/537858357`, matching Content-Length/body size and parent ETag; If-Match used |
| ETag / parent modified | `e9f55c2f3f45d6cdb3aac9e4b7a36aba` / `2025-01-15 03:44:04 GMT`; object metadata, not cryptographic integrity or forecast issue time |
| Raw original | `gfs-2025011500-f024-apcp-18-24h.grib2`, SHA256 **`e2a311fa2089ab1982d9b09e7ec82f483e07ef06f38457d9e379fe9cef970848`** |
| Framing | One complete GRIB edition 2 message, exact total length/end marker; sections 1/3/4/5/6/7; no concatenated field |

Anonymous requests used no credentials, cookie/session store, account, agreement,
paid service or automatic redirect/retry. Advertised sizes and range headers were
checked before streaming bodies; a 200 full-object response would be refused.
No archive mirroring or second scientific payload occurred.

The [NODD notice](https://registry.opendata.aws/noaa-gfs-bdp-pds/) was freshly read
on 10 October 2026. It permits disseminated NOAA data use, requests attribution,
prohibits implied affiliation/endorsement and requires modified material not be
presented as unaltered NOAA data. **Credit NOAA/NCEP GFS through NOAA NODD**;
these numerical receipts/statistics are Meridian-derived research outputs.
This supports bounded anonymous research, not guaranteed retention, unlimited
service access or complete commercial/offline distribution clearance. GDEX terms
were not transferred to this channel. Exact historical executable/suite revision
remains UNRESOLVED (encoded generating-process identifier 96 is not a binary pin).

## 3. Actual parameter, template and time semantics

Authoritative pages retrieved **10 October 2026**: NCEP
[moisture table 4.2, discipline 0/category 1](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-2-0-1.shtml),
[PDT 4.8](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp4-8.shtml)
(created 21 September 2007),
[statistical table 4.10](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-10.shtml),
[time units 4.4](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-4.shtml)
(created 12 May 2005), and
[increment table 4.11](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-11.shtml)
(revised 21 December 2011). Living tables define encoded codes, not this
historical executable's revision. Full response identities are in the receipt.

| Property | Actual value / interpretation |
|---|---|
| Producer | Edition 2, centre **7**, subcentre 0, master table 2/local table 1; operational forecast codes; process type 2/identifier 96 |
| Numeric parameter | **0/1/8**, total precipitation; NOAA inventory **APCP**, ecCodes short name **tp**; aliases alone insufficient |
| Vertical/surface | Fixed surface **1** (ground/water surface), ecCodes `surface`, level 0; no 2 m diagnostic |
| Product/statistic | **PDT 8**, Section 4 length **58**, one range; `typeOfStatisticalProcessing=1` accumulation; `stepType=accum` |
| Reference | Section 1 **2025-01-15 00:00:00 UTC** |
| Start offset | Encoded `forecastTime=18`, `indicatorOfUnitOfTimeRange=1` hours; PDT 4.8 note 2 defines beginning of overall interval |
| Explicit end | Year/month/day/hour/minute/second **2025/1/16/0/0/0** encoded in Section 4 octets 35–41 |
| Range | `numberOfTimeRange=1`, `lengthOfTimeRange=6`, unit **1** hours; duration **21,600 s** |
| Successive-time type | **2**: same forecast start/reference, forecast time incremented |
| Increment | `timeIncrement=0`; PDT note 3 denotes continuous/near-continuous statistical processing. Increment unit **255** missing; no discrete internal cadence inferred |
| Missing statistical inputs | Encoded **0**; distinct from cell bitmap/missingness, not proof of source forecast accuracy |
| ecCodes aliases | `startStep=18`, `endStep=24`, `stepUnits=1`, `stepRange=18-24`; validity Jan 16 00 UTC |
| Independent GDAL | `APCP06`, native `[kg/(m^2)]`, reference epoch **1736899200**, valid **1736985600**, `GRIB_FORECAST_SECONDS=64800`, PDT 8 raw byte list matches Section 4 |

**Derived and cross-checked:** reference + 18 h = **15 Jan 18 UTC**;
start + 6 h = explicit end = valid time **16 Jan 00 UTC**; lead-to-end = 24 h.
GDAL's forecast-seconds tag is **lead-to-start**, not a conflicting 18-hour
valid lead. Different short names and units spellings describe the same numeric
parameter/unit. The utility checks raw documented PDT octets against ecCodes
and GDAL's template octets, without implementing a numerical GRIB decoder.
The interval function is shared receipt arithmetic; it is not advertised as a
third independent temporal interpretation engine.

The missing increment-unit code does not block these outer bounds: start/end/
duration and type are explicit, zero increment is documented, and aliases agree.
Internal timestep/cadence, exact intra-interval rainfall timing and interval
endpoint sampling conventions are not inferred. Non-zero increments, nested
ranges, floating subintervals, calendar/local/missing duration units, missing
statistical values, unknown templates/types or inconsistent timestamps fail closed.
Such profiles require new evidence; they are not automatically scientifically invalid.

## 4. Physical unit and numerical evidence

Encoded native **kg m⁻²** is precipitation mass per horizontal area accumulated
over the interval. Table 4.10's general accumulation multiplies units by seconds
**unless otherwise specified**; APCP table 4.2 note 3 explicitly says its units
do not change. Do not append seconds to APCP, call it PRATE, snowfall depth,
convective-only precipitation or instantaneous rain intensity.

At the stipulated conventional water density **1000 kg/m³**, `depth_mm =
mass_kg_per_m2 / 1000 × 1000`, so numerical amounts correspond to mm of
**water-equivalent depth**. No such conversion is applied to the decoded field;
native values/units are retained. It does not establish snow depth, precipitation
phase or actual local liquid density. No rate conversion, clamping or downscaling.

Actual template **5.3**, complex packing/second-order spatial differencing,
R=**0**, E=**−4**, D=**0**, bits/group-reference=12, **24,575 groups**; bitmap 0,
internal missing management 0, all numerical values finite. The encoding quantum
is **0.0625 kg/m²**, not a measurement precision or meteorological uncertainty.
The decoder's conventional `missingValue=9999` was not treated as an observed
sentinel. Unsupported bitmap/internal-missing profiles are rejected before values.

Existing Windows Python 3.12.6/ecCodes Python/native **2.48.0**, NumPy **2.5.2**
versus separate Python/rasterio **1.4.3**, GDAL **3.9.3**/degrib/g2clib, NumPy
**2.5.3**. No installation. Retained [WR007 decoder source/notice evidence](sources.md#wr007-exact-field-and-independent-decoder-evidence)
was read locally, without a repeat transfer: its binary32 scaling operations
show why this power-of-two case should agree exactly.

Before array values, froze **zero tolerance**, conditional on every reconstructed
integer `X=16×value` being an exact integer in [0,2²⁴). For R=0/D=0/E=−4, both
integer conversion and scaling by 1/16 are exactly representable in binary32
throughout that domain. Every real cell satisfies it. This arithmetic diagnostic
is not a third decoder; the values first came from actual independent libraries.
No temperature decimal-scaling tolerance was reused or tuned after comparison.

| Real numerical result | Native kg/m² / count |
|---|---:|
| Valid / finite / missing | **1,038,240 / 1,038,240 / 0** |
| Minimum / maximum | **0 / 139.9375** |
| Mean / population standard deviation | **0.5714223108337186 / 2.0321239347103286** |
| Zero / negative cells | **525,253 / 0** |
| Compared / bit-identical | **1,038,240 / 1,038,240** |
| Masks / orientation / coordinates / native units | Agree |
| Maximum / mean absolute decoder difference | **0 / 0**, zero tolerance, no unexplained differences |

The global mean is an **unweighted native-node arithmetic mean**, not area-weighted
global precipitation, volume or verification. No unusual value was plausibility-
filtered. No negative occurred; a future negative requires encoding/quantity
investigation rather than a zero clamp. Mathematical mask cases are synthetic only.

Inherited deterministic WR007 node fixtures, fixed before precipitation values:

| Row, column | Latitude, native longitude ° | Accumulated kg/m² |
|---|---|---:|
| 160,0 | 50,0 | 0.125 |
| 520,0 | −40,0 | 0.0625 |
| 360,719 | 0,179.75 | 0.0625 |
| 360,720 | 0,180 | 0.0625 |
| 360,1439 | 0,359.75 | 0.4375 |
| 0,0 | 90,0 | 0.125 |
| 720,0 | −90,0 | 0 |
| 140,1428 | 55,357 | 0 |

## 5. Spatial compatibility and two field families

**VALIDATED:** raw Section 3 byte identity and every retained grid metadata field
match WR007. Both have **1440×721**, regular_ll template 3.0, scan mode 0, point nodes,
latitude 90→−90 descending by 0.25°, longitude 0→359.75 ascending by 0.25°, no duplicate 360°
endpoint, both poles present; sphere radius **6,371,229 m**, not an asserted WGS84
datum. ecCodes checks every native coordinate; GDAL's affine pixel centres and
the eight anchors independently identify equivalent cells. The delivered grid is
not the FV3 computational mesh. No array transpose, regrid or coercion.

WR008's axis-nearest, deterministic ties, cyclic longitude and qualified interior
bilinear geometry are compatible **in principle**, preserving its explicit
polar/missing rules. No precipitation sampling programme was run. A sampled value
would still be a model interval accumulation with method/node/weight provenance;
interpolation adds no resolution or local physical accuracy. It is not a temporal
interpolation rule, conservation guarantee or permission to sample categories/vectors.

| Contract | WR007 temperature | WR009 precipitation |
|---|---|---|
| Parameter / level | 0/0/0, 2 m above model ground | 0/1/8, surface accumulated total precipitation |
| Native units | K | kg/m²; water-equivalent amount, no rate |
| Reference / valid | Jan 15 00 / Jan 16 00 UTC | Same reference / end-valid UTC |
| Temporal support | Instantaneous PDT 4.0, forecastTime=24 | PDT 4.8 accumulation; forecastTime=18, duration 6 h, endStep=24 |
| Statistical processing | Not applicable | Type 1, one range/type 2 increment, zero increment |
| Grid | Verified regular delivered sphere grid | Byte-identical Section 3 and checked geometry |
| Missingness | No bitmap/internal missing; all valid | Same no-missing profile, independently verified |
| Packing | R=22276.79296875/E=0/D=2; quantum 0.01 K | R=0/E=−4/D=0; quantum 0.0625 kg/m² |
| Independent decoding | Explained binary32 decimal-scaling residuals | All values bit-identical under exact binary-scaling proof |
| Point-query evidence | Actual WR008 nearest/bilinear results | Geometry compatible; no new precipitation point replay |
| Provenance | Separate raw message 581/sha/decoded seal | Separate raw message 596/sha/decoded seal, interval retained |
| Interpretation limit | Model-relative 2 m, not real-terrain measurement | Accumulated model mass, not local rain intensity/phase/skill |

## 6. Smallest reusable scientific responsibilities

**INFERRED**, not a production schema: retain raw source/object/range/hash, model/
product/centre/table/process identity, decoder/resources, numeric parameter and
surface/level, native unit, missingness, packing/precision, immutable native grid,
reference time, **explicit temporal-support kind**, qualified valid time and
reproducible interpretation receipt. A decoded-array identity is separate from
source identity; derived products, publications and presentation remain separate.

An instantaneous support has a time; an accumulation has **start/end/duration,
statistic and range/increment qualifiers**. Forecast start offset and end lead
need separate names. Store unknown/unavailable semantics explicitly; a friendly
name, nominal f024 label or shared array shape cannot repair missing meaning.
No inheritance hierarchy, universal schema, database or shared production package.

| Future family | Reusable evidence / distinct gate |
|---|---|
| Instantaneous scalars | Temperature provides one actual scalar case; pressure/humidity need exact units, level and quantity evidence |
| Accumulations / interval fields | This single total-precipitation case establishes one-range accumulation; means/maxima/rates/nested intervals need separate templates and interpretation |
| Vectors | Common source/grid/time checks useful; paired components, earth/grid-relative basis, rotation, units and speed/direction derivation **untested** |
| Fractions / categories | Common identity applies; fraction ranges/units and codebooks/missingness differ. Bilinear categories invalid without a justified interpretation; neither family validated here |
| Vertical fields | Grid identity may match while pressure/hybrid/model-level coordinates, surface elevation and interpolation differ; untested |
| Ensembles | Member/product identities and distributions add dimensions; common grid/time does not establish uncertainty calibration; no members acquired |

The combined evidence is enough to **propose a bounded multi-variable compatibility
pilot**, not approve all families or select GFS permanently. Test representative
families together and expose unsupported combinations rather than another full
standalone programme for every parameter. Regional/rotated/curvilinear grids,
ensembles, mountain weather, observations/nowcasting and sustainable offline
delivery remain separate evidence questions. No other field was acquired for this assessment.

## 7. Reproducibility, tests and resource ledger

[Utility/instructions](../../../scripts/weather-research/wr009/README.md),
[pins](../../../scripts/weather-research/wr009/input-pins.json),
[integrity receipt](../../../scripts/weather-research/wr009/integrity-receipt.json),
[interval receipt](../../../scripts/weather-research/wr009/interval-interpretation-receipt.json)
and [tests](../../../scripts/weather-research/wr009/test_gfs_precipitation_pilot.py)
are isolated. Full scientific receipt **11,360 bytes**, SHA256
**`3fd4ca223e8377872c0c77fb99b758240c2a6cddfb55976e7b354a0b63405451`**;
decoded little-endian float64 SHA256
**`fe7903e822f06a612c6b28c84bd0ed58348393af547974f79dd404e4234856fd`**.
Repeated receipts are byte-identical; raw input and read-only arrays stay unchanged.
Transient resource/acquisition observations are outside the deterministic science
fingerprint. Local pinned replay is established; future independent archive
retrievability, exact historical executable build and worldwide operations are not.

**48 synthetic guards + one real two-decoder replay test**, zero skips, passed.
Synthetic time units/arithmetic, lead/duration, missing/conflicting metadata,
unsupported statistic/ranges/increments, invalid dates, native conversion,
grid/packing/lattice/masks/disagreement, framing, checksum, output/scratch refusal
and deterministic JSON are guard evidence. Only real replay establishes historical
decoding/interval behaviour. Existing WR007 **30**, WR008 **37** and publication
**seven** tests passed with zero skips. Documentation/preservation and lint/types/
application-only build results are recorded in the [development log](../../development-log.md).
Full Weather materialisation, expensive unrelated scientific replays and forecast
verification are omitted: no accepted runtime/contracts/data changed, and skill
verification is outside scope. No unrun suite is claimed. Existing NumPy/rasterio
shape deprecation and build warnings are retained, no package upgrade.

| Controlled attempt | Actual response-body bytes |
|---|---:|
| 1 exact f024 index | 41,250 |
| 2 NOAA NODD notice | 15,298 |
| 3 parent HEAD | 0 |
| 4 single checked range payload | 343,228 |
| 5 PDT 4.8 | 10,078 |
| 6 statistical 4.10 | 11,572 |
| 7 time 4.4 | 3,781 |
| 8 increment 4.11 | 3,611 |
| 9 moisture 0/1 parameter table | 74,665 |
| **Total: nine attempts, no retries/redirects** | **503,483** |

All scientific **and documentation** body bytes count; one acquired message/cycle/
lead/variable. No SDK/dependency installation, automatic package-update lookup,
forecast backfill, paid service or cloud. Git control and HTTP/TLS overhead are
unmetered; **zero total network activity or fully measured total network transfer
is not claimed**. No external retrieval during decoding/tests.

One standalone local run: primary/reference Windows PSAPI lifetime peak working
sets **176,742,400 / 89,546,752 bytes**; the sum **266,289,152** is a conservative
upper bound from separate peaks, **not a measured simultaneous total**. Baselines
**35,471,360 / 49,963,008 bytes** working set; after **125,931,520 / 71,913,472**.
Primary/reference peak PagefileUsage counters **801,738,752 / 706,351,104 bytes**
are process commit, not resident RAM or actual disk writes. Elapsed **1.315443600062281 s**
includes imports/decode/comparison, not a throughput/cold-start/mobile benchmark.
Temporary GDAL values/mask/metadata **9,347,284 bytes** removed after each run;
no permanent full-array copies. Final owned scratch and conservative concurrent
temporary bound are recorded with validation in the development log, below **150 MB**.
No footprint attribution or production/mobile budget follows.

## 8. Remaining limits and exactly one next task — NOT BEGUN

No physical forecast accuracy, mountain/orographic skill, snowfall/phase, local
intensity/timing, hazardous-weather prediction or navigation suitability is
established. No observations, rainfall maps/tiles, terrain correction, regional
model, ensemble, production pipeline, mobile or application integration occurred.
Do not add/difference adjacent accumulations without compatible support/lineage
and separately justified rules. Scientific source, decoded field and presentation
remain distinct. Native binary/resource redistribution retains WR007's unclosed
notice/licensing gates; this task redistributes no binary or raw GRIB.

**WEATHER RESEARCH 010 — MULTI-VARIABLE FIELD-COMPATIBILITY AND SCIENTIFIC-CONTRACT
PILOT — NOT BEGUN.**

**Objective:** test a small shared interpretation receipt across representative
field families, reusing the two pinned scalar/accumulation inputs. Prefer a matched
wind-component pair and, if justified, one fraction field to expose basis/range
semantics together. This follows actual interval closure, not a per-variable programme.

**Required evidence/dependencies:** separately authorised acquisition; exact
inventory/message identities, lawfully bounded extraction, parameter/unit/level/
time/grid/basis definitions, checked independent decoders, preserved WR007–009
pins. Verify grid-relative versus earth-relative wind before any derived speed/
direction. Fraction/categorical/vertical/member dimensions must be explicitly
distinguished; no category interpolation, vertical or ensemble validation by analogy.

**Finite scope/resource proposal:** reuse two inputs; at most **three new messages**
(two vector components and one fraction), one historical initialisation/lead,
**50 MB transfer, 20 controlled requests, 150 MB scratch**. No accounts/paid/cloud,
bulk cycles, forecast verification, route queries, tiles or production ingestion.
The next authorisation must confirm the bounds; no new messages identified/acquired now.

**Acceptance:** independent numerical/message/grid/time/unit checks and deterministic
compatibility receipts showing common identity/provenance versus distinct temporal,
vector/scalar/fraction and level semantics. Reject incompatible joins explicitly;
record unsupported categories/vertical/ensemble families without requiring every
family implemented. No permanent provider/framework/schema choice.

**Stop:** conclude on these representative compatibility results or a precise
source/basis/unit/time/decoder blocker; do not fill gaps by extra unbounded fields.
Evidence may change subsequent priorities. **WR010 has not begun.**
