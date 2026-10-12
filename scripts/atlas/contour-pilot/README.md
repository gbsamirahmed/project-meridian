# Source-aware contour pilot

**Current checkpoint:** the [staged adapter record](../../../docs/atlas/staged-contour-continuation-adapter.md) documents `staged_continuation.py`, `staged_store.py`, `riffelhorn_sources.py`, `stage_worker.py` and `supervise_stage.py`. Stage 1 derives two missing products once; Stage 2 separately verifies five products with per-level retirement. `staged-profile-proposal.json` has `approved: false` and fails workspace/member-cap preflight. No genuine stage is authorised. Older reproduction commands below are historical.

Offline research apparatus for the [Riffelhorn pilot](../../../docs/atlas/source-aware-contour-pilot.md). **Current genuine Outcome C: three Swiss single-run products passed local checks, but the shared vertex gate prevented completion.** The [pipeline recovery](../../../docs/atlas/contour-pipeline-recovery.md) validates accounting, job-tree supervision and limited conservative generalisation. No genuine continuation, acquisition, integration or publication is approved. Historical commands/results below remain context, not execution instructions.

Current recovery modules: `accounting.py` separates roles/work/storage; `worker_supervision.py` contains and monitors the actual workload tree; `topology_generalisation.py` validates complete supplied families; `retained_checks.py` reads only declared existing contour levels. `supervise_retained.py` is a bounded read-only entry point. The old launcher-only `supervise-genuine.ps1` now refuses execution. A new continuation adapter and budgets need owner review.

Use the recovery record's fresh-directory commands for synthetic/read-only checks. Genuine output directories, input pins and historical receipts must remain immutable. Default write caps remain unchanged. No simplified candidate is adopted; current topology evidence does not cover all levels of a whole product.

## Reproduction

Use the already retained scientific environment; do not install packages. Set `$terrainPython` to its Python executable and `$terrainData` to the existing external data root.

```powershell
& $terrainPython -B scripts/atlas/contour-pilot/test_pilot.py
```

Eleven synthetic controls cover edge interpolation, constants/ties/saddles, invalid samples, strict aggregation/filter support, monotonic grids, missing/changed inputs, units/references/identity, prohibited fusion, partition completeness and the allocation gate. They establish mathematics and rejection behaviour only.

The previously approved execution command was:

```powershell
& $terrainPython -B scripts/atlas/contour-pilot/supervise.py `
  --data-root $terrainData `
  --output "$terrainData/experiments/atlas/source-aware-contours-v1"
```

That directory now exists and is deliberately refused. The initial process-handle preflight failure remains in its root. A fresh `execution-2` child, with `--budget-root` pointing at the owning root, retained the subsequent memory-stop receipt. No outputs were overwritten. Do not choose a different directory to bypass this milestone's stop.

## Method and bounds

`input-pins.json` identifies seven retained source/grid files and the accepted compound transformation. Before/after SHA-256 checks are mandatory; missing/changed files stop the utility. PROJ network and GDAL auxiliary-file writing are disabled. Existing ContourPy 1.4.0 uses serial, Separate, Linear, `corner_mask=False`, `quad_as_tri=False`, one thread. Native sample centres are reconstructed once; invalid samples exclude whole touching quads.

The planned products are Swiss native 0.5 m, strict 2 m block means, sigma-2 m/radius-6 m smoothing, full compound-transformed Swiss 2 m XY/heights, and native Copernicus point-post contours. Levels are 2000–3200 m every 10 m, with a 20 m subset and 100 m index classification. Outputs are native-XY NDJSON plus manifests, not a selected production format; projected XY is not GeoJSON. Core partitions use EPSG:2056. Separate DSM/DTM and LN02/EGM2008 meanings remain explicit. No source-family joining is permitted.

Limits span both planned replays: 150,000,000 additional external scratch bytes; 512 MiB process working set; 2,000,000 stored vertices; 20 minutes. Polling and process peak checks are measurements, **not hard allocation confinement**. The observed peak crossed the ceiling during preparation; the process then stopped before generating a contour level. A conservative `40 × cell-count` allocation preflight was added afterwards and tested synthetically. It is a refusal heuristic, not a proven upper bound or a successful genuine-data rerun.

## Evidence and limitations

- `experiment-receipt.json`: sanitised stop evidence and current file hashes. This tool revision includes the later guard; it is not claimed to reproduce the pre-guard peak byte for byte.
- `preservation-receipt.json`: read-only checks against accepted protected hashes, Git baseline blobs, publication inventory and seven input pins.
- No completed manifest, contour geometry, height comparison, native join result, simplification result, deterministic replay pair or figure exists. Downstream code remains unvalidated on genuine outputs.
- No HTTP requests, new dependencies, licence acceptance, Android operations or commits occurred.

Existing package licences apply: ContourPy BSD-3-Clause, NumPy/Rasterio BSD, GDAL MIT, pyproj/PROJ MIT and Shapely BSD. These do not license terrain data. Swiss OGD/©swisstopo and the full Copernicus modified-product notice and applicable downstream terms must accompany any future derived products; retained grids have CC0/public-domain lineage. Exact pixel epochs and combined transformation accuracy remain qualified.

The next proposed task is to remove avoidable native-grid memory copies and validate a conservative allocation plan, then seek approval to repeat the unchanged bounded experiment. No larger extent, increased budget, new source, live map or permanent delivery technology is implied.

## Synthetic memory recovery — current method

The [recovery record](../../../docs/atlas/contour-processing-memory-recovery.md) and
[precomputed-product proposal](../../../docs/atlas/precomputed-terrain-products.md)
extend the historical stop without claiming a genuine contour result. The legacy
`pilot.py`/`supervise.py` path remains historical; do not use it for the next native replay.

Current modules: `windowed.py` owns quads/stitches source-specific seams;
`readers.py` provides bounded native/coarse/context adapters; `resource_guard.py`
confines this process; `rerun.py` is the separately gated genuine two-run driver.
No permanent product encoding or provider framework is adopted.

To repeat focused controls only, choose a fresh owned synthetic check directory:

```powershell
& $terrainPython -B scripts/atlas/contour-pilot/check_synthetic.py `
  --output "$terrainData/experiments/atlas/source-aware-contours-synthetic-recovery-v1/new-checks"
```

The entry point sets one-thread variables before library imports, confines its own
process, measures owned temporary output, and opens no genuine DEM. Twenty-eight
controls pass. No package installation is required. `synthetic_recovery.py` is the
full-shape synthetic harness; its two completed executions and method snapshot are
sealed in the external root and compact `recovery-receipt.json`. Do not overwrite them.

The original seven inputs, extent, native comparison, intervals and reference
qualifications remain fixed. The next genuine command and exact approval/stop
criteria are in the recovery record. **It has not been executed.** No application,
Android, live provider, hosting, tile archive or commit is authorised by these tests.

## Genuine attempt — current Outcome C

The [current scientific record](../../../docs/atlas/source-aware-contour-pilot.md#genuine-offline-rerun--current-outcome-c)
reports the owner-approved `source-aware-contours-v1/execution-3` attempt.
Three Swiss variants completed their single-run checks; transformed extraction
stopped at the shared vertex gate. No Copernicus contours or run 2 were completed.
`genuine-rerun-receipt.json` seals the partial inventory; bulky payloads remain external.
No generated data are accepted for publication or app integration.

Operational-only arguments reserve log bytes, charge prerequisite vertex writes
and use the existing owning root. No numerical method, input pin or tolerance changed.
The supervisor tracked the Windows venv launcher rather than the actual worker;
its aggregate-peak and underlying-worker timeout claims are not validated.
**Do not reuse that supervision as reliable full-process accounting until owner review.**
Do not retry the genuine experiment, reset its ledger or retire payloads without
new approval. Previous stop/synthetic evidence and all inputs remain intact.
