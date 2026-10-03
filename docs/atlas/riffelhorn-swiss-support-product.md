# Riffelhorn Swiss support terrain product

Recorded 2026-10-04; official metadata accessed 2026-10-03. Baseline:
`12945b9751ca30df2863bdef096e16781251d7eb`. This is one bounded acquisition and
unreconciled product task, not a new Lab, reconciliation experiment or resolver.
Production remains AWS. **M** = MERIDIAN EVIDENCE; **E** = EXTERNAL EVIDENCE;
**H** = RESEARCH HYPOTHESES / DIRECTIONS. Measurements concern preparation fidelity
and disagreement between products, not independent elevation accuracy.

## Purpose and selection

**M:** the [earlier prototype](riffelhorn-regional-terrain-prototype.md) retained
useful Swiss terrain but introduced false walls at its AWS join. The
[reconciliation investigation](riffelhorn-terrain-reconciliation.md) found mixed
broad/fine disagreement. Its discrepancy-dependent diagnostic widths reached
2.50 km (95th percentile approximately 2.21 km), exceeding the original crop's
maximum 1 km inward support. Those widths were not accepted transition designs.

The protected interior is a **1.5 km radius around LV95 [2625000,1092000]**:
[geometry](riffelhorn-support-interior.geojson). The 64-sided CRS84 polygon encloses
the original 2 km square, Riffelhorn/Riffelsee and local benchmark camera targets.
It is a preservation intent for later integration, not validated production
coverage or a guarantee that every landscape viewport fits inside it.

One conservative engineering selection supplies **3.5 km minimum native source
support beyond that interior**: whole official kilometre tiles covering LV95
`[2620000,1087000,2630000,1097000]`, 10 Ã— 10 km / 100 kmÂ². This leaves about 1 km
margin beyond the earlier maximum diagnostic. Aligning the outer rectangle with
distribution units makes acquisition and expansion reproducible; its edge is
**not** a proposed seamline. No mathematically optimal collar is claimed. The
selection captures northern valley terrain and southern high/glaciated terrain,
allowing the previous north/south pattern to be tested beyond the research crop.

This is enough support for the next reference/support assessment. Whether a fit
or transition is legitimate still depends on stable terrain, height semantics,
source quality and an explicit product/integration decision.

## Official material and acquisition

**E:** the official [product documentation](https://www.swisstopo.admin.ch/en/height-model-swissalti3d),
[December 2024 update](https://www.swisstopo.admin.ch/en/height-model-swissalti3d-update-20241220)
and [2024-2 release report](https://www.swisstopo.admin.ch/dam/de/sd-web/Zca1yaqlIgTp/swissALTI3D-release-2024_2_de_bf.pdf)
identify a terrain model without vegetation/buildings, supplied in whole kilometre
tiles. This selection uses the **2024 / 2024-2 Valais generation**, retaining
consistency with the completed experiments. Release information identifies
2021/2022 LiDAR and 2023 photogrammetric updates; technology, density, observation
epoch and accuracy vary. A nominal STAC year is not the observation date of every
cell. The distributed 0.5 m grid is not independent 0.5 m measurement resolution.

**M:** the official catalogue still listed all 100 selected 2024 assets. Their
names follow `swissalti3d_2024_{x}-{y}_0.5_2056_5728.tif`, with x=2620â€¦2629 and
y=1087â€¦1096. [Acquisition record](riffelhorn-support-acquisition.json) enumerates
every exact URL, retained path, bounds, bytes, official item properties and SHA-256.
[Official verification](riffelhorn-support-official-verification.json) records that
all 100 local hashes match official STAC SHA-256 multihashes. Four canonical files
were reused from the earlier estate; **96 were downloaded**, with two workers.
No unrelated products or newer generation were acquired.

Inputs are float32 TIFFs, 2000 Ã— 2000 cells each, 0.5 m LV95 grids, EPSG:2056,
declared nodata âˆ’9999 and LN02 / EPSG:5728 heights in metres. All 400 million cells
were scanned: **zero nodata cells**. Total source storage is **1, 667,166,026 bytes**;
the four reused files account for 65, 607,404 bytes. Source identity:
`b24a4fdc7b378ba79d442d0ce216a031dfb95a6bc6eed5ad9c33be61175651f4`.

**E:** [swisstopo OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices)
permit processing and redistribution, including commercial use, subject to credit.
The source/product metadata and evaluation map retain **Â©swisstopo**. These are
custom terms, not an inferred licence based on software licensing.

## Product preparation and delivery contract

**M:** `scripts/atlas/riffelhorn_support.py` creates a relative-path native
`source-mosaic.vrt`, referencing the canonical inputs without copying a physical
mosaic. It then makes a globally aligned Web Mercator hierarchy using the proven
Terrarium encoder and a fixed two-dimensional horizontal operation. No vertical
operation, offset, co-registration, reconciliation, feathering or AWS fill occurs.
LN02 numbers are preserved.

| Property | Contract |
| --- | --- |
| Source mosaic | 20000 Ã— 20000 / 0.5 m LV95, full 100 kmÂ² selection |
| Output | EPSG:3857, XYZ, 256 Ã— 256, lossless RGB PNG |
| Encoding | Terrarium: RÃ—256+G+B/256âˆ’32768 metres |
| Levels | z12â€“18; area-average z12â€“17, bilinear z18 |
| Warp | GDAL 3.9.3 / rasterio 1.4.3, one thread, tolerance 1eâˆ’9 pixels |
| Missing support | Omit whole partial/nodata tiles; no alpha, zero-height or global fill |
| Quantization | 1/256 m increment, maximum encoding rounding error 1/512 m |
| Heights | LN02 preserved; no established equivalence to AWS |

Each tile's complete curved footprint must lie inside source support, including
a 0.5 m guard; every warped pixel must be finite. This differs deliberately from
v1's AWS-padded composition. Partial tiles cannot become anonymous invented Swiss
terrain. The full native mosaic retains source support that is omitted from web
delivery. **Product coverage therefore varies by zoom**, defined by the manifest's
tile inventory, and is distinct from source coverage and protected interior.

At latitude ~46Â°, output ground spacing runs from approximately 26.6 m at z12 to
0.415 m at z18. The last level slightly oversamples the distributed source grid;
delivery zoom is not measurement resolution. Native MapLibre mesh/view LOD further
limits effective displayed detail. Lower levels generalize by averaging.

| Zoom | Supported tiles |
| --- | ---: |
| 12 | 1 |
| 13 | 4 |
| 14 | 25 |
| 15 | 121 |
| 16 | 506 |
| 17 | 2118 |
| 18 | 8654 |

Total: **11,429 tiles / 930,914,852 bytes**, first generation **770.163 seconds**.
Compared with the earlier 547-tile / ~42 MB composed product, this is about 21Ã—
the tile count and 22Ã— tile storage for 25Ã— source area. It remains manageable
locally but does not establish a production hosting/cache strategy. At z18,
466 perimeter candidates were omitted. There are no complete regional tiles below
z12. The benchmark fits inside the one z12 tile; the entire protected circle and
outer source selection do not have identical per-level delivery footprints.

Product identity:
`1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea`.
[Reproducibility record](riffelhorn-support-reproducibility.json) records a complete
independent rebuild and compares every tile hash, the manifest and native VRT.
Generation timestamps/timing are separate from deterministic identity.

## Metadata and provenance

The [source/product record](riffelhorn-support-product.json) actively uses Atlas's
[metadata foundation](terrain-source-product-architecture.md), without importing
it into production. Source revision identifies all 100 authoritative input hashes;
product revision identifies preparation parameters, software and tile hashes.
The source selection, per-level product coverage, valid delivery support and
protected interior are independently represented. **Transition support remains
explicitly unknown.** No fallback is declared for this pure Swiss product.

A small `uniform` contribution option describes one known immediate dataset
contributing throughout valid pixels, avoiding a meaningless all-one mask. It
requires one complete contributor. It does not imply uniform measurement epoch,
technology, quality or confidence. No universal provenance mask/system is added.
The product records DTM semantics, preserved LN02, rights, processing and unknown
measurement resolution/information ceiling. Renderer strength is not provenance.

## Fidelity checks

**M:** [measurements](riffelhorn-support-measurements.json) retain five separated
z18 sectors, not one favourable benchmark. Across 4,500 sample points, decoded
tiles differed from independent native bilinear interpolation by at most
**0.002075 m**. Five strips across adjacent tile joins, compared with independent
512-pixel joint reprojections, differed by at most **0.004639 m**. These include
float32/reprojection effects as well as encoding. Synthetic globally aligned
window tests produce identical values on either side of a tile partition.

These checks support millimetric transfer fidelity in sampled high-zoom sectors;
they do not validate all terrain accuracy, all possible tile joins, or every
lower-zoom generalization. The official source's scientific limitations remain.

## Expanded Swiss/AWS diagnostic

**M:** a 1000 Ã— 1000 diagnostic grid covers the whole native selection at 10 m.
Swiss values are 20Ã—20-cell area averages; AWS z15 is sampled by pixel-centre
bilinear interpolation across tile boundaries after the same horizontal operation.
169 AWS tiles were reused/fetched diagnostically, with hashes and HTTP records.
Neither production analytical sampling nor source policy changes. Filtering the
difference for characterization creates no blended terrain product.

| Region | Mean Swissâˆ’AWS m | Median m | RMS difference m |
| --- | ---: | ---: | ---: |
| Entire 100 kmÂ² | âˆ’5.19 | +1.29 | 30.23 |
| Protected 1.5 km circle | âˆ’31.41 | âˆ’5.75 | 62.08 |
| Radius 1.5â€“2.5 km | âˆ’11.90 | +2.38 | 40.08 |
| Radius 2.5â€“3.5 km | âˆ’6.12 | +1.96 | 30.56 |
| Radius 3.5â€“5 km | âˆ’1.85 | +0.91 | 22.80 |
| NW quadrant | +3.33 | +3.43 | 16.92 |
| NE quadrant | +3.91 | +4.98 | 13.31 |
| SW quadrant | âˆ’5.73 | âˆ’1.74 | 29.32 |
| SE quadrant | âˆ’22.25 | âˆ’5.79 | 48.29 |

Full range is **âˆ’163.64 to +195.12 m**; 5th/95th percentiles âˆ’80.69/+25.35 m.
The original crop on this same diagnostic grid has RMS 68.79 m. These values must
not be substituted for the earlier twelve boundary transects, which sampled a
different set of locations.

The expanded maps retain a broad negative southern/eastern corridor extending
past the old crop and finer alternating ridge/channel differences. Northern
terrain is closer on average, not equivalent. Correlation at 250 m is ~0.71 eastâ€“
west / 0.67 northâ€“south; at 1 km ~0.47/0.22; at 2 km ~0.37/âˆ’0.10. This is mixed,
anisotropic and nonstationary disagreement. Removing a diagnostic Gaussian
Ïƒ 250 m component leaves RMS 15.23 m: finer representation differences remain.
The selection materially improves characterization without demonstrating that
the disagreement decays to zero or that a defensible seam exists.

**H:** glaciated/temporally variable southern sectors, source epoch differences,
surface representation and global generalization are candidates for later
interpretation. Causes are not established per cell. AWS hosted vertical semantics
and exact local lineage remain uncertain; no constant datum correction is justified.
Preparation errors measured in millimetres cannot explain these tens-of-metres
differences, but differing source representations/diagnostic resampling still
affect the comparison.

Future stable-terrain analysis needs defensible exclusions/downweights for glaciers,
snow/ice, water, temporal changes, extreme representation differences, source edges
and nodata. Neither basemap labels nor gentle slope automatically establish stable
terrain. Here slope<0.15 still has RMS disagreement 45.46 m; slope>1 has 30.93 m.
No final stable-terrain mask or co-registration is produced.

## Real application inspection

The evaluation-only Vite plugin changes visual delivery only: local pure Swiss
source, minzoom12/maxzoom18 and bounds. Production files are not replaced on disk;
analytical AWS remains untouched. Native 128 mesh, strengthened IGOR at 315Â°/map
anchor, colors, curve, atmosphere/projection and exaggeration 1.45 are unchanged.
No satellite, Weather, route, imagery or camera policy is tuned.

Captures use Chromium, 1440Ã—900, DPR1, en-GB/London. Central location
`[7.76121329,45.97910794]`: landscape z9.4/pitch45/bearing0; planning11.4/45/0;
close13.2/55/0; detail16.2/55/0; rotation15.2/55/180. Four support views at
z14.2/pitch55/bearing0 use native points [2625000,1094800], [2625000,1089200],
[2622200,1092000], [2627800,1092000]; exact geographic cameras are
[recorded](riffelhorn-support-cameras.json). Same-camera AWS references are retained.

**M:** close/detail and rotated benchmark views retain the earlier gains: channels,
ledges and fine roughness are much more legible than the smooth same-camera AWS
reference. North/east support views show coherent local slope/channel structure
beyond the original crop; southern support exposes substantial glacier/surface
texture. These are visual findings, not evidence of individual feature accuracy
or validated glacier epochs.

**Negative result:** no regional DEM is loaded at z9.4 or 11.4, so those views show
flat terrain rather than a complete regional landscape. At outer/visible support
limits, captures show abrupt walls, flat draping and black voids. The west camera
reports zero rendered centre elevation despite a retained z14 centre tile; its
native coverage/cache/terrain-query path was not further isolated. The southern
view also has a large foreground void. Missing coarse parents/perimeter support
cannot be presented as a seamless integration. These are regional delivery
limitations, distinct from the earlier Swiss/AWS discontinuity: **this product
contains no AWS join**. No attempt was made to fix them by composing or blending.

[Browser record](riffelhorn-support-browser.json) retains exact cameras, image and
production-module hashes. Eighteen paired captures and full request records live
outside Git. The final nine-view Swiss run recorded 299 successful local responses,
124 honest404 responses, ~30.8 MB of bodies and no page exceptions. Five failed
requests and 126 console errors remain recorded; the latter include missing support
and intentionally unavailable Weather. Scene settle durations (~3.2â€“24.6 seconds)
include tile loading, camera/renderer work and an explicit one-second wait: they
are not a latency benchmark. Tile sizes are median 82,079 bytes, p95 ~100, 601,
maximum 133, 755. Local cache headers are public/max-age 3600, not a production CDN
commitment. Panning/rotation complete, but the missing-support artifacts prevent
claiming clean regional browsing.

The first isolated server omitted CORS headers on 404 errors; a separate loopback
evaluation server fixes that diagnostic defect without modifying the frozen
preparation script/build identity. Missing tiles remain honest 404s. This fixes
observability, not source support. MapLibre's `queryTerrainElevation` in the
installed version includes exaggeration; captured query values are renderer
diagnostics, not LN02 analytical heights.

## External estate and reproduction

All paths below are relative to `MERIDIAN_DATA_ROOT`; no large asset is committed:

- `sources/atlas/riffelhorn/swissalti3d-2024-support-v1/`: 96 originals, receipts,
  selected official STAC metadata and acquisition record.
- Four reused originals remain under `sources/atlas/riffelhorn/swisstopo-2021-2024/`.
- `derived/atlas/riffelhorn/riffelhorn-swiss-support-v1/`: native VRT, pure tiles,
  manifest and Atlas metadata.
- `experiments/atlas/riffelhorn-swiss-support-v1/`: timing, numerical report,
  diagnostic NPZ, maps/profiles and capture records.
- `cache/atlas/riffelhorn/riffelhorn-swiss-support-v1/aws-diagnostics/`: diagnostic
  AWS downloads; existing original cache reused where available.

Use the existing scientific environment (NumPy2.5.3, rasterio1.4.3/GDAL3.9.3,
pyproj3.7.2, Pillow12.3.0, Matplotlib). From the repository in PowerShell:

```powershell
$env:MERIDIAN_DATA_ROOT = 'C:/Users/gbsam/Documents/Projects/meridian-data'
$terrainPython = "$env:MERIDIAN_DATA_ROOT/earth-lab/.venv/Scripts/python.exe"
# Selection is one fixed extent; retained plan/receipts are the acquisition record.
& $terrainPython scripts/atlas/select_riffelhorn_support.py select
& $terrainPython scripts/atlas/riffelhorn_support.py acquire --plan "$env:MERIDIAN_DATA_ROOT/sources/atlas/riffelhorn/swissalti3d-2024-support-v1/metadata/selection-plan.json"
& $terrainPython scripts/atlas/select_riffelhorn_support.py verify-official
# Existing immutable products are verified, not overwritten. Fresh build example:
& $terrainPython scripts/atlas/riffelhorn_support.py prepare --suffix=-reproduction
& $terrainPython scripts/atlas/riffelhorn_support.py verify --suffix=-reproduction
& $terrainPython scripts/atlas/verify_riffelhorn_support_rebuild.py --suffix=-reproduction
# Primary build (no suffix) must exist for these explicit evaluation commands:
node scripts/atlas/write_riffelhorn_support_metadata.mjs
& $terrainPython scripts/atlas/check_riffelhorn_support.py
& $terrainPython scripts/atlas/riffelhorn_support_server.py  # separate terminal
node scripts/atlas/capture_riffelhorn_support.mjs support
node scripts/atlas/capture_riffelhorn_support.mjs aws
& $terrainPython -m unittest discover -s scripts/atlas -p test_riffelhorn_support.py
node --test scripts/atlas/test_terrain_metadata.mjs scripts/atlas/test_terrain_policies.mjs
```

On an empty estate run `prepare` without suffix for the primary product. On a
retained estate do not re-select merely to reproduce: use the frozen plan, then
verify hashes. Catalogue revisions could alter metadata; a new selection must be
reviewed rather than silently replacing this source identity. Compare rebuild
manifest identity, all tile hashes and VRT hash, not generation timestamps.

## Conclusion and next bounded step

**M:** one supported, authoritative 100 kmÂ² regional asset now exists, with explicit
protected interior and provenance. It preserves the interior gains and supports
substantially better regional/global characterization at a practical local cost.
It is **not production-ready regional delivery**: coarse-level and perimeter
support gaps remain, and no physically defensible global relationship or seam is
established. Production and normal startup remain independent of this estate.

**H:** the smallest next step is a bounded **global-reference/overlap assessment**
using this asset: establish which physical global height reference and stable-
terrain evidence could support later integration, with explicit mask requirements.
Keep pure Swiss source support separate from a future composed delivery hierarchy.
Do not assume AWS is the permanent reconciliation target. No further acquisition,
provider evaluation, fit, transition or resolver follows within this task.

## Validation and scope

- All 100 source hashes matched official checksums; all source cells checked for nodata.
- Complete independent rebuild matched 11,429 tile hashes, manifest and VRT.
- Five fidelity sectors / 4,500 samples; five independent tile-join checks.
- Synthetic terrain tests: 4 new support, 6 existing preparation, 7 existing
  reconciliation tests passed; existing reconciliation algorithms were not run
  against the new product.
- Active Node suite: 151 passed, 1 existing optional test skipped, 0 failed, using
  an empty data root. This includes 13 metadata and 11 terrain-policy tests.
- Lint passed. TypeScript and application production bundle passed through the
  existing application-only Vite validation config; external GFS materialization
  and public-data copying were deliberately omitted. Existing large-bundle warning
  remains. No publication/deployment was attempted.
- Source/product validation and documentation/reference checks passed. Production
  source/configuration, analytical sampler, App, Weather and Traverse have no diff;
  no normal module imports the new evaluation tooling or metadata foundation.

No external terrain estate or server becomes a CI/startup dependency. Browser
inspection is explicitly separate from deterministic tests. The source/product
metadata validator checks owned typed records, not an untrusted JSON schema.
