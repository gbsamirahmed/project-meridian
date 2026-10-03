# Atlas global terrain foundation evaluation

Evaluated **2026-10-03**, starting from clean canonical `main` at
`d05f054c96249754cc712044a82d6af1f24d628b`, equal to locally recorded
`origin/main`. External service facts describe that access date, not a permanent
service contract. Mapterhorn repository main was
`077e6530bf410ce756fba8817eedfcea0ab0e806` (2026-09-16, vertical-rounding documentation).
This bounded production-source evaluation does not reopen the closed 012A–G epoch.

## Conclusion and gate

**Mapterhorn passed the experimental gate. Production remains AWS Terrarium.**
Official direct-browser examples, live TileJSON, decoded tiles and source records
established enough delivery, rights and resolution information for a controlled
comparison. No adapter beyond a capture-only visual configuration substitution was
required. This is not production legal clearance or a service reliability guarantee.

**MERIDIAN EVIDENCE (M):** materially clearer Welsh and Swiss mountain terrain under
the existing renderer; much smaller gains in the English controls. Higher local
zooms contain additional numerical information, but their incremental display gain
is modest and some steep faces remain striped. Global parent fallback works in
the inspected case; sparse high-zoom delivery causes real 404s. No production
source, rendering, analytical, Weather or Traverse code changed.

**EXTERNAL EVIDENCE (E):** Mapterhorn is a derived, heterogeneous terrain mosaic and
delivery pipeline, with a global Copernicus DSM fallback and finer regional DTMs.
Its source priorities, blending, vertical rounding and sparse tile pyramid matter
as much as its advertised resolution. Public direct use is intended, but a common
output vertical datum, full service commitments and sufficient point provenance
were not established.

**DIRECTION (H):** a plausible global visual foundation, especially in strong
regional coverage. Before migration, decide the acceptable sparse-delivery/source
contract, resolve vertical/water semantics and source-specific attribution, and
decide operational/versioning requirements. Hosting or normalization may help;
neither is demonstrated to be universally required. No resolver, provenance system
or migration is chosen here.

## Frozen production baseline

Authoritative code: `src/atlas/map/visualTerrainConfig.ts`, `terrainLayers.ts`,
`atlasVisuals.ts`, `AtlasMap.ts`, `satelliteLayer.ts`, and independent
`src/atlas/terrain/analyticalElevationConfig.ts` / `terrainElevationSampler.ts`.

- AWS visual URL: `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`;
  Terrarium, 256 pixels, geometry ceiling **14**, visual relief ceiling **15**, existing
  Tilezen terrain credits. `terrain-analysis-dem` is a historical source ID for
  **visual relief**, not the analytical route sampler.
- MapLibre **6.11.2**, native IGOR, **315°**, **map** anchor, linear filtering;
  shadow `#17211f`, highlight `#f4efe0`. Configured accent `#586b66` and altitude
  42° are ineffective under IGOR in this implementation.
- Linear strength stops `(5.5,0), (7,0.09), (9,0.30), (11,0.54), (12,0.45),
  (13,0.36), (14,0.33), (15,0.30), (16,0.30)`; constant thereafter.
  Evaluated strengths at landscape/planning/close zooms are 0.348 / 0.504 / 0.354.
- Exaggeration **1.45**; native terrain mesh size **128**, existing quality factor
  **2**, globe below 5.5 / Mercator terrain at and above 5.5, activation guards and
  lifecycle unchanged. Initial camera remains `[-4.0762,53.0685]`, z11.4, pitch/bearing 0°.
- Existing OpenFreeMap Liberty composition; optional elevation ramp opacity 0.7,
  otherwise zero. Satellite retains real configured MapTiler imagery, linear
  filtering, opacity 1, fade 180 ms, labels and **zero hillshade**.
- Sky `#07111e`, horizon `#9eb4ba`, fog `#bdc9c6`; ground/horizon/sky blends
  0.42 / 0.72 / 0.82. Atmosphere stops `(0,1), (4,0.9), (7,0.25), (9,0)`.
  Comparison pitch is at most 55°; high-pitch ground fog is not separately evaluated.
- Analytical policy stays independent AWS Terrarium, **z15 / 256**, with unchanged
  XYZ/Web Mercator addressing, decoding, interpolation, cancellation and cache.

The earlier [native relief record](native-relief-evaluation.md) explains the selected
presentation policy. This task does not retune it.

## Verified external service and elevation contract (E, with live checks M)

Primary references: [data access](https://mapterhorn.com/data-access/),
[official MapLibre example](https://mapterhorn.com/examples/terrain/),
[live TileJSON](https://tiles.mapterhorn.com/tilejson.json),
[pipeline documentation](https://github.com/mapterhorn/mapterhorn/blob/077e6530bf410ce756fba8817eedfcea0ab0e806/pipelines/README.md),
[distribution documentation](https://github.com/mapterhorn/mapterhorn/blob/077e6530bf410ce756fba8817eedfcea0ab0e806/distribution/README.md).

| Property | Established state / limitation |
| --- | --- |
| Public endpoint | `https://tiles.mapterhorn.com/{z}/{x}/{y}.webp`; no key; official examples intend direct browser use |
| Addressing | XYZ, Web Mercator / EPSG:3857; TileJSON bounds approximately ±85.0511287° latitude |
| Image / encoding | 512×512 RGB, **lossless WebP**, Terrarium `R*256 + G + B/256 - 32768`, metres; confirmed in pipeline and actual decodes |
| Zoom contract | TileJSON omits min/maxzoom. Planet archive z0–12; sparse regional children z13+. Catalogue contains shards reaching z18; this is not z18 coverage everywhere |
| HTTP | Valid probes 200 `image/webp`, CORS `*`, `public,max-age=604800`; many Cloudflare HITs; some Last-Modified/Age headers. TileJSON returned text/plain and no observed cache-control |
| Missing tiles | Real 404 text responses with CORS and seven-day cache. No HTTP parent substitution in probes; MapLibre itself searches retained/requested parents |
| Operational promise | No formal SLA, published quota/fair-use policy or immutable hosted tileset version found in inspected official material. Absence of a published limit is not unlimited-load permission |
| Browser compatibility | Installed Chromium loaded real 512-pixel DEMs with finite terrain heights; no page exceptions. Other browser families not tested |

The operator's [Cloudflare support announcement](https://www.linkedin.com/posts/mapterhorn_cloudflare-is-supporting-mapterhorn-with-activity-7388468516003155968-SSG2)
describes free unrestricted access; treat it as an operator statement, not an SLA.
Bounded normal browser traffic was used, not a load test. Default Python urllib
was rejected by Cloudflare (403/1010); an honestly identified evaluation User-Agent
worked. Normal Node/Chromium access worked. No evasion or credentials were needed.

The tiles are **derived products**. Inspected
[reprojection](https://github.com/mapterhorn/mapterhorn/blob/077e6530bf410ce756fba8817eedfcea0ab0e806/pipelines/aggregation_reproject.py),
[merge](https://github.com/mapterhorn/mapterhorn/blob/077e6530bf410ce756fba8817eedfcea0ab0e806/pipelines/aggregation_merge.py) and
[utilities](https://github.com/mapterhorn/mapterhorn/blob/077e6530bf410ce756fba8817eedfcea0ab0e806/pipelines/utils.py)
show cubic-spline horizontal warping, nodata filling from lower-priority sources,
Gaussian blending at source/nodata seams and 2×2 averaging for lower zooms.
Intermediate nodata is -9999; remaining nodata is encoded as zero when tiled.
There is no exported per-pixel validity mask. A sampled ocean z12 tile is entirely
zero; its z15 child is absent. Inland water/coastal treatment is not a globally
verified hydrological contract.

Sources are grouped by delivery maxzoom, highest first, then lexical source name;
this is not an explicit accuracy/confidence ranking. Local maxzoom is selected
to oversample source grid spacing. Seam processing uses a 150-projected-metre
working buffer; this does not imply a fixed 150-ground-metre blur everywhere.
Vertical values are rounded by zoom: 1 m at z≤11, 0.5 m at z12, 0.25 m at z13,
0.125 m at z14, 0.0625 m at z15, successively halved to 1/256 m at z19.
These are storage increments, **not vertical accuracy**.

**Unresolved vertical reference:** no documented common output datum was found.
Warp configuration declares horizontal EPSG:3857 without an explicit output
vertical target. Whether GDAL/source CRS implicitly transforms any particular
input was not established. Copernicus documents EGM2008; the identified Swiss
files carry LN02. Do not assume those are identical or that every source has
been normalized vertically. Numerical differences below are not datum validation.

## Relevant datasets and resolution (E)

The live [attribution catalogue](https://download.mapterhorn.com/attribution.json)
has 151 sources. [Coverage](https://mapterhorn.com/coverage/) and decoded vector
coverage tiles identify candidate sources at our locations; source priority and
file lists support regional interpretation, but do not prove the winning source
at every pixel or in a blended seam.

| Region | Mapterhorn source support | Comparison meaning |
| --- | --- | --- |
| Tryfan / Eryri | `ukwales`: Wales **1 m DTM**, Welsh Government/NRW; catalogue access year 2025; underlying 2020–2023 LiDAR programme | Substantially finer source support than the sampled AWS EU-DEM; local z16 tiles valid, tested center z18 absent |
| Riffelhorn | `swissalti3d`: published 0.5 m grid, catalogue access 2026; file list contains the same four **2024 0.5 m LV95/LN02** assets identified in Meridian's historical catalogue | Fine heightfield source evidence already familiar from research; z17 valid, tested center z18 absent; does not reopen reconstruction |
| South Downs / Cambridge | `ukengland`: Environment Agency **1 m composite DTM**, access 2025 | AWS already supplies UK LiDAR in the sampled tiles; little matched-grid numerical difference |
| Nepal fallback control | Global `glo30`: Copernicus **1 arc-second / nominal 30 m DSM** | Vegetation/buildings can be included; not a universal bare-earth DTM. Local delivery stops at z12 in the inspected close view |
| Inspected Swiss western coverage edge | `swissalti3d`, `itaosta` **2 m** and `tinitaly` **10 m**, plus GLO-30 candidate support | Heterogeneous source transition, not a presumed national-border seam |

Primary upstream references: [Wales LiDAR](https://datamap.gov.wales/maps/lidar-data-download/)
and [programme metadata](https://datamap.gov.wales/layers/geonode:welsh_government_lidar_tile_catalogue_2020_2023/metadata_detail),
[EA composite](https://www.data.gov.uk/dataset/01b3ee39-da3f-47b6-83da-dc98e73a461f/lidar-composite-dtm-2022-1m),
[swissALTI3D](https://www.swisstopo.admin.ch/en/height-model-swissalti3d),
[Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM),
[Aosta DTM](https://geoportale.regione.vda.it/download/dtm/),
[TINITALY](https://tinitaly.pi.ingv.it/Download_Area1_1.html).

Grid spacing is not measurement accuracy. Swisstopo describes both 0.5 m and 2 m
products, possible oversampling, and acquisition-dependent accuracy: approximately
0.3 m for newer LiDAR, 0.5 m for older LiDAR, and 1–3 m for high-mountain stereo.
Copernicus is an edited multi-acquisition DSM; acquisition history is not the
Mapterhorn catalogue's access year. Catalogue entries elsewhere reach 0.25 m
(e.g. Zurich); no sub-metre accuracy or coverage claim is made from those entries.

At Tryfan, 512-pixel delivery has ground spacing approximately **1.434 m at z15**
and **0.717 m at z16**; the latter oversamples the stated 1 m source. At Riffelhorn,
**1.660 m at z15** and **0.415 m at z17** likewise differ from the source grid.
Screen detail and native mesh LOD are additional limits. A close view is not proof
that metre-scale terrain is represented by metre-spaced geometric vertices.

## Rights, attribution and provenance

**E:** [Mapterhorn code](https://github.com/mapterhorn/mapterhorn) is BSD-3-Clause.
Data rights remain source-specific. Official downloads/mirroring and examples
support experimental use; no requirement that Meridian must self-host was found.
The [attribution page](https://mapterhorn.com/attribution/) supplies source licences,
but a short aggregate credit is not proof of compliance with every upstream term.

Wales/England use OGL; Swiss [free-geodata terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices)
permit redistribution/processing/commercial use with **©swisstopo**. Aosta/TINITALY
use CC BY 4.0. Copernicus requires its full source notice, with modified-product
wording where applicable. Evaluation credits include Mapterhorn and these relevant
producers; no provenance UI is introduced. TINITALY's dataset citation is Tarquini,
Isola, Favalli, Battistini and Dotta (2023), TINITALY v1.1, INGV,
[doi:10.13127/tinitaly/1.1](https://doi.org/10.13127/tinitaly/1.1).
Caching/derivative use is supported by these inspected open-data terms subject to
their conditions, not a blanket BSD licence. A public global client still needs
source-specific notice review, including sources beyond this small comparison.

The [visible-source example](https://mapterhorn.com/examples/attribute-visible-sources/example.html)
uses a separate coverage index and source catalogue. Its z12 parent lookup returns
candidate-source lists; inspected [index generation](https://github.com/mapterhorn/mapterhorn/blob/077e6530bf410ce756fba8817eedfcea0ab0e806/pipelines/create_coverage_index.py)
simplifies/buffers coverage, not final winner/blend masks. Vector coverage and the
coverage index are distinct products. Neither lets Meridian reliably say which
dataset contributed a clicked geometry sample, its weights, acquisition/version
or confidence. Provider credit, candidate coverage, actual provenance and quality
are different concepts.

Incremental aggregations reuse unchanged inputs; downloadable archive catalogue
includes hashes. Hosted URLs remain mutable; response hashes/headers were recorded
locally. No per-tile immutable source revision contract was established.

## Controlled comparison and reproduction (M)

Only a private evaluation Vite loader substitutes `visualTerrainConfig.ts`:
**AWS**, **Mapterhorn 512 / z14 geometry / z15 relief**, and a limited
**Mapterhorn z17 / z17** detail probe. No product selector, environment flag or
production import exists. Fresh browser/map instances per policy avoid in-place
source replacement and the historical paint/RTT-cache comparison issue.

Playwright Chromium **151.0.7922.34**, 1440×900, device scale 1, en-GB,
Europe/London; wait for loaded tiles, native idle and 400 ms settling. Real terrain,
OpenFreeMap and configured satellite imagery; only Weather is synthetic. Camera,
paint, elevation-ramp, sky, projection, terrain configuration and mesh size match
exactly between accepted AWS/Mapterhorn pairs. Protected source-file hashes match.

| Scene / purpose | Center lon, lat | Zoom | Pitch | Bearing |
| --- | --- | --- | --- | --- |
| Tryfan landscape / planning / close | -3.999, 53.115 | 9.4 / 11.4 / 13.2 | 45° / 45° / 55° | 0° |
| Riffelhorn landscape / planning / close | 7.76121329, 45.97910794 | same | same | 0° |
| Mountain detail, three source policies | corresponding mountain center | 16.2 | 55° | 0° |
| South Downs rolling | -0.766, 50.908 | 11.4 | 45° | 0° |
| Cambridge flat | 0.12, 52.20 | 11.4 | 0° | 0° |
| Tryfan rotation | same close center | 13.2 | 55° | 90°, 180° |
| Swiss source edge | 7.6965, 45.94 | 14.2 | 45° | 0° |
| Menai coastline | -4.105, 53.252 | 13.2 | 45° | 0° |
| Open-water control | -4.08, 53.34 | 13.2 | 45° | 0° |
| Nepal global fallback | 86.86, 27.98 | 11.4 / 15.2 | 45° | 0° |
| Snowdonia route and rain | -4.073, 53.102 | 11.4 | 45° | 0° |
| Riffelhorn satellite | same close center | 13.2 | 55° | 0° |
| Tryfan elevation colors | same planning center | 11.4 | 45° | 0° |

These purposes are not universal zoom thresholds. The original `anglesey-coast`
capture name is misleading: it shows open water, so an actual Menai coast pair was
added. No coastal claim relies on that first frame.

**Native implementation caveat:** 512-pixel sources select lower canonical tile
zooms at a given map camera than 256-pixel sources. Installed
`node_modules/maplibre-gl/src/tile/terrain_tile_manager.ts` scales terrain tile
size and uses deltaZoom 1; mesh size/quality remain unchanged. The preparation
shader `src/shaders/glsl/hillshade_prepare.fragment.glsl` corrects pixel spacing
but also amplifies derivatives according to actual tile zoom below z15.
A one-level difference there changes that factor by approximately **2^0.3 ≈ 1.23**.
Therefore identical style does not imply identical native contrast/mesh sampling
response. Numerical height comparisons and satellite silhouettes help separate
information gain from this effect; no correction/renderer retuning was introduced.
At Tryfan close, visible geometry reaches z14 AWS versus z13 Mapterhorn; visual
relief z15 versus z14, with 256 versus 512 decoded dimensions.

Run from repository root, one browser phase at a time, without concurrent heavy
build/test/browser work:

```sh
node scripts/atlas/capture_terrain_foundation.mjs aws core
node scripts/atlas/capture_terrain_foundation.mjs mapterhorn core
# Repeat aws and mapterhorn with: extended, operations, controls
node scripts/atlas/capture_terrain_foundation.mjs mapterhorn-extended extended
python scripts/atlas/probe_terrain_foundation.py
node --test scripts/atlas/test_terrain_policies.mjs
```

Python needs existing NumPy/Pillow; it is a bounded live probe, not CI or the
analytical sampler. Satellite uses existing optional imagery configuration.
Ignored `test-results/atlas-terrain-foundation/` contains **42 captures**, camera/style
manifests, response/image/source-code hashes, redacted diagnostics, external source
records and numeric measurements. No permanent screenshot estate, provider archives,
new dependency, external data/private access or acquisition programme was added.
These products are temporary evaluation output, not promoted terrain assets.
Live service/browser changes preclude promised future byte-identical images.

## Visual, numerical and boundary findings (M)

- **Landscape:** major mountain masses broadly agree; Welsh connected ridges and
  valleys gain definition. Broad Alpine views show smaller proportional changes
  and substantial existing detail. No uniform global improvement is established.
- **Planning:** the most useful mountain gain: distinct ridge shoulders, channels,
  summit forms and Swiss moraine/ledge structure replace much smoother AWS forms.
  Labels and roads remain readable. Fine texture alone is not semantic rock identity.
- **Close/detail:** clearer mountain silhouette and slope structure persists.
  Extending Mapterhorn ceilings adds finer relief at z16.2, but much of the useful
  gain is already visible with existing ceilings. Welsh delivery reaches local z16;
  Swiss relief reaches z17. Repetitive steep-face banding/striping and smoothing
  remain; their source-versus-derivative/mesh origin is unresolved. No accuracy or
  true-3D-cliff claim follows.
- **Controls:** South Downs major scarp/valley forms remain similar, with somewhat
  stronger presentation; Cambridge stays comparatively quiet. Matched-grid numbers
  explain why England is not the same information gain as Wales/Switzerland.
- **Rotation:** mountain gains persist at 90° and 180° under geographically fixed
  illumination; shading rotates on screen with geography. No camera-specific winner
  or proof against every perceptual relief inversion is claimed.
- **Overlays:** elevation coloring remains usable. Normal GPX import
  `scripts/route/fixtures/snowdonia-smoke.gpx` retains 3.6 km, 253 m ascent,
  308 m descent, about 1 h 35 min. Eight real AWS z15 analytical tile responses
  occur in the Mapterhorn route phase. Uniform synthetic 1 mm / 1 h precipitation
  through the unchanged Weather renderer preserves route/label legibility; it is
  not an observed forecast or comprehensive overlay test.
- **Satellite:** geometry/silhouette differences persist with native hillshade
  suppressed. Photographed illumination and draped/stretched imagery remain;
  neither source supplies improved appearance observations in this task.
- **Water/global fallback:** Menai shoreline remains visually coherent in inspected
  frames. Open-water queried visual elevation is zero for Mapterhorn versus negative
  AWS bathymetry. Nepal planning retains recognizable major forms; its closer view
  retains z12 parent DEMs after missing children, so zooming closer supplies no new
  high-resolution source information there.

Decoded diagnostic z15 tiles cover the same geographical footprint. Mapterhorn's
512 grid is averaged 2×2 onto AWS's 256 grid, with explicitly fixed diagnostic
registration. This does **not** modify production pixel registration/interpolation.
No independent ground truth was acquired; differences are not accuracy scores.

| One sampled tile | Mapterhorn−AWS mean, m | RMS difference, m | 95th absolute difference, m | AWS response source metadata |
| --- | --- | --- | --- | --- |
| Tryfan, 15/16020/10656 | +5.653 | 19.023 | 38.271 | EU-DEM `eudem_dem_5deg_n50w005.tif` |
| Riffelhorn, 15/17090/11660 | −40.989 | 73.253 | 125.949 | EU-DEM `eudem_dem_5deg_n45e005.tif` |
| Downs, 15/16314/10983 | +0.071 | 0.124 | 0.238 | UK LiDAR `LIDAR-DTM-2M-SU81.tif` |
| Cambridge, 15/16394/10794 | +0.018 | 0.161 | 0.305 | UK LiDAR `LIDAR-DTM-2M-TL45.tif` |

Higher valid Mapterhorn tiles differ from bilinearly expanded z15 parents:
Tryfan z16 residual RMS **0.195 m**, 95th absolute **0.414 m**; Riffelhorn z17
**0.255 m / 0.529 m**. This rules out exact duplication of that simple parent
interpolation in the sampled tiles, not filtering/rounding effects or an accuracy
claim. MapLibre `queryTerrainElevation` in capture manifests includes exaggeration;
it must not be confused with decoded heights or route elevation.

**Source edge:** public coverage establishes a western swissALTI3D candidate edge
around 7.6965°E at 45.94°N. One paired view and three 200 m east-west transects
(45.939°, 45.940°, 45.941°N, 5 m steps, z16 sampling) show no isolated abrupt height
step: largest adjacent changes are approximately **1.57 m over 5 m** on this slope.
Texture/resolution heterogeneity remains visible. Blending and coarse coverage
metadata prevent precise winner attribution. This is a useful negative finding at
one edge, not global seam validation or vertical-normalization proof.

## Operations, validation and limits

42 captures settle with valid terrain, zero page exceptions and no non-DEM HTTP
failures. **58 actual Mapterhorn 404 responses** occur: eight in the extended Welsh
probe, fifty across sparse-delivery/projection/navigation operations. They are
reported, not counted as success or hidden. Normal ceilings/core/controls have no
HTTP errors. MapLibre's native parent handling retains usable terrain; correctness
across cold starts, all holes and provider outages is not established.

Request-failure diagnostics retain **102 AWS-phase / 83 Mapterhorn-phase
ERR_ABORTED cancellations**, including projection/visibility changes. No other
transport failure was recorded. Globe/terrain transitions 2.8→5.5→2.8→11.4 pass
for both sources; an animated Mapterhorn pan/zoom/rotation settles correctly.
OpenFreeMap's existing shield-filter warnings remain.

For the eight core scenes, including initial view, successful response bodies total
approximately **57.2 MB AWS / 28.5 MB Mapterhorn**, with **509 / 234** recorded DEM
responses. These are observed browser sessions, not equal tile footprints, wire-byte
benchmarks or a speed guarantee: 512 pixels changes selection/request count, cache
conditions vary, and native GPU preparation differs. At the same geographic z15,
Tryfan tile bodies are 84,085 / 171,372 bytes and Riffelhorn 86,295 / 178,056 bytes;
Mapterhorn has four times the pixels. WebP is not always smaller per requested tile.
Native decode succeeds. Headless settled-frame times are not interactive-FPS tests;
some detail views take tens of seconds. Multi-browser/mobile behavior, cold-cache
responsiveness, prolonged availability and large-scale traffic remain untested.

Deterministic policy tests cover the evaluation loader's narrow scope, correct
512/Terrarium ceilings, unchanged native paint/sky/exaggeration, satellite suppression
and actual AWS analytical mock requests/decoding. Live service checks are separate
from CI. All nine focused policy tests pass. The active Node suite reports 136
passes, zero failures and one live-publication test skipped (137 tests), using an
empty data-root stand-in and synthetic publication fixtures. The clock-sensitive
Forecast Workspace test passes unchanged in this run. ESLint and TypeScript/Vite
application build pass; the existing large-chunk warning remains. Build used the
ignored application-only Vite config to omit external GFS materialization and
public copying. Full Weather publication, unrelated Python research suites and
other browsers were not run. New JS syntax checks, Python compilation, diff
whitespace checks and unchanged-production-source checks pass.

## What this establishes for the next decision

**M:** better regional source information can materially improve the current
production heightfield without custom rendering or analytical migration. English
controls and Nepal show why global browsing must remain honest about uneven support.
**E:** the same service can provide coarse global coverage and regional detail, but
delivery density, DSM/DTM semantics, datum, seam processing, licence and revisions
do not collapse into a single URL or resolution number.
**H:** decide whether to adopt this public service contract, obtain clarification,
or require Meridian-controlled normalization/hosting before implementation. Specify
acceptable parent fallback and attribution/versioning requirements first. No evidence
requires exceptional regional data globally, reopening cliff reconstruction,
altering analytical elevation, imagery, lighting or implementing a resolver now.
