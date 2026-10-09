# Atlas portable read contract — reference profile v1

Profile identifier: **`meridian-atlas-read-contract/v1`**. Established 9 October 2026
against unchanged public reference code at `984e7d2b8ebe3b3fe5a358ba7087af5a19d5f282`.
This specifies tested read obligations, not a production API, mobile implementation,
new scientific authority or offline package format. See the [reference fixtures](../../fixtures/atlas-read/v1/manifest.json),
[commands](../../scripts/atlas/read-conformance/README.md) and [evidence report](../research/atlas-portable-read.md).

## Authority and operation boundary

Canonical qualified evidence, retained source/preparation records, immutable component
membership and committed filesystem publication history remain authoritative. SQLite
and portable projections are rebuildable read representations. A projection must retain
the selected scientific identities and qualification documents; it cannot publish,
repair, reinterpret, fabricate missing evidence or silently switch generations.

The smallest tested evidence operation is **`retrieve(query)`**, corresponding exactly
to `AtlasContext.retrieve(EvidenceQuery)` and returning `EvidenceAnswer`. Identity
inspection is this operation with `identity`; lineage inspection uses `relatedTo`.
There are no new `inspect`, `capabilities`, `view`, `renderings` or document-write
operations. The earlier prototype's proposed operations remain proposals, not runtime
features established here.

For the desktop reference, `openAtlas(RuntimeConfig)` opens and fully validates one
committed generation; `buildCatalogue({qualified:true})` makes a disposable index;
`scanEvidence(query)` is the diagnostic full-scan reference; `close()` releases the
worker. They are existing reference lifecycle calls, not requirements that a mobile
reader run Node, Python or SQLite. A future implementation may initialise a validated
read-only projection differently, but must bind every read to an explicit published
generation before answering. File locators and interpreter paths are reference setup,
not portable scientific identity. Generation selection is **not** a query predicate.

## Inputs in the Riffelhorn profile

Use structured finite values, not SQL or a new query language. The exact source type
is [EvidenceQuery](../../runtime/atlas/types.ts). This profile exercises the following
subset; accepting another field in the desktop runtime does not establish portable
conformance for that field.

| Field | Type / observed semantics |
| --- | --- |
| `region` | `"riffelhorn"` for this profile. Required for spatial selection; it does not fuse regions. Existing responses still carry whole-publication membership and regional references |
| `identity` / `feature` / `product` | Nonempty exact strings. Feature identities are source-scoped, not invented from coordinates; scalar results do not acquire feature IDs. Product selects the native prepared product or method selector, retaining its own meaning |
| `families` | Nonempty list of supported families. Tested native families: `dtm`, `dsm`, `worldcover`, `geocover-bedrock`, `geocover-unconsolidated`, `glaciers`, `debris`; derived: `terrain-slope`, `planar-area-ratio` |
| `evidenceClass` | `"source"` or `"derived"`; source includes prepared native representations, not a claim of direct observation |
| `representation` | This profile uses `"vector"`, `"raster"`, `"local-scalar"`. Other runtime types are not portable capabilities proved by this corpus |
| `point` | `[x,y]`, two finite numbers |
| `area` | `[minX,minY,maxX,maxY]`, finite ordered bounds with positive width/height. Point and area are exclusive |
| `crs` | Explicit `"EPSG:2056"`, `"EPSG:4326"` or `"OGC:CRS84"` with point/area. The accepted adapter uses always-xy, so geographic inputs are longitude/latitude; do not silently reverse them. No inferred CRS or vertical transformation |
| `spatialSupport` | `"location"` (default scalar anchor) or `"consumed"`; consumed selection requires derived class and spatial predicate. A scalar location is not a continuous slope surface |
| `time` | `{role:"evidence-epoch"|"product-reference", start:integerYear,end:integerYear}` with inclusive ordered years 1–9999, or `{role:...,unknown:true}`. No exact physical date, open interval, interpolation or inferred observation timestamp |
| `revision` | Exact lowercase 64-hex revision where supported by the runtime. The selected revision type depends on evidence class; this corpus preserves returned revision fields but does not exercise every revision-filter form |
| `knowledge` | `{revision:64HexRegistrationRevision}`; `{start:UTCInstant,end:UTCInstant}` with closed ordered UTC millisecond timestamps such as `2026-10-09T02:07:06.400Z`; or `{unknown:true}`. Knowledge acceptance is not observation/source time |
| `relatedTo` | `{identity:string,direction:"inputs"|"dependents",depth:"direct"|"transitive"}`. Requires an existing seed in the pin; missing seed is an error, not inferred empty lineage |

Combined predicates retain conjunction semantics and the native family-specific
selection meaning. The fixture has negative tests for unsupported family/CRS, inferred
CRS, physical date precision, ambiguous time, open knowledge interval, arbitrary SQL
and the standalone preparation reader's `associated` field. That field is not accepted
by unified runtime retrieval; derived dependency traversal is not a replacement for
source-native glacier association semantics.

There is no promise of general polygon algebra, antimeridian handling, arbitrary
projection pipelines, cross-source fusion or all possible query combinations. Exe
`waterTime`/`referenceTime`/classification predicates and Tryfan queries are outside
this Riffelhorn profile. Unsupported capability must not be advertised from a type
union alone.

## Native spatial and temporal obligations

The applicability core is 4 km², EPSG:2056
`[2624000,1091000,2626000,1093000]`; native full-feature support may extend beyond it.
The accepted reader transforms query areas using densified boundaries (32 segments
per edge), intersects core applicability and checks exact native support. A portable
bounding-box index alone cannot establish scientific matching.

Vector point matching includes covered boundaries; vector area requires positive-area
intersection. Raster point selection is native affine half-open row/column membership:
the DTM seam selects one tile, while maximum-x and lower-y outer edges may select no
cell. Height areas return conservative support/window descriptors, not an aggregate
height. WorldCover area results count native cell centres, not physical fractions or
confidence. Derived location matching uses discrete anchors; consumed support uses
the explicitly recorded native stencil cells and half-open point boundaries.

Preserve Swiss DTM/LN02 versus Copernicus DSM/EGM2008, source/provider datum lineage,
native classifications, nodata and uncertainty. There is no datum harmonisation or
Swiss/AWS terrain blend. A returned height sample's unit is explicitly unknown in the
current payload envelope even where provider context supplies further information;
do not silently rewrite that field. The complete qualifications remain available.

`evidence-epoch` and `product-reference` are selectors over source-native qualified
calendar-year descriptors, not interchangeable physical-time axes. Glacier survey2015
and release2020 differ; WorldCover nominal2021 is a classification epoch, not a dated
observation of current cover. Swiss mixed acquisition support does not establish a
cell-specific epoch. Derived epoch and product-reference years remain unknown; method
and execution identity do not supply them. Registration acceptance clocks, source
publication, preparation time and Atlas publication generation remain distinct.

## Result envelope and identity

Successful retrieval preserves the existing schema **`atlas-qualified-retrieval/v1`**:

- `generation`: the exact committed pin; `members`: explicit component-kind → identity map.
- `results`: ordered `EvidenceRecord[]` with `key`, `identity`, `revision`, source/derived
  class, region, family, representation and `componentIdentity`.
- Each record preserves `support`, `temporal`, `evidenceRef`, `qualificationRef`,
  `provenanceRef`, `rightsRef`, nullable `knowledgeRef` and `relationshipRefs`.
- `documents`: content-identified authoritative response documents. These include native
  fields, definitions, limitations/uncertainty, source and preparation inputs, rights/
  attribution, registration knowledge and derived method/parameters/execution references.
- `relationships`: explicit `identity`, `from`, `to`, `kind`, `fromRevision`, `toRevision`,
  `via`. Source-consumption edges retain raw artifact/qualified-use identity; those
  revision fields are not necessarily the prepared revision returned on a source record.
- `regions`: native and nullable knowledge document references; `traversal`: null or
  the original relationship selection and exact traversed edge IDs; `gap`: null or
  the actual qualified no-match descriptor; `metrics`: operational diagnostics.

The fixtures compare every field above except top-level `metrics`. No source dates,
knowledge clocks, native fields, provenance, units, coordinates, values, rights,
uncertainty or limitation text are omitted or rounded. Referenced source geometry
remains a locator/selector/hash when that is what the reference returns; this corpus
does not embed the full geometry payload or imply it can execute arbitrary queries
without that payload.

A native source's `revision` is the preparation revision, and may stay unchanged
through a knowledge-only qualification correction. The qualified response must also
preserve its pin, qualification reference and knowledge reference. Do not identify
the entire interpreted claim only by `(identity, revision)`. Derived numerical values
may remain equal while their qualified output revision changes. Supersession is
knowledge history, not a claim of physical-world change.

Traversal returns only explicit authoritative relationships. Filtering returned
records does not necessarily reduce the transitive traversal's edge set; retain the
actual response. A relationship endpoint may therefore require another identity
read in the same pin rather than appearing as a fully hydrated record in that answer.
Do not infer extra relationships from overlap or matching property names.

## Unknown, absent, unsupported and failure

Unknown qualification is retained as the authoritative unknown state or nullable
knowledge reference. It does not match every finite time filter. A successful empty
answer has `gap:{reason:"no-matching-qualified-evidence",physicalAbsenceInferred:false}`.
The unified runtime uses this generic reason even for outside-support queries; the
standalone preparation reader has more specific gap reasons. Do not retrofit those
reasons into these expectations. An empty result proves neither physical absence nor
scientific completeness. No top-level `indeterminate` union variant is emitted by
this interface: indeterminate scientific knowledge is exposed in qualifications.

Rejected reference calls throw `AtlasError` with exact `code` and `message`. The corpus
observes `query-invalid` for eight malformed/unsupported predicates and
`relationship-missing` for an absent relationship seed. This common `query-invalid`
code does not independently distinguish every invalid input from unsupported
capability. The harness records `{kind:"error",code,message}` without stack traces;
this wrapper is test serialisation, not a new scientific response schema. Expected
rejection is a passing conformance case, never a skip or a fabricated empty answer.

Publication-open, missing retained input, canonical-integrity and catalogue failures
remain failures. Full authoritative validation is the reference default. No catalogue
or pin fallback is allowed; a portable implementation must report unavailable or
incompatible state rather than answer from another generation. This corpus tests
read outputs, not every storage/corruption or publication failure path; the existing
runtime regression tests retain those responsibilities.

## Versioning and fixture representation

The v1 manifest fixes exact pins, reference source fingerprints, tool versions,
12 input identities, preparation hashes, requests and expected-member checksums.
Each case binds one pin and can be replayed alone. Expected outcomes are generated
through `scanEvidence` and checked against `retrieve`; they are never handwritten.
The generator has no update-in-place mode and writes only a new external directory.
Review/version any changed meaning or reference input; never auto-refresh a failing
expectation. A source-code fingerprint mismatch requires review, not weaker equality.

This reference fixture uses deterministic compact JSON, sorted object keys, unchanged
array order and exact finite values. Shared document bodies are stored once in
`documents.json`; each expected answer lists its document references. Rehydration
restores the entire original semantic envelope. Document IDs use the accepted
canonical identity encoder; file checksums cover the exact committed compact bytes.
Checksums establish consistency, not a trust/signature or redistribution licence.

JSON, this storage layout and diagnostic wording are v1 reference artefact choices,
not mandatory production transport, mobile persistence or offline-package formats.
Semantic equality is tested here on the accepted toolchain. A later cross-language
reader must preserve numeric meaning and justify any tolerance separately; this task
introduces no tolerance or representation-based scientific simplification.

Not established: an independent portable implementation, mobile query performance,
offline closure/recovery, renderers, universal client capability discovery, exact-day
physical filtering, raster nodata examples at these selected queries, or conformance
on another OS/toolchain. See the report for the precisely bounded next task.
