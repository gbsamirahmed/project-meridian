# Source-aware contour pilot — Riffelhorn

**Current visual checkpoint:** [offline review of retained Swiss masters](contour-visual-demonstration.md) preserves the processing improvements and demonstrates existing geometry only. No genuine continuation or scientific outcome change; research-preservation commit requires owner approval.

**Current adapter checkpoint:** [staged continuation](staged-contour-continuation-adapter.md) implements separately gated stages and synthetic controls. The supplied profile refuses genuine execution pending workspace/memory decisions. All genuine evidence and Outcome C below remain unchanged.

**Later recovery checkpoint:** [accounting, actual-worker supervision and topology](contour-pipeline-recovery.md) validates offline controls and proposes an explicitly unapproved continuation. It does not change this genuine Outcome C or regenerate its evidence.

## Genuine offline rerun — current Outcome C

**12 October 2026. C — BLOCKED by the shared stored-vertex budget.** The owner approved one genuine offline rerun, with two planned deterministic runs, under the original inputs, extent and ceilings. The revised implementation completed three Swiss source-specific products in run 1, then refused the next transformed-diagnostic fragment because it would exceed the shared 2,000,000-vertex allowance. No retry, scope reduction, source substitution or limit increase occurred.

The earlier failed memory attempt and synthetic recovery remain historical evidence below and in the [recovery record](contour-processing-memory-recovery.md). This result does not invalidate offline precomputation, but it does not complete the genuine mixed-source pilot. No products are published or integrated into the app.

### Prerequisites, inputs and execution

Public `main` remains `c952b8050c1259fe6d3f674e6f84195a3491d95a`; the private application remains `400a7f4c7fbdd2ae571bb838f92afbca21e59bea`. Both match locally recorded upstream refs, 0/0; no fetch/network request or commit. Existing authorised uncommitted files were preserved.

All **seven exact input byte sizes/SHA-256 values** in [input pins](../../scripts/atlas/contour-pilot/input-pins.json) matched before and after processing: four 2024/2 swissALTI3D 0.5 m LV95/LN02 DTM files, retained 2021 N45/E007 Copernicus EGM2008 DSM, CHGeo2004 LN02 and NGA EGM2008 grids. Source identities, release/epoch/accuracy qualifications, Swiss OGD/©swisstopo and Copernicus GLO-30 F notices remain as recorded below. Pins were not edited; no inputs were copied or modified.

Tools remain Python 3.12.6, NumPy 2.5.3, Rasterio 1.4.3/GDAL 3.9.3, pyproj 3.7.2/PROJ 9.5.1, Shapely 2.1.2 and ContourPy 1.4.0. Numerical engine/reader/resource-guard hashes matched the synthetic recovery seal. **28 focused tests passed before execution.** Changes to `rerun.py` were operational accounting/progress only; [supervision](../../scripts/atlas/contour-pilot/supervise-genuine.ps1) added an external deadline check. No scientific algorithm, interval, tolerance or input was changed.

The core remained EPSG:2056 `[2624000,1091000,2626000,1093000]`, with the declared 250 m global-only context. Output is under `${MERIDIAN_DATA_ROOT}/experiments/atlas/source-aware-contours-v1/execution-3/processing`, outside Git. The original two stop records/five empty files remain byte-identical. No `v2` directory or replacement of earlier evidence was used.

### Completed and incomplete evidence

The following are **locally completed, single-run products**, not a successful two-run publication. Every declared 10 m level from 2000–3200 m was considered; each has a `twentyMetreSubset` flag and every 100 m level an index flag. The 20 m product is the identical even-level subset, not a separately rounded field. Non-empty levels are 2190–2970 m.

| LN02 DTM reconstruction | 10 m master lines | 10 m master vertices | Closed lines | 20 m subset lines / vertices |
|---|---:|---:|---:|---:|
| Native 0.5 m | 1,596 | 662,196 | 1,463 | 762 / 332,486 |
| Strict aligned 4×4 means → 2 m | 356 | 150,389 | 228 | 176 / 75,518 |
| 2 m, Gaussian sigma 2 m/radius 6 m | 203 | 140,562 | 85 | 101 / 70,484 |

Native inputs were preserved; the aggregate/filter products explicitly represent changed reconstructed fields. Sample-centre interpolation domains differ: native centres begin 0.25 m inside the retained rectangle, coarse centres 1 m inside; strict full filter support excludes the first/last three coarse samples. These support differences are declared, not a change to the selected study/source extent.

Total planar LV95 XY line lengths for all 10 m levels were approximately **257.4 km, 236.6 km and 223.3 km**, respectively. These are computed contour geometry lengths, not walking distance, 3D surface length or accuracy. Reduced geometry/closed-line counts demonstrate sensitivity to aggregation/filtering and boundary support; they do not prove improved terrain accuracy or identify which small features are real. Cross-product displacement comparisons were not reached, so no new Hausdorff displacement claim is made.

| Recorded computational validation | Native | 2 m | Smoothed 2 m |
|---|---:|---:|---:|
| Maximum edge-height residual, metres | 5.80×10⁻⁸ | 1.04×10⁻⁸ | 7.49×10⁻⁹ |
| Four-partition reassembly displacement, metres | 0 | 0 | 0 |
| Maximum partition length discrepancy, metres | 2.27×10⁻¹¹ | 1.91×10⁻¹¹ | 1.46×10⁻¹¹ |
| Maximum XY round-trip residual, metres | 0.001251 | 0.001251 | 0.001251 |

These pass the declared 0.001 m edge-height, 1e-6 m partition and 0.01 m XY tolerances. They are numerical checks, not measurement/datum accuracy. Straight contour segments are not asserted to match a continuous terrain surface everywhere. Native extraction visited 256 bounded windows; each coarse variant visited 16. Stitching completed without a reported ambiguous junction/unequal seam. Four 1 km delivery partitions were checked in memory, not published as tiles. Closed master lines are present; no independent second contour algorithm or decoder comparison was added. Genuine nodata cell counts were not recorded; missing-window/hole behaviour remains synthetic evidence, not a new complete missingness census.

**The 2 m simplification candidate failed for all three products.** Maximum displacement stayed below 2 m and no ring collapsed, but new intersecting line-pairs numbered **252 native, 64 coarse and 18 smoothed**. The checker covered all 3,081 non-empty level pairs plus within-level intersections. These are line-pair counts, not individual intersection-point counts. Per-line `preserve_topology` does not preserve relationships between different contours. Unsimplified originals were retained; no simplified output was adopted.

**Vertical diagnostic:** original LN02/EPSG:5728 → target EGM2008/EPSG:3855, forward through the pinned compound LV95/LN02 → CRS84/EGM2008 operation and retained grid files. Full XY and height transformation was attempted on the 2 m reconstruction. Only **83,331 fragment vertices** were retained, from windows with starts `(0,0)`, `(0,256)`, `(0,512)`, `(0,768)`, `(256,0)`, `(256,256)`, `(256,512)`, `(256,768)` and `(512,0)`; the final window/level traversal was incomplete. These are windows with saved fragments, not a completed coverage mask. No stitched diagnostic product, numerical height-offset summary, inverse check or source-compatibility conclusion was completed. Combined transformation accuracy remains unknown (-1), with epoch/surface qualifications preserved.

Copernicus checksum/header/context prerequisites passed, but **global DSM contour generation was not reached**. No DSM/DTM geometry/elevation comparison, source-boundary transition or seamless fusion finding is established. The retained Swiss selection boundary remains a product/subset boundary, not national dataset coverage.

### Budget stop and accounting limitations

[Compact genuine receipt](../../scripts/atlas/contour-pilot/genuine-rerun-receipt.json) seals the full external inventory and completed manifests. There are **867 retained files / 64,250,005 logical file bytes**, including earlier evidence and the inventory, comfortably below 150,000,000 bytes. Filesystem metadata/allocation overhead is not measured.

Retained geometry contains **1,992,909 vertices**. The ledger also charged **6,962 temporary synthetic control writes** conservatively, for **1,999,871** total charged vertices. The next fragment needed more than the remaining 129 vertices and was rejected **before writing**. Thus the cap was not enlarged or exceeded; it prevented completion. The main contribution was retaining extraction fragments and stitched masters: the three completed variants use 1,909,578 retained vertices before the partial diagnostic. Even just those three masters duplicated across two runs would require 1,906,294 vertices, before the diagnostic/global products. Discarding staging alone is not demonstrated to make the complete two-run profile fit.

The supervised attempt lasted **192.210 s**, with 5 s conservatively charged for preceding prerequisites/controls; post-stop inventory/checks also remained short. One numerical processing thread was used. The worker verified a **384 MiB resident maximum** and 384 MiB private-commit guard, reserving 128 MiB of the overall 512 MiB accounting target for supervision. The largest logged completed-product worker peak was **139,104,256 bytes / 132.7 MiB**, but the final peak during diagnostic extraction was not serialised on failure.

**Whole-process monitoring is not conclusively validated:** the supervisor's approximately 4.2 MiB sample was the Windows venv launcher, not the actual Python worker. Supervisor peak was 106,962,944 bytes. Do not treat their sum as the experiment's aggregate peak. The deadline probe likewise demonstrated termination of the monitored launcher, not proven termination of a stalled underlying worker. The genuine worker ended with its own vertex-limit exception before the deadline. No timeout success or exact final aggregate memory claim is accepted. Future execution needs verified actual-worker monitoring/termination before relying on that supervisor again.

Run 2 was never started; neither run produced a complete experiment receipt. **Genuine deterministic repeatability remains unestablished.** No quota reset, selective deletion, extra generation, transform query or retry followed the refusal. Post-stop work only inventoried/hashes existing outputs, verified source checksums and documented evidence. Zero network/provider requests, packages, licence acceptance, app/Chrome/Android launches or commits.

### Architecture assessment and owner review

These results support the feasibility of **bounded native-resolution preprocessing and source-specific stored contour geometry** for this retained Swiss DTM. They do not complete the mixed-source scientific pilot, prove repeatability, certify global costs or establish mobile/offline readiness. The unsimplified Swiss outputs are potential future vector-packaging inputs only after the outstanding scientific/resource/integrity gates. The rejected simplification must not enter a delivery product.

All 113 protected hashes, 42 Atlas status rows and 1,292 existing tracked public files remain unchanged; all seven inputs and prior partial evidence are byte-identical. Existing application map code and the one-line Info-button correction are preserved. No accepted scientific conclusion outside this new pilot was rewritten.

**Next milestone recommendation for owner review:** review output-retention/quota semantics and reliable actual-worker supervision before authorising any further processing. Preserve native resolution, source meaning, scope and intervals; do not assume a larger cap, discard difficult areas or move data into unaccounted storage. Topology-safe generalisation remains unresolved. No new rerun, tile delivery system, source fusion, contour integration or 3D task is begun or proposed for automatic execution.

## Historical first attempt — memory-gated result


**12 October 2026. Numerical pilot blocked at the resource gate.** Public scientific baseline `c952b8050c1259fe6d3f674e6f84195a3491d95a`. The owner approved offline processing of retained inputs, not acquisition, application integration or commits. This report and its [utility](../../scripts/atlas/contour-pilot/README.md) are new, uncommitted research files. Accepted Atlas findings remain unchanged.

## Decision and result

Retain the proposed architecture: **separate, immutable source-specific contour products, derived offline with a compact scientific manifest, then partitioned/generalised for delivery**. It preserves height meaning while allowing processors and delivery providers to change. This experiment does **not** yet validate genuine contour derivation or delivery.

The approved native 0.5 m Swiss reconstruction exceeded the **512 MiB** process working-set ceiling before its first contour level. Its recorded peak was **693,637,120 bytes (about 662 MiB)**. Processing stopped with **zero stored contour vertices**. This is a failed resource gate, not a compliant run or a demonstrated contour product. No budget was enlarged and no smaller source/product was silently substituted. The planned two deterministic numerical runs were not completed.

An earlier attempt failed to read the Windows process handle; that was corrected before the memory-stop attempt. Both stop records remain outside Git. The separate 100 ms supervisor did not capture the transient allocation peak; the worker's Windows peak-working-set counter did. Polling alone did not prevent an allocation from crossing the ceiling. A conservative allocation refusal was subsequently added and tested on synthetic sizes, without restarting genuine-data processing. A revised memory plan is required before any repeat.

## Evidence and source meaning

Reuse the accepted [terrain/product architecture](terrain-source-product-architecture.md), [global evaluation](global-terrain-foundation-evaluation.md), [native relief](native-relief-evaluation.md), [Swiss regional source](riffelhorn-regional-terrain-prototype.md) and [global-reference assessment](global-reference-assessment.md). The [application roadmap](../foundations/scientific-to-application-roadmap-decision.md) does not make rendered cartography an elevation measurement.

Exact paths, byte sizes and SHA-256 values are in [input pins](../../scripts/atlas/contour-pilot/input-pins.json). All seven inputs matched before preparation and again after the stop.

| Input | Meaning and retained qualifications |
|---|---|
| Four `swissalti3d_2024_{2624-1091,2624-1092,2625-1091,2625-1092}_0.5_2056_5728.tif` | Official 2024/2 0.5 m DTM, LV95 EPSG:2056 and LN02 EPSG:5728 metres. Swiss OGD, ©swisstopo. Underlying acquisition/update epochs differ; per-cell epoch unknown |
| `Copernicus_DSM_COG_10_N45_00_E007_00_DEM.tif` | Retained 2021 public GLO-30 COG distribution, exact sub-release unknown; one-arcsecond point posts, EPSG:4326, EGM2008 EPSG:3855 metres; **DSM**, not DTM |
| `ch_swisstopo_chgeo2004_ETRS89_LN02.tif` and `us_nga_egm08_25.tif` | Retained CHGeo2004 and NGA EGM2008 grids, CC0/public-domain lineage; accepted compound operation's combined accuracy is unknown (-1), not a centimetric claim |

Existing source files total **108,202,196 bytes**; grids add **80,880,814 bytes**. None was copied, modified or reacquired. Source URLs and permissions were reviewed in the approved application proposal using retained evidence. No current online availability or worldwide redistribution clearance was established.

Copernicus derivatives must retain the full applicable notice:

> produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved

The retained GLO-30 F terms also require applicable liability/non-endorsement and downstream provisions; this notice alone is not a complete licence. No derived payload was published.

## Approved profile and durable semantics

Core EPSG:2056 bounds: **[2624000,1091000,2626000,1093000]**, 4 km². Copernicus-only context extends 250 m: **[2623750,1090750,2626250,1093250]**, 6.25 km². The Swiss boundary is the **retained product selection**, not national coverage. No DSM/DTM fusion or source-boundary continuity is presumed.

A contour identifies an isoline approximation of a declared reconstructed field. Minimum semantics: level/metres/vertical reference; dataset/revision/input hashes and DSM/DTM meaning; acquisition/accuracy qualifications; coordinate references and explicit transformations; algorithm/version/sample registration/interval/index; missing-support rule; smoothing/simplification lineage; geometry precision/coverage; rights and validation status. Presentation properties and delivery encoding remain replaceable. Equal numeric LN02 and EGM2008 levels are not automatically the same physical heights.

Regional selection must consider valid coverage, vertical meaning, surface, epoch, uncertainty, rights and use, rather than nominal resolution alone. Zoom can select generalisation within a source family. A visual switch between families is not reconciliation. Until reconciliation is justified, preserve source identifiers and clipped endpoints, avoiding offsets, feathering, snapping or fabricated continuity. Current Mapterhorn hillshade has unresolved per-pixel source/common-reference lineage; these products cannot be described as contours of that identical mosaic.

## Method and validation status

Installed tools: Python 3.12.6; NumPy 2.5.3; Rasterio 1.4.3/GDAL 3.9.3; pyproj 3.7.2/PROJ 9.5.1; Shapely 2.1.2; ContourPy 1.4.0. No packages were installed. Network access was disabled for PROJ; GDAL auxiliary-file writing was disabled.

The apparatus reconstructs native centres, using ContourPy serial/Separate/Linear, no corner masking or quad triangulation, and one thread. Every quad touching an invalid sample is excluded. Linear edge crossings are not proof of exact terrain height throughout a straight segment. Proposed 10 m levels 2000–3200 m, 20 m subset and 100 m indices do not establish 10 m vertical accuracy.

| Check | Actual evidence |
|---|---|
| Source identity/integrity | Seven SHA-256 checks passed before and after |
| Native grid loading | Four Swiss headers and 4000×4000 mosaic preparation accepted by the pinned profile checks; no completed numerical contour receipt |
| Mathematical/rejection controls | **11 synthetic tests pass**: affine edge height, constant/tie/saddle behaviour, strict nodata quads, aggregation/filter support, monotonicity, metadata/units/references/fusion, missing/changed inputs, duplicate IDs, partition completeness and allocation refusal |
| Native contour elevations/geometry | **Not established**; stopped before level generation |
| Genuine resampling/smoothing effects | **Not established** |
| Full XY/height datum diagnostic and cross-source comparison | **Not executed**; earlier accepted diagnostic is not a new result for this extent |
| Genuine edge continuity, simplification, output semantics | **Not established**; downstream code remains unvalidated |
| Two-run deterministic agreement | **Not completed** |
| Figures, labels, map/mobile delivery | **Not produced/tested** |

Planned same-source displacement comparisons, regional missing-patch boundary controls and figures were not completed before the stop; the apparatus must not be treated as a finished processing/delivery system.

Declared future computational tolerances remain 0.001 m at unsmoothed edge crossings, 1e-6 m partition reconstruction, 0.01 m XY round trip and a 2 m simplification candidate with no introduced crossings/collapsed rings. None is terrain accuracy. They were not relaxed after the stop.

## Resources and preservation

[Sanitised experiment receipt](../../scripts/atlas/contour-pilot/experiment-receipt.json) and [preservation receipt](../../scripts/atlas/contour-pilot/preservation-receipt.json) distinguish failures from completed checks. The external owning directory contains two stop receipts and five empty NDJSON files: **305 bytes**, **zero stored vertices**. Recorded worker durations total about **1.7 seconds**; no 20-minute timeout occurred. The 150,000,000-byte and 2,000,000-vertex caps were respected; **the working-set cap was exceeded and failed**. Zero provider requests/response bytes, paid services, new licences or dependencies. Marginal service cost £0; local compute/power only.

All **113 protected hashes**, **42 canonical Atlas status rows** and **1,292 existing tracked files** remain unchanged. All **40,841 Weather payload hashes** match the retained publication receipt; including that receipt there are **40,842 files / 1,275,692,110 bytes**. The seven original inputs remain byte-identical. New public scientific files only; no public production code, accepted reports or external organisation was rewritten. The independent one-line private Info-button CSS correction is documented separately in the application proposal; no contour integration occurred.

## Cartography, future boundaries and next step

The existing proposal remains conditional: compare regional 10/20 m and global 20 m sensitivity products, with sparser small-scale candidates and 100 m indices; assess density, labels, flat-land clutter and legibility alongside hillshade before selecting zoom thresholds. No visual recommendation is promoted to a validated setting, and no owner styling decision is replaced.

Offline delivery would need geometry/manifest integrity and redistribution/update/recovery checks; this pilot establishes none. Numerical elevation inspection requires an independent scalar sampling contract. Future 3D needs qualified geometry and explicit representation selection independent of camera pitch. No hosting, MVT encoding, backend or database has been selected.

**Exactly one proposed next task, not begun:** revise native-grid memory handling and its allocation preflight, then seek approval to repeat the same bounded Riffelhorn experiment within 512 MiB. Preserve native baseline meaning, extent, inputs, tolerances and separate products. Do not silently drop the native comparison, enlarge budgets or substitute sources. Commits, live contour integration and Android tests remain separately gated.
