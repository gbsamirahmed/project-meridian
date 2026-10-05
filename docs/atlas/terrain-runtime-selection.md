# Atlas terrain runtime selection — first slice

Implemented against the frozen [Terrain Hierarchy Contract](terrain-hierarchy-contract.md), baseline `53d75f2`. This is a registry, pure selector and delivery adapter. It does not establish a reconciliation method or activate regional terrain in production.

**MERIDIAN EVIDENCE:** focused runtime tests cover canonical registration, support/scale eligibility, parent reuse, handoff/fallback, provenance, immutable reuse and production equivalence. Existing rendering and analytical policy tests remain active. Historical terrain findings remain in their completed reports.

**EXTERNAL EVIDENCE:** no new research or source acquisition. The canonical AWS service metadata retains existing attribution and unknown lineage, vertical reference, information ceiling and assessed global support.

**RESEARCH HYPOTHESES / DIRECTIONS:** the bounded Wales/Tryfan proof remains next. Its real source/support/height/licence declarations must be established separately. No synthetic fixture establishes those facts.

## Ownership and API

| Module | Responsibility |
| --- | --- |
| [Registry](../../src/atlas/terrain/runtime/terrainRegistry.ts) | Validate and freeze a snapshot of canonical hierarchy/product bindings; index exact product revisions, families, level ordering and optional resolved support geometry. |
| [Spatial eligibility](../../src/atlas/terrain/runtime/terrainSpatialEligibility.ts) | Conservative point/footprint containment, without projection or inventory reads. |
| [Selector](../../src/atlas/terrain/runtime/terrainSelector.ts) | Pure synchronous selection with ordered diagnostics, explicit family/level identity, fallback and refinement classification. |
| [Delivery adapter](../../src/atlas/map/terrainDeliveryAdapter.ts) | Adapt eligible XYZ Web Mercator raster heightfields to MapLibre; reject unsupported representations/delivery explicitly. |
| [Production registration](../../src/atlas/terrain/runtime/productionTerrainHierarchy.ts) and [visual policy](../../src/atlas/map/visualTerrainConfig.ts) | Resolve the existing external common service at geometry z14/relief z15 during setup. No camera-dependent source switching. |

Existing source, product, representation, family and composition types remain canonical. Registry indexes and optional normalized geometry/catalogues reference those declarations; they are not a second provider model. Upstream source identities remain in product lineage and existing source records. Exact product references recover delivery, source lineage, height/time semantics, rights, validation and limitations without copying everything into the result.

```ts
const registry = registerTerrainHierarchy(hierarchy, {
  scaleLevels: [{ scheme: declaredScheme, id: 'detail-request', order: 16 }],
});
const decision = selectTerrain(registry, {
  location: { coordinates: [x, y], crs: declaredCrs },
  scale: { scheme: declaredScheme, requestedLevel: 'detail-request' },
  provenanceRequirement: 'product-lineage',
});
// decision.trace explains eligibility/rejection in explicit policy order.
// The renderer adapter consumes the selected declaration; analytical sampling does not.
```

Callers may instead supply a `footprint`. Its whole geometry is tested; the point cannot override it. This slice does not derive footprints or requested levels from a viewport/camera. An optional explicit previous family/level classifies an actual selection change without hidden navigation state. Explicit `family` requests support development diagnostics and opt-in prepared transition selection.

## Spatial and scale eligibility

- Require **product valid support AND per-level valid support**. Source/product coverage, protected interior and transition support do not grant eligibility and remain distinct.
- Complete levels can serve contained requests. Partial, absent and unknown regional levels decline; partial partition rasters are retained by reference but not decoded in this slice. Offline partial parent diagnostics may exist below a product's raster delivery range without becoming deliverable tiles.
- GeoJSON Polygon/MultiPolygon uses `OGC:CRS84`; native rectangles use their declared identifier/name with XY coordinates. Queries must use the same CRS. There is no implicit reprojection, axis swap, dateline inference or national-geography rule.
- Footprint checks include edge crossings and holes, not just corner containment. Each requested polygon must fit a single support component; union-spanning cases decline conservatively. Owned valid geometry is assumed, not an untrusted GIS input parser.
- Asset-backed geometry remains unknown unless registration supplies an explicitly associated assessed geometry, keyed by asset URL/hash/selector. No network or large-data dependency is introduced. Caller footprints must already be explicit geometry.
- Orders come from declared family levels and an optional explicit scale catalogue. Conflicting ID/order mappings are configuration errors. Unknown requests return unavailable; there is no provider-name/zoom-string parsing in the selector.
- Select an eligible exact level first. A missing requested ID in the declared scale catalogue can use the nearest coarser family entry. Rejected children follow declared parents only while source-family identity and level scheme remain coherent. Cross-source parent links do not become ordinary regional LOD.
- Above the finest declared level, rendering overzoom requires explicit family permission. The result retains the actual selected level, requested level, derivation, sample-spacing statement and information ceiling. The adapter never requests tiles above the declared product delivery maximum, including explicit resampled/overzoom representations.

## Decisions, ordering and fallback

`regionalOrder` is the sole default regional ordering: every registered regional family must occur exactly once. There is no implicit numerical priority or object-iteration tie break. All ordered candidates are considered before deciding that declared common fallback is unavailable. Prepared transition families are not automatically ranked or selected; explicit registration enablement and a family request are both required.

Fine regional requests can fall to eligible same-source-family parents under `same-family-parent-then-common`. If regional eligibility is exhausted, declared common fallback is evaluated with its own support/scale/provenance checks. Missing common terrain returns an explicit unavailable result. Policies can forbid common fallback or parent reuse. This does not imply a reconciled geographic boundary or safe coarse handoff.

Selected results retain hierarchy ID/revision, family/source-family/role, exact product reference, representation family/level/kind, selected/requested level, derivation, information/overzoom/support state, composition-policy identity when applicable, reason and ordered trace. Classification is `direct`, `within-family-lod` or `source-family-handoff`. With a previous identity it describes that explicit change; otherwise a parent fallback or attempted regional-to-common fallback describes the decision path. An unchanged prior family/level is direct. Handoff validation state remains declared/unresolved, not automatically safe.

Spatial-contributor requests decline products lacking uniform complete lineage or a declared contribution mask. The selector retains mask/operator references; it does not fetch masks or claim to evaluate numerical contributor weights. Prepared synthetic transitions retain original composition, heterogeneous height, temporal/change and morphology evidence. Registration is not scientific approval. No processing operator runs during selection.

## AWS compatibility and renderer boundary

The [canonical AWS metadata](../../src/atlas/terrain/metadata/awsVisualTerrainProduct.ts) is extracted unchanged from the earlier examples and re-exported there for compatibility. Production imports this record, not the experimental catalogue.

AWS global assessed support is unknown. `legacyCommon` is a narrow explicit operational exception for an **external-unpinned common product**, with a declared addressing extent and policy reference. It preserves existing service use; it does not turn nominal coverage into assessed valid support. Selected results say `legacy-unassessed`, and their trace states that valid support remains unknown. No regional product can opt in. Without the exception AWS selection declines. Provenance requirements still apply; the service cannot satisfy a spatial-contributor request.

At startup the sole common service is resolved at a nominal in-domain setup point. Geometry and relief adapters recover the same AWS URL, XYZ/Terrarium encoding, 256 tile size, geometry maxzoom14, relief maxzoom15 and unchanged attribution. `terrainLayers.ts`, `AtlasMap.ts`, relief expressions, exaggeration1.45, satellite and projection/style-restoration code are unchanged. Existing evaluation hooks retain the same `VISUAL_TERRAIN_DEM` interface.

The adapter supports square PNG/WebP XYZ raster tiles in EPSG:3857 with declared metre units and Terrarium or Mapbox encoding. It checks selection/hierarchy/product identity and rejects unsupported formats. Rendering owns mesh, lighting, source IDs, exaggeration, terrain/projection ordering and lifecycle. No generic renderer or multiple active terrain-source architecture is introduced.

Analytical elevation retains its independent AWS256/z15 policy. The hierarchy is not imported by its configuration or sampler and does not become a source for route gradients, ascent/descent, timing or Weather altitude. Weather and Traverse files are unchanged.

## Errors, limits and next proof

Registration rejects duplicate exact product/family/level identities, broken revisions or parent references, cyclic/invalid parent relationships, inconsistent scale ordering, invalid complete delivery levels, incomplete regional ordering, missing common declarations and invalid transition/compatibility configuration. Re-registration can compare an earlier registry to reject changed immutable prepared content under the same product revision. Owned typed records remain the input contract; this is not an arbitrary JSON parser.

Deferred: partial-mask evaluation, reprojection, viewport/screen-error selection, availability networking, automatic transition adoption, dynamic source switching, meshes/3D, spatial indexing, reconciliation and all unresolved terrain-method limitations. No contract contradiction required changing frozen types. The implementation distinguishes offline partial levels from raster-deliverable levels and preserves honest legacy support unknowns.

Next: the already bounded Wales/Tryfan second-source proof, under separate authorization. Register a verified immutable regional pyramid with its own CRS/height/time/support/rights, test regional parents/common fallback and coexistence with another family, preserve production and analytical ownership, then stop. No additional Riffelhorn elevation-method experiment is performed or recommended.

## Validation / reproduction

```powershell
node --test scripts/atlas/test_terrain_runtime.mjs scripts/atlas/test_terrain_hierarchy_contract.mjs scripts/atlas/test_terrain_metadata.mjs scripts/atlas/test_terrain_policies.mjs
$testFiles = Get-ChildItem scripts/atlas,scripts/route,scripts/weather,scripts/ui -Filter test_*.mjs | ForEach-Object { $_.FullName }
node --test --test-concurrency=4 $testFiles
npm.cmd run lint
npx.cmd tsc -b
node --input-type=module -e "import {build} from 'vite'; import react from '@vitejs/plugin-react'; await build({configFile:false,plugins:[react()],publicDir:false,build:{outDir:'node_modules/.tmp/terrain-runtime-build'}});"
```

Application-only bundling excludes external Weather publication and experimental terrain. Tests include exact legacy/generic source configuration and matched lifecycle-call/snapshot comparison through globe/Mercator zooms, satellite toggling and style restoration. This is deterministic lifecycle verification, not a new terrain-rendering experiment or live source-availability claim. Final application validation:212 passed, one existing optional external-data skip. One concurrent build/test run had two file-startup failures; isolated reruns and the full four-process suite passed. The cause of those transient runner failures is not established.

For a manual compatibility check: `npm.cmd run dev`; open the local URL, start in terrain mode, zoom outward through5.5 and back in, toggle satellite/elevation, and return to terrain. Expect existing appearance and activation order. No local terrain server or `meridian-data` is required.
