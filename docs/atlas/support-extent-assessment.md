# Riffelhorn glacier-aware support-extent assessment

2026-10-05; baseline `28f677ce29e2e2945d6898036d9b20c0411b5c45`.
**Outcome E: no defensible acquisition extent established yet.** No elevation
acquisition, terrain generation, height operation, seam or production change.

## Question and decision

What bounded larger authoritative Swiss support would give an admissible enclosing
corridor around the unchanged 1.5 km circle centred at LV95 `[2625000,1092000]`?

**MERIDIAN EVIDENCE (M):** this is not simply a glacier tongue ending a few kilometres
south of the old crop. The connected historical/recent exclusion network extends
west, east and north beyond the bounded inventory study window, and reaches the
national boundary south. A recent-only, unbuffered SGI2023 connection also reaches
that boundary. Within known Swiss inventory coverage, expansion alone does not
establish a surrounding admissible region.

**Recommendation:** acquire **zero additional elevation tiles now**. Neither a
minimum nor a reasonably robust next terrain extent can honestly be specified
from these inputs. The single next prerequisite is a **bounded transboundary
change/support audit at the southern passage**: establish authoritative glacier/
snow/change coverage across the Swiss–Italian boundary and the actual swissALTI3D
valid-data support there. Tile existence and national territory are not sufficient.
Do not perform that audit or acquire terrain as part of this task.

This does not prove that no larger Swiss delivery product could work, or that a
national product is required. It identifies missing coverage semantics before
committing storage and processing to an unvalidated enlargement.

## Retained evidence and frozen protocol

Reviewed the [larger Swiss asset](riffelhorn-swiss-support-product.md),
[stable-overlap assessment](global-reference-assessment.md),
[common product](copernicus-common-product.md),
[regional parents](regional-parent-diagnostic.md),
[spatial-reconciliation review](spatial-terrain-reconciliation-research.md) and
[same-level corridor diagnostic](seam-corridor-feasibility.md). Their products and
results remain frozen; source/product identities were cross-checked in metadata,
not by rereading unused elevation files. Swiss LN02 and common EGM2008 are untouched.

The [plan](support-extent-plan.json) preceded topology analysis. A recorded
addendum handles censoring and recent-only border attribution after the first
pass. The [measurements](support-extent-measurements.json) and
[hash manifest](support-extent-diagnostic.json) retain inputs, software, graph
parameters, all arrays and output files. No Swiss/Copernicus height field was read.

## Authoritative inputs (E)

Accessed official documentation 2026-10-05. Reused the complete already-retained
national inventory archives; no new glacier archive or elevation file downloaded.

| Input | Reference epoch / release | Basis / rights |
| --- | --- | --- |
| [SGI1973](https://doi.glamos.ch/data/inventory/inventory_sgi1973_r1976.html) | 1973 / r1976 | ETH geographic institute, aerial-image outlines; CC BY 4.0. |
| [SGI2016](https://doi.glamos.ch/data/inventory/inventory_sgi2016_r2020.html) | 2013–2018 / r2020 | GLAMOS, swisstopo imagery/stereophotogrammetry, glaciological revision; CC BY 4.0. |
| [SGI2023](https://doi.glamos.ch/data/inventory/inventory_sgi2023_r2026.html) | 2021–2024 / r2026 | GLAMOS revised swissTLM3D-derived outlines; CC BY 4.0. Local Gorner record acquisition year 2023, internal year_rel 2025; archive publication r2026 remains distinct. |
| [National territory](https://www.swisstopo.admin.ch/en/landscape-model-swissboundaries3d) | Live GeoAdmin country feature CH, accessed 2026-10-05; response carries no exact edition | Official Swiss territorial polygon, requested LV95; frozen response SHA-256. Not an elevation-coverage mask. [OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices), credit ©swisstopo. |

Inventory ZIP hashes: SGI1973 `69a13fde7b142dd29b2f07a6bf5a4923750b502661995ca518e992a591e86145`;
SGI2016 `36ff3252f24f76f0a93eafaa29086ba63725cc2cc99593deca34c15699e933a7`;
SGI2023 `ecef353d4b70f760eda83c6131e5345a2fd999527ea560b0bda4b7c27823f9fb`.
All three verify: combined 45,245,797 bytes. Declared PRJs are LV95; archive text
encodings are respected rather than replacing non-ASCII glacier names.

Only lightweight additional evidence was acquired: 1,260,358-byte country response,
SHA `aab96a561f23186b09df0fbd7b39f8d383739f67e33f0ec6e8492eaad3f6d4d8`,
and two official STAC item responses totalling 5,639 bytes. Source references,
HTTP/access metadata and hashes are in the diagnostic record. Raw responses remain
outside Git. The [GeoAdmin find API](https://docs.geo.admin.ch/access-data/find-features.html)
supports the requested country query/CRS; initial incorrect layer-scoped URL returned
404 before the documented MapServer find request succeeded.

The official 2024 catalogue lists both `swissalti3d_2024_2625-1087` (existing)
and `swissalti3d_2024_2627-1085` (beyond the crop), including 0.5 m LN02 asset
multihashes. **Neither asset was downloaded.** This check specifically prevents
calling the national polygon the exact DEM support: whole distribution tiles can
cross it. Listing a TIFF does not establish every cell's validity or cross-border
glacier/change coverage. No 2026 DEM release was substituted.

## Geography of the obstruction (M)

The southern connection intersects inventory **B56-07 Gornergletscher**. Its
1973 outline spans approximately LV95 `[2620861,1085051,2634323,1092710]`,
57.77 km²; SGI2023 spans `[2624070,1085077,2634377,1092697]`, 35.37 km².
These are published inventory footprints, not glacier-volume or elevation-change
measurements. Both extend roughly 1.9 km beyond the current south boundary;
Gorner extends about 4.4 km beyond its east boundary.

The union and buffers connect a set of glaciers/change exclusions, not one uniform
ice surface: Theodul (B56-28/30), Breithorn (B56-26), Schwärze (B56-32),
Monte Rosa (B56-10), and farther Findel (B56-03), Zmutt (B57-05),
Allalin (B52-29) and Fee (B53-04) enter the observed connected network. Historical
footprints and buffer bridges must not be interpreted as current physical ice
connections. The 500 m case incorporates additional western/northern features.
Exact participating feature IDs/epochs/bounds are recorded for each case.

The study window is LV95 `[2614000,1082000,2640000,1100000]`, **26×18 km**,
derived from known feature bounds plus geographic context, not proposed acquisition.
At 25 m the connected excluded support reaches all its west/east/north boundaries.
Southern minima are 1084950 /1084800 /1084550 for 100/250/500 m buffers,
respectively 2.05 /2.20 /2.45 km beyond the old south edge. Its full north/east/west
extent is therefore **censored**, not established by the map frame.

At the old south edge (north 1087000), summed excluded width across the study
window is 11.18 /11.93 /13.60 km. These are sums of blocked raster intervals,
not widths of one glacier. At north 1085500 the corresponding sums are
3.70 /5.05 /8.65 km. Simply extending south would leave lateral connections.

## Topology and support analysis

Reused the previous four-neighbour cycle/dual-flood test with **zero compatibility
cost**: this task asks only whether support/exclusions admit closure. No terrain
slopes, residuals, fitted error model or final seam costs are extrapolated outside
the existing DEM crop.

Rasterize official outlines all-touched on 25 m LV95 cells; apply the existing
Euclidean raster buffers 100/250/500 m. Repeat at 50 m to disclose sampling
sensitivity. Keep the whole protected circle plus one cell diagonal excluded.
Test source-edge guards 100/200/500 m. Separate:

- **Optimistic plane:** excludes mapped Swiss glacier/change support but does not
  assume that absence of Swiss inventory polygons establishes stable foreign terrain.
- **Known-inventory support:** additionally restrict to the national territory
  proxy, conservatively eroded one cell. This is a coverage diagnostic, not a new
  production rule or a claim that every Swiss DEM ends at the border.

Both the old crop and the entire observed window fail enclosure for **all 36
level/buffer/edge-guard combinations per coverage interpretation**. The exact
25 m, 250 m mask cropped back to the old extent equals the retained mask bit-for-bit,
reconstructing the prior obstruction without reading its terrain fields.

An independent shortest-hop exclusion path also reaches outside known national
territory using **SGI2023 alone without any glacier buffer**: endpoint approximately
LV95 `[2627363,1085938]`; graph length 7.275 km from the guarded protected region.
The 50 m repeat reaches `[2627375,1085925]`, length 7.25 km. These are diagnostic
grid-path lengths, not glacier lengths. Historical 1973 and the unbuffered union
also reach the territory boundary. Thus this is not solely a 500 m-buffer artifact
or a historical-only obstruction.

At 25 m /250 m, the observed component covers 180.45 km² including the protected
region/buffers; 106.44 km² intersects recent 2023 ice and 19.91 km² is 1973 footprint
absent from both later inventories. The latter indicates historical exposure,
**not** proof of DEM-epoch instability everywhere. No exact change between the
Copernicus and Swiss observation epochs or per-cell source epoch is inferred.

Adding water/snow exclusions cannot rescue failed topology in this domain.
Their retained detailed classification covers only the previous study area;
foreign/expanded persistent snow and water remain unresolved. No claim of complete
stable terrain is made. There is no slope cutoff, relaxed-glacier success or
invented numerical confidence.

## Extents, tiles and storage trade-off

The algorithm derives kilometre-aligned rectangles from the connected exclusion
component plus source-edge margin, retaining all existing 100 tiles. **It refuses
to establish a minimum/robust extent when the component touches the study edge.**
Both accepted extent fields are null; no new tile selection is approved.

| Extent | LV95 bounds | Tiles /reuse /new | Approx source /delivery GB |
| --- | --- | ---: | ---: |
| Existing, insufficient | `[2620000,1087000,2630000,1097000]` |100 /100 /0|1.667 /0.931 measured|
| Wider observed inventory window, still insufficient | `[2614000,1082000,2640000,1100000]` |468 /100 /368|7.802 /4.357 estimated|
| Censored bbox +margin illustration, **not a sufficient candidate** | `[2613000,1084000,2641000,1101000]` |476 /100 /376|7.936 /4.431 estimated|

The coarser 50 m /500 m illustration rounds its southern limit to 1083000,
504 tiles (404 new), approximately 8.403 GB source /4.692 GB delivery. This
grid-dependent rounding is another reason not to advertise a minimum.
The existing source pattern is x2620–2629,y1087–1096; the observed window would
be x2614–2639,y1082–1099. Illustrative counts are potential distribution cells,
**not a catalogue-verified list of valid official source assets**.

Estimates use the measured 100 km² baseline: source 1,667,166,026 bytes;
delivery 930,914,852 bytes /11,429 tiles. Observed-window area scaling gives about
53,488 delivery tiles;476-cell illustration about 54,402. Compression, high-zoom
support omission, parent sharing, masks and geometry can change these materially.
No products or exact runtime/processing forecast were generated. GB is decimal.

Geometry favours asymmetric context rather than a larger centred square, but
the closed regional boundary cannot be reduced to a southern extension. Even
4.7× the old source area remains an inadequate observed enclosure. National-scale
processing does not automatically supply transboundary evidence or resolve the
stable-only border obstruction; no national product design/economic winner follows.

## Decision and exact next prerequisite (H)

**No DEM acquisition is recommended now.** Minimum topologically feasible
source support, robust extent and exact new source-asset list remain unestablished.
The strongest missing prerequisite is a **transboundary exclusion/valid-support
audit at the identified southern border passage**, using authoritative glacier/
snow information beyond the Swiss inventory and documented available regional
terrain coverage. Retain the protected geometry, buffer sensitivity and epochs.
Do not infer coverage from tiles or relax change exclusions into a success.

If that establishes a bounded supported enclosure, then—and only then—specify the
exact additional 2024 Swiss assets, acquire/verify official hashes, create a new
immutable regional product/parent revision, and rerun the **same** same-level
seam-corridor feasibility question. Preserve the existing v1 asset and LN02 heights.
Only a subsequent defensible corridor could justify a separate transition test.
None of these steps was performed here. Bounded Riffelhorn experimentation remains
useful, but another terrain purchase/download is premature rather than justified
by the number of kilometres on the map.

## Outputs, reproduction and validation

Canonical additional metadata:
`${MERIDIAN_DATA_ROOT}/sources/atlas/riffelhorn/support-extent-assessment-v1/`.
Diagnostic outputs:
`${MERIDIAN_DATA_ROOT}/experiments/atlas/riffelhorn-support-extent-v1-verified/`;
independent sibling `riffelhorn-support-extent-v1-verified-rebuild/`.
Two compressed grids, diagnostic map and measurements plus hash manifest; all
large outputs outside Git. `support-extent-map.png` marks the protected interior,
original support, kilometre boundaries, inventory/buffer network, source-edge
limitations and border obstruction. The wider outline is **not** an acquisition.

```powershell
$terrainPython = "$env:MERIDIAN_DATA_ROOT/earth-lab/.venv/Scripts/python.exe"
& $terrainPython scripts/atlas/support_extent.py --suffix=-verified
& $terrainPython scripts/atlas/support_extent.py --suffix=-verified-rebuild
# Existing immutable outputs refuse overwrite: use new named siblings for reproduction.
& $terrainPython -m unittest discover -s scripts/atlas -p 'test_*.py'
node --test scripts/atlas/test_support_extent.mjs scripts/atlas/test_seam_corridor.mjs scripts/atlas/test_terrain_policies.mjs scripts/atlas/test_terrain_metadata.mjs scripts/atlas/test_global_reference_metadata.mjs scripts/atlas/test_terrain_hierarchy.mjs
git diff 28f677c -- src vite.config.ts package.json package-lock.json
git diff --check
```

Inputs are frozen local inventory archives, the country response and two catalogue
responses. Generation is offline; it does not fetch metadata or open elevation
rasters. Reacquiring a live service response may change its checksum and must be
recorded as a new input revision, not silently substituted. Tool/helper/protocol
hashes and Python/NumPy/GDAL/rasterio/pyproj versions identify reproduction.

Synthetic tests cover connected components, diagonal contact, unknown-support
barriers, obstruction witnesses, tile alignment, reusable counts and separate
source/delivery estimates. Record tests retain censoring and no-elevation invariants.
Normal CI requires no external estate. Reference/diff checks and focused existing
terrain-policy/model tests protect the unchanged production boundaries. No broad
application build is needed for isolated Python research and documentation.

**Production:** AWS visual terrain and independent AWS z15 analytical elevation,
IGOR 315° map anchor/strength curve, exaggeration 1.45, satellite, Weather, Traverse,
projection/lifecycle and startup all unchanged. No runtime imports or new package
dependencies. No private estate access.

**Evidence discipline:** official inventory definitions, rights, tiling and border
product are **EXTERNAL EVIDENCE**; hashes, components, paths, sampling sensitivity
and cost arithmetic are **MERIDIAN EVIDENCE**; a future supported transboundary
enclosure and any later terrain transition are **RESEARCH HYPOTHESES / DIRECTIONS**.

Validation completed: 54 Atlas Python tests and 40 focused Node policy/model/record
tests pass. Four external output files and every recorded array/file hash match
the independent rebuild; final identity `c129226900840224b273142aebb7c04b27aad439f3288582703fff4676b6f9f5`. Diagnostic
file bytes total 1039433. Portable UTF-8 hashing
was corrected after a record test exposed Windows default-encoding drift; final
code, protocol and manifest hashes now agree. Existing deprecation warnings remain.
Local references, JSON/hash records and production diff checks pass. No application
build, broad application suite, lint or TypeScript rerun: no application, package,
build or runtime configuration changed.
