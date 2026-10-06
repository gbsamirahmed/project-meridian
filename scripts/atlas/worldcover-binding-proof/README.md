# WorldCover binding proof (isolated, retained inputs only)

Run from repository root:

```powershell
node scripts/atlas/worldcover-binding-proof/run-proof.mjs
node --test scripts/atlas/test_worldcover_binding_proof.mjs
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/worldcover-binding-proof/test_reader.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/worldcover-binding-proof/validate.py
```

[Report](../../../docs/research/tryfan-worldcover-binding-proof.md) defines acceptance.
The reader uses existing Earth Lab Python dependencies; no installation/acquisition.
Original assets in `meridian-data/derived/atlas/semantic-comparison-v1` are read-only.
Metadata snapshots live separately in `meridian-data/derived/atlas/worldcover-binding-proof-v1/store`.
No source rasters, query buffers or per-pixel claims are serialized into that store.

`cli.mjs build [store]` and `query [store]` run in independent processes. V1 validates
shared templates and requested instances. Point flooring and centre-selected rectangle
queries preserve native angular grid; no class resampling. Code 0/255 cases are synthetic,
not real crop observations. Timing is diagnostic, outside logical hashes. The snapshot
mechanism is reused unchanged, not a production storage decision.
