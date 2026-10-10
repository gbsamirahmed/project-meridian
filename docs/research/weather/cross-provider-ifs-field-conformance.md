# WR011 — cross-provider IFS field-contract conformance

Research/access date: **10 October 2026**. Starting public main:
`ae1d72475d24a9a9f16f157c7a480d26f4601fea`, clean, fetched, aligned 0/0.

## 1. Decision and scope

**Outcome B — PARTIAL CONFORMANCE.** Three actual historical ECMWF IFS Open Data
messages were anonymously acquired and numerically decoded with ecCodes2.48.0.
Their identities, temporal/vertical meanings and delivered grid fit the scientific
distinctions in the [WR010 candidate](multi-variable-field-compatibility-pilot.md#7-minimal-candidate-scientific-contract--proposed).
This supplies independent-producer evidence, not independent-decoder agreement:
GDAL3.9.3 reads all three metadata templates/geometry but its installed build lacks
libaec for CCSDS template5.42. **Zero cells were numerically compared between
decoders.** No forecast skill, local accuracy, production readiness or general IFS
compatibility is established.

[WR007](historical-gfs-temperature-field-pilot.md),
[WR008](gfs-native-grid-point-sampling.md) and
[WR009](historical-gfs-precipitation-interval-pilot.md) remain accepted and unchanged.
[WR006 MIDAS Decision C](midas-historical-measurement-support.md) stays BLOCKED.
WR010 proposed scalar + paired wind within three messages; this task explicitly
authorised scalar + interval + one component. That change tests a more informative
temporal boundary; **one U component is not a paired wind product**. No safeguard
for pairing, missingness or uncertain evidence was relaxed.

Evidence grades here: **OBSERVED** actual source/metadata/primary numbers;
**VALIDATED** deterministic replay, framing/checksums, independent metadata/geometry;
**INFERRED** architectural implications; **PROPOSED** candidate refinements;
**UNRESOLVED/BLOCKED** independent numerical decoding and untested structures.

## 2. Exact source, rights and predeclaration

One producer/product/run: **ECMWF IFS**, Open Data delivery `ifs/0p25/oper`, MARS
class `od`, type `fc`, expver `0001`; operational deterministic forecast, centre98,
subcentre0, GRIB2 master table33/local table1, generating process158. That process
number does not establish the exact historical executable/suite version, which is
**UNKNOWN**. The delivered regular grid is not a claim about the model's internal
computational grid.

All primary documents below were retrieved/read and body-hashed on the access date:

| Authority / exact document | Evidence and qualification |
|---|---|
| [ECMWF Open Data client README](https://raw.githubusercontent.com/ecmwf/ecmwf-opendata/main/README.md) and [official client routing/index source](https://raw.githubusercontent.com/ecmwf/ecmwf-opendata/main/ecmwf/opendata/client.py) | Product path, `oper/fc`, parameters/units, JSONL `_offset`/`_length`; inspected, not installed or executed. Current specifications do not substitute for historical encoded metadata |
| [ECMWF-managed AWS catalogue](https://registry.opendata.aws/ecmwf-forecasts/) | Bucket `ecmwf-forecasts`, eu-central-1, anonymous/free without AWS account; CC BY4.0 plus ECMWF conditions; AWS replica can retain earlier releases beyond the portal rolling archive |
| [ECMWF licence/conditions](https://apps.ecmwf.int/datasets/licences/general/) and [CC BY4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en) | Copying, retention, transformation and attributed derived sharing under stated conditions; no endorsement/warranty. Source licence and delivery-service conditions are distinct |
| [Producer parameter definitions, ecCodes2.48.0](https://raw.githubusercontent.com/ecmwf/eccodes/2.48.0/definitions/grib2/localConcepts/ecmf/paramId.def) and [matching units definitions](https://raw.githubusercontent.com/ecmwf/eccodes/2.48.0/definitions/grib2/localConcepts/ecmf/units.def) | Exact local0/1/193 + surface + accumulation mapping to paramId228, total precipitation in metres; requires centre/local-table namespace, not code tuple alone |
| [GDAL3.9.3 CCSDS unpack source](https://raw.githubusercontent.com/OSGeo/gdal/v3.9.3/frmts/grib/degrib/g2clib/aecunpack.c) | libaec-dependent decoder; predeclared binary32 arithmetic profile, not proof that this installed build contains libaec |

The public Open Data webpage request failed TLS certificate validation (unable to
find local issuer), zero response-body bytes. No certificate bypass, login,
provider contact or retry occurred. Other exact primary documents above were
available; the failure is a retrieval limitation, not evidence of absent data.
General terms contain a service-agreement requirement for provision-related
services. The official AWS catalogue documents anonymous public download; no
operational service was requested and no agreement/form was signed. Interpretation
of future contractual delivery obligations remains a provider/legal gate. Neither
public access nor this research clears future production redistribution, paid
service use or offline packaging. No numerical pricing/quota was invented.

CC BY permits commercial reuse subject to its conditions; that is not a complete
commercial/offline delivery clearance. Retain attribution/copyright/source/licence,
identify modifications and no endorsement. Published receipts are small modified
derived outputs; raw GRIBs remain outside Git. **This research is based on data and
products of the European Centre for Medium-Range Weather Forecasts (ECMWF).**
Copyright 2025 ECMWF, source [Open Data DOI](https://doi.org/10.21957/open-data).
ECMWF provides no warranty of accuracy, completeness or availability and excludes
liability under its terms. Research assessments are not legal approval.

Local recursive discovery found no independent-provider GRIB candidate; no huge
unrelated dataset was opened. No alternative provider was needed. Run/three fields,
vertical support, units, actual-metadata acceptance and six deterministic queries
were frozen **before retrieval**. Metadata-led CCSDS scaling/temporal/grid details
were frozen **before numerical interpretation**. Pins retain the source-inspection
confirmation timestamp after a failed working-directory read, still before values.

## 3. Acquisition and immutable identities

[Actual parent object](https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/20250115/00z/ifs/0p25/oper/20250115000000-24h-oper-fc.grib2)
HEAD200: **125,566,280 bytes**, ETag `dc1ba435377f76b6dbda3d4c44414ee3`.
Whole parent not downloaded. Last-Modified 15 January2025 08:34:09 GMT is object
metadata, not forecast issue time.
[Actual JSONL index](https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/20250115/00z/ifs/0p25/oper/20250115000000-24h-oper-fc.index)
34,292 bytes, SHA256 `67bd79565b0e018e2f0aa82c7e769655e1f2a45fd11d14522ef71b5732415521`.
Range end = offset + length − 1; conditional If-Match; each response206, exact
Content-Range/parent length/body count, one GRIB2 frame/terminator and checked identity.

| Local immutable name | Indexed offset / length (bytes) | Raw SHA256 |
|---|---|---|
| `temperature.grib2` | 30,668,984 / 650,860 | `7f7e40c92f5375d4af52f68428c02820105bafa10ad29cf2404ad0c37e7a5f30` |
| `precipitation.grib2` | 24,451,999 / 886,088 | `bbe7a629c06579c27e64a181d2066ed1b36af14544238728d0eda4442083c884` |
| `wind_u.grib2` | 18,957,935 / 865,918 | `4b153144cdb6623906501ddfcc915e16e1d593ce4f0ef821d4a0d62524ea9cfc` |

Actual access demonstrates this one historical object/index, correcting any
over-broad assumption that all IFS public paths are limited to the portal rolling
window. It does not demonstrate complete January coverage or future retention.
No date/lead/product substitution, full archive, additional message or raw-data copy.
Owned WR011 scratch is external to Git; external data-root collections unchanged.

## 4. Actual field meanings and numerical evidence

All reference **2025-01-15T00:00:00Z**, endpoint **2025-01-16T00:00:00Z**.
Primary Python3.12.6/ecCodes Python/native2.48.0/NumPy2.5.2. Reference
Python3.12.6/rasterio1.4.3/GDAL3.9.3/NumPy2.5.3, no installs or upgrades.

| Field | Actual GRIB identity / vertical support | Temporal support / native units | Primary numerical range / mean |
|---|---|---|---|
| `2t`, paramId167 | WMO0/0/0; first surface103, 2 m above model ground; second undefined | PDT4.0 instantaneous +24 h; K | 217.9665069580078–313.1227569580078; 277.4459813569907 K |
| `tp`, paramId228 | ECMWF local0/1/193, master33/local1; first surface1; missing encoded altitude, friendly level0 is not 0 m ASL | PDT4.8 accumulation0–24 h, 86,400 s, statistical code1; m water-equivalent depth | 0–0.20748138427734375; 0.0024342310742763145 m |
| `10u`, paramId165 | WMO0/2/2; surface103, 10 m above model ground; `uvRelativeToGrid=0`, flags48, eastward Earth-relative component | PDT4.0 instantaneous +24 h; m s⁻¹ | −26.932388305664062–26.520736694335938; −0.23637805032810935 m s⁻¹ |

Each: **1,038,240 finite/valid cells, zero missing**, no bitmap. Precipitation:
184,798 zero, zero negative; temperature zero zero/negative; U569,300 negative
(valid signed component, not negative wind speed). Means are unweighted native-node
summaries, not area means, atmospheric truth or model skill. Values are unmodified;
no unit conversion, precipitation rate, lapse-rate correction, resampling or clamp.

Precipitation PDT4.8 raw octets and independent GDAL template bytes agree with
ecCodes: reference/start15 January00 UTC, end/valid16 January00 UTC, forecastTime0 h,
duration24 h; end lead24 h differs from start lead0 h. One range, missing-statistical
count0, increment type2/unit13/**450 seconds** retained. No internal step/sample
count or endpoint-integration algorithm is inferred. GFS WR009's18–24 h accumulation
cannot be replaced by this0–24 h quantity merely because endpoints coincide.

All use **template5.42 CCSDS**, flags14/block32/RSI128. R/E/D/bits:
temperature217.9665069580078/−5/0/12; precipitation0/−18/0/16;
U−26.932388305664062/−6/0/12. Bitmap-free does not validate other missingness profiles.
ecCodes 9999 missing sentinel is not an observed missing cell.

Independent GDAL metadata verifies centre/reference/validity/level, raw PDT bytes
and affine geometry. Temperature/U unit labels agree. For local precipitation
GDAL reports **unknown / `[-]`**; the producer's scoped definitions establish
metres, not an independently recognised GDAL unit. Independent numerical reads
fail explicitly: **“Data Representation Template5.42 decoding requires building
against libaec”**, followed by a misleading “Out of memory” wrapper diagnostic.
No actual memory exhaustion is established. No replacement decoder/install,
repacked synthetic GRIB or tolerance increase was used. Predeclared binary32
prediction plus half-ULP bound is retained, **synthetic-only**, awaiting real agreement.

## 5. Geometry and query boundaries

All three encoded Section3 hashes match:
`6e8229bf09d191ccf7d719ef88dc9e848fe663cf45a91d0691b7e17815a03036`.
Template3.0 regular_ll,1440×721,.25° spacing, scan0, north90→south−90,
shape6 sphere radius6,371,229 m. Longitude columns start180°, end179.75°,
periodic with no duplicate endpoint; latitude is not periodic. This is the
**same geographic node set** as GFS but a **different encoded grid/storage origin**.
GFS→IFS column mapping `(column−720) mod1440` identifies corresponding geographic
nodes, not an array mutation/regridding operation. No cross-model values compared.

Four separate representations: encoded native order180..359.75,0..179.75;
ecCodes labels−180..179.75; GDAL affine centres180..539.75; external queries finite
latitude/longitude with deterministic modulo360 labels and signed−180..180 display.
The first replay rejected signed labels before this equivalence was established;
the correction changes coordinate labels only, preserving every value/index.
GDAL transform `(.25,0,179.875,0,−.25,90.125,0,0,1)` matches the same sphere/order.

WR008's old adapter rejects origin180; this is a finite implementation limitation,
not a scientific incompatibility. A narrow shifted-origin geometry adapter reuses
unchanged WR008 sampling mathematics: grid-axis nearest (not minimum geodesic
distance), ties south/east, nearest poles canonical native column0, bilinear angular
weights, all four nodes required even at zero weight, no silent fallback,
bilinear polar caps beyond±89.75° rejected. It does not validate reduced Gaussian,
rotated, curvilinear, projected or unstructured grids.

Frozen query results below are **single-decoder values**. GDAL affine independently
agrees on nodes/coordinates/weights, not numerical samples or a new GDAL-warp kernel.

| Query latitude / longitude / method | Temperature K | Precipitation m over0–24 h | Eastward U m s⁻¹ |
|---|---|---|---|
| 50 / 0 / nearest, native row160 col720 | 282.2790069580078 | .000492095947265625 | −2.4948883056640625 |
| 49.9 / .1 / bilinear | 281.2065069580078 | .000589447021484378 | −2.561138305664074 |
| −40.1 / 179.9 / bilinear | 289.5327569580078 | .0008290100097656269 | 2.786361694335965 |
| −40.1 / −180.1 / bilinear | identical to preceding query | identical | identical |
| 89.875 / 0 / bilinear | polar-cap rejection | polar-cap rejection | polar-cap rejection |
| 91 / 0 / nearest | invalid-latitude rejection | invalid-latitude rejection | invalid-latitude rejection |

Eighteen query receipts:12 successful single-decoder queries,6 explicit rejections.
No independent numerical maximum difference can be reported. Interpolation adds no
meteorological resolution or actual terrain representation; U point sampling is not
vector transport/polar-vector interpretation. Grid queryability is not route/offline
performance, summit/valley accuracy or observational reference eligibility.

## 6. Conformance matrix and candidate revision

Original WR010 concepts are retained; original reports/utilities are immutable.
The following evaluates the conceptual contract separately from GFS-specific code:

| Element | Classification | Evidence / treatment |
|---|---|---|
| Source/product/provenance | Provider-specific mapping | Actual centre98/MARS/local Section2 + checked AWS path/index; model release remains unknown |
| Reference/valid instant | Directly supported | PDT4.0/raw GDAL bytes agree for2t/U; no single universal lead convention |
| Accumulation support | Provider-specific mapping | Same discriminant, explicit0–24 h; retain nonzero450 s increment. Old WR009 narrow implementation rejects it correctly |
| Parameter authority | Explicit contract extension | Qualify tuple with centre/master/local-table/definition edition; local0/1/193 is not GFS0/1/8 or a globally unique WMO meaning |
| Physical/native units | Provider-specific mapping | NativeK,m,m/s; producer metre definition supported, independent GDAL local-unit label unavailable |
| Vertical meaning | Directly supported with explicit mapping | Model-ground-relative2/10 m vs surface with no altitude; friendly zero must not imply height |
| Horizontal geometry | Explicit contract clarification | Retain longitude origin and label/storage mapping; same node set is not same encoded grid |
| Encoding/missingness | Supported with provider mapping, verification BLOCKED | CCSDS is new packing; primary finite/no-bitmap evidence; independent numerical decoder unavailable |
| Evidence/quality | Directly supported | Separate primary numerical, independent metadata, unverified numerical agreement, and forecast skill |
| Optional vector relationship | Not tested as a pair | Earth-relative U component established; no V acquired, no pair/speed/direction assertion |
| Ensemble identity | Deterministic directly supported; members not tested | No ensemble metadata structure in these messages; do not invent member0 |
| Spatial query | Conditional geometry-level support | Shifted regular grid and affine agree; actual numerical samples single-decoder, new interpolation kernel not independently validated |
| Other grid/statistic/level/fraction/category families | Not tested | Explicit rejection, no forced geometry or fabricated compatibility |

**Revised research candidate**, not accepted production API:

1. Keep source/product/provenance and unknown version explicit. Namespace parameter
   codes with authority and table versions, keeping decoder friendly names secondary.
2. Keep temporal support discriminated: instant or interval statistic; interval
   bounds/duration/process plus encoded qualifiers. Lead-to-start/end are separate.
3. Keep quantity/native units and vertical reference separate; absence of a surface
   altitude is null/unknown, not a numerical elevation inferred from level0.
4. Keep horizontal geometry, native storage ordering and coordinate-label conventions;
   grid-family-specific query operations are separate from the shared point-query concept.
5. Keep input/encoding/missingness and evidence grades per axis. Decoding availability,
   metadata interpretation, reproducibility, numerical agreement and scientific skill
   are different assertions; failure receipts cannot become validated values.

No new universal hierarchy/schema or arbitrary GRIB dump replaces physical meaning.
Provider adapters resolve dictionaries; grid adapters implement tested geometry;
variable-family interpreters resolve temporal/units/basis. Ensembles/new geometries
remain unvalidated extension seams. Display choices, route context, cached tiles,
Workspace/Personal/Community and sharing remain outside intrinsic field identity.
GFS is not selected permanently; regional/ensemble/observation/mountain-weather and
offline research remain first-class. No application integration or production changes.

## 7. Replay, validation, resources and preservation

[Instructions](../../../scripts/weather-research/wr011/README.md),
[utility](../../../scripts/weather-research/wr011/ifs_contract_pilot.py),
[tests](../../../scripts/weather-research/wr011/test_ifs_contract_pilot.py),
[pins](../../../scripts/weather-research/wr011/input-pins.json),
[receipt](../../../scripts/weather-research/wr011/integrity-receipt.json).
Scientific JSON **55,996 bytes**, SHA256
`b35534194aa168e8750363f348b74551139fd8f8a14194bdd33d3c8d379ab31b`.
Acquisition dates/resources are separate. Two genuine replays match byte-for-byte;
input hashes/decoded arrays unchanged. This is local reproducibility, not promised
archive retrievability or independent numerical correctness.

**34 focused tests:33 synthetic + one genuine three-field double replay**, zero
skips. Tests cover namespace/units/levels/provenance/member/frame/statistic/timing
contradictions, unsupported grids/packing, missing/nonfinite values, wraps/ties,
affine/constant mathematics, explicit evidence distinction and unchanged old-profile
rejections. Floating constant equality test was corrected to a float64 arithmetic
tolerance; no empirical numerical-comparison tolerance changed. Exact regression,
publication, documentation/preservation/lint/type/app-only results are in the
development log. No expensive unrelated scientific replay or full data-materialising
production build; production/scientific publications unchanged.

Controlled ledger: **14 attempts /3,427,413 response-body bytes**, including all
documentation, index, HEAD and one TLS-failed attempt; **3 payloads /2,402,866 bytes**.
No retries, redirects, credentials, paid/cloud/accounts, package installation or
new fields beyond the declared three. Git/HTTP/TLS overhead/OS traffic unmetered:
**no certified total-network budget or zero-total-network claim**. Source body sizes,
checksums and UTC times are in pins/receipt. No acquisition occurs in replay/tests.

Standalone Windows PSAPI primary peak working set154,886,144 bytes; maximum separate
GDAL peak64,241,664 bytes. Sum219,127,808 is a conservative sum of separate lifetime
peaks, not simultaneous measured RAM; process commit/PagefileUsage is not scratch
storage or disk writes. The failed decoder's error does not imply budget exhaustion.
Sequential temporary metadata≤1,652 bytes in that run, removed. Final audit scratch
and conservative temporary allowance are recorded in the log, below150 MB; scratch
ceiling does not impose a process-RAM ceiling. No full decoded field copies retained.

Preflight33/33 safeguards passed. Final preservation checks repeat the42 statuses,
113 hashes,40,842 Weather publication files and all accepted fixtures/projections/
WR007–010 evidence. No private access, raw input/pin mutation, source moves or external
data-root changes. Only bounded new research code/report/receipt and append-only notes.

## 8. Exactly one next bounded task — NOT BEGUN

**INDEPENDENT CCSDS NUMERICAL-DECODING CONFORMANCE — NOT BEGUN.**

**Objective:** resolve the actual template5.42 independent-decoder gap on these
three preserved IFS inputs, without acquiring new forecasts or comparing skill.
**Evidence/dependencies:** a lawful independently implemented CCSDS-capable decoder
with identified build/libaec support, parameter-table scope and native units;
preserved WR011 pins/primary receipt and prior GFS regressions. If tooling provision
is necessary, require separate task authority for isolated tooling; do not alter
global/project environments or silently install packages here.

**Scope:** replay at most these three messages; compare matching physical cells,
geometry, masks, raw PDT/time metadata and native numbers using the already declared
packing-derived binary32 profile where applicable, or predeclare a justified profile
for a genuinely different implementation. Do not hide local-parameter vocabulary
limitations. No repacking/ecCodes wrapper presented as independent evidence.

**Acceptance:** reproducible independent numerical comparison/qualified local-unit
mapping, immutability and resource receipts, or precise build/semantics blocker.
**Resources:** zero new forecast acquisition;≤150 MB additional scratch; any separately
authorised tooling retrieval must be finite/metered,≤20 requests/≤50 MB bodies, no
paid services or production dependencies. **Stop:** after this one independent-decoder
gate; no provider selection, MIDAS reopening, skill experiment, new field family,
production architecture or application integration. No subsequent task has begun.
