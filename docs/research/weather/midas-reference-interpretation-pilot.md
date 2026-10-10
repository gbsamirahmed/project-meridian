# WR005: MIDAS Open reference interpretation and error-blind eligibility pilot

**10 October 2026.** Public `gbsamirahmed/project-meridian`, main, starting checkpoint
`ce7c9f08bca0ee8c0dc090ab38f519f67abd7677`. Clean working tree and fetched origin/main
matched this commit at 0/0 before changes. [WR001–004](README.md), particularly
[WR004](reference-metadata-and-historical-product-closure.md), [temperature semantics](temperature-semantics.md),
[verification protocol](temperature-verification-protocol.md), [acquisition gates](temperature-acquisition-gates.md),
[compatibility](forecast-reference-compatibility.md), [programme](research-programme.md),
[Foundations engineering](../../foundations/engineering.md), [economics](../../foundations/economics.md)
and [data-layout history](../../phase-4-migration-inventory.md) supply the retained boundaries.

## Executive decision: OUTCOME B — PARTIAL INTERPRETATION

**Real supplied metadata were successfully inspected and reproducibly joined;
an interpretable historical temperature station-era was not established.** The
station CSV contains **1,544 rows / 1,544 distinct source IDs**. **390** first/last-year
ranges nominate 2025 for further investigation. The actual change log lists **692**
new 2025 annual filenames: **302 qcv-0 and 390 qcv-1**, representing **390 source IDs**.
Their county, source ID and station filename agree with the metadata; the qcv-1
source-ID set equals the 2025 year-range nominations.

This improves WR004's listing-only evidence to **inspected metadata contents**.
It does not establish annual-object presence, continuous January reporting, passed
temperature QC, historical location, instrument height, measurement time or exposure.
**Zero station-eras are established as strictly eligible from these inputs; none
was selected and zero annual observation files were opened.** This is insufficient
evidence, not proof that no suitable station exists or a meteorological negative result.

No observation magnitudes or forecast fields were inspected, no errors computed,
no provider selected and no scientific readiness claimed. The conditional annual
file branch stopped at its scientific gate rather than exploiting lawful access
alone. A GFS-only and a paired GFS/UKV reference comparison still share this reference
problem; a UKV issue does not prevent independent global research.

Evidence labels: **CONFIRMED** = inspected stated bytes/metadata; **PARTIALLY CONFIRMED**
= incomplete evidence chain; **INFERRED** = proposed method; **UNRESOLVED** = missing
evidence; **CONTRADICTED** = an assumption contradicted by inspected evidence.
Synthetic tests, documentary interpretation and real metadata results are separate.

## 1. Discovery, immutable inputs and provenance

Recursive filename discovery across the authorised data root located exactly the
three supplied MIDAS files. Edition/header inspection distinguished them from other
202607 geographical inputs. No additional MIDAS edition, capability file, dictionary,
station history or annual observation file was found. SHA256 identities distinguish
the three different contents; no identical duplicate MIDAS copy was found.

Their actual directory, relative to the documented data root, is
`research-inputs/weather/weather/midas-open/v202607/`. The repeated `weather` segment
was accepted rather than treated as missing data. **No directory or file was moved,
copied, overwritten or deleted in the data root.** There was no need to migrate source
files to execute this bounded task; configurable input location avoids new dependencies
on the duplicated spelling. Organisation permission remains optional, not a mandate
for a wider migration. The original directory remains the reproduction location.

| Original file | Bytes | SHA256 |
|---|---:|---|
| `00README_catalogue_and_licence.txt` | 843 | `bbdaa4ca60d0d9c2a261ab1b72df814c2e3bbf57cf2c4715283b03400f028737` |
| `midas-open_uk-hourly-weather-obs_dv-202607_station-metadata.csv` | 134,123 | `3c98d20c4b9a8aba3270280c8692b72a54d66df05d178c5fed27eb70e6fd3acc` |
| `midas-open_uk-hourly-weather-obs_dv-202607_change_log.txt` | 73,638 | `5ee2036336d7c36e7aeb7142d6be0f1e08f3bec7e658de2bc598688898e0c26c` |

**208,604 input bytes** remain in place. Identity is pinned in
[input-pins.json](../../../scripts/weather-research/wr005/input-pins.json).
Acquisition status: manually supplied local files. The actual download session,
date and authenticated access terms were not captured by Codex. Source identity is
supported by the README's exact title/catalogue link and the CSV release header;
hashes pin these copies, not a verified publisher signature or provider checksum.

The README identifies **MIDAS Open: UK hourly weather observation data, v202607**,
the [exact CEDA catalogue](https://catalogue.ceda.ac.uk/uuid/d04207b551674c07801b7d4e6d883e50/),
completed status, registered CEDA access, OGL v3 and mandatory catalogue citation.
The CSV declares `collection_version_number=dataset-version-202607`; `date_valid`,
creation and `last_revised_date` are **13 July 2026**. These are metadata snapshot
dates, not station-era validity. The DOI is bound through the companion README,
not invented as a CSV column. Catalogue publication is **23 July 2026**, distinct
from file creation and local inspection.

Citation: **Met Office (2026): MIDAS Open: UK hourly weather observation data,
v202607. NERC EDS Centre for Environmental Data Analysis, 23 July 2026.
doi:10.5285/d04207b551674c07801b7d4e6d883e50.**

## 2. Actual station metadata schema and scientific limits

The original BADC-CSV declares convention version **1**, Met Office MIDAS database
source and UK land surface observing network. Global/type/column metadata precede
`data`, the ten-column header, 1,544 records and `end data`; no trailing records
were observed. Source IDs retain five-character formatting. All inspected numeric
metadata cells parsed as finite numbers; no blank/NA/NaN tokens occurred in these
numeric columns. This says nothing about temperature missingness.

| Actual column(s) / declaration | What is established | What is not established |
|---|---|---|
| `src_id`, integer; five-character source ID | Unique MIDAS station join key; 1,544 distinct IDs | Reporting-message IDs/capability intervals, instrument cluster or historical era |
| `station_name`, `station_file_name`, `historic_county`, `authority`, char | Names, filename stem, fixed historical county and current authority | County is not modern administrative coverage, mainland membership or exposure classification |
| `station_latitude`, `station_longitude`, float, degrees, WGS84 | Header-defined **currently recorded** station position, rounded to three decimals | January 2025 sensor position/relocation history, exact instrument coordinate or UKV support |
| `station_elevation`, float, m | Header says metres above mean sea level | Sensor height AGL, dated instrument elevation or a named vertical-datum/geoid realisation |
| `first_year`, `last_year`, float with integral values, year | First/last available data in this release and collection | Continuous years, January/February slots, active status, element availability or unchanging equipment |

The header explicitly warns that temporal range can differ between collections,
last year does not establish current operation, and first/last years do not establish
availability between those endpoints. It points to station-folder **capability
files** and the CEDA MIDAS station-search tool for fuller metadata. Those resources
were not supplied or authenticated. The CSV has **no temperature, QC, message,
measurement-height, physical-time, instrument-change or dated-era columns**.

Thus the hypothesis that this CSV alone can establish a historically characterised
thermometer is **CONTRADICTED**. Station elevation cannot supply measurement height.
Current position and release dates cannot silently supply January 2025 history.
The actual 2025 filename join is useful acquisition evidence, not a substitute.

## 3. Release change log and revisions

The inspected log compares **202607 with 202507**, excluding file headers from
the comparison and comparing data rows. It states **52,931 current / 52,236 prior
files**, **52,122 unchanged**, **692 new latest-year**, **3 new historical-year**,
**0 deleted**, **114 modified**. Its accounting is consistent:
`52,122 + 692 + 3 + 114 = 52,931` and `52,122 + 114 = 52,236`.
These counts have the log's scope; the earlier catalogue family total is a different
reported count whose exact reconciliation was not established here.

The utility checks all 692 new-2025 filename identities against their metadata rows.
**All match**; the 390 qcv-1 source IDs equal the 390 year-range nominations. This
does not mean 692 stations or 390 eligible observation series. A listed source file
is not an opened object; qcv-0/qcv-1 denote release states, not temperature quality.
Modified-file entries retain old `dv-202507` filenames as comparison references;
they are not authority to substitute that old edition. File changes do not identify
physical station moves or sensor replacements. Neither per-observation correction
lineage nor a current-value duplicate policy is resolved by this file inventory.

## 4. Timing, height and station-era evidence

The [2021 MIDAS guide](https://zenodo.org/records/7357335), DOI `10.5281/zenodo.7357335`,
was re-read from the WR004 retained documentation, without a new download. Its
2,597,551-byte / 71-page identity remains MD5 `02fe0896273170f69f21eeb04c855445`.
Its internal change table begins at version 1.0, 6 January 2020; publication is
5 July 2021. Documentary rules are not observations of 2025 equipment.

| Rule / source sections | Station-era evidence needed | Support from the supplied files / consequence |
|---|---|---|
| §§3.2, 4.3.5: UTC, 0000 new day; instant versus period-end/count; receipt stamps differ | Source/message clock and actual temperature sample interval | No clock fields; receipt time cannot establish measurement time |
| §4.4.1 SYNOP: stored hour and HH−0…HH−10 local practice, former SIESAWS HH−15; broader guide statement is less specific | Reporting capability, historical equipment and mapping of stored to physical time | UNRESOLVED; no universal ten-minute subtraction or rounding |
| §4.4.3 Mini-MMS AWSHRLY: DCNN/CLBD, HH−10; replacement of former CDL systems | Capability/era and logger identity; historical on-hour CDL rules cannot be assumed current | UNRESOLVED; message name alone is insufficient; CLBD exposure differs |
| §§3.3–3.4: 1.25 m Stevenson-screen/PRT practice; 15-second samples averaged to minute data | Dated station thermometer height, shielding, averaging interval and exposure | NETWORK STANDARD only; no actual historical height assigned, minute average not hourly mean |
| §2.5.7: common station position can mask moved instrument clusters | Dated station and cluster history covering January–2 February 2025 | Current coordinates alone are insufficient; no absence-of-moves inference |

SYNOP/AWSHRLY remain conditionally interpretable **only when their era is evidenced**.
NCM needs temperature-specific lineage; soil/wind/radiation timing does not determine
air-temperature timing. Ordinary daily DLY3208 cannot supply the proposed 00 UTC
cohort. METAR remains outside this Open edition. No actual report was classified
through message metadata in WR005 because none was supplied.

The strict physical-time path remains blocked. A later **nominal-report proxy** could
have value only through an explicit, pre-error estimand revision preserving unknown
offset and short averaging. WR005 does not adopt it. Likewise nominal network height
could qualify a future archive-station proxy, but cannot become observed height.

## 5. QC, missingness and observation revision gate

The current guide §§4.3–5 explains marker/estimate/status/query/level, versioning
and COR overwrites. Query zero can mean no information; level zero means no QC.
Version 1 is assigned on initial ingestion as well as after changes; intermediate
updates need not survive. Consequently version 1 or a `qc-version-1` directory
does not prove that temperature passed checks. The [Open guide](https://help.ceda.ac.uk/article/4982-midas-open-user-guide)
and [WH table](https://artefacts.ceda.ac.uk/badc_datadocs/ukmo-midas/WH_Table.html),
reviewed in WR004, qualify the same distinction; their current pages were not re-fetched.

**No edition-specific temperature/Q/J/state dictionary was supplied.** The metadata
CSV contains no `air_temperature`, `_q`, `_j`, observation-state/version or missing
sentinel declarations. WH documentation is an anticipated observation schema,
not an inspected v202607 annual-file header. MESQL component meanings do not verify
integer packing/order/width. No bit positions, decimal decomposition, `-9999`
sentinel, flag allowlist or correction precedence is implemented.

| Decision class | WR005 implementation / scientific meaning |
|---|---|
| ACCEPT | No real observation acceptance path; requires verified edition/header/dictionary/revision and time/era chain |
| REJECT | Metadata commissioning ID 99999 or year range outside 2025 nomination; parser rejects malformed/changed inputs. These are not rejected temperature measurements |
| REQUIRES REVIEW | Corrected/estimated/status-conflicting observations would need source-qualified, error-blind review; none inspected or counted |
| UNINTERPRETABLE | All 390 nominated IDs lack sufficient historical/time/QC evidence; unknown observation encodings cannot pass |

Temperature QC decoding, missingness and duplicate precedence remain **not executed**.
Synthetic injected QC/time/height columns fail as unsupported metadata schema; this
tests a boundary, not scientific interpretation of real QC integers. Identical or
conflicting duplicate **station IDs** fail explicitly; this is not an annual-record
revision resolver. Such record-level tests must wait for authoritative encoding.

## 6. Error-blind selection and actual receipt

Procedure fixed before observation values: pin three original files; validate exact
product/release/schema; enumerate unique source IDs; reject commissioning identifiers;
use first/last years only to nominate 2025; assess mandatory historical location,
elevation/height/exposure, capability, physical-time/average, QC/revision and planned
valid-time evidence. Require a frozen study domain rather than pretend a rectangle
proves mainland/UKV support. Sort by numeric source ID, then era start if evidenced;
take **at most one eligible station-era**. No substitution after failure.

Actual result: **1,154 IDs do not nominate 2025; 390 are UNINTERPRETABLE for strict
selection; 0 strictly eligible; selected station-era is null.** This counts metadata
eligibility decisions, not temperature QC or observed missingness. Domain/mainland
and future ten-station membership were not claimed. No annual file was selected,
requested or opened; that conditional step had insufficient scientific evidence.

[metadata_pilot.py](../../../scripts/weather-research/wr005/metadata_pilot.py) is isolated,
Python standard-library code. It verifies fixed local hashes before parsing and
again after inspection, exact BADC metadata/unit/CRS/type definitions, finite numbers,
unique IDs, marker/row/header/field limits and filename joins. It neither contacts
providers nor imports the Weather runtime, GIS libraries or forecast code. Source
files remain immutable. It refuses receipt overwrite and output within input folders.
Successful exit 0 means inspection succeeded; the receipt separately states outcome
B and annual gate BLOCKED. Missing/corrupt/unsupported input returns exit 2 and an
explicit failure code, not a valid empty scientific result.

Full source-ID/exclusion receipts remain in owned scratch outside Git, with no
station coordinates/names or observation values. Two repeated **final-version** receipts
are byte-identical: **355,225 bytes**, SHA256
`8eeba7f0f4a60c0fc6c0eb67cdc219d1b6706d2f7c573054209d579e7130a7ab`.
An earlier metadata-only receipt predates the change-log join and is retained locally
as an intermediate result, not substituted for the final receipt.

## 7. Rights, acquisition and resource receipt

The actual supplied README confirms the exact edition's **OGL v3** and catalogue
citation. [OGL v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
was read in WR004: covered copying/adaptation/research/commercial reuse remain subject
to attribution, exclusions and non-endorsement. This supports local metadata research
under documented conditions, not legal clearance for every underlying asset or
future commercial/offline forecast package. Registered access and information reuse
are different questions; no account/session/terms were used or accepted by Codex.
No source payload, authenticated material or raw observation is committed.

| Resource / measured scope | Actual WR005 result / ceiling |
|---|---|
| New MIDAS/scientific/document retrievals, including retries | **0 requests / 0 bytes**; 20 requests / 50 MB ceiling. Required Git upstream synchronisation is separate repository control traffic, not dataset acquisition |
| Local manually supplied inputs | **208,604 bytes**, read in place; **0 copied input bytes** |
| Annual observation files / forecasts | **0 / 0**; annual maximum 1, forecast downloads forbidden |
| Scratch before application check | **1,548,170 bytes** at measurement; includes three final receipts, intermediate receipt, baseline/discovery/preflight files; no source copies |
| Scratch including build/check/diff artefacts | **3,779,798 bytes** at complete-diff review; below **10 MB**, versus 150 MB ceiling. Snapshot inventory, not continuously sampled filesystem high-water |
| Inspection time | Three in-process runs **11.027 / 8.706 / 8.597 ms**, median **8.706 ms**; includes input hash/parse/join/recheck, excludes process launch/receipt write; storage cache not flushed |
| Process peak working set | **24,449,024 bytes**, Windows process counter after three runs; includes interpreter/test-driver imports. Not incremental parser-only memory or annual-file forecast |
| Environment | **Python 3.12.6, Windows 11 build 26200, AMD64**; existing interpreter only; **Node 24.11.0 / npm 11.6.2** for existing checks |

Scratch measurements include preservation/check code and application-only build
artefacts, not just the scientific utility. Synthetic temporary inputs are small
and removed by tests. No full dataset mirror, provider client, new dependency,
paid service, SDK or data-directory migration was used. CPU/memory are desktop
measurements, not device or full Weather resource estimates.

Reproduction commands, limits and error meanings are in the
[utility README](../../../scripts/weather-research/wr005/README.md).
Use the existing interpreter, supplied input directory and a new owned output
outside Git/data; compare repeated receipt SHA256 and the three source hashes.
Neither source nor result needs republishing to repeat inspection.

## 8. Remaining gates and programme implications

| Gate / status | Smallest missing evidence / authoritative route |
|---|---|
| T03 PARTIALLY CONFIRMED | Edition metadata and filenames now inspected; annual body/header/actual slots uninspected. Registered [edition directory](https://data.ceda.ac.uk/badc/ukmo-midas-open/data/uk-hourly-weather-obs/dataset-version-202607/) is the original route; no new edition substituted |
| T04 UNRESOLVED — principal scientific blocker | Lawfully supplied station-folder capability file plus dated instrument/location/height/exposure and temperature-clock/averaging evidence for one deterministically nominated station. CSV points to the CEDA MIDAS station search; a general manual alone cannot fill historical facts |
| T05 UNRESOLVED | Exact v202607 `air_temperature_q` packing/encoding, `air_temperature_j` descriptor, record-state/version/replacement and per-column missing-value dictionaries; authorised links from WH documentation. Component descriptions alone are insufficient |
| T07/T10 BLOCKED | Historical eligibility/domain/completeness and explicit protocol freeze; 390 metadata nominations are not a future paired cohort |
| T01/T02/T06/T08/T09 | Forecast bodies/static support, independence and distribution/resource conditions retain WR004 state; not investigated or acquired here |

No initial supplied file is missing. What the owner would need to provide next is
**historical measurement support**, not another copy of the same station CSV or an
arbitrary annual temperature file. Relevant exact capability/history filenames are
not yet verified; do not invent them. Preserve the edition directory/station-folder
path and provider notice when manually obtaining them, and the dictionary version
when later supplied. No login retries, provider contact or data acquisition is
performed to turn an unknown filename into presumed evidence.

WR005 answers a finite real-metadata question and preserves a negative strict
eligibility receipt. It does not promote W01–W40 into validated capabilities.
Global deterministic, regional enhancement, ensembles, mountain weather, wind/cloud/
precipitation, observations/nowcasting, provenance and offline delivery stay first-class
tracks. Do not postpone all global science for UKV, or replace observations with model
agreement/reanalysis. A nominal-time/network-proxy evaluation would require an explicit
scientific decision before errors, not relaxed flags designed to obtain Outcome A.

## 9. Exactly one subsequent task — NOT BEGUN

**WEATHER RESEARCH 006 — MIDAS HISTORICAL MEASUREMENT SUPPORT AND REFERENCE-TARGET DECISION — NOT BEGUN.**

- **Objective:** determine whether one January–2 February 2025 station-era can be
  historically characterised, or whether the strict reference target must remain
  blocked or be explicitly revised to a qualified archive/nominal-report proxy.
  Historical support is the first failed selection gate in the actual metadata.
- **Required evidence:** WR005 pins/receipt; at most one lawfully supplied station
  capability file and relevant dated location/instrument/height/exposure/temperature
  clock evidence; existing guide and strict WR003 requirements. Metadata missingness
  must remain visible. Do not pretend a capability table alone supplies sensor history.
- **Scope:** freeze a metadata-only audit domain compatible with the proposed UK-mainland
  study, then take the lowest numeric nominated source ID with documented domain
  membership; this is an audit nominee, not an eligible reference. One nominee, no
  replacement; no annual observation magnitudes, forecast download or error calculation.
  Compare strict and explicitly qualified possible targets without adopting either silently.
- **Dependencies:** owner-supplied lawful registered metadata or bounded anonymous
  documentation; no login automation, provider contact or agreement acceptance. Exact
  files must be identified before retrieval. QC dictionaries remain a separate named
  pre-observation gate, not assumed closed by historical support.
- **Acceptance:** source-qualified, dated applicability or a reproducible absence/
  contradiction receipt; explicit keep/revise/stop decision for the reference target,
  with what any proxy could and could not claim. No scientific-readiness/skill result.
- **Resource boundaries:** at most one capability file and its directly relevant
  support documents; ≤20 requests, ≤50 MB transfer, ≤150 MB owned scratch, no paid
  service or bulk acquisition. Reuse WR005 inputs in place.
- **Stops:** unavailable lawful history, ambiguous physical clock/height, unsupported
  era mapping or budget breach. Finish with a specific blocker or target decision;
  do not repeat a broad survey, expand the station set or begin forecast verification.

This is a recommendation only. No WR006 investigation or protocol revision has begun.

## 10. Validation and preservation

Read-only preflight: **33/33 preservation checks passed**. Focused final-version
synthetic tests: **22 passed, 0 failed, 0 skipped**. Real pinned metadata inspection
and repeated final receipt comparison passed. All three original source hashes
remain unchanged; no data-root writes or reorganisation. Existing Weather publication
boundary tests: **7 passed, 0 failed, 0 skipped**, using their synthetic publications.
Repository ESLint and TypeScript build checks passed. An **application-only Vite
build** passed with public copying and the Weather materialisation plugin excluded;
no retained publication was copied or regenerated. Optional-esbuild configuration
bundling notices and large-chunk warnings were emitted; these are not scientific
findings. No production bundle or dependency change is committed.

The initial focused test invocation failed on restricted-host temporary-directory
permissions before substantive checks; rerunning with an explicit owned scratch parent
passed. This was an environment failure, not ignored scientific test success.

Final validation: **31/31 documentation checks** including **27 internal links/anchors**,
and **33/33 full retained preservation checks**, all passed. The exact **13-file**
diff comprises new isolated research code/documentation and eight append-only notes;
all **1,213 existing tracked files** outside those notes remain unchanged. All 42
Atlas canonical rows, 113 protected hashes, 60 frozen cases/
three pins, twelve native prerequisites, accepted stores/publications and original/window
projection seals, 100 Swiss native fingerprints, 11,429 terrain seals and **40,842 Weather
publication hashes** are checked read-only. Historical documents are append-only outside
this new report; scientific contracts, runtime, frontend and legacy Weather code stay
unchanged. No private repository access, credentials, scientific payloads or personal
absolute paths are added to Git.

Full scientific regressions and 60-case replay were deliberately not rerun: the new
utility is isolated, imports no existing runtime and changes no shared scientific
contract or authority. Annual-record QC/missingness/revision/time tests are **not
executable** because their scientific gate was not satisfied; synthetic metadata
tests do not substitute for them. No full Weather/data-materialising build, model
benchmark, mobile experiment or subsequent task was run.
