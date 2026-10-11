# WR012 — independent CCSDS numerical conformance

Evidence collected 10 October 2026; final validation and release 11 October 2026.
Starting main/origin checkpoint:
`47153215c180e8b7997ced2d5a18fa44dc759385`, clean, divergence 0/0.

## 1. Decision and evidence boundary

**Outcome A — VERIFIED INDEPENDENT NUMERICAL CONFORMANCE**, qualified as
**independence B: independent GRIB interpretation with a shared low-level CCSDS
decompressor**. All three preserved [WR011](cross-provider-ifs-field-conformance.md)
IFS messages reproduce ecCodes values exactly across each complete 1,038,240-cell
grid. A separate standard-library Python child interprets sections, temporal and
grid metadata, integer storage and physical scaling; it calls existing libaec
directly and never imports or loads ecCodes. It shares the same libaec DLL with
the primary path, so this does **not** independently verify the entropy algorithm.

This strengthens the finite cross-provider numerical evidence. WR011's historical
**Outcome B** remains unchanged, as do WR006's blocked MIDAS reference decision,
producer-specific parameter mappings, unpaired wind and all earlier results.
No forecast skill, model superiority, production readiness or general decoder
compatibility is established.

## 2. Preserved inputs and rights

Model/product: ECMWF IFS Open Data deterministic `od/oper/fc`, one historical
2025-01-15 00 UTC run, endpoint 2025-01-16 00 UTC. Existing messages only; no new
forecast retrieval, re-encoding or raw copies. Nominal model executable version
remains unknown; generating-process 158 is not an exact executable-version claim.

| WR011 input | Bytes / raw SHA-256 | Parameter, vertical and temporal support | Native unit |
|---|---|---|---|
| temperature.grib2 | 650,860 / `7f7e40c92f5375d4af52f68428c02820105bafa10ad29cf2404ad0c37e7a5f30` | WMO 0/0/0, 2 m above model ground, instantaneous +24 h | K |
| precipitation.grib2 | 886,088 / `bbe7a629c06579c27e64a181d2066ed1b36af14544238728d0eda4442083c884` | ECMWF local 0/1/193, surface without encoded altitude, accumulation +0–24 h | m |
| wind_u.grib2 | 865,918 / `4b153144cdb6623906501ddfcc915e16e1d593ce4f0ef821d4a0d62524ea9cfc` | WMO 0/2/2, 10 m above model ground, instantaneous +24 h; Earth-eastward U only | m/s |

Raw sizes/checksums are verified before native decompression and after reading.
WR011 pins, accepted decoded hashes and full receipt remain byte-identical.
Actual inputs were found at the recorded external WR011 research location, not
inside Git; discovery and pinned evidence required no external-root reorganisation.
Their original authoritative AWS object/ranges, source notices and CC BY4.0
conditions remain [WR011's evidence](cross-provider-ifs-field-conformance.md#2-exact-source-rights-and-predeclaration).
Derived receipts retain ECMWF attribution and no endorsement. No new service
agreement, account, commercial/offline redistribution clearance or legal approval.

## 3. Exact blocker and bounded decoder discovery

**OBSERVED:** installed rasterio 1.4.3 / GDAL 3.9.3 has a GRIB driver and opens the
temperature dataset, inspects raw PDT, geometry and units. `ds.read(1)` then fails:
`g2_unpack7: Data Representation Template 5.42 decoding requires building against libaec.`
Subsequent g2_getfld error 4 / “Out of memory” is a wrapper failure, not evidence
of measured memory exhaustion. The independently implemented GDAL/degrib/g2clib
path therefore still cannot supply numerical arrays in this build. Its actual
native DLL (19,130,368 bytes)/SHA and profile are in the [capability receipt](../../../scripts/weather-research/wr012/decoder-capability-receipt.json).

Limited local PATH/install-directory discovery found no standalone GDAL/wgrib2
executable. Ubuntu's existing libaec0:amd64 1.0.6-1 was identified but not used or
altered. An existing Windows `aec.dll` in the official installed ecCodes 2.48.0
distribution provides the buffer API. No portable package, dependency acquisition,
administrator operation, compilation, installation or environment modification
was needed. This is not a claim that every local scientific installation was searched.

**CONFIRMED:** existing AEC DLL, 31,232 bytes, SHA-256
`99dccaf5fe3e03f1dc47ebefb83fa7772754bfcb5bc002c517fec244b28884a8`,
matching installed distribution RECORD hash/size. Primary loaded-module SHA matches
the reference's explicit DLL pin. ecCodes DLL SHA is also recorded. **UNRESOLVED:**
the AEC binary's upstream version; no version export was available. Upstream
v1.1.3 documents ABI/constants; it is not proof this installed DLL is v1.1.3.
Upstream libaec's BSD-2-Clause licence permits this local use; no binary is committed.

## 4. Preregistered comparison and implementation independence

Comparison frozen 2026-10-10T18:47:40.912479Z, before independent values/differences.
The saved freeze checksum and full method are in [pins](../../../scripts/weather-research/wr012/input-pins.json).
This explicitly replaces the *prospective implementation profile*, not WR011's
historical result: GDAL's float32 scaling rule is irrelevant to this new binary64
path. Require **zero absolute tolerance**, all cells, identical native-unit values,
finite masks and exact little-endian binary64 array hashes. No post-result tolerance change.

Actual template 5.42 encodes R as binary32, D0, E−5/−18/−6 and at most 16-bit integers.
`value = (R + I × 2^E) × 10^-D` is exactly representable for these three profiles
in binary64. The independent reader uses encoded flags 14, requesting big-endian
unsigned16 output with preprocessing; the primary ecCodes implementation adjusts
flags for native little-endian integer storage. Both ultimately use the same AEC
implementation. Status 0, complete compressed-input consumption and exactly 2,076,480
decoded integer bytes are required per field. No arbitrary or unpinned message
reaches the native call; unsupported templates, bitmap, time or scaling fail closed.

Raw Section3 is independently parsed and matches its pinned SHA
`6e8229bf09d191ccf7d719ef88dc9e848fe663cf45a91d0691b7e17815a03036`.
Grid 1440×721, regular latitude/longitude, scan 0, Earth shape 6 / radius 6,371,229 m,
latitudes 90→−90 at 0.25°, longitude origin 180→179.75 periodically, no duplicate
endpoint. Primary actual coordinate arrays agree with this ordering before values
are compared. No array rotation, unit conversion, regridding or interpolation.
The local precipitation name/unit is mapped from retained producer definitions;
this reference is not an independently implemented ECMWF parameter dictionary.

The raw PDT0/PDT8 interpretation preserves reference/validity, level, accumulation
start +0 h / end +24 h, statistical-process 1 and encoded increment 450 s/type 2. The increment
does not become an inferred output frequency or invented internal step count.

## 5. Numerical results and reproducibility

**VALIDATED within the three profiles:** each comparison has 1,038,240 finite cells
per path, zero missing cells, matching masks and 1,038,240 exactly equal cells.

| Field | Packing E / bits / integer range | Max and mean absolute difference | Maximum relative / quantisation-step error |
|---|---|---|---|
| 2 m temperature | −5 / 12 / 0–3045 | 0 K / 0 K | 0 / 0 |
| Surface precipitation | −18 / 16 / 0–54390 | 0 m / 0 m | 0 / 0 |
| 10 m eastward wind | −6 / 12 / 0–3421 | 0 m/s / 0 m/s | 0 / 0 |

No largest disagreement exists. Receipt tie rule records first native cell
(row 0, column 0, 90°N, 180°): respectively 246.3415069580078 K,
0.000087738037109375 m and 4.2238616943359375 m/s, all identical. Relative error is
evaluated only for nonzero primary values; zero-primary disagreements are separately 0.
Encoded quantisation spacing remains 0.03125 K, 0.000003814697265625 m and 0.015625 m/s;
exact decoding agreement does not remove source quantisation or physical uncertainty.

[Numerical receipt](../../../scripts/weather-research/wr012/numerical-comparison-receipt.json)
contains metadata, full-array SHA seals, counts, errors, decompression diagnostics,
versions and utility hashes. Standalone final replay and a genuine double-replay
test reproduce deterministic scientific receipts. Transient timings/memory are
separate. [Utility instructions](../../../scripts/weather-research/wr012/README.md)
use existing optional local DLL/input pins and explicitly fail if absent; no silent
ecCodes fallback. Archive repeat-retrievability was not tested again.

## 6. Contract consequences, validation and resources

| Contract element | WR012 evidence change / limitation |
|---|---|
| Numerical integrity | Strengthened to complete-grid qualified independent agreement; common AEC algorithm remains a dependency |
| Native units / vertical meanings | Unchanged units retained in scaling; local precipitation dictionary authority remains producer-scoped |
| Coordinates / missingness | Native grid/order and no-bitmap finite profile corroborated; other grids/bitmaps remain untested |
| Packing/provenance | Add implementation/dependency SHA, scaling precision and independence degree to evidence; no production schema change |
| Query/skill | No new interpolation, observation verification or skill evidence; WR008/011 query limitations retained |

Focused 36 tests: 35 synthetic rejection/invariant checks, one opted-in **genuine**
three-field double replay, zero skips. WR007–011 regressions 30/37/49/25/34 passed
with local real inputs, publication 7 checks, lint, TypeScript and application-only
build passed. Existing large-chunk build warning remains. No unrelated scientific
replays, full data-materialising builds, production changes or new dependencies.
Preflight 33/33 safeguards passed; final preservation repeats 42 status rows,
113 hashes, 40,842 Weather files, accepted fixtures/projections and all WR007–011
raw inputs/pins/receipts. Documentation links/anchors and complete diff checked.

**12 controlled HTTP attempts, 72,180 body bytes read**, documentation only;
two 404s and one rejected 301 counted, zero error bodies read. Zero forecast or
binary acquisition, zero network in replay code. Git traffic, HTTP/TLS overhead
and incidental OS traffic unmetered: **no certified zero-total-network claim**.
No automated retries, redirects, package-update checks or expanded budget.
Standalone final temporary output ≤8,308,955 bytes, deleted one field at a time.
Primary peak working set 170,106,880 bytes; largest separate reference peak 43,679,744.
Their sum 213,786,624 is a conservative sum of separate lifetime peaks, not measured
simultaneous RAM. Pagefile/commit counters are not scratch writes. Final scratch
inventory and conservative 60 MB transient-test allowance are recorded in the log,
well below 150 MB. No files moved or changed in the external data root.

Authoritative documentation inspected 10 October 2026; exact body hashes/access times
are in the capability receipt: NOAA
[template 5.42](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp5-42.shtml),
[scaling5.0](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp5-0.shtml),
[grid3.0](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp3-0.shtml),
[instant4.0](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp4-0.shtml),
[interval4.8](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp4-8.shtml);
libaec [README v1.1.3](https://raw.githubusercontent.com/MathisRosenhauer/libaec/v1.1.3/README.md),
[ABI header](https://raw.githubusercontent.com/MathisRosenhauer/libaec/v1.1.3/include/libaec.h.in),
[licence](https://raw.githubusercontent.com/MathisRosenhauer/libaec/v1.1.3/LICENSE.txt);
[ecCodes 2.48.0 CCSDS accessor](https://raw.githubusercontent.com/ecmwf/eccodes/2.48.0/src/eccodes/accessor/DataCcsdsPacking.cc).
These are versioned implementation/standard evidence, not forecast-accuracy claims.

## 7. Programme reassessment and exactly one next task — NOT BEGUN

Qualified numerical closure makes another decoder-only task lower information
value than testing how scientific meaning survives bounded offline preparation.
Global/regional, ensembles, mountain representativeness, other quantities,
observations/nowcasting, ML, uncertainty, rights/economics and offline delivery
remain distinct open tracks. No permanent provider, format or architecture selected.

**SCIENTIFIC FIELD-PACKAGING AND OFFLINE QUERY REPLAY PILOT — NOT BEGUN.**

**Objective:** test whether a small offline research subset preserves native
values, geometry, time support and provenance across existing GFS/IFS evidence.
**Evidence/dependencies:** unchanged WR007/WR011 inputs and pins, WR008/WR011 query
rules, WR009/WR011 interval semantics, WR010 candidate contract and WR012 qualified
numerical receipts; retained source rights/attribution review before packaging.
**Scope:** at most three existing fields: GFS temperature, IFS temperature and IFS
precipitation. Freeze one small geographical subset and deterministic in-subset,
boundary and invalid queries before examining results. Use disposable research
representations only; compare original-to-subset values and query receipts,
including different native longitude origins and instant/interval meanings.
**Acceptance:** exact preserved values/masks and metadata, explicit boundary
failures, deterministic replay, measured footprint and immutability; or a precise
loss/boundary/rights blocker. No claim of production offline feasibility from one subset.
**Resources:** zero new forecasts, packages or services, ≤150 MB additional scratch,
no raw public redistribution or existing publication changes.
**Stop:** after this finite preservation/query experiment; no permanent storage
format, tile pipeline, route or application implementation, new provider/field,
MIDAS reopening or forecast skill study. No next-task preparation has begun.
