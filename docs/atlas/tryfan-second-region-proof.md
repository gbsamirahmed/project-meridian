# Wales / Tryfan second-region terrain proof

2026-10-05. Baseline `ba24e546fcb13dcdaf0bb01bf8550c3cf8c5c2dd`, clean `main`,
fetched `origin/main` at the same checkpoint (0 ahead / 0 behind).

**SUCCESS:** a real Welsh DTM selection enters the frozen hierarchy through the
existing registry, spatial eligibility, selector and MapLibre adapter. No frozen
contract or existing runtime change was necessary. The bounded regional elevation
foundation is established; no further elevation benchmark is recommended.
This proves portability and delivery, not terrain accuracy or reconciliation.
The next programme boundary is imagery/appearance, under a separate task.

## Evidence and source-selection gate

**EXTERNAL EVIDENCE:** the [Welsh Government download page](https://datamap.gov.wales/maps/lidar-data-download/)
publishes the national 32-bit DTM/DSM COGs and explicitly links OGL v3 for use of
this data. The [national catalogue](https://datamap.gov.wales/layers/geonode:welsh_government_lidar_tile_catalogue_2020_2023/metadata_detail)
declares 1m grid data and EPSG:27700. Its own licence field says “Not Specified”;
permission is supported by the official **data download** page, not inferred from
the catalogue's availability. A current HEAD of the selected DTM returned 200;
ETag `0x8DCE488A5BF1B2C`, last modified 2024-10-04. The 48.61GB national object
was **not downloaded**. HTML and access-header evidence are retained and hashed.
No new regional elevation was acquired.

| Serious candidate | Decision |
| --- | --- |
| Welsh Government national 2020–2023, 32-bit 1m DTM; local catalogue delivery11, 2021-03-02 | Selected: official, already retained, complete benchmark valid cells, useful bare-earth information and OGL derivative use. |
| [NRW historic archive](https://datamap.gov.wales/layers/geonode:nrw_lidar_tile_catalogue_archive/metadata_detail) | The completed [bounded reconnaissance](tryfan-lidar-reconnaissance.md) found older 1m acquisitions with partial coverage, no intersecting 0.25/0.5m record. No historic download or repeat survey. |
| [OS Terrain50](https://www.ordnancesurvey.co.uk/products/os-terrain-50) | Authoritative open alternative, but 50m postings are broad terrain, unsuitable to demonstrate this high-detail regional use. OS Terrain5 is a documented 5m product; no paid-service/licensing acquisition was needed given the finer public DTM. |

The matching DSM was deliberately not used: Atlas's physical terrain purpose
favours the provider's bare-earth DTM. The publisher cautions that filtering may
retain artificial obstructions; this is not an independently verified pure-ground
or true-3D model. No point-density, local accuracy or independent measurement
resolution was invented from its 1m distributed grid.

[OGL v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
allows reuse/adaptation subject to its terms. Retain attribution:
**Contains Welsh Government information licensed under the Open Government
Licence v3.0.** Research preparation is permitted; future public delivery must
carry the applicable notices and preserve exclusions/third-party rights, rather
than treating a software or portal licence as universal data permission.

## Frozen source and bounded preparation

**MERIDIAN EVIDENCE:** the established `tryfan-004` photographic benchmark is
EPSG:27700 `[264900,357800,267900,360800]`, centre `[266400,359300]`, 3×3km /9km².
Summit reference is `[266405,359387]`. The existing camera benchmark uses
`[-3.999,53.115]`. These were recovered from the retained manifest, promoted
[catalogue](tryfan-data-catalog.json) and `capture_native_relief.mjs`; no study
extent or support ring was invented.

Selected file:
`sources/atlas/tryfan/welsh-lidar-1m/rasters/tryfan-004-dtm-1m.tif`,
15,639,072bytes; SHA-256
`49c131d7de62e0df35f8e02c2f8db3161bfd37f24fea56060fcbb9e6d109b326`.
The 2026-09-24 retrieval used bounded HTTP range reads from
`https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dtm_32bit_cog.tif`.
All five retained source/catalogue/manifest files match their promoted hashes.
Only the DTM contributes to this product; the retained DSM was verified, not used.
The catalogue retains the 16 intersecting official tile IDs/URLs, all delivery11
dated 2021-03-02. Exact national mosaic revision and per-cell epoch mapping remain
unknown. The checksum identifies the retained subset, not a national release.

The GeoTIFF has 3000×3000 float32 cells, 1m XY grid, BNG horizontal CRS,
sentinel−9999, 9,000,000 valid /0 nodata cells. Height values are preserved as
native metre elevations. **The checked primary metadata/GeoTIFF does not establish
their vertical datum.** Prior local ODN labels and non-authoritative descriptions
are insufficient to assert an authoritative ODN declaration. The canonical
source records `unknown`; the product records `preserved` with that unknown
reference. It is neither LN02 nor silently harmonised with AWS. No vertical
transformation, fitted bias or registration was applied.

Final product: `derived/atlas/tryfan/tryfan-welsh-regional-v2`, immutable identity
`db8e4d87b5fa609d455d1e0f8ec3fdebc834579a7e102f69f4d0b0283efa690c`.
Manifest SHA-256
`b254a21b1ec346cc07b43d269d937b059851e95ac168565359a81d3872c69e54`.
The [lightweight preparation record](../../src/atlas/terrain/metadata/tryfanProductRecord.json)
pins software, operations, support and working hashes. Full tile/support inventory
and working rasters remain in `meridian-data`. Independent rebuild is in the
`-rebuild` directory; all manifest, tile, support and working hashes match.

The preparation reuses established Terrarium encoding and the Copernicus-tooling
unencoded parent operation, not a second processor architecture:

- z17 bilinear 2D reprojection, one thread, exact recorded horizontal operation;
- full destination-pixel footprints within source support plus a 2m interpolation
  guard; no extrapolation, common/AWS padding or encoded nodata;
- recursive 2×2 means of unencoded elevations, float64 accumulation /float32
  storage, equal **Mercator pixel-area** weights, strict missing-support propagation;
- independent 256px RGB PNG Terrarium encoding at each complete level;
- complete tile union polygonized into normalized OGC:CRS84 support with holes
  and disconnected components preserved. Native BNG metadata remains intact.

Recorded horizontal route is the installed PROJ OSGB36→WGS84 Helmert operation,
stated operation accuracy2m. Network grids disabled. This is coordinate
normalization, not empirical DEM co-registration or a local accuracy claim.
The exact 2D pipeline is passed to GDAL and used inversely for source-transfer
checks. It does not transform the raster's elevation values.

| Level | Complete tiles | Withheld partial tiles | Complete area, WGS84 km² | Approx. sample spacing near53.115° |
| --- | ---: | ---: | ---: | ---: |
| z13 diagnostic | 0 | 4 | 0 | 11.470m |
| z14 regional parent | 1 | 8 | 2.1595 | 5.735m |
| z15 regional parent | 10 | 17 | 5.3983 | 2.867m |
| z16 regional parent | 52 | 34 | 7.0183 | 1.434m |
| z17 interpolated source signal | 232 | 66 | 7.8282 | 0.717m |

z17 deliberately samples the 1m source signal; it does not create independent
0.717m observations. Higher camera zoom overzooms declared delivery. Renderer
mesh size128 and actual geometry/hillshade DEM levels remain separate. No z18
product or Swiss zoom range was copied. z14–17 suffice to exercise a complete
Tryfan parent/child chain; unsupported z13 hands off honestly rather than triggering
another source expansion. Partial tiles/cell counts and absent tiles remain in
the external inventory. No partial-mask decoder is needed to serve the complete
tile union truthfully.

Storage:295 tiles,23,889,573bytes (23.89MB decimal); working rasters46,691,533bytes.
Retained source15.64MB. Final generation129.05s; independent rebuild168.45s while
other validation ran. These are bounded observations, not performance benchmarks.
The first preparation retained immutable v1/rebuild records; its row-by-row
support geometry was overly fragmented for conservative footprint selection.
v2 corrects polygonization; **all terrain tile bytes remain identical**. This was
a preparation-support defect, not a contract/runtime gap or reconciliation change.

## Registration, selection and delivery

[Canonical source/product/hierarchy fixture](../../src/atlas/terrain/metadata/tryfanTerrainProof.ts)
uses existing entities and exact source/product revisions. Source coverage is
the retained BNG selection; product coverage/valid support are assessed complete
delivery-tile unions; each level has its smaller actual support. No protected
interior or transition support is invented. Parents reference the same
`welsh-2021-regional` family. Common terrain is the existing AWS compatibility
family, not newly acquired Copernicus or an unrelated regional parent.

The registry's existing CRS84 geometry form is used after preparation
normalization. The legacy common addressing extent is explicitly normalized to
the same query CRS for this proof; AWS assessed validity stays unknown. Normal
production registration remains unchanged. Source/product/height/time/rights
identity is recovered through canonical references; this is source-derived
terrain with one immediate contributor, no synthetic transition.

| Query | Deterministic result |
| --- | --- |
| Benchmark interior z17 | Welsh regional z17, source/product revision retained |
| Interior z14 after Welsh z17 | Welsh-derived parent, `within-family-lod` |
| Simulated unavailable z17 child | Eligible Welsh z16 parent, `regional-parent`, same-family refinement |
| Interior z13 | Explicit common fallback; no complete regional z13 tile |
| Actual regional-support edge /outside `[-4.023,53.115]` | Common fallback, explicit `source-family-handoff`, unresolved |
| Common-only request | Existing AWS family |
| Interior z18 request | Explicit z17 rendering overzoom; unchanged information ceiling |

The [decision/evaluation record](tryfan-second-region-proof.json) retains actual
requests, traces, selected product/representation/family/level identities,
adapter configuration and evidence hashes. Missing-child test is a labelled
metadata availability control; it does not delete or modify retained tiles.

`terrainProofGateway.mjs` is an **evaluation-only** XYZ endpoint. Each requested
whole-tile footprint goes through the same registry→selector→adapter, then reads
the selected complete local tile or declared legacy common cache. No point-only
eligibility is used to pretend an entire edge tile is supported. A tiny
floating-edge inset avoids coincident-coordinate roundoff; the source guard is
orders of magnitude larger. The gateway never combines contributors within a
tile. The AWS cache preserves ordinary original responses throughz15; fine common
requests explicitly resample z15 for renderer overzoom, adding no information.
Prepared local levels are not fabricated if absent.

One unified evaluation stream is necessary for MapLibre's single active DEM
source. Its maximum is derived from the selected regional adapter. The Vite
plugin only replaces the visual delivery export and exposes the existing map
for capture; source IDs, lifecycle, relief, projection, satellite and analytical
sampling code are untouched. This is a bounded development harness, not a new
production service, viewport resolver, availability engine or adopted boundary policy.

## Numerical and renderer evaluation

Independent source-transfer checks:59,392 z17 samples, unencoded RMS0.01989m,
95th absolute0.03777m, maximum0.42062m against independent source-cell bilinear
reconstruction under the declared horizontal operation. These measure
reprojection/sampling transfer, not world accuracy; the maximum is retained,
not replaced with a millimetre-fidelity claim. Encoding RMS0.001127m,
maximum0.001953125m. Independent parent checks match the arithmetic mean with
maximum float32 rounding0.00003052m. No source hashes changed.

| Within-regional pair | Child minus repeated mean-parent RMS | Max absolute |
| --- | ---: | ---: |
| z14→z15 | 0.8344m | 12.7273m |
| z15→z16 | 0.4414m | 9.7812m |
| z16→z17 | 0.2309m | 7.3671m |

These statistics use fully supported parent **cells**, including cells in
withheld partial tiles; they quantify ordinary finer terrain variation, not
accuracy or source translation. The exact aggregation test is the consistency
check. They are not ranked against the Swiss0.71m metric. Offline z13→z14
RMS1.581m does not make a partial z13 tile deliverable.

Captures:1440×900, actual MapLibre6.11.2, IGOR, unchanged strengthened relief,
exaggeration1.45, original basemap/camera/lifecycle. Nine matched cameras per
provider: established landscapez9.4/pitch45, planningz11.4/pitch45,
closez13.2/pitch55; parentz15.2/pitch0; childz16.2/pitch35; detailz17.2/pitch45;
child rotation180°; western source edge and outsidez16.2/pitch35. Seven continuous
1.5s zoom/rotation/lateral/outward sequences include moving captures and actual
loaded parent levels. Exact cameras and screenshot hashes are in the JSON.

**Inspected findings:** landscape/planning/benchmark-close geometry uses common
levels (roughlyz7–13); Welsh detail is not falsely asserted there. The regional
parent view uses geometryz14; child/detail views load regionalz15/16 alongside
coarser context. The local mountain retains ridge structure through refinement
and rotation. Against matched production AWS, Welsh terrain clearly exposes
sharper ridge segmentation, ledges/gullies and finer surface structure. This is
useful regional information, not independent validation of physical accuracy.

The support-edge view shows a conspicuous straight relief/geometry boundary.
Geographic transitions and the unsupported coarse source-family handoff can
change terrain character/shape during navigation. They remain explicitly
unreconciled; no offset, feather, common-datum fit, seam or transition was added.
This does not negate portability. Normal within-family refinement has no missing
regional parent beneath the evaluated summit/interior chain. No sustained tile
holes/flat missing-response regions were observed. Strong pitched-view faceting
and mesh limits are not claimed solved. Moving-frame evidence is bounded,
not a universal no-popping guarantee.

Hierarchy run:474 endpoint requests, all200;158 Welsh requests acrossz14–17,
316 common. Browser recorded472 responses and four navigation cancellations;
endpoint completion and browser-delivery counters have different timing scopes.
AWS control:221 requests/responses, all200. Both have zero page errors. Actual
basemap warnings include missing sprites and existing shield filters; no terrain
fetch failure was hidden. Cache retains196 original AWS tiles /19,001,627bytes;
warm renderer/cache reuse avoids repeated endpoint requests. No global mirror.
Screenshots and detailed request/navigation logs remain under
`experiments/atlas/tryfan-second-region-proof/captures` in `meridian-data`.

## Portability, limitations and acceptance

**MERIDIAN EVIDENCE:** existing registry, spatial engine, selector, delivery
adapter, contract types and production terrain files have zero diff from the
checkpoint. Provider-specific naming, BNG input, bounds and source paths terminate
at preparation/metadata. There is no Welsh/Swiss selection branch, LN02/LV95
assumption, radial band, Swiss filename logic or Copernicus regional parent.
The only corrected issue was preparer's support-union geometry. Existing AWS,
Swiss and generic fixtures continue to pass. No frozen-contract contradiction
or generic runtime extension was required.

All15 proof success conditions are met: defensible licensed real source; bounded
deterministic product; truthful metadata; same registration; regional interior;
regional parents; common fallback; LOD/handoff distinction; same adapter;
no Swiss special case; no required extension; recoverable provenance; actual
renderer refinement; unchanged production; independent analytical sampling.
Unknown native vertical datum, mutable upstream COG identity outside the retained
selection, horizontal-operation accuracy, coarse/support-edge handoff and mesh
limitations remain explicit. Selection/registration is not approval for numerical
fusion or public terrain deployment.

Production still uses AWS via registration→selection→adapter, geometrymax14,
visual-reliefmax15,256px/Terrarium, same endpoint/attribution. Analytical AWSz15
remains separately owned, with no use of Welsh terrain for gradients, route
elevation, timing or Weather altitude. Weather, Traverse, satellite, IGOR,
exaggeration, bundled worker and projection/style-restoration behaviour remain
unchanged. Production bundles contain no proof endpoint/product; normal startup
and CI require no `meridian-data`, local server, Welsh service or network asset.

**RESEARCH HYPOTHESES / DIRECTIONS:** this closes second-source elevation
architecture validation, not every composition/rendering limitation. No new
terrain research, further elevation benchmark or Riffelhorn repair is recommended.
Next work crosses to imagery/appearance: source/product metadata and regional
imagery hierarchy, likely SWISSIMAGE with acquisition-light assessment. None of
that work is started here. This is established-method reuse and engineering/
benchmark integration, not a new DEM processing invention.

## Reproduction and validation

Run from repository root; external commands are optional proof operations, never
normal CI. Existing retained DTM must match the pinned source hash. A network COG
subset re-extraction is an acquisition revision unless its values/bytes are
verified; do not silently replace the retained selection with a newer mosaic.

```powershell
$data='C:/Users/gbsam/Documents/Projects/meridian-data'
$python="$data/earth-lab/.venv/Scripts/python.exe"
$env:PROJ_NETWORK='OFF'
# Existing v2 is immutable; use a fresh suffix for another rebuild.
& $python scripts/atlas/tryfan_product.py prepare --data $data --suffix=-another-rebuild
& $python scripts/atlas/tryfan_product.py verify --data $data
& $python scripts/atlas/check_tryfan_product.py --data $data
& $python scripts/atlas/test_tryfan_product.py
& $python scripts/atlas/write_tryfan_record.py --data $data
```

Start the local cache in one terminal; it is a research control, not normal startup:

```powershell
& $python scripts/atlas/terrain_proof_cache.py --root "$data/cache/atlas/tryfan/second-region-proof/aws"
```

In another terminal, inspect/capture both configurations through the hierarchy:

```powershell
$captures="$data/experiments/atlas/tryfan-second-region-proof/captures"
node scripts/atlas/capture_tryfan_proof.mjs $data $captures hierarchy
node scripts/atlas/capture_tryfan_proof.mjs $data $captures aws
node scripts/atlas/record_tryfan_proof.mjs $data
```

Inspect `regional-parent`, `regional-child`, `regional-detail`, rotated and
`support-edge`/moving captures. Expect richer local terrain and an unreconciled
support edge, with common terrain outside. For unchanged normal application:
`npm.cmd run dev`, inspect AWS terrain, satellite restoration and zoom across5.5;
no local terrain service is needed.

```powershell
node --test scripts/atlas/test_tryfan_terrain.mjs scripts/atlas/test_terrain_runtime.mjs scripts/atlas/test_terrain_hierarchy_contract.mjs scripts/atlas/test_terrain_metadata.mjs scripts/atlas/test_terrain_policies.mjs
$testFiles=Get-ChildItem scripts/atlas,scripts/route,scripts/weather,scripts/ui -Filter test_*.mjs | ForEach-Object { $_.FullName }
node --test --test-concurrency=4 $testFiles
npm.cmd run lint
npx.cmd tsc -b
node --input-type=module -e "import {build} from 'vite'; import react from '@vitejs/plugin-react'; await build({configFile:false,plugins:[react()],publicDir:false,build:{outDir:'node_modules/.tmp/tryfan-proof-build'}});"
```

Validation: seven new semantic tests plus four synthetic preparation tests; source/
product/support hashes; independent source/encoding/parent calculations; exact
rebuild; matched renderer/navigation; AWS/Swiss/generic fixtures; full application
suite219 passed, one existing optional external-data skip; lint, TypeScript and
application-only build pass. Existing large-chunk warning remains. Local
documentation references and final diff checked. No normal build publishes
external terrain or Weather data as part of this task.
