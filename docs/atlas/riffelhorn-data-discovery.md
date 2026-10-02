# Riffelhorn / Riffelsee Swiss geodata acquisition

2026-10-02. **Suitable with documented limitations.** This is a bounded source
discovery, acquisition and provenance record, not a Lab, renderer or Atlas
architecture change. The [machine-readable catalog](riffelhorn-data-catalog.json)
records every asset URL, receipt, checksum, actual file properties and uncertainty.

## Selected experimental extent

The exact AOI is **[2624000, 1091000, 2626000, 1093000] in EPSG:2056
(CH1903+/LV95)**: 2,000 × 2,000 m, 4 km², centre [2625000, 1092000].
Its WGS84 envelope is [7.74826006, 45.97007496, 7.77417078, 45.98813946];
centre [7.76121329, 45.97910794], longitude then latitude. The WGS84 envelope was
transformed with pyproj, densifying each boundary with 21 points; no source raster
was reprojected. The projected rectangle is authoritative.

Official federal gazetteer results place Riffelhorn at [2624809.668, 1092252.405]
and Riffelsee within [2625005.863, 1092444.621, 2625116.26, 1092504.281]. The
selected square retains both, northern paths/alpine ground cover, steep rocky faces
and southern ice/debris/moraine transitions. It uses exactly four existing kilometre
tiles: **2624-1091, 2624-1092, 2625-1091, 2625-1092**. No AOI revision was needed.
The downloaded DTM spans 2189.576–2977.790 m LN02, about 788 m of relief.

## Official sources and actual acquisitions

Discovery used the [federal STAC API](https://data.geo.admin.ch/api/stac/v0.9)
with a bounded WGS84 query, followed by exact item requests. Official map metadata
and flight-strip footprints came from the
[federal map API](https://api3.geo.admin.ch/rest/services/api/MapServer), and names
from its SearchServer gazetteer. Exact queries and original responses are retained
externally. Boundary-touching neighbouring STAC items were excluded by the selected
projected tile footprints; filenames were not the only registration evidence.

| Product | Downloaded assets | Actual file information | Observation / update evidence |
| --- | --- | --- | --- |
| SWISSIMAGE | Four 2023 RGB COGs | 10000² each, 3 × uint8, 0.10 m distributed grid; YCbCr JPEG quality 95 | **25 cm native imagery** in all four tile metadata records; 2023 mosaic year |
| swissSURFACE3D Raster | Four collection-2021 COGs | 2000² each, float32, 0.50 m grid, LZW | Three tiles use 2021 LiDAR; northeast tile uses 2021/2022 |
| swissSURFACE3D | Four collection-2021 ZIPs containing LAS | LAS 1.2, point format 1; 50,546,426 points in total | Actual point timestamps: 2021-08-24, 2021-08-26 and northeast-only 2022-08-23 |
| swissALTI3D | Four 2024 COGs | 2000² each, float32, 0.50 m grid, LZW | Valais 2024/2 release: 2021/2022 LiDAR base and 2023 aerial-image change updates |

Original downloads total **896,360,770 bytes**; extracted LAS totals
1,415,300,836 bytes. These are full official product tiles, not the product pages'
test-only sample packages. Every original SHA-256 matches its STAC checksum.
Per-item creation/update timestamps remain in the catalog; those are publication
metadata, not flight timestamps. In particular, STAC January 1 year placeholders
must not be read as acquisition days.

### Imagery information versus its download grid

[SWISSIMAGE's specification](https://www.swisstopo.admin.ch/dam/de/sd-web/WchyQCcLkyd9/Produktinfo_SWISSIMAGE10cm_DE.pdf)
explains the Alpine 25 cm observation resampled onto the standard 10 cm download
grid. The selected items expose 10 cm and 2 m downloads, not a native 25 cm grid
file; the finest official COG was retained unchanged. **This is not native 10 cm
mountain imagery.** No extra enhancement or sharpening was performed here.

The 2023 generation is a conventional DTM-orthorectified, radiometrically processed
RGB mosaic. The [new sensor/product announcement](https://www.swisstopo.admin.ch/en/new-aerial-imaging-sensor)
describes true RGBN orthophotos beginning in 2026; that does not change these 2023
assets. ADS100 is the documented generation sensor, not independently confirmed
tile-specific instrument metadata. Native 25 cm imagery has a nominal ±0.25 m
horizontal accuracy claim (1 sigma); steep-face distortions and occlusion remain.

The official intersecting LUBIS strip dated **2023-09-07**, 25 cm, purpose
SWISSIMAGE, is a plausible mosaic source. Other intersecting August 2023 strips are
cryosphere monitoring. None supplies a delivered pixel-to-strip seamline. The
mosaic-year convention requires at least 70% from that year: exact dates for every
pixel are therefore **unresolved**, not asserted to be September 7 throughout.

### Surface observations and terrain derivation

| LAS tile | Points | First returns/m² | Actual GPS acquisition days |
| --- | ---: | ---: | --- |
| 2624-1091 | 11,923,511 | 11.750666 | 2021-08-24 / 2021-08-26 |
| 2624-1092 | 13,198,914 | 12.958959 | 2021-08-24 / 2021-08-26 |
| 2625-1091 | 12,555,573 | 12.417676 | 2021-08-26 |
| 2625-1092 | 12,868,428 | 12.781554 | 2021-08-24 / 2021-08-26 / 2022-08-23 |

The northeast tile contains **7,965,130 points from 2022-08-23**, despite its
collection-2021 name. Official tile metadata independently records 2021–2022.
GPS dates were decoded from the LAS global-encoding flag and adjusted standard GPS
time, following the [ASPRS definition](https://asprslas.org/stable/02.00_definition.html).
These dates use the GPS timescale, not a claimed UTC conversion. File creation
dates are unrelated to the flight date.

Mean plan-area densities are 12.636607 all returns/m² and 12.477214 first returns/m².
Every 100 × 100 m inspection bin has points. This does not establish gap-free
fine sampling, uniform independent measurements or visibility of vertical faces.
Actual classes are 1, 2, 3, 6 and 9; no class 17 occurs in these tiles.
The [surface specification](https://www.swisstopo.admin.ch/dam/de/sd-web/uIK9XXLTAGiI/swissSURFACE3D-ProdInfo-DE.pdf)
explicitly includes boulders in ground class 2. Class labels are provider decisions,
not independent rock/vegetation truth. The exact LiDAR instrument/contractor is
unprovided. LAS coordinates are quantized to 1 cm, which is not an accuracy claim.
The product nominal accuracy is ±0.20 m horizontal / ±0.10 m vertical, 1 sigma;
it has not been independently tested here.

The [surface raster specification](https://www.swisstopo.admin.ch/dam/de/sd-web/MyQQvIyq6L6H/SS3DR-ProdInfo-DE.pdf)
describes spike-free TIN interpolation, selected classifications and synthetic
water geometry. It is not a raw first-return height raster. Its historical rollout
schedule and format description differ from actual available COG assets; the
downloaded files and tile metadata establish availability and encoding here.

The [ALTI 2024/2 release note](https://www.swisstopo.admin.ch/dam/de/sd-web/Zca1yaqlIgTp/swissALTI3D-release-2024_2_de_bf.pdf)
records Valais replacement with 2021/2022 LiDAR, including high elevations, plus
2023 photogrammetric updates. DTM-TLM/TIN is linearly interpolated to the grid.
**0.5 m output spacing is not independent 0.5 m measurement resolution.**
The new LiDAR terrain's published accuracy is approximately ±0.3 m (1 sigma, three
dimensions), distinct from the surface-product claim. Pixel-level update lineage
and independent local accuracy remain unknown.

## Spatial and temporal compatibility

All 12 rasters are north-up EPSG:2056 on the exact kilometre tile edges, with
zero rotation/mirroring. DSM and DTM affines and dimensions are identical; imagery
has five distributed cells per height cell along each axis. Grid edges coincide,
but imagery centres lie 0.05 m from an edge versus 0.25 m for height cells.
No horizontal reprojection is needed to combine these sources later.

All raster validity masks cover 100% of the AOI, and both height products declare
-9999 NoData with **no missing cells**. Imagery declares no NoData and contains
267 all-zero RGB pixels: 2.67 m² on its distributed grid, 0.00006675% of the AOI.
Because the specification also uses black for missing imagery, dark pixels versus
tiny unflagged holes remain unresolved; complete footprint coverage is not proof
that every image pixel is an observation.

Horizontal datum is CH1903+/LV95; height datum is LN02, metres (EPSG:5728), from
official product provenance. TIFF CRS tags encode only the horizontal reference;
ALTI bands explicitly label metres, surface bands do not. The LAS has no CRS VLRs.
Those omissions are recorded rather than treating EPSG:2056 as a vertical datum.
Actual coordinates, product references and asset metadata agree; no vertical
conversion was performed.

This is **not a co-temporal acquisition**: 2021/2022 LiDAR, 2023 imagery and a
composite 2024 DTM release. Snow/ice movement, water level, ground cover, erosion,
paths and infrastructure can change. Future texture/geometry disagreement cannot
be causally attributed only to resolution. A DSM−DTM difference may also include
classification, water treatment and later terrain updates; it is not object-height
or rock/vegetation evidence by itself.

## Rights and attribution

The official [swisstopo OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices),
version 1.3.2021, permit use, commercial reuse, processing, distribution and making
these standard products accessible, with mandatory source acknowledgement.
Public derived rendering/screenshots are covered by those permissions. Use
**©swisstopo** or **Federal Office of Topography swisstopo** on outputs; infrastructure
operating/fair-use conditions still apply. No product-specific exception was found
for these four datasets. STAC's `proprietary` licence label is preserved; these are
custom terms, not a guessed Creative Commons licence. Raw data remains outside Git
regardless of redistribution permission. Official terms/specifications are retained
externally with URLs and hashes.

## Inspection, limitations and the Tryfan decision

An attributed north-up overview and three 150 m crops were visually inspected.
They show fractured exposed rock/steep faces, loose deposits and large blocks,
green/brown alpine cover, paths, lakes, drainage traces, southern ice/debris/moraine
landforms and limited northern railway/infrastructure. These are qualitative
observations, not semantic labels. Shadows on Riffelhorn and bright ice obscure
details; conventional orthophotos can stretch steep-face pixels. Raster heightfields
cannot represent overhangs. No 3-D scene or common terrain grid has been produced.

Compared with Tryfan, this supplies openly reusable mountain RGB at nominal 25 cm,
classified original LiDAR and 0.5 m derived DSM/DTM, with explicit but mismatched
dates. Tryfan retains its 2021 Welsh 1 m DTM/DSM and Lab 010's 10 m Sentinel colour.
The user-reported Bluesky Tryfan option is 12.5 cm RGB, a £190.82 2 × 2 km quote and
same-date 50 cm CIR; those offer a finer imagery opportunity but derived/public
licensing is unclarified. RCAHMW imagery remains restricted for this use.
No quote, vendor licence or purchase was investigated here.

Lab 012A established native-resolution rendering machinery on an urban sample;
it did not prove mountain semantics or co-temporal resolution-only differences.
Riffelhorn can test mountain evidence, registration and geometry limitations under
clearer reuse terms. It cannot decide whether 12.5 cm imagery is worth buying for
Tryfan or whether its rock/vegetation boundaries will transfer. The next recommended
action is a **separately authorised bounded Swiss mountain representation experiment**,
starting with stable rock/lake terrain and explicitly controlling shadows and
time-variable ice. Nothing beyond acquisition/inspection was implemented.

## Storage and repeatable verification

All originals, extracted immutable LAS, API responses, receipts, retained official
documents and inspection previews are beneath:

```text
MERIDIAN_DATA_ROOT/sources/atlas/riffelhorn/swisstopo-2021-2024/
  originals/{swissimage-dop10,swisssurface3d-raster,swissalti3d,swisssurface3d}/
  extracted/
  metadata/
  diagnostics/
```

The usual sibling `meridian-data` default is supported. No private root is needed.
Use the existing isolated scientific Python environment, or an external virtual
environment installed from
[the research requirements](../../scripts/terrain_research/requirements.txt).
Pillow is needed only for optional previews (available in the existing Earth Lab
environment); acquisition/inspection needs NumPy, rasterio and pyproj. Recorded
versions are Python 3.12.6, NumPy 2.5.3, rasterio 1.4.3/GDAL 3.9.3, pyproj 3.7.2,
Pillow 12.3.0. No new dependency was installed.

From the repository root, with that environment activated:

```powershell
python scripts/terrain_research/riffelhorn_acquisition.py discover
python scripts/terrain_research/riffelhorn_acquisition.py download
python scripts/terrain_research/riffelhorn_acquisition.py inspect
python scripts/terrain_research/riffelhorn_acquisition.py verify
python scripts/terrain_research/riffelhorn_acquisition.py preview
python -m unittest discover -s scripts/terrain_research -p test_riffelhorn_acquisition.py -v
```

Discovery pins these acquisition generations and caches official evidence outside
Git. Downloads verify official SHA-256 before accepting files and refuse to
overwrite changed retained originals. Inspection validates real raster metadata,
full validity/black-pixel counts, LAS records/returns/classifications/dates and
100 m density bins; `verify` rechecks exact tile grids and original/extracted hashes.
The LAS parser deliberately rejects unsupported layouts instead of guessing.
`preview` creates only attributed offline 2-D imagery diagnostics; its 1 m overview
is an inspection reduction, not a new source product or higher-resolution claim.

Validation: all 16 original checksums and four extracted LAS hashes pass; exact
coverage/grid checks and all 16 terrain-research tests pass, including six new
synthetic acquisition tests. JSON/link/whitespace and scope/security checks pass.
ESLint and the TypeScript/Vite production build pass; existing chunk-size/plugin
timing warnings remain. Rasterio/NumPy deprecation warnings do not change the
results. Production code, renderer files, Tryfan data and Lab 012A
implementation remain untouched. No raw geodata or large generated product enters
the repository.
