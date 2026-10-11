# WR013 Scientific field-packaging and offline query replay

11 October 2026. Starting public `main` checkpoint:
`c5fc440c4978811c1ea285452ec716a404d6b6af`.

## 1. Decision and scope

**OUTCOME A — VERIFIED OFFLINE SCIENTIFIC REPLAY**, limited to three genuine,
all-finite, regular-grid subsets and the declared Windows/Python profile.
All **1,575 cells** survive little-endian binary64 packaging exactly. All **66
supported nearest/bilinear queries** reproduce the source-native baseline exactly,
including contributing nonzero-weight nodes and weights; **18 declared invalid,
unsupported, out-of-extent or temporal-assumption requests** fail explicitly.
Replay runs with only a package, standard-library reader and requests, without
GRIB inputs, scientific decoders or network operations in the guarded process.

This establishes scientific preservation/replay semantics, not production format
suitability, mobile performance, scalable delivery, operational availability,
forecast accuracy, terrain accuracy or commercial/offline redistribution rights.
[WR006's reference Decision C](midas-historical-measurement-support.md) remains
BLOCKED. WR011's historical partial outcome is unchanged; the subsequent
[WR012](independent-ccsds-numerical-conformance.md) qualified numerical evidence is
carried forward separately.

The original WR012 next-task proposal suggested GFS temperature, IFS temperature
and IFS precipitation. **This task's explicit instruction supersedes that proposed
sample:** GFS temperature, GFS APCP and IFS precipitation. It tests two different
accumulation durations/native units without adding a fourth field. No historical
conclusion or original source is overwritten.

Evidence terms: **OBSERVED** means actual local input/process inspection;
**VALIDATED** means a declared finite preservation/query check passed;
**INFERRED** means an engineering implication; **PROPOSED** means an unaccepted
research refinement; **UNRESOLVED/BLOCKED** retains an unmet evidence gate.
Synthetic tests are never historical field evidence.

## 2. Accepted inputs and provenance

The original accepted files were found at their existing WR007/WR009/WR011 owned
research locations. Pin identity, contents and checksums resolved discovery; no
new download, broad directory traversal, copies of global fields, external-root
move or reorganisation was needed. Source filenames are retained; machine-specific
paths are deliberately absent from public records.

| Field | Source file | Bytes | Raw SHA256 |
|---|---|---:|---|
| GFS temperature | `gfs-2025011500-f024-t2m.grib2` | 874,115 | `0b95fc06fe9ca08de57f9c5089b8fcd5d7b6a42977b35f669da65ec0f43f40e4` |
| GFS APCP | `gfs-2025011500-f024-apcp-18-24h.grib2` | 343,228 | `e2a311fa2089ab1982d9b09e7ec82f483e07ef06f38457d9e379fe9cef970848` |
| IFS precipitation | `precipitation.grib2` | 886,088 | `bbe7a629c06579c27e64a181d2066ed1b36af14544238728d0eda4442083c884` |

All three raw seals and complete decoded-array seals matched their accepted
baselines before extraction; raw seals matched again afterwards. Primary decoding:
Python3.12.6, ecCodes/native Python binding2.48.0, NumPy2.5.2. Complete arrays are
decoded once per construction, not repeatedly for point queries; each field is
released after its tiny subset/source-query baselines are retained. Development
and final notice-preserving construction runs are separately identified in owned
scratch, not additional scientific acquisitions.

Source evidence: [WR007](historical-gfs-temperature-field-pilot.md),
[WR009](historical-gfs-precipitation-interval-pilot.md) and
[WR011](cross-provider-ifs-field-conformance.md) retain exact authoritative archive
objects, range/index evidence, access times, licences and notices. Their source
documentation was inspected **10 October 2026**; WR013 reuses that dated evidence,
with **zero new documentation lookups**. It does not pretend to recheck hosted
terms or future archive availability. NOAA GFS source terms and ECMWF CC BY4.0,
attribution, copyright and service qualifications remain distinct from new legal
clearance. Generated packages remain local research artefacts, outside Git.

This research is based on data and products of the European Centre for Medium-Range
Weather Forecasts (ECMWF). Copyright 2025 ECMWF; the subset and receipts are modified
derived research material with retained source notices and no endorsement.

| Scientific property | GFS temperature | GFS APCP | IFS precipitation |
|---|---|---|---|
| Product | NOAA/NCEP operational deterministic GFS | Same historical run/product | ECMWF IFS Open Data deterministic `od/oper/fc` |
| Reference / endpoint | 15 Jan2025 00 UTC / 16 Jan2025 00 UTC | Same | Same |
| Parameter authority | WMO0/0/0, centre7, master2/local1 | WMO0/1/8, same table context | ECMWF local0/1/193, centre98, master33/local1, paramId228 |
| Native units | K | `kg m**-2` | m |
| Vertical meaning | 2 m above model ground, code103 | Surface code1; no physical altitude established by friendly level0 | Surface code1; encoded first-surface height/scales missing, not a measured altitude0 m |
| Temporal support | Instantaneous +24 h, PDT0 | Accumulation +18–24 h, PDT8; 15 Jan18 to 16 Jan00 UTC; **21,600 s** | Accumulation +0–24 h, PDT8; 15 Jan00 to 16 Jan00 UTC; **86,400 s** |
| Statistical increment | Not applicable | Code2, zero; increment-unit255 retained as unspecified | Code2, unit13, 450 s; no inferred output cadence/internal sample count |
| Numerical evidence inherited | ecCodes/GDAL, full-grid qualified binary32 residual | ecCodes/GDAL full-grid exact | WR012 separate GRIB interpretation/scaling plus shared libaec, full-grid exact; independence B |
| Packing retained in metadata | GRIB2 template5.3, complex spatial differencing, decimal scale2 | GRIB2 template5.3, decimal scale0 | GRIB2 template5.42 CCSDS, decimal scale0 |

This is a comparison of meanings, not predictive values or precipitation skill.
Metres are not converted to kilograms per square metre; no rates are derived.
The shared endpoint cannot erase different physical quantities, vertical support
or accumulation windows. Exact executable/suite revisions remain unresolved.

## 3. Frozen geometry and query profile

[Input pins](../../../scripts/weather-research/wr013/input-pins.json) contain the UTC
predeclaration, every request, acceptance criteria and immutable dependencies.
The separate original freeze SHA256 is
`50ec81a7041b65d62f34110b32ed40d2396945ccefdfb2ce71f695559c99aad0`;
profile timing precedes first packaging and inspection of new subset/query results. The modest Scottish
rectangle was chosen for outdoor-relevant coordinates and boundary coverage, not
for convenient numerical outcomes.

**Extent:** inclusive native nodes at 54–59°N, 8–2°W; **21 rows ×25 columns**,
0.25-degree increments. Native source row indices124–144 for all fields; GFS
columns1408–1432, IFS columns688–712. Coordinates are point nodes, not area cells.
No grid rolling, transpose, smoothing, resampling or elevation correction occurs.

Both source grids are1440×721 regular latitude/longitude, latitude90 to−90,
scan0, spherical Earth radius6,371,229 m. GFS encoded longitude origin0 differs
from IFS180; IFS ecCodes signed labels and GFS0–360 labels are mapped explicitly.
GFS Section3 SHA256:
`2f05f13897b18b42bb2790905e2476fce9a2e07b89f63499a12da9e202f3367f`;
IFS Section3:
`6e8229bf09d191ccf7d719ef88dc9e848fe663cf45a91d0691b7e17815a03036`.
They are **different encoded grids with coincident subset coordinates**, not
evidence for arbitrary cross-grid interpolation or regridding.

Each field runs the same11 locations in both methods: exact node56.5,−5;
longitude midpoint56.5,−4.875; latitude midpoint56.375,−5;
interior56.37,−4.88; Highland fixture56.79685,−5.00349;
equivalent longitudes355 and715 at56.5; northwest59,−8;
southeast54,−2; north edge59,−5; east edge56.5,−2.
Each also tests north-outside59.01,−5; east-outside54,−1.999;
pole90,−5; invalid latitude91; unsupported`CUBIC`; and the wrong instant/accumulation
assumption. Non-finite, malformed and unit/level cases are additional synthetic
negative tests. Coordinates are fixtures, not local accuracy claims.

Nearest retains [WR008](gfs-native-grid-point-sampling.md)'s **angular-grid-axis**
definition and east/south halfway ties; it is not guaranteed geodesic nearest.
Bilinear retains four finite contributing nodes and weight-sum checks. At the
closed south/east subset edges an **inward adjacent stencil** is used, preserving
the boundary value while avoiding unavailable global zero-weight nodes.
Positive-weight native node coordinates, indices, values and weights agree exactly
with the original global sampler. Full four-node identity is not claimed at those
edges. Missing contributors are unsupported, even when their weight would be zero.

Finite external longitudes normalise modulo360, then must lie inside the bounded
native window352–358. Longitude normalisation is not periodic subset interpolation.
Latitude never wraps; all out-of-extent queries fail even if nearest rounding could
reach an inside node. No subset extrapolation, polar-cap extension, temporal
interpolation or change to the protected WR008/WR011 global rules.

## 4. Disposable package and preservation results

The research representation is **one UTF-8 JSON manifest and three flat
little-endian IEEE754 binary64 row-major payloads**. Transparent metadata and
standard-library `struct` permit an independently executable reader; no running
service or GRIB decoder is needed. Binary64 retains the accepted ecCodes values
exactly rather than introducing decimal text rounding or binary32 conversion.
The format/version is disposable apparatus, not a proposed universal field format,
database, tile specification or permanent production API.

The manifest retains full source parameter/table context, model/run, vertical and
temporal meanings, increment qualifiers, original packing keys/precision and
missingness, raw checksums/source notices, decoder/evidence identities, full native
grid origin/scanning/Earth shape, subset offsets and transformation provenance.
WR007 did not record every later contract key; the missing encoded time-unit,
paramId and second-surface keys are **read from that same verified message** and
labelled source reconstruction in the constructor, rather than guessed from
friendly names. No new numerical decoding claim changes the historical receipt.

| Component | Bytes | SHA256 |
|---|---:|---|
| `manifest.json` | 29,996 | `4836d64d2800ca396b3684256f0302734626da41d94e0a2942f45b7dadee2687` |
| `gfs-temperature.f64` | 4,200 | `3c1c25149ea87f0d35e1b8df3a527d32882e6f563b2fd8b67e1979428c694890` |
| `gfs-apcp.f64` | 4,200 | `519e0f062b3b4224f0f5c34385c04be0f5315395cd4603e73a917e3270ce86a9` |
| `ifs-precipitation.f64` | 4,200 | `9a7664e5540518e654463534160ae3eefa56a10761924210f0770bb7d795f821` |

**Final package42,596 bytes**, metadata29,996 plus numerical payload12,600.
The manifest SHA256 is the package identity and must be supplied from a trusted
receipt. Metadata hashes do not authenticate a maliciously replaced source or
establish meteorological accuracy. Payload hashes/length/precision are validated
before returning any value. Every reopened value is compared with the accepted
source subset: **525/525 exact per field, max/mean absolute difference0, 525 finite,
zero missing**. Original decoded binary64 and packaged binary64 precision agree.
The raw compressed GRIB stream cannot be reconstructed from this subset; its
identity and source encoding metadata are preserved, not its full numerical domain.

[Package integrity receipt](../../../scripts/weather-research/wr013/package-integrity-receipt.json)
records raw and complete-array seals, decoder versions, component seals and every
cell comparison. Package payloads and the manifest stay outside Git; compact
research receipts/pins/code are committed. Transformation is native-index
extraction and reversible value serialisation, not reversible recovery of discarded
global cells or original compressed messages.

## 5. Offline numerical queries and isolation

The [standalone reader](../../../scripts/weather-research/wr013/offline_reader.py)
loads only the package, validates its scientific metadata and answers requests with
field identity, normalised coordinates, native units, temporal/vertical meanings,
source nodes/weights, source input hash and package identity. Field lookup is
explicit. Optional expectations reject incorrect units, vertical reference,
temporal kind or the full temporal object. It never falls back to a source decoder.

| Query example, bilinear | GFS temperature K | GFS APCP kg/m²,18–24 h | IFS precipitation m,0–24 h |
|---|---:|---:|---:|
| Native node56.5,−5 | 278.4979296875 | 0 | 0.00083160400390625 |
| Interior56.37,−4.88 | 277.26165768749996 | 0 | 0.0004697998046874944 |
| Closed southeast54,−2 | 276.6279296875 | 0 | 0.000064849853515625 |

Every supported query has **zero native-value difference**, under the **predeclared
zero absolute tolerance**; nearest and bilinear each have33 successful comparisons.
All18 rejection outcomes match their frozen statuses. The complete
[query receipt](../../../scripts/weather-research/wr013/offline-query-replay-receipt.json)
retains coordinates through the pins, node values/weights and distinct time support.
No favourable-looking number drove location or profile selection. Numerical
agreement is preservation evidence, not rainfall timing, local intensity or skill.

Isolation: the constructor creates a new temporary directory containing only
`package/`, a copy of `offline_reader.py` and `requests.json`. It invokes a fresh
Python process with **`-I -S -B`**. No WR007–WR012 code or scientific dependencies
are copied/imported. The expected manifest identity is passed as a literal argument,
not obtained by opening raw files. A cooperative audit guard rejects scientific
imports, outside file reads, writes, network and child-process operations.
The read log contains only the four package components and requests. Scientific
module list is empty. The opted-in genuine test repeats this process twice;
deterministic results/read logs agree, with volatile process counters excluded.

**Isolation limitation:** standard-library startup imports occur before the guard;
the Windows host and parent still possess the original files. This is evidence
that this reader has no source/network fallback and only reads the finite package,
not an OS sandbox or a hostile-code proof of inaccessibility. Four synthetic guard
probes explicitly reject outside GRIB reads, writes, a simulated socket event and
an ecCodes import; no real remote network connection is attempted by those probes.

## 6. Contract consequences and explicit exclusions

| Candidate element | Evidence classification | Treatment supported by this experiment |
|---|---|---|
| Source/product/run, raw provenance and table authority | Preserved and verified | Intrinsic scientific identity stays independent of storage/display |
| Instant versus accumulation, bounds/statistic/increment | Preserved and verified | Endpoint alone cannot identify a quantity's temporal support |
| Native units and height/surface reference | Preserved and verified | No universal unit or vertical-level normalisation |
| Geometry and native alignment | Preserved with explicit mapping | Source grid plus native subset index window; encoded origins remain distinct |
| Binary64 values/no-bitmap missingness | Preserved and verified for all-finite inputs | No inference about masked/sentinel-bearing fields |
| Source GRIB versus interpreted/package encoding | Requires justified refinement — PROPOSED | Separate source packing metadata from subset encoding, precision and transformation identity |
| Query provenance and bounded domain | Requires justified refinement — PROPOSED | Preserve package identity, supported extent/method and rejection semantics; parent periodicity is not subset periodicity |
| Numerical evidence versus scientific quality | Preserved and verified | Inherited decoder checks, new packaging checks and forecast skill are separate grades |
| Vectors, categories, upper air, ensembles | Not tested | Do not extend this reader/profile by assumption |
| Other grids, antimeridian-spanning subsets, poles, temporal interpolation | Unsupported by this apparatus | Explicit new scientific evidence required |

The smallest refinement is **a declared transformation/subset stage with its own
identity and query domain**, not a new inheritance hierarchy. Source-native encoding,
interpreted field, extracted numerical representation and query answer are distinct
stages with linked provenance. A future representation can change while preserving
these meanings; no storage language, database, cache, cloud, renderer or API choice
is made. The reader's finite validators are research guards, not a general GRIB or
universal scientific-contract implementation.

Values describe model-grid near-surface temperature or water-equivalent accumulation.
They do not establish temperature2 m above real mountain terrain, precipitation
phase, resolved valleys/summits, local intensity or safe navigation suitability.
Bilinear querying adds no meteorological resolution. No observations, corrections,
forecast errors, MIDAS reinterpretation or model-superiority claims.

## 7. Validation and resources

**43 focused tests passed, zero skips:**42 synthetic mathematical/rejection/guard
tests and one genuine three-field package test with two isolated process replays.
Constructor evidence includes all1,575 source-to-reopened values and84 query cases;
synthetic tests do not validate meteorological decoding. Relevant WR007–WR012
regressions **30/37/49/25/34/36** passed with opted-in real local inputs, zero final
skips. Publication checks7, lint, TypeScript and application-only build passed.
Application build excludes public-data copying and materialising Weather plugins;
existing large-chunk/owned-outdir warnings remain. No unrelated scientific replays
or production data build was run.

Preflight **33/33** preservation safeguards passed. Final **44/44** safeguards verify42 Atlas
status rows,113 protected hashes,40,842 retained Weather files, accepted fixtures,
source seals/projections and unchanged WR007–WR012 evidence. Documentation/evidence **47/47** checks and **460 internal links/anchors** pass;
source-date, scope, resource and full-diff checks precede release. No source scientific data,
generated package, binaries, secrets or machine-specific paths enter Git. Existing
production code/behaviour and the external data directory remain unchanged.

**Zero controlled HTTP documentation requests/bytes, zero new forecasts and zero
installations**. Source rights documentation is reused at its recorded access date.
Git fetch/push, protocol overhead and incidental host traffic are unmetered; local
publication fixtures use loopback networking. No certified zero-total-network
claim is made. Replay's guarded code performs no network operations.

Final construction observed owned scratch2,950,788 bytes during isolation, including
70,514 bytes of removable isolation copies. Final package42,596 bytes. Resource
counters are separate from deterministic scientific receipts. Final scratch
inventory plus a conservative60 MB temporary-test allowance stays below150 MB;
the final development log records the measured inventory. No new scientific
payload was copied into the external data root, and no accepted file was moved.

Primary peak working set199,852,032 bytes, isolated reader19,365,888 bytes. Sum of
separate lifetime peaks219,217,920 bytes is a conservative sum, not measured concurrent
RAM. Primary peak pagefile/commit counter821,260,288 bytes is **not scratch storage
written to disk**. The 150 MB constraint applies to owned generated files, not
process virtual-memory reservation. Measurements are this Windows profile, not
mobile/offline application performance.

## 8. Programme reassessment and exactly one next task

Preservation/replay is now established for this small scalar/interval profile.
Further packaging refinement alone has less information value than introducing
the still-unvalidated ensemble dimension. Global/regional, ensemble uncertainty,
mountain representativeness, other quantities, observations/nowcasting, ML,
rights/economics and offline delivery remain open programme tracks. Neither GFS
nor IFS is selected permanently; WR006's reference block does not prevent
legitimate numerical/metadata experiments.

**ENSEMBLE-MEMBER IDENTITY AND BOUNDED UNCERTAINTY-SEMANTICS PILOT — NOT BEGUN.**

**Objective:** test whether a genuine small ensemble cohort can preserve member
identity and scientifically compatible time/unit/level/grid supports without
mistaking a deterministic field or unpaired members for a probability forecast.
**Evidence/dependencies:** existing candidate contract and preservation rules;
source-specific authoritative product/member documentation, lawful bounded archive
access, decoding capability and exact real-message identities, reviewed before
acquisition. No source discovery for that task has begun here.
**Scope:** one global ensemble system, one identified run, one lead, one scalar
quantity/level and at most three genuine member messages (control/perturbations
where that source actually supports them). Select the system through access and
scientific evidence gates, not a predetermined provider. Freeze membership and
compatibility rules; inspect exact GRIB ensemble metadata, missingness and numerical
integrity, independently where available. A tiny cohort can test identity and
bounded descriptive arithmetic; it cannot establish a reliable full-ensemble
probability distribution, calibration, skill or safety suitability.
**Acceptance:** unambiguous product/member provenance, compatible scientific
supports, reproducible numerical/member receipts and explicit rejection of mixed
supports, or a precise access/encoding/member blocker. **Resources:** at most20
controlled HTTP requests/50 MB transfer/150 MB scratch, no installation, paid
service, cloud or bulk cycle. **Stop:** after that finite member/contract evidence;
no ensemble production pipeline, further packaging implementation, observation
verification, forecasting service, application integration or subsequent task.
