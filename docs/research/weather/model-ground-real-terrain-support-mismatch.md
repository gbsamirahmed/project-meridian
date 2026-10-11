# WR015 — Model-ground and real-terrain support mismatch

11 October 2026. Starting public main/origin checkpoint `e368a020c8a1f84bcd597cd57ba255b4b54193a2`, clean, divergence 0/0. **Outcome B — PARTIAL SUPPORT COMPARISON.** Genuine, matched GFS surface geopotential height and five retained Swiss DTM cells were numerically inspected and reproduced. Horizontal sampling is qualified and explicit. A scientific elevation mismatch is **BLOCKED**: no established vertical transformation connects this GFS quantity/reference to LN02. Both heights are retained; every signed/absolute difference is null. Neither a large nor small apparent separation establishes atmospheric accuracy.

[Utility and reproduction](../../../scripts/weather-research/wr015/README.md), [pins, original freeze and prospective amendment](../../../scripts/weather-research/wr015/input-pins.json), [combined model/terrain/location receipt](../../../scripts/weather-research/wr015/integrity-receipt.json). Historical WR007–014 and Atlas conclusions remain unchanged. No WR016 has begun.

## 1. Evidence selection, scope and prospective rules

Read the complete WR007–014 reports/utilities/pins/receipts and relevant Weather/Foundations records, accepted Atlas terrain qualifications, research state and portability/CRS handoff. Local recursive discovery inventoried 138,971 external paths without processing unrelated large fields; no candidate GRIB/orography input was found there. Earlier accepted raw forecast inputs remain in their existing research locations outside Git. Nothing was moved, renamed or reorganised.

Select **one NOAA/NCEP GFS 2025-01-15 00 UTC pgrb2 0.25° f024 product**, valid 2025-01-16 00 UTC, matching [WR007](historical-gfs-temperature-field-pilot.md). Its retained authoritative inventory lists message562 `HGT:surface:24 hour fcst`. This is not an independently sourced static-orography substitute. Product match requires actual parameter/producer/time metadata, identical encoded grid and the original parent-object identity.

Select **one swissALTI3D 2024 / 2024-2 Valais DTM source**, already qualified in the [accepted Atlas support report](../../atlas/riffelhorn-swiss-support-product.md). The Welsh Tryfan candidate has an unresolved accepted vertical datum; do not promote earlier labels to resolved evidence. Swiss selection offers explicit LV95/LN02 support without new terrain acquisition.

Five unchanged accepted Atlas benchmark/camera coordinates were fixed before heights: centre, north, south, west and east. Their terrain labels are selection context, not newly verified summit/valley classifications. Profile frozen **08:21:08 UTC**, SHA-256 `c7d53f2dbfbbe172972d0b3076ea6bba3d3adb773c782c27b9082149c9a46bb0`. GFS payload retrieval began 08:24:27 UTC. No location was changed after results.

Metadata-only inspection then found **E4/D2** packing rather than the initially anticipated E0/D2 comparison profile, and ecCodes' unit alias `m` rather than NCEP's `gpm`. A **prospective amendment at 08:25:27 UTC**, before numerical extraction/comparison, extends the existing binary32 rounding analysis for the encoded scale and preserves both unit labels. The original profile’s fields and checksum are retained, with the amendment separately recorded. This changes the decoder diagnostic, not the physical target, vertical gate or tolerances fitted to differences.

Declared sign: **model-ground height minus Atlas terrain height**. No scientific subtraction, exploratory subtraction, lapse rate or vertical conversion occurs when quantity/reference equivalence is unresolved.

## 2. Exact source and model-ground interpretation

**OBSERVED:** authoritative [NOAA archival object](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024), narrow inclusive range **407176421–407668863**, 492,443 bytes; HTTP206, matching Content-Range total **537,858,357** and parent ETag `e9f55c2f3f45d6cdb3aac9e4b7a36aba` from WR007. Raw SHA-256 **`867da86f7971c8123bd799a90eb5bec0bd9c2ca751452067b7319ef9adec394f`**. GRIB2 framing, length and terminator checked. Exact original inventory SHA `fa11be72ab29ea43520dc6a6fc8de81bd8e0e024c96da94ed05495bc43b39dcb` is retained; an inventory line alone was not treated as decoded evidence.

**VALIDATED delivered-profile match:** centre7/subcentre0, generating-process96, identical reference/step/validity, same parent object and byte-identical section3 grid as the pinned 874,115-byte WR007 temperature input. Its original SHA `0b95fc06fe9ca08de57f9c5089b8fcd5d7b6a42977b35f669da65ec0f43f40e4` passes again. Exact historical suite/executable and internal orography generation are **UNRESOLVED**. Cross-run/lead static behaviour is **NOT TESTED**; this is one delivered surface-height field, not validation of a universal static terrain collection.

Actual WMO discipline/category/number **0/3/5**, master table2/local table1, surface code1, PDT4.0, instantaneous +24h. [NCEP parameter table](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-2-0-3.shtml), accessed 11 October 2026, calls it **geopotential height, gpm**; parameter4 is geopotential, m²/s². ecCodes calls parameter5 `Orography`/`orog` with unit `m`; independent GDAL identifies `HGT`/[gpm]/surface. Preserve this explicit mapping and code authority. It does **not** establish geometric terrain height or LN02. This already-height quantity is not divided by gravity; no geopotential-to-geometric conversion is performed.

The [official product catalogue](https://www.nco.ncep.noaa.gov/pmb/products/gfs/) was inspected, but the attempted specific f024 HTML product page returned404. That failed documentation request is counted and retained; it is not evidence that the independently retrieved archive object is absent. [NOAA dissemination access notice](https://registry.opendata.aws/noaa-gfs-bdp-pds/) is reused from WR007, checked there on10 October2026. Anonymous bounded range access was demonstrated. No account, agreement, payment or credential used. Catalogue openness/one retrieval does not certify future archive continuity, unrestricted service access, every transformed commercial use or legal clearance.

## 3. Numerical and horizontal support

Actual delivery geometry: **1440×721 /1,038,240 nodes**, regular longitude/latitude, 0.25° spacing, north-to-south90…−90, west-to-east0…359.75, scan0, spherical Earth code6/radius6,371,229m, no duplicate360° endpoint. This is the delivered grid, not the FV3 computational mesh or a verified grid-cell mean. Longitude periodicity and WR008's qualified polar/invalid-query rules remain unchanged.

Primary ecCodes **2.48.0** and independent GDAL **3.9.3 /degrib/g2clib** agree under the predeclared analytic two-rounded-operation binary32 bound and **exact predicted g2clib arithmetic for every cell**. Same-cell alignment established from GDAL transform, sphere and dimensions before comparison. **1,038,240 finite cells, zero bitmap/internal missing cells; 15,295 exact equalities**. Maximum absolute difference **0.0003515625003274181**, mean **0.000010345554992646233** native height units; largest analytic bound **0.0006889141992848537**. No fitted tolerance or silent clamping. DRT5.3/order2, reference−35514.0625, binary scale4, decimal scale2; encoded increment0.16 height units. Float64 primary range **−355.140625…5917.819375**, mean380.32041383495147. Negative model heights are retained, not automatically invalidated. Independent agreement establishes unpacking integrity, not terrain or forecast accuracy.

Atlas source identity `b24a4fdc7b378ba79d442d0ce216a031dfb95a6bc6eed5ad9c33be61175651f4`: retained 100km² source support LV95 **[2620000,1087000,2630000,1097000]**. Only five native 2000×2000 float32 TIFFs are opened, **one 0.5m cell each**, with original bytes/SHA verified before and after. No rendering tile, mosaic, source copy or terrain aggregation is created. Heights in metres, **LN02 /EPSG:5728**, horizontal **EPSG:2056**, declared nodata−9999; five sampled cells valid. A fine DTM cell is not a model grid-node height, cell mean or effective NWP support.

Nearest terrain centre uses **east/south exact-tie** and half-open cells: left≤E<right; bottom<N≤top. Frozen coordinates on raster boundaries therefore select the named south/east cell, not an adjacent tile silently. Native sampled centres are E+0.25,N−0.25m; exact source paths, footprints, indices and hashes appear in receipts. Catalogue2024 denotes a release, not every pixel's survey date. Accepted 2021/2022 LiDAR and2023 photogrammetry qualifications, dated snow/ice/glacier surfaces and varying accuracy remain. No universal numerical terrain uncertainty is invented. Source is a DTM without vegetation/buildings, not an unqualified bare-rock model beneath all ice. Retained [swisstopo product](https://www.swisstopo.admin.ch/en/height-model-swissalti3d) and [OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices), originally accessed3 October2026, permit processing/redistribution including commercial use with **©swisstopo** credit; WR015 reuses that accepted evidence without new download or legal clearance.

Accepted **PROJ9.5.1 /pyproj3.7.2 XY-only** LV95→longitude-first CRS84 operation is pinned and recorded in full. Network disabled, no elevation argument/transformation. Native C binding and pyproj interface agree exactly for five coordinate pairs; they share PROJ and are **not independent CRS algorithms**. Geographic labels query the actual spherical GFS grid; no exact three-dimensional equivalence between the model sphere and survey reference is claimed. No unprovided vertical grid was fetched.

## 4. Frozen location results and vertical decision

Numbers below are display-rounded only; full precision, contributing model nodes/weights and terrain support in the receipt. Coordinates latitude,longitude are derived from frozen LV95 E,N. **GFS quantity is geopotential height (gpm authority, ecCodes m alias); Atlas is LN02 metres.** The columns are deliberately not subtracted.

| Location | LV95 E,N | Derived latitude,longitude | GFS nearest native height | GFS bilinear height | Native DTM LN02 m | Signed/absolute difference |
|---|---|---|---:|---:|---:|---|
| benchmark-centre | 2625000, 1092000 | 45.979107939, 7.761213293 | 2845.339375 | 2734.616398 | 2587.482910 | WITHHELD |
| north-support | 2625000, 1094800 | 46.004294926, 7.761361592 | 2845.339375 | 2806.195040 | 2272.895752 | WITHHELD |
| south-support | 2625000, 1089200 | 45.953921028, 7.761065130 | 2845.339375 | 2631.175966 | 2941.132812 | WITHHELD |
| west-support | 2622200, 1092000 | 45.979205480, 7.725086450 | 2845.339375 | 2748.119343 | 2644.354248 | WITHHELD |
| east-support | 2627800, 1092000 | 45.978998792, 7.797340001 | 2845.339375 | 2658.590449 | 2703.971436 | WITHHELD |

All nearest queries select **row176/column31, 46°N/7.75°E**: no claim of five independent model cells. Bilinear queries use four actual native nodes with finite weights summing to one, preserving WR008 arithmetic through an explicit height-label adapter; no Kelvin interpretation or numerical conversion. Bilinear orography is a sampled representation of the coarse field, not more resolved topography or an atmospheric correction.

**UNRESOLVED for all five:** NCEP's parameter identity and grid sphere do not establish an exact GFS height datum/reference compatible with national LN02, nor a justified geopotential/geometric/national-height transformation. Atlas's accepted horizontal operation deliberately leaves LN02 numbers unchanged. No uncertainty bound for the missing bridge is available. Every accepted signed/absolute difference remains **null**. Horizontal support is also explicitly unequal; no model-cell terrain mean was estimated. Neither approximate equality of metre labels nor known coordinate transformations resolves these problems. This partial result establishes genuine heights and support differences, not a quantified scientifically comparable elevation mismatch.

## 5. Near-surface interpretation and candidate contract

The accepted GFS 2m quantity is diagnosed above its represented ground, rather than 2m above the sampled real DTM cell. WR011 IFS and WR014 GEFS near-surface semantics require the same qualification; **their orography relationship is not numerically tested here**. A queried summit/valley is not thereby resolved; no lapse-rate correction, downscaling, terrain-adjusted temperature, observed error, model ranking or safety suitability follows.

| Candidate requirement | WR015 evidence classification |
|---|---|
| Separate producer/product/run/parameter/grid identities | VERIFIED for this delivered GFS HGT/WR007 match |
| Authoritative height quantity versus decoder unit alias | VERIFIED WITH EXPLICIT MAPPING; no unit/datum harmonisation |
| Independent terrain identity, CRS, LN02, native support/epoch | VERIFIED within accepted Atlas qualifications and five actual cells |
| XY transformation and sampling provenance | VERIFIED WITH EXPLICIT TRANSFORMATION, horizontal only |
| Model internal cell mean/static generation/history | UNRESOLVED /NOT TESTED |
| Exact common vertical reference or bridge | UNRESOLVED; comparison blocked |
| Relationship record with eligible/blocked result | REQUIRES JUSTIFIED REFINEMENT: explicit comparability gate and null difference |
| Temperature correction, forecast skill or universal terrain-weather schema | UNSUPPORTED |

Minimal research refinement: keep **model-ground support** and **independent terrain support** separately scoped by quantity/reference/source/grid; attach coordinate/sampling operations, datum authority, known uncertainty or explicit unknown, comparison eligibility and sign convention. Missing equivalence is a result, not a plausible-looking number. A blocked comparison does not invalidate source decoding or the independent scientific contracts. This is not a production schema, correction pipeline, architecture or provider decision.

## 6. Reproduction, validation and resources

The isolated utility reads pinned local inputs, enforces producer/parameter/time/grid/object checks, independently decodes, samples five cells, records explicit vertical rejection and deterministic receipt bytes. **35 focused tests:**34 synthetic scientific rejection/invariant cases and one genuine complete-grid/five-cell replay equal to the committed receipt. WR007–014 regressions **30/37/49/25/34/36/43/37 =291 tests**, genuine opt-ins, no final skips. Accepted Atlas tests: four source-support tests and four native CRS/geometry operation tests; the first CRS invocation lacked Shapely in the primary environment, so the successful final run uses the existing Atlas environment. No install or assertion relaxation. Publication7, lint, TypeScript and application-only build passed. Existing NumPy deprecation/large-chunk build warnings retained. Full unrelated scientific replays, broad envelope replay and data-materialising builds omitted because no shared production scientific code changed.

Preflight **33/33 preservation checks** passed. Final documentation/link/evidence and preservation totals are recorded in the development log after validation. Preserve all42 canonical Atlas statuses/113 protected hashes/40,842 Weather publication files, accepted projections/native inputs and WR007–014 evidence; no source edits or external-root changes. New code/pins/receipt/report only, with seven append-only navigation/history updates.

Controlled retrieval: **4 attempts /586,437 response-body bytes**, comprising **492,443B one GRIB message +93,994B documentation**; one404 included with0body bytes read. No retry, whole product, new run, terrain acquisition, package install or paid service. Git/HTTP/TLS/protocol/host traffic is **unmetered**; publication tests use loopback. No claim of fully metered total network activity.

Final genuine-run peak working sets: primary **226,508,800B**, independent process **89,591,808B**, separate lifetime peaks rather than simultaneous RAM or scratch. Pagefile/private commit counts are not scientific files. Maximum sequential temporary decoding files **9,346,045B**, removed; no source copies. Owned scratch inventory plus conservative60MB regression/build allowance is recorded at final audit, below150MB. The scratch ceiling is not a process-RAM ceiling or continuous filesystem monitor. Scientific raw inputs/results remain outside Git; small attributed metadata/numerical receipts only are committed.

## 7. Programme decision and exactly one next task

**SCIENTIFIC-TO-APPLICATION ROADMAP DECISION CHECKPOINT — NOT BEGUN.**

- **Objective:** decide which accepted Atlas foundations can support a minimal first application, which Weather scientific gaps genuinely block a proposed integration, and which can continue independently.
- **Required evidence:** accepted Atlas portability/architecture/preservation/device/delivery gates; WR007–015 finite results, WR006 reference blockers, rights/provenance/terrain-support limits; Foundations product, economics, privacy and parity requirements.
- **Scope:** one finite documentary decision matrix and justified next priority. Distinguish optional scientific research from necessary integration gates, and identify minimal Atlas application scope without selecting a framework, renderer, database, provider or deployment solution prematurely.
- **Dependencies:** immutable accepted reports and actual gate statuses; no invented device, performance, skill or commercial clearance.
- **Acceptance:** explicit accepted/proposed/blocked distinctions, rationale for the immediate priority, preservation obligations and one subsequently bounded action with its evidence gates. Weather terrain correction/accuracy stays blocked; numerical Weather experiments may proceed independently where justified.
- **Resources:** retained evidence only, no new scientific acquisition, installs, cloud, paid services or physical-device work; no more than150MB owned scratch if tooling is needed.
- **Stop:** deliver the roadmap checkpoint decision; do not start application construction, another datum research chain, correction experiment or subsequent task.

Remaining Weather tracks include global/regional systems, ensembles/calibration, other physical quantities, mountains, observations/nowcasting, verification, ML, provenance, offline delivery and sustainable public operation. WR015 does not make every unresolved Weather question a prerequisite for the minimal Atlas application. Reassess priorities deliberately instead of automatically extending orography research. No next-task preparation begins here.
