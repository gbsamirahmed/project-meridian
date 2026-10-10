# WR006: MIDAS historical measurement support and reference-target decision

**10 October 2026.** Public `gbsamirahmed/project-meridian`, main, starting checkpoint
`8a432d80afd3888dee82f23a42996a66fdaea283`. Clean tree, fetched origin/main, exact
checkpoint and 0/0 divergence confirmed before edits. Read WR001–005 evidence,
particularly [WR005](midas-reference-interpretation-pilot.md), [WR004](reference-metadata-and-historical-product-closure.md),
[semantics](temperature-semantics.md), [protocol](temperature-verification-protocol.md),
[gates](temperature-acquisition-gates.md), [compatibility](forecast-reference-compatibility.md),
[programme](research-programme.md), [register](research-register.md) and [sources](sources.md).
[Foundations engineering](../../foundations/engineering.md), [economics](../../foundations/economics.md)
and [data-layout preservation](../../phase-4-migration-inventory.md) remain applicable.

## Executive decision

**REFERENCE-TARGET DECISION C — STRICT AND REVISED TARGETS BLOCKED.**
**WR006 OUTCOME C — EVIDENCE BLOCKED.** One error-blind audit nominee was fixed:
**MIDAS `00032`, WICK AIRPORT, intended January 2025 era**. The available evidence
cannot establish its dated equipment/location history, sensor height or physical
temperature clock. A station-specific capability file is publicly listed, but its
body redirects to sign-in. No new local capability/history/annual file was found.
No actual historical station-era or accepted reference observation is established.

There is a useful documentary refinement: the linked historical **QC/J document
is anonymously readable** through its public delivery redirect. It explicitly
explains the MESQL positional layout and temperature descriptors. WR004/WR005's
unread-dictionary limitation is refined, not silently erased. This does not establish
v202607 header/missing-code applicability, shortened-flag semantics in actual
records or temperature revision precedence. Both the strict physical-time reference
and a nominal-report proxy remain blocked; **no revised protocol is adopted**.

The negative result concerns evidence/access within this scope, not instrument
failure, station non-existence or forecast quality. Metadata and filenames are not
historical measurement support. WR005 remains Outcome B for its successful metadata
inspection; WR006 is C for its unsuccessful historical-support objective. No annual
observation file or forecast body was opened; no magnitudes, errors or skill were
computed. Stop MIDAS-only investigation here. Independent global forecast decoding
can progress without pretending to verify predictive skill.

Evidence labels: **CONFIRMED** = inspected specified document/metadata bytes;
**INFERRED** = the proposed audit or future method; **UNKNOWN** = unsupported historical
property; **CONTRADICTED** = an assumption contradicted by evidence. A documented
capability, listed file, inspected file, interpretable record and eligible reference
remain distinct. Source hashes establish local byte identity, not publisher authenticity.

## 1. Discovery and immutable identities

Recursive filename/context discovery throughout the authorised external data root
found only the same three MIDAS files, in
`research-inputs/weather/weather/midas-open/v202607/`. A second filename walk included
MIDAS context, edition/station/QC names and `00032`/Wick variants; no additional
capability, history, dictionary or annual input was located. Header inspection and
hashes confirm the existing copies rather than a filename-only edition assumption.
The repeated `weather` directory is harmless; **no meridian-data file was moved,
copied, deleted, overwritten or reorganised**. No private repository or unrelated
personal directory was searched. Scratch and public-document responses are separate
from source data and Git.

Pinned edition: **MIDAS Open UK hourly weather observations v202607**,
DOI **10.5285/d04207b551674c07801b7d4e6d883e50**. The supplied README binds the
[exact catalogue and citation](https://catalogue.ceda.ac.uk/uuid/d04207b551674c07801b7d4e6d883e50/).
Metadata snapshot dates are 13 July 2026; catalogue publication is 23 July 2026.
Neither is a station-era validity date. Actual user download date/session and
provider-side checksum/signature remain uncaptured.

| Original immutable input | Bytes | SHA256 |
|---|---:|---|
| `00README_catalogue_and_licence.txt` | 843 | `bbdaa4ca60d0d9c2a261ab1b72df814c2e3bbf57cf2c4715283b03400f028737` |
| `midas-open_uk-hourly-weather-obs_dv-202607_station-metadata.csv` | 134,123 | `3c98d20c4b9a8aba3270280c8692b72a54d66df05d178c5fed27eb70e6fd3acc` |
| `midas-open_uk-hourly-weather-obs_dv-202607_change_log.txt` | 73,638 | `5ee2036336d7c36e7aeb7142d6be0f1e08f3bec7e658de2bc598688898e0c26c` |

All **208,604 bytes** were read in place and checked before/after. WR005's
[input pins and parser](../../../scripts/weather-research/wr005/README.md) are unchanged.
The retained 2021 [MIDAS guide](https://zenodo.org/records/7357335), DOI 10.5281/zenodo.7357335,
was re-read locally: 2,597,551 bytes, MD5 `02fe0896273170f69f21eeb04c855445`,
SHA256 `4e7b4e46b5b054b46eab49d5753a4bce49e506347b6b7cd1a1c855c362d5136c`.
No repeat PDF transfer. Its publication is 5 July 2021, not January 2025 applicability.

## 2. One frozen audit nomination

Before public station investigation and before any observation magnitudes, fix:
use the pinned metadata only; nominate non-commissioning IDs whose first/last-year
range includes 2025; restrict to the existing `historic_county == caithness` metadata
group; sort ascending numeric `src_id`; take the first, **no replacement**. Two rows
nominate this audit group; only **one** is investigated. The lowest is `00032`.
Caithness is a finite northern-UK metadata grouping chosen to bound a historical
support audit, without a forecast performance preference. This is not random or
representative sampling, a modern county polygon, a UK-mainland proof or a frozen
future verification cohort. Actual historical UKV support remains unverified.

| Selected metadata / candidate | Evidence status and meaning |
|---|---|
| `00032`, WICK AIRPORT; stem `wick-airport`; authority Met Office | CONFIRMED in the pinned snapshot; source ID does not alone prove instrument continuity |
| `caithness`, 58.454° N, 3.090° W (WGS84, rounded three decimals) | CONFIRMED **currently recorded** location; January 2025 location UNKNOWN |
| Elevation 36 m above mean sea level | CONFIRMED header/row meaning; named vertical-datum realisation and historical instrument elevation UNKNOWN; not sensor height |
| First 1968 / last 2025 | CONFIRMED release metadata endpoints; intervening reporting, January availability and unchanged equipment UNKNOWN |
| Intended 1 January–2 February 2025 support | INFERRED audit interval covering the original initialisations and +48 h spillover; not an established era |
| SYNOP/AWSHRLY identity, WMO/DCNN mapping, prime capability and dated equipment | UNKNOWN; the capability contents were not obtained |

The prior counts reproduce: 1,544 unique IDs, 390 2025 year-range nominations;
692 release-listed 2025 files (302 qcv-0, 390 qcv-1), county/stem/ID joins agree.
These facts nominate objects; they do not establish passed temperature QC or
continuous station-eras. The initially frozen selection receipt is **1,567 bytes**,
SHA256 `c1066b1f0f021dc816d3ca3ee6c899fb9f580078d1fcf0f2c6c3071b21c3521f`.
Its JSON content reproduces exactly; the CLI's LF serialisation is distinguished
from the original Windows-newline receipt, rather than claiming their byte hashes match.

## 3. Bounded public evidence attempt

Six anonymous GETs, checked **10 October 2026**, no credentials/cookies or automatic
redirects. Only a public document-delivery redirect was followed explicitly; sign-in
was not followed. Bodies, status and hashes are retained in owned scratch and pinned
in [public-evidence-pins.json](../../../scripts/weather-research/wr006/public-evidence-pins.json).
No recursive network browsing or pagination; no provider contact or agreement.

| Request / exact route | Inspected result / body bytes |
|---|---|
| 1 [Selected station directory](https://data.ceda.ac.uk/badc/ukmo-midas-open/data/uk-hourly-weather-obs/dataset-version-202607/caithness/00032_wick-airport/) | HTTP 200, **17,706**; capability CSV listed at displayed 2.0 KB, qcv-0/qcv-1 directories |
| 2 [Listed capability CSV download](https://dap.ceda.ac.uk/badc/ukmo-midas-open/data/uk-hourly-weather-obs/dataset-version-202607/caithness/00032_wick-airport/midas-open_uk-hourly-weather-obs_dv-202607_caithness_00032_wick-airport_capability.csv?download=1) | HTTP 302 to sign-in, **15**; no CSV contents. No authentication retry |
| 3 [WH table](https://artefacts.ceda.ac.uk/badc_datadocs/ukmo-midas/WH_Table.html) | HTTP 200, **42,114**; anticipated air-temperature/Q/J/state/time fields and actual linked dictionary route |
| 4 [Selected qcv-1 directory](https://data.ceda.ac.uk/badc/ukmo-midas-open/data/uk-hourly-weather-obs/dataset-version-202607/caithness/00032_wick-airport/qc-version-1/) | HTTP 200, **79,291**; exact v202607 qcv-1 2025 filename listed at displayed **3.1 MB**. Not exact size, inspected header or record content |
| 5 [Linked QC/J route, HTTPS](https://data.ceda.ac.uk/badc/ukmo-midas/metadata/doc/QC_J_flags.html) | HTTP 302 public redirect to dap.ceda, **0** |
| 6 [Public QC/J document](https://dap.ceda.ac.uk/badc/ukmo-midas/metadata/doc/QC_J_flags.html) | HTTP 200, **25,668**; genuine QC document, not a sign-in page. No credentials or access-control bypass |

The WH link advertises registered-user information; anonymous delivery nonetheless
served its document. This observation refines the prior **retrieval** limitation,
not every station-data entitlement. No publication/revision date or v202607 binding
was stated in the inspected QC page. Its historical shorthand about version 1 being
QC-checked conflicts with the Open guide/current manual caveat: ingestion can already
have version 1. Preserve that conflict; do not convert it into an acceptance rule.
The station capability body remains inaccessible in this session, not scientifically
invalid or proven absent.

## 4. Historical measurement support

| Property / authoritative evidence | Actual selected-era support / strict consequence |
|---|---|
| Identity/history — metadata snapshot; guide §2.5.7 | No dated location, instrument cluster, relocation, replacement or exposure history. A common reference position can conceal cluster movement. UNKNOWN; current location cannot establish January continuity |
| Reporting capability — guide §4.2; listed selected capability | Capability is met-domain/ID-type/ID with date interval; prime designation does not guarantee no gaps. Contents UNKNOWN; neither reporting identity nor a unique historical source is established |
| Height — guide §§3.3–3.4 | 1.25 m screen/PRT practice is a NETWORK STANDARD only. No Wick station-era height, shielding or sampling configuration established; GFS 2 m, UKV 1.5 m and actual station construct remain distinct |
| Time — guide §§3.2, 4.3.5, 4.4.1 | UTC nominal/report, physical and receipt times differ. SYNOP local HH−0…HH−10 and former HH−15 rules require equipment/era mapping. No selected message convention or sample support known |
| AWSHRLY — guide §4.4.3 | Mini-MMS HH−10 versus legacy equipment context; no evidence assigns that system to Wick in January 2025. No universal subtraction, on-hour assumption or soil/wind timing transfer |
| Temperature short average — guide §3.4 | Network minute averages from short samples do not prove a selected record's support or hourly mean. Exact physical-time pairing remains BLOCKED |

No dated station-era-specific measurement fact was established. Outcome C is therefore
more precise than B for this objective, despite successful current metadata/document
inspection. No absence-of-relocation inference, invented instrument history or
sensor uncertainty is assigned. Station history access through fuller MIDAS metadata
may require a lawful user/provider step; the exact historical record file/availability
is UNKNOWN, not fabricated.

## 5. QC, missingness, revisions and annual-file gate

**Documentary advance:** the inspected QC page describes `_q` as up to five decimal
positions ordered **marker, estimate, status, query, level (MESQL)**. Its shortened
example places `1` in the final position with four **blank** preceding positions;
blanks are not silently equated to documented zero codes. `_j` is an element-specific
character descriptor; the temperature family is code_id 8010. These are historical
encoding documentation, not guessed bit masks. Estimate/query zero can mean missing
information, and QC level alone does not prove every validation/visual check occurred.
The precipitation marker/negative trace discussion does not define ordinary air-temperature
acceptance. No QC decoder, zero-padding acceptance or guessed missing sentinel is added.

Remaining chain: actual v202607 annual header/field types/units/missing encodings;
applicable dictionary revision; how absent leading components appear in this CSV;
J-descriptor applicability to air temperature rather than wet-bulb/extrema/soil;
record-state codes and unique revision/report key. Guide §§4.3 and 5 explains
version updates and possible COR overwrites; the WH snapshot receipt-time guidance
is not licence to choose across different message clocks or silently reconstruct
lost intermediate versions. Exact source-qualified duplicate handling remains open.

| Record decision | WR006 position |
|---|---|
| ACCEPT | None: no actual reference record inspected or accepted |
| REJECT | No actual record rejected; malformed/pin-mismatched inputs and unsupported historical assertions fail the utility |
| REQUIRES REVIEW | Documented estimates, corrections, failed-query/non-suspect combinations and conflicting revisions would need a frozen error-blind rule; no counts invented |
| UNINTERPRETABLE | Actual edition encodings/history/time unresolved; cannot manufacture a series from filenames or generic QC guidance |

**Annual files inspected: 0 (maximum 1).** The public 2025 listing is useful identity
and approximate-size evidence. Its exact listed filename is
`midas-open_uk-hourly-weather-obs_dv-202607_caithness_00032_wick-airport_qcv-1_2025.csv`.
The file is not locally supplied, capability contents
require sign-in, and an annual header cannot itself establish historical sensor height
or a dated clock mapping. No observation-body request was made just to demonstrate
activity; no temperature magnitudes or missingness/duplicate counts were read. Annual
identity and future authorised header interpretation remain separate from its historical
eligibility. Scientific evidence unavailable is not a meteorological rejection.

## 6. Formal decision and possible protocol change

The original [WR003 strict-support preference](temperature-verification-protocol.md)
remains **BLOCKED**, not superseded. Decision A fails on history/height/time and record
interpretability. Decision B is also unsupported: unknown-height qualification alone
cannot repair unknown temperature QC/missingness/revisions or unbounded station-era
clock interpretation. The openly readable generic dictionary reduces one uncertainty
but does not supply interpretable real reference records. **Decision C is retained.**

A possible **nominal-report archive-station discrepancy** estimand remains **PROPOSED**:
compare each delivered forecast at its decoded valid hour with explicitly defined,
QC-interpretable reports at the same nominal UTC hour, retaining original forecast
heights, unknown actual sensor height, measurement offset/average and point/grid mismatch.
It would measure discrepancy to those reports, not exact-height/time physical error.
Such a revision would require an inspected annual header, source/report mapping,
applicable QC/missing/revision rules, a bounded documented temporal class, error-blind
inclusion and an explicit pre-error freeze. No tolerance window, nearest-hour rounding,
interpolation, lapse-rate adjustment, correction preference or numeric acceptance rule
is adopted. Unknowns cannot be made small merely by calling the target operational.

Permitted present claims: evidence/byte identity, metadata nomination, public listing,
documented historical encoding and a blocked target. Prohibited: January continuity,
passed-QC measurements, strict or proxy pairability, forecast skill, model superiority,
resolution benefit, mountain/route suitability or independent observational truth.

### Smallest outstanding manual evidence checklist

1. The exact **v202607 `00032_wick-airport_capability.csv`** linked in request 2:
   user-supplied lawful copy, original filename/size/hash and acquisition/terms receipt.
   Establish dated reporting-ID/met-domain/prime-capability intervals. This alone
   does not prove sensor height, timing or exposure.
2. If available, authoritative **Wick source 00032 instrument/location history covering
   January–2 February 2025**, including height, logger/sampling/report clock and dated
   changes. Source file/title/availability beyond the described station metadata
   facilities is not known; a manual provider enquiry may be necessary, **not sent**.
3. Before interpreting any observations, one authorised exact-edition annual file/header
   and applicable missing/Q/J/state/revision definitions. The generic QC page is now
   readable; only the residual applicability questions need clarification.

These are outstanding evidence requirements, **not another authorised or recommended
MIDAS task**. No request to wait indefinitely or supply passwords/session material.

## 7. Reproducible executable evidence and limits

[Isolated WR006 utility and instructions](../../../scripts/weather-research/wr006/README.md)
reuse the unchanged WR005 parser/pins. `freeze` regenerates the metadata-only subject;
`audit` validates that frozen object and six exact public-response pins, rechecks
inputs, and reproduces the **manually assessed C/C decision for this evidence bundle**.
It is not a general station-history validator or automated scientific decision engine.
Additional/changed evidence cannot silently produce A/B; unsupported selection,
height/time/QC assertions or changed bytes fail. No annual/forecast decoder, network
code, new dependency or production import is introduced.

Two offline audit runs produce **byte-identical 3,751-byte receipts**, SHA256
`1db9f38dbe81cd8f23c4805998321ae0d7b8bffc7e47809dc2ea664d868f167d`.
Frozen selection content regenerates deterministically; original newline byte identity
is recorded separately. The full receipts and response bodies remain outside Git;
only code, public source pins and qualified findings are committed. Changed live
HTML must not be automatically repinned to make a test pass.

**12 new synthetic tests** cover nomination/order/year exclusions, no substitution,
unsupported historical height/clock/QC claims, malformed/changed receipts, public
body corruption, source/repository output rejection and no overwrite. They test the
selection/audit boundary, **not real QC decoding, sensor history or observation timing**.
**22 unchanged WR005 synthetic tests** pass, including malformed header/schema/release/
missing metadata/duplicate-ID cases. Actual source inspection and repeat receipts
are separate real-evidence checks. Annual-record QC/timing/missingness/duplicate
interpretation tests remain **NOT EXECUTABLE**, not passed.

| Resource / measured scope | Actual / authorised ceiling |
|---|---|
| New public-document/listing retrievals, redirects counted individually | **6 requests / 164,794 response-body bytes**, versus 20 / 50 MB; no automatic redirects/retries, no dataset body |
| Transfer accounting | Actual bytes read from HTTP bodies; transport headers/TLS overhead unmeasured. Required Git fetch/push is separate repository control traffic, not scientific acquisition |
| Source data copies / annual files / forecast bodies | **0 bytes / 0 / 0**; manually supplied 208,604 bytes read in place; no GFS/UKV downloads |
| Station-era audit candidates / eligible eras established | **1 / 0**; second nominee not investigated; no automatic replacement |
| Owned scratch | **Less than 5 MB at final inventory**, including source-response bodies, receipts, baseline/check/diff files and application-only build; 150 MB ceiling. Snapshot, not continuously sampled peak; small synthetic temporary fixtures removed |
| Runtime/tooling | Existing Python 3.12.6, Windows 11 build 26200 AMD64; Node 24.11.0/npm 11.6.2. No installs, mobile toolchain or claimed performance improvement |

Local directory discovery reads filenames/stat information before scientific content;
no unbounded large-file load. Each network body is capped at 2,000,000 bytes with a
cumulative 50,000,000-byte/request ledger and redirects disabled. All six responses
completed below their caps. Nothing uses user credentials or accepts an agreement.
The isolated audit has no network access itself. Scratch cannot be an input directory
or the repository; outputs cannot overwrite existing files.

## 8. Rights, preservation and executed checks

The pinned README's **OGL v3 and catalogue citation** support covered local metadata
research under documented conditions; registered acquisition is separate. Retain the
Met Office/CEDA v202607 citation from [WR005](midas-reference-interpretation-pilot.md#7-rights-acquisition-and-resource-receipt).
An anonymous QC document response is not permission to acquire restricted station
history, mirror data, redistribute observations or clear future commercial/offline
packages. No account/session, provider agreement, paid resource or legal clearance.

Executed: **33/33 preflight preservation checks**, focused **12 + 22 synthetic tests**,
**7/7 existing Weather publication tests**, documentation/link/register/input checks
and final preservation checks recorded in the development log. Lint, TypeScript and
**application-only** build pass. A first publication-test attempt failed one loopback
case with sandbox EACCES; the access-scoped rerun passed all seven. A first isolated
build attempt failed sandbox filesystem EPERM; the scoped rerun passed, with existing
optional-esbuild config-bundling and large-chunk warnings. No source fixes were needed.

Protected 42 Atlas statuses, 113 production hashes, frozen 60-case/three-pin fixtures,
accepted original/window projection bytes, retained scientific/native evidence,
negative Swiss/AWS finding and **40,842 Weather publication files** remain unchanged.
Preservation checks read retained scientific bytes only to verify hashes; these are
separate from the zero new historical forecast/observation inspections above.
No runtime, shared contract, dependency or source-data change. Full scientific suites,
60-case conformance replay, decoder/model benchmarks and full Weather/data-materialising
build are omitted because this isolated selection/pin harness does not alter those
implementations or scientific inputs. No unrun suite is claimed passed. No private
access, data acquisition, mobile/device work or later task has begun.

## 9. Programme consequence and exactly one next task

The common reference problem blocks **GFS-only reference verification and paired
GFS/UKV verification**, not legitimate global source-format/decoding research. Keep
GFS and UKV as global and regional **research candidates**, neither a production
selection. No regional superiority, reanalysis truth substitute or model-agreement
skill claim. The broad global/regional, ensembles, nowcasting/observations, ML/hybrid,
mountain weather, uncertainty, wind/cloud/precipitation/temperature, provenance,
offline and Atlas/Guide programme remains. W01–W40 maturity statuses are unchanged.

**WEATHER — BOUNDED HISTORICAL GFS TEMPERATURE-FIELD ACQUISITION, DECODING AND INTEGRITY PILOT — NOT BEGUN.**

**Objective:** establish actual source-format/numerical integrity of **one** historical
global forecast temperature field, independently of unresolved MIDAS reference support.
This is decoding/interpretation evidence, not forecast verification or model selection.

**Required evidence:** WR004 GDEX d084001, DOI 10.5065/D65D8PWK, publicly listed
`gfs.0p25.2025010100.f024.grib2` as candidate parent; exact lawful field subset or
indexed message route; product/service terms, byte preflight and producing/table/grid/
packing/time/height metadata. The parent listing is approximately **539.5 MB**, so
whole-file download is outside the proposed budget. A filename is not verified
`TMP` at 2 m content; no endpoint/range support or entitlement is assumed.

**Scope:** at most one 1 January 2025 00 UTC +24 h operational forecast field,
instantaneous air temperature at 2 m, delivered native grid. Establish the request
and message identity before values; obtain only a lawful bounded subset/message;
retain immutable source/metadata/hash/rights receipt outside Git. Use existing local
decoder tools if sufficient; compare independent decoding paths or source-derived
packing/reference anchors, units K, masks, scanning/native coordinates and decoded
reference+lead=valid time. If genuinely independent numerical checking is unavailable,
report that limitation instead of claiming validation. No MIDAS/UKV acquisition,
station errors, skill metrics, reanalysis substitution, production ingestion or tiles.

**Dependencies:** separately authorised next task; lawful subset/index access or a
manually supplied exact field; byte sizes/rights verified first; inventory existing
decoders and their versions before implementation. No hardware or new SDK required.

**Acceptance:** reproducible pinned one-field decode, correct quantity/2 m height,
forecast rather than analysis, native grid/units/time/missingness and justified
independent numerical checks, or a precise access/format/resource blocker. No silent
cycle, edition, field or source substitution; preserve negative receipts.

**Resource boundaries:** proposed ceilings **50 MB transfer, 150 MB owned scratch,
20 retrievals including retries, one scientific field**, no full parent file, paid
service, cloud, bulk download or new dependency. These constrain the future proposal;
no forecast retrieval has occurred in WR006.

**Stop conditions:** authentication/agreement/provider contact, unavailable lawful
bounded field route, unknown size beyond the ceiling, wrong historical product,
unsupported packing or need for substantial new tooling. Stop rather than expand to
another provider/variable or a full GRIB engine. Evidence may redirect the programme;
this is not an unconditional sequence of numbered implementation tasks. **NOT BEGUN.**
