# WR014 — Ensemble-member identity and bounded uncertainty semantics

11 October 2026. Starting checkpoint `41ebfa17a581edb2bb21537e2a7d0f33e282cd43`, public `main`, clean and aligned with `origin/main`, divergence 0/0.

## 1. Decision and evidence scope

**OUTCOME A — VERIFIED BOUNDED ENSEMBLE CONFORMANCE.** Three actual NOAA/NCEP GEFS messages establish one coherent historical ensemble profile, encoded member identities and independent numerical agreement. This result is limited to the selected control and two positively perturbed members, one scalar, one run/lead, one delivered grid and the tested Windows decoding environments. It does not establish a complete ensemble distribution, calibrated uncertainty, forecast skill or production readiness.

**OBSERVED:** PDT4.1 identifies member numbers 0, 1 and 2 and type codes 1, 3 and 3. All three encode an ensemble-count value of **30**. **DOCUMENTED:** NCEP's GEFS v12 system has **31 members**, comprising 30 perturbations and one control. The NOAA-managed AWS registry still describes a 21-member product. **UNRESOLVED:** exact interpretation of the encoded count relative to that complete historical population. No count is silently replaced with another; the filename alone is not identity evidence. This unresolved full-population mapping does not invalidate the three encoded identities or their selected-subset comparison.

[WR010](multi-variable-field-compatibility-pilot.md), [WR011](cross-provider-ifs-field-conformance.md), [WR012](independent-ccsds-numerical-conformance.md) and [WR013](scientific-field-packaging-offline-replay.md) retain their historical findings. WR006's strict and revised MIDAS targets remain **BLOCKED**. No reference verification or application implementation begins here.

## 2. Source gate, predeclaration and provenance

Authoritative documents were retrieved anonymously on **11 October 2026**, with exact URLs, acquisition timestamps, sizes, SHA-256 hashes and HTTP evidence retained in [input pins](../../../scripts/weather-research/wr014/input-pins.json). Evidence is documentation, index evidence or actual-message inspection as stated; no restricted accounts or terms were accepted.

- [NOAA-managed GEFS AWS registry](https://registry.opendata.aws/noaa-gefs/) identifies `noaa-gefs-pds`, public anonymous access and the data-use notice. It permits use as desired, requests NOAA attribution, prohibits implied endorsement/affiliation and requires modified data not be represented as unaltered NOAA data. Its **21-member description contradicts NCEP system documentation**; it is not used to classify historical members.
- [NCEP EMC GEFS technical system page](https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gefs.php) describes v12 implementation on 23 September 2020 and 30 perturbed members plus one control. Its computational C384L64/~25 km resolution is distinct from this **0.50° delivered product**. The exact January 2025 executable/suite revision is **UNKNOWN**.
- [NCEP GEFS product catalogue](https://www.nco.ncep.noaa.gov/pmb/products/gens/) and three historical `.idx` inventories provide the atmospheric-product route and the single selected TMP/2 m/+24 h message.
- [PDT4.1](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp4-1.shtml) defines individual ensemble messages and octets 35–37 for type, perturbation number and number of forecasts. [Code table 4.6](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-6.shtml) maps type **1** to unperturbed low-resolution control and type **3** to positively perturbed forecast. The accessed table was revised on 18 September 2025; it supplies definitions for the actual encoded codes, rather than a claim to have preserved a January table snapshot.
- [NCEP generating-process table](https://www.nco.ncep.noaa.gov/pmb/docs/on388/tablea.html) identifies process **107** as GEFS. A generating-process code is not an executable-version identifier.

GEFS was selected because precise historical inventories, encoded member fields, official code definitions and small verified extraction supported the identity question. No additional ensemble provider was needed.

A complete authorised external-root filename inventory contained **133,328 paths and no candidate raw ensemble files**. No numerical values in unrelated collections were read. No external files were moved or reorganised.

The original profile was frozen at **07:34:33.001307 UTC**, before the first GRIB payload. SHA-256: `49d9fdb6885ecd26afcc156ca941950edaf55b77e072fd7b0ecf35d16c30b7ff`. It specified GEFS `pgrb2ap5/pgrb2a`, **2025-01-15 00 UTC**, **+24 h**, valid **2025-01-16 00 UTC**, instantaneous **2 m temperature in K**, members 0/type1, 1/type3 and 2/type3; expected support/grid, rejection rules, five native-node locations and descriptive-only arithmetic. No substitution occurred.

### Prospective comparison amendment

The original declaration used a final binary32 half-ULP bound. Metadata-only inspection then established DRT3 complex spatial differencing with decimal scale **D=2**, binary scale **E=0**. Before numerical arrays or decoder differences were examined, at **07:37:06.241735 UTC**, that bound was replaced with the already accepted WR007 **two-operation** g2clib rounding bound. Original and revised rules, reason and timing are preserved; amendment SHA-256 `a7a270c83490f215ae715d942a251b5214983f3b77e57c154ead02ea73cdbde3`.

Revised acceptance requires exact agreement with predicted g2clib binary32 values **and** the per-cell bound:
`0.5 ULP(sum) × |D32| + |exact sum| × |D32 − 0.01| + 0.5 ULP(product) + 8 ε64 × |primary|`.
This allows explained coefficient/addition/multiplication rounding, not an empirically fitted tolerance. Source, members, native units, locations and limits were unchanged. The original rule is not represented as having passed.

## 3. Exact acquisitions and scientific identity

Historical prefix: `https://noaa-gefs-pds.s3.amazonaws.com/gefs.20250115/00/atmos/pgrb2ap5/`. Inventories end in `.idx`; object labels identify the original full product, not a downloaded full cycle.

| Member / object | Inclusive byte range | Extracted bytes |
|---|---|---:|
| control / `gec00.t00z.pgrb2a.0p50.f024` | 11591484–11828588 | 237,105 |
| perturbation 1 / `gep01.t00z.pgrb2a.0p50.f024` | 11779362–12017449 | 238,088 |
| perturbation 2 / `gep02.t00z.pgrb2a.0p50.f024` | 11579762–11817516 | 237,755 |

All three returned **206**, matching `Content-Range`, exact bytes, GRIB framing and one complete message. Parent sizes were 15,002,189, 15,203,057 and 15,006,133 bytes; parent bodies were not downloaded. Actual metadata, rather than inventory labels, establishes acceptance. Inputs remain immutable outside Git.

| Portable input label | Bytes | SHA-256 |
|---|---:|---|
| control | 237,105 | `6ad704158ed29f984fdc2f0dbbbe132fbe06b519b2e2a4396b0ec2dc9265634e` |
| perturbed01 | 238,088 | `da8c47f8801fda48fbcdfa31d03eeb44ed4caa10562698e9ea5e04252d4ac20a` |
| perturbed02 | 237,755 | `beb60bd3efbb3eb0d6af527907c25d05d1b7ed4d5e462ba39a8130614d332813` |

**Encoded common metadata:** GRIB2, centre7/subcentre2, operational status0, ensemble generating process4/process107, master table2/local1, discipline/category/number **0/0/0** (temperature), fixed surface103 / scaled value2 / scale0 (height above model ground), no second surface255, native `K`. ecCodes friendly ID167/`2t` is supplementary. PDT1 provides instantaneous +24 h with the reference and validity above.

Encoded member octets: **[1,0,30], [3,1,30], [3,2,30]**. GDAL independently exposes the same complete template octets and control/perturbed forecast status. Member0 is an actual encoded low-resolution control, not deterministic GFS relabelled. Perturbations1/2 have positive type under this system; universal cross-provider numbering is not assumed.

### Rights and access classification

| Pathway | Finding under accessed product notice |
|---|---|
| Public documentation, inventories and range extraction | **Documented permissible / demonstrated anonymous access**; no credentials, fees or agreements |
| Local research storage, decoding, transformations and derived receipts | **Documented permissible under stated conditions**; NOAA attribution/modified-research qualification retained |
| Redistribution / commercial or offline raw packaging | NOAA notice permits broad use with stated conditions; future delivery/service/third-party/product-specific review still required; **no commercial legal clearance or production pathway selected** |
| Archive continuity, exact suite history, quotas/long-term service promise | **UNRESOLVED**; retrieval proves these objects only |

Committed samples/receipts are modified Meridian research derived from NOAA GEFS, not unaltered NOAA products; NOAA endorsement is not implied. Data licence and hosted-service availability are separate.

## 4. Geometry, numerical integrity and conformance

**VALIDATED:** all three section-3 byte hashes are `45f032582fad6270b54ba8c883ccfcd67e7b7297d80f487ee0ad52a8d975f9ab`. GDT0 `regular_ll`: **720 × 361 = 259,920 nodes**, 0.5° spacing, north90→south−90, longitude0→359.5, scan0 (i increasing, j decreasing, i consecutive), sphere6/radius6,371,229 m. Both poles, no duplicate longitude endpoint. GDAL pixel-centre transform `(.5,0,−.25,0,−.5,90.25)` agrees with nodes. Delivered grid is not computational model geometry.

This differs from WR007/WR008's 1440 × 721 grid. Shared coordinate/provenance/method concepts apply; WR008's grid-specific implementation is not reused unchanged. Five exact native nodes are checked, with no new interpolation/global service claim.

Packing: DRT3, complex spatial differencing order2, bitsPerValue12, E0/D2. Bitmap absent, missing-value management0, missing0. Decoder `missingValue=9999` is not assumed to occur; all 259,920 values per member are finite. Native Kelvin is retained.

Primary: **ecCodes2.48.0**, Python3.12.6, NumPy2.5.2. Independent: **GDAL3.9.3 GRIB driver/degrib/g2clib**, rasterio1.4.3, Python3.12.6, NumPy2.5.3. Separate GRIB numerical implementations, not ecCodes wrappers; no CCSDS/libaec needed for this packing. Actual independent parameter, units, member-template octets, coordinates and time precede cell comparison.

| Member | Native range K | Bit-identical cells | Max absolute difference K | Mean absolute difference K |
|---|---|---:|---:|---:|
| control | 228.872460937500–311.442460937500 | 10,329 | 2.19726562705e-05 | 8.25439199582e-06 |
| perturbed01 | 229.117031250000–312.107031250000 | 10,411 | 2.19726562705e-05 | 8.23452128582e-06 |
| perturbed02 | 228.168046875000–311.338046875000 | 10,218 | 2.19726562705e-05 | 8.22799790689e-06 |

**259,920 cells compared per member; 779,760 total.** Masks agree. All 779,760 independently decoded cells exactly match the declared g2clib binary32 profile and meet per-cell bounds. Largest derived bound **0.000032000550179 K**. Sources/decoded arrays unchanged; genuine double replay yields identical scientific receipt bytes. Numerical integrity is separate from meteorological accuracy.

| Requirement | Evidence grade |
|---|---|
| Same system/product, reference, lead/validity | **Verified**, actual centre/process/PDT/time plus source mapping |
| Same quantity, authority/table context, native K | **Verified** |
| Same 2 m model-ground height / instantaneous support | **Verified** |
| Identical encoded grid, coordinate order, finite/no-bitmap profile | **Verified**, sections/coordinates/independent comparison |
| Distinct member identities | **Verified**, actual PDT octets/keys |
| Control / positive-perturbation roles | **Verified through explicit provider/code-table mapping** |
| Equal encoded count30 | **Verified** |
| Encoded30 to documented31 / obsolete registry21 mapping | **Unresolved**, not overwritten |
| Complete population, operational weights, calibrated distribution | **Not tested** |

## 5. Preregistered selected-subset arithmetic

Frozen exact native nodes were selected before temperature values. Terrain labels are fixture context, not local terrain/atmospheric-resolution evidence. Member order: **control, positive1, positive2**. Arithmetic uses unrounded accepted values; only table display is shortened. Exact values are in the [combined integrity/conformance/statistics receipt](../../../scripts/weather-research/wr014/integrity-receipt.json).

| Native location (latitude, longitude 0–360) | Member values K | Selected-subset mean K | Selected-subset range K | Selected-subset population SD K |
|---|---|---:|---:|---:|
| Highland-native (56.5, 355.0) | 277.242460938, 277.287031250, 275.918046875 | 276.815846354 | 1.368984375 | 0.635100809 |
| Alpine-native (46.0, 8.0) | 266.782460937, 268.227031250, 266.038046875 | 267.015846354 | 2.188984375 | 0.908759122 |
| Southern-native (-33.5, 18.5) | 286.002460938, 285.547031250, 284.468046875 | 285.339179688 | 1.534414062 | 0.643432635 |
| antimeridian-native (0.0, 179.5) | 300.012460938, 300.097031250, 300.168046875 | 300.092513021 | 0.155585938 | 0.063597991 |
| near-polar-native (89.5, 0.0) | 251.182460937, 251.087031250, 250.658046875 | 250.975846354 | 0.524414062 | 0.228070293 |

These are **three selected members only**, equally weighted descriptive arithmetic. They are not operational ensemble mean/spread, event probabilities, confidence bounds, percentiles, calibrated uncertainty, reliability, safety recommendations or skill. No selection changed after values.

## 6. Candidate contract refinement and exclusions

Research refinement, **not a production API**:

1. Retain common field identity, source/run, parameter authority/native unit, vertical/temporal support, geometry, encoding, missingness and verification/provenance.
2. Explicit ensemble-membership discriminant: key scoped by **producing system/product/run/support + encoded member identifier/type + mapping authority**. A number or deterministic lineage alone is inadequate; unknown membership never fabricates control0.
3. Preserve raw count metadata, documented population, actual selected identities/cardinality and unresolved mapping separately. Selected cardinality cannot create complete-population size/weights.
4. Selected-subset result names its members, validated common support, arithmetic/weighting, source seals and **selected-subset-only** scope. Complete products require separate coverage/weight/calibration evidence.
5. Geometry remains grid-specific; this delivery differs from prior sources. Results carry numerical rounding evidence. Model-ground height is not actual terrain height.

**Preserved/verified:** identity, support, units, geometry, integrity, selected identities. **Explicit mapping:** GEFS process/roles. **Justified refinement:** scoped member and raw/documented/selected population distinctions. **Unsupported/not tested:** other types, multimodel/lagged ensembles, unequal weights, missing-cell ensembles, interval/member combinations, complete distributions/calibration, offline ensemble packaging. WR013's deterministic reader still rejects ensembles; historical apparatus/contract/evidence unchanged.

## 7. Reproduction, tests, resources and preservation

[Instructions](../../../scripts/weather-research/wr014/README.md) replay pinned local inputs using two existing environments. No installation, acquisition client, production integration or dependency framework. Raw files outside Git. GDAL interpreter mandatory; absent independent path cannot become a passing result.

**37 focused tests:** 36 explicitly synthetic mismatch/invalid/probability invariants and one genuine three-member full-grid **double replay** comparing identical receipt bytes to the committed result, no skips. Initial synthetic fixtures lacked required producer/table fields; they were completed explicitly without changing real metadata or acceptance.

Opted-in regressions: WR00730, WR00837, WR00949, WR01025, WR01134, WR01236, WR01343 (**254 tests**), with actual raw-input paths. Publication7, **37/37 documentation/evidence checks and 466 internal links/anchors**, lint, TypeScript and application-only build passed. Existing NumPy deprecation and large-chunk build warnings do not imply scientific failures or trigger installs.

Preflight **33 preservation checks** passed. Final **48/48 preservation safeguards** verify **42 Atlas statuses, 113 hashes, 40,842 Weather publication files (1,275,692,110 bytes)**, accepted fixtures/projections/native inputs and WR007–WR013 raw/pins/receipts. All 1,272 existing tracked baseline files outside seven append-only notes remain unchanged. Production contracts/code untouched; raw/generated arrays outside Git. Unrelated full scientific replay/data-materialising builds omitted because no shared production science changed.

Controlled acquisition **12 requests /931,091 response-body bytes**: raw **712,948B** + documentation/index **218,143B**. No retries/credentials/full bodies/other fields or runs. Exact HTTP/timestamps/seals in pins. Local decoding adds no retrievals. Git and HTTP/TLS/header overhead are **unmetered**; publication tests use loopback fixtures. No claim of zero or fully metered total network activity.

Each run decodes three messages with ecCodes and three with GDAL, sequentially. Maximum sequential temporary files **2,341,338B**, removed. Final-run peak working set primary **119,664,640B**, largest GDAL child **68,665,344B**: per-process peaks, not concurrent RAM/scratch. Private/pagefile counts separate. Owned persistent footprint after validation: **3,452,241B** across 54 files, before the small inventory receipt and subsequent Git/diff logs; conservative **60MB** allowance for regression/build transients remains below **150MB** scratch. No existing external data-directory changes; only new owned WR014 acquisitions/outputs.

## 8. Programme reassessment and exactly one next task

**MODEL-GROUND AND REAL-TERRAIN SUPPORT MISMATCH PILOT — NOT BEGUN.**

- **Objective:** examine an accepted forecast grid's model-ground elevation relative to accepted Atlas terrain at frozen coordinates, preserving supports/uncertainty without temperature correction/skill claims.
- **Evidence:** one authoritative orography field matching a previously accepted deterministic forecast grid/profile, actual units/datum/geometry, independent decoding where feasible; immutable accepted Atlas terrain with its own height/reference evidence.
- **Scope:** one provider/grid, at most one new orography message, up to five preregistered coordinates within verified accepted Atlas coverage, including mountain and contrasting terrain where available. Numerical support/coordinate/elevation comparisons only; no new terrain acquisition, lapse rates, downscaling, observations, ensemble probabilities or application implementation.
- **Dependencies:** lawful bounded access, precise orography/temperature-grid relationship and existing Atlas sampling evidence; no WR006 reopening.
- **Acceptance:** reproduce seals/geometry/heights; separate model node/terrain support, datum uncertainty and legitimate comparison from unsupported atmospheric inference; reject incompatible geometry/reference.
- **Resource boundaries:** at most20 controlled requests/50MB transfer/150MB scratch/five coordinates, existing tools, no installs/paid services/production changes.
- **Stop:** one reproducible support comparison or precise source/geometry/datum blocker; no Weather downscaling or first integrated Atlas implementation.

Terrain-first interpretation adds more information than another full-population-count/subset-arithmetic refinement. Global/regional, ensembles, other quantities, mountains, observations/nowcasting, ML, verification, offline delivery, provenance and sustainable costs remain open. GEFS/GFS/IFS remain candidates. Weather integrity does not close the first integrated Atlas application's architecture/device/preservation/delivery prerequisites; accepted gates remain unchanged. No next task has begun.
