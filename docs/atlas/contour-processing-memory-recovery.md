# Contour processing memory recovery

**Current continuation gate:** the [staged adapter](staged-contour-continuation-adapter.md) preserves this numerical method and all genuine evidence, but refuses the unapproved 200,000-coordinate/128 MiB member profile. Synthetic results do not authorise a genuine replay.

**Later checkpoint:** the [pipeline recovery record](contour-pipeline-recovery.md) repairs accounting and workload supervision and reports limited topology evidence. The historical memory results below remain unchanged; its old genuine-repeat proposal is superseded by the new, unapproved continuation proposal.

**12 October 2026 — synthetic recovery verified; genuine Riffelhorn replay pending approval.** This extends the [resource-blocked pilot](source-aware-contour-pilot.md), without rewriting its failed outcome. Public baseline `c952b8050c1259fe6d3f674e6f84195a3491d95a`; no commit or provider request. [Architecture proposal](precomputed-terrain-products.md) separates scientific products from delivery.

## Diagnosis

The original process reported **693,637,120 bytes**, about **662 MiB**, before its first contour level. It did not retain per-operation measurements, so the entire spike cannot be attributed retrospectively.

Installed ContourPy 1.4.0 source was inspected locally: it converts heights to float64 and expands 1D X/Y arrays with `np.meshgrid`. These are full arrays even though the caller supplied compact axes. At 4000×4000:

| Allocation | Exact array bytes, excluding allocator/library overhead |
|---|---:|
| Native float32 mosaic | 64,000,000 |
| Orientation copy while original survives | 64,000,000 transient |
| ContourPy float64 heights | 128,000,000 |
| Two internal float64 coordinate meshes | **256,000,000** |
| One full Boolean mask | 16,000,000 |
| Retained 2 m float64 height array | 8,000,000 |

The explicit `masked_invalid` call adds a data copy/mask; finite-value advanced indexing creates another temporary. Lifetimes overlap differently: the orientation copy is not asserted to survive until extraction. C++ caches, GDAL/PROJ state and allocator retention were not separately measured in the old run. Geometry accumulation is a later risk, **not a cause of that pre-level failure**; raster reprojection/compound transformation had not yet run.

A **1024×1024 synthetic** staged reproduction observed working set rise from 63.5 MB baseline to 109.3 MB after generator construction; the process peak reached 114.5 MB during statistics. After releasing references, current working set fell to 65.2 MB. Python/NumPy tracing showed the generator stage add about 26.2 MB of retained allocations. These measurements corroborate the allocation path; they are not a full-size reproduction or a linear prediction of every native-library cost.

## Revised method

[Windowed engine](../../scripts/atlas/contour-pilot/windowed.py) processes **256×256 grid quads**, reading at most **257×257 contour samples**. Adjacent windows share their bordering samples; each quad has exactly one owner. Resolution, sample centres, extent and ContourPy flags remain unchanged. No grid is replaced by a coarser source to make the native baseline pass.

One generator/window is retained. Heights convert once within that window; masks/XY meshes stay bounded. Levels outside its finite range are skipped. Fragments are written immediately to source/level-specific files. Seam endpoints use native grid-edge/node identities and canonical linear edge crossings, not geographic proximity snapping. One level is reassembled at a time; a **100,000-vertex geometry workspace** is an additional safety gate. Ambiguous degree>2 level-tie junctions fail explicitly. No new continuation is invented at nodata or source-family boundaries.

Strict 2 m means still use aligned 4×4 native samples. Gaussian sigma 2 m/radius 6 m adds a **three-coarse-sample filter halo**; this is distinct from contour ownership overlap. Every filter sample must be valid. Native reads for these windows are bounded to at most **1052×1052 samples**, including the smoothing halo. No whole native mosaic is needed. The full compound XY/height diagnostic is also windowed; no height-only conversion is substituted.

[Retained-source adapters](../../scripts/atlas/contour-pilot/readers.py) and [gated replay driver](../../scripts/atlas/contour-pilot/rerun.py) are prepared. The adapters have synthetic/mocked validation, **not real-file execution in this task**. Genuine datum-grid loading, Copernicus support, actual contour density and total run cost remain pending.

## Synthetic evidence

**28 focused controls pass:** affine edge heights; constants, ties and saddles; disjoint quad ownership; open and closed contours crossing windows; curvilinear seams; nodata holes and a completely missing window; filtered overlap; mocked four-tile native joins/centres; deterministic geometry; invalid inputs/references/fusion; scratch/vertex/memory/time refusals; folded/oversized grids; simplification displacement, ring preservation and introduced same-/cross-level intersections. Small monolithic references agree with windowed unions to **1e-6** in distance and length. Edge-height residual tolerance remains **0.001 m**. These are computational tolerances, not terrain accuracy.

Two lazy **4000×4000, 0.5 m, 2×2 km** synthetic runs covered the declared 2000–3200 m/10 m level set, 20 m membership and 100 m indices. Each produced native, strict 2 m and smoothed 2 m products. All fragment/master payload hashes and canonical receipts agree between runs. No full 4000-square synthetic height array was allocated by the windowed path.

| Measured property | Result |
|---|---:|
| Peak process working set, including scaled diagnosis/initial controls | **114,532,352 bytes / 109.2 MiB** |
| Numerical workload elapsed | **26.171 s** |
| Stored vertices, fragments plus masters, both runs | **1,190,706** |
| Stored bytes before completion receipt | **37,634,574** |
| Largest contour window | **66,049 samples** |
| Final 28-control suite | **1.031 s; 96,354,304-byte peak** |
| Final suite temporary file high-water mark | **32,038 bytes** |
| Final suite temporary vertex writes | **6,962**, deleted with owned fixtures |

These are laptop synthetic measurements, not Android performance or a guarantee for rougher real terrain. Full-shape tests do not cover the genuine transformation or delivery packages. Initial suite temporary writes were not logged in its benchmark receipt; the repeatable focused runner now measures them separately. Their same unchanged window controls were replayed successfully. All synthetic processes were sequential; no worker subprocesses were spawned or hidden.

The [compact receipt](../../scripts/atlas/contour-pilot/recovery-receipt.json) points to external diagnosis, two-run receipts and final checks. Measured method files were frozen and hash-verified before the later guard-preflight clarification. Geometry code was unchanged; historical method hashes remain distinguishable from current replay code. Bulky outputs stay outside Git.

## Enforcement and limitations

The [process guard](../../scripts/atlas/contour-pilot/resource_guard.py) verified a **hard 512 MiB resident maximum** and a stricter **384 MiB private-commit allocation limit**, applied only to the current Python process. A 512 MiB private allocation was rejected before touching memory. These limits constrain different quantities; they are not total laptop-memory or battery guarantees. Hard resident limits may cause paging; elapsed time must still be checked.

All entry points set OMP/OpenBLAS/MKL thread limits before importing NumPy; numerical processing/ContourPy use one thread. A separate auxiliary test invocation initially imported NumPy first, then exhausted its own private-commit headroom during imports. That failed invocation is not a pass or proof the machine's paging file needs changes. Correct ordering passed; a new baseline-commit preflight now fails clearly instead of assigning an already overcommitted process.

One ledger spans both proposed real runs and all products: **150,000,000 additional bytes, 2,000,000 stored vertices and 1200 s**, with pre-write byte/vertex checks, bounded workspace reservations and Windows current/peak checks. Time is checked at windows, levels, writes and pairwise controls; it is a cooperative elapsed limit, not an OS hard wall-time kill inside a stalled native call. A hang would require stopping the process; no result is accepted without the completion receipt. Exact memory safety of future native caches remains subject to the hard OS guards; refusal is an incomplete experiment, never authority to raise limits.

## Proposed original Riffelhorn repeat — approval required

**Inputs unchanged:** seven pinned Swiss/Copernicus/grid assets in [input pins](../../scripts/atlas/contour-pilot/input-pins.json). SHA-256/byte verification before and after. No acquisition, source copies, overwrite, packages, licence acceptance or requests. Swiss OGD/©swisstopo and full Copernicus GLO-30 F notices/obligations remain; per-cell epochs and combined transform accuracy remain qualified.

**Extent unchanged:** EPSG:2056 core `[2624000,1091000,2626000,1093000]`; 250 m global-only context. Native sample-centre domains/halo remain explicit; this selection edge is not national coverage. Fresh proposed output: `${MERIDIAN_DATA_ROOT}/experiments/atlas/source-aware-contours-v2` (**not created**).

Exactly two serial runs, with the same process-wide ledger, would:

1. Derive and stitch Swiss native 0.5 m, strict 2 m, sigma-2 m/radius-6 m filtered 2 m, full XY/height EGM2008 diagnostic and native Copernicus contours. Keep separate DSM/DTM and vertical references. Generate every declared 10 m level, identify 20 m membership/100 m indices.
2. Validate edge crossings, closed/open seams, finite coordinates, four 1 km partition reconstruction and XY round trip. Test one 2 m simplification candidate against **all non-empty level pairs and same-level lines**, one bounded pair at a time; preserve originals and reject crossings/collapsed rings/excess displacement. No simplified product is silently adopted.
3. Compare same-source resolution/filter geometry on common supported interior, then transformed Swiss/Copernicus geometry at 20 m levels and qualified sampled-height diagnostics. Equal raw LN02/EGM2008 labels are never compared as common heights. No offsets or fusion.
4. Store fragments, stitched native-coordinate NDJSON, manifests/receipts and all hashes. Test delivery partition arithmetic in memory; no MVT archive, basemap, main-map integration or Android test. No figures are necessary for this repeat.
5. Compare canonical receipts/payload hashes across runs; verify sources unchanged and caps satisfied. Any unsupported seam, reference, rights, density, resource refusal, missing input or numerical mismatch stops with an incomplete outcome. No scope/budget relaxation.

After separate approval, the prepared command is:

```powershell
& $terrainPython -B scripts/atlas/contour-pilot/rerun.py `
  --owner-approved-riffelhorn --data-root $terrainData `
  --output "$terrainData/experiments/atlas/source-aware-contours-v2"
```

The flag records an operator decision; it does not grant permission. **This command has not been run.** Success requires genuine source-specific products, unchanged inputs, deterministic hashes, declared numerical/seam controls and resource conformance. Synthetic recovery alone does not satisfy that gate.
