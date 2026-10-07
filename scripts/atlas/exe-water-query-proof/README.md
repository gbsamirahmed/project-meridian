# Retained Exe qualified-water query proof

Research-only property-scoped resolution over existing retained native evidence. No acquisition,
hydrological inference, source geometry changes, production imports or package/runtime changes.
The [matrix](matrix.json) fixes75 queries before new query outputs, using all six original probes.

```powershell
node scripts/atlas/exe-water-query-proof/run-proof.mjs
node --test scripts/atlas/exe-water-query-proof/test-proof.mjs
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/exe-water-query-proof/validate.py
```

The existing Python scientific runtime and `meridian-data/derived/atlas/water-check-v1` are
required. The adapter verifies31 pinned source/document hashes and records66 directory-file hashes.
It reads native polygons/geographic cells, without reprojection of raster values or inferred labels.
The resolver uses frozen Contract v1 definitions/validator, small native templates and source-scoped
FeatureRef associations. Operational unavailable stays outside the semantic ClaimResult enum.

The runner launches four genuinely fresh CLI processes: initialize, recover, independent rebuild,
and recover again. Existing single-writer snapshot tooling is reused unchanged. Each process
reads retained assets plus declared matrix/configuration; disposable GIS/query facts are not stored.
Stores and intermediate query files live in a uniquely created temporary directory and are removed
only after verifying that path. No persistent runtime store is committed. No fabricated source release.

For local inspection, `cli.mjs init|recover <scratch-store> <output-json>` exposes qualified queries.
A snapshot contains complete qualified claims and asset selectors, not source geometries/pixel data.
`resolveQuery` and `evaluate` are research functions, not a public API or universal water layer.
The durable artifact contains shared collection contexts, query-selected native records/templates,
exact provenance/time/conditions, direct scoped dependencies, gaps, and restart logical hashes.

[Report](../../../docs/research/exe-water-query-proof.md),
[results](../../../docs/research/exe-water-query-results.json),
[validation](../../../docs/research/exe-water-query-validation.json).
