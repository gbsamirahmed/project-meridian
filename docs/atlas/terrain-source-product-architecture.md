# Atlas terrain source and product architecture

Decision date: 2026-10-03. Status: **accepted metadata foundation; no resolver or
production adoption**. Baseline: `6d36b460008495757689e466de6af830a980bf47`.

This decision turns completed integration evidence into an Atlas data model.
It does not accept a reconciled surface, make the research crop a seamline,
establish a new terrain provider, or prescribe a blending algorithm.

## Empirical requirements

**MERIDIAN EVIDENCE (M)** means the identified experiment supports the requirement,
not that the model or any eventual regional architecture was itself tested there.

| Requirement | Evidence that exposed it | Model response |
| --- | --- | --- |
| Separate numeric analysis from visual experiments | [Policy separation](../architecture.md); source substitutions left route sampling AWS | Metadata beside production; no sampler/config imports |
| Separate published source from derived delivery product | [Direct Swiss prototype](riffelhorn-regional-terrain-prototype.md): four official TIFFs became a resampled encoded pyramid | `TerrainSource`, `TerrainProduct`, source/product references |
| Preserve authority, release and input identity | Direct prototype retained official hashes, acquisition records, processing versions | Source assets, revisions, rights and product build record |
| Admit incomplete upstream lineage | [Global evaluation](global-terrain-foundation-evaluation.md): catalogue candidates are not per-pixel winners; [reconciliation](riffelhorn-terrain-reconciliation.md): AWS header identifies EU-DEM input but not complete ingestion | Contributor-list completeness separate from spatial mapping |
| Distinguish coverage and legitimate support | Reconciliation controls needed kilometre-scale support unavailable in 2 km crop | Separate source coverage, product coverage, valid support, protected interior and transition support |
| Do not encode research rectangles as universal seamlines | Reconciliation: arbitrary west/south joins failed; controls reshaped terrain | Spatial roles describe assessed support; no source-priority/geometry selection algorithm |
| Preserve resolution distinctions | Global evaluation: 512 pixels/sparse high-z children do not imply globally fine terrain; direct 0.5 m grid does not imply measurement accuracy | Grid spacing with CRS/units, nominal and measurement descriptions, separate delivery zoom and scoped information ceiling |
| Preserve vertical and terrain-surface semantics | Swiss LN02 DTM versus incompletely established hosted AWS; Swiss/AWS differences change sign | Explicit known/unknown references, DTM/DSM/heterogeneous/other/unknown, heterogeneous product heights |
| Retain epoch uncertainty | Swiss release 2024 incorporates 2021/22 LiDAR and 2023 updates; no cell-level epoch | Acquisition basis/interval separate from release and generation timestamp |
| Model contribution without inventing confidence | Prototype masks select inputs; reconciliation controls generated weights | Optional contribution-mask reference and interpretation, not quality score |
| Keep fallback distinct from preferred coverage | Mapterhorn sparse fine children/coarse parents; Swiss evaluation falls through to AWS | Described availability plus optional cross-product fallback relationship |
| Version builds and preserve mutable-service limits | Direct frozen build reproducible; public service URLs do not pin content | Stable ID, revision/version knowledge, asset hashes and build records |
| Preserve rights beyond UI credit | Global evaluation: software BSD does not license all contributors | Source/product terms and attribution separate from renderer string |
| Support current single-source heightfield consumption without deciding the resolver | Direct prototype required a composed endpoint; MapLibre does not blend arbitrary DEM sources | Data semantics independent of delivery adapter and representation |

The reconciliation result remains negative: neither the 250 m feather nor adaptive
overlap is accepted. Broad, mixed-frequency disagreement, sign changes and unknown
hosted height semantics prevent treating it as one constant offset. The new model
records those limitations; it does not make them disappear.

## Bounded external metadata review

**EXTERNAL EVIDENCE (E)**, consulted 2026-10-03. We borrow established concepts,
not a claim of STAC, ISO, OGC or PROV conformance.

- [STAC Item 1.1.0](https://github.com/radiantearth/stac-spec/blob/v1.1.0/item-spec/item-spec.md)
  distinguishes item identity, footprint, bbox, time and assets. A bbox indexes an
  extent; it is not automatically the supported footprint. A combined observation
  need not have one precise acquisition instant.
- [STAC Projection 2.0.0](https://github.com/stac-extensions/projection/blob/v2.0.0/README.md)
  uses authority CRS identifiers and separates asset projection, footprint, shape
  and affine transform. We use authority identifiers where established, and keep
  native projected coordinates explicitly separate from geographic footprints.
- [STAC Raster 2.0.0](https://github.com/stac-extensions/raster/blob/v2.0.0/README.md)
  separates units, nodata, sampling, scale/offset and pixel spatial resolution.
  These are useful delivery/raster concepts, not proof of measurement accuracy.
- [STAC Processing 1.2.0](https://github.com/stac-extensions/processing/blob/v1.2.0/README.md)
  records lineage, software/version and processing time separately. Atlas retains
  meaningful process parameters and a build-record reference rather than embedding
  a workflow engine.
- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)
  distinguishes entities, activities and derivation. Source/product references
  and processing steps are enough here; no graph store or generic provenance
  execution system is justified.
- [RFC 7946, sections 3–5](https://datatracker.ietf.org/doc/html/rfc7946)
  defines GeoJSON longitude/latitude footprints in WGS84/CRS84. Atlas restricts
  these footprints to 2D. LV95 is not encoded as GeoJSON, and LN02 heights are not
  placed in GeoJSON's optional ellipsoidal-height coordinate.

National source semantics, rights and EPSG identifiers come from the retained
[Swiss acquisition/prototype record](riffelhorn-regional-terrain-prototype.md).
We do not reverify providers or conduct a general standards survey here. ISO-style
lineage/quality concerns are reflected through these accessible primary models;
no ISO compliance is asserted. 3D Tiles metadata is unnecessary for this heightfield
foundation and was not adopted.

## Terminology and ownership

| Term | Meridian meaning |
| --- | --- |
| Terrain source | Upstream observed or published elevation dataset, optionally an explicitly scoped retained input selection of that dataset |
| Terrain product | Derived representation for Atlas use/delivery, possibly external, heterogeneous, non-tiled or incompletely understood |
| Terrain representation | Form Atlas consumes/renders in a stated context; current explicit form is raster-DEM heightfield |
| Source coverage | Where the described dataset/input selection contains data; scope must be stated |
| Product coverage | Footprint of this prepared/delivered product; not automatically its contributors' observation footprint |
| Valid support | Area with an identified assessment for a stated purpose; footprint alone does not establish suitability |
| Protected interior | Optional supported area whose preferred terrain should remain unmodified during reconciliation |
| Transition support | Optional area of legitimate overlapping support available to evaluate reconciliation; not just an opacity collar |
| Fallback | Another product used under described conditions; does not expand preferred source observations |
| Contribution / lineage | Immediate contributors, transformations and (where available) spatial contribution; completeness at one level does not establish full upstream lineage |

Types, focused validation and evidence examples live in
`src/atlas/terrain/metadata/`. They import neither React nor MapLibre, Weather,
Traverse or App. No production module imports them. They are an owned architectural
foundation, not a service registry. App still orchestrates numeric sampling;
Traverse receives provider-neutral terrain profiles.

`src/atlas/map/visualTerrainConfig.ts` remains the operative visual policy;
`src/atlas/terrain/analyticalElevationConfig.ts` remains independently AWS z15/256.
The model may eventually describe either policy's data, but this task creates no
analytical dependency. Changing metadata does not change map behavior.

MapLibre consumes delivery through a future explicit adapter, not by interpreting
these semantic records today. Delivery CRS, encoding and dimensions belong to a
product. IGOR direction/strength/colors, atmosphere, exaggeration, camera and
projection policy belong to visual rendering. Renderer ceilings z14/z15 are not
evidence of native source resolution. The minimal representation reference records
product and context only; no speculative mesh/material hierarchy is introduced.

## The implemented model

`Knowledge<T>` is either `known` with a value or `unknown` with a reason. Critical
unknowns stay explicit. Optional fields are not a hidden assertion of certainty:
an omitted optional assessment/process detail is unrecorded/not applicable; use
`unknown` where a specific unresolved question matters. No quality, accuracy or
datum default is inferred from a provider name.

### Source

`TerrainSource` retains stable ID/name, publisher, dataset/release/revision,
surface semantics, horizontal/vertical references, units, grid/nominal/measurement
information, acquisition description or interval, scoped coverage, nodata, optional
quality, rights, documentation and optional hashed assets. A release is not a
download date. Asset hashes identify bytes; they do not prove measurement accuracy.

Only a useful core is required; detailed quality, assets, intervals and registry
codes are optional. Text descriptions are intentional for evidence that cannot
honestly be reduced to one number. A known grid spacing carries units and CRS;
it is not a globally meaningful ground-resolution scalar.

### Product and provenance

`TerrainProduct` retains stable ID plus version/revision knowledge, producer,
surface and vertical semantics, units, lineage, delivery, source-information
description/ceiling, spatial roles, nodata, optional fallback, rights, generation
time/build record and references. A product can contain source and product
contributors. Unknown upstream contributors are represented by an incomplete or
unknown list, including an empty list where nothing complete is established.

Lineage records contributors, completeness (`complete`, `partial`, `unknown`),
spatial mapping (`mask`, `catalogue-only`, `unavailable`), processing steps and
limitations. Complete means complete **immediate** contributors within the stated
product scope. Mask references identify contributors and interpretation; a weighted
mask may be added later without pretending weights express confidence. Scientific
process parameters, software versions and original build records survive without
duplicating large manifests. This is not a DAG database or automatic inheritance
of licence/CRS claims.

Delivery distinguishes raster tiles, raster files, a described other form, and
an explicitly unknown contract. Output horizontal CRS can remain unknown.
Tiles carry CRS, XYZ/TMS scheme, dimensions, encoding, format, template, delivery
zoom, availability and resampling. Encoding is named/described rather than limited
to Terrarium. Unknown hosted maxzoom is permitted. Sparse children and same-product
parent search are availability behavior; cross-product fallback is a separate
optional reference. Neither is an automatic resolver instruction.

Version, immutable revision and generation time remain distinct. A prepared build
can be immutable while an endpoint's fallback service is mutable. A software commit
does not pin a hosted tile collection. A future adapter/cache must explicitly bind
revision identity; this task does not change existing cache keys.

### Spatial support

Areas can be 2D GeoJSON Polygon/MultiPolygon footprints, explicit native-CRS
rectangles, or asset references to masks/footprints/tile inventories with CRS and
interpretation. The last form avoids manufacturing a complex footprint from a
rectangle or requiring GIS operations in browser metadata.

Source coverage has dataset versus retained-input-selection scope. Product coverage
and the three optional/assessed support roles remain independent. A projected
rectangle may be an exact selected input footprint; its reprojected envelope must
not silently become exact valid support. Asset-backed geometry needs its referenced
interpretation, not just an unlabelled path. No containment, overlap feasibility,
topology repair, reprojection or seamline algorithm is implemented. Future support
assessments must verify those relationships explicitly.

### Resolution, vertical and surface semantics

Grid spacing, nominal resolution, measurement resolution, delivery tile dimensions,
delivery zoom and source-information ceiling are distinct fields/concepts.
Effective rendered detail also depends on the mesh and view and is not invented
as a product-wide metre value. Overzoom/resampling is documented processing, not
new source observations. Encoding increment is storage precision, not accuracy.

Sources have known/unknown vertical references. Products additionally distinguish
known, preserved, transformed, heterogeneous and unknown height semantics.
Transformation metadata requires source/target references, method, accuracy
knowledge and limitations. Processing may reference the same transformation.
No transformation is executed; matching two CRS labels alone proves no physical
reconciliation. Units remain separately explicit. LN02 is not EPSG:3857.

Surface kinds are DTM, DSM, heterogeneous, other (with description), and explicitly
unknown. Neither mixed vertical references nor mixed DTM/DSM surfaces become one
apparently precise height/datum label.

## Fit to the four retained cases

All examples are typed metadata snapshots, not production provider settings.

| Case | How represented | Important retained uncertainty |
| --- | --- | --- |
| AWS production visual terrain | Hosted external derived product, 256 px XYZ/3857 RGB PNG Terrarium; nominal delivery footprint, mutable revision; current configuration linked | Complete contributors, hosted height reference, nodata and current full zoom contract unknown; Riffelhorn EU-DEM header is a scoped hint |
| Direct swissALTI3D | Source record explicitly scoped to four retained 2024 files, each hash retained; LV95/LN02, metres, 0.5 m distributed grid and observation basis | This selection is not national coverage; cell-specific epoch, support/accuracy and measurement resolution unknown |
| Riffelhorn v1 | Immutable prepared product/build identity, Swiss source plus AWS product, binary contributor masks, GDAL reprojection/resampling/encoding, prepared-tile coverage and AWS fallthrough | Heterogeneous heights; accepted valid/protected/transition support unresolved; 37 frozen inputs do not freeze the global fallback endpoint |
| Mapterhorn evaluation | External heterogeneous product with a **partial** list of relevant GLO-30/Swiss/Wales contributors and catalogue-only spatial mapping; 512 px XYZ Terrarium WebP | Sparse fine coverage, common vertical normalization, point contributor, revisions, aggregate rights and service commitments remain incomplete |

Riffelhorn's four input hashes, prepared identity, manifest checksum, dimensions,
zoom and precision are cross-checked against the existing lightweight canonical
record. It references the unchanged original manifest for full toolchain, input
receipts, frozen AWS inventory and generated file hashes. No source or product was
accessed/regenerated for this task. The old experimental manifest is not retrofitted
to the new model, and no duplicated tile pyramid enters Git.

Riffelhorn v1 records LN02 only for Swiss pixels. The originally demonstrated
interior benefit does not justify declaring the whole research AOI valid support.
Its undefined support fields are important negative evidence, not missing polygons
to fill in by guessing. Mapterhorn is described as a product, not an invented single
upstream dataset or production dependency.

## Validation and practical limits

`terrainMetadataValidation.ts` checks owned typed records: reasons for unknowns,
checksums, finite/positive grid and tile dimensions, delivery zoom, encoding
increment, basic 2D footprint/ring conventions, mask contributor references and
vertical-transform essentials. It is not an untrusted-JSON parser, a full metadata
schema validator, a GIS topology validator or suitability/rights clearance.

Twelve focused semantic tests cover unknown heights, distinct grid/zoom concepts,
canonical input/build identity, immediate lineage and masks, independent spatial
roles, fallback without coverage expansion, partial catalogue provenance, recorded
vertical transformation, non-tiled/preserved output, GeoJSON/native separation,
invalid numeric/checksum contracts and repository reference integrity. Spatial and
transformation fixtures are explicitly synthetic, not new Riffelhorn support decisions.

Reproduction, from repository root:

```powershell
node --test scripts/atlas/test_terrain_metadata.mjs scripts/atlas/test_terrain_policies.mjs
npm.cmd run lint
npx.cmd tsc -b
```

The normal application build/test results for this decision are recorded in the
development log. Normal tests have no metadata dependence on a live provider,
external terrain estate or Swiss tile server. Production configuration/pipeline,
Weather and Traverse are unchanged; no application startup dependency is added.

## Deferred decisions and smallest next step

**RESEARCH HYPOTHESES / DIRECTIONS (H)**: this foundation supports a later
preprocessed harmonized delivery hierarchy, but does not choose it, source priority,
quality ranking, resolver logic, interpolation, seamline, contribution encoding,
vertical transformation, service hosting, cache adapter or provenance UI. It does
not justify datum fusion with AWS or promise that more support alone solves it.

The smallest justified next implementation is a **larger Riffelhorn Swiss support
selection and unreconciled visual product, driven by these metadata concepts**.
Before acquisition/generation, define the desired protected interior and purpose,
document an outer support selection in the native CRS, and record available epoch/
quality/stable-terrain evidence and the unknown AWS reference. Size support from
those requirements and the measured disagreement; the earlier 2.21 km percentile
is a diagnostic, not an automatic acquisition width or accepted transition.

Then, in a separately authorized task, acquire only that bounded official Swiss
selection, retain its asset identities, and prepare a versioned height-preserving
product with contribution/support records. This would exercise source selection,
spatial roles, revision and lineage on real inputs without first accepting blending.
Reassess overlap and physical height semantics before a reconciliation decision.
That prerequisite is explicit: unknown AWS semantics remain a barrier to claiming
a physically harmonized product, even if a future visual continuity treatment is
evaluated. No acquisition, larger preparation or experiment occurs here.
