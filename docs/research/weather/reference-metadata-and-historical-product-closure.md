# WR004: reference measurement metadata and historical temperature product closure

Reviewed **10 October 2026**. Starting checkpoint `492b4b51e7cfdb1da4ced7b9d90798c2669970a1`; public main and fetched origin/main were clean and aligned, with zero divergence. Read [WR001–003](README.md), particularly the [WR003 gates](temperature-acquisition-gates.md), [semantics](temperature-semantics.md) and [conditional protocol](temperature-verification-protocol.md). This report refines their documentary evidence; it does not replace their scientific question or authorise acquisition. Primary sources and retrieval qualifications are recorded in [the WR004 ledger](sources.md#wr004-reference-and-historical-product-evidence).

## Executive decision: OUTCOME B — PARTIAL CLOSURE

**A bounded source-interpretation pilot is defensible, subject to its access, rights and resource preflight. A frozen forecast–reference comparison is not yet defensible.** Public listings confirm two GDEX GFS forecast identifiers and three UKV screen-temperature identifiers, including a January-end +48-hour object. The current MIDAS guide is now readable and explains message/equipment-specific clocks, thermometer practice, QC components and revisions. It does not establish a January 2025 station-era cohort or the exact v202607 CSV flag encoding.

The shared blocker for a GFS-only or paired GFS/UKV reference comparison remains **interpretable observations**: physical time/short averaging, station-era height/history, field-level QC/missingness and actual eligible records. CEDA's station-metadata and change-log downloads redirect to sign-in; those contents were not obtained. Publicly listed files are not publicly verified records. No temperature values, scientific field bodies, model errors, skill results or station eligibility counts were acquired or computed.

This is B rather than A because object existence and general manuals do not freeze the reference or protocol. It is B rather than a requirement to abandon the sources because a finite metadata/header/interpretation check can test the remaining assumptions without model benchmarking. It is conditional feasibility, **not an executable acquisition approval**. If lawful reference metadata cannot be obtained, stop that pilot at a documented prerequisite; do not replace it with another broad survey or an unqualified skill comparison.

Evidence vocabulary: **CONFIRMED** means a specific primary document or non-value listing was read; **PARTIALLY CONFIRMED** means only part of the necessary chain; **INFERRED** identifies our planning/method proposal; **UNRESOLVED** lacks evidence; **CONTRADICTED** records inconsistent claims. Separately distinguish documented capability, observed listing, inspected metadata and verified scientific content. The last category was not reached for any forecast or observation record.

## 1. MIDAS exact edition and accessible evidence

The [CEDA catalogue](https://catalogue.ceda.ac.uk/uuid/d04207b551674c07801b7d4e6d883e50/) identifies **MIDAS Open: UK hourly weather observation data, v202607**, DOI `10.5285/d04207b551674c07801b7d4e6d883e50`, published **23 July 2026**, with family coverage **1875–2025**, BADC-CSV delivery, registered-user access and OGL v3. Air temperature is in °C. The stated extent and catalogue totals describe the family, not continuous records at every station. The selected Open subset excludes METAR; the full MIDAS weather table is not the edition's membership definition.

The [public edition directory](https://data.ceda.ac.uk/badc/ukmo-midas-open/data/uk-hourly-weather-obs/dataset-version-202607/) exposes these identifiers:

| Item | Observed listing / status | What remains unverified |
|---|---|---|
| `00README_catalogue_and_licence.txt` | Listed, 843 bytes; body request redirects to CEDA sign-in | Exact text and any edition-specific notices |
| `midas-open_uk-hourly-weather-obs_dv-202607_station-metadata.csv` | Listed, 131.0 KB as displayed; body redirects to sign-in | Actual station rows, columns, precision, historical validity and eligible count |
| `midas-open_uk-hourly-weather-obs_dv-202607_change_log.txt` | Listed, 71.9 KB as displayed; body redirects to sign-in | Actual amended/removed file inventory |
| `change_log_station_files/` | Listed directory; no station log acquired | Individual file revisions and reasons |

The [Open guide](https://help.ceda.ac.uk/article/4982-midas-open-user-guide), updated 18 July 2025, describes station county/coordinates/altitude and first/last years, annual site files, headers and checksums. Its older coverage example does not override the edition catalogue. First/last years are not a continuous-availability test; current station coordinates are not automatically historical instrument coordinates.

The publicly readable [v202607 release record](https://zenodo.org/records/21378182), DOI `10.5281/zenodo.21378182`, published **15 July 2026**, contains a one-page release note and a listed new-stations workbook. The PDF confirms extension through end-2025 and station additions. Its text calls the workbook `v202507`, whereas the record lists `midas-open_v202607_new-stations.xlsx`: an explicit document/file-name discrepancy, not evidence that histories were inspected. The workbook was not downloaded. Additions between releases cannot establish historical height, relocation or exposure for the entire cohort.

Dataset citation: **Met Office (2026): MIDAS Open: UK hourly weather observation data, v202607. NERC EDS Centre for Environmental Data Analysis, 23 July 2026. doi:10.5285/d04207b551674c07801b7d4e6d883e50.** Retain edition, original path, header and checksum alongside every future input. A changed release needs a new input identity, not silent replacement of v202607.

## 2. Physical observation time: improved documentation, incomplete applicability

The [2021 Met Office MIDAS User Guide](https://zenodo.org/records/7357335), DOI `10.5281/zenodo.7357335`, was retrieved as public documentation after the web extraction route failed. The PDF is **2,597,551 bytes, 71 pages**, MD5 `02fe0896273170f69f21eeb04c855445`, matching Zenodo’s published checksum. Its internal change table begins with version 1.0, 6 January 2020; record publication and document revision are distinct. Relevant sections are 3.2–3.4, 4.3–4.5 and 5. This closes WR003's *retrieval* gap, not all 2025 applicability questions.

The guide documents UTC; `OB_TIME` for an instant, `OB_END_TIME` plus a count for period quantities; receipt/elapsed stamps have a different role. It gives HH−10 UK practice, SYNOP local variation HH−0…HH−10 (formerly HH−15 for SIESAWS), Mini-MMS AWSHRLY HH−10 and PRT minute averages from 15-second samples. Its broad SYNOP statement and later local-variation account differ in specificity. HCM period descriptions also differ; they do not define hourly air-temperature averaging. Station-era mapping therefore remains necessary. [Historic guidance](https://artefacts.ceda.ac.uk/badc_datadocs/ukmo-midas/ukmo_guide.html) describes CDL on-hour practice, but equipment replacement prevents treating the message label alone as an era proof.

The following are **WR004 interpretation decisions**, not decoded-record findings:

| Candidate message / equipment | Temporal classification for the proposed 00 UTC comparison | Evidence required to match forecasts |
|---|---|---|
| SYNOP | **CONDITIONALLY INTERPRETABLE**. A nominal hour cannot universally select a physical instant | Equipment/era and actual reporting convention; short-average support and whether CSV timestamp is nominal or effective. Do not subtract ten minutes twice |
| AWSHRLY, including Mini-MMS/former CDL | **CONDITIONALLY INTERPRETABLE** when equipment is known; otherwise **UNRESOLVED** | Distinguish legacy logger from MMS era; timestamp mapping, minute-sampling support, source capability and ID mapping |
| NCM | **UNRESOLVED** for an eligible hourly air-temperature series; a message can contribute other fields to a weather row | Temperature-specific provenance and support; do not transfer soil/state-of-ground or extrema timings to air temperature |
| DLY3208 | **UNSUITABLE FOR THE PROPOSED 00 UTC COHORT** on documented ordinary-climate daily practice | Usually 09 UTC, with local variation; a different question/cycle would require a new protocol |
| METAR | **UNSUITABLE FOR THIS EXACT OPEN EDITION** | Excluded from the catalogue subset; cannot be introduced from full MIDAS |
| HSUN3445 / HCM wind or radiation periods | **UNSUITABLE AS TEMPERATURE-TIME EVIDENCE** | Element-specific rules; a shared table/hour does not transfer support between quantities |

No selected 2025 observation's physical support is **CONFIRMED**. Timestamp string precision is not sensor timing accuracy. A one-minute instrumental average is not an hourly mean or an ideal instantaneous temperature; even known endpoint matching remains a qualified proxy. Temperature extremes, receipt times, period-end fields and air-temperature `ob_time` remain separate.

**Strict path:** retain WR003's physical-time/support gate; unknown mapping excludes the record. If a documented reference is effectively 23:50 while the forecast field is 00:00, there is no exact pair merely because both are labelled 00. Neither nearest-time tolerance nor interpolation is implicitly introduced.

**Possible revised path — INFERRED, not adopted:** compare delivered forecast temperature at the nominal reporting hour against documented nominal-hour station reports, preserving the observed/unknown offset and minute averaging. The estimand becomes *nominal-report product discrepancy*, including temporal mismatch, rather than exact physical-time discrepancy. Freeze that change, permitted message/era classes and claim limits before any errors; unknown or unbounded timing is not a licence to call the comparison instantaneous. No clock-induced uncertainty number is invented. A metadata pilot can decide whether this narrower question is useful; WR004 does not silently implement it.

## 3. Height, station identity and historical support

The current guide documents 1.25 m Stevenson-screen/PRT practice (§§3.3–3.4) and a metadata database distinct from MIDAS (§2.5.7). Reporting capabilities can change and instrument clusters can move while a common station reference position persists. These are **network standards and history requirements**, not a station-era proof for January 2025.

| Level of evidence | WR004 finding | Proposed eligibility consequence |
|---|---|---|
| NETWORK STANDARD | Nominal 1.25 m screened measurement is documented | Record this as guidance, never as measured height for every source ID |
| STATION-SPECIFIC EVIDENCE | Public Open documentation describes a station CSV; contents require sign-in | Coordinates/elevation/IDs must be inspected, including their valid dates and reference conventions |
| HISTORICAL STATION-ERA EVIDENCE | Relevant database/history is described; public release changes are not a complete sensor history | Actual height, instrumentation, location and exposure through January–2 February 2025 remain unverified |
| UNKNOWN CONFIGURATION | No selected station has been inspected | Cannot assert strict-cohort eligibility, continuity, calibrated uncertainty or ten available stations |

**Strict minimum, before selection:** pinned edition/source ID and reporting-capability mapping; historical position/CRS and elevation with qualification; valid station-era interval; instrument/screen height and sampling/reporting mapping; known moves, replacements and exposure changes or an explicit authoritative statement covering the era; temperature dictionary/QC and availability. An absence of a relocation entry in an incomplete log is not proof of stability. Screen height above local ground and station elevation above sea level are different metadata.

**Qualified proxy alternative — not adopted:** retain documented network practice, separately mark actual height/history/exposure unknown, and state an archive-station proxy target rather than a historically characterised thermometer. This may support decoding/interpretation research. A skill comparison would require a pre-error protocol revision explaining how missing history affects eligibility and inference. Do not impute 1.25 m as observed, claim identical 1.5/2 m quantities, or apply a lapse-rate correction to repair this gap. Unknown coastal/urban class is not inland/rural.

## 4. Temperature QC, missingness and revisions

The guide (§§4.3.4–4.3.10, 5.1–5.3) now supplies **documented component meanings**: marker/estimate/status/query/level; no QC at level 0; a zero query can also mean no information; corrections/estimates and record state are distinct. Version 1 is also assigned on ingestion; corrections can create version 0, and some station COR messages overwrite originals. The [Open guide](https://help.ceda.ac.uk/article/4982-midas-open-user-guide) explicitly warns that latest-state files may include un-QC-ed observations. No version or directory alone passes temperature QC.

The [WH table](https://artefacts.ceda.ac.uk/badc_datadocs/ukmo-midas/WH_Table.html) identifies `air_temperature`, `_q`, `_j`, `version_num`, `rec_st_ind`, `src_id`, `met_domain_name`, `id`, `id_type`, `ob_time` and receipt fields. Its linked code dictionaries are registered-user resources. The current guide explains components but **does not by itself verify their packing/order/width in the v202607 CSV integer, all temperature J-descriptors, current state-code applicability or per-column missing sentinels**. No integer-to-MESQL algorithm, guessed allowlist or universal `-9999` is adopted. Leading zeros, nulls and sentinel collisions must be resolved from headers/dictionaries. The catalogue's generic field units do not replace a file header.

Conditional policy after dictionary/header closure:

| Decision | Metadata condition / action |
|---|---|
| **ACCEPT** | Non-missing original temperature; documented non-suspect status, no unresolved failed checks, an explicitly preregistered completed-QC level, interpretable descriptors/state and unique valid revision. Requires verified encoding; none accepted in WR004 |
| **REJECT** | Documented missing temperature; commissioning `src_id=99999`; wrong quantity/time; source-declared suspect or rejected state under the frozen policy. Do not reject unusual weather merely because its value is extreme |
| **REQUIRES REVIEW** | Correction/estimate, reverted/observer-verified status, failed query with non-suspect status, changed record state or conflicting reporting capabilities. Review is source-rule/error-blind, not whichever value is closer to a forecast; exclude from primary use until resolved |
| **UNINTERPRETABLE** | Unknown code/packing/dictionary version, undocumented missing token or unresolved duplicate precedence. Quarantine; no primary comparison |

QC level 9 is documented as completed checks in the guide, but that alone is not an edition-specific acceptance code, uncertainty certificate or guarantee against error. A restricted unambiguous subset is **plausible, not demonstrated**. Its size could be zero. A pilot must verify the actual dictionary/header chain before any real record can pass.

For duplicates, use the pinned release, not a mutable live database. Preserve keys `(src_id, id_type/id, met_domain_name, ob_time/support, version)` and file/revision lineage. Collapse identical duplicates retaining references; prefer a unique documented current replacement within the same report identity only. Receipt metadata can assist documented precedence; it is not physical time. Unresolved conflicting values or multiple capabilities are quarantined, not averaged or chosen by forecast agreement. An overwriting COR history cannot be reconstructed from assumed version pairs. Missingness, source-QC rejection and eligibility rejection require separate counts.

## 5. Deterministic, error-blind station procedure

This is a **proposed algorithm for authorised metadata acquisition**, not an actual eligible list:

1. Pin the edition, headers/dictionaries/change logs and candidate metadata snapshot. Fix a numeric UK-mainland domain and historical interval before values/errors; these WR003 parameters remain open. Enumerate source IDs using metadata, not attractive station names or expected performance.
2. Join reporting IDs/capabilities to source IDs and dated station eras. Exclude commissioning ID 99999. Screen historical location/elevation, measurement height/time/interval and support; record unknowns and failed rules. First/last-year fields only nominate candidates.
3. Apply the strict or separately preregistered proxy policy, never a mixture hidden within one cohort. Inspect coordinates and forecast domain support from authorised static metadata before temperature errors. Urban/coastal/exposure strata require a reproducible metadata rule or remain unknown.
4. Establish planned valid slots and source availability/QC/revision counts without using temperature magnitudes or forecast discrepancies. This may require authorised parsing of annual files; raw-value access must be logged even if the screening process ignores values. Public listings cannot supply these counts.
5. Fix completeness thresholds and minimum scientific information before selection. Sort eligible station-era keys by numeric source ID then era start; take **at most ten**, recording the entire rejected/eligible inventory and reason. If geographic stratification is preferred, freeze its allocation/tie rules first; do not add it after seeing results.
6. Freeze the receipt before forecast-error computation. Zero eligible stations is a valid outcome. No invisible replacement of a station, period or missing forecast cycle is allowed.

The ten-station ceiling is a planning bound. No names, actual eligible population, continuity or completeness have been established. A future value-blind selection receipt is different from a claim that no one could access raw observations during acquisition.

## 6. Historical GFS closure

**Family documented:** GDEX **d084001**, DOI `10.5065/D65D8PWK`, operational GFS analysis/forecast GRIB2, 0.25° delivery grid, 1440 × 721, four UTC cycles and three-hour forecast sampling through 240 h. This is the delivered grid, not the FV3 computational mesh. The candidate remains 00 UTC, +24/+48 and instantaneous 2 m air temperature; f000 analysis, FNL/GDAS and reanalysis are excluded.

**Historical product documented:** the [NCEP implementation notice](https://www.weather.gov/media/notification/pdf2/scn22-104_gfs.v16.3.0_aaa.pdf) dates v16.3.0 to 29 November 2022, and the [EMC operational description](https://www.emc.ncep.noaa.gov/users/verification/global/gfs/ops/main.php) identifies v16.3. This supports lineage investigation, not a binary/patch/UPP pin for every January 2025 object. Exact archived generating-process/parameter-table identities remain to be inspected. The [NCO product inventory](https://www.nco.ncep.noaa.gov/pmb/products/gfs/) distinguishes the common 0.25° forecast product; its date and live patterns cannot substitute for the archive.

**Object identifiers publicly verified:** the [GDEX THREDDS day catalogue](https://tds.gdex.ucar.edu/thredds/catalog/files/g/d084001/2025/20250101/catalog.xml) returned HTTP 200 without credentials. The linked 2025 catalogue also lists January day directories. Two selected entries are:

| Exact GDEX `urlPath` | Displayed catalogue size | Catalogue modified time |
|---|---|---|
| `files/g/d084001/2025/20250101/gfs.0p25.2025010100.f024.grib2` | 539.5 Mbytes | `2025-01-02T19:25:49.556Z` |
| `files/g/d084001/2025/20250101/gfs.0p25.2025010100.f048.grib2` | 536.6 Mbytes | `2025-01-02T19:42:00.943Z` |

These are confirmed GDEX paths, unlike WR003's illustrative NOAA pattern. Rounded catalogue sizes are **whole multivariable files**, not temperature-field transfer sizes; modification time is not forecast issue or measurement time. Only one initialisation was inspected at file level; **62 required objects are not confirmed**. No file-server, OPeNDAP, subset or byte-range scientific request was made.

**Scientific content unverified:** exact TMP parameter/GRIB tables, height-above-ground level 2 m, K, instantaneous rather than statistical interval, reference/step/valid time, earth shape/scanning, packing/missingness, model terrain/land masks and historical software edition. Filenames are not proof of these. The THREDDS catalogue advertises HTTPServer and scientific subset protocols; advertisement is not successful data access or a verified single-field index. GDEX's converted/subset request route explicitly says login required. A registered subset and an anonymous catalogue are different pathways.

The GDEX summary's future endpoint and early-2026 update-stop note remain unreliable for completeness. Existing historical entries provide stronger bounded evidence, not resolution of the whole archive. The policy page is now readable but principally describes stewardship/FAIR principles, without a checked numerical quota, price or authenticated-service entitlement. No access charge or unlimited service guarantee is inferred.

## 7. Historical UKV closure

The [exact ASDI registry](https://registry.opendata.aws/met-office-uk-deterministic/) documents Met Office UK deterministic delivery, eu-west-2 bucket `met-office-atmospheric-model-data`, rolling two-year history, unsigned access, NetCDF and short 00 UTC forecasts nominally reaching 54 h. It identifies **British Crown copyright 2023–2025, CC BY-SA 4.0**. That gives documentary historical-year relevance but is not inspection of each object's embedded notice or clearance for all Met Office channels.

Public unsigned S3 ListObjectsV2 returned HTTP 200. The discovered root contains `uk-deterministic-2km/`; its first ten cycle prefixes begin 8 October 2024 and are truncated. That is a limited observed listing, not a complete earliest-date guarantee. Selected cycle and variable-prefix checks then confirmed:

| Exact object key under `uk-deterministic-2km/` | Listed bytes | LastModified (UTC) |
|---|---|---|
| `20250101T0000Z/20250102T0000Z-PT0024H00M-temperature_at_screen_level.nc` | 1,668,965 | `2025-01-01T06:01:54.000Z` |
| `20250101T0000Z/20250103T0000Z-PT0048H00M-temperature_at_screen_level.nc` | 1,669,312 | `2025-01-01T06:01:59.000Z` |
| `20250131T0000Z/20250202T0000Z-PT0048H00M-temperature_at_screen_level.nc` | 1,599,590 | `2025-01-31T06:01:55.000Z` |

The containing directory names the initialisation; the selected filename's first timestamp is **consistent with valid time**, followed by elapsed lead. A prefix repeating the initialisation in the +24 filename returned zero keys: that demonstrates a wrong lookup prefix, **not a missing +24 forecast**. The corrected prefix found the object. The listing separately exposes previous-hour maxima/minima, surface and dew-point temperature; none substitutes for `temperature_at_screen_level.nc`. ETags are observed storage metadata, not trusted-publisher identity or a universal SHA256.

The [November 2019 parameter document](https://www.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/data/ukv-aws-parameters-nov-2019.pdf) describes K, instantaneous screen temperature at 1.5 m and separate extrema. This is historical product guidance, **not proof of the selected 2025 array**. Present PS47 grid details do not identify the January 2025 delivery. Historical coordinates/CRS/axis order/shape, static orography and land mask bindings, diagnostic processing, suite changes, driving boundary model, reference/valid/period attributes, calendar, units and missing/packing semantics remain unverified. No NetCDF body or header bytes were retrieved. A listed mask at the selected lead is not proof of a static grid version or source-model orography.

Only **three** desired screen-temperature objects were checked, not all 62 or all station support. LastModified is an object timestamp, not independently established producer issue time; neither retained timestamps nor a typical 3–6 h latency guarantee availability to a historical end user.

## 8. Rolling retention and error-blind period handling

January 2025 UKV objects are **observed present for the three checks**, so wholesale absence is contradicted by this bounded evidence. Whole-month completeness is UNRESOLVED. At 10 October 2026 the period is about 21 months old; a nominal two-year window suggests removal around January 2027 (**INFERRED**, not an expiry SLA). The observed October 2024 prefixes illustrate rolling storage, not a preservation contract. A future authorised task must recheck exact identifiers before transfer; presence today does not reserve them.

Do not acquire data to rescue retention within WR004. If required objects later disappear, first record exact confirmed missing identifiers versus failed/truncated listings. A new candidate period may preserve the basic question if it has completed MIDAS-edition coverage, known forecast suites, common cycles/leads and reference metadata. Select it from a predefined metadata-overlap rule before errors, record changed season/version/estimand, and issue a new protocol. Moving to 2026 is not automatic: v202607 ends in 2025, and UKV delivery changes are relevant. Urgency does not bypass rights or budgets; 2019 documentation does not guarantee any replacement period.

## 9. Access, rights and retention: pathway-specific assessment

Checked **10 October 2026**. These are documentary assessments, **not legal approvals**. Reading public policies and listings did not accept a provider agreement, create credentials or configure AWS resources. Service permissions, copyright/database licences and experimental authority are separate.

| Intention | GFS through GDEX d084001 | UKV through this ASDI bucket | MIDAS Open hourly v202607 |
|---|---|---|---|
| Public catalogue / metadata listing | Observed anonymous catalogue | Observed unsigned S3 list | Observed edition listing |
| Scientific download | Advertised HTTP/scientific services; selected body access untested. Converted/subset route login required | Anonymous delivery documented; bodies untested | Registered CEDA users; metadata body redirects confirm access gate, no authentication performed |
| Research processing / transformation / local retention | CC BY 4.0 documented; source notices and service pathway require capture | CC BY-SA 4.0 documented for registry years; source notice applicability retained as gate | OGL v3 documented; licensed material scope and authorised access must be retained |
| Derived outputs / public display / raw redistribution | Attribution/modification and no-endorsement obligations; exact output/third-party scope review | Attribution/notices/modification; share-alike where adapted material or relevant database rights apply | Attribution/citation, exclusions and no endorsement; dataset versus restricted full MIDAS distinction |
| Commercial use / offline packages | Licence basis potentially supports these under conditions; delivery entitlement not blanket cleared | CC BY-SA is not a non-commercial licence; adaptation/package and distribution review still required | OGL allows commercial reuse of covered information; access/citation and excluded rights still apply |
| Long-term local archive / continuing supply | Licence does not guarantee continued hosting; exact selected service limits unresolved | Licence and retention of acquired material differ from rolling provider availability | Pin the release and lawful retained inputs; no guarantee every historical record survives unchanged across editions |

The full [OGL v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) is now readable via a public HTTP request, refining WR001–003's retrieval limitation. It permits reuse/adaptation/commercial exploitation of covered information with attribution, but excludes personal data, third-party rights and other specified material and disclaims continuing supply. It is not authority to bypass CEDA access controls. The [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.en) and [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en) legal texts were inspected. Retain supplied credit, licence/disclaimer/source links and changes; share-alike depends on the material actually shared, not an assumed universal licence for Meridian code.

The old Met Office Planetary/CC BY-NC-ND pathway and DataHub agreement remain **different channels**; their conditions are not silently imported into or erased by ASDI. The registry's 2023–2025 notice improves historical scope evidence; exact downloaded notice and any excluded contributor rights still require review. Zenodo's release-note record is CC BY 4.0, while the dataset is OGL: documentation rights are not observation rights. No new price, quota, concurrency cap, retention restriction or service-level promise was found that can safely be assigned to the experiment; those details remain UNKNOWN rather than zero/unlimited. Provider hosting does not require Meridian to provision paid AWS services for anonymous listing.

## 10. Gate reconciliation and global/regional feasibility

| WR003 gate | WR004 refinement | Remaining evidence / consequence |
|---|---|---|
| **T01** GFS archive | Two exact GDEX 2025010100 forecast paths listed; catalogue and advertised services readable | All desired cycles/messages, field metadata/version/static support, actual chosen transfer entitlement and bounded bytes not verified |
| **T02** UKV history | Three exact historical temperature paths/bytes listed; 2023–2025 registry notice captured | Complete selected inventory, 2025 array/static/suite metadata and notices remain |
| **T03** MIDAS edition | Edition, public metadata identifiers and release note confirmed | Station/QC/revision contents need authorised access; actual annual records not inspected |
| **T04** physical time/height | Current guide retrieved; equipment/message distinctions and nominal network height documented | Station-era mapping, short averaging and valid historical configuration block exact cohort; proxy revision optional, not adopted |
| **T05** QC/revisions | Component definitions and overwrite/latest-state caveats documented | v202607 encoding/J/missing/state dictionaries and header consistency required before a real acceptance list |
| **T06** scientific grid/quantity | Candidate forecast files now identifiable | Native delivery metadata, support/height/time interpretation and static bindings require controlled inspection |
| **T07** population/statistics | Deterministic selection procedure refined without errors | Actual cohort/completeness/domain and uncertainty parameters remain; no ten-station or interval guarantee |
| **T08** dependence | WR003 assimilation/tuning qualifications unchanged | Historic station assimilation and UKV boundary/version lineage unresolved; cannot claim independent ground truth |
| **T09** rights/resources | Exact documented licences and anonymous/registered pathways better separated | Terms/notices, wire/peak/request limits and acquisition authority required; no public distribution approval |
| **T10** freeze/reproducibility | Specific metadata-first handoff now possible | Full comparison still not preregistered; unresolved parameters cannot be defaulted |

**A future GFS-only/reference study:** conditional, blocked by common reference interpretation and remaining GFS metadata, not by regional archive access. **A future paired GFS/UKV/reference study:** conditional with the same reference blocker plus historical UKV/static/version closure. **Neither skill comparison is executable now.** Independent forecast decoding can be investigated without claiming a reference comparison; regional failure must not block all global scientific work. The broader global/regional, ensemble, mountain, nowcast, ML/hybrid, uncertainty and offline tracks remain intact.

## 11. Finite acquisition handoff, not executed

Keep two profiles distinct: **an interpretation pilot** and the later **WR003 January comparison**. Acquisition itself would be a separately authorised task, with no implicit account creation, agreement acceptance, provider contact or infrastructure.

| Input / prerequisite | Interpretation-pilot boundary | Later comparison / status |
|---|---|---|
| MIDAS release/metadata | v202607 station CSV, relevant file/station change log, licence/readme and temperature QC/J/state dictionaries; exact objects/dictionary editions must be captured before values | Public paths VERIFIED as listed; bodies/access BLOCKED until authorised credentials or lawfully supplied copies |
| Reference sample | At most **one metadata-selected station-era and one 2025 hourly-weather annual file**; retain January–2 February support if present. No claim that such a file/station is eligible | Message/filename UNKNOWN until metadata screening; ≤10 stations is only later planning bound |
| Forecasts | **None in the recommended reference pilot**; five listed identifiers retained as handoff evidence | Later Jan1–31 00 UTC +24/+48: 62 fields per model DOCUMENTED plan, complete objects NOT VERIFIED |
| Static support | Station-era history and sensor/reporting evidence first; future GFS/UKV original coordinate/terrain/land-mask resources need exact bindings | Historical forecast static-resource identifiers UNKNOWN; no new terrain acquisition |
| Processing | Existing local CSV/text tooling if available; isolated parsing and retained metadata checks; no provider client or production model | Required GRIB/NetCDF decoders and independent reference tools to be inventoried in a later authorised forecast task |
| Provenance | DOI/edition/source keys, dates/statuses/terms, headers/dictionary hashes, byte hashes and file sizes; no public raw data by default | Integrity does not establish publisher authenticity; preserve uncertainty and failed interpretation receipts |

Request classes: public catalogue/listing, registered metadata/dictionary retrieval, station-era records and one conditional annual observation download. Avoid directory mirroring, automatic pagination or repeated unbounded retries. Rights/access preflight can terminate before any scientific bytes. The pilot must not inspect forecast errors, rank stations, acquire forecasts, benchmark models, choose a production provider or create a publication pipeline.

**Resources:** the two example UKV temperature objects total **3,338,277 bytes** as listed; this is an observed metadata sum, not measured transfer or a month-size estimate. GDEX displays **539.5/536.6 Mbytes** for the two full files; compressed whole-file transfer is very different from one selected variable. Do not download them automatically to obtain a small temperature sample. Single-field subset/index feasibility and exact bytes remain UNKNOWN.

WR003's planning arithmetic remains `62 × 1440 × 721 × 4 = 257,483,520 bytes` (**245.56 MiB**) for float32 global GFS temperature values alone; it excludes GRIB, other fields, indexes, metadata, decoding, copies and observations. Up to `10 × 31 × 2 = 620` triplets / `1,240` model errors are logical ceilings, not usable counts or independent sample sizes. UKV dimensions, station-file bytes and decoded arrays remain UNKNOWN. No total transfer/storage/processing price is fabricated.

For the proposed reference pilot, adopt **provisional hard ceilings** of **50 MB scientific/metadata transfer**, **150 MB owned local scratch including original and parsed copies**, **one annual observation file**, and **20 retrieval requests including retries**, with no paid access. These are task limits, **not estimated needs or provider quotas**. Preflight listed/exact lengths, bounded streaming and actual rights; if dictionaries/history/file size cannot fit or cannot be established safely, stop before values rather than raise the ceiling silently. Documentation already inspected is not a new dataset dependency. RAM/time requirements remain unmeasured; avoid loading an unknown-size annual file wholesale.

**Scientific stop conditions:** no lawful metadata access; unknown QC packing or descriptor; unresolvable message/era clock; unsupported sensor/history assertion; ambiguous duplicate/revision; absent annual temperature field; inconsistent edition/header; exceeded byte/request limits. A pilot may return a precise incompatibility receipt. That is useful evidence, not a valid empty meteorological answer or authority to loosen WR003.

## 12. Reproduction and retrieval limitations

Metadata-only examples used Windows PowerShell `Invoke-WebRequest -UseBasicParsing -TimeoutSec 20`, without AWS tools, credentials or new clients. These requests list metadata; **do not replace their URLs with object/download endpoints** in WR004:

```powershell
# GDEX catalogue XML, not a GRIB file or scientific subset
Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 -Uri 'https://tds.gdex.ucar.edu/thredds/catalog/files/g/d084001/2025/20250101/catalog.xml'
# UKV exact historical +24 temperature key listing, not its NetCDF body
Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 -Uri 'https://met-office-atmospheric-model-data.s3.eu-west-2.amazonaws.com/?list-type=2&max-keys=2&prefix=uk-deterministic-2km%2F20250101T0000Z%2F20250102T0000Z-PT0024H00M-temperature_at_screen_level.nc'
```

For the other verified UKV entries substitute only their listed keys in the bounded `prefix` parameter. Check exact key equality, truncation and status; a zero-key wrong prefix is not absence. No automatic continuation was used. Read catalogues via their linked route rather than inventing GDEX object paths from NOAA conventions.

The web extraction tool could not read several Zenodo, GDEX and S3 endpoints. Ordinary public HTTP requests subsequently read the guide/release PDFs, GDEX catalogue/policy, OGL and unsigned S3 listings. This is a resolved **tool retrieval limitation**, not bypass of authenticated access. CEDA station CSV/change-log/readme redirected to sign-in and were not pursued. Registered QC dictionaries were not read. The current historical NCO f024 inventory remained unavailable; no actual historical GRIB message was inspected. Release PDF text has a workbook-name discrepancy; no attempt was made to invent its intended contents. No observation file, scientific forecast body, byte range, API client, account or provider contact was used.

The report records the selected listings as dated observations. Listings can change; future acquisitions require new receipts and file hashes. No private access, data acquisition, decoder or forecast verification was used to validate documentation.

## 13. Programme implication and exactly one next bounded task

WR004 closes retrieval and selected-object identity gaps while showing why manual completeness cannot establish a reference cohort. Prioritise a **reference interpretation pilot**, not another provider catalogue or a rushed rolling-archive rescue. This changes no WR001 broad topic status, WR002 source shortlist, production choice or accepted protocol. A later nominal-time or network-proxy revision must be explicit and pre-error. If strict reference interpretation fails, reconsider that reference/question with its negative evidence; do not use unqualified model agreement as validation.

**WEATHER RESEARCH 005 — MIDAS OPEN REFERENCE INTERPRETATION AND ERROR-BLIND ELIGIBILITY PILOT — NOT BEGUN.**

- **Objective:** determine whether the pinned v202607 metadata/header/dictionary chain can yield one defensibly interpretable historical near-surface temperature station-era, or an exact negative result. Do not assess forecast skill.
- **Required evidence:** exact edition notices and lawful metadata access; station CSV/history/capability mapping; authoritative temperature QC/J/state encoding and missing tokens; relevant 2021-guide sections; at most one error-blind selected annual observation file after metadata preflight.
- **Scope:** isolated, removable parser/interpretation checks and immutable receipts; confirm timestamps/short support, network versus actual height, identity/era, revisions and QC. Synthetic parser edge cases may test documented rules but cannot establish real station eligibility. No forecast downloads/errors, production pipeline or public raw-data publication.
- **Dependencies:** separately authorised acquisition/implementation; existing authorised CEDA access or lawfully supplied files, without creating accounts or accepting agreements automatically; rights and exact-size/request preflight. If access is absent, stop that gate and state which files the owner must lawfully obtain. No authentication was performed in WR004.
- **Acceptance criteria:** reproducible, source-qualified interpretation and selection/exclusion receipt; codes derived from verified dictionaries, not guessed; actual configuration distinct from guidance; at least one demonstrable interpretable era **or** a precise scientifically actionable blocker. A single era does not establish ten stations, a strict paired cohort or forecast performance.
- **Resource boundaries:** one annual station file, 50 MB transfer, 150 MB owned scratch, 20 requests including retries, no paid service; check these before retrieval, keep scientific inputs outside Git and authoritative data roots, preserve all existing evidence.
- **Stop conditions:** missing lawful access, missing/contradictory dictionaries or historical support, ambiguous message timing/revision, absent eligible sample or budget breach. End at the interpretation result; propose any protocol/reference change with reasons, without beginning forecast verification.

This task has **NOT BEGUN**. It is the sole subsequent task. Neither the full January comparison nor any fallback provider investigation is authorised through this handoff.

## 14. Validation receipt

Read-only preflight preservation: **33/33 passed** before edits. Final documentation and preservation pass: **65/65 passed** (32 documentation/scope checks and 33 preservation checks); all **20 new internal links/anchors** resolve, 19 dated primary-source entries and six documentary WR004 questions are consistent. The nine-file Markdown change preserves all 1,212 tracked files outside eight append-only records, all 42 Atlas status rows, 113 protected hashes, frozen 60 cases/three pins/source prerequisites, accepted stores/publications and original/window projection identities/member seals. All 100 Swiss native fingerprints, 11,429 terrain seals and **40,842 Weather publication file hashes** remain unchanged. Historical WR001–003 content and broad Weather topic statuses are retained. Complete diff reviewed for unintended changes, whitespace, credentials, private paths and generated payloads.

Scientific regression suites, conformance replay, lint, TypeScript and builds were deliberately not run because no executable code, scientific data, contracts or dependencies changed. Documentation checks do not establish decoded-value conformance or skill. No data-materialising pipeline, private access, account, scientific acquisition or subsequent experiment occurred. Final post-receipt checks and Git delivery state are reported separately.
