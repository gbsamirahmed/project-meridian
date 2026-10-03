# Riffelhorn regional visual-terrain prototype

Evaluated 2026-10-03 from clean canonical `main` at
`340bf521bc8a042ac34d5a28d95351b9f6fb5077`, equal to locally recorded origin/main.
This is a bounded web-product integration prototype, not another Lab or a reopening
of the 012B–G terrain-reconstruction programme.

## Outcome

**The authoritative regional product renders successfully and reproduces meaningful
interior terrain gains. The unblended AWS join is not production-ready. AWS remains
the normal production visual and independent analytical source.**

**MERIDIAN EVIDENCE (M):** four verified official TIFFs can be prepared into a compact,
reproducible, attributed visual DEM product and used by the real application with
unchanged IGOR, exaggeration, imagery and domain behavior. The Swiss interior has
clearer ledges, channels, summit/slope structure and moraine forms. Twelve boundary
transects and multiple cameras expose spatially varying elevation differences and
false walls at the crop boundary. This is not a seamless-integration success.

**EXTERNAL EVIDENCE (E):** MapLibre 6.11.2 supports multiple DEM source objects but
one active terrain source; it does not automatically fuse overlapping DEMs. Official
Swiss provenance establishes LV95/LN02, a 2024 release and a distributed 0.5 m grid,
not independent 0.5 m measurement resolution. Upstream EU-DEM has different source
and reference semantics; the actual AWS output vertical relationship is not fully
established by those upstream descriptions.

**DIRECTION (H):** decide boundary/vertical accounting and source-support policy
before a general resolver or adoption. Composing tiles before MapLibre is a viable
prototype integration point, not a choice of universal service architecture.
Neither a constant height correction nor an indiscriminate seam blend is justified
by this result. No new source acquisition, imagery programme or reconstruction follows.

## Frozen application baseline

Every production `src/` file is unchanged. `src/atlas/map/visualTerrainConfig.ts`
remains AWS Terrarium, 256 pixels, geometry z14 / visual relief z15.
`src/atlas/terrain/analyticalElevationConfig.ts` remains independent AWS z15/256.
The earlier Mapterhorn loader remains evaluation-only and is not used as fallback.

`terrainLayers.ts` / `atlasVisuals.ts` retain native IGOR, 315° map-anchored light,
shadow `#17211f`, highlight `#f4efe0`, linear filtering and the strengthened continuous
curve `(5.5,0),(7,.09),(9,.30),(11,.54),(12,.45),(13,.36),(14,.33),(15,.30),(16,.30)`.
Accent/altitude remain configured but ineffective under IGOR. Exaggeration is **1.45**.
Optional elevation coloring, source IDs, stack ordering, OpenFreeMap basemap,
MapTiler imagery and satellite hillshade suppression remain unchanged.

`AtlasMap.ts` and the existing globe/Mercator transition guards are untouched.
Sky/fog/atmosphere retain the settings in the
[native relief record](native-relief-evaluation.md#frozen-baseline-and-controls).
Native mesh size 128 / quality factor 2 remain unchanged. Cameras use normal
MapLibre terrain-aware navigation; equal map camera controls do not fix a camera
to the same absolute world height over different terrain.

## Exact source estate and provenance

Only the relevant swissALTI3D inputs, their receipts/item metadata and retained
product provenance were read under:

```text
${MERIDIAN_DATA_ROOT}/sources/atlas/riffelhorn/swisstopo-2021-2024/
```

No SWISSIMAGE, swissSURFACE3D Raster or point-cloud inputs were processed. No private
estate was inspected. The existing scientific interpreter was invoked as tooling,
not as an invitation to inspect unrelated experiment data.

| Official input under `originals/swissalti3d/` | SHA-256 |
| --- | --- |
| `swissalti3d_2024_2624-1091_0.5_2056_5728.tif` | `c68c305e4a142da416b46b555a80916ecc52f8fa50bf1efd5cd2c3f24f9cd4bc` |
| `swissalti3d_2024_2624-1092_0.5_2056_5728.tif` | `9fa4a4391e2e1bfd650f2f31c7d38ed9a5a94494a967011468e6c44559bbcb2c` |
| `swissalti3d_2024_2625-1091_0.5_2056_5728.tif` | `0d2ebc6d0b4fd06ab2191cbf2a2f5ab77728249fa8c835075040bce4dc4899de` |
| `swissalti3d_2024_2625-1092_0.5_2056_5728.tif` | `4dffaad9efb82d3bf327a86b4f82d55762165ea5f825c386c23380a9320ff875` |

All match the repository [acquisition catalogue](riffelhorn-data-catalog.json),
local receipts and retained official checksum records. They total **65,607,404 bytes**;
each is float32, 2000×2000, north-up, 0.5 m area-cell spacing, LZW COG, EPSG:2056.
Four kilometre tiles form the exact AOI **[2624000,1091000,2626000,1093000]**.
Declared nodata is -9999; every source cell is valid. Heights span approximately
2189.576–2977.790 m. No research-normalized R16, reconstructed surface or derived
Unreal product is used: the pipeline reads official TIFFs directly.

Horizontal CH1903+/LV95 is encoded in the files. **LN02 / EPSG:5728, metres** is
established by product provenance, not by the horizontal TIFF CRS tag. Retained STAC
records identify publication on 2024-12-19; the acquisition receipts are dated
2026-10-02. Those dates are distinct from measurements.

The retained 2024/2 release record describes 2021/2022 LiDAR and 2023 photogrammetric
change updates in Valais, with DTM/TIN interpolation. Per-cell update lineage remains
unavailable. [swissALTI3D](https://www.swisstopo.admin.ch/en/height-model-swissalti3d)
and the [2024/2 release note](https://www.swisstopo.admin.ch/dam/de/sd-web/Zca1yaqlIgTp/swissALTI3D-release-2024_2_de_bf.pdf)
are primary references; the historical
[discovery record](riffelhorn-data-discovery.md) retains their hashes and interpretation.
The distributed grid and published LiDAR accuracy are not interchangeable claims.
Official [OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices)
permit reuse subject to credit; the prototype displays **©swisstopo** and existing
AWS terrain-source credits. No guessed Creative Commons licence replaces Swiss terms.

## Product preparation and contract

`scripts/atlas/riffelhorn_terrain.py` is isolated evaluation tooling. It verifies
source/receipt hashes and grid contracts, joins the adjacent rasters in memory,
and horizontally reprojects onto globally aligned Web Mercator XYZ grids.
It neither duplicates canonical source TIFFs nor alters them.

| Property | Prototype contract |
| --- | --- |
| Version | `riffelhorn-regional-terrain-v1`, experimental visual-only |
| CRS / scheme | EPSG:3857, XYZ; 2D horizontal reprojection only |
| Tile format | 256×256 RGB PNG, lossless, no color profile or alpha/nodata DEM convention |
| Encoding | Terrarium: `R*256 + G + B/256 - 32768`, metres |
| Hierarchy | Prepared z5–18 candidates; nonempty Swiss masks begin at z7. 547 composed terrain tiles, with 547 masks |
| Source sampling | GDAL area-average at z5–17; bilinear at z18; one thread, fixed grid/operation and parameters |
| Swiss coverage | Pixel centre inverse-projects inside the exact native AOI and has valid warped Swiss data |
| Missing/outside Swiss | AWS height fill, never Swiss -9999 or a transparent DEM; request failure is not sea-level zero |
| Join | Hard substitution, no height shift, boundary taper or seam blur |
| Height reference | LN02 inside Swiss mask; AWS outside, with its output reference incompletely established |
| Encoding loss | Round to nearest 1/256 m; measured maximum error **0.001953125 m** relative to pre-encoding composed values |
| Borders | All tiles share global alignment; the in-memory Swiss mosaic crosses native kilometre boundaries. MapLibre backfills DEM borders; AWS overzoom interpolation samples across parent boundaries |

Terrarium was chosen over supported Mapbox/custom encoding because its standard
1/256 m increment is finer than Mapbox's 0.1 m increment and needs no custom decoder.
This is encoding precision, not source accuracy or total reprojection fidelity.
MapLibre's actual `src/data/dem_data.ts` supports all three encodings; native
`raster_dem_tile_source.ts` disables image color-space conversion.

The recorded PROJ horizontal operation uses Swiss oblique Mercator, a three-parameter
Helmert translation and Web Mercator; the available non-ballpark operation reports
**1 m stated horizontal accuracy**. This limits georeferencing claims despite the
0.5 m source grid. Only x/y coordinates are transformed; LN02 elevation values
are not passed through a geoid/datum operation. The exact pipeline and installed
versions are retained in the manifest: Python 3.12.6, NumPy 2.5.3,
rasterio 1.4.3/GDAL 3.9.3, pyproj 3.7.2 and Pillow 12.3.0.

At this latitude, 256-pixel tile ground spacing is approximately **6.64 m at z14,
3.32 m at z15, 1.66 m at z16, 0.83 m at z17, 0.415 m at z18**.
The final level slightly oversamples the 0.5 m distributed grid. It does not create
new measurements or guarantee 0.415 m rendered vertices. Native heightfield mesh
LOD remains an additional limit.

## Storage, identity and reproduction

Generated product:

```text
${MERIDIAN_DATA_ROOT}/derived/atlas/riffelhorn/riffelhorn-regional-terrain-v1/
  manifest.json
  tiles/{z}/{x}/{y}.png
  masks/{z}/{x}/{y}.png
```

Terrain PNGs occupy **41,855,904 bytes**; masks **238,866 bytes**; total **42,094,770
bytes**, plus a 222,168-byte manifest. Median terrain tile is **76,446 bytes**,
range **19,377–158,556**. Per-level tile counts z7–18 are
**1,1,1,1,1,1,2,4,9,36,110,380**. Most storage is in the finest level.
The product records file hashes, four exact source identities, processing hash,
horizontal operation, output semantics and **37 frozen AWS input tiles**.

Accepted identity:
`4fc837f299271c7238591865a393f98facc6fa7b93d9cc75305160df900b1fe5`.
The lightweight checked-in [product record](riffelhorn-regional-product.json)
points to the external full manifest and its hash; it contains no personal absolute
paths or generated tile pyramid. Source masks identify Swiss versus AWS cells,
not acquisition confidence or individual LiDAR observations. Display interpolation
can involve multiple contributor cells.

AWS cached originals/HTTP metadata live at
`${MERIDIAN_DATA_ROOT}/cache/atlas/riffelhorn/riffelhorn-regional-terrain-v1/aws/`.
Numerical and regeneration evidence lives under
`${MERIDIAN_DATA_ROOT}/experiments/atlas/riffelhorn-regional-terrain-v1/`.
An independent rebuild remains in `scratch/atlas/riffelhorn-regeneration-v1/`:
**all 1,094 tile/mask file hashes match**, establishing byte determinism on the
recorded toolchain and cached inputs. The final verifier/Pillow/canonical-text review rebuild also matches all 1,094
hashes in `scratch/atlas/riffelhorn-canonical-text-regeneration-v1/`. Accepted captures retain
the earlier metadata identity but identical terrain bytes; the external final
regeneration check records this mapping. Cross-version GDAL/PNG byte equality is
not promised.
Repository catalogue and preparation-code hashes use canonical UTF-8/LF text,
matching Git checkout semantics; TIFF, receipt, cached AWS and output hashes use
raw bytes. A focused test covers LF/CRLF equivalence without weakening content
identity. The historical catalogue was not edited.

First-run preparation refuses an already completed product rather than silently
changing its identity; `verify` checks files, source inputs, cache hashes and code.

From repository root, using an environment with the recorded scientific dependencies:

```powershell
$atlasPython = '..\meridian-data\earth-lab\.venv\Scripts\python.exe'
# First build only; leave an existing completed product intact.
& $atlasPython scripts/atlas/riffelhorn_terrain.py prepare
& $atlasPython scripts/atlas/riffelhorn_terrain.py verify
& $atlasPython scripts/atlas/check_riffelhorn_product.py
& $atlasPython -m unittest discover -s scripts/atlas -p test_riffelhorn_terrain.py
# Separate terminal, loopback only; requires explicitly prepared product.
& $atlasPython scripts/atlas/riffelhorn_terrain.py serve
# One capture process at a time, no concurrent heavy browser/build/test work.
node scripts/atlas/capture_riffelhorn.mjs aws inside
node scripts/atlas/capture_riffelhorn.mjs riffelhorn inside
# Repeat both sources with phases: boundary, operations
node --test scripts/atlas/test_terrain_policies.mjs
```

Preparation uses the normal `MERIDIAN_DATA_ROOT` resolver. It does not create a
new scientific environment or install dependencies. Bounded AWS fallback downloads
are cached; no additional Swiss source is acquired.

## MapLibre composition constraint and adapter

Installed `src/ui/map.ts:setTerrain` constructs one `Terrain` from one source
tile manager and destroys the prior terrain/RTT resources when switching.
Multiple raster-dem objects can exist, but source bounds only restrict their
requests; they do not nominate another source to fill missing geography. Parent
fallback is within the chosen source, not across AWS and Swiss source IDs.
Separate overlapping hillshade layers cannot compose terrain geometry.

Accordingly, the prototype presents **one composed endpoint** to each of the existing
two internal visual DEM source IDs. This retains the recommended separate geometry
and relief caches while they consume the same composed data policy. A private Vite
loader in `scripts/atlas/riffelhorn_evaluation.mjs` replaces only the visual config
for the evaluation server; normal Vite/application startup has no import or flag.
Neither renderer source IDs nor production lifecycle callbacks change.

The local Python endpoint is `http://127.0.0.1:4180/tiles/{z}/{x}/{y}.png`.
Prepared intersecting tiles include Swiss cells and AWS fill. Elsewhere it redirects
to original AWS through z15; above z15 it serves cross-parent bilinear AWS overzoom.
This supplies no new global information. Prototype geometry/relief ceilings are
both z18 to expose Swiss delivery; production ceilings remain z14/z15.
Consequently higher geometry LOD is also available over resampled AWS outside,
a real cost/scale limitation of this simple single-source model.

The endpoint is loopback-only tooling, not a product backend or final CDN.
Prepared product identity does not freeze every future global fallback tile;
runtime fallback cache identities remain separate. One-hour browser caching and
two visual source caches avoid changing production cache policy. A tile generation
failure yields an explicit error, not fabricated heights.

**Initial negative run:** missing CORS on redirect responses caused browser fetch
failures and no accepted regional captures. The adapter was corrected; full
regeneration retained identical terrain/mask bytes. The initial manifest/failure
diagnostics remain external. The accepted manifest describes the corrected code.
No production HTTP/lifecycle workaround was shipped.

## Controlled observations and numerical evidence (M)

Headless Chromium 151.0.7922.34, 1440×900, device scale 1, en-GB, Europe/London.
Real terrain, basemap and existing configured imagery; loaded tiles/native idle
plus 400 ms settling. Paired source-file hashes, camera controls, sky, paint,
exaggeration, projection and native mesh size are recorded. Unlike the Mapterhorn
comparison, both policies use **256 pixels**; ordinary views below AWS ceilings
do not introduce its 512-pixel tile-size/hillshade-amplification confound.
Detail views intentionally differ in delivery ceiling/native LOD, not style.
At z16.2, observed AWS geometry tops out at z14 and relief at z15; regional
geometry reaches z16 and relief z18. Native mesh size remains 128. The native
hillshade kernel/zoom amplification and selected mesh LOD are part of this delivery
difference. Stronger fine-view appearance is not attributed solely to higher
measurement information; decoded matched-grid checks supply the independent data
comparison. The final delivery level is not necessarily loaded as geometry.

| Purpose | Camera |
| --- | --- |
| Riffelhorn landscape/planning/close | center `[7.76121329,45.97910794]`; z9.4/11.4/13.2; pitch 45°/45°/55°; bearing 0° |
| Detail | same center; z16.2, pitch 55°, bearing 0° |
| Rotation | same center; z15.2, pitch 55°, bearings 90°/180° |
| Boundary | native west/east midpoints `(2624000,1092000)` / `(2626000,1092000)`, south/north `(2625000,1091000)` / `(2625000,1093000)`, north-west corner; z15.2, pitch 55°, bearing 0° except corner 45° |
| Outside control | `[7.737,45.99]`, z14.2, pitch 45°, bearing 0° |
| Synthetic route | same Riffelhorn center, z14.2, pitch 45°, bearing 0° |
| Satellite | same close camera; native hillshade zero |

Exact transformed boundary cameras are checked in as
`scripts/atlas/riffelhorn-boundary-cameras.json`. These purposes are not universal
zoom categories. Generated captures/style/network manifests remain ignored at
`test-results/atlas-riffelhorn/`; no screenshot estate is committed.
Weather publication is deliberately unavailable (503 fixture), with honest UI state;
no external Weather publication/private data is read or Weather calculations altered.
This task does not repeat the prior rain-overlay evaluation.

The synthetic three-waypoint GPX in the capture script is solely a test path,
**not a recommended mountain route**. It uses normal import/route preparation and
real independent AWS analytical sampling. It can therefore be displayed over Swiss
visual geometry while its profile/timing still follows AWS. That discrepancy is
intentional staging, not a hidden migration.
Both accepted route imports report 1.1 km, 371 m ascent, 0 m descent, moving 50 min,
breaks 30 min and about 1 h 20 min. Absolute departure/arrival labels differ because
the normal application initializes departure from the wall clock (14:15 versus
14:30 during the sequential runs); they are not a provider-induced timing change.
Deterministic sampler/policy tests independently verify the AWS request and values.

Interior observations: landscape gains are localized to a small 2×2 km patch;
at planning/close views channels, ledges and moraine structure become much clearer.
Higher zoom retains useful finer texture, but steep-face banding/striping and
heightfield topology limits remain. No detail normal, cliff reconstruction, true-3D
content or imagery enhancement is implied. Rotation preserves interior gains and
also exposes boundary walls from other directions. Satellite preserves native
hillshade suppression and photographed appearance; sharper geometry cannot repair
unobserved/stretching imagery.

There are 28 accepted paired captures across the three phases. Initial satellite
screenshots reached map idle before asynchronous imagery metadata/loading and showed
the vector fallback; they were rejected and retained externally. The corrected
capture wait explicitly requires a visible, loaded satellite raster source. Fresh
sequential operations runs provide the accepted real-imagery comparisons. No
production satellite/loading workaround was made. Route/labels remain readable
over Swiss geometry, although the false boundary walls remain unacceptable.

Independent checks distinguish encoding from preparation:

- At 784 actual z18 target-pixel centres, decoded product minus independent native
  source-grid bilinear samples has **0.047 m RMS**, 95th absolute **0.056 m**, maximum
  **0.654 m**. This includes warp/resampling transfer differences, not just encoding;
  it is not a source accuracy test. Total preparation must not be described as 2 mm
  fidelity simply because the codec rounds within 2 mm.
- Across 1,600 interior diagnostic positions, source minus AWS z15 has mean
  **−35.646 m**, RMS **69.160 m**, range **−150.462 to +172.951 m**. A 71-point
  low-local-slope subset still differs substantially; it supplies no clean datum fit.
- Composed source sampling versus native bilinear reference has RMS approximately
  **0.919 / 0.396 / 0.224 / 0.133 / 0.050 m** at z14/15/16/17/18. Area averaging,
  reprojection and subsequent interpolation progressively retain finer information;
  those are not independent measurement improvements or universal visual thresholds.
- One **retained**, fully interior Mapterhorn z17/512 tile aligns with four new
  z18/256 tiles. Direct Swiss minus retained Mapterhorn: mean **0.004 m**, RMS
  **0.063 m**, 95th absolute **0.109 m**, extremes about ±2.2 m. This supports the
  same useful interior information with differing preparation, not identical
  processing, a fresh provider evaluation or independent truth. No new Mapterhorn
  requests were made. The optional comparison reports unavailable if that old
  ignored capture product is absent.

### Boundary and vertical-reference result

Twelve 100 m transects, 1 m spacing, cross all four native AOI sides at 25/50/75%
positions. Raw inside Swiss-minus-AWS differences vary approximately **−112 to
+51 m**. Largest adjacent 1 m changes in the composed finest-grid samples range
**1.27–70.17 m**. North is generally less severe; west/south are particularly bad.
The renderer shows false vertical walls, abrupt shade/texture changes and the
rectangular patch boundary. No general missing-DEM hole is needed to explain them.
Native tile-border backfill/skirts do not reconcile a discontinuity inside a DEM.
Repeated cameras, rotations and zooms do not make the join acceptable.

**E:** local AWS response metadata identifies
`eudem/eudem_dem_5deg_n45e005.tif`. [Eurostat's EU-DEM description](https://ec.europa.eu/eurostat/web/gisco/geodata/digital-elevation-model/eu-dem)
identifies a fused SRTM/ASTER DSM and EVRS2000/EGG08 upstream reference. This does
not independently establish every transformation in the historical AWS tile
pipeline, or a valid LN02→AWS operation. EPSG:3857 is not a height datum.

**M:** observed differences dwarf the measured encoding/warp transfer effects,
vary spatially and change sign. Source resolution, terrain displacement, surface
semantics, acquisition and datum may contribute. Neither a mean-offset correction
nor attributing the full mismatch to vertical datum is supported. LN02 is preserved;
vertical reconciliation and a defensible boundary policy remain unresolved.

## Operational evidence and validation

Bounded Chromium interaction completed with finite terrain at all capture centres,
no page exceptions and no failed DEM HTTP responses after the redirect-CORS fix.
Repeated globe→Mercator→globe→Mercator transitions and animated pan/zoom/rotation
pass. The outside-control terrain query is exactly equal for both policies
(3132.21525386207 m, including the renderer's exaggeration); through z15, external
fallback uses original AWS bytes. This is a local control, not global validation.

| Phase | AWS successful DEM responses / body bytes | Regional-policy successful responses / body bytes | Regional redirects |
| --- | --- | --- | --- |
| Inside | 283 / 34,696,011 | 341 / 40,207,905 | 261 |
| Boundary | 174 / 19,407,320 | 363 / 32,440,396 | 154 |
| Operations | 506 / 51,557,321 | 684 / 65,003,626 | 539 |

These are observed successful response bodies, including cache-served/duplicate
requests, not measured network-wire transfer or unique tile counts. Redirects are
counted separately from followed AWS responses. Native geometry/relief have
separate caches; the higher regional ceiling also permits finer **resampled AWS**
outside, increasing global request/generation burden. The local server serializes
decoded AWS cache access and generates those overzoom tiles on demand. This is
practical for a bounded prototype, not evidence of a production-ready service.

Settled-capture waits ranged roughly 6–18 s for AWS and 6–25 s for regional policy,
including native idle, network/CPU work and the fixed 400 ms wait. They are not FPS
or an isolated performance benchmark; early runs also overlapped unrelated local
validation work. All 76 AWS and 101 regional request failures in the accepted
manifests are ordinary `ERR_ABORTED` cancellations during view/source-visibility
changes, not DEM error responses. Twelve Weather 503 responses are deliberate
fixtures, two per isolated run. No live Weather-overlay evaluation, load test,
cross-browser claim or cache/CDN optimization is made.

Verification completed:

- Six isolated synthetic Python tests: Terrarium precision/range handling,
  adjacent XYZ pixel alignment, cross-parent interpolation, stable identity and
  frozen-source provenance drift rejection and canonical LF text-hash stability. They need the scientific libraries,
  not external source files/network/server.
- All 1,094 output hashes match independent rebuilds; real-product verification
  checks manifest/code identity, frozen catalogue/receipt/input provenance, output
  decoding and cached AWS hashes. The lightweight repository record matches the
  final manifest. Numerical checks were repeated against the final product identity.
- Ten focused terrain-policy tests pass, including actual source configuration,
  unchanged rendering/exaggeration, satellite suppression, and independent AWS
  analytical request/value behavior under the regional visual override.
- Full active Node suite: **137 passes, zero failures, one live-publication skip
  (138 tests)** using an empty data-root stand-in and synthetic fixtures. An initial
  unexplained file-level temperature-contour test-process failure passed in isolation
  and the complete rerun; no Weather tests/code were edited. The clock-sensitive
  Forecast Workspace test passed unchanged.
- ESLint, TypeScript/application Vite build, new JS syntax/Python compilation,
  unchanged production-source checks and diff checks pass. Build used the existing
  ignored application-only config to omit external GFS materialization/public
  copying; the existing large-chunk warning remains. Full Weather publication and
  unrelated historical research suites were not run.

The full application suite is selected from existing `scripts/{atlas,route,ui,weather}`
`test_*.mjs` files and run with `node --test --test-concurrency=1`. Production build:
`npm.cmd run build -- --config node_modules/.tmp/atlas-validation.vite.mjs`;
that ignored configuration contains only the React plugin and `copyPublicDir:false`.
Normal CI and application startup have no Swiss estate/server dependency. Only
explicit isolated preparation, verification, serving and capture commands require it.

## Practical implications and stopping point

Direct ownership gives source checksums, authority, release, grid/height reference,
processing/version control and per-cell contributor masks beyond Mapterhorn's
candidate-coverage attribution. It does not recover source per-cell acquisition
lineage or confidence. It also introduces preparation, storage, fallback handling,
HTTP delivery, global overzoom cost and seam/vertical responsibility.

The prototype demonstrates a viable **product-to-native-renderer** path and the
single-source composition constraint. It does not demonstrate production regional
substitution, seamless transitions or independently verified accuracy. The next
decision should concern source support, boundary behavior and vertical accounting
before generalizing the resolver. No Swiss production default, SWISSIMAGE,
analytical migration, rendering retune or follow-on programme is begun here.

Operational and validation results are recorded in the development log and final
accepted capture manifests. Live services/local product tests are isolated from
normal CI; ordinary application startup does not require this estate or server.
