# Atlas portable read contract and reference-conformance fixtures

Recorded 9 October 2026. **REFERENCE CONTRACT AND FIXTURES ESTABLISHED**, bounded to
the existing desktop authority and retained Riffelhorn publications. No portable
reader, mobile validation or offline reliability is claimed.

## Checkpoint and scope

Required/observed start `984e7d2b8ebe3b3fe5a358ba7087af5a19d5f282`, public
`gbsamirahmed/project-meridian`, clean `main` / `origin/main`; fetched alignment 0/0.
No unrelated work, private access or canonical changes. The [frozen driver scope](../../scripts/atlas/read-conformance/README.md)
was written before implementation. Acceptance required at least 25 deterministic
diverse cases, authoritative generation, complete qualification equality, independent
replay, compact metadata, explicit errors and unchanged accepted evidence.

Read the committed Foundations decisions/engineering/platform and current summary,
prototype's proposed client boundary, mobile prerequisite gate, Atlas runtime types,
library/worker/catalogue implementation, Riffelhorn preparation/retrieval and existing
query tests. Reused the accepted native [matrix](../../scripts/atlas/riffelhorn-retrieval/matrix.json)
and [runtime cases](../../runtime/atlas/retrieval-cases.mjs); did not duplicate native
spatial/time predicates or implement a second scientific authority.

The user-authorised contract task advances foundational work without requiring a
phone or SDK. It does not resolve the [mobile gate](meridian-mobile-feasibility-gate.md)
or revise the negative Swiss/AWS reconciliation finding. F03/F12 gain a tested
reference boundary; their production/portable choices remain provisional. F04/F05/
F11/F16 retain their unproven physical-platform and offline requirements.

## Deliverables and retained inputs

- [Read contract](../atlas/portable-read-contract.md): versioned profile
  `meridian-atlas-read-contract/v1`, exact `retrieve` inputs/envelope and semantic obligations.
- [Manifest](../../fixtures/atlas-read/v1/manifest.json),
  [requests](../../fixtures/atlas-read/v1/requests.json),
  [expected answers/errors](../../fixtures/atlas-read/v1/expected.json),
  [shared documents](../../fixtures/atlas-read/v1/documents.json).
- [Generation/replay/test drivers](../../scripts/atlas/read-conformance/README.md):
  existing authoritative reads, complete envelope reconstruction, exact diagnostics,
  integrity checks, owned temporary catalogues and single-case replay.

The fixture uses the existing 4 km² native preparation revision
`357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb`:
12 retained inputs / 120,347,916 bytes, six raster supports and 38 native features.
Selected registration generations expose the existing 32 derived scalar results
alongside the native evidence; the legacy world exposes native sources without that
runtime derived state. No new source, method, observation or publication is created.

| Fixture pin | Exact generation | Purpose |
| --- | --- | --- |
| `before` | `65989736a06f72182fba9d9ad9d47955869f51ce943ef120effcad2df91352fd` | Before the accepted controlled source-qualification revision |
| `after` | `5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289` | After source correction and derived requalification |
| `legacy` | `7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8` | Accepted multi-region history with unknown knowledge acceptance |

These are published historical states. The two registration pins have 81 indexed
world records (49 native descriptors and 32 derived); legacy has 49. The corpus
queries Riffelhorn while retaining the authority's whole-world membership/region
documents. It is not an Exe or full Tryfan portable conformance claim. The controlled
qualification correction is administrative knowledge about real evidence, not a
fabricated physical event.

Manifest prerequisites enumerate exact public-data-relative input hashes/sizes,
prepared member hashes, publication members/fingerprints, reference source hashes
and tool versions. Physical locations are supplied by an uncommitted local config.
The existing receipt locators are documented discovery hints, not identity or a
fallback when a required pin is absent. The runner fully opens/validates each pin
and checks its fingerprint before comparisons.

## Coverage and observed semantics

**60 fixed cases:** 28 native cases reused from the 29-case preparation matrix;
the standalone `associated` flag becomes a rejection case because unified retrieval
does not implement it. Added scalar location/consumed support, method/source identities,
direct/transitive dependencies, CRS84, separate physical/knowledge selectors and
five historical cases. Nine cases expect rejection; 51 expect qualified answers,
including successful empty outcomes. Cases are not fabricated to meet quotas.

Raster seam and outer half-open edges, vector covered boundary, narrow/broad/partial/
outside area, latitude/longitude axis conventions, source family/product match and
mismatch, native WorldCover cell-centre counts, glacier survey versus release,
unknown epoch, derived discrete support and historical knowledge are preserved.
Source/preparation/method identity, raw input revisions, support/datum, lineage,
rights, limitations and uncertainty remain in every applicable complete envelope.

Two important contract limits are explicit:

1. Native source `revision` remains its preparation revision through a knowledge
   correction; qualified identity also needs publication, qualification and knowledge
   references. Historical slope value stays equal while its qualified revision changes.
2. Unified retrieval has a generic no-match gap even outside support; it has no
   top-level indeterminate outcome or universal capability operation. Unknowns reside
   in native qualifications. We preserved these actual results rather than adopting
   more precise standalone gap reasons or inventing application responses.

No new contradiction with accepted read semantics was observed. Positive raster
values are represented-heightfield samples, not independent validation of physical
truth. The current payload's explicitly unknown unit is preserved. Selected cases
do not encounter raster nodata; no artificial nodata observation was introduced.
Exact physical dates, standalone source-association queries, arbitrary algebra and
fully independent scientific verification remain outside this profile.

## Generation and reproducibility

Expected answers were obtained from `AtlasContext.scanEvidence`; every generated
case was compared with `AtlasContext.retrieve`. The existing `semantic` helper
excludes only top-level operational metrics. Object keys are deterministically
ordered, arrays and scientific values unchanged. Shared documents are stored once
with their original content identities; complete per-case envelopes rehydrate exactly.
No scientific qualification is summarised away to fit a portable reader.

Toolchain recorded by actual invocation: Node 24.11.0, Python 3.12.6, SQLite 3.45.3,
NumPy 2.5.3, rasterio 1.4.3/GDAL 3.9.3, Shapely 2.1.2, pyproj 3.7.2/PROJ 9.5.1,
Windows host. No installation or network acquisition. The generator initially hit
its 2 MiB metadata gate; compact serialisation and bounded combined scalar queries
kept all meanings and diverse cases within it before installing the final fixture.

Committed fixture bytes: requests 16,755; expected 902,437; shared documents 1,144,893;
manifest 10,872; **2,074,957 bytes total**, with 201 distinct response documents. No
source rasters, full geometry payload, SQLite catalogue, sensitive physical locator
or new binary is committed. Temporary catalogues are owned by the invocation and
removed after sessions close. Existing publications and the separate data repository
are read-only. This is test metadata, not a ready offline geographical package.

Exact configuration and generation/replay/single-case commands are in the driver
README. Future readers can consume the same request/expected files without the
desktop authority, but an independent reader has not been written in this task.
The 60-case corpus is finite; passing it does not prove every possible query.

## Validation record

Executed on the recorded desktop toolchain:

| Check | Actual result |
| --- | --- |
| Three fresh `run.mjs` processes | 60/60 each; 360 indexed/full expected-result comparisons; zero failures/skips; nine expected errors per run |
| Single historical case replay | `source-before-qualification`: 1/1; two comparisons, only its pinned context opened |
| Initial generation and independent regeneration | 60 scan/index agreements each; all four regenerated files byte-identical |
| New fixture tests | 12 passed, zero failures/skips |
| Existing `runtime/atlas/test-retrieval.mjs` | 92 passed, zero failures/skips; 135.96 seconds |
| Existing native `test_query.py` | 31 passed; existing NumPy/affine deprecation warnings |
| Six new driver modules | Syntax checks and explicitly configured ESLint passed, zero lint warnings |
| Repository lint and TypeScript build | Passed |
| Application-only Vite bundle | Passed; 113 modules, 1.24 seconds; existing large-chunk warning |
| Read-only preservation/navigation safeguards | 40/40 passed |

Commands for the new runner/tests are in the driver README. Existing regressions:
`node --test runtime/atlas/test-retrieval.mjs` and the configured GIS interpreter's
`-B -m unittest discover -s scripts/atlas/riffelhorn-retrieval -p test_query.py`.
Root lint used `npm run lint`; types used `node node_modules/typescript/bin/tsc -b`.
The application-only build deliberately omitted the external Weather-publication
materialisation plugin and public-directory copy, using an external output directory.
It is not a claim that the complete Weather/data build or all historical test suites
were rerun. No executable runtime or application code changed.

The preservation audit checked all 1,129 pre-existing tracked files outside the seven
append-only navigation files, 42 canonical status rows and 113 protected production
hashes against the starting checkpoint. It also rehashed selected retained Tryfan,
Riffelhorn source/preparation, Exe, multi-region, temporal and latest habitat/planning
worlds against the captured baseline. Frozen scientific contracts, accepted reports,
prototype plan and negative Swiss/AWS finding remain unchanged. Fixture seals, all
12 source-input fingerprints, regenerated bytes, new links/anchors, bounded file
scope, locators/credentials and whitespace were checked. An initially case-sensitive
wording check was corrected to recognise the existing “No top-level” sentence;
scientific expectations were unchanged.

The 12 new tests cover document reconstruction, values/unknowns/array order,
independent accepted boundary/time/identity anchors, supersession, lineage and
corruption rejection. They do not replace scientific-method validation. Missing
prerequisites or invalid authority are nonzero blockers, never skips or permission
to refresh expectations. No mobile, offline, renderer or independent-platform result
is claimed. No private access, data acquisition, canonical writes or infrastructure.

## Exactly one subsequent bounded task — NOT BEGUN

**MERIDIAN ATLAS PORTABLE READ-ONLY PROJECTION AND INDEPENDENT READER SPIKE.**

**Objective:** determine whether a small versioned read-only projection can satisfy
the accepted reference corpus without invoking Node/Python authority to answer each
query. This addresses semantic portability, not mobile performance or package readiness.

**Starting evidence:** this contract, exact fixture manifest, accepted canonical
Riffelhorn inputs/publications and unchanged scientific qualifications.

**Scope:** one bounded independently implemented reader and an explicitly identified
projection of the selected pins; use only retained evidence, preserve exact lineage,
coverage, rights, unknowns, times and unsupported outcomes. Start with the finite profile;
document any missing geometry/raster dependency honestly. Choose a test language or
storage representation only for the spike, without a final framework, native core,
production package or transport commitment. No private repository, mobile SDK,
new acquisition, endpoint, paid/cloud service or canonical writes.

**Deliverables:** projection identity/closure specification, independent reader,
conformance adapter, exact per-case comparison diagnostics and limits. Do not merely
dispatch requests to the reference runtime or look up precomputed expected answers.

**Acceptance:** all applicable 60 cases reproduce their unchanged complete semantic
expectations; any unsupported subset is explicit and cannot be labelled full profile
conformance. Qualifier loss or native boundary mismatch is a blocker, not permission
to weaken the fixtures. Historical pins and corruption/incompatibility rejection
remain explicit. No cross-platform/offline/mobile claim without corresponding evidence.

**Stop:** one bounded semantic portability result or precise blocker, documented and
reviewable; no production reader, mobile app, private restructuring or optimisation.
This subsequent task is **NOT BEGUN**.
