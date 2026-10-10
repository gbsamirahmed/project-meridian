# Weather Research 002: source-specific access and rights

Checked **10 October 2026**. Companion to the [product feasibility report](global-regional-source-feasibility.md) and [reference/validation design opportunities](forecast-reference-compatibility.md). These are **research assessments, not legal approvals**. No account, contract, API request for scientific data, download or purchase occurred. An open licence is evidence about information reuse; it is not an unlimited hosted-service entitlement, an operational guarantee or authority over third-party material.

## Pathway register

**P** = documented permissible under stated conditions; **V** = potentially permissible, verification required; **C** = paid or contractual permission required; **R** = restricted/prohibited under identified terms; **U** = unresolved. P does not certify compliance. It applies only to the named product/channel and documented information, with exclusions/notices below. Nine intentions are recorded separately: research; local retention; processing; commercial application; public display; derived distribution; raw redistribution; offline end-user packaging; long-term archiving.

| Exact channel / information | Research | Retain | Process | Commercial | Display | Derived | Raw | Offline | Archive | Basis and outstanding condition |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 current ECMWF IFS open subset | P | P | P | P | P | P | P | P | P | CC BY 4.0 and ECMWF terms; identify edition, credit, licence and modifications; current service retention is not a ban on user archiving |
| G1 historical TIGGE / MARS-selected delivery | V | V | V | U | U | U | U | U | V | Registration/accepted dataset terms or archive entitlement required. Exact applicable historical licence/access agreement not resolved; current open-feed permission does not settle it |
| G2 GFS original NOAA NODD distribution | P | P | P | P | P | P | P | P | P | Specific registry's NOAA reuse conditions; credit, non-endorsement and distinguish modified material. Confirm selected file's provenance/exceptions |
| G2 GDEX d084001 historical archive | P | P | P | P | P | P | P | P | P | Dataset record declares CC BY 4.0; acknowledge producer and archive/DOI. Subset/download account policy and archive service continuity remain separate gaps |
| G3 current ECMWF AIFS open delivery | P | P | P | P | P | P | P | P | P | Documented CC BY 4.0 information reuse; model-code/training-data terms are separate |
| G3 AIFS history via MARS | V | V | V | V | V | V | V | V | V | Data licence is documented, but delivery entitlement/charges/contract and exact experimental versus operational edition must be established |
| R1 UKV ASDI NetCDF current documented channel | P | P | P | P | P | V | P | V | P | Registry links CC BY-SA 4.0. Attribution and change notice; share-alike applies to adaptations. Resolve obsolete conflicting page and adaptation/package compatibility before distribution |
| R1 alternative DataHub contract channel | C | V | V | C | V | V | R | V | V | Product-specific subscription/agreement; raw resale and distribution outside the permitted Application are restricted. A paid plan is not raw/offline redistribution clearance |
| R2 ICON-CH1/CH2-EPS OGD | P | P | P | P | P | P | P | P | P | MeteoSwiss OGD CC BY 4.0 with source attribution, no endorsement, applicable upstream conditions; service access limits remain |
| O1 legacy ISD through NODD | P | P | P | P | P | P | P | P | P | Specific NOAA NODD notice; contributor provenance/exceptions still require review of the selected information. Supersession limits freshness, not automatically reuse |
| O1 successor GHCNh selected edition | V | V | V | U | U | U | U | U | V | Source integration/QC documented, but exact edition's conditions and contributing rights not completely retrieved. Do not inherit ISD's grant mechanically |
| O2 MIDAS Open hourly weather v202607 | P | P | P | P | P | P | P | P | P | Exact CEDA record identifies OGL v3 and registered access; stated provider attribution and excluded rights apply. Full licence text retrieval blocked; primary indexed permission text checked |
| O3 SwissMetNet OGD | P | P | P | P | P | P | P | P | P | Same specified OGD terms, parameter/station provenance and modifications retained; QC edition/history requirements are scientific, not licence exceptions |

There is **no production redistribution clearance**. P means the published grant supports that intended pathway for the covered information, subject to verified licence compliance. V/U must not be relabelled P merely because files can be copied. No restrictions on retention or processing were invented where the product documents did not identify them. Hashes establish integrity, not publisher authenticity. A provider/API contract, information licence and a downstream archive's agreement may all apply.

## Evidence, editions and conditions

### ECMWF information versus delivery

[Current open-data terms](https://www.ecmwf.int/en/forecasts/datasets/open-data) identify CC BY 4.0 and [ECMWF general terms](https://apps.ecmwf.int/datasets/licences/general/). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) requires attribution, licence reference and indication of changes; it does not convey trademarks/endorsement or override excluded rights. [ECMWF's 2025 catalogue-opening announcement](https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwf-makes-its-entire-real-time-catalogue-open-all) distinguishes information licensing from delivery costs. A complete catalogue being openly licensed does not mean every resolution or historical request is free to retrieve.

For current public subsets, no source registration is described. The published 500 simultaneous-connection portal limit is a **service-wide condition**, not a promised user allowance. Actual download volumes, throughput, reliability and precise hosted-cloud retrieval charges to Meridian were not measured. AIFS access-controlled archives are documented in its [dataset page](https://www.ecmwf.int/en/forecasts/datasets/aifs-machine-learning-data); no historical entitlement or tariff is assumed.

TIGGE's [catalogue/download conditions](https://ecds.ecmwf.int/datasets/tigge-forecasts?tab=download) require accepted terms. An older licence found on an ECMWF test-host describes non-commercial terms; that is **not verified as the current licence** and cannot resolve the selected archive's rights. Obtain the exact current accepted agreement and source-centre conditions before historical acquisition or commercial/offline planning. This is a live historical-channel uncertainty, not a claim that all ECMWF data remain non-commercial.

### NOAA and GDEX

[GFS](https://registry.opendata.aws/noaa-gfs-bdp-pds/) and [ISD](https://registry.opendata.aws/noaa-isd/) registry entries permit reuse under NOAA conditions, request acknowledgement, disallow implied endorsement and require modified data not be passed off as unaltered originals. Anonymous access does not require opening an AWS account. Use the selected channel's terms; no cloud resource is necessary for a future ordinary public download.

The [NWS disclaimer/service guidance](https://www.weather.gov/disclaimer) separately permits access controls against excessive use and does not guarantee delivery. No verified per-user numerical quota, cache-duration limit or source fee was obtained for these selected bulk routes; **UNKNOWN is not unlimited**. General government/public-domain descriptions do not automatically resolve contributor material in a multi-agency reference product. The current [GHCNh page](https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly) establishes provenance/QC breadth; exact distribution conditions and current edition metadata remain a separate gate.

[GDEX's exact GFS archive](https://gdex.ucar.edu/datasets/d084001/) labels its dataset CC BY 4.0 and gives the DOI. Its delivery/account policies could not be fully retrieved. Do not bypass an authenticated subset service or infer an unlimited anonymous archive entitlement. Missing service evidence does not erase the documented data licence, but prevents claiming an end-to-end proven access route. Reproducibility requires retaining selected historic file identities, index records and attribution rather than trusting a changing catalogue end date.

### UKV: reconcile channel-specific rights

The [current UKV ASDI registry](https://registry.opendata.aws/met-office-uk-deterministic/) specifically links [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.en); [Met Office's current external-channel page](https://www.metoffice.gov.uk/services/data/external-data-channels) points to that distribution. The [older planetary-scale description](https://www.metoffice.gov.uk/services/data/planetary-scale-applications-from-the-uk-met-office) instead describes CC BY-NC-ND 4.0 and a different service/retention design. **CONTRADICTED as a provider-wide uniform licence assumption.** Current exact-channel evidence supports the ASDI pathway, but pin its licence and resolve historical-object applicability before redistribution. Do not use an old non-commercial/no-derivatives statement to veto all UKV, or assume it has no bearing on a historic object.

CC BY-SA allows commercial use and sharing, with conditions on adaptations. Whether a numerical subset, transformation or combined scientific package is an adaptation, and how its licence interacts with other components, needs a bounded rights review. A licence for covered data does not automatically require the application's unrelated software to use that licence; neither does it establish compatibility of every proposed derived package. Preserve provider/Crown credit, licence link and modification provenance. No legal conclusion about derivative status is made here.

[DataHub terms](https://www.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/data/met-office-weatherdatahub-terms-and-conditions.pdf), especially §§3.2.1–3.2.2, describe different distribution restrictions. [DataHub products](https://datahub.metoffice.gov.uk/) and subscription conditions are alternatives, not the authority for the ASDI archive. Paid commercial application access does not imply reselling raw data or exporting a freely redistributable offline numerical package. Pricing, supported delivery, quotas and negotiated rights depend on the exact plan and are UNKNOWN here; no monetary estimate is quoted.

### MeteoSwiss forecast and observations

[OGD terms](https://opendatadocs.meteoswiss.ch/general/terms-of-use) cover the selected open products under CC BY 4.0 with source credit and no implied endorsement. Changes and scientific meanings must remain visible. Official warning products have additional presentation obligations and are **not selected** in WR002.

Free information does not make the service unbounded. The terms allow limiting excessive repeated access and reference upstream FSDI/CSCS conditions. Operational services take priority and delivery can be constrained during emergencies. No numerical request allowance, SLA or long-term forecast archive entitlement is established. The current forecast retrieval window cannot be stretched by technical polling without a separately approved retention/resource plan. Ground observations have different historical holdings and QC than forecasts; both need their own publication identities.

### MIDAS Open is not the restricted full MIDAS archive

The [exact hourly-weather v202607 catalogue](https://catalogue.ceda.ac.uk/uuid/d04207b551674c07801b7d4e6d883e50/) assigns OGL v3 and access to registered CEDA users. It is the open edition, not a grant for all full-MIDAS or third-party station collections. [OGL v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) permits commercial/non-commercial reuse with source acknowledgement and exclusions; the primary indexed text was available, while full-page retrieval returned 403. Record this retrieval limitation before a distribution review and capture the applicable provider attribution at acquisition. Registration is an access prerequisite, not permission to create an account in this task. Selected station files, metadata, QC and edition citations must travel together.

## Access and economic register

| Channel | Current / historical distinction | Authentication, charges and limits established | Unresolved operational burden |
|---|---|---|---|
| ECMWF open IFS/AIFS | Rolling current subset; not a retrospective archive | Free subset, published shared connection condition; full-service delivery can differ | Whole-world fields, ensembles, pressure levels, retries, retained cycles; archive service/entitlement costs |
| GFS NOAA / GDEX | Current/bucket history and named historical archive are separate routes | Anonymous NODD documented; GDEX access policy incomplete; no purchase made | Exact subset mechanism, wire bytes, index/file counts, update continuity and archive gaps |
| UKV ASDI | Rolling two-year archive; historical availability decays | Anonymous, unsupported; source fee not specified as paid; no numeric quota inferred | One-variable extraction may still require whole-domain objects; outage, rolling expiry and version changes |
| ICON OGD | Forecasts retrievable only briefly after publication | Free OGD, proportional service use; no authenticated session tested | Capture timing, coordinate/height files, ensembles, invalid-boundary mask and retained versions |
| ISD / GHCNh | ISD frozen legacy; successor required for current extension | NODD anonymous for legacy; successor's bulk route documented, no exact delivery conditions proved | Reference migration, QC/source flags, station history and contributor notices |
| MIDAS Open | Fixed cited annual edition and corrections | CEDA registration; OGL; actual quota/access response untested | Annual files rather than just chosen hours; updated QC and station metadata |
| SwissMetNet | Station/parameter-dependent historical/recent holdings | OGD terms, no numerical quota invented | Revision/QC timing, historical gaps and future retained snapshot identities |

Source charges, access fees and Meridian's processing/storage/transfer costs are different quantities. No tariff, account budget or production usage estimate has been invented. Cost of a future experiment is **UNKNOWN** until an authorised acquisition plan pins request/file counts and observed sizes. Worldwide operation is not costed by multiplying a tiny validation sample. Local-first work remains preferred.

Before any public or paid exposure, [F32](../../foundations/economics.md) requires source rights, service inventory, fixed/variable costs, ordinary/high-demand/abusive scenarios, user-approved budget/exposure ceiling, controls, alerts, ownership and safe suspension/recovery. Alerts are not hard caps. Retaining versions, archive redundancy, retries, logs and egress all need accounting. No source/provider choice passes that gate here.

Meridian's principle remains: do not charge merely for information/functionality that costs Meridian nothing to provide; transparent recovery of real licensed-data, processing, delivery or service costs is permissible. This report does not choose a business model.

## Gates before acquisition and distribution

Before **research acquisition**: exact product/edition, lawful route, permitted retention, source/version/time/grid identity, bounded resources, reference-QC suitability and explicit task authority. Before **application/offline distribution**: exact grants and exclusions, attribution bundle, adaptation/share-alike review, all downstream service terms, native software notices and financial gate. Research feasibility is not completion of either gate.

Most urgent rights gaps are historical ECMWF/TIGGE entitlements, historical UKV channel terms, GHCNh contributors/edition, and adaptation treatment of combined packages. They do not require rejecting documented GFS/UKV/MIDAS semantic-design opportunities. If any later selected route is restricted, change route/question or stop; do not substitute another product without recording the scientific and rights consequences.
