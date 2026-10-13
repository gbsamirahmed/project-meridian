# Riffelhorn — source-aware contour vector-tile feasibility

**13 October 2026. The owner accepts the vector-tile experiment and refined index opacity as a successful visual and technical prototype. Preservation commit remains unapproved.** The [accepted multiscale experiment](multiscale-contours-hillshade.md) supplies three immutable Swiss contour masters and its shaded PNG. The [genuine scientific pilot](source-aware-contour-pilot.md) remains Outcome C; no missing products, contour extraction, source fusion or independent genuine repeatability has been established by this display experiment.

## Product and preview

Open **http://127.0.0.1:5180/** while the loopback-only server is running. [Commands and scoped utilities](../../scripts/atlas/contour-vector-tiles/README.md) reproduce startup, packaging and focused checks. The UI offers scale-driven display, manual source/interval comparison, hillshade, pan/zoom and retained-line height picking. **Regional scale** demonstrates hidden contours; **Study area** returns to z14. The prior accepted viewer is linked for a separate same-terrain comparison. No private application code or full Meridian interface is used.

External root:

```text
C:\Users\gbsam\Documents\Projects\meridian-data\experiments\atlas\contour-vector-tiles-v1
```

`tiles/{swiss-native|swiss-2m|swiss-smoothed}/{z}/{x}/{y}.pbf` are **standard MVT v2**, source layer `contours`, XYZ scheme, **z10–17**, extent8192, buffer64, tolerance0. `product.json` retains source manifests, operation, datum, rights and coverage. `tile-receipt.json` records versions/settings and every tile hash; `delivery.json` combines their delivery identity. `geometry-validation.json` and `browser-review-final/browser-receipt.json` retain measurements. `demo/` is a local Vite build. No generated artefacts enter Git.

## Scientific meaning and coordinate handling

Input masters remain native0.5 m **662,196** vertices / 1,596 lines, strict2 m **150,389** / 356, and smoothed2 m **140,562** / 203. They represent source-specific LN02 DTM fields, not interchangeable global DSM contours. Interval subsets use exact integer elevation divisibility; no new heights or geometry are extracted to obtain 50/100 m intervals.

Original XY: **EPSG:2056 LV95**. Offline PyProj 3.7.2 / PROJ9.5.1 transforms XY via **Inverse Swiss Oblique Mercator1995 + CH1903+ to WGS84 (1) + axis-order change (2D)**. The exact pipeline is recorded in `product.json`; no ballpark substitution, grid download or external service. This available operation reports **1 m accuracy**, which is a coordinate-operation qualification, not an assertion of source DTM or contour accuracy. Maximum measured horizontal forward/inverse discrepancy across all **953,147** vertices: **0.001250161689 m**; numerical round-trip agreement does not establish absolute accuracy.

GeoJSON WGS84 positions are projected by the installed GeoJSONVT tiler into the Web Mercator grid, buffered/clipped, and rounded to8192 integer tile units. Elevation attributes are copied exactly as `elevation_m`, `vertical_ref=LN02`, `units=m`, with `index100`, `source_product`, original `source_line` and stable source-local numeric feature IDs. **No LN02 height transformation** occurs. Source revision, DTM representation, processing history, rights and known limitations remain in the source manifests. These tiles are visual delivery derivatives, not authoritative point elevation evidence.

The previous 4000² shaded PNG is horizontally warped to an axis-aligned **3859 × 3846** EPSG:3857 image using the recorded operation, bilinear intensity/alpha resampling and **0.75 projected metres/pixel** (about0.52 ground metres here). MapLibre receives the rectangle's inverse-Mercator corner coordinates. No DEM is decoded or hillshade recomputed. Transparency preserves unsupported areas; the image is visual only and is not the application’s Mapterhorn mosaic.

## Provisional cartography

| MapLibre viewing zoom | Intended contour interval |
|---|---|
| Below11 | Hidden |
| 11–12 | 100 m |
| 12–13.5 | 50 m |
| 13.5–15.5 | 20 m |
| 15.5 and above | 10 m |

Interval changes fade over **0.25 zoom levels**, selecting existing elevation levels. Smoothed2 m geometry transitions to strict2 m over **z14.75–15.25**, then to native0.5 m over **z17.25–17.75**. Native display overzooms z17 tiles to z21, without inventing extra resolution. Configurable constants are in `rules.mjs`. These zoom values depend on the renderer's512 px zoom convention, latitude and display; they are not replacements for scientific resolution or permanent global cartography.

Index contours are100 m, darker/thicker (1.3 versus0.6 CSS px). No glyph/label dependency is used; clicking a visible line supplies its source-labelled height. Zero-opacity features can still appear in MapLibre queries, so picking explicitly rejects hidden interval/source features and clears stale selections after camera/mode changes. Browser query counts include invisible feature-dependent lines and must not be presented as painted-line counts.

Opacity transitions avoid abrupt membership switches but can temporarily show both reconstructed fields: ghosting/line movement is possible, not scientific fusion. No new smoothing, simplification or controls in the application were introduced. Geographical consistency, exact thresholds, distant-source coverage and final appearance remain owner decisions.

### Focused automatic index-opacity refinement

The owner found the overall tiled demonstration satisfactory, but prominent lines became dark too quickly during regional zoom-in. Automatic **100 m index contours only** now use linear zoom/opacity stops:

| Zoom | Index opacity before source weighting |
|---|---:|
| ≤11 | 0 |
| 11.5 | 0.08 |
| 12 | 0.22 |
| 13 | 0.60 |
| 14 | 1.00 |
| 16 | 0.60 |
| 18 | 0.40 |
| ≥21 | 0.30 |

For example, z11.05 is0.008 and z11.25 is0.04, rather than the previous0.20 and1.00. Reference z14 remains provisional and retains the previous maximum colour/width/opacity. Beyond it, index prominence decreases; ordinary-contour interval fades, source weights, manual comparison opacity, picking logic, colours and widths remain unchanged. Each source enters with zero source weight; the first automatic layer starts with zero index opacity at z11. The new stops are included in the compiled MapLibre expression, so it does not skip the reference peak.

Before/after browser frames were captured at12 fractional zooms:10.99,11,11.05,11.25,11.5,12,13,13.9,14,14.1,16,18.5. Inspected paired screenshots show gentler regional lines at z12, unchanged study-area prominence at z14 and lighter index lines at z18.5. The captured z14 map rectangle is pixel-identical before/after; this is a screenshot comparison, not an accuracy claim. Browser outputs are external `opacity-before/`, `opacity-after/` and `opacity-comparisons/`. No external HTTP page requests or normal rendering errors occurred.

**Eight focused tests pass**, including the new opacity monotonicity/stops/manual-preservation check. An initial exact-equality assertion exposed ordinary binary floating-point rounding (0.22000000000000003); the styling test uses1e-12 tolerance, with no scientific input/result adjustment. Existing browser regressions were rerun into fresh `opacity-regression-browser/`: manual variants, intervals, pan/wheel, visible-line picking, reference viewport, flat rendering and controlled error/reload recovery pass. Existing geometry validation is now compared read-only rather than rewritten. Tiles, attributes, product metadata and earlier scientific/browser receipts remain byte-for-byte unchanged. Standalone build and scoped lint pass; the existing large-chunk advisory remains. Android touch behaviour is untested.

### Tolerated reconstructed-geometry ghosting

The owner reports briefly doubled or overlapping contours during continuous zoom and considers this tolerable here. Smoothed, strict and native products trace **independently reconstructed elevation fields**. A shared height label does not give them an identical position or a vertex correspondence. During z14.75–15.25 and z17.25–17.75, both fields are painted at fractional opacity; source crossfading changes their visibility, **not their geometry**, so it cannot guarantee one intermediate contour position.

The effect is expected to be most noticeable inside those fade bands where the fields diverge, particularly dense cliffs, narrow ridges and fine native waviness. Continuous Android touch/pinch zoom may expose the overlap more clearly than isolated desktop zoom samples; no physical-device check was performed. Index opacity is softer, but no ghosting reduction is claimed and source-fade timing is unchanged.

Later options include shorter or delayed fades/settling behaviour, or validated generalised representations derived from a common geometry. Those have different continuity/topology and source-meaning trade-offs. No geometry morphing, intermediate dataset or new generalisation pipeline was implemented. The owner accepts the remaining ghosting as tolerable in this prototype. Acceptance is limited to Riffelhorn visual and technical feasibility, not production readiness, global coverage or Android performance. Preservation and any application integration require separate approval.

## Storage, processing and validation

| Product | Tiles | Raw MVT bytes | z17 median / maximum tile bytes |
|---|---:|---:|---:|
| Native0.5 m | 164 | 11,478,265 | 10,149 / 51,008 |
| Strict2 m | 164 | 2,789,518 | 3,353.5 / 16,019 |
| Smoothed2 m | 164 | 2,576,601 | 2,998.5 / 15,473 |
| **Total** | **492** | **16,844,384** | |

These are uncompressed HTTP body/file bytes; no storage-block/transport-overhead or worldwide cost estimate. Largest tile across all zooms is **1,388,614 bytes** (native coarse zoom), demonstrating why shipping every native feature at every zoom is wasteful. Automatic mode does not render/request native layers at distant scales. This deliberately redundant prototype retains all three sources for manual comparison; a later product should package only justified bands. The retained whole experiment, including prepared inputs, partial attempts, build variants and screenshots, was about**111 MB** before final audit/manifest writes; that is not the deliverable tile footprint.

Preparation: **7.4 s**, no new contour vertices. Successful packaging: **36.9 s**, measured peak Node RSS **507,797,504 bytes / 484.3 MiB**, one process, Node heap cap512 MiB. Every tile is decoded and its properties checked; **23,991 fragments / 7,813,998 encoded coordinates** include buffered fragments and repeated zoom representations, not new source vertices. Encoding the same clipped tile twice produced matching bytes; **no independent full-pipeline repeatability claim** is made.

Early attempts are retained externally: empty-layer handling initially failed; retaining the complete unsimplified zoom cache exhausted the heap; per-tile public-API indices solved memory retention but z10–18 then exceeded the120-second cap. Final z10–17 packaging fits the unchanged caps without simplifying native geometry. Stored z17 precision is about**0.026 m per tile unit** at Riffelhorn, sufficient for this visual trial; preserving original rasters/masters remains essential. No historical evidence was altered to obtain success.

**Original feasibility validation: seven focused Node tests passed.** The opacity refinement adds an eighth test; all eight pass. They cover standard encoding/decoding, properties, valid empty tiles, buffered seams, a closed synthetic ring crossing four tile corners, scale rules and the real product seals. All source-local master lines remain represented at z17; **594 vertex samples** have no missing matches and maximum point-to-delivered-segment displacement **0.62416 tile units / about0.01619 ground metres**. Across **48 representative adjacent z17 pairs / 449 crossings**, no unmatched feature crossing group was found; maximum sampled seam difference **0.06212 tile units** (about0.0016 ground metres). These bounded samples do not prove whole-product topology preservation or exact continuity at every zoom. Integer quantisation can collapse vertices and affect narrow features, particularly at coarse scales; tolerance0 does not eliminate that loss.

Actual installed headless Chromium with **SwiftShader software WebGL** rendered seven zoom snapshots9.5–18.5, desktop1280×900 and reference384×832. Drag pan, wheel zoom, manual source switching, height clicking, flat pitch0/no terrain, controlled failed local tile requests and reload recovery passed. Normal rendering produced no page/console errors and no non-loopback HTTP page requests. Source/interval unit tests and inspected browser images support the intended behaviour; no hardware-GPU, touch-pinch or physical Android result is claimed.

Final browser trial: initial first idle **331 ms**, recovery first idle **278 ms**; programmatic zoom-to-settled observations **602–1,011 ms**, including driver overhead and an intentional150 ms settling wait, with caching/warm-runtime effects. This is not frame rate or sustained mobile performance. The server counted **52 tile requests / 2,532,456 response-body bytes** during that sequence. Hillshade and JS/CSS bytes are separate: whole-image shading (~10 MB) and renderer/worker bundles (~1.5 MB) remain important mobile costs. Vite reports its existing large-chunk advisory; no framework split or dependency change was added merely to silence it.

## Comparison and handover

Inspected screenshots show broad hillshade/contour alignment and retained close native waviness without an obvious seam in those views; visual alignment is not independent accuracy evidence. Compared with the accepted whole-study viewer, the map now loads spatial vector tiles and selects broad intervals before20/10 m, while supporting conventional MapLibre camera interactions. It also introduces horizontal datum conversion, integer quantisation, clipping and renderer antialiasing, so pixel-for-pixel equality is neither expected nor claimed. Dense cliffs remain crowded; transition ghosting is accepted as tolerable for this prototype. The whole shaded image and unused native coarse-zoom tiles make this prototype unsuitable as a final mobile package.

**Recommend a controlled application integration trial only under separate approval.** The smallest handover is this Riffelhorn-only overlay: one or a few bounded vector sources with declared z10–17 bounds, `source-layer=contours`, attribute-driven index/interval styling, source/vertical metadata and unchanged flat camera. Select only necessary source/zoom bands and retain source-local IDs. Bundled or approved local delivery would need to respect the application's existing resource accounting, lifecycle/error handling, attribution, source permissions and bundled/live separation. Recheck the actual application's MapLibre version and physical-device cost; public renderer6.11.2 is not proof of private WebView compatibility. No new hosting, provider, licence grant, phone trial or integration is authorised here.

Licences: Swiss OGD / ©swisstopo data; installed MapLibre BSD-3-Clause, geojson-vt ISC, vt-pbf MIT, vector-tile/pbf BSD-3-Clause and Vite MIT. No fees/accounts, downloads, source changes, application access, production distribution, commit or push. Original inputs, masters, receipts, protected code hashes and research statuses are rechecked before handoff. New utilities/tests/report plus append-only development log are the only public working-tree changes. All generated data and failed-attempt evidence remain outside Git.
