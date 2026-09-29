# Phase 4 data migration inventory

This is the non-destructive input to Phase 4. It records the current estate and
proposed classifications; it does not authorise copying, moving or deleting anything.

The evidence-based, subphase-by-subphase execution plan is maintained in
[Phase 4 filesystem migration execution plan](phase-4-execution-plan.md).

**Phase 4B status:** the curated historical payload has been copied to
`[DATA]/experiments/earth-lab` and validated against the explicit
[`phase-4b-migration-manifest.json`](phase-4b-migration-manifest.json). The old
`[DATA]/earth-lab` tree remains intact as the transition rollback source.

**Phase 4C status:** nine reusable Tryfan source/derived products have been copied to
`[DATA]/{sources,derived}/atlas/tryfan` and validated against
[`phase-4c-promotion-manifest.json`](phase-4c-promotion-manifest.json). The neutral
consumer contract is [`atlas/tryfan-data-catalog.json`](atlas/tryfan-data-catalog.json).
Historical copies remain.

**Phase 4D status:** four private estates, with research results and cache separated,
have been copied to `[PRIVATE]/traverse` and validated against the privacy-safe aggregate
[`phase-4d-private-migration-manifest.json`](phase-4d-private-migration-manifest.json).
The detailed inventory remains private. The old estates remain solely as rollback copies;
Phase 4E has copied and validated the current and previous complete GFS runs under
`[DATA]/derived/weather/gfs`; the old publication remains unchanged and no deletion has begun.

The migration sequence for every category is:

```text
COPY -> UPDATE REFERENCES -> VALIDATE -> COMPARE HASHES -> ONLY THEN REMOVE OLD COPY
```

Removal is a separate reviewed decision. Frozen experiment identities and the
`pre-atlas-restructure` restore point remain valid throughout.

## Current estate summary

The current external root contains approximately:

| Current category | Approximate size | Approximate files | Character |
| --- | ---: | ---: | --- |
| `earth-lab` | 1.72 GiB | 5,796 | Mixed environment, sources, derived products and experiments |
| `terrain-research` | 158 MiB | 385 | Historical experiments with embedded cache/derived/report state |
| `activity-research` | 150 MiB | 2,268 | Private research, caches and derived personal analysis |
| `strava-export` | 33 MiB | 341 | Private source export |
| `route-benchmarks` | 2.1 MiB | 11 | Private Traverse benchmark data unless public/licensed fixture status is positively established |
| `public/weather/gfs` in the repository worktree | 2.41 GiB | 42,283 | Ignored generated runtime publication |

Counts and sizes are filesystem observations from Phase 3, not canonical identities.

## Migration inventory

| Current location or pattern | Proposed eventual category | Git tracked? | Reproducible / identity evidence | Privacy | Current dependencies | Risk and Phase 4 validation |
| --- | --- | --- | --- | --- | --- | --- |
| `meridian-data/earth-lab/.venv` | Rebuild locally; cache/tooling environment, not durable data | No | Recreated from `scripts/earth_lab/requirements.txt` | No known private data | Historical command examples invoke its interpreter | Low. Recreate in the chosen environment; run the full Earth Lab suite. Do not copy as durable data. |
| `meridian-data/earth-lab/tryfan-001` | `experiments/earth-lab/tryfan-001` initially; classify retained source extracts and deterministic terrain products only after preserving experiment integrity | No | Repository AOI/config and generated reports/manifests; not every file has a top-level inventory hash | Public-sector terrain source | Historical Lab 001 configs, README commands and later terrain work | Medium/high. Preserve directory as a unit first, update explicit paths, compare critical raster/manifests and rerun focused terrain validation before considering a split. |
| `meridian-data/earth-lab/tryfan-004` | Mixed: historical outputs under `experiments`; retained source/reference observations under `sources`; canonical terrain under `derived/atlas/tryfan`; external Unreal project retained as recovery evidence until separately retired | No | Canonical R16, terrain manifest, reference image, reports and renderer dependencies have recorded SHA-256 values | Reference photographs carry source/licence provenance; no personal activity data | Frozen Labs 004/005A, Labs 006-009, renderer bootstrap and many historical configs | **Highest risk.** Copy without splitting first or use a manifest-led staged split. Verify the canonical R16, landscape manifest, photographs, frozen reports and all renderer bootstrap hashes. Never treat the old Unreal project as disposable until repository renderer recovery is revalidated from the new paths. |
| `meridian-data/earth-lab/tryfan-005b` and `tryfan-005c` | `experiments/earth-lab/...` for reports/diagnostics; retained Sentinel subsets may later sit under `sources/copernicus`; aligned/temporal products under `derived/atlas/tryfan` only where they have continuing use | No | Product IDs, acquisition metadata, output hashes and deterministic Lab reports | No known private data | Labs 005B/C and frozen Labs 006-009 | High. Preserve native/effective-resolution metadata and source/product IDs. Compare report/result hashes and aligned-grid inventories; do not collapse 10/20 m evidence into 1 m products. |
| `meridian-data/earth-lab/tryfan-006` | Primarily `experiments/earth-lab/tryfan-006`; reusable clipped source evidence may be classified under `sources` only with licence/provenance intact | No | Frozen result hash plus evidence-package and lookup hashes in configs | No known private data | Labs 007-009 | High. Verify Lab 006 result/package identities and source category lookups; preserve NRW/BGS scale and temporal semantics. |
| `meridian-data/earth-lab/tryfan-007`, `tryfan-008`, `tryfan-009` | Frozen reports under `experiments/earth-lab`; renderer-neutral model/reconstruction products with continuing use may be promoted to `derived/atlas/tryfan` while frozen copies/identities remain addressable | No | Frozen deterministic identities: Lab 007 `574ce8...`, Lab 008 `399636...`, Lab 009 `14f909...`; file inventories in reports/packages | No known private data | Lab 009 and Tryfan Reference Renderer bootstrap | High. Copy and compare complete reported inventories and deterministic hashes. Update bootstrap/config references only after both old and new products validate. Do not relabel inference/reconstruction as observation. |
| `meridian-data/terrain-research/wales-v1` and `england-v2` | `[PRIVATE]/traverse/experiments/terrain-research`; embedded reacquirable tile caches under `[PRIVATE]/traverse/cache/terrain-research` | No | Repository processing code and reports; complete private copy now validated | **Private route-conditioned output** | `scripts/terrain_research` accepts explicit roots | Copied and hash-validated in Phase 4D. Old copy retained until Phase 4G. |
| `meridian-data/activity-research/**` | `[PRIVATE]/traverse/experiments/activity-research`; separable `dem-cache` trees under `[PRIVATE]/traverse/cache/activity-research` | No | Repository analysis code; outputs depend on private source activities | **Private** | `scripts/activity_research` uses explicit CLI paths | Copied and hash-validated in Phase 4D. Old copy retained until Phase 4G. |
| `meridian-data/strava-export/**` | `[PRIVATE]/traverse/sources/strava-export` | No | Original export is the source; may not be reacquirable identically | **Private** | Activity-research CLI inputs | Copied and hash-validated in Phase 4D. Old copy retained until Phase 4G. Never add to Git. |
| `meridian-data/route-benchmarks/gpx/**` | `[PRIVATE]/traverse/benchmarks/routes` | No | Eleven GPX files; detailed inventory remains private | **Private unless public/licensed fixture status is positively established** | Terrain research and possible route validation workflows use explicit paths | Copied and hash-validated in Phase 4D without disclosing route identities. Old copy retained until Phase 4G. |
| `public/weather/gfs/**` | Authoritative current + previous complete runs now under `[DATA]/derived/weather/gfs`; legacy tree remains rollback/cache/partial history pending Phase 4G | Ignored | All 40,841 promoted payload files match source SHA-256; both complete runs pass ten-field/24-step PNG validation | No | Builder defaults to the external root; guarded Vite adapter preserves `/weather/gfs`; production builds materialize only the catalogue-selected run | Copied and validated in Phase 4E. Eleven stale source-building trees, the older partial run and lock were not promoted and remain unchanged for Phase 4F/4G review. |
| `renderers/unreal/tryfan-reference` durable source | Remains version-controlled renderer source | Yes; map uses path-specific Git LFS | Manifest, bootstrap, fixed hashes and validators | No secrets/private pointers tracked | Consumes data-root products listed above | Already canonical source. Phase 4 updates only external dependency paths/manifests after copied data validate. Map hash must remain `85ef8f...`; no Unreal save is required for a path migration. |
| External historical `earth-lab/tryfan-004/unreal-project/TryfanLab004` | Retain as experiment/recovery copy until a separately approved retirement | No | Pre-restructure backup and critical hashes; repository renderer now independently preserved | No known private data; contains machine-local state | Historical workflows may still point at it | High. It is no longer source of truth, but removal is not part of Phase 4 path migration. Compare critical hashes and retain until repository renderer bootstrap and manual recovery criteria have been exercised after migration. |
| Repository `docs/earth-lab/*.json` and `scripts/earth_lab` | Historical source/config remain in Git; later shared code promotion is a separate architecture task | Yes | Git history and frozen configs | No | Many configs encode `../meridian-data/earth-lab/...` | Do not rewrite wholesale during data copy. Use the compatibility resolver or targeted reference updates with frozen hash checks. Preserve historical identity. |

## Known reference classes

Phase 3 found four distinct path classes:

1. **Root-aware active tooling**: `scripts/meridian_paths.py` and the Tryfan
   Reference Renderer bootstrap consume configured roots.
2. **Explicit-path tools**: terrain/activity research and many acquisition commands
   receive input/output roots on the command line. They are portable when callers
   supply paths, though historical examples use the sibling layout.
3. **Frozen legacy configs/entry points**: Labs 001-009 contain
   `../meridian-data/earth-lab/...` conventions and often resolve them relative to
   the repository. These remain deliberate compatibility exceptions until Phase 4.
4. **Generated runtime pointers**: ignored Unreal `meridian-*-source.json` files use
   absolute paths required by Unreal Python. The bootstrap rewrites them per machine;
   they are not source or provenance and must never be committed.

No tracked personal `C:\Users\...` path was found in the Phase 3 privacy scan.
The binary Unreal map contains historical import metadata; changing that would
require an Unreal save and is neither necessary nor permitted for path migration.

## Recorded decisions and decisions required before removal

- The eleven route-benchmark GPX files are provisionally private Traverse benchmark
  data. Phase 4 places them under `MERIDIAN_PRIVATE_ROOT` unless public/licensed
  fixture status is positively established before migration.
- Decide which renderer-neutral Lab 007-009 products deserve a promoted
  `derived/atlas/tryfan` copy in addition to their frozen experiment home.
- Decide whether current weather publication remains under Vite `public` through a
  generated copy/link or whether a future build step reads an external root.
- Define retention periods for reacquirable Sentinel subsets and weather runs after
  reproducibility and licensing requirements are satisfied.
- Treat retirement of the old external Unreal project as a separate, explicitly
  approved cleanup after the migrated repository renderer has been recovered and
  validated.
