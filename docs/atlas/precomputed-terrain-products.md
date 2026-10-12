# Precomputed terrain products — bounded architecture proposal

**Current execution gate:** [pipeline recovery](contour-pipeline-recovery.md) preserves the source/product architecture, validates offline controls and proposes an unapproved genuine continuation. The earlier replay recommendation below is historical; no terrain delivery or new scientific processing is authorised by this document.

**12 October 2026. Proposed direction, no production implementation.** Build on accepted [terrain source/product meanings](terrain-source-product-architecture.md), [global evaluation](global-terrain-foundation-evaluation.md), [roadmap](../foundations/scientific-to-application-roadmap-decision.md) and the [synthetic contour recovery](contour-processing-memory-recovery.md). No database, host, permanent renderer or universal encoding is selected.

The working pattern is **sources → reproducible offline processing → stored geographical products → web/mobile rendering and lawful offline delivery**. Generate expensive derivatives once per source/method revision. Clients still decode tiles, render, interact and perform justified lightweight operations. This does not require precomputing every future scientific question.

## Minimum durable concepts

| Concept | Meaning and boundary |
|---|---|
| Original elevation source | Published/native evidence with asset hashes, release/acquisition qualifications, grid registration, CRS, height reference, DSM/DTM/other and rights |
| Qualified elevation product | Declared reconstruction/resampling of identified evidence with supported purpose, units, coverage, missingness and limitations. A single-source product need not be a reconciled mosaic |
| Reconciled elevation product | A **new** product only after justified coordinate/height/surface/epoch/overlap treatment and validation. Failed Swiss/global reconciliation remains failed; blending is not evidence |
| Derived contour product | Isoline approximations of one specified reconstructed field, levels/reference/interval/index, algorithm, nodata and generalisation lineage. A contour is not a scalar elevation API |
| Visual relief product | Precomputed hillshade imagery or qualified prepared DEM tiles used for lightweight client shading. Lighting/presentation is distinct from analytical height meaning; an unknown mosaic is not a qualified measurement source |
| 3D terrain representation | Heightfield-to-geometry or precomputed mesh/LOD with explicit height/coordinate semantics and approximation. Geometry remains present in 3D mode even at zero pitch; pitch never switches representation |
| Delivery tiles/package | Spatially partitioned/quantised/encoded assets referencing a scientific product. Container/zoom/buffer/decoder details do not redefine the height reference or improve source accuracy |

These are related product roles, not new app tabs, services or a plugin framework. Keep visual DEM selection independent from numerical elevation reporting. When pixel provenance/reference is unresolved, report that limitation or decline a numerical answer; do not read authoritative elevation from shading or a contour label.

## Practical manifest recommendation

Use a small versioned manifest next to immutable payloads. Its hash, supplied through a trusted publication/receipt, identifies its bytes; hashes alone do not authenticate a hostile replacement or prove terrain accuracy. Scientific processing identity and encoded delivery identity are related but distinct: repackaging the same validated geometry changes delivery bytes, not its source meaning. Include only relevant fields:

```json
{
  "manifestVersion": "research-example-1",
  "kind": "contours",
  "sourceRefs": ["qualified source/product identities and input-hash receipt"],
  "meaning": {
    "units": "m", "verticalReference": "LN02 / EPSG:5728",
    "surface": "DTM", "levelOrigin": 0, "interval": 10, "indexInterval": 100
  },
  "geometry": {"horizontalReference": "EPSG:2056", "dimensions": 2},
  "support": {"coverageRef": "retained-selection footprint", "validityRef": "nodata/support record"},
  "processing": {"methodRef": "code/version/parameter hashes", "transformRef": "none or explicit operation/grid hashes"},
  "generalisation": {"resamplingRef": "declared native or aggregate", "smoothingRef": "none or explicit", "simplificationRef": "none or validated candidate"},
  "qualification": {"accuracy": "unknown unless evidenced", "epochRef": "source acquisition qualifications", "validationReceiptRef": "actual outcome"},
  "rightsRef": "source/product licences, notices and redistribution obligations",
  "assets": ["relative path, role, byte length, checksum, encoding and partition references"]
}
```

This is an **illustrative proposed manifest**, not a schema, real accepted product or standards-conformance claim. Source references retain dataset/publisher/revision, sample spacing/registration, native CRS/height units, source hashes and known/unknown epochs. A transformation records authority, exact operation/grids and known/unknown accuracy. Product coverage is not observation coverage or valid scientific support. Acquisition, processing and publication times are separate. Rendering zoom and nominal grid spacing are not measurement accuracy.

No projected coordinates masquerade as longitude/latitude. In vector tiles, metric contour level remains an attribute qualified through the manifest; a vertical datum is not silently changed by an XY tile projection. Required notices travel with products/packages, not only the app footer. Product IDs are scoped; friendly names or a mutable URL are insufficient revision identities.

## Mixed resolution and source transitions

1. **Separate products:** maintain a qualified global fallback and regional products with independent reference/surface/epoch/support. Choose by geography, purpose, usable coverage and evidence; nominal resolution alone does not determine priority. Zoom may select generalisation within a product family.
2. **Reconciled mosaic:** undertake explicit reconciliation only where overlap and transformations justify it, with preserved contributors and tested boundaries. DSM/DTM differences persist after legitimate datum conversion; no universal offset or smoothness guarantee.
3. **Visual handoff/blend:** may be useful cartography after owner review, but does not reconcile heights. Preserve source-switch/gap meaning. Source-specific contours must not be snapped together merely because labels match.

Current Mapterhorn hillshade retains incomplete per-pixel lineage/common-reference qualifications. A new Swiss/Copernicus contour product cannot be called contours of that identical mosaic. Do not silently reuse a visual mosaic for numerical inspection. Sparse high-resolution tiles and overzoom add no new observations. Global Web Mercator delivery leaves a polar limit requiring an explicit later projection decision.

## Minimal processing and delivery route

Keep originals in existing authoritative external storage. For each bounded build: verify input identities/rights; declare reconstructed field and support; process coherent source-specific windows with filter halos and unique quad ownership; stitch/validate master contours; create identified generalisations; then partition for delivery. Never derive incompatible contour geometry separately on each client or independently simplify shared edges in neighbouring tiles.

The next delivery proof, **after genuine contour acceptance and separate scope approval**, would take one stored contour product and produce a tiny vector-tile set at a few declared zooms. Preserve level/source/product/index attributes and feature identity; choose projected quantisation precision, buffers and clipping rules; decode independently and test boundary continuity, displacement, duplicate labels and feature IDs. Labels are a rendering problem with tile buffers/cross-tile coordination, not evidence of height accuracy. This is a route, not a second recommended current task.

Raster elevation/relief pyramids need declared resampling, shared edge samples/gutters, missing-support semantics and encoding error. Coarse levels must not quietly change source/height meaning. Precomputed height tiles plus lightweight client mesh generation may be adequate for future 3D; precomputed meshes merit a separate bounded test if evidence demands them. No mesh or hillshade processing is added now.

| Delivery option | Suitable role | Constraints to validate before adoption |
|---|---|---|
| Individual vector tiles (MVT-style encoding) | Contour geometry/attributes, spatial requests, straightforward initial decode proof | Quantisation/clipping/buffers/IDs/labels; tile coordinates are not source CRS; many objects/requests; no inherent complete scientific manifest |
| PMTiles-style archive | Immutable vector/raster tile container, potentially HTTP range delivery and downloadable regions | Range/CORS/caching support and actual archive/runtime compatibility; native/WebView adapter and interruption/recovery tests; archive is not source semantics or an automatic offline right |
| MBTiles-style archive | Local tile container using SQLite; candidate for device region access | Native access/adapter and browser delivery differ; tile-row conventions versus XYZ must be handled; no new database/plugin adopted; container does not make raster/vector meanings identical |
| Terrain raster tiles | Prepared heights for shading/geometry, existing MapLibre-compatible delivery candidate | Quantisation, CRS, borders, nodata and ceilings; Terrarium/other encoding does not prove datum or accuracy; visual lossless encoding still differs from source evidence |
| Native raster/master contour files | Reproducible scientific baseline and processor interchange | Useful offline authority/reference; not automatically an efficient interactive phone-delivery format |

No new format library, licence review, provider request or interoperability proof occurred. Format characteristics here are conceptual options, not current endpoint capabilities. A future archive can contain one product without becoming a universal terrain/Weather format.

## Versions, offline operation and cost

Store immutable product/delivery versions with manifests, byte hashes and validation receipts. A small current/catalogue pointer may select a version only after validation; readers pin one coherent version. Updating a source, vertical operation, reconstruction or smoothing creates new lineage; packaging/encoding creates a new delivery revision. Retain explicit dependencies to avoid invalidating unrelated products. Do not make latest-only URLs authoritative or overwrite a published package during download.

Offline regions require selected manifest closure, actual rights/notices, byte/storage budgets, integrity checks, staged download, interruption handling, atomic activation appropriate to platform storage, restart/recovery and update/retirement rules. Their tests require web/Android evidence and owner approval later. Neither a private app nor a container grants redistribution permission. Existing limited OpenFreeMap/Mapterhorn trials authorise no archive or new requests.

Costs divide into **build costs** (source acquisition/licensing, retention, CPU/RAM/scratch, derivation/generalisation/validation) and **recurring costs** (stored versions, delivery/egress/requests, downloads, cache misses, updates, monitoring and recovery). Fine regional coverage and multiple generalisations can dominate volume; compression, selected extents and reuse reduce it but must not erase qualifications. The synthetic Riffelhorn-sized workload is not a worldwide cost estimate. No paid infrastructure was created. Public exposure requires measured representative workloads, rights clearance, credible storage/egress budgets and spend/request safeguards.

## Relationship to Weather and current application

The historical [numerical Weather architecture](../global-weather-architecture.md) demonstrates preprocessing, manifests, immutable run/time identities and bounded lightweight client consumption. Its old frontend details are historical, not a migration instruction for the new app. [WR013](../research/weather/scientific-field-packaging-offline-replay.md) independently separates source encoding, interpreted field, packaged subset and replay, preserving integrity and qualification offline.

Reuse those principles, plus the [external-storage boundary](../architecture.md#repository-and-external-storage-contract). Do **not** force forecast-time scalar arrays, vector contours and terrain meshes into one encoding/grid/lifecycle. Terrain revisions/acquisition support differ from forecast issue/valid/interval semantics. An existing local query-catalogue decision is not a decision to introduce a production global terrain backend.

The private application's OpenFreeMap/Mapterhorn, flat geometry, UI, lifecycle, loaders and bundled/live profiles remain unchanged. No source-aware resolver, download UI, elevation inspector or 3D mode is implemented. **Current next gate: approve the unchanged genuine contour replay described in the memory recovery record.** Production formats, hosting, reconciliation, rendering appearance, global costs and offline/device suitability remain deferred.
